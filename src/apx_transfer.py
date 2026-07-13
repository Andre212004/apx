"""Compose bounded download and protected streaming staging boundaries."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from apx_downloader import DownloadRequest, DownloadResult, download_bounded
from apx_staging import FixtureAcquisitionStaging, StagedFile, StagingError


@dataclass(frozen=True)
class AcquiredFixtureFile:
    transfer: DownloadResult
    staged: StagedFile


def acquire_to_fixture(
    *,
    request: DownloadRequest,
    staging: FixtureAcquisitionStaging,
    opener: Callable[[str, float], object],
    timeout_seconds: float,
) -> AcquiredFixtureFile:
    """Execute one injected transfer into repository-only fixture staging."""
    writer = staging.begin_stream(
        filename=request.filename,
        maximum_bytes=request.maximum_bytes,
    )
    try:
        transfer = download_bounded(
            request,
            opener=opener,
            consume=writer.write,
            timeout_seconds=timeout_seconds,
        )
        staged = writer.finalize(
            expected_bytes=transfer.bytes_received,
            expected_sha256=transfer.sha256,
        )
        if (
            staged.bytes_written != transfer.bytes_received
            or staged.sha256 != transfer.sha256
            or staged.filename != transfer.filename
        ):
            raise StagingError("published fixture evidence disagrees with transfer")
        return AcquiredFixtureFile(transfer, staged)
    finally:
        writer.close()
