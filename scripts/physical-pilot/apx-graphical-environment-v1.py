#!/usr/bin/env python3
"""Launch an admitted non-Hub graphical Environment through the proven device path."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import time


NAME = re.compile(r"[a-z](?:[a-z0-9]|-(?=[a-z0-9])){0,26}")
SOURCE = Path(__file__).with_name("apx-official-hub-graphical-v1.py")
INSTALLED_SOURCE = Path("/var/lib/apx/official-hub-v1/apx-official-hub-graphical-v1.py")
GENERIC_INSTALLED = Path("/usr/lib/apx/apx-graphical-environment-v1.py")
PROVEN_SESSION = Path("/var/lib/apx/official-hub-v1/apx-official-hub-session-v1.sh")
ACTIVE = Path("/run/apx/active-graphical-environment-v1.json")


def load_engine():
    path = SOURCE if SOURCE.is_file() else INSTALLED_SOURCE
    spec = importlib.util.spec_from_file_location("apx_graphical_engine", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("the proven graphical engine is unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def trusted_registration(environment: Path) -> dict[str, object]:
    path = environment / "registration.json"
    metadata = path.lstat(); data = path.read_bytes()
    if path.is_symlink() or not path.is_file() or metadata.st_uid != 0 or metadata.st_gid != 0 \
            or not data or len(data) > 8192:
        raise RuntimeError("untrusted graphical Environment registration")
    value = json.loads(data)
    if type(value) is not dict:
        raise RuntimeError("graphical Environment registration is malformed")
    return value


def configure(engine, name: str) -> dict[str, object]:
    if NAME.fullmatch(name) is None or name == "hub":
        raise RuntimeError("the general launcher requires a named non-Hub Environment")
    environment = Path("/var/lib/apx/environments") / name
    record = trusted_registration(environment)
    if record.get("name") != name or record.get("role") != "graphical-base" \
            or record.get("release") != "hyprland-base-v2" \
            or record.get("state") not in {"stopped", "running"}:
        raise RuntimeError("Environment is not an admitted graphical-base instance")
    generation = str(record.get("generation"))
    if re.fullmatch(r"[0-9a-f]{8}-[0-9a-f-]{27}", generation) is None:
        raise RuntimeError("graphical Environment generation differs")
    short = generation.split("-", 1)[0]
    network_identity = "g" + short[:7]
    engine.GENERATION = generation
    engine.RELEASE = "hyprland-base-v2"
    # Linux veth names are limited to 15 characters.  Bind the runtime machine
    # and network identity to the trusted generation, so long logical names do
    # not collide after truncation.
    engine.MACHINE = "apx-" + network_identity
    engine.OUTER_UNIT = f"apx-graphical-{name}-{short}"
    engine.INNER_UNIT = "apx-graphical-hyprland"
    engine.SEATD_UNIT = "apx-graphical-seatd"
    engine.EXPIRY_UNIT = f"apx-graphical-{name}-expiry"
    engine.WATCHDOG_UNIT = f"apx-graphical-{name}-watchdog"
    engine.ENVIRONMENT = environment
    engine.REGISTRATION = environment / "registration.json"
    engine.ROOT = environment / "root"
    engine.HOME = environment / "home"
    engine.CONFIG = engine.HOME / "apx/.config/hyprland/hyprland.conf"
    engine.SESSION = PROVEN_SESSION
    engine.INSTALLED = GENERIC_INSTALLED
    engine.ACTIVE = ACTIVE
    engine.WATCHDOG_STATE = Path(f"/run/apx/graphical-{name}-watchdog-v1.json")
    engine.DEVICE_LEASE_DIR = Path("/dev/apx-graphical-device-leases-v1")
    engine.DEVICE_LEASE_STATE = engine.DEVICE_LEASE_DIR / "state.json"
    engine.HOST_CONSOLE_ENABLED = False
    engine.UPDATE_ENABLED = False
    engine.POWER_ENABLED = False
    engine.LEASED_SERVICE_SOCKETS = tuple(
        endpoint for endpoint in engine.LEASED_SERVICE_SOCKETS
        if endpoint not in {engine.HOST_CONSOLE_SOCKET, engine.UPDATE_SOCKET, engine.POWER_SOCKET}
    )

    original_run = engine.run

    def routed_run(arguments: tuple[str, ...], check: bool = True):
        values = list(arguments)
        if len(values) >= 4 and values[0] == str(engine.NETWORK) \
                and values[-2:] == ["--environment", "hub"]:
            values[-1] = network_identity
        return original_run(tuple(values), check)

    def read_registration() -> dict[str, object]:
        current = trusted_registration(environment)
        if (current.get("name"), current.get("role"), current.get("release"),
                current.get("generation")) != (name, "graphical-base", "hyprland-base-v2", generation):
            raise engine.OfficialHubGraphicalError("graphical Environment identity changed")
        return current

    def publish_active_state(pid: int) -> None:
        ACTIVE.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
        temporary = ACTIVE.with_name(f".{ACTIVE.name}.{os.getpid()}.tmp")
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        try:
            payload = {"schema": 1, "profile": "apx-active-graphical-environment-v1",
                       "name": name, "role": "graphical-base", "generation": generation,
                       "unit": engine.OUTER_UNIT + ".service", "pid": pid}
            os.write(descriptor, (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode())
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        os.replace(temporary, ACTIVE)

    def process_pids(process_name: bytes) -> list[int]:
        result: list[int] = []
        unit_path = f"/system.slice/{engine.OUTER_UNIT}.service"
        for entry in Path("/proc").iterdir():
            if not entry.name.isdecimal():
                continue
            try:
                if (entry / "comm").read_bytes().strip() == process_name and any(
                    line.split(":", 2)[-1].startswith(unit_path)
                    for line in (entry / "cgroup").read_text().splitlines()
                ):
                    result.append(int(entry.name))
            except OSError:
                pass
        return result

    def verify_desktop_shell() -> str:
        deadline = time.monotonic() + 10
        expected = b"quickshell" if (engine.HOME / "apx/.config/quickshell/apx/shell.qml").is_file() \
            or (engine.HOME / "apx/.config/apx/red-shell-v1").is_file() else b"waybar"
        bootstrap_attempted = False
        bootstrap_after = time.monotonic() + 2
        while time.monotonic() < deadline:
            if len(process_pids(expected)) == 1:
                return expected.decode()
            if expected == b"quickshell" and not bootstrap_attempted \
                    and time.monotonic() >= bootstrap_after:
                bootstrap_attempted = True
                pid, signature, _monitor, _keyboards = engine.compositor_state()
                if pid and signature:
                    engine.hyprctl(
                        pid, signature, "dispatch", "exec",
                        "/home/apx/.local/bin/apx-shell-v1",
                    )
            time.sleep(0.1)
        raise engine.OfficialHubGraphicalError("the selected workload shell did not remain active")

    def open_terminal(pid: int, signature: str) -> None:
        # The red handoff trial is an owner-facing session, not a launcher
        # certification run. Keep its shell visible instead of covering it
        # with the historical automatic terminal proof.
        if (engine.HOME / "apx/.config/apx/red-shell-v1").is_file():
            return
        dispatched = engine.hyprctl(pid, signature, "dispatch", "exec", "/usr/bin/alacritty")
        if dispatched.returncode or dispatched.stdout.strip().lower() != "ok":
            raise engine.OfficialHubGraphicalError("Hyprland refused the Alacritty launch")

    def verify_shared_audio() -> None:
        result = routed_run(("systemd-run", "-M", engine.MACHINE, "--quiet", "--pipe", "--wait",
                             "--collect", "--uid=apx", "--", "/run/apx/audio-state-client-v1.py", "get"), False)
        try:
            value = json.loads(result.stdout)
        except json.JSONDecodeError as error:
            raise engine.OfficialHubGraphicalError("shared audio state returned malformed data") from error
        if result.returncode or not all(field in value for field in (
            "profile", "output_volume", "input_volume", "microphone_active"
        )):
            raise engine.OfficialHubGraphicalError("shared audio state proof failed")

    def verify_local_admin(pid: int, uid_base: int) -> None:
        status = dict(line.split(":", 1) for line in Path(f"/proc/{pid}/status").read_text().splitlines() if ":" in line)
        if status.get("Uid", "").split() != [str(uid_base + 1000)] * 4 \
                or status.get("NoNewPrivs", "").strip() != "0":
            raise engine.OfficialHubGraphicalError("graphical user session cannot acquire local authority")
        policy = "apx ALL=(root) NOPASSWD: /usr/bin/id -u\n"
        prepare = ("/usr/bin/printf '%s' '" + policy + "' | /usr/bin/install -m 0440 /dev/stdin "
                   + engine.LOCAL_ADMIN_PROOF)
        routed_run(("machinectl", "shell", f"root@{engine.MACHINE}", "/usr/bin/bash", "-lc", prepare))
        try:
            elevated = routed_run(("systemd-run", "-M", engine.MACHINE, "--quiet", "--pipe", "--wait",
                                   "--collect", "--uid=apx", "--", "/usr/bin/sudo", "-n", "/usr/bin/id", "-u"), False)
            refused = routed_run(("systemd-run", "-M", engine.MACHINE, "--quiet", "--pipe", "--wait",
                                  "--collect", "--uid=root", "--", "/run/apx/host-services-client-v1.py", "json"), False)
            hostname = routed_run(("machinectl", "shell", f"root@{engine.MACHINE}",
                                   "/usr/bin/cat", "/etc/hostname"), False).stdout.strip()
            if elevated.returncode or elevated.stdout.strip() != "0" or refused.returncode == 0 \
                    or hostname not in {"apx-" + name, engine.MACHINE}:
                raise engine.OfficialHubGraphicalError("Environment-local authority proof failed")
        finally:
            routed_run(("machinectl", "shell", f"root@{engine.MACHINE}", "/usr/bin/rm", "-f",
                        engine.LOCAL_ADMIN_PROOF), False)

    def start_inner(inputs: dict[str, str], audio: dict[str, str], graphics: dict[str, str]) -> None:
        arguments = ["systemd-run", "-M", engine.MACHINE, f"--unit={engine.INNER_UNIT}", "--collect",
                     "--property=Type=simple", "--property=KillMode=mixed", "--property=TimeoutStopSec=3s"]
        arguments.extend(f"--setenv=APX_{label.upper()}_DEVICE={node}" for label, node in inputs.items())
        arguments.extend(f"--setenv=APX_{label.upper()}_DEVICE={node}" for label, node in audio.items())
        arguments.extend((f"--setenv=APX_GPU_POLICY={graphics['policy']}",
                          f"--setenv=APX_DISPLAY_CARD={graphics['display_card']}",
                          f"--setenv=APX_DISPLAY_RENDER={graphics['display_render']}"))
        if "offload_render" in graphics:
            arguments.append(f"--setenv=APX_NVIDIA_CARD_DEVICE={graphics['offload_card']}")
            arguments.append(f"--setenv=APX_NVIDIA_RENDER_DEVICE={graphics['offload_render']}")
        arguments.extend(("--setenv=APX_HYPRLAND_CONFIG=/home/apx/.config/hypr/hyprland.lua",
                          "--", "/run/apx/official-hub-session"))
        routed_run(tuple(arguments))

    def no_existing_machine() -> None:
        if engine.machine_running():
            raise engine.OfficialHubGraphicalError("graphical Environment is already running")

    engine.run = routed_run
    engine.read_registration = read_registration
    engine.publish_active_state = publish_active_state
    engine.process_pids = process_pids
    engine.verify_desktop_shell = verify_desktop_shell
    engine.open_and_verify_kitty = open_terminal
    engine.verify_update_and_audio_services = verify_shared_audio
    engine.verify_local_admin = verify_local_admin
    # GPU tools remain Environment-local packages.  The common launcher leases
    # the render node but does not require every workload to install vulkaninfo.
    engine.verify_nvidia_render = lambda _pid: "available-by-policy; verifier-not-installed"
    engine.start_inner = start_inner
    engine.stop_text_hub_if_needed = no_existing_machine
    # No new recovery/watchdog mechanism is introduced in this milestone.
    # The foreground launcher still guarantees its existing finally-cleanup.
    engine.arm_health_watchdog = lambda: None
    return record


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--environment", required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--interactive", action="store_true")
    mode.add_argument("--test", action="store_true")
    mode.add_argument("--recover", action="store_true")
    parser.add_argument("--authenticated-handoff", action="store_true")
    args = parser.parse_args()
    engine = load_engine(); configure(engine, args.environment)
    if args.recover:
        engine.recover(); return 0
    engine.arm_test_expiry = lambda _seconds: None
    if args.authenticated_handoff and not args.interactive:
        parser.error("authenticated handoff requires interactive mode")
    result = engine.launch(args.test, args.authenticated_handoff)
    if args.test:
        result.update({"desktop_shell": "quickshell", "quickshell": True,
                       "kitty": False, "terminal": "alacritty", "coordinated_updates": False,
                       "nvidia_render": False,
                       "system_power_two_step": False})
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"APX graphical Environment refused: {error}", file=os.sys.stderr)
        raise SystemExit(2)
