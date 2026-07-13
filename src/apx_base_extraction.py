"""Bounded extraction of the fixed, verified Arch package set into /tmp."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess

from apx_package_acquisition import AUTHORIZED_MANIFEST, MANIFEST_PATH
from apx_package_metadata import AUTHORIZED_SIGNATURE_EVIDENCE, ROOT as METADATA_ROOT
from apx_resolution import parse_resolution_manifest
from apx_signature_verification import PACKAGE_ROOT


ROOT = Path("/tmp/apx-base-extraction-20260711-v1")
ROOTFS = ROOT / "rootfs"
METADATA_EVIDENCE = METADATA_ROOT / "package-metadata.json"
AUTHORIZED_METADATA = "0722db2c4a04f46d8617b7607e534dfd8429de6482bfbdaf57e3e69162a4f294"
MAX_EXTRACTED_BYTES = 1024**3
MAX_MEMBERS = 250_000
MAX_LISTING_BYTES = 16 * 1024**2
PACKAGE_METADATA_MEMBERS = (".BUILDINFO", ".INSTALL", ".MTREE", ".PKGINFO")


class BaseExtractionError(RuntimeError):
    """The disposable base cannot be extracted within its closed policy."""


@dataclass(frozen=True)
class BaseExtractionReport:
    schema_version: int
    manifest_digest: str
    signature_evidence_digest: str
    metadata_digest: str
    package_count: int
    archive_member_count: int
    regular_file_count: int
    directory_count: int
    symlink_count: int
    logical_bytes: int
    allocated_bytes: int
    rootfs_tree_digest: str


def _load_metadata() -> dict:
    try:
        payload = json.loads(METADATA_EVIDENCE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise BaseExtractionError("verified metadata receipt is unavailable") from error
    digest = payload.pop("metadata_digest", None)
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    if (
        digest != AUTHORIZED_METADATA
        or hashlib.sha256(canonical.encode()).hexdigest() != digest
        or payload.get("manifest_digest") != AUTHORIZED_MANIFEST
        or payload.get("signature_evidence_digest") != AUTHORIZED_SIGNATURE_EVIDENCE
        or payload.get("package_count") != 138
    ):
        raise BaseExtractionError("verified metadata receipt identity changed")
    return payload


def validate_member_listing(output: bytes) -> int:
    if len(output) > MAX_LISTING_BYTES:
        raise BaseExtractionError("archive member listing exceeded its bound")
    try:
        names = output.decode("utf-8", "strict").splitlines()
    except UnicodeDecodeError as error:
        raise BaseExtractionError("archive member path is not UTF-8") from error
    for name in names:
        path = PurePosixPath(name)
        if not name or path.is_absolute() or ".." in path.parts or "\x00" in name:
            raise BaseExtractionError("archive contains a path outside the disposable base")
    return len(names)


def _run(command: tuple[str, ...], *, maximum_output: int) -> bytes:
    result = subprocess.run(
        command, shell=False, stdin=subprocess.DEVNULL, capture_output=True,
        timeout=120, env={"LC_ALL": "C", "PATH": "/usr/bin"}, check=False,
    )
    if len(result.stdout) > maximum_output or len(result.stderr) > maximum_output:
        raise BaseExtractionError("archive tool output exceeded its bound")
    if result.returncode != 0:
        raise BaseExtractionError("archive tool rejected a verified package")
    return result.stdout


def _tree_measurement(root: Path) -> tuple[int, int, int, int, int, str]:
    regular = directories = symlinks = logical = allocated = 0
    records = []
    seen: set[tuple[int, int]] = set()
    for directory, names, files in os.walk(root, topdown=True, followlinks=False):
        names.sort(); files.sort()
        for name in names + files:
            path = Path(directory) / name
            info = path.lstat()
            relative = path.relative_to(root).as_posix()
            mode = stat.S_IFMT(info.st_mode)
            if stat.S_ISDIR(info.st_mode):
                directories += 1; kind = "d"; target = ""
            elif stat.S_ISLNK(info.st_mode):
                symlinks += 1; kind = "l"; target = os.readlink(path)
            elif stat.S_ISREG(info.st_mode):
                regular += 1; kind = "f"; target = ""
                identity = (info.st_dev, info.st_ino)
                if identity not in seen:
                    seen.add(identity); logical += info.st_size; allocated += info.st_blocks * 512
            else:
                raise BaseExtractionError("extraction created a forbidden special file")
            records.append(f"{kind}\0{relative}\0{info.st_mode & 0o7777:o}\0{info.st_size}\0{target}\n")
    digest = hashlib.sha256("".join(records).encode("utf-8")).hexdigest()
    return regular, directories, symlinks, logical, allocated, digest


def _write_exclusive(path: Path, content: bytes) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        view = memoryview(content)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise BaseExtractionError("extraction receipt write made no progress")
            view = view[written:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def extract_fixed_base(*, root: Path = ROOT) -> BaseExtractionReport:
    if root != ROOT and not str(root).startswith("/tmp/"):
        raise BaseExtractionError("extraction root is outside /tmp policy")
    manifest = parse_resolution_manifest(MANIFEST_PATH.read_text(encoding="utf-8"))
    metadata = _load_metadata()
    declared = sum(item["installed_size"] for item in metadata["packages"])
    if declared > MAX_EXTRACTED_BYTES:
        raise BaseExtractionError("declared installed size exceeds authorization")
    try:
        os.mkdir(root, 0o700)
    except FileExistsError as error:
        raise BaseExtractionError("extraction root exists; refusing adoption") from error
    ROOTFS.mkdir(mode=0o700) if root == ROOT else (root / "rootfs").mkdir(mode=0o700)
    rootfs = root / "rootfs"
    members = 0
    for item in manifest.packages:
        package = PACKAGE_ROOT / item.filename
        listing = _run(("/usr/bin/bsdtar", "-tf", str(package)), maximum_output=MAX_LISTING_BYTES)
        members += validate_member_listing(listing)
        if members > MAX_MEMBERS:
            raise BaseExtractionError("archive member aggregate exceeds authorization")
        command = ["/usr/bin/bsdtar", "-xf", str(package), "-C", str(rootfs),
                   "--no-same-owner", "--no-same-permissions", "--no-acls", "--no-xattrs", "--no-fflags"]
        for excluded in PACKAGE_METADATA_MEMBERS:
            command.extend(("--exclude", excluded))
        _run(tuple(command), maximum_output=1024**2)
        _, _, _, logical, allocated, _ = _tree_measurement(rootfs)
        if logical > MAX_EXTRACTED_BYTES or allocated > MAX_EXTRACTED_BYTES:
            raise BaseExtractionError("extracted base exceeded the authorized 1 GiB")
    regular, directories, symlinks, logical, allocated, tree_digest = _tree_measurement(rootfs)
    report = BaseExtractionReport(
        1, manifest.manifest_digest, AUTHORIZED_SIGNATURE_EVIDENCE,
        AUTHORIZED_METADATA, len(manifest.packages), members, regular,
        directories, symlinks, logical, allocated, tree_digest,
    )
    payload = asdict(report)
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    receipt = {**payload, "receipt_digest": hashlib.sha256(canonical.encode()).hexdigest()}
    _write_exclusive(root / "extraction-receipt.json", (json.dumps(receipt, sort_keys=True, indent=2) + "\n").encode())
    return report


def main() -> int:
    report = extract_fixed_base()
    print("APX disposable base extraction")
    print(f"Packages opened: {report.package_count}")
    print(f"Regular files: {report.regular_file_count}")
    print(f"Logical bytes: {report.logical_bytes}")
    print(f"Allocated bytes: {report.allocated_bytes}")
    print(f"Tree digest: {report.rootfs_tree_digest}")
    print(f"Root: {ROOT}")
    print("Host install/execute/service/user/Btrfs/cleanup effects: none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
