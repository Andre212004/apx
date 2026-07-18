"""Pure two-unit launch plan for the exact physical H0 experiment."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re

from apx_hyprland_h0_device_lease import H0DeviceLeasePlan


EXPERIMENT = "h0-3ef21d19a2518d4fcea9d51513cc1eee-v6"
ENVIRONMENT = "codex-test-hyprland-h0-v1"
GENERATION = "c4fc5c49-4106-4a56-b1f0-13bffa41a0c1"
LEASE_PLAN_DIGEST = "3ef21d19a2518d4fcea9d51513cc1eee63f6ff593d4470bcc10955b06e3059cb"
GRAPHICAL_UNIT = "apx-h0-graphical-c4fc5c49"
EXPIRY_UNIT = "apx-h0-expiry-c4fc5c49"
STATE = f"/var/lib/apx/h0/{EXPERIMENT}"
ROOT = f"/var/lib/apx/environments/{ENVIRONMENT}/root"
HOME = f"/var/lib/apx/environments/{ENVIRONMENT}/home"
MACHINE = f"apx-{ENVIRONMENT}"
ASSETS = (
    ("hyprland.conf", "59c824f5aeb83f51cd1127712c57c8f7bce69ba85c97e793c1589953677f7529", 0o400),
    ("session", "db099965ab22ba322f2d113365af6e561c612c92bd660a3205d6023072ed743c", 0o500),
    ("watchdog", "5c7d63bb2dd505f7f1c916fa1d3dd3083c4f8e591e11d2514424e2e2af7402e9", 0o500),
)
BIND_SOURCES = {
    "built-in-keyboard": "/dev/input/event3",
    "built-in-touchpad": "/dev/input/event11",
}
_SHA = re.compile(r"[0-9a-f]{64}")


class H0LaunchPlanError(ValueError):
    pass


@dataclass(frozen=True)
class H0LaunchPlan:
    experiment: str
    generation: str
    lease_plan_digest: str
    assets: tuple[tuple[str, str, int], ...]
    ordered_gates: tuple[str, ...]
    expiry_command: tuple[str, ...]
    graphical_command: tuple[str, ...]
    plan_digest: str


def build_launch_plan(lease: H0DeviceLeasePlan) -> H0LaunchPlan:
    if type(lease) is not H0DeviceLeasePlan or lease.plan_digest != LEASE_PLAN_DIGEST:
        raise H0LaunchPlanError("launch lease is stale or outside exact H0")
    if lease.generation != GENERATION or lease.environment != ENVIRONMENT or lease.timeout_seconds != 120:
        raise H0LaunchPlanError("launch subject or timeout changed")
    expiry = (
        "/usr/bin/systemd-run", f"--unit={EXPIRY_UNIT}", "--on-active=120s",
        "--timer-property=AccuracySec=1s", "--property=Type=oneshot",
        "--property=NoNewPrivileges=yes", "--property=ProtectSystem=strict",
        "--property=ProtectHome=yes", "--property=PrivateNetwork=yes",
        f"{STATE}/watchdog", "--expire",
    )
    properties = (
        "--property=Delegate=yes", "--property=KillMode=mixed",
        "--property=MemoryMax=1536M", "--property=TasksMax=512",
        "--property=CPUQuota=100%", "--property=DevicePolicy=closed",
        *(f"--property=DeviceAllow={host} {access}" for _, host, _, _, _, access in lease.devices),
    )
    binds = tuple(
        f"--bind={BIND_SOURCES.get(name, host)}:{inside}"
        for name, host, inside, _, _, _ in lease.devices
    )
    graphical = (
        "/usr/bin/systemd-run", f"--unit={GRAPHICAL_UNIT}", "--collect", *properties,
        "--", "/usr/bin/systemd-nspawn", "--quiet", "--keep-unit",
        f"--directory={ROOT}", f"--machine={MACHINE}", f"--hostname={MACHINE}",
        "--register=yes", "--settings=no", "--private-network",
        "--resolv-conf=off", "--timezone=off", "--link-journal=no",
        "--console=pipe", "--private-users=no", "--no-new-privileges=yes",
        f"--bind={HOME}:/home", f"--bind-ro={STATE}/hyprland.conf:/run/apx-h0/hyprland.conf",
        f"--bind-ro={STATE}/session:/run/apx-h0/session", *binds,
        "--", "/run/apx-h0/session",
    )
    ordered = (
        "revalidate-generation-release-devices-vts-and-zero-residue",
        "stage-and-rehash-three-fixed-assets",
        "start-independent-expiry-timer",
        "verify-expiry-timer-active-before-any-device-grant",
        "start-generation-bound-graphical-unit",
        "observe-wayland-eDP2-keyboard-touchpad-within-deadline",
        "invoke-expiry-path-even-after-normal-session-exit",
        "verify-tty1-and-zero-residue-before-cancelling-timer",
    )
    draft = {"experiment": EXPERIMENT, "generation": GENERATION,
        "lease_plan_digest": LEASE_PLAN_DIGEST, "assets": ASSETS,
        "ordered_gates": ordered, "expiry_command": expiry,
        "graphical_command": graphical}
    digest = hashlib.sha256(json.dumps(draft, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return H0LaunchPlan(**draft, plan_digest=digest)
