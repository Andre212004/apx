"""Bounded HTTPS transfer contract with an injected, non-redirecting opener."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re
from typing import Callable
from urllib.parse import unquote, urlsplit


ARCHIVE_HOST = "archive.archlinux.org"
ARCHIVE_PREFIX = "/repos/2026/07/11/"
CHUNK_BYTES = 64 * 1024
_SHA256 = re.compile(r"[0-9a-f]{64}")
_FILENAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9@+_.:-]{0,254}")


class DownloadError(RuntimeError):
    """A transfer crossed policy or produced ambiguous evidence."""


@dataclass(frozen=True)
class DownloadRequest:
    uri: str
    filename: str
    maximum_bytes: int
    expected_bytes: int | None
    expected_sha256: str | None


@dataclass(frozen=True)
class DownloadResult:
    requested_uri: str
    final_uri: str
    filename: str
    bytes_received: int
    sha256: str
    status: int
    content_length: int


def validate_download_request(request: DownloadRequest) -> None:
    if type(request) is not DownloadRequest:
        raise DownloadError("download request has wrong type")
    if not _FILENAME.fullmatch(request.filename):
        raise DownloadError("unsafe download filename")
    parsed = urlsplit(request.uri)
    if (
        parsed.scheme != "https"
        or parsed.hostname != ARCHIVE_HOST
        or parsed.netloc != ARCHIVE_HOST
        or parsed.query
        or parsed.fragment
        or not unquote(parsed.path).startswith(ARCHIVE_PREFIX)
        or unquote(parsed.path).rsplit("/", 1)[-1] != request.filename
    ):
        raise DownloadError("download URI is outside fixed archive policy")
    if type(request.maximum_bytes) is not int or request.maximum_bytes <= 0:
        raise DownloadError("invalid download maximum")
    if request.expected_bytes is not None:
        if type(request.expected_bytes) is not int or not 0 <= request.expected_bytes <= request.maximum_bytes:
            raise DownloadError("invalid expected download size")
    if request.expected_sha256 is not None and (
        not isinstance(request.expected_sha256, str)
        or not _SHA256.fullmatch(request.expected_sha256)
    ):
        raise DownloadError("invalid expected download digest")


def _content_length(headers: object) -> int:
    getter = getattr(headers, "get", None)
    if not callable(getter):
        raise DownloadError("response headers cannot be read safely")
    raw = getter("Content-Length")
    if raw is None or not isinstance(raw, str) or not raw.isascii() or not raw.isdigit():
        raise DownloadError("response has no single valid Content-Length")
    value = int(raw)
    if value < 0:
        raise DownloadError("response Content-Length is invalid")
    return value


def download_bounded(
    request: DownloadRequest,
    *,
    opener: Callable[[str, float], object],
    consume: Callable[[bytes], None],
    timeout_seconds: float,
) -> DownloadResult:
    """Stream one response to a supplied sink; never creates a file itself."""
    validate_download_request(request)
    if type(timeout_seconds) not in {int, float} or not 0 < timeout_seconds <= 300:
        raise DownloadError("download timeout is outside policy")
    if not callable(opener) or not callable(consume):
        raise DownloadError("download boundary callback is invalid")
    try:
        response = opener(request.uri, float(timeout_seconds))
    except Exception as error:
        raise DownloadError("download could not be opened") from error
    close = getattr(response, "close", None)
    try:
        status = getattr(response, "status", None)
        final_uri = getattr(response, "geturl", lambda: None)()
        headers = getattr(response, "headers", None)
        read = getattr(response, "read", None)
        if type(status) is not int or status != 200:
            raise DownloadError("download response status is not 200")
        if final_uri != request.uri:
            raise DownloadError("download redirect or final URI mismatch")
        if not callable(getattr(headers, "get", None)):
            raise DownloadError("download response headers are unavailable")
        length = _content_length(headers)
        if length > request.maximum_bytes:
            raise DownloadError("response exceeds approved maximum")
        if request.expected_bytes is not None and length != request.expected_bytes:
            raise DownloadError("response length disagrees with approved size")
        if not callable(read):
            raise DownloadError("download response is not readable")
        digest = hashlib.sha256()
        received = 0
        while True:
            try:
                chunk = read(CHUNK_BYTES)
            except Exception as error:
                raise DownloadError("download read failed") from error
            if not isinstance(chunk, bytes):
                raise DownloadError("download returned non-byte content")
            if not chunk:
                break
            received += len(chunk)
            if received > length or received > request.maximum_bytes:
                raise DownloadError("download exceeded declared or approved size")
            try:
                consume(chunk)
            except Exception as error:
                raise DownloadError("protected staging rejected download bytes") from error
            digest.update(chunk)
        if received != length:
            raise DownloadError("download ended before declared size")
        actual_digest = digest.hexdigest()
        if request.expected_sha256 is not None and actual_digest != request.expected_sha256:
            raise DownloadError("download digest mismatch")
        return DownloadResult(
            request.uri,
            final_uri,
            request.filename,
            received,
            actual_digest,
            status,
            length,
        )
    finally:
        if callable(close):
            close()
