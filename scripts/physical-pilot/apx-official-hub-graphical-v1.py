#!/usr/bin/env python3
"""Start the owner-built official Hub graphically with bounded Host recovery."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import time


GENERATION = "6f63f9a9-daea-40d1-969f-e25ff0752f4d"
RELEASE = "hub-headless-v4"
MACHINE = "apx-hub"
OUTER_UNIT = "apx-official-hub-graphical-6f63f9a9"
INNER_UNIT = "apx-official-hyprland"
EXPIRY_UNIT = "apx-official-hub-graphical-expiry"
ENVIRONMENT = Path("/var/lib/apx/environments/hub")
REGISTRATION = ENVIRONMENT / "registration.json"
ROOT = ENVIRONMENT / "root"
HOME = ENVIRONMENT / "home"
CONFIG = HOME / "apx/.config/hypr/hyprland.lua"
SESSION = Path("/var/lib/apx/official-hub-v1/apx-official-hub-session-v1.sh")
INSTALLED = Path("/var/lib/apx/official-hub-v1/apx-official-hub-graphical-v1.py")
NETWORK = Path("/usr/lib/apx/apx-environment-network-v1.py")
ACTIVE = Path("/run/apx/official-hub-graphical-v1.json")
INPUT_IDENTITIES = {
    "keyboard_i8042": {
        "ID_PATH": "platform-i8042-serio-0",
        "ID_INPUT_KEYBOARD": "1",
    },
    "keyboard_ite": {
        "ID_PATH": "pci-0000:05:00.3-usb-0:4:1.0",
        "ID_VENDOR_ID": "048d",
        "ID_MODEL_ID": "c101",
        "ID_INPUT_KEYBOARD": "1",
        "ID_INTEGRATION": "internal",
    },
    "elan_mouse": {
        "ID_PATH": "platform-AMDI0010:01",
        "ID_INPUT_MOUSE": "1",
    },
    "elan_touchpad": {
        "ID_PATH": "platform-AMDI0010:01",
        "ID_INPUT_TOUCHPAD": "1",
    },
}


class OfficialHubGraphicalError(RuntimeError):
    pass


def run(arguments: tuple[str, ...], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        arguments, check=check, text=True, capture_output=True,
        env={"PATH": "/usr/bin:/usr/local/bin", "LC_ALL": "C"},
    )


def read_registration() -> dict[str, object]:
    value = json.loads(REGISTRATION.read_text())
    if type(value) is not dict or (
        value.get("name"), value.get("role"), value.get("release"), value.get("generation")
    ) != ("hub", "hub", RELEASE, GENERATION):
        raise OfficialHubGraphicalError("official Hub registration identity differs")
    return value


def write_registration_state(state: str) -> None:
    if state not in {"running", "stopped"}:
        raise OfficialHubGraphicalError("official Hub registration state is invalid")
    value = read_registration()
    value["state"] = state
    temporary = REGISTRATION.with_name(f".{REGISTRATION.name}.{os.getpid()}.tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        os.write(descriptor, (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode())
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    os.replace(temporary, REGISTRATION)


def unit_active(unit: str) -> bool:
    return run(("systemctl", "is-active", "--quiet", unit + ".service"), False).returncode == 0


def machine_running() -> bool:
    return run(("machinectl", "show", MACHINE), False).returncode == 0


def resolve_input_devices() -> dict[str, str]:
    matches: dict[str, list[str]] = {label: [] for label in INPUT_IDENTITIES}
    for node in sorted(Path("/dev/input").glob("event*")):
        result = run(("udevadm", "info", "--query=property", f"--name={node}"), False)
        if result.returncode:
            continue
        properties = dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)
        for label, identity in INPUT_IDENTITIES.items():
            if properties.get("DEVNAME") == str(node) and all(
                properties.get(key) == expected for key, expected in identity.items()
            ):
                matches[label].append(str(node))
    if any(len(nodes) != 1 for nodes in matches.values()):
        raise OfficialHubGraphicalError("an admitted internal input identity is absent or ambiguous")
    resolved = {label: nodes[0] for label, nodes in matches.items()}
    if len(set(resolved.values())) != len(resolved):
        raise OfficialHubGraphicalError("admitted internal input identities overlap")
    return resolved


def validate_devices(inputs: dict[str, str]) -> None:
    expected = {
        Path("/dev/dri/card2"): (226, 2),
        Path("/dev/dri/renderD129"): (226, 129),
        Path("/dev/tty2"): (4, 2),
    }
    for path, device in expected.items():
        metadata = path.stat()
        if not stat.S_ISCHR(metadata.st_mode) or (os.major(metadata.st_rdev), os.minor(metadata.st_rdev)) != device:
            raise OfficialHubGraphicalError(f"required graphical device differs: {path}")
    for node in inputs.values():
        metadata = os.stat(node)
        if not stat.S_ISCHR(metadata.st_mode) or os.major(metadata.st_rdev) != 13:
            raise OfficialHubGraphicalError("resolved input node is not an evdev character device")


def stop_text_hub_if_needed() -> None:
    if machine_running():
        result = run(("/usr/bin/apx", "environment", "stop", "hub"), False)
        if result.returncode:
            raise OfficialHubGraphicalError("textual Hub could not be stopped safely")
    if machine_running():
        raise OfficialHubGraphicalError("Hub machine survived textual stop")


def recover() -> None:
    run(("systemctl", "-M", MACHINE, "stop", INNER_UNIT + ".service"), False)
    run(("systemctl", "stop", OUTER_UNIT + ".service"), False)
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline and (unit_active(OUTER_UNIT) or machine_running()):
        time.sleep(0.1)
    run(("chvt", "1"), False)
    run((str(NETWORK), "remove", "--environment", "hub"), False)
    if REGISTRATION.is_file():
        write_registration_state("stopped")
    ACTIVE.unlink(missing_ok=True)
    run(("systemctl", "stop", EXPIRY_UNIT + ".timer"), False)
    if unit_active(OUTER_UNIT) or machine_running():
        raise OfficialHubGraphicalError("official Hub graphical recovery left runtime residue")
    if Path("/sys/class/tty/tty0/active").read_text().strip() != "tty1":
        raise OfficialHubGraphicalError("official Hub graphical recovery did not restore tty1")


def arm_watchdog(seconds: int) -> None:
    run(("systemctl", "stop", EXPIRY_UNIT + ".timer"), False)
    run((
        "systemd-run", f"--unit={EXPIRY_UNIT}", f"--on-active={seconds}s",
        "--timer-property=AccuracySec=1s", "--property=Type=oneshot",
        "--property=NoNewPrivileges=yes", "--property=ProtectSystem=strict",
        "--property=ProtectHome=yes", "--property=ReadWritePaths=/run/apx",
        "--property=ReadWritePaths=/var/lib/apx/environments/hub",
        str(INSTALLED), "--recover",
    ))
    if run(("systemctl", "is-active", "--quiet", EXPIRY_UNIT + ".timer"), False).returncode:
        raise OfficialHubGraphicalError("independent official Hub watchdog did not arm")


def start_outer(inputs: dict[str, str]) -> None:
    input_nodes = tuple(inputs[label] for label in (
        "keyboard_i8042", "keyboard_ite", "elan_mouse", "elan_touchpad"
    ))
    run((str(NETWORK), "apply", "--environment", "hub"))
    command = (
        "systemd-run", f"--unit={OUTER_UNIT}", "--collect", "--property=Delegate=yes",
        "--property=KillMode=mixed", "--property=TimeoutStopSec=5s",
        "--property=MemoryMax=4G", "--property=TasksMax=1024", "--property=CPUQuota=200%",
        "--property=DevicePolicy=closed", "--property=DeviceAllow=/dev/dri/card2 rw",
        "--property=DeviceAllow=/dev/dri/renderD129 rw",
        *(f"--property=DeviceAllow={node} rw" for node in input_nodes),
        "--property=DeviceAllow=/dev/tty2 rw", "--", "systemd-nspawn", "--quiet",
        "--keep-unit", "--boot", f"--directory={ROOT}", f"--machine={MACHINE}",
        f"--hostname={MACHINE}", "--register=yes", "--settings=no", "--private-network",
        "--network-veth", "--link-journal=no", "--console=pipe", "--private-users=no",
        "--no-new-privileges=yes", f"--bind={HOME}:/home",
        f"--bind-ro={SESSION}:/run/apx/official-hub-session",
        "--bind-ro=/run/udev/data:/run/udev/data",
        *(f"--bind={node}" for node in input_nodes),
        "--bind=/dev/dri/card2", "--bind=/dev/dri/renderD129", "--bind=/dev/tty2",
    )
    run(command)
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if machine_running():
            state = run(("systemctl", "-M", MACHINE, "is-system-running"), False).stdout.strip()
            if state in {"running", "degraded"}:
                return
        time.sleep(0.2)
    raise OfficialHubGraphicalError("official Hub systemd did not become ready")


def start_inner(inputs: dict[str, str]) -> None:
    arguments = [
        "systemd-run", "-M", MACHINE, f"--unit={INNER_UNIT}", "--collect",
        "--property=Type=simple", "--property=KillMode=mixed",
        "--property=TimeoutStopSec=3s",
    ]
    arguments.extend(f"--setenv=APX_{label.upper()}_DEVICE={node}" for label, node in inputs.items())
    arguments.extend(("--", "/run/apx/official-hub-session"))
    run(tuple(arguments))


def process_pids(process_name: bytes) -> list[int]:
    found: list[int] = []
    for entry in Path("/proc").iterdir():
        if not entry.name.isdecimal():
            continue
        try:
            if (entry / "comm").read_bytes().strip() == process_name \
                    and (entry / "root/etc/apx/official-hub-base-v1").is_file():
                found.append(int(entry.name))
        except OSError:
            pass
    return found


def compositor_state() -> tuple[int, str, bool, tuple[str, ...]]:
    pids = process_pids(b"Hyprland")
    if len(pids) != 1:
        return 0, "", False, ()
    pid = pids[0]
    runtime = Path(f"/proc/{pid}/root/run/user/1000/hypr")
    sockets = list(runtime.glob("*/.socket.sock"))
    if len(sockets) != 1 or not sockets[0].is_socket():
        return pid, "", False, ()
    signature = sockets[0].parent.name
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,200}", signature):
        return pid, "", False, ()
    prefix = (
        "nsenter", "--target", str(pid), "--mount", "--pid", "--", "env",
        "XDG_RUNTIME_DIR=/run/user/1000", f"HYPRLAND_INSTANCE_SIGNATURE={signature}", "hyprctl", "-j",
    )
    monitors_result = run(prefix + ("monitors",), False)
    devices_result = run(prefix + ("devices",), False)
    try:
        monitors = json.loads(monitors_result.stdout)
        devices = json.loads(devices_result.stdout)
    except json.JSONDecodeError:
        return pid, signature, False, ()
    monitor = any(
        type(item) is dict and item.get("name") == "eDP-2" and item.get("disabled") is False
        for item in monitors if type(monitors) is list
    )
    keyboard_names = tuple(sorted(
        str(item.get("name")) for item in devices.get("keyboards", ())
        if type(item) is dict and type(item.get("name")) is str
    )) if type(devices) is dict else ()
    return pid, signature, monitor, keyboard_names


def hyprctl(pid: int, signature: str, *arguments: str) -> subprocess.CompletedProcess[str]:
    return run((
        "nsenter", "--target", str(pid), "--mount", "--pid", "--", "env",
        "XDG_RUNTIME_DIR=/run/user/1000", f"HYPRLAND_INSTANCE_SIGNATURE={signature}",
        "hyprctl", *arguments,
    ), False)


def open_and_verify_kitty(pid: int, signature: str) -> None:
    dispatched = hyprctl(pid, signature, "dispatch", 'hl.dsp.exec_cmd("kitty")')
    if dispatched.returncode or dispatched.stdout.strip().lower() != "ok":
        raise OfficialHubGraphicalError(
            "Hyprland refused the automatic Kitty launch: " + dispatched.stdout.strip()
        )
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        observed = hyprctl(pid, signature, "-j", "clients")
        try:
            clients = json.loads(observed.stdout)
        except json.JSONDecodeError:
            clients = ()
        if type(clients) is list and any(
            type(client) is dict and "kitty" in str(client.get("class", "")).lower()
            for client in clients
        ):
            return
        time.sleep(0.2)
    raise OfficialHubGraphicalError("Kitty did not create a Hyprland window")


def wait_ready() -> tuple[int, str, tuple[str, ...]]:
    deadline = time.monotonic() + 20
    stable_since: float | None = None
    last = (0, "", False, ())
    while time.monotonic() < deadline:
        last = compositor_state()
        if last[0] and last[1] and last[2] and len(last[3]) >= 1:
            stable_since = time.monotonic() if stable_since is None else stable_since
            if time.monotonic() - stable_since >= 2:
                return last[0], last[1], last[3]
        else:
            stable_since = None
        time.sleep(0.2)
    raise OfficialHubGraphicalError(
        f"Hyprland readiness incomplete: pid={last[0]} socket={bool(last[1])} "
        f"eDP-2={last[2]} keyboards={len(last[3])}"
    )


def launch(test_mode: bool) -> dict[str, object]:
    if os.geteuid() != 0 or Path("/etc/hostname").read_text().strip() != "apx-host":
        raise OfficialHubGraphicalError("official Hub graphics require root on the APX Host")
    if Path("/sys/class/tty/tty0/active").read_text().strip() != "tty1":
        raise OfficialHubGraphicalError("official Hub graphics require tty1")
    if not SESSION.is_file() or not CONFIG.is_file() or CONFIG.is_symlink():
        raise OfficialHubGraphicalError("official Hub session runner or owner config is absent")
    record = read_registration()
    if record.get("state") not in {"running", "stopped"}:
        raise OfficialHubGraphicalError("official Hub state is not launchable")
    stop_text_hub_if_needed()
    if run(("machinectl", "list", "--no-legend"), False).stdout.strip():
        raise OfficialHubGraphicalError("another Environment is running")
    inputs = resolve_input_devices()
    validate_devices(inputs)
    arm_watchdog(75 if test_mode else 14400)
    result: dict[str, object] = {}
    try:
        start_outer(inputs)
        start_inner(inputs)
        print("APX: a mudar para tty2. Super+Q abre Kitty; Super+M termina o Hyprland.", flush=True)
        print("APX: Ctrl+Alt+F1 volta visualmente ao Host; o watchdog também recupera.", flush=True)
        run(("chvt", "2"), False)
        pid, signature, keyboards = wait_ready()
        write_registration_state("running")
        ACTIVE.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
        ACTIVE.write_text(json.dumps({
            "profile": "apx-official-hub-graphical-v1", "generation": GENERATION,
            "unit": OUTER_UNIT + ".service", "pid": pid,
        }, sort_keys=True, separators=(",", ":")) + "\n")
        open_and_verify_kitty(pid, signature)
        if test_mode:
            time.sleep(3)
            result = {
                "classification": "verified", "hyprland": True, "kitty": True,
                "monitor": "eDP-2", "keyboard_count": len(keyboards),
                "input_identities": tuple(sorted(inputs)),
            }
        else:
            while machine_running() and run(
                ("systemctl", "-M", MACHINE, "is-active", "--quiet", INNER_UNIT + ".service"), False
            ).returncode == 0:
                time.sleep(0.5)
            result = {"classification": "session-ended", "owner_exit": True}
    finally:
        recover()
    result.update({"tty1_restored": True, "machine_residue": False})
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--test", action="store_true")
    mode.add_argument("--interactive", action="store_true")
    mode.add_argument("--recover", action="store_true")
    arguments = parser.parse_args()
    if arguments.recover:
        recover()
        return 0
    result = launch(arguments.test)
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OfficialHubGraphicalError, subprocess.CalledProcessError, OSError, ValueError) as error:
        print(f"APX official Hub graphics refused: {error}", file=os.sys.stderr)
        raise SystemExit(2)
