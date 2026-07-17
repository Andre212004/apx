"""Pure candidate and preview contract for physical-pilot updates.

This module accepts supplied metadata only. It cannot fetch, copy, install,
restart, replace, roll back, or otherwise change the physical pilot.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import re


SCHEMA_VERSION = 1
PROFILE = "apx-physical-headless-pilot-update-v1"
MAX_JSON_BYTES = 64 * 1024
MAX_ARTIFACT_BYTES = 256 * 1024**2
MAX_MEMBERS = 4096
MINIMUM_HOST_RESERVE_BYTES = 16 * 1024**3
ALLOWED_COMPONENTS = (
    "hub-client",
    "host-executor",
    "host-runtime",
)
UPDATE_EFFECTS = (
    "reserve-private-update-staging",
    "copy-bounded-untrusted-artifact",
    "verify-artifact-members-and-provenance",
    "verify-installed-identity-and-recovery",
    "stop-development-and-hub-cleanly",
    "retain-current-installed-rollback-set",
    "install-exact-reviewed-component-set",
    "verify-host-hub-development-and-separation",
    "publish-new-installed-update-identity",
    "retain-rollback-until-separate-retirement",
)

_HEX_32 = re.compile(r"[0-9a-f]{32}")
_HEX_40_OR_64 = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})")
_HEX_64 = re.compile(r"[0-9a-f]{64}")
_UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}")


class PhysicalUpdateError(ValueError):
    """Candidate, evidence, or preview is malformed or outside policy."""


@dataclass(frozen=True)
class PhysicalUpdateCandidate:
    schema_version: int
    profile: str
    update_id: str
    source_revision: str
    parent_revision: str
    artifact_sha256: str
    artifact_bytes: int
    member_manifest_digest: str
    member_count: int
    components: tuple[str, ...]
    tests_digest: str
    tests_passed: int
    tests_skipped: int
    compatibility_digest: str
    rollback_manifest_digest: str
    documentation_digest: str
    credentials_absent: bool
    private_keys_absent: bool
    arbitrary_commands_absent: bool
    package_hooks_absent: bool
    candidate_is_untrusted: bool


@dataclass(frozen=True)
class InstalledPilotEvidence:
    schema_version: int
    profile: str
    machine_identity_digest: str
    physical_marker_digest: str
    installed_source_revision: str
    installed_runtime_sha256: str
    installed_client_sha256: str
    installed_executor_sha256: str
    hub_release: str
    hub_generation: str
    development_generation: str
    audit_evidence_digest: str
    audit_reconciled: bool
    recovery_console_verified: bool
    github_source_recovery_verified: bool
    no_uncertain_apx_operation: bool
    hub_clean: bool
    development_repository_healthy: bool
    host_free_bytes: int


@dataclass(frozen=True)
class PhysicalUpdatePreview:
    schema_version: int
    profile: str
    classification: str
    blockers: tuple[str, ...]
    update_id: str
    installed_source_revision: str
    next_source_revision: str
    components: tuple[str, ...]
    effects: tuple[str, ...]
    candidate_digest: str
    installed_evidence_digest: str
    consequence_digest: str
    plan_digest: str
    separate_import_approval_required: bool
    separate_activation_approval_required: bool
    rollback_retirement_requires_later_approval: bool


def _reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise PhysicalUpdateError("JSON has duplicate fields")
        value[key] = item
    return value


def _parse(text: str, expected: frozenset[str], label: str) -> dict[str, object]:
    if not isinstance(text, str) or not text:
        raise PhysicalUpdateError(f"{label} JSON is empty or oversized")
    try:
        encoded = text.encode("utf-8")
    except UnicodeEncodeError as error:
        raise PhysicalUpdateError(f"{label} JSON is not valid UTF-8") from error
    if len(encoded) > MAX_JSON_BYTES:
        raise PhysicalUpdateError(f"{label} JSON is empty or oversized")
    try:
        value = json.loads(text, object_pairs_hook=_reject_duplicates)
    except json.JSONDecodeError as error:
        raise PhysicalUpdateError(f"{label} JSON is invalid") from error
    if not isinstance(value, dict) or set(value) != expected:
        raise PhysicalUpdateError(f"{label} fields do not match schema")
    return value


def parse_candidate_json(text: str) -> PhysicalUpdateCandidate:
    value = _parse(text, frozenset(PhysicalUpdateCandidate.__dataclass_fields__), "candidate")
    if isinstance(value.get("components"), list):
        value["components"] = tuple(value["components"])
    try:
        candidate = PhysicalUpdateCandidate(**value)
    except TypeError as error:
        raise PhysicalUpdateError("candidate values are malformed") from error
    validate_candidate(candidate)
    return candidate


def parse_installed_evidence_json(text: str) -> InstalledPilotEvidence:
    value = _parse(text, frozenset(InstalledPilotEvidence.__dataclass_fields__), "installed evidence")
    try:
        evidence = InstalledPilotEvidence(**value)
    except TypeError as error:
        raise PhysicalUpdateError("installed evidence values are malformed") from error
    validate_installed_evidence(evidence)
    return evidence


def _digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _sha(value: object, label: str) -> None:
    if not isinstance(value, str) or not _HEX_64.fullmatch(value):
        raise PhysicalUpdateError(f"{label} is not a canonical SHA-256")


def validate_candidate(candidate: PhysicalUpdateCandidate) -> None:
    if type(candidate) is not PhysicalUpdateCandidate:
        raise PhysicalUpdateError("candidate object type is invalid")
    if type(candidate.schema_version) is not int or candidate.schema_version != SCHEMA_VERSION:
        raise PhysicalUpdateError("candidate schema is invalid")
    if candidate.profile != PROFILE:
        raise PhysicalUpdateError("candidate profile is invalid")
    if not isinstance(candidate.update_id, str) or not candidate.update_id.startswith("update-") or not _HEX_32.fullmatch(candidate.update_id[7:]):
        raise PhysicalUpdateError("update identity is invalid")
    for field in ("source_revision", "parent_revision"):
        value = getattr(candidate, field)
        if not isinstance(value, str) or not _HEX_40_OR_64.fullmatch(value):
            raise PhysicalUpdateError(f"{field} is invalid")
    if candidate.source_revision == candidate.parent_revision:
        raise PhysicalUpdateError("update source and parent revisions are identical")
    for field in (
        "artifact_sha256", "member_manifest_digest", "tests_digest",
        "compatibility_digest", "rollback_manifest_digest", "documentation_digest",
    ):
        _sha(getattr(candidate, field), field)
    if type(candidate.artifact_bytes) is not int or not 0 < candidate.artifact_bytes <= MAX_ARTIFACT_BYTES:
        raise PhysicalUpdateError("artifact byte count is invalid")
    if type(candidate.member_count) is not int or not 0 < candidate.member_count <= MAX_MEMBERS:
        raise PhysicalUpdateError("artifact member count is invalid")
    if (
        type(candidate.components) is not tuple
        or not candidate.components
        or tuple(sorted(set(candidate.components))) != candidate.components
        or any(component not in ALLOWED_COMPONENTS for component in candidate.components)
    ):
        raise PhysicalUpdateError("component set is invalid")
    if type(candidate.tests_passed) is not int or candidate.tests_passed <= 0:
        raise PhysicalUpdateError("passing test count is invalid")
    if type(candidate.tests_skipped) is not int or candidate.tests_skipped < 0:
        raise PhysicalUpdateError("skipped test count is invalid")
    for field in (
        "credentials_absent", "private_keys_absent", "arbitrary_commands_absent",
        "package_hooks_absent", "candidate_is_untrusted",
    ):
        if getattr(candidate, field) is not True:
            raise PhysicalUpdateError(f"{field} must be explicitly true")


def validate_installed_evidence(evidence: InstalledPilotEvidence) -> None:
    if type(evidence) is not InstalledPilotEvidence:
        raise PhysicalUpdateError("installed evidence object type is invalid")
    if type(evidence.schema_version) is not int or evidence.schema_version != SCHEMA_VERSION:
        raise PhysicalUpdateError("installed evidence schema is invalid")
    if evidence.profile != PROFILE:
        raise PhysicalUpdateError("installed evidence profile is invalid")
    for field in (
        "machine_identity_digest", "physical_marker_digest", "installed_runtime_sha256",
        "installed_client_sha256", "installed_executor_sha256", "audit_evidence_digest",
    ):
        _sha(getattr(evidence, field), field)
    if not isinstance(evidence.installed_source_revision, str) or not _HEX_40_OR_64.fullmatch(evidence.installed_source_revision):
        raise PhysicalUpdateError("installed source revision is invalid")
    if evidence.hub_release not in {"hub-headless-v3"}:
        raise PhysicalUpdateError("installed Hub release is outside the physical pilot profile")
    for field in ("hub_generation", "development_generation"):
        value = getattr(evidence, field)
        if not isinstance(value, str) or not _UUID.fullmatch(value):
            raise PhysicalUpdateError(f"{field} is invalid")
    boolean_fields = (
        "audit_reconciled", "recovery_console_verified", "github_source_recovery_verified",
        "no_uncertain_apx_operation", "hub_clean", "development_repository_healthy",
    )
    for field in boolean_fields:
        if type(getattr(evidence, field)) is not bool:
            raise PhysicalUpdateError(f"{field} must be boolean evidence")
    if type(evidence.host_free_bytes) is not int or evidence.host_free_bytes < 0:
        raise PhysicalUpdateError("host free byte count is invalid")


def build_update_preview(
    candidate: PhysicalUpdateCandidate,
    installed: InstalledPilotEvidence,
) -> PhysicalUpdatePreview:
    validate_candidate(candidate)
    validate_installed_evidence(installed)
    blockers: list[str] = []
    if candidate.parent_revision != installed.installed_source_revision:
        blockers.append("candidate-parent-does-not-match-installed-revision")
    gates = {
        "physical-audit-not-reconciled": installed.audit_reconciled,
        "recovery-console-not-verified": installed.recovery_console_verified,
        "github-source-recovery-not-verified": installed.github_source_recovery_verified,
        "uncertain-apx-operation-present": installed.no_uncertain_apx_operation,
        "hub-is-not-clean": installed.hub_clean,
        "development-repository-is-not-healthy": installed.development_repository_healthy,
    }
    blockers.extend(label for label, passed in gates.items() if not passed)
    if installed.host_free_bytes < MINIMUM_HOST_RESERVE_BYTES:
        blockers.append("host-reserve-below-16-gib")
    candidate_digest = _digest(asdict(candidate))
    installed_digest = _digest(asdict(installed))
    consequences = (
        "hub-and-development-will-stop-during-activation",
        "host-owned-apx-components-will-change",
        "current-components-remain-a-bounded-rollback-set",
        "rollback-retirement-is-a-later-separate-decision",
        "uncertain-state-blocks-activation-and-preserves-data",
    )
    consequence_digest = _digest(consequences)
    plan = {
        "profile": PROFILE,
        "update_id": candidate.update_id,
        "installed_source_revision": installed.installed_source_revision,
        "next_source_revision": candidate.source_revision,
        "components": candidate.components,
        "effects": UPDATE_EFFECTS,
        "candidate_digest": candidate_digest,
        "installed_evidence_digest": installed_digest,
        "consequence_digest": consequence_digest,
        "authority": "none-preview-only",
    }
    return PhysicalUpdatePreview(
        SCHEMA_VERSION,
        PROFILE,
        "ready-for-separate-import-approval" if not blockers else "blocked",
        tuple(blockers),
        candidate.update_id,
        installed.installed_source_revision,
        candidate.source_revision,
        candidate.components,
        UPDATE_EFFECTS,
        candidate_digest,
        installed_digest,
        consequence_digest,
        _digest(plan),
        True,
        True,
        True,
    )
