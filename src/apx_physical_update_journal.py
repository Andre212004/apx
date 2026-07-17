"""Pure ordered journal for a future physical-pilot update.

It records supplied evidence only and has no import, install, service, runtime,
Hub, Development, rollback, or cleanup adapter. The fixture store is test-only.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import hashlib
import json
import re

from apx_physical_update import (
    PhysicalUpdatePreview,
    PROFILE,
    SCHEMA_VERSION,
    UPDATE_EFFECTS,
)


ACTIVATION_BOUNDARY = 4
MAX_REASON = 160
_UPDATE_ID = re.compile(r"update-[0-9a-f]{32}")
_SHA256 = re.compile(r"[0-9a-f]{64}")


class PhysicalUpdateJournalError(ValueError):
    """Update journal state or transition is malformed."""


@dataclass(frozen=True)
class PhysicalUpdateRecord:
    schema_version: int
    profile: str
    update_id: str
    plan_digest: str
    candidate_digest: str
    installed_evidence_digest: str
    import_approval_digest: str
    activation_approval_digest: str | None
    effects: tuple[str, ...]
    completed_effects: tuple[str, ...]
    effect_evidence_digests: tuple[str, ...]
    prepared_effect: str | None
    status: str
    failure_reason: str | None
    sequence: int
    previous_digest: str | None
    record_digest: str


@dataclass(frozen=True)
class PhysicalUpdateRecovery:
    classification: str
    continuation_allowed: bool
    automatic_rollback_allowed: bool
    automatic_cleanup_allowed: bool
    explanation: str


def _digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _record_digest(record: PhysicalUpdateRecord) -> str:
    value = asdict(record)
    value.pop("record_digest")
    return _digest(value)


def _with_digest(record: PhysicalUpdateRecord) -> PhysicalUpdateRecord:
    return replace(record, record_digest=_record_digest(record))


def create_update_record(
    preview: PhysicalUpdatePreview, *, import_approval_digest: str
) -> PhysicalUpdateRecord:
    if type(preview) is not PhysicalUpdatePreview:
        raise PhysicalUpdateJournalError("update preview has wrong type")
    if (
        preview.schema_version != SCHEMA_VERSION
        or preview.profile != PROFILE
        or preview.classification != "ready-for-separate-import-approval"
        or preview.blockers
        or preview.effects != UPDATE_EFFECTS
        or preview.separate_import_approval_required is not True
        or preview.separate_activation_approval_required is not True
        or preview.rollback_retirement_requires_later_approval is not True
    ):
        raise PhysicalUpdateJournalError("update preview is not ready")
    if not _SHA256.fullmatch(import_approval_digest):
        raise PhysicalUpdateJournalError("import approval digest is invalid")
    record = PhysicalUpdateRecord(
        SCHEMA_VERSION,
        PROFILE,
        preview.update_id,
        preview.plan_digest,
        preview.candidate_digest,
        preview.installed_evidence_digest,
        import_approval_digest,
        None,
        UPDATE_EFFECTS,
        (),
        (),
        None,
        "import-approved",
        None,
        0,
        None,
        "",
    )
    record = _with_digest(record)
    validate_update_record(record)
    return record


def _next(record: PhysicalUpdateRecord, **changes: object) -> PhysicalUpdateRecord:
    candidate = replace(
        record,
        sequence=record.sequence + 1,
        previous_digest=record.record_digest,
        record_digest="",
        **changes,
    )
    candidate = _with_digest(candidate)
    validate_update_record(candidate)
    return candidate


def prepare_next_effect(record: PhysicalUpdateRecord) -> PhysicalUpdateRecord:
    validate_update_record(record)
    if record.prepared_effect is not None or record.status in {
        "installed-rollback-retained", "preserved-uncertain",
    }:
        raise PhysicalUpdateJournalError("update cannot prepare another effect")
    completed = len(record.completed_effects)
    if completed >= len(record.effects):
        raise PhysicalUpdateJournalError("all update effects are complete")
    if completed >= ACTIVATION_BOUNDARY and record.activation_approval_digest is None:
        raise PhysicalUpdateJournalError("separate activation approval is required")
    return _next(
        record,
        prepared_effect=record.effects[completed],
        status="effect-prepared",
    )


def record_effect_success(
    record: PhysicalUpdateRecord, *, evidence_digest: str
) -> PhysicalUpdateRecord:
    validate_update_record(record)
    if record.status != "effect-prepared" or record.prepared_effect is None:
        raise PhysicalUpdateJournalError("no exact prepared effect can complete")
    if not _SHA256.fullmatch(evidence_digest):
        raise PhysicalUpdateJournalError("effect evidence digest is invalid")
    completed = record.completed_effects + (record.prepared_effect,)
    if len(completed) == ACTIVATION_BOUNDARY:
        status = "verified-awaiting-activation-approval"
    elif len(completed) == len(record.effects):
        status = "installed-rollback-retained"
    elif len(completed) < ACTIVATION_BOUNDARY:
        status = "importing-and-verifying"
    else:
        status = "activating-and-verifying"
    return _next(
        record,
        completed_effects=completed,
        effect_evidence_digests=record.effect_evidence_digests + (evidence_digest,),
        prepared_effect=None,
        status=status,
    )


def bind_activation_approval(
    record: PhysicalUpdateRecord, *, activation_approval_digest: str
) -> PhysicalUpdateRecord:
    validate_update_record(record)
    if record.status != "verified-awaiting-activation-approval" or record.prepared_effect is not None:
        raise PhysicalUpdateJournalError("update is not ready for activation approval")
    if record.activation_approval_digest is not None:
        raise PhysicalUpdateJournalError("activation approval is already bound")
    if not _SHA256.fullmatch(activation_approval_digest):
        raise PhysicalUpdateJournalError("activation approval digest is invalid")
    return _next(
        record,
        activation_approval_digest=activation_approval_digest,
        status="activation-approved",
    )


def mark_update_uncertain(
    record: PhysicalUpdateRecord, *, reason: str
) -> PhysicalUpdateRecord:
    validate_update_record(record)
    if record.status in {"installed-rollback-retained", "preserved-uncertain"}:
        raise PhysicalUpdateJournalError("terminal update cannot become uncertain")
    if (
        not isinstance(reason, str)
        or not reason
        or len(reason) > MAX_REASON
        or any(not char.isprintable() for char in reason)
    ):
        raise PhysicalUpdateJournalError("uncertainty reason is invalid")
    return _next(record, status="preserved-uncertain", failure_reason=reason)


def assess_update_recovery(record: PhysicalUpdateRecord) -> PhysicalUpdateRecovery:
    validate_update_record(record)
    if record.status == "installed-rollback-retained":
        return PhysicalUpdateRecovery(
            "complete-with-rollback-retained", False, False, False,
            "the update is verified and the previous installed set remains available",
        )
    if record.prepared_effect is not None:
        return PhysicalUpdateRecovery(
            "preserve-effect-outcome-uncertain", False, False, False,
            "the prepared effect may have occurred and requires physical inspection",
        )
    if record.status == "preserved-uncertain":
        return PhysicalUpdateRecovery(
            "preserve-and-inspect", False, False, False,
            "the current and rollback sets must be identified before any continuation",
        )
    completed = len(record.completed_effects)
    if completed == 0:
        return PhysicalUpdateRecovery(
            "no-effect-recorded", False, False, False,
            "no update effect has completed",
        )
    if completed < ACTIVATION_BOUNDARY:
        return PhysicalUpdateRecovery(
            "preserve-private-staging", True, False, False,
            "bounded staging may continue only after its identities are rechecked",
        )
    if completed == ACTIVATION_BOUNDARY and record.activation_approval_digest is None:
        return PhysicalUpdateRecovery(
            "verified-awaiting-new-activation-approval", False, False, False,
            "verified bytes still require a fresh separate activation decision",
        )
    return PhysicalUpdateRecovery(
        "preserve-partial-activation-with-rollback", False, False, False,
        "host components may have changed; inspect both installed sets and recovery state",
    )


def validate_update_record(record: PhysicalUpdateRecord) -> None:
    if type(record) is not PhysicalUpdateRecord or record.schema_version != SCHEMA_VERSION:
        raise PhysicalUpdateJournalError("update record schema is invalid")
    if record.profile != PROFILE or not _UPDATE_ID.fullmatch(record.update_id):
        raise PhysicalUpdateJournalError("update record identity is invalid")
    if record.effects != UPDATE_EFFECTS:
        raise PhysicalUpdateJournalError("update effects changed")
    if record.completed_effects != UPDATE_EFFECTS[: len(record.completed_effects)]:
        raise PhysicalUpdateJournalError("completed effects are not an exact prefix")
    if len(record.effect_evidence_digests) != len(record.completed_effects):
        raise PhysicalUpdateJournalError("effect evidence count is inconsistent")
    for value in (
        record.plan_digest,
        record.candidate_digest,
        record.installed_evidence_digest,
        record.import_approval_digest,
        record.record_digest,
        *record.effect_evidence_digests,
    ):
        if not _SHA256.fullmatch(value):
            raise PhysicalUpdateJournalError("update record contains malformed digest")
    for value in (
        record.activation_approval_digest,
        record.previous_digest,
    ):
        if value is not None and not _SHA256.fullmatch(value):
            raise PhysicalUpdateJournalError("optional update digest is malformed")
    if type(record.sequence) is not int or record.sequence < 0:
        raise PhysicalUpdateJournalError("update sequence is invalid")
    if (record.sequence == 0) != (record.previous_digest is None):
        raise PhysicalUpdateJournalError("update chain is invalid")
    if record.record_digest != _record_digest(record):
        raise PhysicalUpdateJournalError("update record digest mismatch")
    if record.failure_reason is not None and record.status != "preserved-uncertain":
        raise PhysicalUpdateJournalError("failure reason exists outside uncertain state")
    if record.status == "preserved-uncertain":
        if not record.failure_reason:
            raise PhysicalUpdateJournalError("uncertain state lacks a reason")
        return
    completed = len(record.completed_effects)
    if record.prepared_effect is not None:
        if (
            completed >= len(UPDATE_EFFECTS)
            or record.prepared_effect != UPDATE_EFFECTS[completed]
            or record.status != "effect-prepared"
        ):
            raise PhysicalUpdateJournalError("prepared effect is not exact")
        if completed >= ACTIVATION_BOUNDARY and record.activation_approval_digest is None:
            raise PhysicalUpdateJournalError("activation effect prepared without approval")
        return
    if completed == 0:
        expected = "import-approved"
    elif completed < ACTIVATION_BOUNDARY:
        expected = "importing-and-verifying"
    elif completed == ACTIVATION_BOUNDARY and record.activation_approval_digest is None:
        expected = "verified-awaiting-activation-approval"
    elif completed == ACTIVATION_BOUNDARY:
        expected = "activation-approved"
    elif completed < len(UPDATE_EFFECTS):
        expected = "activating-and-verifying"
    else:
        expected = "installed-rollback-retained"
    if record.status != expected:
        raise PhysicalUpdateJournalError("update status disagrees with progress")
    if completed > ACTIVATION_BOUNDARY and record.activation_approval_digest is None:
        raise PhysicalUpdateJournalError("activation progressed without approval")


class FixturePhysicalUpdateStore:
    """In-memory compare-and-swap fixture; it performs no physical effect."""

    def __init__(self, *, plan_digest: str) -> None:
        if not _SHA256.fullmatch(plan_digest):
            raise PhysicalUpdateJournalError("allowed plan digest is invalid")
        self._plan_digest = plan_digest
        self._record: PhysicalUpdateRecord | None = None

    def publish_new(self, record: PhysicalUpdateRecord) -> None:
        validate_update_record(record)
        if self._record is not None:
            raise PhysicalUpdateJournalError("update record already exists")
        if record.plan_digest != self._plan_digest or record.sequence != 0:
            raise PhysicalUpdateJournalError("record is not the exact allowed initial update")
        self._record = record

    def compare_and_swap(
        self, record: PhysicalUpdateRecord, *, expected_digest: str
    ) -> None:
        validate_update_record(record)
        if self._record is None or self._record.record_digest != expected_digest:
            raise PhysicalUpdateJournalError("stale update writer")
        if (
            record.previous_digest != self._record.record_digest
            or record.sequence != self._record.sequence + 1
            or record.plan_digest != self._plan_digest
        ):
            raise PhysicalUpdateJournalError("update transition is not one exact next record")
        self._record = record

    def read(self) -> PhysicalUpdateRecord | None:
        return self._record
