"""Bounded .PKGINFO inspection for the double-verified Hyprland role."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
import subprocess

from apx_graphical_acquisition import AUTHORIZED_MANIFEST, MANIFEST_PATH
from apx_graphical_resolution import parse_graphical_manifest
from apx_graphical_signature_verification import PACKAGE_ROOT, ROOT as SIGNATURE_ROOT
from apx_package_metadata import MAX_METADATA_BYTES, PackageMetadata, PackageMetadataError, parse_pkginfo


ROOT = Path("/tmp/apx-hyprland-metadata-20260711-v1")
SIGNATURE_EVIDENCE = SIGNATURE_ROOT / "graphical-signature-evidence.json"
AUTHORIZED_SIGNATURE_EVIDENCE = "15ee100d7be5bfef16278f476503c2b2d7e3546fb3027b5f3a541180dc302863"


@dataclass(frozen=True)
class GraphicalMetadataReport:
    schema_version: int
    manifest_digest: str
    signature_evidence_digest: str
    package_count: int
    installed_bytes: int
    packages: tuple[PackageMetadata, ...]
    metadata_digest: str


def _signature_receipt() -> dict:
    try:
        payload = json.loads(SIGNATURE_EVIDENCE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise PackageMetadataError("graphical signature receipt is unavailable") from error
    digest = payload.pop("evidence_digest", None)
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    if (
        digest != AUTHORIZED_SIGNATURE_EVIDENCE
        or hashlib.sha256(canonical.encode()).hexdigest() != digest
        or payload.get("manifest_digest") != AUTHORIZED_MANIFEST
        or payload.get("package_count") != 194
    ):
        raise PackageMetadataError("graphical signature receipt identity changed")
    return payload


def inspect_graphical_metadata() -> GraphicalMetadataReport:
    manifest = parse_graphical_manifest(MANIFEST_PATH.read_text(encoding="utf-8"))
    receipt = _signature_receipt()
    signed = {item["filename"]: item for item in receipt.get("evidence", ())}
    if len(signed) != 194:
        raise PackageMetadataError("graphical signature evidence package count disagrees")
    try:
        os.mkdir(ROOT, 0o700)
    except FileExistsError as error:
        raise PackageMetadataError("graphical metadata root exists; refusing adoption") from error
    results = []
    for item in manifest.role_packages:
        evidence = signed.get(item.filename)
        if not evidence or evidence.get("package_sha256") != item.sha256 or not evidence.get("independent_valid"):
            raise PackageMetadataError("graphical package lacks double-verification evidence")
        result = subprocess.run(
            ("/usr/bin/bsdtar", "-xOf", str(PACKAGE_ROOT / item.filename), ".PKGINFO"),
            shell=False, stdin=subprocess.DEVNULL, capture_output=True, timeout=10,
            env={"LC_ALL": "C", "PATH": "/usr/bin"}, check=False,
        )
        if result.returncode != 0 or len(result.stdout) > MAX_METADATA_BYTES or len(result.stderr) > MAX_METADATA_BYTES:
            raise PackageMetadataError("bounded graphical metadata inspection failed")
        try:
            metadata = parse_pkginfo(result.stdout.decode("utf-8", "strict"), filename=item.filename)
        except UnicodeDecodeError as error:
            raise PackageMetadataError("graphical metadata is not UTF-8") from error
        if (metadata.name, metadata.version, metadata.architecture) != (item.name, item.version, item.architecture):
            raise PackageMetadataError("inside graphical package identity disagrees with manifest")
        results.append(metadata)
    unsigned = {
        "schema_version": 1, "manifest_digest": manifest.manifest_digest,
        "signature_evidence_digest": AUTHORIZED_SIGNATURE_EVIDENCE,
        "package_count": len(results),
        "installed_bytes": sum(item.installed_size for item in results),
        "packages": [asdict(item) for item in results],
    }
    canonical = json.dumps(unsigned, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode()).hexdigest()
    payload = {**unsigned, "metadata_digest": digest}
    descriptor = os.open(ROOT / "graphical-package-metadata.json",
                         os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        os.write(descriptor, (json.dumps(payload, sort_keys=True, indent=2) + "\n").encode())
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return GraphicalMetadataReport(
        1, manifest.manifest_digest, AUTHORIZED_SIGNATURE_EVIDENCE, len(results),
        unsigned["installed_bytes"], tuple(results), digest,
    )


def main() -> int:
    result = inspect_graphical_metadata()
    print("APX Hyprland verified package metadata")
    print(f"Packages matched inside and outside: {result.package_count}")
    print(f"Installed bytes declared: {result.installed_bytes}")
    print(f"Metadata digest: {result.metadata_digest}")
    print("Install/full-extract/execute/GPU/network/system/cleanup effects: none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
