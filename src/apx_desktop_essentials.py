"""Pure admission contract for the common APX desktop-essential profile."""

from __future__ import annotations

from dataclasses import dataclass


PROFILE = "desktop-essential-v1"
CONFIGURATION_PROFILE = "waybar-ascii-v1"
LOCAL_PACKAGES = (
    "iproute2",
    "iputils",
    "pipewire",
    "pipewire-audio",
    "pipewire-pulse",
    "tzdata",
    "waybar",
    "wireplumber",
)
OPTIONAL_LOCAL_PACKAGES = ("pavucontrol", "vulkan-nouveau", "vulkan-tools")
LOCAL_CONTROLS = ("audio",)
HOST_MEDIATED_CONTROLS = ("bluetooth", "network", "system_time")
SERVICES_NOT_ENABLED = (
    "bluetooth.service",
    "NetworkManager.service",
    "systemd-timesyncd.service",
)


class DesktopEssentialsError(ValueError):
    pass


@dataclass(frozen=True)
class DesktopEssentialsEvidence:
    profile: str
    configuration_profile: str
    package_names: tuple[str, ...]
    independent_config_copy: bool
    environment_local_audio: bool
    private_host_mediated_network: bool
    host_owned_system_time: bool
    bluetooth_exclusive_mediator: bool
    host_hardware_services_disabled: bool


@dataclass(frozen=True)
class DesktopEssentialsAssessment:
    classification: str
    ready_controls: tuple[str, ...]
    locked_controls: tuple[str, ...]
    issues: tuple[str, ...]


def assess_desktop_essentials(
    evidence: DesktopEssentialsEvidence,
) -> DesktopEssentialsAssessment:
    if type(evidence) is not DesktopEssentialsEvidence:
        raise DesktopEssentialsError("desktop-essential evidence has wrong type")
    issues: list[str] = []
    if (evidence.profile, evidence.configuration_profile) != (
        PROFILE,
        CONFIGURATION_PROFILE,
    ):
        issues.append("desktop-essential profile identity differs")
    if evidence.package_names != tuple(sorted(set(evidence.package_names))):
        issues.append("desktop-essential package set is not canonical")
    elif not set(LOCAL_PACKAGES) <= set(evidence.package_names):
        issues.append("desktop-essential local package set is incomplete")
    required = (
        evidence.independent_config_copy,
        evidence.environment_local_audio,
        evidence.private_host_mediated_network,
        evidence.host_owned_system_time,
        evidence.host_hardware_services_disabled,
    )
    if any(type(value) is not bool for value in (*required, evidence.bluetooth_exclusive_mediator)):
        raise DesktopEssentialsError("desktop-essential evidence has wrong boolean type")
    if not all(required):
        issues.append("desktop-essential isolation evidence is incomplete")
    ready = ("audio", "network-status", "system-time-status") if not issues else ()
    locked = () if evidence.bluetooth_exclusive_mediator and not issues else ("bluetooth",)
    return DesktopEssentialsAssessment(
        "ready" if not issues and not locked else "ready-with-locked-capability" if not issues else "blocked",
        ready,
        locked,
        tuple(issues),
    )
