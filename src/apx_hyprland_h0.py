"""Pure readiness and preview contract for the clean-host Hyprland H0 gate.

The module consumes supplied evidence and performs no session, VT, device,
runtime, compositor, service, package, or host operation.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import re


SCHEMA_VERSION = 1
PROFILE = "apx-hyprland-h0-clean-host-v1"
MAX_JSON_BYTES = 64 * 1024
AMD_PCI = "0000:05:00.0"
NVIDIA_PCI = "0000:01:00.0"
INPUT_KINDS = ("built-in-keyboard", "built-in-touchpad")
MAX_RUNTIME_SECONDS = 300
H0_EFFECTS = (
    "reverify-clean-host-and-independent-recovery-vt",
    "stop-headless-hub-and-development-cleanly",
    "reserve-one-generation-bound-graphical-lease",
    "grant-only-exact-amd-kms-and-render-devices",
    "grant-only-mediated-built-in-keyboard-and-touchpad",
    "start-disposable-hyprland-environment-on-experiment-vt",
    "verify-wayland-output-input-and-apx-return-control",
    "enforce-watchdog-and-recovery-vt-availability",
    "stop-hyprland-environment-and-revoke-every-device",
    "verify-zero-residue-and-restore-headless-hub-path",
)

_HEX_32 = re.compile(r"[0-9a-f]{32}")
_HEX_64 = re.compile(r"[0-9a-f]{64}")
_UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}")


class H0Error(ValueError):
    """H0 evidence or preview is malformed or outside the fixed experiment."""


@dataclass(frozen=True)
class H0Evidence:
    schema_version: int
    profile: str
    experiment_id: str
    physical_audit_digest: str
    physical_audit_reconciled: bool
    machine_identity_digest: str
    physical_marker_digest: str
    no_display_manager_installed: bool
    no_display_manager_enabled: bool
    no_display_manager_active: bool
    no_graphical_session_owner: bool
    no_stale_graphical_lease: bool
    recovery_vt_identity_digest: str
    recovery_vt_verified: bool
    recovery_vt_independent: bool
    headless_hub_healthy: bool
    development_healthy: bool
    no_uncertain_apx_operation: bool
    amd_pci: str
    amd_driver: str
    amd_gpu_identity_digest: str
    amd_kms_identity_digest: str
    amd_render_identity_digest: str
    amd_connector_identity_digest: str
    nvidia_pci: str
    nvidia_excluded: bool
    input_kinds: tuple[str, ...]
    input_identity_digests: tuple[str, ...]
    input_mediation_verified: bool
    broad_input_access_absent: bool
    audio_access_absent: bool
    camera_access_absent: bool
    microphone_access_absent: bool
    host_filesystem_access_absent: bool
    executor_access_absent: bool
    graphical_release_digest: str
    graphical_package_evidence_digest: str
    hyprland_config_digest: str
    apx_return_control_digest: str
    disposable_environment_generation: str
    timeout_seconds: int
    watchdog_verified: bool
    teardown_observer_digest: str


@dataclass(frozen=True)
class H0Preview:
    schema_version: int
    profile: str
    classification: str
    blockers: tuple[str, ...]
    experiment_id: str
    environment_generation: str
    amd_pci: str
    input_kinds: tuple[str, ...]
    timeout_seconds: int
    effects: tuple[str, ...]
    evidence_digest: str
    consequence_digest: str
    plan_digest: str
    separate_physical_approval_required: bool
    cleanup_not_authorized: bool


def _reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise H0Error("H0 JSON has duplicate fields")
        value[key] = item
    return value


def parse_h0_evidence_json(text: str) -> H0Evidence:
    if not isinstance(text, str) or not text:
        raise H0Error("H0 JSON is empty or oversized")
    try:
        encoded = text.encode("utf-8")
    except UnicodeEncodeError as error:
        raise H0Error("H0 JSON is not valid UTF-8") from error
    if len(encoded) > MAX_JSON_BYTES:
        raise H0Error("H0 JSON is empty or oversized")
    try:
        value = json.loads(text, object_pairs_hook=_reject_duplicates)
    except json.JSONDecodeError as error:
        raise H0Error("H0 JSON is invalid") from error
    if not isinstance(value, dict) or set(value) != frozenset(H0Evidence.__dataclass_fields__):
        raise H0Error("H0 fields do not match schema")
    for field in ("input_kinds", "input_identity_digests"):
        if isinstance(value.get(field), list):
            value[field] = tuple(value[field])
    try:
        evidence = H0Evidence(**value)
    except TypeError as error:
        raise H0Error("H0 values are malformed") from error
    validate_h0_evidence(evidence)
    return evidence


def _digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _sha(value: object, label: str) -> None:
    if not isinstance(value, str) or not _HEX_64.fullmatch(value):
        raise H0Error(f"{label} is not a canonical SHA-256")


def validate_h0_evidence(evidence: H0Evidence) -> None:
    if type(evidence) is not H0Evidence:
        raise H0Error("H0 evidence object type is invalid")
    if type(evidence.schema_version) is not int or evidence.schema_version != SCHEMA_VERSION:
        raise H0Error("H0 schema is invalid")
    if evidence.profile != PROFILE:
        raise H0Error("H0 profile is invalid")
    if not isinstance(evidence.experiment_id, str) or not evidence.experiment_id.startswith("h0-") or not _HEX_32.fullmatch(evidence.experiment_id[3:]):
        raise H0Error("H0 experiment identity is invalid")
    digest_fields = (
        "physical_audit_digest", "machine_identity_digest", "physical_marker_digest",
        "recovery_vt_identity_digest", "amd_gpu_identity_digest",
        "amd_kms_identity_digest", "amd_render_identity_digest",
        "amd_connector_identity_digest", "graphical_release_digest",
        "graphical_package_evidence_digest", "hyprland_config_digest",
        "apx_return_control_digest", "teardown_observer_digest",
    )
    for field in digest_fields:
        _sha(getattr(evidence, field), field)
    if evidence.amd_pci != AMD_PCI or evidence.amd_driver != "amdgpu":
        raise H0Error("H0 AMD identity is outside the target-bound profile")
    if evidence.nvidia_pci != NVIDIA_PCI:
        raise H0Error("H0 NVIDIA identity is outside the target-bound profile")
    if evidence.input_kinds != INPUT_KINDS:
        raise H0Error("H0 input kinds are not the exact built-in set")
    if type(evidence.input_identity_digests) is not tuple or len(evidence.input_identity_digests) != len(INPUT_KINDS):
        raise H0Error("H0 input identity count is invalid")
    for digest in evidence.input_identity_digests:
        _sha(digest, "input identity")
    if len(set(evidence.input_identity_digests)) != len(evidence.input_identity_digests):
        raise H0Error("H0 input identities are not distinct")
    if not isinstance(evidence.disposable_environment_generation, str) or not _UUID.fullmatch(evidence.disposable_environment_generation):
        raise H0Error("H0 Environment generation is invalid")
    boolean_fields = (
        "physical_audit_reconciled", "no_display_manager_installed",
        "no_display_manager_enabled", "no_display_manager_active",
        "no_graphical_session_owner", "no_stale_graphical_lease",
        "recovery_vt_verified", "recovery_vt_independent", "headless_hub_healthy",
        "development_healthy", "no_uncertain_apx_operation", "nvidia_excluded",
        "input_mediation_verified", "broad_input_access_absent", "audio_access_absent",
        "camera_access_absent", "microphone_access_absent",
        "host_filesystem_access_absent", "executor_access_absent",
        "watchdog_verified",
    )
    for field in boolean_fields:
        if type(getattr(evidence, field)) is not bool:
            raise H0Error(f"{field} must be boolean evidence")
    if type(evidence.timeout_seconds) is not int or not 30 <= evidence.timeout_seconds <= MAX_RUNTIME_SECONDS:
        raise H0Error("H0 timeout is outside the fixed bound")


def build_h0_preview(evidence: H0Evidence) -> H0Preview:
    validate_h0_evidence(evidence)
    gates = {
        "physical-audit-not-reconciled": evidence.physical_audit_reconciled,
        "display-manager-installed": evidence.no_display_manager_installed,
        "display-manager-enabled": evidence.no_display_manager_enabled,
        "display-manager-active": evidence.no_display_manager_active,
        "graphical-session-owner-present": evidence.no_graphical_session_owner,
        "stale-graphical-lease-present": evidence.no_stale_graphical_lease,
        "recovery-vt-not-verified": evidence.recovery_vt_verified,
        "recovery-vt-not-independent": evidence.recovery_vt_independent,
        "headless-hub-unhealthy": evidence.headless_hub_healthy,
        "development-unhealthy": evidence.development_healthy,
        "uncertain-apx-operation-present": evidence.no_uncertain_apx_operation,
        "nvidia-not-excluded": evidence.nvidia_excluded,
        "input-mediation-not-verified": evidence.input_mediation_verified,
        "broad-input-access-present": evidence.broad_input_access_absent,
        "audio-access-present": evidence.audio_access_absent,
        "camera-access-present": evidence.camera_access_absent,
        "microphone-access-present": evidence.microphone_access_absent,
        "host-filesystem-access-present": evidence.host_filesystem_access_absent,
        "executor-access-present": evidence.executor_access_absent,
        "watchdog-not-verified": evidence.watchdog_verified,
    }
    blockers = tuple(label for label, passed in gates.items() if not passed)
    evidence_digest = _digest(asdict(evidence))
    consequences = (
        "headless-hub-and-development-stop-for-the-experiment",
        "physical-display-and-built-in-input-temporarily-belong-to-one-environment",
        "nvidia-audio-camera-microphone-and-broad-input-remain-unavailable",
        "failure-returns-to-independent-text-recovery",
        "cleanup-requires-separate-evidence-and-approval",
    )
    consequence_digest = _digest(consequences)
    plan = {
        "profile": PROFILE,
        "experiment_id": evidence.experiment_id,
        "environment_generation": evidence.disposable_environment_generation,
        "amd_pci": evidence.amd_pci,
        "input_kinds": evidence.input_kinds,
        "timeout_seconds": evidence.timeout_seconds,
        "effects": H0_EFFECTS,
        "evidence_digest": evidence_digest,
        "consequence_digest": consequence_digest,
        "authority": "none-preview-only",
    }
    return H0Preview(
        SCHEMA_VERSION,
        PROFILE,
        "ready-for-separate-physical-approval" if not blockers else "blocked",
        blockers,
        evidence.experiment_id,
        evidence.disposable_environment_generation,
        evidence.amd_pci,
        evidence.input_kinds,
        evidence.timeout_seconds,
        H0_EFFECTS,
        evidence_digest,
        consequence_digest,
        _digest(plan),
        True,
        True,
    )
