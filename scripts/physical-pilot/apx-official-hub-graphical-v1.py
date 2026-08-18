#!/usr/bin/env python3
"""Start the owner-built official Hub graphically with bounded Host recovery."""

from __future__ import annotations

import argparse
import ctypes
import fcntl
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
SEATD_UNIT = "apx-official-hub-seatd"
EXPIRY_UNIT = "apx-official-hub-graphical-expiry"
WATCHDOG_UNIT = "apx-official-hub-graphical-watchdog"
ENVIRONMENT = Path("/var/lib/apx/environments/hub")
REGISTRATION = ENVIRONMENT / "registration.json"
ROOT = ENVIRONMENT / "root"
HOME = ENVIRONMENT / "home"
CONFIG = HOME / "apx/.config/hypr/hyprland.lua"
SESSION = Path("/var/lib/apx/official-hub-v1/apx-official-hub-session-v1.sh")
INSTALLED = Path("/var/lib/apx/official-hub-v1/apx-official-hub-graphical-v1.py")
NETWORK = Path("/usr/lib/apx/apx-environment-network-v1.py")
HOST_SERVICES_SOCKET = Path("/run/apx/host-services-v1.sock")
HOST_SERVICES_CLIENT = Path("/usr/lib/apx/apx-host-services-client-v1.py")
HOST_SERVICES_CONTRACT = Path("/usr/lib/apx/apx_host_services_contract.py")
HOST_SERVICES_V2_SOCKET = Path("/run/apx/host-services-v2.sock")
HOST_SERVICES_V2_CLIENT = Path("/usr/lib/apx/apx-host-services-client-v2.py")
HOST_SERVICES_V2_CONTRACT = Path("/usr/lib/apx/apx_host_services_v2_contract.py")
HOST_SERVICES_V3_SOCKET = Path("/run/apx/host-services-v3.sock")
HOST_SERVICES_V3_CLIENT = Path("/usr/lib/apx/apx-host-services-client-v3.py")
HOST_SERVICES_V3_CONTRACT = Path("/usr/lib/apx/apx_host_services_v3_contract.py")
HOST_SERVICES_UI_V3 = Path("/usr/lib/apx/apx-host-services-ui-v3.py")
DESKTOP_MENU_V2 = Path("/usr/lib/apx/apx-desktop-menu-v2.py")
AUDIO_STATE_SOCKET = Path("/run/apx/audio-state-v1.sock")
AUDIO_STATE_CLIENT = Path("/usr/lib/apx/apx-audio-state-client-v1.py")
AUDIO_STATE_CONTRACT = Path("/usr/lib/apx/apx_audio_state_contract.py")
UPDATE_SOCKET = Path("/run/apx/coordinated-update-v1.sock")
UPDATE_CLIENT = Path("/usr/lib/apx/apx-coordinated-update-client-v1.py")
POWER_SOCKET = Path("/run/apx/system-power-v1.sock")
POWER_CLIENT = Path("/usr/lib/apx/apx-system-power-client-v1.py")
POWER_CONTRACT = Path("/usr/lib/apx/apx_system_power_contract.py")
MODEL_STORE_SOCKET = Path("/run/apx/model-store-control-v1.sock")
MODEL_STORE_CLIENT = Path("/usr/lib/apx/apx-model-store-client-v1.py")
BRIGHTNESS_KEYS = Path("/usr/lib/apx/apx-legion-brightness-keys-v1.py")
HOST_CONSOLE_SOCKET = Path("/run/apx/host-console-v1.sock")
HOST_CONSOLE_CLIENT = Path("/usr/lib/apx/apx-host-console-client-v1.py")
HOST_CONSOLE_CONTRACT = Path("/usr/lib/apx/apx_host_console_contract.py")
HOST_CONSOLE_ENABLED = True
ENVIRONMENT_SWITCH_SOCKET = Path("/run/apx/environment-switch-v1.sock")
ENVIRONMENT_SWITCH_CLIENT = Path("/usr/lib/apx/apx-environment-switch-client-v1.py")
ENVIRONMENT_SWITCH_CONTRACT = Path("/usr/lib/apx/apx_environment_switch_contract.py")
ENVIRONMENT_FEATURES = Path("/usr/lib/apx/apx_environment_features.py")
UPDATE_ENABLED = True
POWER_ENABLED = POWER_SOCKET.is_socket()
HANDOFF_PROOF = Path("/run/apx/authenticated-handoff-v1")
ACTIVE = Path("/run/apx/official-hub-graphical-v1.json")
WATCHDOG_STATE = Path("/run/apx/official-hub-graphical-watchdog-v1.json")
SESSION_RUNTIME = "/run/apx/session-1000"
RECOVERY_LOCK = Path("/run/apx/official-hub-recovery-v1.lock")
DEVICE_LEASE_DIR = Path("/dev/apx-official-hub-device-leases-v1")
DEVICE_LEASE_STATE = DEVICE_LEASE_DIR / "state.json"
USER_NAMESPACE_LENGTH = 65536
LOCAL_ADMIN_PROOF = "/etc/sudoers.d/11-apx-graphical-proof"
SEATD_SOCKET = Path("/run/seatd.sock")
HUB_CPU_QUOTA = "600%"
HUB_CPU_WEIGHT = "200"
HUB_IO_WEIGHT = "200"
HUB_MEMORY_HIGH = "10G"
HUB_MEMORY_MAX = "12G"
HUB_TASKS_MAX = "4096"
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
AUDIO_ID_PATH = "pci-0000:05:00.6"
AMD_PCI = "0000:05:00.0"
NVIDIA_PCI = "0000:01:00.0"
HARDWARE_PROFILE = Path("/var/lib/apx/system-power-v1/hardware-profile.json")
BOOT_ID = Path("/proc/sys/kernel/random/boot_id")


class OfficialHubGraphicalError(RuntimeError):
    pass


def run(arguments: tuple[str, ...], check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        arguments, check=False, text=True, capture_output=True, input="",
        env={"PATH": "/usr/bin:/usr/local/bin", "LC_ALL": "C"},
    )
    if check and result.returncode:
        detail = (result.stderr or result.stdout).strip()[-800:]
        raise OfficialHubGraphicalError(
            f"command failed ({result.returncode}): {arguments[0]}: {detail}"
        )
    return result


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


def publish_active_state(pid: int) -> None:
    ACTIVE.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
    temporary = ACTIVE.with_name(f".{ACTIVE.name}.{os.getpid()}.tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        os.write(descriptor, (json.dumps({
            "profile": "apx-official-hub-graphical-v1", "generation": GENERATION,
            "unit": OUTER_UNIT + ".service", "pid": pid,
        }, sort_keys=True, separators=(",", ":")) + "\n").encode())
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    os.replace(temporary, ACTIVE)


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


def resolve_audio_devices() -> dict[str, str]:
    controls: list[str] = []
    for node in sorted(Path("/dev/snd").glob("controlC*")):
        result = run(("udevadm", "info", "--query=property", f"--name={node}"), False)
        if result.returncode:
            continue
        properties = dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)
        if properties.get("DEVNAME") == str(node) and properties.get("ID_PATH") == AUDIO_ID_PATH:
            controls.append(str(node))
    if len(controls) != 1:
        raise OfficialHubGraphicalError("the admitted internal audio identity is absent or ambiguous")
    match = re.fullmatch(r"/dev/snd/controlC([0-9]+)", controls[0])
    if match is None:
        raise OfficialHubGraphicalError("the admitted audio control identity is malformed")
    playback = f"/dev/snd/pcmC{match.group(1)}D0p"
    capture = f"/dev/snd/pcmC{match.group(1)}D0c"
    return {
        "audio_control": controls[0],
        "audio_playback": playback,
        "audio_capture": capture,
        "audio_timer": "/dev/snd/timer",
    }


