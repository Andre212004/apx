"""Fixed authorized acquisition of the closed 138-package Arch manifest."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Callable

from apx_downloader import DownloadRequest
from apx_http import open_archive_response
from apx_resolution import ResolutionManifest, parse_resolution_manifest
from apx_staging import FixtureAcquisitionStaging
from apx_transfer import AcquiredFixtureFile, acquire_to_fixture


ROOT = Path("/tmp/apx-package-acquisition-20260711-v1")
MANIFEST_PATH = Path("/tmp/apx-package-resolution-20260711-v1/resolution-manifest.json")
AUTHORIZED_MANIFEST = "574f5d31e7c4ee46b1982fe2baf285d014ba0d712e91aea6d00413ba8fe5e3f9"
SIGNATURE_MAX = 64 * 1024
AUTHORIZED_AGGREGATE = 137_308_097


@dataclass(frozen=True)
class PackageAcquisitionReport:
    root: str
    operation_id: str
    manifest_digest: str
    package_count: int
    signature_count: int
    aggregate_bytes: int
    files: tuple[AcquiredFixtureFile, ...]


def fixed_requests(manifest: ResolutionManifest) -> tuple[DownloadRequest, ...]:
    if manifest.manifest_digest != AUTHORIZED_MANIFEST:
        raise ValueError("package manifest is not the authorized identity")
    requests: list[DownloadRequest] = []
    for item in manifest.packages:
        requests.append(
            DownloadRequest(
                item.package_uri, item.filename, item.compressed_size,
                item.compressed_size, item.sha256,
            )
        )
        requests.append(
            DownloadRequest(
                item.signature_uri, item.filename + ".sig", SIGNATURE_MAX,
                None, None,
            )
        )
    if len(requests) != 276:
        raise ValueError("authorized request count changed")
    return tuple(requests)


def acquire_fixed_packages(
    *,
    root: Path = ROOT,
    manifest_path: Path = MANIFEST_PATH,
    opener: Callable[[str, float], object] = open_archive_response,
) -> PackageAcquisitionReport:
    root = Path(root)
    manifest_path = Path(manifest_path)
    if root != ROOT and not str(root).startswith("/tmp/"):
        raise ValueError("package acquisition root is outside /tmp policy")
    if os.path.lexists(root):
        raise RuntimeError("package acquisition root exists; refusing adoption")
    manifest = parse_resolution_manifest(manifest_path.read_text(encoding="utf-8"))
    if manifest.manifest_digest != AUTHORIZED_MANIFEST:
        raise ValueError("resolution evidence does not match authorization")
    try:
        os.mkdir(root, 0o700)
    except FileExistsError as error:
        raise RuntimeError("package acquisition root exists; refusing adoption") from error
    operation_id = "op-" + manifest.manifest_digest[:32]
    staging = FixtureAcquisitionStaging(root, operation_id, manifest.manifest_digest)
    staging.reserve()
    acquired: list[AcquiredFixtureFile] = []
    aggregate = 0
    for request in fixed_requests(manifest):
        result = acquire_to_fixture(
            request=request, staging=staging, opener=opener, timeout_seconds=300
        )
        aggregate += result.transfer.bytes_received
        if aggregate > AUTHORIZED_AGGREGATE:
            raise RuntimeError("authorized package acquisition aggregate exceeded")
        acquired.append(result)
    return PackageAcquisitionReport(
        str(root), operation_id, manifest.manifest_digest,
        len(manifest.packages), len(manifest.packages), aggregate, tuple(acquired),
    )


def main() -> int:
    report = acquire_fixed_packages()
    print("APX package and signature acquisition")
    print(f"Manifest: {report.manifest_digest}")
    print(f"Packages: {report.package_count}")
    print(f"Signatures: {report.signature_count}")
    print(f"Aggregate bytes: {report.aggregate_bytes}")
    print(f"Root: {report.root}")
    print("Install/extract/execute/cleanup effects: none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
