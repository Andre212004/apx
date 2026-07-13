"""Fixed first real acquisition of dated Arch core/extra databases only."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Callable

from apx_downloader import DownloadRequest
from apx_http import open_archive_response
from apx_isolation import build_snapshot_acquisition_plan
from apx_staging import FixtureAcquisitionStaging
from apx_transfer import AcquiredFixtureFile, acquire_to_fixture


ACQUISITION_ROOT = Path("/tmp/apx-arch-databases-20260711-v1")
DATABASE_MAX = 64 * 1024**2
AGGREGATE_MAX = 128 * 1024**2
BASE_URI = "https://archive.archlinux.org/repos/2026/07/11"


@dataclass(frozen=True)
class DatabaseAcquisitionReport:
    root: str
    operation_id: str
    plan_digest: str
    files: tuple[AcquiredFixtureFile, ...]
    aggregate_bytes: int


def fixed_requests() -> tuple[DownloadRequest, ...]:
    return tuple(
        DownloadRequest(
            uri=f"{BASE_URI}/{repository}/os/x86_64/{repository}.db",
            filename=f"{repository}.db",
            maximum_bytes=DATABASE_MAX,
            expected_bytes=None,
            expected_sha256=None,
        )
        for repository in ("core", "extra")
    )


def acquire_fixed_databases(
    *,
    root: Path = ACQUISITION_ROOT,
    opener: Callable[[str, float], object] = open_archive_response,
) -> DatabaseAcquisitionReport:
    """Create one new root and acquire exactly core.db and extra.db."""
    root = Path(root)
    if root != ACQUISITION_ROOT and not str(root).startswith("/tmp/"):
        raise ValueError("database acquisition root must be the fixed path or a /tmp test path")
    try:
        os.mkdir(root, 0o700)
    except FileExistsError as error:
        raise RuntimeError("database acquisition root already exists; refusing adoption") from error
    plan = build_snapshot_acquisition_plan()
    operation_id = "op-" + plan.digest[:32]
    staging = FixtureAcquisitionStaging(root, operation_id, plan.digest)
    staging.reserve()
    acquired: list[AcquiredFixtureFile] = []
    aggregate = 0
    for request in fixed_requests():
        result = acquire_to_fixture(
            request=request,
            staging=staging,
            opener=opener,
            timeout_seconds=300,
        )
        aggregate += result.transfer.bytes_received
        if aggregate > AGGREGATE_MAX:
            raise RuntimeError("authorized database aggregate exceeded")
        acquired.append(result)
    return DatabaseAcquisitionReport(
        str(root), operation_id, plan.digest, tuple(acquired), aggregate
    )


def render_report(report: DatabaseAcquisitionReport) -> str:
    lines = [
        "APX Arch database acquisition",
        "Result: downloaded and staged; not installed or extracted",
        f"Root: {report.root}",
        f"Operation: {report.operation_id}",
        f"Plan digest: {report.plan_digest}",
    ]
    for item in report.files:
        lines.append(
            f"- {item.staged.filename}: {item.staged.bytes_written} bytes; SHA-256 {item.staged.sha256}"
        )
    lines.append(f"Aggregate: {report.aggregate_bytes} bytes")
    lines.append("Cleanup: not performed; requires separate approval")
    return "\n".join(lines)


def main() -> int:
    report = acquire_fixed_databases()
    print(render_report(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