def ensure_audio_master_playback(audio: dict[str, str]) -> None:
    """Enable only the Host-owned physical playback master before device lease.

    Environments retain authority over their PipeWire volume/mute state.  This
    function only establishes the physical codec route required for that
    Environment-local logical state to reach the internal audio hardware.
    """
    match = re.fullmatch(r"/dev/snd/controlC([0-9]+)", audio["audio_control"])
    if match is None:
        raise OfficialHubGraphicalError("resolved audio control identity is malformed")

    card = match.group(1)

    try:
        alsa = ctypes.CDLL("libasound.so.2")
    except OSError as error:
        raise OfficialHubGraphicalError("Host ALSA control library is unavailable") from error

    pointer = ctypes.c_void_p
    integer = ctypes.c_int
    unsigned = ctypes.c_uint
    long_integer = ctypes.c_long
    string = ctypes.c_char_p

    alsa.snd_ctl_open.argtypes = [ctypes.POINTER(pointer), string, integer]
    alsa.snd_ctl_open.restype = integer
    alsa.snd_ctl_close.argtypes = [pointer]
    alsa.snd_ctl_close.restype = integer

    alsa.snd_ctl_elem_list_malloc.argtypes = [ctypes.POINTER(pointer)]
    alsa.snd_ctl_elem_list_malloc.restype = integer
    alsa.snd_ctl_elem_list_free.argtypes = [pointer]
    alsa.snd_ctl_elem_list_free.restype = None
    alsa.snd_ctl_elem_list.argtypes = [pointer, pointer]
    alsa.snd_ctl_elem_list.restype = integer
    alsa.snd_ctl_elem_list_get_count.argtypes = [pointer]
    alsa.snd_ctl_elem_list_get_count.restype = unsigned
    alsa.snd_ctl_elem_list_get_used.argtypes = [pointer]
    alsa.snd_ctl_elem_list_get_used.restype = unsigned
    alsa.snd_ctl_elem_list_alloc_space.argtypes = [pointer, unsigned]
    alsa.snd_ctl_elem_list_alloc_space.restype = integer
    alsa.snd_ctl_elem_list_free_space.argtypes = [pointer]
    alsa.snd_ctl_elem_list_free_space.restype = None
    alsa.snd_ctl_elem_list_get_numid.argtypes = [pointer, unsigned]
    alsa.snd_ctl_elem_list_get_numid.restype = unsigned
    alsa.snd_ctl_elem_list_get_name.argtypes = [pointer, unsigned]
    alsa.snd_ctl_elem_list_get_name.restype = string
    alsa.snd_ctl_elem_list_get_index.argtypes = [pointer, unsigned]
    alsa.snd_ctl_elem_list_get_index.restype = unsigned

    alsa.snd_ctl_elem_id_malloc.argtypes = [ctypes.POINTER(pointer)]
    alsa.snd_ctl_elem_id_malloc.restype = integer
    alsa.snd_ctl_elem_id_free.argtypes = [pointer]
    alsa.snd_ctl_elem_id_free.restype = None
    alsa.snd_ctl_elem_id_set_numid.argtypes = [pointer, unsigned]
    alsa.snd_ctl_elem_id_set_numid.restype = None

    alsa.snd_ctl_elem_info_malloc.argtypes = [ctypes.POINTER(pointer)]
    alsa.snd_ctl_elem_info_malloc.restype = integer
    alsa.snd_ctl_elem_info_free.argtypes = [pointer]
    alsa.snd_ctl_elem_info_free.restype = None
    alsa.snd_ctl_elem_info_set_id.argtypes = [pointer, pointer]
    alsa.snd_ctl_elem_info_set_id.restype = None
    alsa.snd_ctl_elem_info.argtypes = [pointer, pointer]
    alsa.snd_ctl_elem_info.restype = integer
    alsa.snd_ctl_elem_info_get_type.argtypes = [pointer]
    alsa.snd_ctl_elem_info_get_type.restype = integer
    alsa.snd_ctl_elem_info_get_count.argtypes = [pointer]
    alsa.snd_ctl_elem_info_get_count.restype = unsigned
    alsa.snd_ctl_elem_info_get_min.argtypes = [pointer]
    alsa.snd_ctl_elem_info_get_min.restype = long_integer
    alsa.snd_ctl_elem_info_get_max.argtypes = [pointer]
    alsa.snd_ctl_elem_info_get_max.restype = long_integer

    alsa.snd_ctl_elem_value_malloc.argtypes = [ctypes.POINTER(pointer)]
    alsa.snd_ctl_elem_value_malloc.restype = integer
    alsa.snd_ctl_elem_value_free.argtypes = [pointer]
    alsa.snd_ctl_elem_value_free.restype = None
    alsa.snd_ctl_elem_value_set_id.argtypes = [pointer, pointer]
    alsa.snd_ctl_elem_value_set_id.restype = None
    alsa.snd_ctl_elem_read.argtypes = [pointer, pointer]
    alsa.snd_ctl_elem_read.restype = integer
    alsa.snd_ctl_elem_write.argtypes = [pointer, pointer]
    alsa.snd_ctl_elem_write.restype = integer
    alsa.snd_ctl_elem_value_get_boolean.argtypes = [pointer, unsigned]
    alsa.snd_ctl_elem_value_get_boolean.restype = long_integer
    alsa.snd_ctl_elem_value_set_boolean.argtypes = [pointer, unsigned, long_integer]
    alsa.snd_ctl_elem_value_set_boolean.restype = None
    alsa.snd_ctl_elem_value_get_integer.argtypes = [pointer, unsigned]
    alsa.snd_ctl_elem_value_get_integer.restype = long_integer
    alsa.snd_ctl_elem_value_set_integer.argtypes = [pointer, unsigned, long_integer]
    alsa.snd_ctl_elem_value_set_integer.restype = None

    snd_ctl_elem_type_boolean = 1
    snd_ctl_elem_type_integer = 2

    def checked(label: str, result: int) -> None:
        if result < 0:
            raise OfficialHubGraphicalError(
                f"Host ALSA physical playback initialization failed at {label}: {result}"
            )

    control = pointer()
    elements = pointer()
    element_id = pointer()
    element_info = pointer()
    element_value = pointer()
    list_space = False

    try:
        checked(
            "control-open",
            alsa.snd_ctl_open(ctypes.byref(control), f"hw:{card}".encode(), 0),
        )

        checked(
            "element-list-allocation",
            alsa.snd_ctl_elem_list_malloc(ctypes.byref(elements)),
        )
        checked("element-list-count", alsa.snd_ctl_elem_list(control, elements))

        count = alsa.snd_ctl_elem_list_get_count(elements)
        if not 1 <= count <= 1024:
            raise OfficialHubGraphicalError(
                "Host ALSA physical playback control catalogue differs"
            )

        checked(
            "element-list-space",
            alsa.snd_ctl_elem_list_alloc_space(elements, count),
        )
        list_space = True
        checked("element-list-read", alsa.snd_ctl_elem_list(control, elements))

        master_numid = None
        master_volume_numid = None

        for index in range(alsa.snd_ctl_elem_list_get_used(elements)):
            raw_name = alsa.snd_ctl_elem_list_get_name(elements, index)
            name = raw_name.decode("utf-8", "replace") if raw_name else ""
            control_index = alsa.snd_ctl_elem_list_get_index(elements, index)

            if name == "Master Playback Switch" and control_index == 0:
                if master_numid is not None:
                    raise OfficialHubGraphicalError(
                        "Host ALSA Master Playback Switch is ambiguous"
                    )
                master_numid = alsa.snd_ctl_elem_list_get_numid(elements, index)

            if name == "Master Playback Volume" and control_index == 0:
                if master_volume_numid is not None:
                    raise OfficialHubGraphicalError(
                        "Host ALSA Master Playback Volume is ambiguous"
                    )
                master_volume_numid = alsa.snd_ctl_elem_list_get_numid(elements, index)

        if master_numid is None:
            raise OfficialHubGraphicalError(
                "Host ALSA Master Playback Switch is unavailable"
            )
        if master_volume_numid is None:
            raise OfficialHubGraphicalError(
                "Host ALSA Master Playback Volume is unavailable"
            )

        checked(
            "element-id-allocation",
            alsa.snd_ctl_elem_id_malloc(ctypes.byref(element_id)),
        )
        alsa.snd_ctl_elem_id_set_numid(element_id, master_numid)

        checked(
            "element-info-allocation",
            alsa.snd_ctl_elem_info_malloc(ctypes.byref(element_info)),
        )
        alsa.snd_ctl_elem_info_set_id(element_info, element_id)
        checked("element-info-read", alsa.snd_ctl_elem_info(control, element_info))

        if alsa.snd_ctl_elem_info_get_type(element_info) != snd_ctl_elem_type_boolean:
            raise OfficialHubGraphicalError(
                "Host ALSA Master Playback Switch type differs"
            )

        channels = alsa.snd_ctl_elem_info_get_count(element_info)
        if not 1 <= channels <= 8:
            raise OfficialHubGraphicalError(
                "Host ALSA Master Playback Switch channel count differs"
            )

        checked(
            "element-value-allocation",
            alsa.snd_ctl_elem_value_malloc(ctypes.byref(element_value)),
        )
        alsa.snd_ctl_elem_value_set_id(element_value, element_id)
        checked("master-read", alsa.snd_ctl_elem_read(control, element_value))

        if not all(
            alsa.snd_ctl_elem_value_get_boolean(element_value, channel)
            for channel in range(channels)
        ):
            for channel in range(channels):
                alsa.snd_ctl_elem_value_set_boolean(element_value, channel, 1)

            checked("master-write", alsa.snd_ctl_elem_write(control, element_value))
            checked("master-verify-read", alsa.snd_ctl_elem_read(control, element_value))

        if not all(
            alsa.snd_ctl_elem_value_get_boolean(element_value, channel) == 1
            for channel in range(channels)
        ):
            raise OfficialHubGraphicalError(
                "Host ALSA Master Playback Switch did not enable"
            )

        # Keep the physical codec path neutral (0 dB / maximum hardware level);
        # Environment-local PipeWire remains the sole logical volume authority.
        alsa.snd_ctl_elem_id_set_numid(element_id, master_volume_numid)
        alsa.snd_ctl_elem_info_set_id(element_info, element_id)
        checked(
            "master-volume-info-read",
            alsa.snd_ctl_elem_info(control, element_info),
        )

        if alsa.snd_ctl_elem_info_get_type(element_info) != snd_ctl_elem_type_integer:
            raise OfficialHubGraphicalError(
                "Host ALSA Master Playback Volume type differs"
            )

        volume_channels = alsa.snd_ctl_elem_info_get_count(element_info)
        if not 1 <= volume_channels <= 8:
            raise OfficialHubGraphicalError(
                "Host ALSA Master Playback Volume channel count differs"
            )

        volume_min = alsa.snd_ctl_elem_info_get_min(element_info)
        volume_max = alsa.snd_ctl_elem_info_get_max(element_info)

        if volume_min < 0 or volume_max < volume_min or volume_max > 255:
            raise OfficialHubGraphicalError(
                "Host ALSA Master Playback Volume range differs"
            )

        alsa.snd_ctl_elem_value_set_id(element_value, element_id)
        checked(
            "master-volume-read",
            alsa.snd_ctl_elem_read(control, element_value),
        )

        if not all(
            alsa.snd_ctl_elem_value_get_integer(element_value, channel)
            == volume_max
            for channel in range(volume_channels)
        ):
            for channel in range(volume_channels):
                alsa.snd_ctl_elem_value_set_integer(
                    element_value,
                    channel,
                    volume_max,
                )

            checked(
                "master-volume-write",
                alsa.snd_ctl_elem_write(control, element_value),
            )
            checked(
                "master-volume-verify-read",
                alsa.snd_ctl_elem_read(control, element_value),
            )

        if not all(
            alsa.snd_ctl_elem_value_get_integer(element_value, channel)
            == volume_max
            for channel in range(volume_channels)
        ):
            raise OfficialHubGraphicalError(
                "Host ALSA Master Playback Volume did not reach neutral maximum"
            )

    finally:
        if element_value:
            alsa.snd_ctl_elem_value_free(element_value)
        if element_info:
            alsa.snd_ctl_elem_info_free(element_info)
        if element_id:
            alsa.snd_ctl_elem_id_free(element_id)
        if elements:
            if list_space:
                alsa.snd_ctl_elem_list_free_space(elements)
            alsa.snd_ctl_elem_list_free(elements)
        if control:
            alsa.snd_ctl_close(control)


