"""Pure admission contract for the owner-built, headless official Hub base."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json


PROFILE = "apx-hub-headless-v4-release"
RELEASE_ID = "hub-headless-v4"
REQUIRED_PACKAGES = frozenset({"base", "pacman", "systemd", "sudo", "ca-certificates"})
FORBIDDEN_PACKAGES = frozenset({
    "hyprland", "kitty", "waybar", "foot", "fuzzel", "mako",
    "xdg-desktop-portal", "xdg-desktop-portal-hyprland",
    "pipewire", "wireplumber",
})


class HubCleanReleaseError(ValueError):
    pass


@dataclass(frozen=True)
class HubCleanReleaseEvidence:
    package_names: tuple[str, ...]
    build_a_tree_digest: str
    build_b_tree_digest: str
    apx_client_present: bool
    apx_user_locked_before_enrollment: bool
    sudo_requires_password: bool
    empty_graphical_config: bool
    network_namespace_declared: bool
    host_and_sibling_denial_declared: bool
    package_signatures_verified: bool


@dataclass(frozen=True)
class HubCleanReleaseResult:
    profile: str
    release_id: str
    classification: str
    blockers: tuple[str, ...]
    manifest_digest: str


def assess_hub_clean_release(evidence: HubCleanReleaseEvidence) -> HubCleanReleaseResult:
    if type(evidence) is not HubCleanReleaseEvidence:
        raise HubCleanReleaseError("Hub release evidence has wrong type")
    if tuple(sorted(set(evidence.package_names))) != evidence.package_names:
        raise HubCleanReleaseError("package names must be unique and sorted")
    if any(not name or len(name) > 128 for name in evidence.package_names):
        raise HubCleanReleaseError("package name is invalid")
    for digest in (evidence.build_a_tree_digest, evidence.build_b_tree_digest):
        if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
            raise HubCleanReleaseError("build tree digest is malformed")
    booleans = (
        evidence.apx_client_present, evidence.apx_user_locked_before_enrollment,
        evidence.sudo_requires_password, evidence.empty_graphical_config,
        evidence.network_namespace_declared, evidence.host_and_sibling_denial_declared,
        evidence.package_signatures_verified,
    )
    if any(type(value) is not bool for value in booleans):
        raise HubCleanReleaseError("Hub release gate is not boolean")
    packages = set(evidence.package_names)
    blockers: list[str] = []
    missing = sorted(REQUIRED_PACKAGES - packages)
    forbidden = sorted(FORBIDDEN_PACKAGES & packages)
    if missing:
        blockers.append("required base packages are missing: " + ",".join(missing))
    if forbidden:
        blockers.append("graphical packages are present: " + ",".join(forbidden))
    gates = (
        ("independent builds differ", evidence.build_a_tree_digest == evidence.build_b_tree_digest),
        ("APX Hub client is absent", evidence.apx_client_present),
        ("apx password is not locked before enrollment", evidence.apx_user_locked_before_enrollment),
        ("sudo is not password protected", evidence.sudo_requires_password),
        ("graphical configuration is not empty", evidence.empty_graphical_config),
        ("private network namespace is not declared", evidence.network_namespace_declared),
        ("Host and sibling network denial is not declared", evidence.host_and_sibling_denial_declared),
        ("package signatures were not verified", evidence.package_signatures_verified),
    )
    blockers.extend(label for label, passed in gates if not passed)
    payload = {
        "profile": PROFILE, "release_id": RELEASE_ID,
        "package_names": evidence.package_names,
        "tree_digest": evidence.build_a_tree_digest,
        "apx_client_present": evidence.apx_client_present,
        "apx_user_locked_before_enrollment": evidence.apx_user_locked_before_enrollment,
        "sudo_requires_password": evidence.sudo_requires_password,
        "empty_graphical_config": evidence.empty_graphical_config,
        "network_namespace_declared": evidence.network_namespace_declared,
        "host_and_sibling_denial_declared": evidence.host_and_sibling_denial_declared,
        "package_signatures_verified": evidence.package_signatures_verified,
    }
    manifest_digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return HubCleanReleaseResult(
        profile=PROFILE, release_id=RELEASE_ID,
        classification="ready-for-publication" if not blockers else "blocked",
        blockers=tuple(blockers), manifest_digest=manifest_digest,
    )
