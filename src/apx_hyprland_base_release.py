"""Pure admission contract for the reusable APX Hyprland base release."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import re


PROFILE = "apx-hyprland-base-release-v2"
RELEASE = "hyprland-base-v2"
CONFIG_SEED = "hyprland-minimal-v2"
PACKAGE_SEEDS = (
    "alacritty", "base", "base-devel", "bash-completion", "ca-certificates", "chafa", "dbus-broker",
    "egl-gbm", "fastfetch", "file-roller", "flatpak", "foot", "fuzzel", "gnome-keyring",
    "git", "grim", "gtk4", "gvfs", "gvfs-gphoto2", "gvfs-mtp", "gvfs-smb",
    "hypridle", "hyprland", "hyprlock", "hyprpolkitagent", "iproute2", "iputils", "less", "libadwaita",
    "libnotify", "mako", "man-db", "mesa", "mousepad", "nano", "ncurses", "noto-fonts", "nvidia-utils", "pacman-contrib",
    "pipewire", "polkit", "python-gobject", "ristretto", "rofi", "slurp",
    "sudo", "thunar", "tumbler", "udiskie", "udisks2",
    "vulkan-radeon", "waybar", "wireplumber", "xdg-desktop-portal",
    "xdg-desktop-portal-gtk", "xdg-desktop-portal-hyprland", "xdg-user-dirs",
    "xkeyboard-config",
)
CONFIG_ASSETS = (
    ("alacritty/alacritty.toml", "14f9191aec4f69568e4c12bba0b96c3cf90989f0a2295eb79bf1a277b7b6a3be"),
    ("fastfetch/apx-logo.txt", "cd7ae1943f3b4da9c751e93a1f19f5c12594ae35a28dce0d80fcfaa8f7149077"),
    ("fastfetch/config.jsonc", "9c8f7b3184452b42c3e8670805cf7215fa073a7fe32f25d9251a17e08bc4c736"),
    ("hyprland/hyprland.conf", "8d793c51f1fb5195d12636ebc504d6c80cfac836245bacbcf5f90ac769a925ac"),
    ("rofi/config.rasi", "2894cd7636fcf0f03f1a7c19a1008cb8b0c162ac5fae4e9fa85dfe7484a2aa78"),
    ("waybar/config.json", "7a045de24f89c69be7e373cc7dc82bb06b62b0a8ee15ec41719fbce0f0de2d2f"),
    ("waybar/style.css", "4e649de831c068be9ff05d0c9d6ad03351e1b1a1c44ad752b44a8c353bcd90ca"),
)
# The GTK program in prototypes/ is deliberately excluded. A future production
# Hub overlay must define and admit its own immutable artifact.
HUB_ASSETS: tuple[tuple[str, str], ...] = ()
HUB_APPLICATION_STATUS = "future-production-artifact-required"
_SHA = re.compile(r"[0-9a-f]{64}")


class HyprlandBaseReleaseError(ValueError):
    pass


@dataclass(frozen=True)
class HyprlandBaseEvidence:
    profile: str
    release: str
    config_seed: str
    package_names: tuple[str, ...]
    package_manifest_digest: str
    all_package_signatures_verified: bool
    independent_signature_pass_verified: bool
    first_root_digest: str
    second_root_digest: str
    config_assets: tuple[tuple[str, str], ...]
    hub_assets: tuple[tuple[str, str], ...]
    machine_identity_empty: bool
    package_log_empty: bool
    private_keys_absent: bool
    special_files_absent: bool


@dataclass(frozen=True)
class HyprlandBaseAssessment:
    classification: str
    issues: tuple[str, ...]
    evidence_digest: str


def assess_release(evidence: HyprlandBaseEvidence) -> HyprlandBaseAssessment:
    if type(evidence) is not HyprlandBaseEvidence:
        raise HyprlandBaseReleaseError("release evidence has wrong type")
    issues: list[str] = []
    if (evidence.profile, evidence.release, evidence.config_seed) != (PROFILE, RELEASE, CONFIG_SEED):
        issues.append("release identity differs from the fixed Hyprland base")
    if evidence.package_names != tuple(sorted(set(evidence.package_names))):
        issues.append("package names are not unique and canonically sorted")
    if not set(PACKAGE_SEEDS) <= set(evidence.package_names):
        issues.append("graphical package seed is incomplete")
    for value in (evidence.package_manifest_digest, evidence.first_root_digest, evidence.second_root_digest):
        if not isinstance(value, str) or not _SHA.fullmatch(value):
            issues.append("release digest is malformed")
            break
    if evidence.first_root_digest != evidence.second_root_digest:
        issues.append("independent release builds differ")
    if evidence.config_assets != CONFIG_ASSETS or evidence.hub_assets != HUB_ASSETS:
        issues.append("versioned graphical assets differ")
    booleans = (
        evidence.all_package_signatures_verified,
        evidence.independent_signature_pass_verified,
        evidence.machine_identity_empty,
        evidence.package_log_empty,
        evidence.private_keys_absent,
        evidence.special_files_absent,
    )
    if any(type(value) is not bool for value in booleans) or not all(booleans):
        issues.append("signature or sanitization evidence is incomplete")
    encoded = json.dumps(asdict(evidence), sort_keys=True, separators=(",", ":")).encode()
    return HyprlandBaseAssessment(
        "verified" if not issues else "blocked",
        tuple(dict.fromkeys(issues)),
        hashlib.sha256(encoded).hexdigest(),
    )