def effective_gpu_policy() -> str:
    try:
        value = json.loads(HARDWARE_PROFILE.read_text())
    except (OSError, json.JSONDecodeError):
        return "hybrid"
    if type(value) is not dict or value.get("schema") != 1:
        raise OfficialHubGraphicalError("hardware profile state is malformed")
    requested = "hybrid" if value.get("requested_gpu") == "amd" else value.get("requested_gpu")
    previous_value = value.get("previous_gpu", "hybrid")
    previous = "hybrid" if previous_value == "amd" else previous_value
    if requested not in {"hybrid", "nvidia"} or previous not in {"hybrid", "nvidia"}:
        raise OfficialHubGraphicalError("hardware GPU policy differs")
    same_boot = value.get("set_boot_id") == BOOT_ID.read_text().strip()
    return previous if value.get("reboot_required") is True and same_boot else requested


def resolve_drm_device(pci: str, kind: str, vendor: str, device: str) -> str:
    if kind not in {"card", "render"}:
        raise OfficialHubGraphicalError("DRM node kind differs")
    link = Path(f"/dev/dri/by-path/pci-{pci}-{kind}")
    try:
        target = link.resolve(strict=True)
        metadata = target.stat()
        observed_vendor = Path(f"/sys/bus/pci/devices/{pci}/vendor").read_text().strip()
        observed_device = Path(f"/sys/bus/pci/devices/{pci}/device").read_text().strip()
    except OSError as error:
        raise OfficialHubGraphicalError(f"{pci} {kind} identity is unavailable") from error
    pattern = r"/dev/dri/card[0-9]+" if kind == "card" else r"/dev/dri/renderD[0-9]+"
    if observed_vendor != vendor or observed_device != device or not stat.S_ISCHR(metadata.st_mode) \
            or os.major(metadata.st_rdev) != 226 or not re.fullmatch(pattern, str(target)):
        raise OfficialHubGraphicalError(f"resolved {pci} {kind} identity differs")
    return str(target)


def ensure_nvidia_control_device(
    node: Path = Path("/dev/nvidiactl"),
    proc_devices: Path = Path("/proc/devices"),
) -> None:
    """Repair the exact control node when nvidia-modprobe omits it.

    NVIDIA 610 can return success after creating the GPU and modeset nodes
    while leaving the registered nvidiactl character device unpublished.  Do
    not infer a dynamic device identity: require the kernel's exact fixed
    registration before creating only major 195, minor 255.
    """
    try:
        node.lstat()
        return
    except FileNotFoundError:
        pass
    registrations = []
    for line in proc_devices.read_text().splitlines():
        fields = line.split()
        if len(fields) == 2 and fields[1] == "nvidiactl":
            registrations.append(fields[0])
    if registrations != ["195"]:
        raise OfficialHubGraphicalError("the NVIDIA control device registration differs")
    try:
        os.mknod(node, stat.S_IFCHR | 0o666, os.makedev(195, 255))
    except FileExistsError:
        pass
    os.chmod(node, 0o666)


def resolve_nvidia_auxiliary_devices() -> dict[str, str]:
    """Create and admit the proprietary NVIDIA userspace control nodes."""
    helper = Path("/usr/bin/nvidia-modprobe")
    metadata = helper.stat()
    if helper.is_symlink() or not helper.is_file() or metadata.st_uid != 0 \
            or metadata.st_gid != 0 or metadata.st_mode & 0o022:
        raise OfficialHubGraphicalError("the NVIDIA device helper is untrusted")
    run((str(helper), "-c", "0"))
    run((str(helper), "-m"))
    ensure_nvidia_control_device()
    expected = {
        "nvidia_device": ("/dev/nvidia0", 195, 0),
        "nvidia_control": ("/dev/nvidiactl", 195, 255),
        "nvidia_modeset": ("/dev/nvidia-modeset", 195, 254),
    }
    resolved: dict[str, str] = {}
    for label, (name, major, minor) in expected.items():
        node = Path(name)
        node_metadata = node.stat()
        if not stat.S_ISCHR(node_metadata.st_mode) or (
                os.major(node_metadata.st_rdev), os.minor(node_metadata.st_rdev)
        ) != (major, minor):
            raise OfficialHubGraphicalError("resolved NVIDIA auxiliary device differs")
        resolved[label] = name
    return resolved


def resolve_graphics() -> dict[str, str]:
    policy = effective_gpu_policy()
    if policy == "nvidia":
        display_pci, vendor, device = NVIDIA_PCI, "0x10de", "0x2560"
    else:
        display_pci, vendor, device = AMD_PCI, "0x1002", "0x1638"
    graphics = {
        "policy": policy,
        "display_card": resolve_drm_device(display_pci, "card", vendor, device),
        "display_render": resolve_drm_device(display_pci, "render", vendor, device),
    }
    if policy == "hybrid":
        graphics["offload_card"] = resolve_drm_device(NVIDIA_PCI, "card", "0x10de", "0x2560")
        graphics["offload_render"] = resolve_drm_device(NVIDIA_PCI, "render", "0x10de", "0x2560")
    graphics.update(resolve_nvidia_auxiliary_devices())
    return graphics


def validate_devices(inputs: dict[str, str], audio: dict[str, str], graphics: dict[str, str]) -> None:
    expected = {Path("/dev/tty2"): (4, 2)}
    for path, device in expected.items():
        metadata = path.stat()
        if not stat.S_ISCHR(metadata.st_mode) or (os.major(metadata.st_rdev), os.minor(metadata.st_rdev)) != device:
            raise OfficialHubGraphicalError(f"required graphical device differs: {path}")
    for node in inputs.values():
        metadata = os.stat(node)
        if not stat.S_ISCHR(metadata.st_mode) or os.major(metadata.st_rdev) != 13:
            raise OfficialHubGraphicalError("resolved input node is not an evdev character device")
    if set(audio) != {"audio_control", "audio_playback", "audio_capture", "audio_timer"}:
        raise OfficialHubGraphicalError("resolved audio device catalogue differs")
    if not re.fullmatch(r"/dev/snd/controlC[0-9]+", audio["audio_control"]):
        raise OfficialHubGraphicalError("resolved audio control node differs")
    if not re.fullmatch(r"/dev/snd/pcmC[0-9]+D0p", audio["audio_playback"]):
        raise OfficialHubGraphicalError("resolved audio playback node differs")
    if not re.fullmatch(r"/dev/snd/pcmC[0-9]+D0c", audio["audio_capture"]):
        raise OfficialHubGraphicalError("resolved audio capture node differs")
    if audio["audio_timer"] != "/dev/snd/timer":
        raise OfficialHubGraphicalError("resolved audio timer node differs")
    for node in audio.values():
        metadata = os.stat(node)
        if not stat.S_ISCHR(metadata.st_mode) or os.major(metadata.st_rdev) != 116:
            raise OfficialHubGraphicalError("resolved audio node is not an ALSA character device")
    if graphics.get("policy") not in {"hybrid", "nvidia"} \
            or not re.fullmatch(r"/dev/dri/card[0-9]+", graphics.get("display_card", "")) \
            or not re.fullmatch(r"/dev/dri/renderD[0-9]+", graphics.get("display_render", "")):
        raise OfficialHubGraphicalError("resolved display GPU catalogue differs")
    if graphics["policy"] == "hybrid" and (
            not re.fullmatch(r"/dev/dri/card[0-9]+", graphics.get("offload_card", ""))
            or not re.fullmatch(r"/dev/dri/renderD[0-9]+", graphics.get("offload_render", ""))):
        raise OfficialHubGraphicalError("resolved NVIDIA display/offload nodes differ")
    if tuple(graphics.get(label) for label in (
            "nvidia_device", "nvidia_control", "nvidia_modeset",
    )) != ("/dev/nvidia0", "/dev/nvidiactl", "/dev/nvidia-modeset"):
        raise OfficialHubGraphicalError("resolved NVIDIA auxiliary catalogue differs")


