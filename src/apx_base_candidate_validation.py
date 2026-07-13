"""Read-only admission assessment for the disposable APX base candidate."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path

from apx_base_extraction import ROOT as EXTRACTION_ROOT, ROOTFS, _tree_measurement


ROOT = Path("/tmp/apx-base-candidate-validation-20260711-v1")
RECEIPT = EXTRACTION_ROOT / "extraction-receipt.json"
AUTHORIZED_RECEIPT = "e415c0040a56ef51a8f94a8cf6814ca4ddc3651a8beb2ba9511feee1c493ae7e"
REQUIRED = ("usr/lib/systemd/systemd", "usr/bin/bash", "usr/bin/pacman", "usr/lib/os-release", "etc/passwd", "etc/group", "etc/shadow")
MACHINE_LOCAL = ("etc/machine-id", "var/lib/dbus/machine-id", "var/lib/systemd/random-seed", "etc/hostname")


class CandidateValidationError(RuntimeError):
    """Candidate evidence is unavailable or has changed."""


@dataclass(frozen=True)
class CandidateAssessment:
    status: str
    passed: tuple[str, ...]
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]
    observed_uid_counts: tuple[tuple[int, int], ...]
    observed_gid_counts: tuple[tuple[int, int], ...]
    tree_digest: str
    assessment_digest: str


def _load_receipt() -> dict:
    try:
        payload = json.loads(RECEIPT.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise CandidateValidationError("extraction receipt is unavailable") from error
    digest = payload.pop("receipt_digest", None)
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    if digest != AUTHORIZED_RECEIPT or hashlib.sha256(canonical.encode()).hexdigest() != digest:
        raise CandidateValidationError("extraction receipt identity changed")
    return payload


def assess_candidate(*, rootfs: Path = ROOTFS) -> CandidateAssessment:
    receipt = _load_receipt()
    regular, directories, symlinks, logical, allocated, tree_digest = _tree_measurement(rootfs)
    observed = (regular, directories, symlinks, logical, allocated, tree_digest)
    expected = tuple(receipt[key] for key in (
        "regular_file_count", "directory_count", "symlink_count", "logical_bytes",
        "allocated_bytes", "rootfs_tree_digest",
    ))
    if observed != expected:
        raise CandidateValidationError("candidate tree changed after extraction")
    passed = ["all extracted bytes and paths still match the closed receipt"]
    missing = [relative for relative in REQUIRED if not (rootfs / relative).exists()]
    if missing:
        raise CandidateValidationError("candidate lacks a required base component")
    passed.append("systemd, Bash, pacman, Arch identity, and root account files are present")
    residue = [relative for relative in MACHINE_LOCAL if (rootfs / relative).exists() or (rootfs / relative).is_symlink()]
    if residue:
        raise CandidateValidationError("candidate contains machine-local identity residue")
    passed.append("machine identity, hostname, and random seed are absent")
    uid_counts: dict[int, int] = {}; gid_counts: dict[int, int] = {}
    for directory, names, files in os.walk(rootfs, followlinks=False):
        for name in names + files:
            info = (Path(directory) / name).lstat()
            uid_counts[info.st_uid] = uid_counts.get(info.st_uid, 0) + 1
            gid_counts[info.st_gid] = gid_counts.get(info.st_gid, 0) + 1
    blockers = []
    if set(uid_counts) != {0} or set(gid_counts) != {0}:
        blockers.append("filesystem ownership is a development fixture, not final root ownership")
    local_db = rootfs / "var/lib/pacman/local"
    if not local_db.is_dir() or not any(local_db.iterdir()):
        blockers.append("pacman has no installed-package database for this filesystem")
    blockers.append("candidate has not passed an isolated boot and verified shutdown")
    blockers.append("no generation-bound Environment identity or disposable lifecycle record exists")
    warnings = (
        "this is a minimal console base; Hyprland and the APX graphical shell are not included",
        "network, GPU, audio, input, portals, and graphical session handoff remain untested",
    )
    draft = {
        "status": "not-admitted" if blockers else "admitted",
        "passed": tuple(passed), "blockers": tuple(blockers), "warnings": warnings,
        "observed_uid_counts": tuple(sorted(uid_counts.items())),
        "observed_gid_counts": tuple(sorted(gid_counts.items())), "tree_digest": tree_digest,
    }
    digest = hashlib.sha256(json.dumps(draft, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return CandidateAssessment(**draft, assessment_digest=digest)


def main() -> int:
    try:
        os.mkdir(ROOT, 0o700)
    except FileExistsError as error:
        raise CandidateValidationError("validation root exists; refusing adoption") from error
    assessment = assess_candidate()
    payload = asdict(assessment)
    path = ROOT / "candidate-assessment.json"
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        os.write(descriptor, (json.dumps(payload, sort_keys=True, indent=2) + "\n").encode())
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    print("APX disposable base candidate assessment")
    print(f"Status: {assessment.status}")
    print(f"Passed checks: {len(assessment.passed)}")
    print(f"Blocking items: {len(assessment.blockers)}")
    for item in assessment.blockers:
        print(f"BLOCKED: {item}")
    print(f"Assessment digest: {assessment.assessment_digest}")
    print("System changes/boot/execution: none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
