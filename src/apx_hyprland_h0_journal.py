"""Pure ordered H0 graphical experiment journal and recovery assessment."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import hashlib
import json
import re

from apx_hyprland_h0 import H0Preview, H0_EFFECTS, PROFILE, SCHEMA_VERSION


GRAPHICAL_START_INDEX = 5
GRAPHICAL_READY_COUNT = 7
TEARDOWN_START_INDEX = 8
MAX_REASON = 160
_H0_ID = re.compile(r"h0-[0-9a-f]{32}")
_SHA256 = re.compile(r"[0-9a-f]{64}")


class H0JournalError(ValueError):
    """H0 journal state or transition is invalid."""


@dataclass(frozen=True)
class H0Record:
    schema_version: int
    profile: str
    experiment_id: str
    plan_digest: str
    evidence_digest: str
    physical_approval_digest: str
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
class H0Recovery:
    classification: str
    recovery_vt_required: bool
    automatic_graphical_restart_allowed: bool
    automatic_cleanup_allowed: bool
    headless_hub_restore_claimed: bool
    explanation: str


def _digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _record_digest(record: H0Record) -> str:
    value = asdict(record)
    value.pop("record_digest")
    return _digest(value)


def _with_digest(record: H0Record) -> H0Record:
    return replace(record, record_digest=_record_digest(record))


def create_h0_record(
    preview: H0Preview, *, physical_approval_digest: str
) -> H0Record:
    if type(preview) is not H0Preview:
        raise H0JournalError("H0 preview has wrong type")
    if (
        preview.schema_version != SCHEMA_VERSION
        or preview.profile != PROFILE
        or preview.classification != "ready-for-separate-physical-approval"
        or preview.blockers
        or preview.effects != H0_EFFECTS
        or preview.separate_physical_approval_required is not True
        or preview.cleanup_not_authorized is not True
    ):
        raise H0JournalError("H0 preview is not ready")
    if not _SHA256.fullmatch(physical_approval_digest):
        raise H0JournalError("H0 physical approval digest is invalid")
    record = H0Record(
        SCHEMA_VERSION,
        PROFILE,
        preview.experiment_id,
        preview.plan_digest,
        preview.evidence_digest,
        physical_approval_digest,
        H0_EFFECTS,
        (),
        (),
        None,
        "approved-not-started",
        None,
        0,
        None,
        "",
    )
    record = _with_digest(record)
    validate_h0_record(record)
    return record


def _next(record: H0Record, **changes: object) -> H0Record:
    candidate = replace(
        record,
        sequence=record.sequence + 1,
        previous_digest=record.record_digest,
        record_digest="",
        **changes,
    )
    candidate = _with_digest(candidate)
    validate_h0_record(candidate)
    return candidate


def prepare_next_effect(record: H0Record) -> H0Record:
    validate_h0_record(record)
    if record.prepared_effect is not None or record.status in {
        "headless-restored", "preserved-uncertain"
    }:
        raise H0JournalError("H0 cannot prepare another effect")
    index = len(record.completed_effects)
    if index >= len(record.effects):
        raise H0JournalError("all H0 effects are complete")
    return _next(
        record,
        prepared_effect=record.effects[index],
        status="effect-prepared",
    )


def record_effect_success(record: H0Record, *, evidence_digest: str) -> H0Record:
    validate_h0_record(record)
    if record.status != "effect-prepared" or record.prepared_effect is None:
        raise H0JournalError("no exact prepared H0 effect can complete")
    if not _SHA256.fullmatch(evidence_digest):
        raise H0JournalError("H0 effect evidence digest is invalid")
    completed = record.completed_effects + (record.prepared_effect,)
    count = len(completed)
    if count <= GRAPHICAL_START_INDEX:
        status = "preparing-graphical-lease"
    elif count < GRAPHICAL_READY_COUNT:
        status = "starting-hyprland"
    elif count < TEARDOWN_START_INDEX:
        status = "graphical-ready"
    elif count < len(record.effects):
        status = "stopping-and-revoking"
    else:
        status = "headless-restored"
    return _next(
        record,
        completed_effects=completed,
        effect_evidence_digests=record.effect_evidence_digests + (evidence_digest,),
        prepared_effect=None,
        status=status,
    )


def mark_h0_uncertain(record: H0Record, *, reason: str) -> H0Record:
    validate_h0_record(record)
    if record.status in {"headless-restored", "preserved-uncertain"}:
        raise H0JournalError("terminal H0 record cannot become uncertain")
    if (
        not isinstance(reason, str)
        or not reason
        or len(reason) > MAX_REASON
        or any(not char.isprintable() for char in reason)
    ):
        raise H0JournalError("H0 uncertainty reason is invalid")
    return _next(record, status="preserved-uncertain", failure_reason=reason)


def assess_h0_recovery(record: H0Record) -> H0Recovery:
    validate_h0_record(record)
    if record.status == "headless-restored":
        return H0Recovery(
            "complete-headless-restored", False, False, False, True,
            "Hyprland stopped, devices were revoked, residue is absent, and the headless path is verified",
        )
    if record.prepared_effect is not None:
        return H0Recovery(
            "effect-outcome-unknown", True, False, False, False,
            "the prepared effect may have occurred; use the independent recovery VT",
        )
    if record.status == "preserved-uncertain":
        return H0Recovery(
            "preserve-and-inspect-from-recovery-vt", True, False, False, False,
            "session, VT, GPU, input, process, mount, and lease state must be re-observed",
        )
    completed = len(record.completed_effects)
    if completed == 0:
        return H0Recovery(
            "no-effect-recorded", False, False, False, False,
            "no H0 effect has completed",
        )
    if completed <= GRAPHICAL_START_INDEX:
        return H0Recovery(
            "partial-lease-preparation", True, False, False, False,
            "some session or device preparation may remain and must be revoked through recovery",
        )
    if completed < TEARDOWN_START_INDEX:
        return H0Recovery(
            "graphical-session-may-be-active", True, False, False, False,
            "Hyprland or its device lease may still be active; do not start another session",
        )
    return H0Recovery(
        "partial-teardown", True, False, False, False,
        "teardown began but zero residue and restored headless operation are not proven",
    )


def validate_h0_record(record: H0Record) -> None:
    if type(record) is not H0Record or record.schema_version != SCHEMA_VERSION:
        raise H0JournalError("H0 record schema is invalid")
    if record.profile != PROFILE or not _H0_ID.fullmatch(record.experiment_id):
        raise H0JournalError("H0 record identity is invalid")
    if record.effects != H0_EFFECTS:
        raise H0JournalError("H0 effects changed")
    if record.completed_effects != H0_EFFECTS[: len(record.completed_effects)]:
        raise H0JournalError("completed H0 effects are not an exact prefix")
    if len(record.effect_evidence_digests) != len(record.completed_effects):
        raise H0JournalError("H0 evidence count is inconsistent")
    for value in (
        record.plan_digest,
        record.evidence_digest,
        record.physical_approval_digest,
        record.record_digest,
        *record.effect_evidence_digests,
    ):
        if not _SHA256.fullmatch(value):
            raise H0JournalError("H0 record contains malformed digest")
    if record.previous_digest is not None and not _SHA256.fullmatch(record.previous_digest):
        raise H0JournalError("H0 previous digest is malformed")
    if type(record.sequence) is not int or record.sequence < 0:
        raise H0JournalError("H0 sequence is invalid")
    if (record.sequence == 0) != (record.previous_digest is None):
        raise H0JournalError("H0 record chain is invalid")
    if record.record_digest != _record_digest(record):
        raise H0JournalError("H0 record digest mismatch")
    if record.failure_reason is not None and record.status != "preserved-uncertain":
        raise H0JournalError("H0 failure reason exists outside uncertain state")
    if record.status == "preserved-uncertain":
        if not record.failure_reason:
            raise H0JournalError("uncertain H0 record lacks reason")
        return
    count = len(record.completed_effects)
    if record.prepared_effect is not None:
        if (
            count >= len(H0_EFFECTS)
            or record.prepared_effect != H0_EFFECTS[count]
            or record.status != "effect-prepared"
        ):
            raise H0JournalError("prepared H0 effect is not exact")
        return
    if count == 0:
        expected = "approved-not-started"
    elif count <= GRAPHICAL_START_INDEX:
        expected = "preparing-graphical-lease"
    elif count < GRAPHICAL_READY_COUNT:
        expected = "starting-hyprland"
    elif count < TEARDOWN_START_INDEX:
        expected = "graphical-ready"
    elif count < len(H0_EFFECTS):
        expected = "stopping-and-revoking"
    else:
        expected = "headless-restored"
    if record.status != expected:
        raise H0JournalError("H0 status disagrees with progress")


class FixtureH0Store:
    """Test-only compare-and-swap store; it performs no graphical effect."""

    def __init__(self, *, plan_digest: str) -> None:
        if not _SHA256.fullmatch(plan_digest):
            raise H0JournalError("allowed H0 plan digest is invalid")
        self._plan_digest = plan_digest
        self._record: H0Record | None = None

    def publish_new(self, record: H0Record) -> None:
        validate_h0_record(record)
        if self._record is not None:
            raise H0JournalError("H0 record already exists")
        if record.plan_digest != self._plan_digest or record.sequence != 0:
            raise H0JournalError("record is not the exact allowed initial H0 record")
        self._record = record

    def compare_and_swap(self, record: H0Record, *, expected_digest: str) -> None:
        validate_h0_record(record)
        if self._record is None or self._record.record_digest != expected_digest:
            raise H0JournalError("stale H0 writer")
        if (
            record.previous_digest != self._record.record_digest
            or record.sequence != self._record.sequence + 1
            or record.plan_digest != self._plan_digest
        ):
            raise H0JournalError("H0 transition is not one exact next record")
        self._record = record

    def read(self) -> H0Record | None:
        return self._record