def stop_text_hub_if_needed() -> None:
    if machine_running():
        result = run(("/usr/bin/apx", "environment", "stop", "hub"), False)
        if result.returncode:
            raise OfficialHubGraphicalError("textual Hub could not be stopped safely")
    if machine_running():
        raise OfficialHubGraphicalError("Hub machine survived textual stop")


def prepare_device_leases(nodes: tuple[str, ...]) -> dict[str, str]:
    if DEVICE_LEASE_DIR.exists():
        cleanup_device_leases()
    DEVICE_LEASE_DIR.mkdir(mode=0o700, parents=False)
    leases: list[dict[str, object]] = []
    bindings: dict[str, str] = {}
    for index, node in enumerate(nodes):
        metadata = os.stat(node)
        proxy = DEVICE_LEASE_DIR / f"device-{index}"
        os.mknod(proxy, stat.S_IFCHR, metadata.st_rdev)
        leases.append({
            "node": node, "proxy": str(proxy),
            "major": os.major(metadata.st_rdev), "minor": os.minor(metadata.st_rdev),
        })
        bindings[node] = str(proxy)
    temporary = DEVICE_LEASE_STATE.with_name(f".{DEVICE_LEASE_STATE.name}.{os.getpid()}.tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        payload = {"schema": 1, "leases": leases}
        os.write(descriptor, (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode())
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    os.replace(temporary, DEVICE_LEASE_STATE)
    return bindings


def _device_lease_state() -> tuple[dict[str, object], ...]:
    metadata = DEVICE_LEASE_STATE.lstat()
    data = DEVICE_LEASE_STATE.read_bytes()
    if DEVICE_LEASE_STATE.is_symlink() or not DEVICE_LEASE_STATE.is_file() \
            or metadata.st_uid != 0 or metadata.st_gid != 0 or len(data) > 4096:
        raise OfficialHubGraphicalError("graphical device lease state is untrusted")
    value = json.loads(data)
    if type(value) is not dict:
        raise OfficialHubGraphicalError("graphical device lease state is not an object")
    leases = value.get("leases")
    if value.get("schema") != 1 or type(leases) is not list or not 1 <= len(leases) <= 16:
        raise OfficialHubGraphicalError("graphical device lease state is malformed")
    for index, lease in enumerate(leases):
        if type(lease) is not dict or set(lease) != {"node", "proxy", "major", "minor"} \
                or not re.fullmatch(
                    r"/dev/(?:dri/(?:card|renderD)[0-9]+|input/event[0-9]+|snd/(?:controlC[0-9]+|pcmC[0-9]+D0[pc]|timer)|nvidia(?:[0-9]+|ctl|-modeset)|tty2)",
                    str(lease.get("node")),
                ) or lease.get("proxy") != str(DEVICE_LEASE_DIR / f"device-{index}") \
                or type(lease.get("major")) is not int or type(lease.get("minor")) is not int:
            raise OfficialHubGraphicalError("graphical device lease record differs")
    return tuple(leases)


def activate_device_leases(uid_base: int) -> None:
    for lease in _device_lease_state():
        proxy = Path(str(lease["proxy"]))
        metadata = proxy.stat()
        if not stat.S_ISCHR(metadata.st_mode) or (
            os.major(metadata.st_rdev), os.minor(metadata.st_rdev)
        ) != (lease["major"], lease["minor"]):
            raise OfficialHubGraphicalError("graphical device proxy identity differs")
        # Bind-mounted device nodes are not idmapped by nspawn. Give the proxy
        # directly to the translated Environment user, not translated root.
        os.chown(proxy, uid_base + 1000, uid_base + 1000)
        os.chmod(proxy, 0o660)
    if not SEATD_SOCKET.is_socket():
        raise OfficialHubGraphicalError("Host seatd broker socket disappeared")
    os.chown(SEATD_SOCKET, uid_base + 1000, uid_base + 1000)
    os.chmod(SEATD_SOCKET, 0o660)


LEASED_SERVICE_SOCKETS = (
    HOST_SERVICES_SOCKET, HOST_SERVICES_V2_SOCKET, HOST_SERVICES_V3_SOCKET,
    AUDIO_STATE_SOCKET, UPDATE_SOCKET, POWER_SOCKET, HOST_CONSOLE_SOCKET,
    ENVIRONMENT_SWITCH_SOCKET, MODEL_STORE_SOCKET,
)


def activate_service_sockets(uid_base: int) -> None:
    for endpoint in LEASED_SERVICE_SOCKETS:
        metadata = endpoint.stat()
        if not stat.S_ISSOCK(metadata.st_mode) or metadata.st_uid not in {0, uid_base + 1000} \
                or metadata.st_gid not in {0, uid_base + 1000}:
            raise OfficialHubGraphicalError(f"Host service socket identity differs: {endpoint}")
        os.chown(endpoint, uid_base + 1000, uid_base + 1000)
        os.chmod(endpoint, 0o660)


def deactivate_service_sockets() -> None:
    for endpoint in LEASED_SERVICE_SOCKETS:
        if not endpoint.exists():
            continue
        metadata = endpoint.stat()
        if not stat.S_ISSOCK(metadata.st_mode):
            raise OfficialHubGraphicalError(f"Host service endpoint is no longer a socket: {endpoint}")
        os.chown(endpoint, 0, 0)
        os.chmod(endpoint, 0o600)


def cleanup_device_leases() -> None:
    if not DEVICE_LEASE_STATE.exists():
        if DEVICE_LEASE_DIR.exists():
            DEVICE_LEASE_DIR.rmdir()
        return
    leases = _device_lease_state()
    DEVICE_LEASE_STATE.unlink()
    for lease in leases:
        Path(str(lease["proxy"])).unlink(missing_ok=True)
    DEVICE_LEASE_DIR.rmdir()


def unlink_if_present(path: Path) -> None:
    """Avoid unlinking an absent path below a read-only sandbox parent."""
    try:
        path.lstat()
    except FileNotFoundError:
        return
    path.unlink()


def _recover() -> None:
    run(("systemctl", "-M", MACHINE, "stop", INNER_UNIT + ".service"), False)
    if machine_running():
        run(("machinectl", "shell", f"root@{MACHINE}", "/usr/bin/rm", "-f", LOCAL_ADMIN_PROOF), False)
    run(("systemctl", "stop", OUTER_UNIT + ".service"), False)
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline and (unit_active(OUTER_UNIT) or machine_running()):
        time.sleep(0.1)
    run(("systemctl", "stop", SEATD_UNIT + ".service"), False)
    run(("/usr/lib/apx/apx-audio-state-v1.py", "--clear"), False)
    deactivate_service_sockets()
    unlink_if_present(SEATD_SOCKET)
    cleanup_device_leases()
    run(("chvt", "1"), False)
    run((str(NETWORK), "remove", "--environment", "hub"), False)
    if REGISTRATION.is_file():
        write_registration_state("stopped")
    ACTIVE.unlink(missing_ok=True)
    WATCHDOG_STATE.unlink(missing_ok=True)
    run(("systemctl", "stop", EXPIRY_UNIT + ".timer"), False)
    run(("systemctl", "stop", WATCHDOG_UNIT + ".timer"), False)
    if unit_active(OUTER_UNIT) or machine_running():
        raise OfficialHubGraphicalError("official Hub graphical recovery left runtime residue")
    if Path("/sys/class/tty/tty0/active").read_text().strip() != "tty1":
        raise OfficialHubGraphicalError("official Hub graphical recovery did not restore tty1")


def recover() -> None:
    """Serialize recovery requested by the launcher, watchdog, and Host power runner."""
    RECOVERY_LOCK.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
    descriptor = os.open(RECOVERY_LOCK, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        _recover()
    finally:
        os.close(descriptor)


def arm_test_expiry(seconds: int) -> None:
    run(("systemctl", "stop", EXPIRY_UNIT + ".timer"), False)
    run((
        "systemd-run", f"--unit={EXPIRY_UNIT}", f"--on-active={seconds}s",
        "--timer-property=AccuracySec=1s", "--property=Type=oneshot",
        "--property=NoNewPrivileges=yes", "--property=ProtectSystem=strict",
        "--property=ProtectHome=yes", "--property=ReadWritePaths=/run/apx",
        "--property=ReadWritePaths=/run/seatd.sock",
        "--property=ReadWritePaths=/var/lib/apx/environments/hub",
        str(INSTALLED), "--recover",
    ))
    if run(("systemctl", "is-active", "--quiet", EXPIRY_UNIT + ".timer"), False).returncode:
        raise OfficialHubGraphicalError("independent official Hub test expiry did not arm")


def arm_health_watchdog() -> None:
    run(("systemctl", "stop", WATCHDOG_UNIT + ".timer"), False)
    run(("systemctl", "reset-failed", WATCHDOG_UNIT + ".service"), False)
    WATCHDOG_STATE.unlink(missing_ok=True)
    run((
        "systemd-run", f"--unit={WATCHDOG_UNIT}", "--on-active=60s",
        "--on-unit-active=30s", "--timer-property=AccuracySec=2s",
        "--property=Type=oneshot", "--property=TimeoutStartSec=30s",
        "--property=NoNewPrivileges=yes", "--property=ProtectSystem=strict",
        "--property=ProtectHome=yes", "--property=ReadWritePaths=/run/apx",
        "--property=ReadWritePaths=/run/seatd.sock",
        "--property=ReadWritePaths=/var/lib/apx/environments/hub",
        str(INSTALLED), "--watchdog",
    ))
    if run(("systemctl", "is-active", "--quiet", WATCHDOG_UNIT + ".timer"), False).returncode:
        raise OfficialHubGraphicalError("independent official Hub health watchdog did not arm")


def start_host_seatd(inputs: dict[str, str], graphics: dict[str, str]) -> None:
    run(("systemctl", "stop", SEATD_UNIT + ".service"), False)
    unlink_if_present(SEATD_SOCKET)
    nodes = (*inputs.values(), graphics["display_card"],
             *((graphics["offload_card"],) if "offload_card" in graphics else ()),
             "/dev/tty2")
    command = (
        "systemd-run", f"--unit={SEATD_UNIT}", "--collect", "--property=Type=simple",
        "--property=KillMode=mixed", "--property=TimeoutStopSec=3s",
        "--property=DevicePolicy=closed",
        *(f"--property=DeviceAllow={node} rw" for node in nodes),
        "--setenv=SEATD_VTBOUND=0", "--", "/usr/bin/seatd", "-u", "root", "-l", "info",
    )
    run(command)
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if SEATD_SOCKET.is_socket() and unit_active(SEATD_UNIT):
            return
        time.sleep(0.05)
    raise OfficialHubGraphicalError("Host seatd broker did not become ready")


def start_outer(
    inputs: dict[str, str], audio: dict[str, str], graphics: dict[str, str],
    bindings: dict[str, str], authenticated_handoff: bool = False,
) -> None:
    input_nodes = tuple(inputs[label] for label in (
        "keyboard_i8042", "keyboard_ite", "elan_mouse", "elan_touchpad"
    ))
    audio_nodes = tuple(audio[label] for label in (
        "audio_control", "audio_playback", "audio_capture", "audio_timer"
    ))
    if not HOST_SERVICES_SOCKET.is_socket() or not HOST_SERVICES_CLIENT.is_file() \
            or not HOST_SERVICES_CONTRACT.is_file() or not HOST_SERVICES_V2_SOCKET.is_socket() \
            or not HOST_SERVICES_V2_CLIENT.is_file() or not HOST_SERVICES_V2_CONTRACT.is_file() \
            or not HOST_SERVICES_V3_SOCKET.is_socket() or not HOST_SERVICES_V3_CLIENT.is_file() \
            or not HOST_SERVICES_V3_CONTRACT.is_file() or not HOST_SERVICES_UI_V3.is_file() \
            or not DESKTOP_MENU_V2.is_file() or not AUDIO_STATE_SOCKET.is_socket() \
            or not AUDIO_STATE_CLIENT.is_file() or not AUDIO_STATE_CONTRACT.is_file() \
            or UPDATE_ENABLED and (not UPDATE_SOCKET.is_socket() or not UPDATE_CLIENT.is_file()) \
            or POWER_ENABLED and (not POWER_SOCKET.is_socket() or not POWER_CLIENT.is_file()
                or not POWER_CONTRACT.is_file() or not BRIGHTNESS_KEYS.is_file()) \
            or not MODEL_STORE_SOCKET.is_socket() or not MODEL_STORE_CLIENT.is_file() \
            or not ENVIRONMENT_SWITCH_SOCKET.is_socket() or not ENVIRONMENT_SWITCH_CLIENT.is_file() \
            or not ENVIRONMENT_SWITCH_CONTRACT.is_file() or not ENVIRONMENT_FEATURES.is_file() \
            or HOST_CONSOLE_ENABLED and (not HOST_CONSOLE_SOCKET.is_socket()
                or not HOST_CONSOLE_CLIENT.is_file() or not HOST_CONSOLE_CONTRACT.is_file()):
        raise OfficialHubGraphicalError("read-only Host-services bundle is unavailable")
    if authenticated_handoff:
        metadata = HANDOFF_PROOF.lstat()
        data = HANDOFF_PROOF.read_bytes()
        if HANDOFF_PROOF.is_symlink() or not HANDOFF_PROOF.is_file() \
                or metadata.st_uid != 0 or metadata.st_gid != 0 \
                or stat.S_IMODE(metadata.st_mode) != 0o444 or data != b"apx-authenticated-handoff-v1\n":
            raise OfficialHubGraphicalError("authenticated handoff proof differs")
    run((str(NETWORK), "apply", "--environment", "hub"))
    command = (
        "systemd-run", f"--unit={OUTER_UNIT}", "--collect", "--property=Delegate=yes",
        "--property=KillMode=mixed", "--property=TimeoutStopSec=5s",
        f"--property=CPUQuota={HUB_CPU_QUOTA}", f"--property=CPUWeight={HUB_CPU_WEIGHT}",
        f"--property=IOWeight={HUB_IO_WEIGHT}", f"--property=MemoryHigh={HUB_MEMORY_HIGH}",
        f"--property=MemoryMax={HUB_MEMORY_MAX}", f"--property=TasksMax={HUB_TASKS_MAX}",
        "--property=DevicePolicy=closed",
        *(f"--property=DeviceAllow={node} rw" for node in bindings),
        "--", "systemd-nspawn", "--quiet",
        "--keep-unit", "--boot", f"--directory={ROOT}", f"--machine={MACHINE}",
        f"--hostname={MACHINE}", "--register=yes", "--settings=no", "--private-network",
        "--network-veth", "--timezone=bind", "--link-journal=no", "--console=pipe",
        "--private-users=pick",
        "--private-users-ownership=chown", f"--bind={HOME}:/home:idmap",
        f"--bind-ro={SESSION}:/run/apx/official-hub-session",
        f"--bind={HOST_SERVICES_SOCKET}:{HOST_SERVICES_SOCKET}",
        f"--bind-ro={HOST_SERVICES_CLIENT}:/run/apx/host-services-client-v1.py",
        f"--bind-ro={HOST_SERVICES_CONTRACT}:/usr/lib/apx/apx_host_services_contract.py",
        f"--bind={HOST_SERVICES_V2_SOCKET}:{HOST_SERVICES_V2_SOCKET}",
        f"--bind-ro={HOST_SERVICES_V2_CLIENT}:/run/apx/host-services-client-v2.py",
        f"--bind-ro={HOST_SERVICES_V2_CONTRACT}:/usr/lib/apx/apx_host_services_v2_contract.py",
        f"--bind={HOST_SERVICES_V3_SOCKET}:/run/apx/host-services-v3.sock",
        f"--bind-ro={HOST_SERVICES_V3_CLIENT}:/run/apx/host-services-client-v3.py",
        f"--bind-ro={HOST_SERVICES_V3_CONTRACT}:/usr/lib/apx/apx_host_services_v3_contract.py",
        f"--bind-ro={HOST_SERVICES_UI_V3}:/run/apx/host-services-ui-v3.py",
        f"--bind-ro={DESKTOP_MENU_V2}:/run/apx/desktop-menu-v2.py",
        f"--bind={AUDIO_STATE_SOCKET}:/run/apx/audio-state-v1.sock",
        f"--bind-ro={AUDIO_STATE_CLIENT}:/run/apx/audio-state-client-v1.py",
        f"--bind-ro={AUDIO_STATE_CONTRACT}:/usr/lib/apx/apx_audio_state_contract.py",
        *((f"--bind={UPDATE_SOCKET}:/run/apx/coordinated-update-v1.sock",
           f"--bind-ro={UPDATE_CLIENT}:/run/apx/coordinated-update-client-v1.py")
          if UPDATE_ENABLED else ()),
        *((f"--bind={POWER_SOCKET}:/run/apx/system-power-v1.sock",
           f"--bind-ro={POWER_CLIENT}:/run/apx/system-power-client-v1.py",
           f"--bind-ro={POWER_CONTRACT}:/usr/lib/apx/apx_system_power_contract.py",
           f"--bind-ro={BRIGHTNESS_KEYS}:/usr/lib/apx/apx-legion-brightness-keys-v1.py")
          if POWER_ENABLED else ()),
        f"--bind={MODEL_STORE_SOCKET}:/run/apx/model-store-control-v1.sock",
        f"--bind-ro={MODEL_STORE_CLIENT}:/run/apx/model-store-client-v1.py",
        f"--bind={ENVIRONMENT_SWITCH_SOCKET}:/run/apx/environment-switch-v1.sock",
        f"--bind-ro={ENVIRONMENT_SWITCH_CLIENT}:/run/apx/environment-switch-client-v1.py",
        f"--bind-ro={ENVIRONMENT_SWITCH_CONTRACT}:/usr/lib/apx/apx_environment_switch_contract.py",
        f"--bind-ro={ENVIRONMENT_FEATURES}:/usr/lib/apx/apx_environment_features.py",
        *((f"--bind-ro={HANDOFF_PROOF}:/run/apx/authenticated-handoff-v1",)
          if authenticated_handoff else ()),
        *((f"--bind={HOST_CONSOLE_SOCKET}:/run/apx/host-console-v1.sock",
           f"--bind-ro={HOST_CONSOLE_CLIENT}:/run/apx/host-console-client-v1.py",
           f"--bind-ro={HOST_CONSOLE_CONTRACT}:/usr/lib/apx/apx_host_console_contract.py")
          if HOST_CONSOLE_ENABLED else ()),
        f"--bind={SEATD_SOCKET}:/run/seatd.sock",
        "--bind-ro=/run/udev/data:/run/udev/data",
        *(f"--bind={proxy}:{node}" for node, proxy in bindings.items()),
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


def resolve_user_namespace() -> int:
    result = run(("machinectl", "show", MACHINE, "-p", "Leader", "--value"), False)
    if result.returncode or not result.stdout.strip().isdecimal():
        raise OfficialHubGraphicalError("official Hub user namespace leader is unavailable")
    leader = int(result.stdout.strip())
    starts: list[int] = []
    for label in ("uid_map", "gid_map"):
        fields = Path(f"/proc/{leader}/{label}").read_text().split()
        if len(fields) != 3 or not all(field.isdecimal() for field in fields):
            raise OfficialHubGraphicalError("official Hub user namespace map is malformed")
        container_start, host_start, length = (int(field) for field in fields)
        if container_start != 0 or host_start < USER_NAMESPACE_LENGTH \
                or length != USER_NAMESPACE_LENGTH:
            raise OfficialHubGraphicalError("official Hub user namespace map differs")
        starts.append(host_start)
    if starts[0] != starts[1]:
        raise OfficialHubGraphicalError("official Hub UID/GID namespace ranges differ")
    return starts[0]


def start_inner(inputs: dict[str, str], audio: dict[str, str], graphics: dict[str, str]) -> None:
    arguments = [
        "systemd-run", "-M", MACHINE, f"--unit={INNER_UNIT}", "--collect",
        "--property=Type=simple", "--property=KillMode=mixed",
        "--property=TimeoutStopSec=3s",
    ]
    arguments.extend(f"--setenv=APX_{label.upper()}_DEVICE={node}" for label, node in inputs.items())
    arguments.extend(f"--setenv=APX_{label.upper()}_DEVICE={node}" for label, node in audio.items())
    arguments.extend((f"--setenv=APX_GPU_POLICY={graphics['policy']}",
                      f"--setenv=APX_DISPLAY_CARD={graphics['display_card']}",
                      f"--setenv=APX_DISPLAY_RENDER={graphics['display_render']}"))
    if "offload_render" in graphics:
        arguments.append(f"--setenv=APX_NVIDIA_CARD_DEVICE={graphics['offload_card']}")
        arguments.append(f"--setenv=APX_NVIDIA_RENDER_DEVICE={graphics['offload_render']}")
    arguments.extend(("--", "/run/apx/official-hub-session"))
    run(tuple(arguments))


def process_pids(process_name: bytes, proc: Path = Path("/proc")) -> list[int]:
    unit_path = f"/system.slice/{OUTER_UNIT}.service"
    found: list[int] = []
    for entry in proc.iterdir():
        if not entry.name.isdecimal():
            continue
        try:
            cgroups = (entry / "cgroup").read_text().splitlines()
            in_official_unit = any(
                (path := line.split(":", 2)[-1]) == unit_path or path.startswith(unit_path + "/")
                for line in cgroups
            )
            if (entry / "comm").read_bytes().strip() == process_name \
                    and (entry / "root/etc/apx/official-hub-base-v1").is_file() \
                    and in_official_unit:
                found.append(int(entry.name))
        except OSError:
            pass
    return found


def compositor_state() -> tuple[int, str, str, tuple[str, ...]]:
    pids = process_pids(b"Hyprland")
    if len(pids) != 1:
        return 0, "", "", ()
    pid = pids[0]
    runtime = Path(f"/proc/{pid}/root{SESSION_RUNTIME}/hypr")
    sockets = list(runtime.glob("*/.socket.sock"))
    if len(sockets) != 1 or not sockets[0].is_socket():
        return pid, "", "", ()
    signature = sockets[0].parent.name
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,200}", signature):
        return pid, "", "", ()
    prefix = (
        "nsenter", "--target", str(pid), "--mount", "--pid", "--", "env",
        f"XDG_RUNTIME_DIR={SESSION_RUNTIME}", f"HYPRLAND_INSTANCE_SIGNATURE={signature}", "hyprctl", "-j",
    )
    monitors_result = run(prefix + ("monitors",), False)
    devices_result = run(prefix + ("devices",), False)
    try:
        monitors = json.loads(monitors_result.stdout)
        devices = json.loads(devices_result.stdout)
    except json.JSONDecodeError:
        return pid, signature, "", ()
    internal = tuple(
        str(item.get("name")) for item in monitors
        if type(monitors) is list and type(item) is dict
        and re.fullmatch(r"eDP-[0-9]+", str(item.get("name", "")))
        and item.get("disabled") is False
    )
    monitor = internal[0] if len(internal) == 1 else ""
    keyboard_names = tuple(sorted(
        str(item.get("name")) for item in devices.get("keyboards", ())
        if type(item) is dict and type(item.get("name")) is str
    )) if type(devices) is dict else ()
    return pid, signature, monitor, keyboard_names


def hyprctl(pid: int, signature: str, *arguments: str) -> subprocess.CompletedProcess[str]:
    return run((
        "nsenter", "--target", str(pid), "--mount", "--pid", "--", "env",
        f"XDG_RUNTIME_DIR={SESSION_RUNTIME}", f"HYPRLAND_INSTANCE_SIGNATURE={signature}",
        "hyprctl", *arguments,
    ), False)


def verify_audio_playback(pid: int) -> str:
    container_snd = Path(f"/proc/{pid}/root/dev/snd")
    if len(tuple(container_snd.glob("pcm*C*c"))) != 1:
        raise OfficialHubGraphicalError("the exact audio capture lease is unavailable inside the Hub")
    result = run((
        "nsenter", "--target", str(pid), "--mount", "--pid", "--", "env",
        f"XDG_RUNTIME_DIR={SESSION_RUNTIME}", "wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@",
    ), False)
    if result.returncode or not result.stdout.strip().startswith("Volume:"):
        raise OfficialHubGraphicalError("Environment-local playback sink is unavailable")
    capture = run((
        "nsenter", "--target", str(pid), "--mount", "--pid", "--", "env",
        f"XDG_RUNTIME_DIR={SESSION_RUNTIME}", "wpctl", "get-volume", "@DEFAULT_AUDIO_SOURCE@",
    ), False)
    if capture.returncode or not capture.stdout.strip().startswith("Volume:"):
        status = run((
            "nsenter", "--target", str(pid), "--mount", "--pid", "--", "env",
            f"XDG_RUNTIME_DIR={SESSION_RUNTIME}", "wpctl", "status",
        ), False)
        alsa = run(("nsenter", "--target", str(pid), "--mount", "--pid", "--", "aplay", "-l"), False)
        access = run(("nsenter", "--target", str(pid), "--mount", "--pid", "--", "setpriv",
                      "--reuid=1000", "--regid=1000", "--clear-groups", "--", "bash", "-c",
                      "exec 3<>/dev/snd/controlC1 && exec 4<>/dev/snd/pcmC1D0c && echo audio-open-ok"), False)
        detail = " ".join((access.stdout + access.stderr + " " + alsa.stdout + alsa.stderr + " " + status.stdout).split())[-1000:]
        raise OfficialHubGraphicalError(f"Environment-local microphone source is unavailable: {detail}")
    return result.stdout.strip()


def verify_desktop_shell() -> str:
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if len(process_pids(b"quickshell")) == 1:
            return "quickshell"
        # On a normal boot the owner must authenticate before Quickshell is
        # started.  A live hyprlock is therefore a healthy login surface, not
        # a failed desktop shell.  The watchdog continues to monitor Hyprland
        # while authentication is pending.
        if len(process_pids(b"hyprlock")) == 1:
            return "login-lock"
        time.sleep(0.1)
    raise OfficialHubGraphicalError("neither the login surface nor Quickshell remained active")


def verify_update_and_audio_services() -> None:
    audio_value: dict[str, object] | None = None
    for command, required in (
        (("/run/apx/audio-state-client-v1.py", "get"), ("profile", "microphone_active", "output_volume", "input_volume")),
        (("/run/apx/coordinated-update-client-v1.py", "preview"), ("plan_digest", "targets", "excluded_environments", "classification")),
        (("/run/apx/system-power-client-v1.py", "capabilities"), ("actions", "confirmation", "ttl_seconds", "arbitrary_commands")),
    ):
        result = run(("systemd-run", "-M", MACHINE, "--quiet", "--pipe", "--wait", "--collect",
                      "--uid=apx", "--", *command), False)
        try: value = json.loads(result.stdout)
        except json.JSONDecodeError as error: raise OfficialHubGraphicalError("new Host service returned malformed state") from error
        if result.returncode or not all(field in value for field in required):
            raise OfficialHubGraphicalError("new Host service physical proof failed")
        if command[0].endswith("audio-state-client-v1.py"): audio_value = value
    deadline = time.monotonic() + 5
    expected = f"Volume: {int(audio_value['output_volume']) / 100:.2f}" if audio_value else ""
    while time.monotonic() < deadline:
        observed = run(("systemd-run", "-M", MACHINE, "--quiet", "--pipe", "--wait", "--collect",
                        "--uid=apx", f"--setenv=XDG_RUNTIME_DIR={SESSION_RUNTIME}", "--",
                        "/usr/bin/wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"), False)
        if observed.returncode == 0 and observed.stdout.strip().startswith(expected): return
        time.sleep(0.25)
    raise OfficialHubGraphicalError("stored audio volume was not restored in the active Environment")


def host_services_call(mode: str) -> dict[str, object]:
    if mode not in {"json", "bluetooth-toggle"}:
        raise OfficialHubGraphicalError("Host-services verification mode is unsupported")
    result = run((
        "systemd-run", "-M", MACHINE, "--quiet", "--pipe", "--wait", "--collect",
        "--uid=apx", "--", "/run/apx/host-services-client-v1.py", mode,
    ), False)
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise OfficialHubGraphicalError(
            "Host-services client returned malformed state: "
            f"status={result.returncode} stdout={result.stdout[:160]!r} stderr={result.stderr[:160]!r}"
        ) from error
    required = {
        "network_backend", "network_interface", "network_connected", "network_name",
        "timezone", "ntp_enabled", "time_synchronized", "bluetooth_backend",
        "bluetooth_controller_present", "bluetooth_powered",
    }
    if result.returncode or set(value) != required or (
        value.get("network_backend"), value.get("network_interface"),
        value.get("network_connected"), value.get("timezone"),
        value.get("bluetooth_controller_present"),
    ) != ("iwd", "wlan0", True, "America/Sao_Paulo", True):
        raise OfficialHubGraphicalError("authenticated Host-services state differs")
    return value


def verify_host_services() -> dict[str, object]:
    initial = host_services_call("json")
    initial_power = initial["bluetooth_powered"]
    if initial["bluetooth_backend"] != "bluez" or type(initial_power) is not bool:
        raise OfficialHubGraphicalError("Bluetooth Host baseline differs before toggle proof")
    try:
        toggled = host_services_call("bluetooth-toggle")
        if toggled["bluetooth_powered"] is initial_power:
            raise OfficialHubGraphicalError("Bluetooth Host toggle proof failed")
    finally:
        observed = host_services_call("json")
        restored = host_services_call("bluetooth-toggle") \
            if observed["bluetooth_powered"] is not initial_power else observed
    if restored["bluetooth_powered"] is not initial_power:
        raise OfficialHubGraphicalError("Bluetooth Host state recovery failed")
    return initial


def host_services_v2_call(operation: str, target: str | None = None) -> dict[str, object]:
    if operation not in {"status", "wifi-scan", "bluetooth-power"} \
            or operation == "bluetooth-power" and target not in {"on", "off"} \
            or operation != "bluetooth-power" and target is not None:
        raise OfficialHubGraphicalError("Host-services v2 verification operation differs")
    command = [
        "systemd-run", "-M", MACHINE, "--quiet", "--pipe", "--wait", "--collect",
        "--uid=apx", "--", "/run/apx/host-services-client-v2.py", operation,
    ]
    if target is not None:
        command.append(target)
    result = run((
        *command,
    ), False)
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise OfficialHubGraphicalError("Host-services v2 returned malformed state") from error
    if result.returncode or value.get("network_backend") != "iwd" \
            or value.get("bluetooth_backend") != "bluez" \
            or type(value.get("known_networks")) is not list \
            or type(value.get("bluetooth_devices")) is not list:
        raise OfficialHubGraphicalError("authenticated Host-services v2 state differs")
    return value


def verify_host_services_v2() -> dict[str, object]:
    initial = host_services_v2_call("status")
    initial_power = initial.get("bluetooth_powered")
    if type(initial_power) is not bool:
        raise OfficialHubGraphicalError("Host-services v2 Bluetooth baseline differs")
    scanned = host_services_v2_call("wifi-scan")
    if scanned.get("network_name") != initial.get("network_name"):
        raise OfficialHubGraphicalError("Host-services v2 Wi-Fi scan changed the active network")
    try:
        target = "off" if initial_power else "on"
        powered = host_services_v2_call("bluetooth-power", target)
        if powered.get("bluetooth_powered") is initial_power:
            raise OfficialHubGraphicalError("Host-services v2 Bluetooth power proof failed")
    finally:
        observed = host_services_v2_call("status")
        restored = host_services_v2_call("bluetooth-power", "on" if initial_power else "off") \
            if observed.get("bluetooth_powered") is not initial_power else observed
    if restored.get("bluetooth_powered") is not initial_power:
        raise OfficialHubGraphicalError("Host-services v2 Bluetooth state recovery failed")
    return initial


def host_services_v3_call(operation: str) -> dict[str, object]:
    if operation not in {"capabilities", "events", "snapshot", "wifi-status"}:
        raise OfficialHubGraphicalError("Host-services v3 verification operation differs")
    result = run((
        "systemd-run", "-M", MACHINE, "--quiet", "--pipe", "--wait", "--collect",
        "--uid=apx", "--", "/run/apx/host-services-client-v3.py", operation,
    ), False)
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise OfficialHubGraphicalError("Host-services v3 returned malformed state") from error
    if result.returncode or type(value) is not dict:
        raise OfficialHubGraphicalError("authenticated Host-services v3 state differs")
    return value


def verify_host_services_v3() -> dict[str, object]:
    capabilities = host_services_v3_call("capabilities")
    state = host_services_v3_call("wifi-status")
    snapshot = host_services_v3_call("snapshot")
    events = host_services_v3_call("events")
    if "network.connect" not in capabilities.get("operations", ()) \
            or capabilities.get("security", {}).get("secret_transport") != "unix-socket-body" \
            or state.get("backend") != "iwd" or type(state.get("networks")) is not list \
            or snapshot.get("version") != 3 or snapshot.get("network", {}).get("network") != state.get("network") \
            or type(events.get("events")) is not list or not events["events"]:
        raise OfficialHubGraphicalError("Host-services v3 capabilities or snapshot differ")
    return state


def verify_nvidia_render(pid: int) -> str:
    result = run((
        "nsenter", "--target", str(pid), "--mount", "--pid", "--", "env",
        "DRI_PRIME=1!", "/usr/bin/vulkaninfo", "--summary",
    ), False)
    match = re.search(r"deviceName\s*=\s*(.+NVIDIA.+|.+RTX 3060.+)$", result.stdout, re.MULTILINE | re.IGNORECASE)
    if result.returncode or match is None:
        raise OfficialHubGraphicalError(
            "NVIDIA render offload proof failed: " + (result.stderr or result.stdout)[-300:]
        )
    return match.group(1).strip()


def verify_local_admin(pid: int, uid_base: int) -> None:
    status = dict(
        line.split(":", 1) for line in Path(f"/proc/{pid}/status").read_text().splitlines()
        if ":" in line
    )
    uid_fields = status.get("Uid", "").split()
    if uid_fields != [str(uid_base + 1000)] * 4 or status.get("NoNewPrivs", "").strip() != "0" \
            or int(status.get("CapBnd", "0").strip(), 16) == 0:
        raise OfficialHubGraphicalError("graphical user session cannot acquire Environment-local authority")
    policy = "apx ALL=(root) NOPASSWD: /usr/bin/id -u\n"
    prepare = (
        "/usr/bin/printf '%s' '" + policy + "' | "
        "/usr/bin/install -m 0440 /dev/stdin " + LOCAL_ADMIN_PROOF
    )
    run(("machinectl", "shell", f"root@{MACHINE}", "/usr/bin/bash", "-lc", prepare))
    try:
        result = run((
            "systemd-run", "-M", MACHINE, "--quiet", "--pipe", "--wait", "--collect",
            "--uid=apx", "--", "/usr/bin/sudo", "-n", "/usr/bin/id", "-u",
        ), False)
        if result.returncode or result.stdout.strip() != "0":
            raise OfficialHubGraphicalError("Environment-local sudo elevation proof failed")
        refused = run((
            "systemd-run", "-M", MACHINE, "--quiet", "--pipe", "--wait", "--collect",
            "--uid=root", "--", "/run/apx/host-services-client-v1.py", "json",
        ), False)
        if refused.returncode == 0:
            raise OfficialHubGraphicalError("Environment-local root reached the user-only Host service")
        hostname = run(("machinectl", "shell", f"root@{MACHINE}", "/usr/bin/cat", "/etc/hostname"), False)
        if hostname.stdout.strip() != MACHINE:
            raise OfficialHubGraphicalError("Environment-local root filesystem identity differs")
    finally:
        run(("machinectl", "shell", f"root@{MACHINE}", "/usr/bin/rm", "-f", LOCAL_ADMIN_PROOF), False)


def open_and_verify_kitty(pid: int, signature: str) -> None:
    dispatched = hyprctl(
        pid, signature, "dispatch",
        'hl.dsp.exec_cmd("kitty --directory /home/apx /usr/bin/nice -n 10 '
        '/usr/bin/ionice -c 3 /usr/bin/bash")',
    )
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
    stable_observations = 0
    last = (0, "", "", ())
    while time.monotonic() < deadline:
        last = compositor_state()
        if last[0] and last[1] and last[2] and len(last[3]) >= 1:
            stable_observations += 1
            if stable_observations >= 2:
                return last[0], last[1], last[3]
        else:
            stable_observations = 0
        time.sleep(0.05)
    raise OfficialHubGraphicalError(
        f"Hyprland readiness incomplete: pid={last[0]} socket={bool(last[1])} "
        f"internal_monitor={last[2] or 'absent'} keyboards={len(last[3])}"
    )


def _watchdog_failures() -> int:
    if not WATCHDOG_STATE.exists():
        return 0
    metadata = WATCHDOG_STATE.lstat()
    data = WATCHDOG_STATE.read_bytes()
    if WATCHDOG_STATE.is_symlink() or not WATCHDOG_STATE.is_file() \
            or metadata.st_uid != 0 or metadata.st_gid != 0 or len(data) > 512:
        raise OfficialHubGraphicalError("health watchdog state is untrusted")
    value = json.loads(data)
    failures = value.get("failures") if type(value) is dict else None
    if type(value) is not dict or value.get("schema") != 1 \
            or type(failures) is not int or not 1 <= failures <= 2:
        raise OfficialHubGraphicalError("health watchdog state is malformed")
    return failures


def _write_watchdog_failures(failures: int) -> None:
    if not 1 <= failures <= 2:
        raise OfficialHubGraphicalError("health watchdog failure count differs")
    WATCHDOG_STATE.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
    temporary = WATCHDOG_STATE.with_name(f".{WATCHDOG_STATE.name}.{os.getpid()}.tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        payload = {"schema": 1, "failures": failures}
        os.write(descriptor, (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode())
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    os.replace(temporary, WATCHDOG_STATE)


def health_watchdog() -> dict[str, object]:
    if not unit_active(OUTER_UNIT) and not machine_running():
        WATCHDOG_STATE.unlink(missing_ok=True)
        return {"classification": "inactive", "recovered": False}
    healthy = False
    try:
        registration = read_registration()
        active = json.loads(ACTIVE.read_text())
        pid, signature, monitor, keyboards = compositor_state()
        healthy = registration.get("state") == "running" \
            and type(active) is dict \
            and (active.get("profile"), active.get("generation"), active.get("unit")) == (
                "apx-official-hub-graphical-v1", GENERATION, OUTER_UNIT + ".service",
            ) \
            and active.get("pid") == pid and pid > 0 and bool(signature) and monitor \
            and len(keyboards) >= 1 and unit_active(OUTER_UNIT) and machine_running() \
            and run(("systemctl", "-M", MACHINE, "is-active", "--quiet", INNER_UNIT + ".service"), False).returncode == 0
    except (OSError, ValueError, json.JSONDecodeError, OfficialHubGraphicalError):
        healthy = False
    if healthy:
        WATCHDOG_STATE.unlink(missing_ok=True)
        return {"classification": "healthy", "recovered": False}
    # A transient compositor/IPC observation must never end an interactive
    # session behind the owner's back. Keep reporting a saturated degraded
    # state; explicit return/recovery actions remain available when wanted.
    failures = min(_watchdog_failures() + 1, 2)
    _write_watchdog_failures(failures)
    return {"classification": "degraded", "failures": failures,
            "recovered": False, "action_required": True}


def launch(test_mode: bool, authenticated_handoff: bool = False) -> dict[str, object]:
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
    audio = resolve_audio_devices()
    graphics = resolve_graphics()
    validate_devices(inputs, audio, graphics)
    ensure_audio_master_playback(audio)
    device_nodes = tuple(dict.fromkeys((
        *inputs.values(), *audio.values(), graphics["display_card"], graphics["display_render"],
        *((graphics["offload_card"], graphics["offload_render"])
          if "offload_render" in graphics else ()),
        graphics["nvidia_device"], graphics["nvidia_control"], graphics["nvidia_modeset"],
        "/dev/tty2",
    )))
    bindings = prepare_device_leases(device_nodes)
    result: dict[str, object] = {}
    try:
        start_host_seatd(inputs, graphics)
        arm_test_expiry(75) if test_mode else arm_health_watchdog()
        start_outer(inputs, audio, graphics, bindings, authenticated_handoff)
        uid_base = resolve_user_namespace()
        activate_device_leases(uid_base)
        activate_service_sockets(uid_base)
        start_inner(inputs, audio, graphics)
        print("APX: a mudar para tty2. Super+Q abre Kitty; Super+M volta à recuperação Host.", flush=True)
        print("APX: Ctrl+Alt+F1 volta visualmente ao Host; o watchdog apenas monitoriza.", flush=True)
        run(("chvt", "2"), False)
        pid, signature, keyboards = wait_ready()
        audio_state = verify_audio_playback(pid)
        desktop_shell = verify_desktop_shell()
        write_registration_state("running")
        publish_active_state(pid)
        host_services: dict[str, object] = {}
        host_services_v2: dict[str, object] = {}
        host_services_v3: dict[str, object] = {}
        nvidia_device = ""
        if test_mode:
            verify_update_and_audio_services()
            host_services = verify_host_services()
            host_services_v2 = verify_host_services_v2()
            host_services_v3 = verify_host_services_v3()
            nvidia_device = verify_nvidia_render(pid)
            verify_local_admin(pid, uid_base)
        if test_mode:
            open_and_verify_kitty(pid, signature)
            time.sleep(3)
            result = {
                "classification": "verified", "hyprland": True, "kitty": True,
                "desktop_shell": desktop_shell, "quickshell": True,
                "audio_playback": True, "audio_capture": True, "audio_handoff": True,
                "coordinated_updates": True, "audio_state": audio_state,
                "system_power_two_step": True,
                "host_services": True, "network_backend": host_services["network_backend"],
                "ntp_enabled": host_services["ntp_enabled"],
                "bluetooth_backend": host_services["bluetooth_backend"],
                "bluetooth_toggle": True,
                "context_menus_backend": bool(host_services_v2["known_networks"]),
                "host_services_v3": True,
                "wifi_network_objects": bool(host_services_v3["networks"]),
                "gpu_policy": graphics["policy"],
                "nvidia_render": True, "nvidia_device": nvidia_device,
                "private_users": True, "local_admin": True,
                "monitor": compositor_state()[2], "keyboard_count": len(keyboards),
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
    mode.add_argument("--watchdog", action="store_true")
    parser.add_argument("--authenticated-handoff", action="store_true")
    arguments = parser.parse_args()
    if arguments.recover:
        recover()
        return 0
    if arguments.watchdog:
        print(json.dumps(health_watchdog(), sort_keys=True, separators=(",", ":")))
        return 0
    if arguments.authenticated_handoff and not arguments.interactive:
        parser.error("authenticated handoff requires interactive mode")
    result = launch(arguments.test, arguments.authenticated_handoff)
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OfficialHubGraphicalError, subprocess.CalledProcessError, OSError, ValueError) as error:
        print(f"APX official Hub graphics refused: {error}", file=os.sys.stderr)
        raise SystemExit(2)
