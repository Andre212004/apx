#!/usr/bin/env python3
"""Coordinate exact Environment shutdown before asking Host logind for power."""

from __future__ import annotations

import argparse
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import time

LOCK = Path("/run/apx/machine-transition-v1.lock")
RESERVATION = Path("/run/apx/system-power-v1.reserved")
STATUS = Path("/var/lib/apx/system-power-v1/status.json")
HUB_RECOVERY = "/var/lib/apx/official-hub-v1/apx-official-hub-graphical-v1.py"
HUB_AUTOSTART_UNIT = "apx-official-hub-autostart-v1.service"


def atomic(value: dict[str, object]) -> None:
    temporary = STATUS.with_name(f".{STATUS.name}.{os.getpid()}.tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try: os.write(descriptor, (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()); os.fsync(descriptor)
    finally: os.close(descriptor)
    os.replace(temporary, STATUS)


def run(arguments: tuple[str, ...]) -> None:
    result = subprocess.run(arguments, text=True, capture_output=True, check=False,
                            env={"PATH": "/usr/bin", "LC_ALL": "C"})
    if result.returncode: raise RuntimeError((result.stderr or result.stdout or "operation failed")[-800:])


def update_active() -> bool:
    candidates = sorted(Path("/var/lib/apx/coordinated-updates-v1/operations").glob("*/status.json"), reverse=True)
    if not candidates: return False
    try: return json.loads(candidates[0].read_text()).get("state") in {"preparing", "staged", "applying"}
    except (OSError, json.JSONDecodeError): return True


def transition_inhibited(action: str) -> bool:
    result = subprocess.run(("/usr/bin/systemd-inhibit", "--list", "--mode=block", "--no-legend"),
                            text=True, capture_output=True, check=False,
                            env={"PATH": "/usr/bin", "LC_ALL": "C"})
    kind = "sleep" if action == "suspend" else "shutdown"
    return result.returncode != 0 or any(kind in line.lower() for line in result.stdout.splitlines() if line.strip())


def hub_launcher_supervisors(proc: Path = Path("/proc")) -> tuple[tuple[int, str], ...]:
    supervisors = []
    for entry in proc.iterdir():
        if not entry.name.isdigit():
            continue
        try:
            arguments = (entry / "cmdline").read_bytes().rstrip(b"\0").split(b"\0")
            status = dict(line.split(":", 1) for line in (entry / "status").read_text().splitlines() if ":" in line)
            cgroup = (entry / "cgroup").read_text()
        except (OSError, KeyError):
            continue
        if arguments[1:] == [HUB_RECOVERY.encode(), b"--interactive"] \
                and status.get("Uid", "").split() == ["0", "0", "0", "0"]:
            supervisors.append((int(entry.name), cgroup))
    if len(supervisors) > 1:
        raise RuntimeError("multiple official Hub launch supervisors exist")
    return tuple(supervisors)


def quiesce_hub_launcher() -> None:
    supervisors = hub_launcher_supervisors()
    if not supervisors:
        return
    pid, cgroup = supervisors[0]
    if f"/{HUB_AUTOSTART_UNIT}" in cgroup:
        run(("/usr/bin/systemctl", "stop", HUB_AUTOSTART_UNIT))
    else:
        os.kill(pid, signal.SIGTERM)
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline and Path(f"/proc/{pid}").exists():
        time.sleep(0.05)
    if Path(f"/proc/{pid}").exists():
        raise RuntimeError("official Hub launch supervisor did not stop")


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--action", required=True, choices=("reboot", "poweroff", "suspend")); args = parser.parse_args()
    LOCK.touch(mode=0o600, exist_ok=True); descriptor = os.open(LOCK, os.O_RDWR | os.O_NOFOLLOW)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB); RESERVATION.unlink(missing_ok=True)
        if update_active(): raise RuntimeError("coordinated update became active")
        if transition_inhibited(args.action): raise RuntimeError("a Host power inhibitor became active")
        if args.action == "suspend":
            atomic({"schema": 1, "profile": "apx-system-power-v1", "state": "committed", "action": args.action})
            run(("/usr/bin/loginctl", "suspend")); return 0
        atomic({"schema": 1, "profile": "apx-system-power-v1", "state": "closing-environment", "action": args.action})
        time.sleep(2); quiesce_hub_launcher(); run((HUB_RECOVERY, "--recover"))
        machines = subprocess.run(("/usr/bin/machinectl", "list", "--no-legend"), text=True, capture_output=True, check=False)
        if machines.returncode or machines.stdout.strip(): raise RuntimeError("an Environment survived coordinated shutdown")
        atomic({"schema": 1, "profile": "apx-system-power-v1", "state": "committed", "action": args.action})
        run(("/usr/bin/systemctl", "--no-block", args.action)); return 0
    except Exception as error:
        RESERVATION.unlink(missing_ok=True)
        atomic({"schema": 1, "profile": "apx-system-power-v1", "state": "failed", "action": args.action, "error": str(error)[:500]})
        raise
    finally: os.close(descriptor)


if __name__ == "__main__": raise SystemExit(main())
