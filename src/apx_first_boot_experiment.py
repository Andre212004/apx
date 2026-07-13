"""Execute and attest the exact authorized first APX console boot preview."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

from apx_first_boot_preview import FINAL_REPORT_DIGEST, MACHINE, build_preview, fixed_command
from apx_offline_base_build import ROOT, ROOTFS


AUTHORIZED_PREVIEW = "53c30a3c55c1a6b5b196d9f73694b3b6851e7cab84fdcd6f4bcace24bdb91944"
FINAL_REPORT = ROOT / "final-report.json"
OUTPUT_LIMIT = 4 * 1024**2


class FirstBootExperimentError(RuntimeError):
    """The authorized boot could not start or left uncertain runtime state."""


@dataclass(frozen=True)
class FirstBootReport:
    schema_version: int
    preview_digest: str
    machine: str
    process_exit_code: int
    timed_out_as_planned: bool
    systemd_started: bool
    multi_user_reached: bool
    clean_shutdown_observed: bool
    source_report_unchanged: bool
    matching_processes_after: int
    matching_mounts_after: int
    output_sha256: str
    output_bytes: int
    report_digest: str


def _final_report_bytes() -> bytes:
    content = FINAL_REPORT.read_bytes()
    payload = json.loads(content)
    if payload.get("final_report_digest") != FINAL_REPORT_DIGEST:
        raise FirstBootExperimentError("final root report identity changed")
    return content


def _runtime_residue() -> tuple[int, int]:
    processes = 0
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            command = (entry / "cmdline").read_bytes().replace(b"\0", b" ")
        except (OSError, PermissionError):
            continue
        if MACHINE.encode() in command and b"apx_first_boot_experiment" not in command:
            processes += 1
    mounts = 0
    for line in Path("/proc/self/mountinfo").read_text(encoding="utf-8").splitlines():
        if str(ROOTFS) in line or MACHINE in line:
            mounts += 1
    return processes, mounts


def execute_first_boot() -> FirstBootReport:
    if os.geteuid() != 0:
        raise FirstBootExperimentError("the bounded namespace experiment requires administrator execution")
    preview = build_preview()
    if preview.preview_digest != AUTHORIZED_PREVIEW or preview.command != fixed_command():
        raise FirstBootExperimentError("authorized preview identity changed")
    before = _final_report_bytes()
    if _runtime_residue() != (0, 0):
        raise FirstBootExperimentError("matching runtime state exists before boot")
    result = subprocess.run(
        preview.command, shell=False, stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=150,
        env={"LC_ALL": "C", "PATH": "/usr/bin"}, check=False,
    )
    output = result.stdout
    if len(output) > OUTPUT_LIMIT:
        raise FirstBootExperimentError("bounded boot output exceeded policy")
    deadline = time.monotonic() + 15
    residue = _runtime_residue()
    while residue != (0, 0) and time.monotonic() < deadline:
        time.sleep(0.25)
        residue = _runtime_residue()
    after = _final_report_bytes()
    text = output.decode("utf-8", "replace")
    systemd_started = any(marker in text for marker in ("systemd 261", "Welcome to Arch Linux", "systemd[1]"))
    multi_user = any(marker in text for marker in ("Reached target Multi-User System", "Reached target multi-user.target"))
    clean = any(marker in text for marker in ("Reached target System Power Off", "Powering off", "Shutting down"))
    draft = {
        "schema_version": 1, "preview_digest": preview.preview_digest,
        "machine": MACHINE, "process_exit_code": result.returncode,
        "timed_out_as_planned": result.returncode == 124,
        "systemd_started": systemd_started, "multi_user_reached": multi_user,
        "clean_shutdown_observed": clean, "source_report_unchanged": before == after,
        "matching_processes_after": residue[0], "matching_mounts_after": residue[1],
        "output_sha256": hashlib.sha256(output).hexdigest(), "output_bytes": len(output),
    }
    digest = hashlib.sha256(json.dumps(draft, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    report = FirstBootReport(**draft, report_digest=digest)
    descriptor = os.open(ROOT / "first-boot-report-v2.json", os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        os.write(descriptor, (json.dumps(asdict(report), sort_keys=True, indent=2) + "\n").encode())
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    output_path = ROOT / "first-boot-output-v2.log"
    descriptor = os.open(output_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        os.write(descriptor, output)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    if residue != (0, 0) or before != after:
        raise FirstBootExperimentError("boot ended with runtime residue or source change")
    return report


def main() -> int:
    report = execute_first_boot()
    print("APX first bounded console boot")
    print(f"Exit code: {report.process_exit_code}")
    print(f"Systemd started: {report.systemd_started}")
    print(f"Multi-user reached: {report.multi_user_reached}")
    print(f"Clean shutdown observed: {report.clean_shutdown_observed}")
    print(f"Processes after: {report.matching_processes_after}")
    print(f"Mounts after: {report.matching_mounts_after}")
    print(f"Source unchanged: {report.source_report_unchanged}")
    print(f"Report digest: {report.report_digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
