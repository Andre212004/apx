"""Execute only the exact owner-approved physical Hyprland H0 v2 run."""

from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import time

import apx_hyprland_h0_device_lease as device
import apx_hyprland_h0_launch_plan as launch


STATE = Path(launch.STATE)
RESULT = STATE / "physical-result.json"
DIAGNOSTIC_LOG = STATE / "hyprland-diagnostic.log"
COMPOSITOR_STATE = STATE / "hyprland-state.json"
REGISTRATION = Path(f"/var/lib/apx/environments/{launch.ENVIRONMENT}/registration.json")
OBSERVE_SECONDS = 10
# Physical H0 is deliberately locked after the 2026-07-18 recovery UX incident.
# Re-enabling requires a reviewed short-deadline design and a non-graphical
# rehearsal; owner authorization alone must not bypass this code interlock.
PHYSICAL_RUN_ENABLED = False


class H0LaunchError(RuntimeError):
    pass


def _run(arguments: tuple[str, ...] | list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(arguments, text=True, capture_output=True, check=False, env={**os.environ, "LC_ALL": "C"})
    if check and result.returncode != 0:
        raise H0LaunchError(f"fixed command failed: {arguments[0]}: {result.stderr[-500:]}")
    return result


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _exact_observation() -> device.H0DeviceObservation:
    return device.H0DeviceObservation(
        device.GENERATION,
        "dc1beaaaf6f073f8c3493d2e6b1d001e4b5f07f431f8a522f2125f242151ea40",
        "0000:05:00.0", "amdgpu", "card2-eDP-2", True, True, True, True,
        True, True, True, True,
        tuple((name, host, major, minor) for name, host, _, major, minor, _ in device.DEVICES),
    )


def _preflight() -> launch.H0LaunchPlan:
    if not PHYSICAL_RUN_ENABLED:
        raise H0LaunchError("physical H0 is safety-locked pending a shorter reviewed recovery design")
    if os.geteuid() != 0 or RESULT.exists():
        raise H0LaunchError("H0 launch requires root and an absent exact result")
    registration = json.loads(REGISTRATION.read_text())
    if registration.get("generation") != launch.GENERATION or registration.get("state") != "stopped" or registration.get("role") != "graphical-h0":
        raise H0LaunchError("H0 registration changed or is not stopped")
    plan = launch.build_launch_plan(device.build_device_lease_plan(_exact_observation()))
    if plan.plan_digest != "c360cc97adce381b56368bde6db034cd685f6d05c688e33719ef4d57f62a9026":
        raise H0LaunchError("H0 launch plan identity changed")
    for name, digest, mode in launch.ASSETS:
        path = STATE / name
        info = path.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or stat.S_IMODE(info.st_mode) != mode or _sha(path) != digest:
            raise H0LaunchError("staged H0 asset changed")
    for name, host, _, major, minor, _ in device.DEVICES:
        info = Path(host).stat()
        if not stat.S_ISCHR(info.st_mode) or os.major(info.st_rdev) != major or os.minor(info.st_rdev) != minor:
            raise H0LaunchError(f"H0 device identity changed: {name}")
        if name in launch.BIND_SOURCES and Path(host).resolve() != Path(launch.BIND_SOURCES[name]):
            raise H0LaunchError(f"stable H0 input path resolved to a different event: {name}")
    if Path("/sys/class/drm/card2-eDP-2/status").read_text().strip() != "connected":
        raise H0LaunchError("internal AMD connector is not connected")
    if not Path("/sys/class/drm/card2/device/driver").resolve().name == "amdgpu":
        raise H0LaunchError("card2 is not owned by amdgpu")
    if _run(["fgconsole"]).stdout.strip() != "1":
        raise H0LaunchError("tty1 is not the active recovery console")
    if _run(["systemctl", "is-active", "display-manager.service"], check=False).stdout.strip() == "active":
        raise H0LaunchError("a display manager is active")
    if _run(["systemctl", "is-active", f"{launch.GRAPHICAL_UNIT}.service"], check=False).stdout.strip() in {"active", "activating"}:
        raise H0LaunchError("old H0 graphical unit is active")
    if _run(["machinectl", "show", launch.MACHINE, "--property=State", "--value"], check=False).returncode == 0:
        raise H0LaunchError("old H0 machine is registered")
    if _run(["systemctl", "--failed", "--no-legend"], check=False).stdout.strip():
        raise H0LaunchError("Host has failed units")
    return plan


def _process_present(executable: bytes) -> bool:
    for item in Path("/proc").iterdir():
        if not item.name.isdigit():
            continue
        try:
            arguments = (item / "cmdline").read_bytes().split(b"\0")
        except OSError:
            continue
        if executable in arguments:
            return True
    return False


def _runtime_observation() -> tuple[bool, bytes, dict[str, object]]:
    """Read bounded evidence through Hyprland's proc root while it is alive."""
    socket_observed = False
    log = b""
    state: dict[str, object] = {}
    for item in Path("/proc").iterdir():
        if not item.name.isdigit():
            continue
        try:
            arguments = (item / "cmdline").read_bytes().split(b"\0")
            if b"/usr/bin/Hyprland" not in arguments:
                continue
            runtime = item / "root/run/user/1000/hypr"
            for candidate in runtime.glob("*/.socket.sock"):
                socket_observed |= stat.S_ISSOCK(candidate.stat().st_mode)
                signature = candidate.parent.name
                for query in ("monitors", "clients"):
                    answer = _run([
                        "/usr/bin/nsenter", "--target", item.name, "--mount", "--pid", "--",
                        "/usr/bin/env", "XDG_RUNTIME_DIR=/run/user/1000",
                        f"HYPRLAND_INSTANCE_SIGNATURE={signature}",
                        "/usr/bin/hyprctl", "-j", query,
                    ], check=False)
                    if answer.returncode == 0:
                        try:
                            state[query] = json.loads(answer.stdout)
                        except json.JSONDecodeError:
                            pass
            for candidate in runtime.glob("*/hyprland.log"):
                log = candidate.read_bytes()[:262144]
        except OSError:
            continue
    return socket_observed, log, state


def _write_result(value: dict[str, object]) -> None:
    data = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
    descriptor = os.open(RESULT, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o400)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(data); stream.flush(); os.fsync(stream.fileno())


def execute_h0() -> dict[str, object]:
    plan = _preflight()
    timer_started = graphical_started = hyprland_observed = foot_observed = machine_observed = False
    wayland_socket_observed = False
    diagnostic_log = b""
    compositor_state: dict[str, object] = {}
    try:
        _run(plan.expiry_command)
        timer_started = _run(["systemctl", "is-active", f"{launch.EXPIRY_UNIT}.timer"]).stdout.strip() == "active"
        if not timer_started:
            raise H0LaunchError("independent expiry timer did not become active")
        _run(["/usr/bin/chvt", "2"])
        _run(plan.graphical_command)
        graphical_started = True
        deadline = time.monotonic() + OBSERVE_SECONDS
        while time.monotonic() < deadline:
            machine = _run(["machinectl", "show", launch.MACHINE, "--property=State", "--value"], check=False)
            machine_observed |= machine.returncode == 0 and machine.stdout.strip() in {"running", "degraded"}
            hyprland_observed |= _process_present(b"/usr/bin/Hyprland")
            foot_observed |= _process_present(b"/usr/bin/foot")
            socket_now, log_now, state_now = _runtime_observation()
            wayland_socket_observed |= socket_now
            if log_now:
                diagnostic_log = log_now
            if state_now:
                compositor_state = state_now
            if _run(["systemctl", "is-active", f"{launch.GRAPHICAL_UNIT}.service"], check=False).stdout.strip() not in {"active", "activating"}:
                break
            time.sleep(0.25)
    finally:
        _run([str(STATE / "watchdog"), "--expire"], check=False)
        _run(["systemctl", "stop", f"{launch.EXPIRY_UNIT}.timer", f"{launch.EXPIRY_UNIT}.service"], check=False)
    tty1 = _run(["fgconsole"]).stdout.strip() == "1"
    machine_absent = _run(["machinectl", "show", launch.MACHINE, "--property=State", "--value"], check=False).returncode != 0
    unit_inactive = _run(["systemctl", "is-active", f"{launch.GRAPHICAL_UNIT}.service"], check=False).stdout.strip() not in {"active", "activating"}
    if diagnostic_log:
        descriptor = os.open(DIAGNOSTIC_LOG, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o400)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(diagnostic_log); stream.flush(); os.fsync(stream.fileno())
    if compositor_state:
        _write_result_file = (json.dumps(compositor_state, sort_keys=True, separators=(",", ":")) + "\n").encode()
        descriptor = os.open(COMPOSITOR_STATE, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o400)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(_write_result_file); stream.flush(); os.fsync(stream.fileno())
    monitors = compositor_state.get("monitors", [])
    monitor_observed = isinstance(monitors, list) and any(
        isinstance(monitor, dict) and monitor.get("name") == "eDP-2" and not monitor.get("disabled", False)
        for monitor in monitors
    )
    result = {
        "schema": 1, "experiment": launch.EXPERIMENT, "generation": launch.GENERATION,
        "plan_digest": plan.plan_digest, "timer_started_before_graphics": timer_started,
        "graphical_unit_started": graphical_started, "machine_observed": machine_observed,
        "hyprland_process_observed": hyprland_observed,
        "wayland_socket_observed": wayland_socket_observed,
        "monitor_log_observed": monitor_observed,
        "diagnostic_log_preserved": bool(diagnostic_log),
        "visual_marker_process_observed": foot_observed, "tty1_restored": tty1,
        "machine_absent_after": machine_absent, "graphical_unit_inactive_after": unit_inactive,
        "classification": "h0-visual-marker-observed-and-headless-restored" if all((timer_started, graphical_started, machine_observed, hyprland_observed, wayland_socket_observed, monitor_observed, foot_observed, tty1, machine_absent, unit_inactive)) else "bounded-negative-or-incomplete-headless-restored",
    }
    _write_result(result)
    return result


if __name__ == "__main__":
    print(json.dumps(execute_h0(), sort_keys=True, indent=2))
