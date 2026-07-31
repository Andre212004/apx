#!/usr/bin/env python3
"""Assisted, bounded proof that exact physical input reaches graphical Hub."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import re
import selectors
import struct
import subprocess
import sys
import time

sys.path.insert(0, "/usr/lib/apx")
from apx_graphical_input_proof import GraphicalInputProofEvidence, assess_graphical_input


HUB_GENERATION = "2c3dbacc-106f-4053-8603-f649552f5513"
TEST_GENERATION = "69b56acc-fd4d-4499-8009-e1d0108466f4"
HUB_UNIT = "apx-graphical-hub-2c3dbacc.service"
HUB_MACHINE = "apx-hub"
EXPIRY = "apx-graphical-session-expiry"
RECOVERY = Path("/var/lib/apx/graphical-v1/apx-graphical-recovery-v1.py")
BROKER = Path("/var/lib/apx/graphical-v1/apx-graphical-broker-v1.py")
MARKER = Path("/run/user/1000/apx-input-proof-key-v1")
RECEIPT = Path("/var/lib/apx/evidence/graphical-input-proof-v1.json")
EVENT = struct.Struct("llHHI")
EV_KEY = 0x01
EV_REL = 0x02
EV_ABS = 0x03
ITE_KEYBOARD_IDENTITY = {
    "ID_PATH": "pci-0000:05:00.3-usb-0:4:1.0",
    "ID_VENDOR_ID": "048d",
    "ID_MODEL_ID": "c101",
    "ID_INPUT_KEYBOARD": "1",
    "ID_INTEGRATION": "internal",
}


class PhysicalInputProofError(RuntimeError):
    pass


def run(arguments: tuple[str, ...], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        arguments, text=True, capture_output=True, check=check,
        env={"PATH": "/usr/bin:/usr/local/bin", "LC_ALL": "C"},
    )


def installed_broker():
    spec = importlib.util.spec_from_file_location("apx_installed_graphical_broker", BROKER)
    if spec is None or spec.loader is None:
        raise PhysicalInputProofError("installed graphical broker cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def hyprland_pid() -> int:
    result = run(("/usr/bin/pgrep", "-x", "Hyprland"))
    values = [line for line in result.stdout.splitlines() if line.isdecimal()]
    if len(values) != 1:
        raise PhysicalInputProofError("exactly one Hyprland process is required")
    return int(values[0])


def instance_signature(pid: int) -> str:
    root = Path(f"/proc/{pid}/root/run/user/1000/hypr")
    values = [path.name for path in root.iterdir() if path.is_dir()]
    if len(values) != 1 or not re.fullmatch(r"[A-Za-z0-9_.-]{1,200}", values[0]):
        raise PhysicalInputProofError("Hyprland instance signature is absent or ambiguous")
    return values[0]


def hyprctl(pid: int, signature: str, *arguments: str) -> subprocess.CompletedProcess[str]:
    return run((
        "/usr/bin/nsenter", "--target", str(pid), "--mount", "--pid", "--",
        "/usr/bin/env", "XDG_RUNTIME_DIR=/run/user/1000",
        f"HYPRLAND_INSTANCE_SIGNATURE={signature}", "/usr/bin/hyprctl", *arguments,
    ))


def cursor_position(pid: int, signature: str) -> tuple[int, int]:
    result = hyprctl(pid, signature, "-j", "cursorpos")
    value = json.loads(result.stdout)
    if type(value) is not dict or type(value.get("x")) not in (int, float) \
            or type(value.get("y")) not in (int, float):
        raise PhysicalInputProofError("Hyprland cursor position is malformed")
    return round(value["x"]), round(value["y"])


def exact_nodes_visible(pid: int, devices: dict[str, str]) -> bool:
    for node in devices.values():
        host = os.stat(node)
        inside = os.stat(f"/proc/{pid}/root{node}")
        if not stat_character(host.st_mode) or not stat_character(inside.st_mode) \
                or host.st_rdev != inside.st_rdev:
            return False
    return True


def stat_character(mode: int) -> bool:
    import stat
    return stat.S_ISCHR(mode)


def closed_device_policy(devices: dict[str, str]) -> bool:
    result = run(("/usr/bin/systemctl", "show", HUB_UNIT,
                  "--property=DevicePolicy", "--property=DeviceAllow"))
    lines = result.stdout.splitlines()
    if "DevicePolicy=closed" not in lines:
        return False
    rendered = "\n".join(lines)
    return all(node in rendered for node in devices.values()) \
        and "/dev/dri/card2" in rendered and "/dev/dri/renderD129" in rendered \
        and "/dev/tty2" in rendered


def count_events(devices: dict[str, str], seconds: float) -> tuple[int, int]:
    selector = selectors.DefaultSelector()
    descriptors: list[int] = []
    try:
        for label, node in devices.items():
            descriptor = os.open(node, os.O_RDONLY | os.O_NONBLOCK | os.O_CLOEXEC)
            descriptors.append(descriptor)
            selector.register(descriptor, selectors.EVENT_READ, label)
        keyboard = pointer = 0
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            for key, _mask in selector.select(min(0.2, deadline - time.monotonic())):
                try:
                    chunk = os.read(key.fd, EVENT.size * 64)
                except BlockingIOError:
                    continue
                for offset in range(0, len(chunk) - EVENT.size + 1, EVENT.size):
                    _sec, _usec, event_type, _code, _value = EVENT.unpack_from(chunk, offset)
                    if key.data == "keyboard" and event_type == EV_KEY:
                        keyboard += 1
                    elif key.data != "keyboard" and event_type in (EV_KEY, EV_REL, EV_ABS):
                        pointer += 1
        return keyboard, pointer
    finally:
        selector.close()
        for descriptor in descriptors:
            os.close(descriptor)


def count_host_keyboards(nodes: dict[str, str], seconds: float) -> dict[str, int]:
    selector = selectors.DefaultSelector()
    descriptors: list[int] = []
    counts = {label: 0 for label in nodes}
    try:
        for label, node in nodes.items():
            descriptor = os.open(node, os.O_RDONLY | os.O_NONBLOCK | os.O_CLOEXEC)
            descriptors.append(descriptor)
            selector.register(descriptor, selectors.EVENT_READ, label)
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            for key, _mask in selector.select(min(0.2, deadline - time.monotonic())):
                try:
                    chunk = os.read(key.fd, EVENT.size * 64)
                except BlockingIOError:
                    continue
                for offset in range(0, len(chunk) - EVENT.size + 1, EVENT.size):
                    _sec, _usec, event_type, _code, _value = EVENT.unpack_from(chunk, offset)
                    if event_type == EV_KEY:
                        counts[key.data] += 1
        return counts
    finally:
        selector.close()
        for descriptor in descriptors:
            os.close(descriptor)


def resolve_ite_keyboard() -> str:
    matches: list[str] = []
    for node in sorted(Path("/dev/input").glob("event*")):
        result = run(("/usr/bin/udevadm", "info", "--query=property", f"--name={node}"), False)
        if result.returncode:
            continue
        properties = dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)
        if properties.get("DEVNAME") == str(node) and all(
            properties.get(key) == value for key, value in ITE_KEYBOARD_IDENTITY.items()
        ):
            matches.append(str(node))
    if len(matches) != 1:
        raise PhysicalInputProofError("internal ITE keyboard identity is absent or ambiguous")
    return matches[0]


def arm_short_expiry() -> None:
    run(("/usr/bin/systemctl", "stop", EXPIRY + ".timer"), False)
    run((
        "/usr/bin/systemd-run", f"--unit={EXPIRY}", "--on-active=30s",
        "--timer-property=AccuracySec=1s", "--property=Type=oneshot",
        "--property=NoNewPrivileges=yes", "--property=ProtectSystem=strict",
        "--property=ProtectHome=yes", "--property=ReadWritePaths=/run/apx",
        "--property=ReadWritePaths=/var/lib/apx/environments/hub",
        "--property=ReadWritePaths=/var/lib/apx/environments/test",
        "--property=PrivateNetwork=yes", str(RECOVERY), "--recover-hub",
    ))
    if run(("/usr/bin/systemctl", "is-active", "--quiet", EXPIRY + ".timer"), False).returncode:
        raise PhysicalInputProofError("30-second independent recovery did not arm")


def recover() -> None:
    run((str(RECOVERY), "--recover-hub"), False)
    run(("/usr/bin/systemctl", "stop", EXPIRY + ".timer"), False)
    run(("/usr/bin/systemctl", "reset-failed", EXPIRY + ".service"), False)


def registration_stopped(name: str) -> bool:
    try:
        value = json.loads(Path(f"/var/lib/apx/environments/{name}/registration.json").read_text())
    except (OSError, ValueError):
        return False
    return value.get("state") == "stopped"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seconds", type=int, default=12, choices=range(8, 21))
    parser.add_argument("--acknowledge-assisted-gesture", action="store_true")
    parser.add_argument("--host-keyboard-only", action="store_true")
    arguments = parser.parse_args()
    if os.geteuid() != 0 or not arguments.acknowledge_assisted_gesture:
        raise PhysicalInputProofError("root and explicit assisted-gesture acknowledgement are required")
    if arguments.host_keyboard_only:
        if Path("/sys/class/tty/tty0/active").read_text().strip() != "tty1":
            raise PhysicalInputProofError("Host keyboard probe requires tty1")
        broker_keyboard = installed_broker().resolve_input_devices()["keyboard"]
        ite_keyboard = resolve_ite_keyboard()
        candidates = {
            "i8042": broker_keyboard,
            "ite": ite_keyboard,
        }
        if len(set(candidates.values())) != len(candidates):
            raise PhysicalInputProofError("Host keyboard candidates must be distinct")
        print("Prime uma tecla inofensiva várias vezes durante os próximos segundos.")
        print("A prova conta apenas eventos EV_KEY; códigos e valores são descartados.")
        input("Prime Enter para iniciar: ")
        counts = count_host_keyboards(candidates, arguments.seconds)
        total = sum(counts.values())
        print(json.dumps({
            "profile": "apx-host-keyboard-candidate-count-v2",
            "classification": "observed" if total else "blocked",
            "candidate_event_counts": counts,
            "candidate_identities": {
                "i8042": "platform-i8042-serio-0",
                "ite": ITE_KEYBOARD_IDENTITY["ID_PATH"],
            },
            "tty1_preserved": Path("/sys/class/tty/tty0/active").read_text().strip() == "tty1",
        }, sort_keys=True, separators=(",", ":")))
        return 0 if total else 2
    print("Durante a janela gráfica: move o touchpad e prime Super+F12 uma vez.")
    print("A prova não guarda códigos de teclas, texto, coordenadas intermédias ou eventos brutos.")
    input("Prime Enter para iniciar a janela limitada: ")

    devices = installed_broker().resolve_input_devices()
    before = after = (0, 0)
    keyboard = pointer = 0
    marker = nodes = policy = False
    try:
        run(("/usr/local/bin/entrar_no_HUB",))
        arm_short_expiry()
        pid = hyprland_pid()
        signature = instance_signature(pid)
        nodes = exact_nodes_visible(pid, devices)
        policy = closed_device_policy(devices)
        marker_inside = f"/proc/{pid}/root{MARKER}"
        Path(marker_inside).unlink(missing_ok=True)
        hyprctl(pid, signature, "keyword", "bind",
                f"SUPER,F12,exec,touch {MARKER}")
        before = cursor_position(pid, signature)
        keyboard, pointer = count_events(devices, arguments.seconds)
        after = cursor_position(pid, signature)
        marker = Path(marker_inside).is_file()
        Path(marker_inside).unlink(missing_ok=True)
    finally:
        recover()

    evidence = GraphicalInputProofEvidence(
        resolved_devices=tuple((label, devices[label]) for label in
                               ("keyboard", "elan_mouse", "elan_touchpad")),
        keyboard_event_count=keyboard,
        pointer_event_count=pointer,
        cursor_before=before,
        cursor_after=after,
        shortcut_marker_present=marker,
        exact_nodes_visible_inside=nodes,
        closed_unit_device_policy=policy,
        tty1_restored=Path("/sys/class/tty/tty0/active").read_text().strip() == "tty1",
        registrations_stopped=registration_stopped("hub") and registration_stopped("test"),
        no_machine_residue=not run(("/usr/bin/machinectl", "list", "--no-legend"), False).stdout.strip(),
        no_unit_residue=run(("/usr/bin/systemctl", "is-active", "--quiet", HUB_UNIT), False).returncode != 0,
        no_failed_units=not run(("/usr/bin/systemctl", "--failed", "--no-legend"), False).stdout.strip(),
    )
    result = assess_graphical_input(evidence)
    receipt = {
        "profile": result.profile, "classification": result.classification,
        "blockers": result.blockers, "evidence_digest": result.evidence_digest,
        "keyboard_event_count": keyboard, "pointer_event_count": pointer,
        "cursor_changed": before != after,
        "tty1_restored": evidence.tty1_restored,
        "registrations_stopped": evidence.registrations_stopped,
        "no_machine_residue": evidence.no_machine_residue,
        "no_unit_residue": evidence.no_unit_residue,
        "no_failed_units": evidence.no_failed_units,
    }
    if result.classification == "verified":
        RECEIPT.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        temporary = RECEIPT.with_name(f".{RECEIPT.name}.{os.getpid()}.tmp")
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o400)
        try:
            os.write(descriptor, (json.dumps(
                receipt, sort_keys=True, separators=(",", ":")
            ) + "\n").encode())
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        os.replace(temporary, RECEIPT)
    print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))
    return 0 if result.classification == "verified" else 2


if __name__ == "__main__":
    raise SystemExit(main())
