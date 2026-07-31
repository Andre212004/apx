#!/usr/bin/env python3
"""Exact ten-second graphical activation of the stopped APX test Environment."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import time


GENERATION = "69b56acc-fd4d-4499-8009-e1d0108466f4"
PLAN = "7603c8d17c787ed4122cff9520f49392c0865412967b5a53e9b595ff8dec43f3"
UNIT = "apx-graphical-test-69b56acc"
EXPIRY = "apx-graphical-test-expiry"
MACHINE = "apx-test"
ROOT = "/var/lib/apx/environments/test/root"
HOME = "/var/lib/apx/environments/test/home"
STATE = "/var/lib/apx/graphical-v1"
RECOVERY_MODE = "--recover-test"
REGISTRATION = "/var/lib/apx/environments/test/registration.json"
INPUT_IDENTITIES = {
    "keyboard": ("platform-i8042-serio-0", "ID_INPUT_KEYBOARD"),
    "elan_mouse": ("platform-AMDI0010:01", "ID_INPUT_MOUSE"),
    "elan_touchpad": ("platform-AMDI0010:01", "ID_INPUT_TOUCHPAD"),
}


def run(args, check=True):
    return subprocess.run(tuple(args), text=True, capture_output=True, check=check,
                          env={**os.environ, "LC_ALL": "C"})


def resolve_input_devices() -> dict[str, str]:
    matches = {name: [] for name in INPUT_IDENTITIES}
    for node in sorted(Path("/dev/input").glob("event*")):
        result = run(("udevadm", "info", "--query=property", f"--name={node}"), False)
        if result.returncode:
            continue
        properties = dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)
        for name, (path, capability) in INPUT_IDENTITIES.items():
            if properties.get("DEVNAME") == str(node) and properties.get("ID_PATH") == path \
                    and properties.get(capability) == "1":
                matches[name].append(str(node))
    if any(len(nodes) != 1 for nodes in matches.values()):
        raise SystemExit("graphical launch refused: admitted input identity is absent or ambiguous")
    return {name: nodes[0] for name, nodes in matches.items()}


def process_pids(executable: bytes) -> list[int]:
    found = []
    for item in Path("/proc").iterdir():
        if not item.name.isdigit():
            continue
        try:
            if executable in (item / "cmdline").read_bytes().split(b"\0"):
                found.append(int(item.name))
        except OSError:
            pass
    return found


def compositor_observation() -> tuple[bool, bool]:
    socket_seen = monitor_seen = False
    for pid in process_pids(b"/usr/bin/Hyprland"):
        runtime = Path(f"/proc/{pid}/root/run/user/1000/hypr")
        try:
            for socket_path in runtime.glob("*/.socket.sock"):
                socket_seen |= socket_path.is_socket()
                result = run(("nsenter", "--target", str(pid), "--mount", "--pid", "--",
                              "env", "XDG_RUNTIME_DIR=/run/user/1000",
                              f"HYPRLAND_INSTANCE_SIGNATURE={socket_path.parent.name}",
                              "hyprctl", "-j", "monitors"), False)
                if result.returncode == 0:
                    monitors = json.loads(result.stdout)
                    monitor_seen |= any(item.get("name") == "eDP-2" and not item.get("disabled", False)
                                        for item in monitors if isinstance(item, dict))
        except (OSError, json.JSONDecodeError):
            pass
    return socket_seen, monitor_seen


def main() -> int:
    record = json.loads(Path(REGISTRATION).read_text())
    if os.geteuid() or record.get("generation") != GENERATION or record.get("state") != "stopped":
        raise SystemExit("test graphical launch refused: generation or state changed")
    if Path("/sys/class/tty/tty0/active").read_text().strip() != "tty1":
        raise SystemExit("test graphical launch refused: tty1 is not active")
    if run(("systemctl", "--failed", "--no-legend"), False).stdout.strip() or run(("machinectl", "list", "--no-legend"), False).stdout.strip():
        raise SystemExit("test graphical launch refused: Host is not clean")
    recovery = f"{STATE}/apx-graphical-recovery-v1.py"
    session = f"{STATE}/apx-graphical-session-v1.sh"
    inputs = resolve_input_devices()
    input_nodes = tuple(inputs[key] for key in ("keyboard", "elan_mouse", "elan_touchpad"))
    run(("systemd-run", f"--unit={EXPIRY}", "--on-active=15s",
         "--timer-property=AccuracySec=1s", "--property=Type=oneshot",
         "--property=NoNewPrivileges=yes", "--property=ProtectSystem=strict",
         "--property=ProtectHome=yes", "--property=PrivateNetwork=yes",
         recovery, RECOVERY_MODE))
    if run(("systemctl", "is-active", "--quiet", EXPIRY + ".timer"), False).returncode:
        raise SystemExit("test graphical launch refused: watchdog did not arm")
    command = (
        "systemd-run", f"--unit={UNIT}", "--collect", "--property=Delegate=yes",
        "--property=KillMode=mixed", "--property=TimeoutStopSec=3s",
        "--property=MemoryMax=1536M", "--property=TasksMax=512",
        "--property=CPUQuota=100%", "--property=DevicePolicy=closed",
        "--property=DeviceAllow=/dev/dri/card2 rw", "--property=DeviceAllow=/dev/dri/renderD129 rw",
        *(f"--property=DeviceAllow={node} rw" for node in input_nodes),
        "--property=DeviceAllow=/dev/tty2 rw", "--", "systemd-nspawn", "--quiet", "--keep-unit",
        f"--directory={ROOT}", f"--machine={MACHINE}", f"--hostname={MACHINE}",
        "--register=yes", "--settings=no", "--private-network", "--resolv-conf=off",
        "--timezone=off", "--link-journal=no", "--console=pipe", "--private-users=no",
        "--no-new-privileges=yes", f"--bind={HOME}:/home",
        f"--bind-ro={session}:/run/apx/session",
        "--bind-ro=/run/udev/data:/run/udev/data",
        *(f"--bind={node}" for node in input_nodes),
        *(f"--setenv=APX_{key.upper()}_DEVICE={value}" for key, value in inputs.items()),
        "--bind=/dev/dri/card2", "--bind=/dev/dri/renderD129", "--bind=/dev/tty2", "--", "/run/apx/session",
    )
    machine_seen = hyprland_seen = waybar_seen = socket_seen = monitor_seen = False
    try:
        run(command)
        run(("chvt", "2"), False)
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline and run(("systemctl", "is-active", "--quiet", UNIT + ".service"), False).returncode == 0:
            machine_seen |= run(("machinectl", "show", MACHINE), False).returncode == 0
            hyprland_seen |= bool(process_pids(b"/usr/bin/Hyprland"))
            waybar_seen |= bool(process_pids(b"/usr/bin/waybar"))
            socket_now, monitor_now = compositor_observation()
            socket_seen |= socket_now; monitor_seen |= monitor_now
            time.sleep(0.25)
    finally:
        run((recovery, RECOVERY_MODE), False)
        run(("systemctl", "stop", EXPIRY + ".timer"), False)
    if Path("/sys/class/tty/tty0/active").read_text().strip() != "tty1" or run(("machinectl", "list", "--no-legend"), False).stdout.strip():
        raise SystemExit("test graphical launch ended with recovery residue")
    if not all((machine_seen, hyprland_seen, waybar_seen, socket_seen, monitor_seen)):
        raise SystemExit(
            "graphical test recovered but readiness evidence is incomplete: "
            f"machine={machine_seen} hyprland={hyprland_seen} waybar={waybar_seen} "
            f"wayland={socket_seen} eDP-2={monitor_seen}"
        )
    print(f"graphical-test-passed plan={PLAN} machine=true hyprland=true waybar=true wayland=true eDP-2=true tty1=true zero-residue=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
