"""Pure boundary validator for the fixed APX Arch base acquisition."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import posixpath
import re
from typing import Sequence
from urllib.parse import unquote, urlsplit


ARCHIVE_ORIGIN = "https://archive.archlinux.org"
ARCHIVE_PREFIX = "/repos/2026/07/11/"
REPOSITORIES = ("core", "extra")
ARCHITECTURES = ("any", "x86_64")
DATABASE_MAX = 64 * 1024**2
PACKAGE_MAX = 1024**3
AGGREGATE_MAX = 4 * 1024**3
FILE_COUNT_MAX = 1028
_FILENAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9@+_.:-]{0,254}")
_SHA256 = re.compile(r"[0-9a-f]{64}")


@dataclass(frozen=True)
class AcquisitionItem:
    kind: str
    repository: str
    architecture: str
    filename: str
    uri: str
    expected_bytes: int
    expected_sha256: str | None


@dataclass(frozen=True)
class ObservedTransfer:
    requested_uri: str
    final_uri: str
    filename: str
    bytes_received: int
    sha256: str
    regular_file: bool
    symlink: bool
    complete: bool


@dataclass(frozen=True)
class AcquisitionBoundaryDecision:
    decision: str
    issues: tuple[str, ...]
    aggregate_expected_bytes: int
    manifest_digest: str


def _safe_uri(uri: str, repository: str, architecture: str, filename: str) -> bool:
    if not all(isinstance(value, str) for value in (uri, repository, architecture, filename)):
        return False
    parsed = urlsplit(uri)
    if parsed.scheme != "https" or parsed.netloc != "archive.archlinux.org":
        return False
    if parsed.username or parsed.password or parsed.port or parsed.query or parsed.fragment:
        return False
    try:
        decoded = unquote(parsed.path, errors="strict")
    except (UnicodeError, ValueError):
        return False
    expected = f"{ARCHIVE_PREFIX}{repository}/os/x86_64/{filename}"
    return decoded == expected and posixpath.normpath(decoded) == decoded


def _manifest_digest(items: Sequence[AcquisitionItem]) -> str:
    rows = "\n".join(
        "|".join(
            (
                item.kind,
                item.repository,
                item.architecture,
                item.filename,
                item.uri,
                str(item.expected_bytes),
                item.expected_sha256 or "",
            )
        )
        for item in items
    )
    return hashlib.sha256(rows.encode("utf-8")).hexdigest()


def assess_acquisition_manifest(
    items: Sequence[AcquisitionItem],
) -> AcquisitionBoundaryDecision:
    issues: list[str] = []
    if isinstance(items, (str, bytes)) or not isinstance(items, Sequence):
        return AcquisitionBoundaryDecision("blocked", ("manifest has wrong type",), 0, "0" * 64)
    items_tuple = tuple(items)
    if not items_tuple or len(items_tuple) > FILE_COUNT_MAX:
        return AcquisitionBoundaryDecision("blocked", ("manifest file count is outside policy",), 0, "0" * 64)
    filenames: set[str] = set()
    aggregate = 0
    previous_key: tuple[str, str, str] | None = None
    for item in items_tuple:
        if type(item) is not AcquisitionItem:
            issues.append("manifest contains an invalid item")
            continue
        if item.kind not in {"database", "package", "signature"}:
            issues.append(f"unknown item kind for {item.filename}")
        if item.repository not in REPOSITORIES:
            issues.append(f"repository is not allowed for {item.filename}")
        if item.architecture not in ARCHITECTURES:
            issues.append(f"architecture is not allowed for {item.filename}")
        if not _FILENAME.fullmatch(item.filename) or item.filename in {".", ".."}:
            issues.append("unsafe acquisition filename")
        if item.filename in filenames:
            issues.append(f"duplicate filename: {item.filename}")
        filenames.add(item.filename)
        if not _safe_uri(item.uri, item.repository, item.architecture, item.filename):
            issues.append(f"URI is outside fixed archive policy for {item.filename}")
        if type(item.expected_bytes) is not int or item.expected_bytes < 0:
            issues.append(f"invalid expected size for {item.filename}")
        else:
            maximum = DATABASE_MAX if item.kind == "database" else PACKAGE_MAX
            if item.expected_bytes > maximum:
                issues.append(f"per-file size limit exceeded for {item.filename}")
            aggregate += item.expected_bytes
        if item.expected_sha256 is not None and (
            not isinstance(item.expected_sha256, str)
            or not _SHA256.fullmatch(item.expected_sha256)
        ):
            issues.append(f"invalid expected digest for {item.filename}")
        key = (item.repository, item.kind, item.filename)
        if previous_key is not None and key <= previous_key:
            issues.append("manifest is not uniquely canonically ordered")
        previous_key = key
    if aggregate > AGGREGATE_MAX:
        issues.append("aggregate acquisition limit exceeded")
    return AcquisitionBoundaryDecision(
        "accepted-boundary-only" if not issues else "blocked",
        tuple(issues),
        aggregate,
        _manifest_digest(items_tuple) if all(type(item) is AcquisitionItem for item in items_tuple) else "0" * 64,
    )


def verify_transfer(item: AcquisitionItem, observed: ObservedTransfer) -> tuple[str, ...]:
    """Verify supplied post-download evidence; never opens or downloads a file."""
    issues: list[str] = []
    if type(item) is not AcquisitionItem or type(observed) is not ObservedTransfer:
        return ("transfer evidence has wrong type",)
    if observed.requested_uri != item.uri or observed.final_uri != item.uri:
        issues.append("redirect or requested URI mismatch")
    if observed.filename != item.filename:
        issues.append("transfer filename mismatch")
    if type(observed.bytes_received) is not int or observed.bytes_received != item.expected_bytes:
        issues.append("transfer byte count mismatch")
    if not isinstance(observed.sha256, str) or not _SHA256.fullmatch(observed.sha256):
        issues.append("transfer digest is malformed")
    elif item.expected_sha256 is not None and observed.sha256 != item.expected_sha256:
        issues.append("transfer digest mismatch")
    if type(observed.regular_file) is not bool or not observed.regular_file:
        issues.append("transfer result is not a regular file")
    if type(observed.symlink) is not bool or observed.symlink:
        issues.append("transfer result is or may be a symlink")
    if type(observed.complete) is not bool or not observed.complete:
        issues.append("transfer is incomplete")
    return tuple(issues)
