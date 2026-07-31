"""Pure exact device-lease plan for the first physical Hyprland H0 run."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import re


PROFILE = "apx-hyprland-h0-device-lease-v2"
ENVIRONMENT = "codex-test-hyprland-h0-v1"
GENERATION = "c4fc5c49-4106-4a56-b1f0-13bffa41a0c1"
RECOVERY_VT = "/dev/tty1"
EXPERIMENT_VT = "/dev/tty2"
TIMEOUT_SECONDS = 15
DEVICES = (
    ("amd-kms", "/dev/dri/card2", "/dev/dri/card2", 226, 2, "rw"),
    ("amd-render", "/dev/dri/renderD129", "/dev/dri/renderD129", 226, 129, "rw"),
    ("built-in-keyboard", "/dev/input/by-path/platform-i8042-serio-0-event-kbd", "/dev/input/event0", 13, 67, "r"),
    ("built-in-touchpad", "/dev/input/by-path/platform-AMDI0010:01-event-mouse", "/dev/input/event1", 13, 75, "r"),
    ("experiment-vt", EXPERIMENT_VT, EXPERIMENT_VT, 4, 2, "rw"),
)
DENIED = (
    "/dev/dri/card1", "/dev/dri/renderD128", "/dev/input/event0",
    "/dev/input/event1", "/dev/input/event2", "/dev/input/event4",
    "/dev/input/event5", "/dev/input/event6", "/dev/input/event7",
    "/dev/input/event8", "/dev/input/event9", "/dev/input/event10",
    "/dev/tty1", "/dev/snd", "/dev/video0",
)
_SHA = re.compile(r"[0-9a-f]{64}")


class H0DeviceLeaseError(ValueError):
    pass


@dataclass(frozen=True)
class H0DeviceObservation:
    environment_generation: str
    release_manifest_digest: str
    amd_pci: str
    amd_driver: str
    connector: str
    connector_connected: bool
    recovery_vt_active: bool
    experiment_vt_inactive: bool
    no_graphical_owner: bool
    no_display_manager: bool
    hub_stopped: bool
    development_stopped: bool
    no_uncertain_apx_operation: bool
    device_identities: tuple[tuple[str, str, int, int], ...]


@dataclass(frozen=True)
class H0DeviceLeasePlan:
    profile: str
    environment: str
    generation: str
    recovery_vt: str
    experiment_vt: str
    timeout_seconds: int
    devices: tuple[tuple[str, str, str, int, int, str], ...]
    denied: tuple[str, ...]
    runtime_properties: tuple[str, ...]
    watchdog_actions: tuple[str, ...]
    observation_digest: str
    plan_digest: str


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def build_device_lease_plan(observation: H0DeviceObservation) -> H0DeviceLeasePlan:
    if type(observation) is not H0DeviceObservation:
        raise H0DeviceLeaseError("H0 device observation has wrong type")
    if observation.environment_generation != GENERATION:
        raise H0DeviceLeaseError("H0 Environment generation changed")
    if not _SHA.fullmatch(observation.release_manifest_digest):
        raise H0DeviceLeaseError("release manifest identity is malformed")
    if observation.amd_pci != "0000:05:00.0" or observation.amd_driver != "amdgpu":
        raise H0DeviceLeaseError("AMD device identity changed")
    if observation.connector != "card2-eDP-2":
        raise H0DeviceLeaseError("internal connector identity changed")
    gates = (
        observation.connector_connected, observation.recovery_vt_active,
        observation.experiment_vt_inactive, observation.no_graphical_owner,
        observation.no_display_manager, observation.hub_stopped,
        observation.development_stopped, observation.no_uncertain_apx_operation,
    )
    if any(type(value) is not bool for value in gates) or not all(gates):
        raise H0DeviceLeaseError("H0 clean-host or recovery gate is not satisfied")
    expected = tuple((name, host_path, major, minor) for name, host_path, _, major, minor, _ in DEVICES)
    if observation.device_identities != expected:
        raise H0DeviceLeaseError("H0 device set or character identity changed")
    properties = (
        "DevicePolicy=closed",
        *(f"DeviceAllow={host_path} {access}" for _, host_path, _, _, _, access in DEVICES),
        "PrivateNetwork=yes", "ProtectSystem=strict", "ProtectHome=yes",
        "NoNewPrivileges=yes", "TimeoutStopSec=3s",
    )
    watchdog = (
        "arm-host-owned-15-second-deadline-before-device-grant",
        "terminate-only-the-generation-bound-h0-unit-on-deadline",
        "revoke-all-five-device-grants",
        "switch-active-console-back-to-tty1",
        "verify-no-machine-process-wayland-socket-or-device-lease-remains",
        "never-restart-graphical-session-automatically",
        "keep-local-super-shift-e-emergency-exit",
    )
    observation_digest = _digest(asdict(observation))
    draft = {
        "profile": PROFILE, "environment": ENVIRONMENT, "generation": GENERATION,
        "recovery_vt": RECOVERY_VT, "experiment_vt": EXPERIMENT_VT,
        "timeout_seconds": TIMEOUT_SECONDS, "devices": DEVICES, "denied": DENIED,
        "runtime_properties": properties, "watchdog_actions": watchdog,
        "observation_digest": observation_digest,
    }
    return H0DeviceLeasePlan(**draft, plan_digest=_digest(draft))
