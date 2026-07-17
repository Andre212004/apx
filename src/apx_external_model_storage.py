"""Pure readiness contract for a future external Development model store."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import re


SCHEMA_VERSION = 1
PROFILE = "development-external-model-store-v1"
MAX_SERIALIZED_BYTES = 32 * 1024
MINIMUM_DEVICE_BYTES = 64 * 1024**3
MINIMUM_HOST_RESERVE_BYTES = 32 * 1024**3
MINIMUM_STORE_RESERVE_BYTES = 16 * 1024**3

_HEX_32 = re.compile(r"[0-9a-f]{32}")
_HEX_64 = re.compile(r"[0-9a-f]{64}")
_UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
_GENERATION = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}")


class ExternalModelStorageError(ValueError):
    """Evidence is malformed or outside the closed v1 profile."""


@dataclass(frozen=True)
class AttachmentEvidence:
    schema_version: int
    profile: str
    attachment_id: str
    development_name: str
    development_generation: str
    development_stopped: bool
    device_identity_digest: str
    stable_by_id_digest: str
    device_size_bytes: int
    device_is_not_internal_apx_disk: bool
    device_is_not_backup_disk: bool
    luks_uuid: str
    luks2_verified: bool
    recovery_unlock_tested: bool
    filesystem_uuid: str
    filesystem_type: str
    filesystem_healthy: bool
    attachment_detached: bool
    host_private_mount_absent: bool
    hub_visibility_absent: bool
    other_environment_visibility_absent: bool
    service_identity_verified: bool
    ownership_mapping_verified: bool
    host_free_bytes: int
    store_free_bytes: int
    store_limit_bytes: int
    expected_model_bytes: int
    model_manifest_digest: str
    partial_download_absent: bool
    disconnect_fixture_passed: bool
    recovery_plan_digest: str


@dataclass(frozen=True)
class AttachmentReadiness:
    schema_version: int
    profile: str
    classification: str
    blockers: tuple[str, ...]
    attachment_id: str
    development_generation: str
    evidence_digest: str
    no_effect_plan_digest: str
    separate_destructive_dossier_required: bool


def _reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ExternalModelStorageError("evidence JSON has duplicate fields")
        result[key] = value
    return result


def parse_attachment_evidence_json(text: str) -> AttachmentEvidence:
    if not isinstance(text, str) or not text:
        raise ExternalModelStorageError("evidence JSON is empty or oversized")
    try:
        encoded = text.encode("utf-8")
    except UnicodeEncodeError as error:
        raise ExternalModelStorageError("evidence JSON is not valid UTF-8") from error
    if len(encoded) > MAX_SERIALIZED_BYTES:
        raise ExternalModelStorageError("evidence JSON is empty or oversized")
    try:
        value = json.loads(text, object_pairs_hook=_reject_duplicates)
    except json.JSONDecodeError as error:
        raise ExternalModelStorageError("evidence JSON is invalid") from error
    expected = frozenset(AttachmentEvidence.__dataclass_fields__)
    if not isinstance(value, dict) or set(value) != expected:
        raise ExternalModelStorageError("evidence fields do not match schema")
    try:
        evidence = AttachmentEvidence(**value)
    except TypeError as error:
        raise ExternalModelStorageError("evidence values are malformed") from error
    _validate(evidence)
    return evidence


def _digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _canonical_digest(value: object, label: str) -> None:
    if not isinstance(value, str) or not _HEX_64.fullmatch(value):
        raise ExternalModelStorageError(f"{label} is not a canonical SHA-256")


def _validate(evidence: AttachmentEvidence) -> None:
    if type(evidence) is not AttachmentEvidence:
        raise ExternalModelStorageError("evidence object type is invalid")
    if type(evidence.schema_version) is not int or evidence.schema_version != SCHEMA_VERSION:
        raise ExternalModelStorageError("schema version is invalid")
    if evidence.profile != PROFILE:
        raise ExternalModelStorageError("profile is invalid")
    if not isinstance(evidence.attachment_id, str) or not evidence.attachment_id.startswith("attachment-") or not _HEX_32.fullmatch(evidence.attachment_id[11:]):
        raise ExternalModelStorageError("attachment identity is invalid")
    if evidence.development_name != "development":
        raise ExternalModelStorageError("attachment is not bound to Development")
    if not isinstance(evidence.development_generation, str) or not _GENERATION.fullmatch(evidence.development_generation):
        raise ExternalModelStorageError("Development generation is invalid")
    for field in (
        "device_identity_digest", "stable_by_id_digest", "model_manifest_digest",
        "recovery_plan_digest",
    ):
        _canonical_digest(getattr(evidence, field), field)
    for field in ("luks_uuid", "filesystem_uuid"):
        value = getattr(evidence, field)
        if not isinstance(value, str) or not _UUID.fullmatch(value):
            raise ExternalModelStorageError(f"{field} is invalid")
    if evidence.luks_uuid == evidence.filesystem_uuid:
        raise ExternalModelStorageError("LUKS and filesystem identities must differ")
    if evidence.filesystem_type != "btrfs":
        raise ExternalModelStorageError("filesystem type is outside the v1 profile")
    boolean_fields = (
        "development_stopped", "device_is_not_internal_apx_disk",
        "device_is_not_backup_disk", "luks2_verified", "recovery_unlock_tested",
        "filesystem_healthy", "attachment_detached", "host_private_mount_absent",
        "hub_visibility_absent", "other_environment_visibility_absent",
        "service_identity_verified", "ownership_mapping_verified",
        "partial_download_absent", "disconnect_fixture_passed",
    )
    for field in boolean_fields:
        if type(getattr(evidence, field)) is not bool:
            raise ExternalModelStorageError(f"{field} must be boolean evidence")
    number_fields = (
        "device_size_bytes", "host_free_bytes", "store_free_bytes",
        "store_limit_bytes", "expected_model_bytes",
    )
    for field in number_fields:
        value = getattr(evidence, field)
        if type(value) is not int or value < 0:
            raise ExternalModelStorageError(f"{field} is invalid")
    if evidence.store_free_bytes > evidence.device_size_bytes or evidence.store_limit_bytes > evidence.device_size_bytes:
        raise ExternalModelStorageError("store capacity exceeds the physical device")
    if evidence.expected_model_bytes > evidence.store_limit_bytes:
        raise ExternalModelStorageError("model size exceeds the store limit")


def assess_attachment(evidence: AttachmentEvidence) -> AttachmentReadiness:
    _validate(evidence)
    blockers: list[str] = []
    boolean_gates = {
        "development-must-be-stopped": evidence.development_stopped,
        "device-matches-internal-apx-disk": evidence.device_is_not_internal_apx_disk,
        "device-matches-a-backup-disk": evidence.device_is_not_backup_disk,
        "luks2-not-verified": evidence.luks2_verified,
        "recovery-unlock-not-tested": evidence.recovery_unlock_tested,
        "filesystem-unhealthy": evidence.filesystem_healthy,
        "attachment-is-not-detached": evidence.attachment_detached,
        "host-private-mount-still-present": evidence.host_private_mount_absent,
        "hub-can-see-model-store": evidence.hub_visibility_absent,
        "another-environment-can-see-model-store": evidence.other_environment_visibility_absent,
        "service-identity-unverified": evidence.service_identity_verified,
        "ownership-mapping-unverified": evidence.ownership_mapping_verified,
        "partial-download-present": evidence.partial_download_absent,
        "disconnect-fixture-not-passed": evidence.disconnect_fixture_passed,
    }
    blockers.extend(label for label, passed in boolean_gates.items() if not passed)
    if evidence.device_size_bytes < MINIMUM_DEVICE_BYTES:
        blockers.append("external-device-smaller-than-64-gib")
    if evidence.host_free_bytes < MINIMUM_HOST_RESERVE_BYTES:
        blockers.append("internal-host-reserve-below-32-gib")
    if evidence.store_free_bytes - evidence.expected_model_bytes < MINIMUM_STORE_RESERVE_BYTES:
        blockers.append("external-store-reserve-below-16-gib-after-model")
    evidence_digest = _digest(asdict(evidence))
    plan = {
        "profile": PROFILE,
        "attachment_id": evidence.attachment_id,
        "development_generation": evidence.development_generation,
        "device_identity_digest": evidence.device_identity_digest,
        "luks_uuid": evidence.luks_uuid,
        "filesystem_uuid": evidence.filesystem_uuid,
        "store_limit_bytes": evidence.store_limit_bytes,
        "model_manifest_digest": evidence.model_manifest_digest,
        "effect": "none-readiness-only",
    }
    return AttachmentReadiness(
        SCHEMA_VERSION,
        PROFILE,
        "ready-for-separate-design-review" if not blockers else "blocked",
        tuple(blockers),
        evidence.attachment_id,
        evidence.development_generation,
        evidence_digest,
        _digest(plan),
        True,
    )
