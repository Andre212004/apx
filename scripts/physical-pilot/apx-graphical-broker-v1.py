#!/usr/bin/env python3
"""Closed physical-pilot broker for the first Hub/test graphical handoff."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import time

sys.path.insert(0, "/usr/lib/apx")
from apx_executor_contract import RequesterContext, build_operation_plan
import apx_executor_store as store
from apx_session_descriptor_issuer import IssuedDesktopAction, issue_session_descriptor


HUB_GENERATION = "2c3dbacc-106f-4053-8603-f649552f5513"
TEST_GENERATION = "69b56acc-fd4d-4499-8009-e1d0108466f4"
STATE = Path("/run/apx")
ACTIVE = STATE / "active-session-v1.json"
SESSION_DIR = STATE / "graphical-sessions-v1"
SOCKET = STATE / "executor-v1.sock"
RECOVERY = "/var/lib/apx/graphical-v1/apx-graphical-recovery-v1.py"
SESSION_RUNNER = "/var/lib/apx/graphical-v1/apx-graphical-session-v1.sh"
LOCK = STATE / "graphical-handoff-v1.lock"
ENVIRONMENTS = Path("/var/lib/apx/environments")
SPECS = {
    "hub": {"generation": HUB_GENERATION, "role": "hub-graphical", "machine": "apx-hub"},
    "test": {"generation": TEST_GENERATION, "role": "graphical-base", "machine": "apx-test"},
}
INPUT_IDENTITIES = {
    "keyboard": ("platform-i8042-serio-0", "ID_INPUT_KEYBOARD"),
    "elan_mouse": ("platform-AMDI0010:01", "ID_INPUT_MOUSE"),
    "elan_touchpad": ("platform-AMDI0010:01", "ID_INPUT_TOUCHPAD"),
}


class BrokerError(RuntimeError):
    pass


def run(arguments: tuple[str, ...], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(arguments, text=True, capture_output=True, check=check,
                          env={"PATH": "/usr/bin", "LC_ALL": "C"})


def resolve_input_devices() -> dict[str, str]:
    """Resolve the admitted physical devices without trusting unstable event numbers."""
    matches: dict[str, list[str]] = {name: [] for name in INPUT_IDENTITIES}
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
        raise BrokerError("admitted physical input identity is absent or ambiguous")
    resolved = {name: nodes[0] for name, nodes in matches.items()}
    if len(set(resolved.values())) != len(resolved):
        raise BrokerError("admitted physical input identities overlap")
    return resolved


def atomic_json(path: Path, value: dict[str, object], mode: int = 0o600) -> None:
    path.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode)
    try:
        data = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
        os.write(descriptor, data); os.fsync(descriptor)
    finally:
        os.close(descriptor)
    os.replace(temporary, path)


def registration(name: str) -> dict[str, object]:
    path = ENVIRONMENTS / name / "registration.json"
    value = json.loads(path.read_text())
    spec = SPECS[name]
    if (value.get("name"), value.get("generation"), value.get("role")) != (
        name, spec["generation"], spec["role"]
    ):
        raise BrokerError(f"{name} registration identity differs")
    return value


def set_registration_state(name: str, state: str) -> None:
    if state not in {"running", "stopped"}:
        raise BrokerError("registration state is outside the closed broker")
    value = registration(name); value["state"] = state
    atomic_json(ENVIRONMENTS / name / "registration.json", value, 0o600)


def unit(name: str) -> str:
    return f"apx-graphical-{name}-{SPECS[name]['generation'][:8]}"


def active_state() -> dict[str, object]:
    try:
        value = json.loads(ACTIVE.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise BrokerError("active graphical session is unavailable") from error
    if type(value) is not dict:
        raise BrokerError("active graphical session is malformed")
    return value


def publish_descriptor(name: str) -> tuple[Path, str]:
    spec = SPECS[name]
    session_id = "session-" + secrets.token_hex(16)
    requester = RequesterContext(session_id, name, str(spec["role"]), str(spec["generation"]),
                                 True, True, True)
    if name == "hub":
        plan = build_operation_plan("activate", "test", TEST_GENERATION)
        action_id, label = "activate", "Abrir APX Test"
    else:
        plan = build_operation_plan("stop", "test", TEST_GENERATION)
        action_id, label = "return-to-hub", "Voltar ao HUB"
    token = secrets.token_hex(16)
    now = int(time.time())
    action = IssuedDesktopAction(action_id, label, plan, "op-" + token,
                                 "approval-" + secrets.token_hex(16), secrets.token_hex(32))
    bundle = issue_session_descriptor(requester, (action,), issued_at=now, expires_at=now + 240)
    store.initialize_store()
    try:
        store.publish_plan(plan)
    except FileExistsError:
        if store.load_plan(plan.plan_digest) != plan:
            raise BrokerError("existing executor plan differs")
    store.publish_approval(bundle.approvals[0])
    SESSION_DIR.mkdir(mode=0o755, parents=True, exist_ok=True)
    path = SESSION_DIR / f"{session_id}.json"
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o444)
    try:
        os.write(descriptor, bundle.descriptor); os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return path, session_id


def stop(name: str) -> None:
    run(("systemctl", "stop", unit(name) + ".service"), False)
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline and run(("systemctl", "is-active", "--quiet", unit(name) + ".service"), False).returncode == 0:
        time.sleep(0.1)
    if run(("systemctl", "is-active", "--quiet", unit(name) + ".service"), False).returncode == 0:
        raise BrokerError(f"{name} graphical unit survived stop")
    set_registration_state(name, "stopped")


def arm_watchdog(name: str) -> None:
    timer = "apx-graphical-session-expiry"
    run(("systemctl", "stop", timer + ".timer"), False)
    recovery_mode = "--recover-hub" if name == "hub" else "--recover-test"
    run(("systemd-run", f"--unit={timer}", "--on-active=180s", "--timer-property=AccuracySec=1s",
         "--property=Type=oneshot", "--property=NoNewPrivileges=yes",
         "--property=ProtectSystem=strict", "--property=ProtectHome=yes",
         "--property=ReadWritePaths=/run/apx",
         "--property=ReadWritePaths=/var/lib/apx/environments/hub",
         "--property=ReadWritePaths=/var/lib/apx/environments/test",
         "--property=PrivateNetwork=yes", RECOVERY, recovery_mode))
    if run(("systemctl", "is-active", "--quiet", timer + ".timer"), False).returncode:
        raise BrokerError("independent graphical watchdog did not arm")


def start(name: str, descriptor: Path, session_id: str) -> None:
    if not SOCKET.is_socket():
        raise BrokerError("typed executor socket is unavailable")
    spec = SPECS[name]
    inputs = resolve_input_devices()
    input_nodes = tuple(inputs[key] for key in ("keyboard", "elan_mouse", "elan_touchpad"))
    root = ENVIRONMENTS / name / "root"; home = ENVIRONMENTS / name / "home"
    command = (
        "systemd-run", f"--unit={unit(name)}", "--collect", "--property=Delegate=yes",
        "--property=KillMode=mixed", "--property=TimeoutStopSec=3s", "--property=MemoryMax=1536M",
        "--property=TasksMax=512", "--property=CPUQuota=100%", "--property=DevicePolicy=closed",
        "--property=DeviceAllow=/dev/dri/card2 rw", "--property=DeviceAllow=/dev/dri/renderD129 rw",
        *(f"--property=DeviceAllow={node} rw" for node in input_nodes),
        "--property=DeviceAllow=/dev/tty2 rw", "--", "systemd-nspawn", "--quiet", "--keep-unit",
        f"--directory={root}", f"--machine={spec['machine']}", f"--hostname={spec['machine']}",
        "--register=yes", "--settings=no", "--private-network", "--resolv-conf=off", "--timezone=off",
        "--link-journal=no", "--console=pipe", "--private-users=no", "--no-new-privileges=yes",
        f"--bind={home}:/home", f"--bind-ro={SESSION_RUNNER}:/run/apx/session",
        f"--bind-ro={descriptor}:/run/apx/session-ui-v1.json", f"--bind={SOCKET}:{SOCKET}",
        "--bind-ro=/run/udev/data:/run/udev/data",
        *(f"--bind={node}" for node in input_nodes),
        *(f"--setenv=APX_{key.upper()}_DEVICE={value}" for key, value in inputs.items()),
        "--bind=/dev/dri/card2", "--bind=/dev/dri/renderD129", "--bind=/dev/tty2", "--", "/run/apx/session",
    )
    arm_watchdog(name); run(command); run(("chvt", "2"), False)
    deadline = time.monotonic() + 12
    stable_since = None
    while time.monotonic() < deadline:
        unit_ok = run(("systemctl", "is-active", "--quiet", unit(name) + ".service"), False).returncode == 0
        machine_ok = run(("machinectl", "show", str(spec["machine"])), False).returncode == 0
        hyprland_ok = run(("pgrep", "-x", "Hyprland"), False).returncode == 0
        waybar_ok = run(("pgrep", "-x", "waybar"), False).returncode == 0
        if unit_ok and machine_ok and hyprland_ok and waybar_ok:
            stable_since = time.monotonic() if stable_since is None else stable_since
            if time.monotonic() - stable_since >= 2:
                break
        else:
            stable_since = None
        time.sleep(0.2)
    else:
        stop(name); run(("chvt", "1"), False)
        raise BrokerError(f"{name} graphical session did not become ready")
    set_registration_state(name, "running")
    atomic_json(ACTIVE, {"profile": "apx-active-session-v1", "session_id": session_id,
        "logical_name": name, "role": spec["role"], "generation": spec["generation"],
        "unit": unit(name) + ".service"})


def handoff(direction: str) -> dict[str, object]:
    outgoing, incoming = ("hub", "test") if direction == "hub-to-test" else ("test", "hub")
    state = active_state()
    if (state.get("logical_name"), state.get("generation")) != (outgoing, SPECS[outgoing]["generation"]):
        raise BrokerError("outgoing active session identity differs")
    descriptor, session_id = publish_descriptor(incoming)
    stop(outgoing)
    try:
        start(incoming, descriptor, session_id)
    except Exception:
        # Fixed recovery is preferable to guessing that rollback is usable.
        run(("chvt", "1"), False); ACTIVE.unlink(missing_ok=True)
        raise
    return {"classification": "handoff-complete", "direction": direction,
            "outgoing_generation": SPECS[outgoing]["generation"],
            "incoming_generation": SPECS[incoming]["generation"], "single_owner": True,
            "watchdog_active": True, "recovery_verified": True}


def bootstrap_hub() -> dict[str, object]:
    if Path("/sys/class/tty/tty0/active").read_text().strip() != "tty1":
        raise BrokerError("Hub bootstrap requires tty1 recovery state")
    if run(("machinectl", "list", "--no-legend"), False).stdout.strip():
        raise BrokerError("Hub bootstrap refuses an existing Environment machine")
    if registration("hub").get("state") != "stopped" or registration("test").get("state") != "stopped":
        raise BrokerError("Hub bootstrap requires both registrations stopped")
    descriptor, session_id = publish_descriptor("hub")
    start("hub", descriptor, session_id)
    return {"classification": "bootstrap-complete", "logical_name": "hub",
            "generation": HUB_GENERATION, "single_owner": True,
            "watchdog_active": True, "recovery_verified": True}


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--handoff", choices=("hub-to-test", "test-to-hub"))
    mode.add_argument("--bootstrap-hub", action="store_true")
    parser.add_argument("--hub-generation", required=True); parser.add_argument("--test-generation", required=True)
    args = parser.parse_args()
    if os.geteuid() != 0 or (args.hub_generation, args.test_generation) != (HUB_GENERATION, TEST_GENERATION):
        raise BrokerError("broker identity or privilege differs")
    STATE.mkdir(mode=0o755, parents=True, exist_ok=True)
    lock_fd = os.open(LOCK, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        result = bootstrap_hub() if args.bootstrap_hub else handoff(args.handoff)
    finally:
        os.close(lock_fd); LOCK.unlink(missing_ok=True)
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
