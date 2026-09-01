#!/usr/bin/env python3
"""Boot-time direct entry into the official graphical Hub."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import time


HOSTNAME = "apx-host"
HUB = "/var/lib/apx/official-hub-v1/apx-official-hub-graphical-v1.py"
GENERAL = "/usr/lib/apx/apx-graphical-environment-v1.py"
ENVIRONMENTS = Path("/var/lib/apx/environments")
HANDOFF_LOCK = Path("/run/apx/environment-handoff-v1.lock")
REQUIRED_SOCKETS = tuple(Path("/run/apx") / name for name in (
    "host-services-v1.sock", "host-services-v2.sock", "host-services-v3.sock",
    "audio-state-v1.sock", "coordinated-update-v1.sock", "host-console-v1.sock",
    "environment-switch-v1.sock",
))
OPTIONAL_SOCKETS = (Path("/run/apx/system-power-v1.sock"),)


def run(arguments: tuple[str, ...], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(arguments, text=True, capture_output=True, check=check,
                          env={"PATH": "/usr/bin:/usr/local/bin", "LC_ALL": "C"})


def wait_for_tty1() -> None:
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        if Path("/sys/class/tty/tty0/active").read_text().strip() == "tty1":
            return
        time.sleep(0.2)
    raise RuntimeError("tty1 recovery console did not become ready at boot")


def clear_recovery_console() -> None:
    """Hide the raw getty while the graphical Hub takes over the display."""
    descriptor = os.open("/dev/tty1", os.O_WRONLY | os.O_NOCTTY)
    try:
        os.write(descriptor, b"\033[2J\033[H\033[?25l")
    finally:
        os.close(descriptor)


def wait_for_host_services() -> None:
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        if all(endpoint.is_socket() for endpoint in REQUIRED_SOCKETS):
            return
        time.sleep(0.2)
    missing = ", ".join(str(endpoint) for endpoint in REQUIRED_SOCKETS if not endpoint.is_socket())
    raise RuntimeError(f"Host service sockets did not become ready: {missing}")


def handoff_active() -> bool:
    """Recognize only the root-owned supervisor lock for an active handoff."""
    try:
        metadata = HANDOFF_LOCK.lstat()
    except FileNotFoundError:
        return False
    return HANDOFF_LOCK.is_file() and not HANDOFF_LOCK.is_symlink() \
        and metadata.st_uid == 0 and metadata.st_gid == 0


def interrupted_workloads() -> list[str]:
    running: list[str] = []
    for directory in sorted(ENVIRONMENTS.iterdir()):
        name = directory.name
        registration = directory / "registration.json"
        if name == "hub" or re.fullmatch(r"[a-z](?:[a-z0-9]|-(?=[a-z0-9])){0,26}", name) is None \
                or not registration.is_file() or registration.is_symlink():
            continue
        metadata = registration.stat(); data = registration.read_bytes()
        if metadata.st_uid != 0 or metadata.st_gid != 0 or not data or len(data) > 8192:
            raise RuntimeError(f"untrusted Environment registration during boot: {name}")
        value = json.loads(data)
        if type(value) is not dict or (value.get("name"), value.get("role"), value.get("release")) != (
            name, "graphical-base", "hyprland-base-v2",
        ):
            continue
        if value.get("state") == "running":
            running.append(name)
    return running


def reconcile_interrupted_workloads() -> None:
    running = interrupted_workloads()
    if not running:
        return
    if run(("machinectl", "list", "--no-legend"), False).stdout.strip():
        raise RuntimeError("an Environment machine exists during boot reconciliation")
    for name in running:
        run((GENERAL, "--environment", name, "--recover"))


def main() -> int:
    if os.geteuid() != 0 or Path("/etc/hostname").read_text().strip() != HOSTNAME:
        raise RuntimeError("official Hub autostart requires APX Host root")
    # The handoff supervisor, not boot autostart, owns Hub restoration after
    # an Environment switch. Returning success prevents Restart=on-failure
    # from launching a competing Hub while the RTX is still leased to VFIO.
    if handoff_active():
        return 0
    wait_for_tty1()
    clear_recovery_console()
    wait_for_host_services()
    missing_optional = [str(endpoint) for endpoint in OPTIONAL_SOCKETS if not endpoint.is_socket()]
    if missing_optional:
        print("APX: optional Host controls unavailable: " + ", ".join(missing_optional), flush=True)
    if run(("machinectl", "list", "--no-legend"), False).stdout.strip():
        raise RuntimeError("official Hub autostart refuses an existing Environment")
    reconcile_interrupted_workloads()
    result = run((HUB, "--interactive"), False)
    if result.returncode and handoff_active():
        return 0
    if result.returncode:
        print(result.stderr.strip() or result.stdout.strip(), flush=True)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
