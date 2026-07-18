"""Finalize the fixed temporary Hyprland root into identity-neutral evidence."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat

from apx_hyprland_offline_build import (
    AUTHORIZED_METADATA,
    AUTHORIZED_SIGNATURE_EVIDENCE,
    EXPECTED_BASE_PACKAGES,
    EXPECTED_ROLE_PACKAGES,
    EXPECTED_TOTAL_PACKAGES,
    GPGDIR,
    ROOT,
    ROOTFS,
)
from apx_graphical_acquisition import AUTHORIZED_MANIFEST


REPORT_PATH = ROOT / "final-release-report.json"
MACHINE_ID = ROOTFS / "etc/machine-id"
PACMAN_LOG = ROOTFS / "var/log/pacman.log"
LOCAL_DB = ROOTFS / "var/lib/pacman/local"
MAX_TREE_BYTES = 3 * 1024**3
BUILD_REPORT_FIELDS = {
    "schema_version", "manifest_digest", "signature_evidence_digest",
    "metadata_digest", "base_package_count", "role_package_count",
    "final_package_count", "logical_bytes", "allocated_bytes",
    "source_before_digest", "source_after_digest", "development_uid_entries",
    "special_file_count", "report_digest",
}


class HyprlandReleaseFinalizeError(RuntimeError):
    """The temporary graphical root is unsafe, changed, or not finalizable."""


@dataclass(frozen=True)
class HyprlandReleaseFinalReport:
    schema_version: int
    build_report_digest: str
    package_count: int
    logical_bytes: int
    allocated_bytes: int
    tree_digest: str
    machine_identity_empty: bool
    pacman_log_empty: bool
    install_dates_normalized: int
    pacman_trust_entries: int
    private_key_entries: int
    random_seed_entries: int
    development_uid_entries: int
    special_file_count: int
    report_digest: str


def _canonical_digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _validated_build_report() -> str:
    try:
        report = json.loads((ROOT / "build-report.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise HyprlandReleaseFinalizeError("graphical build report is unavailable") from error
    if not isinstance(report, dict) or set(report) != BUILD_REPORT_FIELDS:
        raise HyprlandReleaseFinalizeError("graphical build report schema changed")
    claimed = report.pop("report_digest")
    if not isinstance(claimed, str) or claimed != _canonical_digest(report):
        raise HyprlandReleaseFinalizeError("graphical build report digest is invalid")
    if (
        report["schema_version"] != 1
        or report["manifest_digest"] != AUTHORIZED_MANIFEST
        or report["signature_evidence_digest"] != AUTHORIZED_SIGNATURE_EVIDENCE
        or report["metadata_digest"] != AUTHORIZED_METADATA
        or report["base_package_count"] != EXPECTED_BASE_PACKAGES
        or report["role_package_count"] != EXPECTED_ROLE_PACKAGES
        or report["final_package_count"] != EXPECTED_TOTAL_PACKAGES
        or report["source_before_digest"] != report["source_after_digest"]
        or report["development_uid_entries"] != 0
        or report["special_file_count"] != 0
    ):
        raise HyprlandReleaseFinalizeError("graphical build report invariants failed")
    return claimed


def normalize_local_database_desc(text: str) -> tuple[str, int]:
    if not isinstance(text, str) or not text:
        raise HyprlandReleaseFinalizeError("package database description is empty")
    lines = text.splitlines(keepends=True)
    matches = [index for index, line in enumerate(lines) if line == "%INSTALLDATE%\n"]
    if len(matches) != 1 or matches[0] + 2 >= len(lines):
        raise HyprlandReleaseFinalizeError("package install date field is malformed")
    index = matches[0] + 1
    if not lines[index].removesuffix("\n").isdigit() or lines[index + 1] != "\n":
        raise HyprlandReleaseFinalizeError("package install date value is malformed")
    lines[index] = "0\n"
    return "".join(lines), 1


def _rewrite_regular(path: Path, content: bytes, mode: int) -> None:
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or info.st_gid != 0:
        raise HyprlandReleaseFinalizeError("normalization target is not a root-owned regular file")
    temporary = path.with_name("." + path.name + ".apx-finalize")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode)
    try:
        os.write(descriptor, content)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    os.replace(temporary, path)


def _measure_tree() -> tuple[int, int, int, int, str]:
    logical = allocated = development = special = 0
    digest = hashlib.sha256()
    for directory, names, files in os.walk(ROOTFS, topdown=True, followlinks=False):
        names.sort(); files.sort()
        for name in names + files:
            path = Path(directory) / name
            info = path.lstat()
            relative = path.relative_to(ROOTFS).as_posix()
            kind = stat.S_IFMT(info.st_mode)
            digest.update(
                f"{relative}\0{kind:o}\0{stat.S_IMODE(info.st_mode):o}\0{info.st_uid}\0{info.st_gid}\0{info.st_size}\0".encode()
            )
            if info.st_uid == 1002:
                development += 1
            if stat.S_ISREG(info.st_mode):
                logical += info.st_size; allocated += info.st_blocks * 512
                with path.open("rb") as stream:
                    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                        digest.update(chunk)
            elif stat.S_ISLNK(info.st_mode):
                digest.update(os.readlink(path).encode())
            elif not stat.S_ISDIR(info.st_mode):
                special += 1
    return logical, allocated, development, special, digest.hexdigest()


def finalize_hyprland_release() -> HyprlandReleaseFinalReport:
    if os.geteuid() != 0:
        raise HyprlandReleaseFinalizeError("graphical finalization requires ownership-visible execution")
    build_digest = _validated_build_report()
    if REPORT_PATH.exists() or not ROOTFS.is_dir() or ROOTFS.is_symlink():
        raise HyprlandReleaseFinalizeError("graphical finalization destination or root is unsafe")
    if not GPGDIR.is_dir() or GPGDIR.is_symlink() or GPGDIR.parent != ROOTFS / "etc/pacman.d":
        raise HyprlandReleaseFinalizeError("temporary pacman trust root is unsafe")
    shutil.rmtree(GPGDIR)
    GPGDIR.mkdir(mode=0o700)
    _rewrite_regular(MACHINE_ID, b"", 0o444)
    _rewrite_regular(PACMAN_LOG, b"", 0o600)
    normalized = 0
    entries = sorted(path for path in LOCAL_DB.iterdir() if path.is_dir() and not path.is_symlink())
    if len(entries) != EXPECTED_TOTAL_PACKAGES:
        raise HyprlandReleaseFinalizeError("graphical package database count changed")
    for entry in entries:
        desc = entry / "desc"
        content, count = normalize_local_database_desc(desc.read_text(encoding="utf-8"))
        _rewrite_regular(desc, content.encode("utf-8"), stat.S_IMODE(desc.stat().st_mode))
        normalized += count
    logical, allocated, development, special, tree_digest = _measure_tree()
    private_keys = sum(1 for path in ROOTFS.rglob("*") if "private-keys-v1.d" in path.parts or path.name == "secring.gpg")
    random_seeds = sum(1 for path in ROOTFS.rglob("random-seed"))
    trust_entries = sum(1 for _ in GPGDIR.iterdir())
    if (
        logical > MAX_TREE_BYTES or allocated > MAX_TREE_BYTES or development or special
        or MACHINE_ID.read_bytes() != b"" or PACMAN_LOG.read_bytes() != b""
        or normalized != EXPECTED_TOTAL_PACKAGES or trust_entries or private_keys or random_seeds
    ):
        raise HyprlandReleaseFinalizeError("normalized graphical root invariants failed")
    draft = {
        "schema_version": 1, "build_report_digest": build_digest,
        "package_count": len(entries), "logical_bytes": logical,
        "allocated_bytes": allocated, "tree_digest": tree_digest,
        "machine_identity_empty": True, "pacman_log_empty": True,
        "install_dates_normalized": normalized, "pacman_trust_entries": trust_entries,
        "private_key_entries": private_keys, "random_seed_entries": random_seeds,
        "development_uid_entries": development, "special_file_count": special,
    }
    report = HyprlandReleaseFinalReport(**draft, report_digest=_canonical_digest(draft))
    descriptor = os.open(REPORT_PATH, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        os.write(descriptor, (json.dumps(asdict(report), sort_keys=True, indent=2) + "\n").encode())
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return report


def main() -> int:
    report = finalize_hyprland_release()
    print("APX finalized temporary Hyprland release")
    print(f"Packages: {report.package_count}")
    print(f"Tree digest: {report.tree_digest}")
    print(f"Private-key/random-seed/trust entries: {report.private_key_entries}/{report.random_seed_entries}/{report.pacman_trust_entries}")
    print(f"Report digest: {report.report_digest}")
    print("Host/APX/GPU/input/service/release-promotion effects: none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
