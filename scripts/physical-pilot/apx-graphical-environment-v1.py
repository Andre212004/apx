#!/usr/bin/env python3
"""Launch an admitted non-Hub graphical Environment through the proven device path."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import time


NAME = re.compile(r"[a-z](?:[a-z0-9]|-(?=[a-z0-9])){0,26}")
SOURCE = Path(__file__).with_name("apx-official-hub-graphical-v1.py")
INSTALLED_SOURCE = Path("/var/lib/apx/official-hub-v1/apx-official-hub-graphical-v1.py")
GENERIC_INSTALLED = Path("/usr/lib/apx/apx-graphical-environment-v1.py")
PROVEN_SESSION = Path("/var/lib/apx/official-hub-v1/apx-official-hub-session-v1.sh")
ACTIVE = Path("/run/apx/active-graphical-environment-v1.json")
KVM_CAPABILITY_NAME = "kvm-v1"
KVM_CAPABILITY_CONTENT = b"apx-kvm-v1\n"
VM_CAPABILITY_NAME = "virtual-machine-v1"
VM_CAPABILITY_CONTENT = b"apx-virtual-machine-v1\n"
VFIO_CAPABILITY_NAME = "vfio-pci-v1.json"
VFIO_STATE = Path("/run/apx/vfio-pci-environment-v1.json")
VFIO_PROFILE = "apx-vfio-pci-v1"
VM_FORBIDDEN_PROCESSES = (
    b"quickshell", b"waybar", b"hypridle", b"hyprlock",
    b"pipewire-pulse", b"xdg-desktop-por",
)


def load_engine():
    # The installed generic launcher and the HUB must share one canonical
    # engine. A stale sibling in /usr/lib/apx previously shadowed the live
    # engine and applied pre-VFIO graphics policy after binding the RTX.
    path = INSTALLED_SOURCE if Path(__file__).resolve() == GENERIC_INSTALLED \
        else (SOURCE if SOURCE.is_file() else INSTALLED_SOURCE)
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


def trusted_vfio_capability(environment: Path) -> dict[str, object] | None:
    path = environment / VFIO_CAPABILITY_NAME
    if not path.exists():
        return None
    metadata = path.lstat(); data = path.read_bytes()
    if path.is_symlink() or not path.is_file() or metadata.st_uid != 0 or metadata.st_gid != 0 \
            or stat.S_IMODE(metadata.st_mode) != 0o400 or not data or len(data) > 2048:
        raise RuntimeError("untrusted Environment VFIO capability")
    value = json.loads(data)
    expected_devices = (
        {"address": "0000:01:00.0", "vendor": "0x10de", "device": "0x2560", "driver": "nvidia"},
        {"address": "0000:01:00.1", "vendor": "0x10de", "device": "0x228e", "driver": "snd_hda_intel"},
    )
    if type(value) is not dict or set(value) != {"schema", "profile", "group", "devices"} \
            or value.get("schema") != 1 or value.get("profile") != VFIO_PROFILE \
            or value.get("group") != 11 or tuple(value.get("devices", ())) != expected_devices:
        raise RuntimeError("Environment VFIO capability differs from the admitted RTX group")
    return value


def _atomic_vfio_state(value: dict[str, object]) -> None:
    VFIO_STATE.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
    temporary = VFIO_STATE.with_name(f".{VFIO_STATE.name}.{os.getpid()}.tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        os.write(descriptor, (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode())
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    os.replace(temporary, VFIO_STATE)


def _trusted_vfio_state() -> dict[str, object]:
    metadata = VFIO_STATE.lstat(); data = VFIO_STATE.read_bytes()
    if VFIO_STATE.is_symlink() or not VFIO_STATE.is_file() or metadata.st_uid != 0 \
            or metadata.st_gid != 0 or stat.S_IMODE(metadata.st_mode) != 0o600 \
            or not data or len(data) > 2048:
        raise RuntimeError("untrusted active VFIO state")
    value = json.loads(data)
    if type(value) is not dict or set(value) != {"schema", "profile", "phase", "group", "devices"} \
            or value.get("schema") != 1 or value.get("profile") != VFIO_PROFILE \
            or value.get("phase") not in {"binding", "active"} or value.get("group") != 11 \
            or type(value.get("devices")) is not list:
        raise RuntimeError("active VFIO state differs")
    return value


def _write_sysfs(path: Path, value: str) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_NOFOLLOW)
    try:
        os.write(descriptor, value.encode())
    finally:
        os.close(descriptor)


def activate_vfio(capability: dict[str, object]) -> tuple[str, ...]:
    if "iommu=pt" not in Path("/proc/cmdline").read_text().split() \
            or not Path("/sys/kernel/iommu_groups/11").is_dir():
        raise RuntimeError("the signed APX IOMMU boot is not active")
    if VFIO_STATE.exists():
        raise RuntimeError("a previous VFIO lease still exists")
    machines = subprocess.run(("machinectl", "list", "--no-legend"), text=True,
                              capture_output=True, check=False)
    if machines.returncode or machines.stdout.strip():
        raise RuntimeError("VFIO activation requires every Environment to be stopped")
    devices = capability["devices"]
    group_members = {
        path.name for path in Path("/sys/kernel/iommu_groups/11/devices").iterdir()
    }
    if group_members != {item["address"] for item in devices}:
        raise RuntimeError("the RTX IOMMU group changed")
    state_devices: list[dict[str, str]] = []
    for item in devices:
        address = item["address"]; device_path = Path("/sys/bus/pci/devices") / address
        observed_driver = device_path.joinpath("driver").resolve().name
        if device_path.joinpath("vendor").read_text().strip() != item["vendor"] \
                or device_path.joinpath("device").read_text().strip() != item["device"] \
                or observed_driver != item["driver"]:
            raise RuntimeError(f"VFIO source identity differs for {address}")
        state_devices.append({"address": address, "driver": observed_driver})
    state = {"schema": 1, "profile": VFIO_PROFILE, "phase": "binding",
             "group": 11, "devices": state_devices}
    _atomic_vfio_state(state)
    subprocess.run(("modprobe", "vfio-pci"), check=True)
    try:
        for item in state_devices:
            address = item["address"]; device_path = Path("/sys/bus/pci/devices") / address
            _write_sysfs(device_path / "driver_override", "vfio-pci\n")
            _write_sysfs(device_path / "driver/unbind", address)
            _write_sysfs(Path("/sys/bus/pci/drivers_probe"), address)
            if device_path.joinpath("driver").resolve().name != "vfio-pci":
                raise RuntimeError(f"VFIO did not claim {address}")
        group_node = Path("/dev/vfio/11")
        control_node = Path("/dev/vfio/vfio")
        if not group_node.exists() or not control_node.exists() \
                or not stat.S_ISCHR(group_node.stat().st_mode) \
                or not stat.S_ISCHR(control_node.stat().st_mode):
            raise RuntimeError("the exact VFIO group device was not published")
        state["phase"] = "active"; _atomic_vfio_state(state)
        nodes = ["/dev/kvm", "/dev/vfio/vfio", "/dev/vfio/11"]
        if Path("/dev/kvmfr0").exists():
            metadata = Path("/dev/kvmfr0").stat()
            if not stat.S_ISCHR(metadata.st_mode):
                raise RuntimeError("Looking Glass KVMFR identity differs")
            nodes.append("/dev/kvmfr0")
        return tuple(nodes)
    except Exception:
        restore_vfio()
        raise


def restore_vfio() -> None:
    if not VFIO_STATE.exists():
        return
    state = _trusted_vfio_state()
    failures: list[str] = []
    for item in reversed(state["devices"]):
        address = item.get("address"); original = item.get("driver")
        if type(address) is not str or type(original) is not str:
            raise RuntimeError("active VFIO device state differs")
        device_path = Path("/sys/bus/pci/devices") / address
        try:
            current_link = device_path / "driver"
            if current_link.exists() and current_link.resolve().name == "vfio-pci":
                _write_sysfs(current_link / "unbind", address)
            _write_sysfs(device_path / "driver_override", "\n")
            _write_sysfs(Path("/sys/bus/pci/drivers_probe"), address)
            if device_path.joinpath("driver").resolve().name != original:
                failures.append(address)
        except OSError:
            failures.append(address)
    if failures:
        raise RuntimeError("the Host drivers were not restored for: " + ",".join(failures))
    VFIO_STATE.unlink()


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
    kvm_capability = environment / KVM_CAPABILITY_NAME
    if kvm_capability.exists():
        metadata = kvm_capability.lstat()
        if kvm_capability.is_symlink() or not kvm_capability.is_file() \
                or metadata.st_uid != 0 or metadata.st_gid != 0 \
                or stat.S_IMODE(metadata.st_mode) != 0o400 \
                or kvm_capability.read_bytes() != KVM_CAPABILITY_CONTENT:
            raise RuntimeError("untrusted Environment KVM capability")
        engine.EXTRA_DEVICE_NODES = ("/dev/kvm",)
    else:
        engine.EXTRA_DEVICE_NODES = ()
    vm_capability = environment / VM_CAPABILITY_NAME
    virtual_machine = vm_capability.exists()
    if virtual_machine:
        metadata = vm_capability.lstat()
        if vm_capability.is_symlink() or not vm_capability.is_file() \
                or metadata.st_uid != 0 or metadata.st_gid != 0 \
                or stat.S_IMODE(metadata.st_mode) != 0o400 \
                or vm_capability.read_bytes() != VM_CAPABILITY_CONTENT \
                or not kvm_capability.exists():
            raise RuntimeError("untrusted Environment virtual-machine capability")
    vfio_capability = trusted_vfio_capability(environment)
    if vfio_capability is not None and not virtual_machine:
        raise RuntimeError("VFIO requires an admitted virtual-machine Environment")
    engine.VFIO_GUEST_MODE = vfio_capability is not None
    if virtual_machine:
        # A VM surface needs only the authenticated return broker. Do not
        # expose desktop summaries, model control, Host menus or audio-state
        # authority to a session that has no Linux desktop shell.
        engine.HOST_SERVICES_ENABLED = False
        engine.AUDIO_STATE_ENABLED = False
        engine.MODEL_STORE_ENABLED = False
        engine.LEASED_SERVICE_SOCKETS = (engine.ENVIRONMENT_SWITCH_SOCKET,)
        # The v2 runtime measures the actual admitted CPU and RAM. The outer
        # unit no longer imposes the old 8-vCPU/12-GiB shape: it may use the
        # full 12-thread budget and up to 26 GiB, while the runtime itself
        # reserves one physical core and at least 5 GiB for Host presentation.
        engine.HUB_CPU_QUOTA = "1200%"
        engine.HUB_MEMORY_HIGH = "24G"
        engine.HUB_MEMORY_MAX = "26G"
        engine.VFIO_MEMLOCK_LIMIT = "24G"
    else:
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
        if virtual_machine:
            # The v2 VM has no second readiness protocol. The already-proven
            # Hyprland owner session is the boundary; its one runtime owns QEMU
            # and Looking Glass, reports a visible local error, and exits the
            # compositor on guest shutdown or failure. systemd then tears down
            # the complete cgroup before APX restores the Hub and the RTX.
            unexpected = tuple(
                process.decode() for process in VM_FORBIDDEN_PROCESSES
                if process_pids(process)
            )
            if unexpected:
                raise engine.OfficialHubGraphicalError(
                    "the minimal VM session started forbidden desktop services: "
                    + ",".join(unexpected)
                )
            if len(process_pids(b"Hyprland")) != 1:
                raise engine.OfficialHubGraphicalError("the VM owner compositor is not active")
            return "virtual-machine"
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
        arguments = ["systemd-run", "-M", engine.MACHINE, f"--unit={engine.INNER_UNIT}",
                     "--property=Type=simple", "--property=KillMode=mixed", "--property=TimeoutStopSec=3s"]
        if engine.VFIO_GUEST_MODE:
            arguments.append(f"--property=LimitMEMLOCK={engine.VFIO_MEMLOCK_LIMIT}")
        arguments.extend(f"--setenv=APX_{label.upper()}_DEVICE={node}" for label, node in inputs.items())
        arguments.extend(f"--setenv=APX_{label.upper()}_DEVICE={node}" for label, node in audio.items())
        arguments.extend((f"--setenv=APX_GPU_POLICY={graphics['policy']}",
                          f"--setenv=APX_DISPLAY_CARD={graphics['display_card']}",
                          f"--setenv=APX_DISPLAY_RENDER={graphics['display_render']}"))
        if "offload_render" in graphics:
            arguments.append(f"--setenv=APX_NVIDIA_CARD_DEVICE={graphics['offload_card']}")
            arguments.append(f"--setenv=APX_NVIDIA_RENDER_DEVICE={graphics['offload_render']}")
        arguments.extend(("--setenv=APX_HYPRLAND_CONFIG=/home/apx/.config/hypr/hyprland.lua",
                          f"--setenv=APX_SESSION_MODE={'virtual-machine' if virtual_machine else 'desktop'}",
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
    # Recovery publishes the Environment as stopped, which wakes the Hub
    # autostart service.  A VFIO guest must return its display GPU first or the
    # Hub can race the driver rebind and fail while identifying its card.
    engine.before_publish_stopped = restore_vfio if vfio_capability is not None else lambda: None
    record["_vfio_capability"] = vfio_capability
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
    engine = load_engine(); record = configure(engine, args.environment)
    vfio_capability = record.pop("_vfio_capability")
    if args.recover:
        engine.recover(); restore_vfio(); return 0
    engine.arm_test_expiry = lambda _seconds: None
    if args.authenticated_handoff and not args.interactive:
        parser.error("authenticated handoff requires interactive mode")
    if vfio_capability is not None:
        engine.EXTRA_DEVICE_NODES = activate_vfio(vfio_capability)
    try:
        result = engine.launch(args.test, args.authenticated_handoff)
    finally:
        if vfio_capability is not None:
            restore_vfio()
    if args.test:
        result.update({"desktop_shell": "virtual-machine" if (engine.ENVIRONMENT / VM_CAPABILITY_NAME).exists() else "quickshell",
                       "quickshell": not (engine.ENVIRONMENT / VM_CAPABILITY_NAME).exists(),
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
