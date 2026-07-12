"""Pure, non-mutating isolation-policy contracts for APX Environments."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json


POLICY_SCHEMA_VERSION = 1
POLICY_VERSION = "environment-boundary-v1"

REQUIRED_NAMESPACES = (
    "cgroup",
    "ipc",
    "mount",
    "network",
    "pid",
    "user",
    "uts",
)

FORBIDDEN_HOST_SURFACES = (
    "apx-control-plane",
    "apx-metadata",
    "base-writable-state",
    "host-dbus",
    "host-home",
    "host-package-cache",
    "host-package-database",
    "host-root",
    "host-runtime-sockets",
    "host-secret-store",
    "hub-home",
    "hub-root",
    "sibling-environment-home",
    "sibling-environment-root",
)

FILESYSTEM_RULES = (
    ("apx-base", "read-only"),
    ("apx-control-plane", "inaccessible"),
    ("apx-metadata", "inaccessible"),
    ("environment-home", "writable-owner-only"),
    ("environment-root", "writable-owner-only"),
    ("host-home", "inaccessible"),
    ("host-package-state", "inaccessible"),
    ("host-root", "inaccessible"),
    ("hub-home", "inaccessible"),
    ("hub-root", "inaccessible"),
    ("sibling-environments", "inaccessible"),
)

TEARDOWN_REQUIREMENTS = (
    "no-active-session",
    "no-device-clients",
    "no-mounts",
    "no-network-objects",
    "no-processes",
    "no-runtime-record",
    "no-user-manager",
)

NORMAL_LIMITS = (
    ("cpu-weight", "bounded"),
    ("home-storage", "enforced-policy-limit"),
    ("io-weight", "bounded"),
    ("memory-high", "required"),
    ("memory-max", "required"),
    ("root-storage", "enforced-policy-limit"),
    ("tasks-max", "required"),
)

HIGH_SECURITY_LIMITS = (
    ("cpu-time", "required"),
    ("cpu-weight", "restricted"),
    ("home-storage", "enforced-policy-limit"),
    ("io-weight", "restricted"),
    ("memory-high", "required"),
    ("memory-max", "required"),
    ("root-storage", "enforced-policy-limit"),
    ("tasks-max", "restricted"),
)


@dataclass(frozen=True)
class EnvironmentIsolationPolicy:
    schema_version: int
    policy_version: str
    profile: str
    security_claim: str
    namespaces: tuple[str, ...]
    filesystem_rules: tuple[tuple[str, str], ...]
    forbidden_host_surfaces: tuple[str, ...]
    writable_host_binds: tuple[tuple[str, str], ...]
    privileged_mode: bool
    host_uid_zero_mapping: bool
    capability_policy: str
    syscall_policy: str
    privilege_escalation_policy: str
    network_policy: str
    integration_surfaces: tuple[str, ...]
    direct_devices: tuple[str, ...]
    local_administration: str
    linger: bool
    resource_limits: tuple[tuple[str, str], ...]
    teardown_requirements: tuple[str, ...]


@dataclass(frozen=True)
class PolicyAssessment:
    classification: str
    issues: tuple[str, ...]
    digest: str


def _normal_policy() -> EnvironmentIsolationPolicy:
    return EnvironmentIsolationPolicy(
        schema_version=POLICY_SCHEMA_VERSION,
        policy_version=POLICY_VERSION,
        profile="normal-desktop",
        security_claim="shared-kernel-containment-not-vm-equivalent",
        namespaces=REQUIRED_NAMESPACES,
        filesystem_rules=FILESYSTEM_RULES,
        forbidden_host_surfaces=FORBIDDEN_HOST_SURFACES,
        writable_host_binds=(),
        privileged_mode=False,
        host_uid_zero_mapping=False,
        capability_policy="fixed-reduced-normal-v1",
        syscall_policy="fixed-normal-v1",
        privilege_escalation_policy="denied-except-reviewed-environment-local-admin",
        network_policy="private-namespace-host-mediated-outbound",
        integration_surfaces=(
            "audio-mediated",
            "display-mediated",
            "notifications-mediated",
            "portal-mediated",
        ),
        direct_devices=(),
        local_administration="owner-confirmed-environment-local-only",
        linger=False,
        resource_limits=NORMAL_LIMITS,
        teardown_requirements=TEARDOWN_REQUIREMENTS,
    )


def _high_security_policy() -> EnvironmentIsolationPolicy:
    return EnvironmentIsolationPolicy(
        schema_version=POLICY_SCHEMA_VERSION,
        policy_version=POLICY_VERSION,
        profile="high-security-headless",
        security_claim="shared-kernel-restricted-profile-not-vm-equivalent",
        namespaces=REQUIRED_NAMESPACES,
        filesystem_rules=FILESYSTEM_RULES,
        forbidden_host_surfaces=FORBIDDEN_HOST_SURFACES,
        writable_host_binds=(),
        privileged_mode=False,
        host_uid_zero_mapping=False,
        capability_policy="fixed-minimal-high-security-v1",
        syscall_policy="fixed-high-security-v1",
        privilege_escalation_policy="denied",
        network_policy="denied",
        integration_surfaces=(),
        direct_devices=(),
        local_administration="disabled",
        linger=False,
        resource_limits=HIGH_SECURITY_LIMITS,
        teardown_requirements=TEARDOWN_REQUIREMENTS,
    )


FIXED_POLICIES = {
    "normal-desktop": _normal_policy(),
    "high-security-headless": _high_security_policy(),
}


def build_fixed_policy(profile: str) -> EnvironmentIsolationPolicy:
    """Return one internal policy; callers cannot supply individual controls."""

    try:
        return FIXED_POLICIES[profile]
    except KeyError as error:
        raise ValueError("unsupported APX isolation profile") from error


def canonical_policy_json(policy: EnvironmentIsolationPolicy) -> str:
    return json.dumps(asdict(policy), sort_keys=True, separators=(",", ":"))


def compute_policy_digest(policy: EnvironmentIsolationPolicy) -> str:
    return hashlib.sha256(canonical_policy_json(policy).encode("utf-8")).hexdigest()


def assess_environment_policy(policy: EnvironmentIsolationPolicy) -> PolicyAssessment:
    """Fail closed unless the policy exactly matches an internal reviewed policy."""

    issues: list[str] = []

    expected = FIXED_POLICIES.get(policy.profile)
    if policy.schema_version != POLICY_SCHEMA_VERSION:
        issues.append("unsupported schema version")
    if policy.policy_version != POLICY_VERSION:
        issues.append("unsupported policy version")
    if expected is None:
        issues.append("unknown profile")
    elif policy != expected:
        issues.append("policy differs from the fixed reviewed profile")

    if policy.security_claim == "vm-equivalent":
        issues.append("shared-kernel policy cannot claim VM equivalence")
    if tuple(sorted(set(policy.namespaces))) != REQUIRED_NAMESPACES:
        issues.append("required namespace boundary is incomplete or non-canonical")
    if policy.filesystem_rules != FILESYSTEM_RULES:
        issues.append("filesystem boundary differs from the fixed denial policy")
    if policy.forbidden_host_surfaces != FORBIDDEN_HOST_SURFACES:
        issues.append("host or cross-Environment denial set differs from policy")
    if policy.writable_host_binds:
        issues.append("writable host binds are forbidden")
    if policy.privileged_mode:
        issues.append("privileged runtime mode is forbidden")
    if policy.host_uid_zero_mapping:
        issues.append("Environment root cannot map to host UID zero")
    if policy.direct_devices:
        issues.append("direct devices require a separate reviewed profile")
    if policy.linger:
        issues.append("Environment processes cannot linger after stop")
    if policy.teardown_requirements != TEARDOWN_REQUIREMENTS:
        issues.append("complete teardown verification is required")

    return PolicyAssessment(
        classification="accepted-contract" if not issues else "rejected",
        issues=tuple(dict.fromkeys(issues)),
        digest=compute_policy_digest(policy),
    )


def render_policy_summary(policy: EnvironmentIsolationPolicy) -> str:
    assessment = assess_environment_policy(policy)
    internet = "controlled outbound access" if policy.network_policy != "denied" else "no network"
    admin = (
        "local administration requires owner confirmation"
        if policy.local_administration.startswith("owner-confirmed")
        else "local administration is disabled"
    )
    integrations = ", ".join(policy.integration_surfaces) or "none"
    return "\n".join(
        (
            f"Profile: {policy.profile}",
            f"Contract: {assessment.classification}",
            "Isolation: host, Hub, base writable state, and sibling Environments are inaccessible",
            f"Network: {internet}",
            f"Local administrator: {admin}",
            f"Controlled integrations: {integrations}",
            "Security limit: one Linux kernel is shared; this is not VM-equivalent isolation",
            f"Policy digest: {assessment.digest}",
        )
    )
