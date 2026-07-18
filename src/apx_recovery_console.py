"""Pure evidence contract for a physical APX recovery-console rehearsal."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import datetime as dt
import hashlib
import json
import re


SCHEMA_VERSION = 1
PROFILE = "apx-physical-recovery-console-v1"
MAX_JSON_BYTES = 64 * 1024
_SHA256 = re.compile(r"[0-9a-f]{64}")
_BOOT_ID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}")


class RecoveryConsoleError(ValueError):
    """Recovery evidence is malformed, ambiguous, or outside policy."""


@dataclass(frozen=True)
class RecoveryConsoleEvidence:
    schema_version: int
    profile: str
    receipt_id: str
    machine_identity_digest: str
    physical_marker_digest: str
    boot_entry_digest: str
    kernel_digest: str
    initramfs_digest: str
    before_boot_id: str
    recovery_boot_id: str
    observed_at: str
    observer_kind: str
    physical_presence_confirmed: bool
    built_in_keyboard_confirmed: bool
    encrypted_root_unlock_confirmed: bool
    root_console_confirmed: bool
    apx_status_reconciled_after_boot: bool
    hub_generation_unchanged: bool
    development_generation_unchanged: bool
    disposable_hold_unchanged: bool
    no_uncertain_apx_operation: bool
    no_disk_layout_change: bool
    no_encryption_change: bool
    no_bootloader_change: bool
    no_package_change: bool
    no_apx_lifecycle_effect: bool
    secrets_absent_from_receipt: bool


@dataclass(frozen=True)
class RecoveryConsoleAssessment:
    classification: str
    blockers: tuple[str, ...]
    evidence_digest: str
    update_gate_satisfied: bool


def _duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise RecoveryConsoleError("recovery JSON has duplicate fields")
        result[key] = value
    return result


def parse_recovery_evidence_json(text: str) -> RecoveryConsoleEvidence:
    if not isinstance(text, str) or not text:
        raise RecoveryConsoleError("recovery JSON is empty or oversized")
    try:
        encoded = text.encode("utf-8")
    except UnicodeEncodeError as error:
        raise RecoveryConsoleError("recovery JSON is not UTF-8") from error
    if len(encoded) > MAX_JSON_BYTES:
        raise RecoveryConsoleError("recovery JSON is empty or oversized")
    try:
        raw = json.loads(text, object_pairs_hook=_duplicates)
    except json.JSONDecodeError as error:
        raise RecoveryConsoleError("recovery JSON is invalid") from error
    if not isinstance(raw, dict) or set(raw) != frozenset(RecoveryConsoleEvidence.__dataclass_fields__):
        raise RecoveryConsoleError("recovery fields do not match schema")
    try:
        evidence = RecoveryConsoleEvidence(**raw)
    except TypeError as error:
        raise RecoveryConsoleError("recovery values are malformed") from error
    validate_recovery_evidence(evidence)
    return evidence


def _digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def validate_recovery_evidence(evidence: RecoveryConsoleEvidence) -> None:
    if type(evidence) is not RecoveryConsoleEvidence:
        raise RecoveryConsoleError("recovery evidence type is invalid")
    if evidence.schema_version != SCHEMA_VERSION or evidence.profile != PROFILE:
        raise RecoveryConsoleError("recovery schema or profile is invalid")
    if not isinstance(evidence.receipt_id, str) or not re.fullmatch(r"recovery-[0-9a-f]{32}", evidence.receipt_id):
        raise RecoveryConsoleError("recovery receipt identity is invalid")
    for field in (
        "machine_identity_digest", "physical_marker_digest", "boot_entry_digest",
        "kernel_digest", "initramfs_digest",
    ):
        if not isinstance(getattr(evidence, field), str) or not _SHA256.fullmatch(getattr(evidence, field)):
            raise RecoveryConsoleError(f"{field} is not a canonical SHA-256")
    if not _BOOT_ID.fullmatch(evidence.before_boot_id) or not _BOOT_ID.fullmatch(evidence.recovery_boot_id):
        raise RecoveryConsoleError("recovery boot identity is invalid")
    if evidence.before_boot_id == evidence.recovery_boot_id:
        raise RecoveryConsoleError("recovery rehearsal did not cross a boot boundary")
    try:
        observed = dt.datetime.fromisoformat(evidence.observed_at)
    except (TypeError, ValueError) as error:
        raise RecoveryConsoleError("recovery observation time is invalid") from error
    if observed.tzinfo is None:
        raise RecoveryConsoleError("recovery observation time lacks timezone")
    if evidence.observer_kind != "owner-physical-plus-root-host-reconciliation":
        raise RecoveryConsoleError("recovery observer kind is not authoritative")
    boolean_fields = tuple(
        name for name, field in RecoveryConsoleEvidence.__dataclass_fields__.items()
        if field.type == "bool"
    )
    for field in boolean_fields:
        if type(getattr(evidence, field)) is not bool:
            raise RecoveryConsoleError(f"{field} must be boolean")


def assess_recovery_console(evidence: RecoveryConsoleEvidence) -> RecoveryConsoleAssessment:
    validate_recovery_evidence(evidence)
    gates = {
        "physical-presence-not-confirmed": evidence.physical_presence_confirmed,
        "built-in-keyboard-not-confirmed": evidence.built_in_keyboard_confirmed,
        "encrypted-root-unlock-not-confirmed": evidence.encrypted_root_unlock_confirmed,
        "root-console-not-confirmed": evidence.root_console_confirmed,
        "post-boot-apx-state-not-reconciled": evidence.apx_status_reconciled_after_boot,
        "hub-generation-changed": evidence.hub_generation_unchanged,
        "development-generation-changed": evidence.development_generation_unchanged,
        "disposable-hold-changed": evidence.disposable_hold_unchanged,
        "uncertain-apx-operation-present": evidence.no_uncertain_apx_operation,
        "disk-layout-changed": evidence.no_disk_layout_change,
        "encryption-changed": evidence.no_encryption_change,
        "bootloader-changed": evidence.no_bootloader_change,
        "package-state-changed": evidence.no_package_change,
        "apx-lifecycle-effect-occurred": evidence.no_apx_lifecycle_effect,
        "receipt-may-contain-secrets": evidence.secrets_absent_from_receipt,
    }
    blockers = tuple(label for label, passed in gates.items() if not passed)
    return RecoveryConsoleAssessment(
        "verified" if not blockers else "blocked",
        blockers,
        _digest(asdict(evidence)),
        not blockers,
    )
