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
REGISTRATION = Path(f"/var/lib/apx/environments/{launch.ENVIRONMENT}/registration.json")
OBSERVE_SECONDS = 45


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
    if os.geteuid() != 0 or RESULT.exists():
        raise H0LaunchError("H0 launch requires root and an absent exact result")
    registration = json.loads(REGISTRATION.read_text())
    if registration.get("generation") != launch.GENERATION or registration.get("state") != "stopped" or registration.get("role") != "graphical-h0":
        raise H0LaunchError("H0 registration changed or is not stopped")
    plan = launch.build_launch_plan(device.build_device_lease_plan(_exact_observation()))
    if plan.plan_digest != "8e1096161261b68b1bb0b4d540eb78502860b88948c8f035fafc222085026fb0":
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


def _write_result(value: dict[str, object]) -> None:
    data = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
    descriptor = os.open(RESULT, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o400)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(data); stream.flush(); os.fsync(stream.fileno())


def execute_h0() -> dict[str, object]:
    plan = _preflight()
    timer_started = graphical_started = hyprland_observed = foot_observed = machine_observed = False
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
            if _run(["systemctl", "is-active", f"{launch.GRAPHICAL_UNIT}.service"], check=False).stdout.strip() not in {"active", "activating"}:
                break
            time.sleep(0.25)
    finally:
        _run([str(STATE / "watchdog"), "--expire"], check=False)
        _run(["systemctl", "stop", f"{launch.EXPIRY_UNIT}.timer", f"{launch.EXPIRY_UNIT}.service"], check=False)
    tty1 = _run(["fgconsole"]).stdout.strip() == "1"
    machine_absent = _run(["machinectl", "show", launch.MACHINE, "--property=State", "--value"], check=False).returncode != 0
    unit_inactive = _run(["systemctl", "is-active", f"{launch.GRAPHICAL_UNIT}.service"], check=False).stdout.strip() not in {"active", "activating"}
    result = {
        "schema": 1, "experiment": launch.EXPERIMENT, "generation": launch.GENERATION,
        "plan_digest": plan.plan_digest, "timer_started_before_graphics": timer_started,
        "graphical_unit_started": graphical_started, "machine_observed": machine_observed,
        "hyprland_process_observed": hyprland_observed,
        "visual_marker_process_observed": foot_observed, "tty1_restored": tty1,
        "machine_absent_after": machine_absent, "graphical_unit_inactive_after": unit_inactive,
        "classification": "h0-visual-marker-observed-and-headless-restored" if all((timer_started, graphical_started, machine_observed, hyprland_observed, foot_observed, tty1, machine_absent, unit_inactive)) else "bounded-negative-or-incomplete-headless-restored",
    }
    _write_result(result)
    return result


if __name__ == "__main__":
    print(json.dumps(execute_h0(), sort_keys=True, indent=2))
