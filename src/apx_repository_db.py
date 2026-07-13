"""Strict read-only parser for staged Arch repository database metadata."""

from __future__ import annotations

from dataclasses import dataclass
import base64
import hashlib
import os
from pathlib import Path, PurePosixPath
import re
import stat
import tarfile


MAX_DATABASE_BYTES = 64 * 1024**2
MAX_EXPANDED_BYTES = 64 * 1024**2
MAX_RECORD_BYTES = 256 * 1024
MAX_RECORDS = 100_000
_SAFE = re.compile(r"[A-Za-z0-9][A-Za-z0-9@+_.:-]{0,254}")
_SHA256 = re.compile(r"[0-9a-f]{64}")


class RepositoryDatabaseError(ValueError):
    """Repository metadata is malformed, unsafe, or disagrees with evidence."""


@dataclass(frozen=True)
class RepositoryPackage:
    repository: str
    name: str
    version: str
    architecture: str
    filename: str
    compressed_size: int
    installed_size: int
    sha256: str
    pgp_signature: str
    dependencies: tuple[str, ...]


@dataclass(frozen=True)
class RepositoryDatabase:
    repository: str
    file_bytes: int
    file_sha256: str
    device: int
    inode: int
    packages: tuple[RepositoryPackage, ...]


def _fields(content: bytes) -> dict[str, tuple[str, ...]]:
    if len(content) > MAX_RECORD_BYTES or b"\x00" in content:
        raise RepositoryDatabaseError("repository record is oversized or binary")
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as error:
        raise RepositoryDatabaseError("repository record is not UTF-8") from error
    result: dict[str, tuple[str, ...]] = {}
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line:
            index += 1
            continue
        if not (line.startswith("%") and line.endswith("%") and len(line) > 2):
            raise RepositoryDatabaseError("repository record field marker is malformed")
        name = line[1:-1]
        if name in result:
            raise RepositoryDatabaseError("repository record field is duplicated")
        index += 1
        values: list[str] = []
        while index < len(lines) and lines[index]:
            values.append(lines[index])
            index += 1
        result[name] = tuple(values)
    return result


def _one(fields: dict[str, tuple[str, ...]], name: str) -> str:
    values = fields.get(name)
    if values is None or len(values) != 1:
        raise RepositoryDatabaseError(f"repository field {name} is missing or repeated")
    return values[0]


def _number(value: str, name: str) -> int:
    if not value.isascii() or not value.isdigit():
        raise RepositoryDatabaseError(f"repository field {name} is not numeric")
    return int(value)


def parse_repository_database(
    path: Path, *, repository: str, expected_sha256: str
) -> RepositoryDatabase:
    path = Path(path)
    if repository not in {"core", "extra"} or not _SHA256.fullmatch(expected_sha256):
        raise RepositoryDatabaseError("repository identity or expected digest is invalid")
    metadata = os.lstat(path)
    if not stat.S_ISREG(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
        raise RepositoryDatabaseError("repository database is not a regular file")
    if metadata.st_size > MAX_DATABASE_BYTES:
        raise RepositoryDatabaseError("repository database exceeds compressed bound")
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(64 * 1024):
            digest.update(chunk)
    actual_hash = digest.hexdigest()
    if actual_hash != expected_sha256:
        raise RepositoryDatabaseError("repository database digest mismatch")

    packages: list[RepositoryPackage] = []
    expanded = 0
    seen_names: set[str] = set()
    seen_files: set[str] = set()
    with tarfile.open(path, mode="r:gz") as archive:
        for member in archive:
            pure = PurePosixPath(member.name)
            if pure.is_absolute() or ".." in pure.parts or len(pure.parts) not in {1, 2}:
                raise RepositoryDatabaseError("repository member path is unsafe")
            if member.isdir():
                continue
            if not member.isfile() or len(pure.parts) != 2 or pure.name != "desc":
                raise RepositoryDatabaseError("repository contains an unexpected member")
            if member.size < 0 or member.size > MAX_RECORD_BYTES:
                raise RepositoryDatabaseError("repository member exceeds record bound")
            expanded += member.size
            if expanded > MAX_EXPANDED_BYTES or len(packages) >= MAX_RECORDS:
                raise RepositoryDatabaseError("repository expanded bounds exceeded")
            stream = archive.extractfile(member)
            if stream is None:
                raise RepositoryDatabaseError("repository record cannot be opened")
            fields = _fields(stream.read(MAX_RECORD_BYTES + 1))
            name = _one(fields, "NAME")
            version = _one(fields, "VERSION")
            architecture = _one(fields, "ARCH")
            filename = _one(fields, "FILENAME")
            sha256 = _one(fields, "SHA256SUM")
            pgp_signature = _one(fields, "PGPSIG")
            for value in (name, version, architecture, filename):
                if not _SAFE.fullmatch(value):
                    raise RepositoryDatabaseError("repository package identity is unsafe")
            if architecture not in {"any", "x86_64"} or not _SHA256.fullmatch(sha256):
                raise RepositoryDatabaseError("repository architecture or digest is invalid")
            try:
                base64.b64decode(pgp_signature, validate=True)
            except ValueError as error:
                raise RepositoryDatabaseError("repository package signature is malformed") from error
            if name in seen_names or filename in seen_files:
                raise RepositoryDatabaseError("repository package identity is duplicated")
            seen_names.add(name)
            seen_files.add(filename)
            packages.append(
                RepositoryPackage(
                    repository,
                    name,
                    version,
                    architecture,
                    filename,
                    _number(_one(fields, "CSIZE"), "CSIZE"),
                    _number(_one(fields, "ISIZE"), "ISIZE"),
                    sha256,
                    pgp_signature,
                    fields.get("DEPENDS", ()),
                )
            )
    packages.sort(key=lambda item: item.name)
    return RepositoryDatabase(
        repository, metadata.st_size, actual_hash, metadata.st_dev, metadata.st_ino,
        tuple(packages),
    )
