"""Fixed authorized acquisition of the closed Hyprland role package set."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Callable

from apx_downloader import DownloadRequest
from apx_graphical_resolution import ROOT as RESOLUTION_ROOT, parse_graphical_manifest
from apx_http import open_archive_response
from apx_staging import FixtureAcquisitionStaging
from apx_transfer import AcquiredFixtureFile, acquire_to_fixture


ROOT = Path("/tmp/apx-hyprland-package-acquisition-20260711-v1")
MANIFEST_PATH = RESOLUTION_ROOT / "graphical-resolution-manifest.json"
AUTHORIZED_MANIFEST = "e2f6adfc19e00dfe7cae21b4eab1650437edf24d817dc355a9af449d1cd9b25e"
SIGNATURE_MAX = 64 * 1024
AUTHORIZED_AGGREGATE = 277_362_247


@dataclass(frozen=True)
class GraphicalAcquisitionReport:
    root: str
    operation_id: str
    manifest_digest: str
    package_count: int
    signature_count: int
    aggregate_bytes: int
    files: tuple[AcquiredFixtureFile, ...]


def fixed_requests() -> tuple[DownloadRequest, ...]:
    manifest = parse_graphical_manifest(MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest.manifest_digest != AUTHORIZED_MANIFEST:
        raise ValueError("graphical manifest is not the authorized identity")
    requests = []
    for item in manifest.role_packages:
        requests.append(DownloadRequest(item.package_uri, item.filename, item.compressed_size,
                                        item.compressed_size, item.sha256))
        requests.append(DownloadRequest(item.signature_uri, item.filename + ".sig",
                                        SIGNATURE_MAX, None, None))
    if len(requests) != 388:
        raise ValueError("authorized graphical request count changed")
    return tuple(requests)


def acquire_graphical_packages(
    *, opener: Callable[[str, float], object] = open_archive_response,
) -> GraphicalAcquisitionReport:
    requests = fixed_requests()
    try:
        os.mkdir(ROOT, 0o700)
    except FileExistsError as error:
        raise RuntimeError("graphical acquisition root exists; refusing adoption") from error
    operation_id = "op-" + AUTHORIZED_MANIFEST[:32]
    staging = FixtureAcquisitionStaging(ROOT, operation_id, AUTHORIZED_MANIFEST)
    staging.reserve()
    acquired = []; aggregate = 0
    for request in requests:
        result = acquire_to_fixture(request=request, staging=staging, opener=opener, timeout_seconds=300)
        aggregate += result.transfer.bytes_received
        if aggregate > AUTHORIZED_AGGREGATE:
            raise RuntimeError("authorized graphical acquisition aggregate exceeded")
        acquired.append(result)
    return GraphicalAcquisitionReport(
        str(ROOT), operation_id, AUTHORIZED_MANIFEST, 194, 194, aggregate, tuple(acquired)
    )


def main() -> int:
    report = acquire_graphical_packages()
    print("APX Hyprland package and signature acquisition")
    print(f"Manifest: {report.manifest_digest}")
    print(f"Packages: {report.package_count}")
    print(f"Signatures: {report.signature_count}")
    print(f"Aggregate bytes: {report.aggregate_bytes}")
    print(f"Root: {report.root}")
    print("Install/extract/execute/GPU/system/cleanup effects: none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
