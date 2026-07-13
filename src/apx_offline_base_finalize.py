"""Finalize and attest the already-built first offline APX console root."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess

from apx_package_acquisition import AUTHORIZED_MANIFEST
from apx_package_metadata import AUTHORIZED_SIGNATURE_EVIDENCE
from apx_offline_base_build import GPGDIR, PACMAN_DB, ROOT, ROOTFS, EXPECTED_PACKAGES, MAX_BYTES


BUILD_REPORT_FIELDS = {
    "schema_version", "manifest_digest", "signature_evidence_digest",
    "package_count", "local_database_count", "logical_bytes",
    "allocated_bytes", "development_uid_entries",
    "machine_identity_present", "report_digest",
}


class OfflineBaseFinalizeError(RuntimeError):
    """The built root cannot be safely finalized or attested."""


@dataclass(frozen=True)
class OfflineBaseFinalReport:
    schema_version: int
    build_report_digest: str
    package_database_count: int
    logical_bytes: int
    allocated_bytes: int
    machine_identity_sha256: str
    development_uid_entries: int
    special_file_count: int
    final_report_digest: str


def _measure() -> tuple[int, int, int, int]:
    logical = allocated = development = special = 0
    seen = set()
    for directory, names, files in os.walk(ROOTFS, followlinks=False):
        for name in names + files:
            path = Path(directory) / name
            info = path.lstat()
            if info.st_uid == 1002:
                development += 1
            if stat.S_ISREG(info.st_mode):
                identity = (info.st_dev, info.st_ino)
                if identity not in seen:
                    seen.add(identity); logical += info.st_size; allocated += info.st_blocks * 512
            elif not stat.S_ISDIR(info.st_mode) and not stat.S_ISLNK(info.st_mode):
                special += 1
    return logical, allocated, development, special


def _validated_build_report() -> str:
    try:
        build = json.loads((ROOT / "build-report.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise OfflineBaseFinalizeError("build report is unavailable") from error
    if not isinstance(build, dict) or set(build) != BUILD_REPORT_FIELDS:
        raise OfflineBaseFinalizeError("build report schema changed")
    report_digest = build.pop("report_digest")
    canonical = json.dumps(build, sort_keys=True, separators=(",", ":"))
    if not isinstance(report_digest, str) or hashlib.sha256(canonical.encode()).hexdigest() != report_digest:
        raise OfflineBaseFinalizeError("build report digest is invalid")
    integers = ("package_count", "local_database_count", "logical_bytes", "allocated_bytes", "development_uid_entries")
    if any(not isinstance(build[field], int) or isinstance(build[field], bool) for field in integers):
        raise OfflineBaseFinalizeError("build report numbers are invalid")
    if (
        build["schema_version"] != 1
        or build["manifest_digest"] != AUTHORIZED_MANIFEST
        or build["signature_evidence_digest"] != AUTHORIZED_SIGNATURE_EVIDENCE
        or build["package_count"] != EXPECTED_PACKAGES
        or build["local_database_count"] != EXPECTED_PACKAGES
        or not 0 < build["logical_bytes"] <= MAX_BYTES
        or not 0 < build["allocated_bytes"] <= MAX_BYTES
        or build["development_uid_entries"] != 0
        or build["machine_identity_present"] is not True
    ):
        raise OfflineBaseFinalizeError("build report invariants are not satisfied")
    return report_digest


def finalize_offline_base() -> OfflineBaseFinalReport:
    if os.geteuid() != 0:
        raise OfflineBaseFinalizeError("finalization requires ownership-visible execution")
    build_report_digest = _validated_build_report()
    subprocess.run(
        ("/usr/bin/gpgconf", "--homedir", str(GPGDIR), "--kill", "all"),
        shell=False, stdin=subprocess.DEVNULL, capture_output=True, timeout=30,
        env={"LC_ALL": "C", "PATH": "/usr/bin"}, check=False,
    )
    for path in GPGDIR.glob("S.gpg-agent*"):
        if not stat.S_ISSOCK(path.lstat().st_mode):
            raise OfflineBaseFinalizeError("unexpected GPG runtime entry type")
        path.unlink()
    machine_id = (ROOTFS / "etc/machine-id").read_text(encoding="ascii")
    value = machine_id.strip()
    if len(value) != 32 or any(character not in "0123456789abcdef" for character in value):
        raise OfflineBaseFinalizeError("generated Environment identity is malformed")
    packages = sum(1 for path in (PACMAN_DB / "local").iterdir() if path.is_dir())
    logical, allocated, development, special = _measure()
    if packages != EXPECTED_PACKAGES or logical > MAX_BYTES or allocated > MAX_BYTES or development or special:
        raise OfflineBaseFinalizeError("final root invariants are not satisfied")
    draft = {
        "schema_version": 1, "build_report_digest": build_report_digest,
        "package_database_count": packages, "logical_bytes": logical,
        "allocated_bytes": allocated,
        "machine_identity_sha256": hashlib.sha256(machine_id.encode()).hexdigest(),
        "development_uid_entries": development, "special_file_count": special,
    }
    digest = hashlib.sha256(json.dumps(draft, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    report = OfflineBaseFinalReport(**draft, final_report_digest=digest)
    descriptor = os.open(ROOT / "final-report.json", os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        os.write(descriptor, (json.dumps(asdict(report), sort_keys=True, indent=2) + "\n").encode())
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return report


def main() -> int:
    report = finalize_offline_base()
    print("APX first console root finalization")
    print(f"Packages recorded internally: {report.package_database_count}")
    print(f"Allocated bytes: {report.allocated_bytes}")
    print(f"Development-owner entries: {report.development_uid_entries}")
    print(f"Special runtime entries: {report.special_file_count}")
    print(f"Final report digest: {report.final_report_digest}")
    print("Boot/network/download/host-account/service/Btrfs/previous-area cleanup effects: none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
