"""Closed package-resolution manifest bound to staged Arch databases."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
from typing import Sequence

from apx_isolation import BASE_PACKAGES, build_snapshot_acquisition_plan
from apx_repository_db import RepositoryDatabase, RepositoryPackage, parse_repository_database


RESOLUTION_ROOT = Path("/tmp/apx-package-resolution-20260711-v1")
DATABASE_ROOT = Path(
    "/tmp/apx-arch-databases-20260711-v1/"
    "op-f1cce5db72b63a928a77f0bc3854cd01/files"
)
DATABASE_DIGESTS = {
    "core": "12aea0ea6b5a16125064a19c7e8415d22e19b4517896d09eb2eb6cb2ee60b295",
    "extra": "5a5f994a35a6cf65ff2adb6b5f61aa4349aba62f8ee2a286d45b8d80819f43f7",
}
MAX_PACKAGES = 512
MAX_AGGREGATE_BYTES = 4 * 1024**3
OUTPUT_MAX = 2 * 1024**2
BASE_URI = "https://archive.archlinux.org/repos/2026/07/11"


class ResolutionError(ValueError):
    """Resolver output is malformed, incomplete, or disagrees with databases."""


@dataclass(frozen=True)
class ResolvedPackage:
    repository: str
    name: str
    version: str
    architecture: str
    filename: str
    compressed_size: int
    sha256: str
    database_signature: str
    package_uri: str
    signature_uri: str


@dataclass(frozen=True)
class ResolutionManifest:
    schema_version: int
    plan_digest: str
    database_digests: tuple[tuple[str, str], ...]
    seeds: tuple[str, ...]
    packages: tuple[ResolvedPackage, ...]
    aggregate_package_bytes: int
    manifest_digest: str


def _manifest_digest(manifest: ResolutionManifest) -> str:
    payload = asdict(manifest)
    payload.pop("manifest_digest", None)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def build_resolution_manifest(
    output: str,
    *,
    databases: Sequence[RepositoryDatabase],
    plan_digest: str,
) -> ResolutionManifest:
    if not isinstance(output, str) or len(output.encode("utf-8")) > OUTPUT_MAX:
        raise ResolutionError("resolver output is invalid or oversized")
    if len(plan_digest) != 64 or any(character not in "0123456789abcdef" for character in plan_digest):
        raise ResolutionError("resolution plan digest is invalid")
    database_map: dict[tuple[str, str], RepositoryPackage] = {}
    database_digests: list[tuple[str, str]] = []
    for database in databases:
        if type(database) is not RepositoryDatabase or database.repository not in {"core", "extra"}:
            raise ResolutionError("resolution database evidence is invalid")
        database_digests.append((database.repository, database.file_sha256))
        for package in database.packages:
            key = (package.repository, package.name)
            if key in database_map:
                raise ResolutionError("database package identity is duplicated")
            database_map[key] = package
    if sorted(name for name, _ in database_digests) != ["core", "extra"]:
        raise ResolutionError("resolution requires exactly core and extra databases")

    resolved: list[ResolvedPackage] = []
    seen_names: set[str] = set()
    for line in output.splitlines():
        if not line:
            continue
        fields = line.split("|")
        if len(fields) != 7:
            raise ResolutionError("resolver output row has wrong field count")
        repository, name, version, architecture, filename, size_text, uri = fields
        if name in seen_names:
            raise ResolutionError("resolver selected a duplicate package name")
        seen_names.add(name)
        record = database_map.get((repository, name))
        if record is None:
            raise ResolutionError("resolver selected a package outside staged databases")
        if not size_text.isascii() or not size_text.isdigit():
            raise ResolutionError("resolver package size is invalid")
        size = int(size_text)
        expected_uri = f"{BASE_URI}/{repository}/os/x86_64/{record.filename}"
        if (
            version != record.version
            or architecture != record.architecture
            or filename != record.filename
            or size != record.compressed_size
            or uri != expected_uri
        ):
            raise ResolutionError("resolver output disagrees with signed database metadata")
        resolved.append(
            ResolvedPackage(
                repository,
                name,
                version,
                architecture,
                filename,
                size,
                record.sha256,
                record.pgp_signature,
                uri,
                uri + ".sig",
            )
        )
    if not resolved or len(resolved) > MAX_PACKAGES:
        raise ResolutionError("resolved package count is outside policy")
    missing_seeds = set(BASE_PACKAGES) - seen_names
    if missing_seeds:
        raise ResolutionError("resolver output omits a fixed seed")
    aggregate = sum(item.compressed_size for item in resolved)
    if aggregate > MAX_AGGREGATE_BYTES:
        raise ResolutionError("resolved package bytes exceed aggregate policy")
    resolved.sort(key=lambda item: (item.repository, item.filename))
    draft = ResolutionManifest(
        1,
        plan_digest,
        tuple(sorted(database_digests)),
        BASE_PACKAGES,
        tuple(resolved),
        aggregate,
        "0" * 64,
    )
    return ResolutionManifest(
        draft.schema_version,
        draft.plan_digest,
        draft.database_digests,
        draft.seeds,
        draft.packages,
        draft.aggregate_package_bytes,
        _manifest_digest(draft),
    )


def _write_exclusive(path: Path, content: str) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        data = content.encode("utf-8")
        view = memoryview(data)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise ResolutionError("resolution evidence write made no progress")
            view = view[written:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _fixed_command(root: Path, config: Path) -> tuple[str, ...]:
    return (
        "pacman", "-Sp", "--print-format", "%r|%n|%v|%a|%f|%s|%l",
        "--config", str(config), "--dbpath", str(root / "db"),
        "--root", str(root / "root"), "--cachedir", str(root / "cache"),
        "--gpgdir", str(root / "gpg"), "--hookdir", str(root / "hooks"),
        "--logfile", str(root / "pacman.log"), "--", *BASE_PACKAGES,
    )


def resolve_fixed_manifest() -> ResolutionManifest:
    try:
        os.mkdir(RESOLUTION_ROOT, 0o700)
    except FileExistsError as error:
        raise ResolutionError("resolution root exists; refusing adoption") from error
    for relative in ("db", "db/sync", "root", "root/var", "root/var/lib", "root/var/lib/pacman", "root/var/lib/pacman/local", "cache", "gpg", "hooks"):
        (RESOLUTION_ROOT / relative).mkdir(mode=0o700)
    databases = tuple(
        parse_repository_database(
            DATABASE_ROOT / f"{name}.db", repository=name, expected_sha256=digest
        )
        for name, digest in sorted(DATABASE_DIGESTS.items())
    )
    for name in ("core", "extra"):
        shutil.copyfile(DATABASE_ROOT / f"{name}.db", RESOLUTION_ROOT / "db" / "sync" / f"{name}.db")
        os.chmod(RESOLUTION_ROOT / "db" / "sync" / f"{name}.db", 0o600)
    config = RESOLUTION_ROOT / "pacman.conf"
    _write_exclusive(
        config,
        "[options]\nArchitecture = x86_64\nSigLevel = Required DatabaseOptional\n"
        "LocalFileSigLevel = Required\n\n"
        f"[core]\nServer = {BASE_URI}/core/os/x86_64\n\n"
        f"[extra]\nServer = {BASE_URI}/extra/os/x86_64\n",
    )
    command = _fixed_command(RESOLUTION_ROOT, config)
    environment = {"LC_ALL": "C", "PATH": "/usr/bin"}
    outputs: list[str] = []
    for _ in range(2):
        completed = subprocess.run(
            command, shell=False, capture_output=True, text=True, timeout=30,
            env=environment,
        )
        if completed.returncode != 0 or len(completed.stdout.encode()) > OUTPUT_MAX:
            raise ResolutionError("fixed pacman resolution failed")
        outputs.append(completed.stdout)
    if outputs[0] != outputs[1]:
        raise ResolutionError("independent resolver passes disagree")
    plan = build_snapshot_acquisition_plan()
    manifest = build_resolution_manifest(outputs[0], databases=databases, plan_digest=plan.digest)
    serialized = json.dumps(asdict(manifest), sort_keys=True, separators=(",", ":")) + "\n"
    _write_exclusive(RESOLUTION_ROOT / "resolution-manifest.json", serialized)
    return manifest


def main() -> int:
    manifest = resolve_fixed_manifest()
    print("APX closed package resolution")
    print(f"Packages: {len(manifest.packages)}")
    print(f"Package bytes: {manifest.aggregate_package_bytes}")
    print(f"Manifest digest: {manifest.manifest_digest}")
    print(f"Evidence: {RESOLUTION_ROOT / 'resolution-manifest.json'}")
    print("Network/download/install/extract effects: none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
