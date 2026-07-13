"""Bounded inspection of .PKGINFO in the verified fixed package set."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
import subprocess

from apx_package_acquisition import AUTHORIZED_MANIFEST, MANIFEST_PATH
from apx_resolution import parse_resolution_manifest
from apx_signature_verification import PACKAGE_ROOT, ROOT as SIGNATURE_ROOT


ROOT = Path("/tmp/apx-package-metadata-20260711-v1")
SIGNATURE_EVIDENCE = SIGNATURE_ROOT / "signature-evidence.json"
AUTHORIZED_SIGNATURE_EVIDENCE = "468116fb5277d91a099d0d4adbc5ca6579a5962965b062c0b6a1f09db9e4ea84"
MAX_METADATA_BYTES = 256 * 1024
REQUIRED_SINGLE = {"pkgname", "pkgver", "arch", "size", "packager", "builddate"}


class PackageMetadataError(RuntimeError):
    """Verified package metadata is missing, malformed, or inconsistent."""


@dataclass(frozen=True)
class PackageMetadata:
    filename: str
    name: str
    version: str
    architecture: str
    installed_size: int
    packager: str
    build_date: int
    dependencies: tuple[str, ...]
    optional_dependencies: tuple[str, ...]
    provides: tuple[str, ...]
    conflicts: tuple[str, ...]


def parse_pkginfo(text: str, *, filename: str) -> PackageMetadata:
    if not isinstance(text, str) or len(text.encode("utf-8")) > MAX_METADATA_BYTES:
        raise PackageMetadataError("package metadata is invalid or oversized")
    fields: dict[str, list[str]] = {}
    for line in text.splitlines():
        if not line or line.startswith("#"):
            continue
        key, separator, value = line.partition(" = ")
        if not separator or not key or not value or any(c in value for c in "\x00\r\n"):
            raise PackageMetadataError("package metadata contains a malformed row")
        fields.setdefault(key, []).append(value)
    if any(len(fields.get(key, ())) != 1 for key in REQUIRED_SINGLE):
        raise PackageMetadataError("package metadata lacks one required identity")
    try:
        size, build_date = int(fields["size"][0]), int(fields["builddate"][0])
    except ValueError as error:
        raise PackageMetadataError("package metadata number is malformed") from error
    if size < 0 or build_date <= 0:
        raise PackageMetadataError("package metadata number is outside policy")
    values = lambda key: tuple(sorted(set(fields.get(key, ()))))
    return PackageMetadata(
        filename, fields["pkgname"][0], fields["pkgver"][0], fields["arch"][0],
        size, fields["packager"][0], build_date, values("depend"),
        values("optdepend"), values("provides"), values("conflict"),
    )


def _signature_receipt() -> dict:
    try:
        payload = json.loads(SIGNATURE_EVIDENCE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise PackageMetadataError("signature receipt is unavailable or malformed") from error
    digest = payload.pop("evidence_digest", None)
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    if digest != AUTHORIZED_SIGNATURE_EVIDENCE or hashlib.sha256(canonical.encode()).hexdigest() != digest:
        raise PackageMetadataError("signature receipt identity changed")
    if payload.get("manifest_digest") != AUTHORIZED_MANIFEST or payload.get("package_count") != 138:
        raise PackageMetadataError("signature receipt is not the closed package set")
    return payload


def inspect_fixed_metadata(*, root: Path = ROOT) -> tuple[PackageMetadata, ...]:
    manifest = parse_resolution_manifest(MANIFEST_PATH.read_text(encoding="utf-8"))
    receipt = _signature_receipt()
    signed = {item["filename"]: item for item in receipt.get("evidence", ())}
    if len(signed) != len(manifest.packages):
        raise PackageMetadataError("signature receipt package count disagrees")
    try:
        os.mkdir(root, 0o700)
    except FileExistsError as error:
        raise PackageMetadataError("metadata root exists; refusing adoption") from error
    results = []
    for item in manifest.packages:
        evidence = signed.get(item.filename)
        if not evidence or evidence.get("package_sha256") != item.sha256 or not evidence.get("independent_valid"):
            raise PackageMetadataError("package lacks matching double-verification evidence")
        result = subprocess.run(
            ("/usr/bin/bsdtar", "-xOf", str(PACKAGE_ROOT / item.filename), ".PKGINFO"),
            shell=False, stdin=subprocess.DEVNULL, capture_output=True, timeout=10,
            env={"LC_ALL": "C", "PATH": "/usr/bin"}, check=False,
        )
        if result.returncode != 0 or len(result.stdout) > MAX_METADATA_BYTES or len(result.stderr) > MAX_METADATA_BYTES:
            raise PackageMetadataError("bounded package metadata inspection failed")
        try:
            metadata = parse_pkginfo(result.stdout.decode("utf-8", "strict"), filename=item.filename)
        except UnicodeDecodeError as error:
            raise PackageMetadataError("package metadata is not UTF-8") from error
        if (metadata.name, metadata.version, metadata.architecture) != (item.name, item.version, item.architecture):
            raise PackageMetadataError("inside-package identity disagrees with signed repository identity")
        results.append(metadata)
    payload = {"schema_version": 1, "manifest_digest": manifest.manifest_digest,
               "signature_evidence_digest": AUTHORIZED_SIGNATURE_EVIDENCE,
               "package_count": len(results), "packages": [asdict(item) for item in results]}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    payload["metadata_digest"] = hashlib.sha256(canonical.encode()).hexdigest()
    descriptor = os.open(root / "package-metadata.json", os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        os.write(descriptor, (json.dumps(payload, sort_keys=True, indent=2) + "\n").encode())
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return tuple(results)


def main() -> int:
    packages = inspect_fixed_metadata()
    receipt = json.loads((ROOT / "package-metadata.json").read_text())
    print("APX verified package metadata inspection")
    print(f"Packages matched inside and outside: {len(packages)}")
    print(f"Installed bytes declared: {sum(item.installed_size for item in packages)}")
    print(f"Metadata digest: {receipt['metadata_digest']}")
    print("Install/full-extract/execute/network effects: none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
