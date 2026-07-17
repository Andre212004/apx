"""Pure lifecycle journal for a future external Development model store.

This module records ordered evidence. It cannot unlock, mount, bind, start,
stop, detach, or remove anything. ``FixtureAttachmentStore`` is test-only.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import hashlib
import json
import re

from apx_external_model_storage import AttachmentPreview, PROFILE, SCHEMA_VERSION


ATTACH_STEPS = (
    "reverify-exact-device-and-stopped-development",
    "unlock-exact-reviewed-luks2-volume",
    "mount-exact-filesystem-at-private-host-path",
    "bind-only-model-store-into-development",
    "verify-hub-and-other-environment-denial",
    "publish-generation-bound-attachment-state",
)
DETACH_STEPS = (
    "stop-model-client-and-service",
    "verify-no-open-model-store-handle",
    "verify-development-runtime-stopped",
    "remove-exact-development-bind",
    "unmount-private-filesystem-and-close-luks2",
    "verify-attachment-absence-and-publish-detached-state",
)
MAX_FAILURE_REASON = 160

_OPERATION_ID = re.compile(r"operation-[0-9a-f]{32}")
_ATTACHMENT_ID = re.compile(r"attachment-[0-9a-f]{32}")
_GENERATION = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}")
_SHA256 = re.compile(r"[0-9a-f]{64}")


class AttachmentLifecycleError(ValueError):
    """Lifecycle record, transition, or fixture-store action is invalid."""


@dataclass(frozen=True)
class AttachmentLifecycleRecord:
    schema_version: int
    profile: str
    operation_id: str
    attachment_id: str
    development_generation: str
    preview_digest: str
    attach_steps: tuple[str, ...]
    completed_attach_steps: tuple[str, ...]
    attach_evidence_digests: tuple[str, ...]
    activation_evidence_digest: str | None
    detach_approval_digest: str | None
    detach_steps: tuple[str, ...]
    completed_detach_steps: tuple[str, ...]
    detach_evidence_digests: tuple[str, ...]
    prepared_step: str | None
    status: str
    failure_reason: str | None
    sequence: int
    previous_digest: str | None
    record_digest: str


@dataclass(frozen=True)
class AttachmentRecovery:
    classification: str
    continuation_allowed: bool
    automatic_cleanup_allowed: bool
    development_activation_allowed: bool
    explanation: str


def _digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _record_digest(record: AttachmentLifecycleRecord) -> str:
    payload = asdict(record)
    payload.pop("record_digest")
    return _digest(payload)


def _with_digest(record: AttachmentLifecycleRecord) -> AttachmentLifecycleRecord:
    return replace(record, record_digest=_record_digest(record))


def create_lifecycle(preview: AttachmentPreview) -> AttachmentLifecycleRecord:
    if type(preview) is not AttachmentPreview:
        raise AttachmentLifecycleError("attachment preview has wrong type")
    if (
        preview.schema_version != SCHEMA_VERSION
        or preview.profile != PROFILE
        or preview.classification != "preview-only"
        or preview.effects != ATTACH_STEPS
        or preview.separate_implementation_and_approval_required is not True
    ):
        raise AttachmentLifecycleError("attachment preview is outside the fixed lifecycle")
    if not _OPERATION_ID.fullmatch(preview.operation_id):
        raise AttachmentLifecycleError("attachment operation identity is invalid")
    if not _SHA256.fullmatch(preview.preview_digest):
        raise AttachmentLifecycleError("attachment preview digest is invalid")
    record = AttachmentLifecycleRecord(
        SCHEMA_VERSION,
        PROFILE,
        preview.operation_id,
        preview.attachment_id,
        preview.development_generation,
        preview.preview_digest,
        ATTACH_STEPS,
        (),
        (),
        None,
        None,
        DETACH_STEPS,
        (),
        (),
        None,
        "attach-planned",
        None,
        0,
        None,
        "",
    )
    record = _with_digest(record)
    validate_lifecycle(record)
    return record


def _next(record: AttachmentLifecycleRecord, **changes: object) -> AttachmentLifecycleRecord:
    candidate = replace(
        record,
        sequence=record.sequence + 1,
        previous_digest=record.record_digest,
        record_digest="",
        **changes,
    )
    candidate = _with_digest(candidate)
    validate_lifecycle(candidate)
    return candidate


def prepare_next_step(record: AttachmentLifecycleRecord) -> AttachmentLifecycleRecord:
    validate_lifecycle(record)
    if record.prepared_step is not None or record.status in {
        "attached-stopped", "active", "detached", "preserved-uncertain"
    }:
        raise AttachmentLifecycleError("lifecycle cannot prepare another step")
    if record.status in {"attach-planned", "attaching"}:
        steps = record.attach_steps
        completed = record.completed_attach_steps
    elif record.status in {"detach-planned", "detaching"}:
        steps = record.detach_steps
        completed = record.completed_detach_steps
    else:
        raise AttachmentLifecycleError("lifecycle status cannot prepare an effect")
    if len(completed) >= len(steps):
        raise AttachmentLifecycleError("all lifecycle steps are complete")
    return _next(record, prepared_step=steps[len(completed)], status="effect-prepared")


def record_step_success(
    record: AttachmentLifecycleRecord, *, evidence_digest: str
) -> AttachmentLifecycleRecord:
    validate_lifecycle(record)
    if record.status != "effect-prepared" or record.prepared_step is None:
        raise AttachmentLifecycleError("no exact prepared step can be completed")
    if not _SHA256.fullmatch(evidence_digest):
        raise AttachmentLifecycleError("step evidence digest is invalid")
    if record.prepared_step in record.attach_steps:
        if record.detach_approval_digest is not None or record.completed_detach_steps:
            raise AttachmentLifecycleError("attach step appeared during detach")
        completed = record.completed_attach_steps + (record.prepared_step,)
        return _next(
            record,
            completed_attach_steps=completed,
            attach_evidence_digests=record.attach_evidence_digests + (evidence_digest,),
            prepared_step=None,
            status="attached-stopped" if completed == record.attach_steps else "attaching",
        )
    if record.prepared_step in record.detach_steps:
        if record.detach_approval_digest is None:
            raise AttachmentLifecycleError("detach approval is absent")
        completed = record.completed_detach_steps + (record.prepared_step,)
        return _next(
            record,
            completed_detach_steps=completed,
            detach_evidence_digests=record.detach_evidence_digests + (evidence_digest,),
            prepared_step=None,
            status="detached" if completed == record.detach_steps else "detaching",
        )
    raise AttachmentLifecycleError("prepared step is outside the fixed lifecycle")


def record_activation(
    record: AttachmentLifecycleRecord, *, evidence_digest: str
) -> AttachmentLifecycleRecord:
    validate_lifecycle(record)
    if record.status != "attached-stopped" or record.prepared_step is not None:
        raise AttachmentLifecycleError("attachment is not ready for Development activation")
    if not _SHA256.fullmatch(evidence_digest):
        raise AttachmentLifecycleError("activation evidence digest is invalid")
    return _next(record, activation_evidence_digest=evidence_digest, status="active")


def begin_detach(
    record: AttachmentLifecycleRecord, *, detach_approval_digest: str
) -> AttachmentLifecycleRecord:
    validate_lifecycle(record)
    if record.status not in {"active", "attached-stopped"} or record.prepared_step is not None:
        raise AttachmentLifecycleError("attachment is not ready for detach")
    if not _SHA256.fullmatch(detach_approval_digest):
        raise AttachmentLifecycleError("detach approval digest is invalid")
    return _next(
        record,
        detach_approval_digest=detach_approval_digest,
        status="detach-planned",
    )


def mark_uncertain(
    record: AttachmentLifecycleRecord, *, reason: str
) -> AttachmentLifecycleRecord:
    validate_lifecycle(record)
    if record.status in {"detached", "preserved-uncertain"}:
        raise AttachmentLifecycleError("terminal lifecycle cannot become uncertain")
    if (
        not isinstance(reason, str)
        or not reason
        or len(reason) > MAX_FAILURE_REASON
        or any(not char.isprintable() for char in reason)
    ):
        raise AttachmentLifecycleError("uncertainty reason is invalid")
    return _next(record, status="preserved-uncertain", failure_reason=reason)


def assess_recovery(record: AttachmentLifecycleRecord) -> AttachmentRecovery:
    validate_lifecycle(record)
    if record.status == "detached":
        return AttachmentRecovery(
            "complete-detached", False, False, True,
            "the exact bind, mount, encrypted volume, and attachment state are verified absent",
        )
    if record.status == "active":
        return AttachmentRecovery(
            "active-requires-normal-stop", True, False, True,
            "Development must follow the reviewed stop and detach sequence",
        )
    if record.status == "attached-stopped":
        return AttachmentRecovery(
            "attached-stopped", True, False, True,
            "the store is attached and Development may activate only with fresh evidence",
        )
    if record.prepared_step is not None:
        return AttachmentRecovery(
            "preserve-effect-outcome-uncertain", False, False, False,
            "the prepared effect may have occurred and requires authoritative inspection",
        )
    if record.status == "preserved-uncertain":
        return AttachmentRecovery(
            "preserve-and-inspect", False, False, False,
            "identity, process, mount, filesystem, and encryption evidence must be reconciled",
        )
    if record.completed_detach_steps:
        return AttachmentRecovery(
            "preserve-partial-detach", False, False, False,
            "partial detach must be inspected and never completed by assumption",
        )
    if record.completed_attach_steps:
        return AttachmentRecovery(
            "preserve-partial-attach", False, False, False,
            "partial attach must be inspected before retry or rollback",
        )
    return AttachmentRecovery(
        "no-effect-recorded", False, False, False,
        "no attachment effect has completed",
    )


def validate_lifecycle(record: AttachmentLifecycleRecord) -> None:
    if type(record) is not AttachmentLifecycleRecord or record.schema_version != SCHEMA_VERSION:
        raise AttachmentLifecycleError("lifecycle schema is invalid")
    if record.profile != PROFILE or not _OPERATION_ID.fullmatch(record.operation_id):
        raise AttachmentLifecycleError("lifecycle identity is invalid")
    if not _ATTACHMENT_ID.fullmatch(record.attachment_id) or not _GENERATION.fullmatch(record.development_generation):
        raise AttachmentLifecycleError("bound attachment or Development identity is invalid")
    if record.attach_steps != ATTACH_STEPS or record.detach_steps != DETACH_STEPS:
        raise AttachmentLifecycleError("lifecycle steps changed")
    if record.completed_attach_steps != ATTACH_STEPS[: len(record.completed_attach_steps)]:
        raise AttachmentLifecycleError("completed attach steps are not an exact prefix")
    if record.completed_detach_steps != DETACH_STEPS[: len(record.completed_detach_steps)]:
        raise AttachmentLifecycleError("completed detach steps are not an exact prefix")
    if len(record.attach_evidence_digests) != len(record.completed_attach_steps):
        raise AttachmentLifecycleError("attach evidence count disagrees with completed steps")
    if len(record.detach_evidence_digests) != len(record.completed_detach_steps):
        raise AttachmentLifecycleError("detach evidence count disagrees with completed steps")
    for digest in (
        record.preview_digest,
        record.record_digest,
        *record.attach_evidence_digests,
        *record.detach_evidence_digests,
    ):
        if not _SHA256.fullmatch(digest):
            raise AttachmentLifecycleError("lifecycle digest is invalid")
    for optional in (
        record.activation_evidence_digest,
        record.detach_approval_digest,
        record.previous_digest,
    ):
        if optional is not None and not _SHA256.fullmatch(optional):
            raise AttachmentLifecycleError("optional lifecycle digest is invalid")
    valid_statuses = {
        "attach-planned", "attaching", "effect-prepared", "attached-stopped",
        "active", "detach-planned", "detaching", "detached", "preserved-uncertain",
    }
    if record.status not in valid_statuses:
        raise AttachmentLifecycleError("lifecycle status is invalid")
    if type(record.sequence) is not int or record.sequence < 0:
        raise AttachmentLifecycleError("lifecycle sequence is invalid")
    if record.sequence == 0 and record.previous_digest is not None:
        raise AttachmentLifecycleError("initial lifecycle has a previous digest")
    if record.sequence > 0 and record.previous_digest is None:
        raise AttachmentLifecycleError("advanced lifecycle lacks previous digest")
    if record.record_digest != _record_digest(record):
        raise AttachmentLifecycleError("lifecycle record digest mismatch")
    if record.status == "active" and (
        record.completed_attach_steps != ATTACH_STEPS
        or record.activation_evidence_digest is None
    ):
        raise AttachmentLifecycleError("active lifecycle lacks complete attachment evidence")
    if record.completed_detach_steps and record.detach_approval_digest is None:
        raise AttachmentLifecycleError("detach steps lack approval")
    if record.status == "detached" and record.completed_detach_steps != DETACH_STEPS:
        raise AttachmentLifecycleError("detached lifecycle is incomplete")
    if record.failure_reason is not None and record.status != "preserved-uncertain":
        raise AttachmentLifecycleError("failure reason exists outside uncertain state")
    if record.status != "preserved-uncertain":
        if record.detach_approval_digest is None:
            if record.completed_detach_steps or record.detach_evidence_digests:
                raise AttachmentLifecycleError("detach progress exists before detach planning")
            if record.prepared_step is not None:
                expected_prepared = ATTACH_STEPS[len(record.completed_attach_steps)]
                if record.prepared_step != expected_prepared or record.status != "effect-prepared":
                    raise AttachmentLifecycleError("prepared attach step is not exact")
            elif record.activation_evidence_digest is not None:
                if record.status != "active" or record.completed_attach_steps != ATTACH_STEPS:
                    raise AttachmentLifecycleError("activation state is inconsistent")
            elif record.completed_attach_steps == ATTACH_STEPS:
                if record.status != "attached-stopped":
                    raise AttachmentLifecycleError("complete attach state is inconsistent")
            elif record.completed_attach_steps:
                if record.status != "attaching":
                    raise AttachmentLifecycleError("partial attach state is inconsistent")
            elif record.status != "attach-planned":
                raise AttachmentLifecycleError("initial attach state is inconsistent")
        else:
            if record.completed_attach_steps != ATTACH_STEPS:
                raise AttachmentLifecycleError("detach planned before attachment completed")
            if record.prepared_step is not None:
                expected_prepared = DETACH_STEPS[len(record.completed_detach_steps)]
                if record.prepared_step != expected_prepared or record.status != "effect-prepared":
                    raise AttachmentLifecycleError("prepared detach step is not exact")
            elif record.completed_detach_steps == DETACH_STEPS:
                if record.status != "detached":
                    raise AttachmentLifecycleError("complete detach state is inconsistent")
            elif record.completed_detach_steps:
                if record.status != "detaching":
                    raise AttachmentLifecycleError("partial detach state is inconsistent")
            elif record.status != "detach-planned":
                raise AttachmentLifecycleError("planned detach state is inconsistent")


class FixtureAttachmentStore:
    """In-memory compare-and-swap store for tests; it performs no host effect."""

    def __init__(self, *, preview_digest: str) -> None:
        if not _SHA256.fullmatch(preview_digest):
            raise AttachmentLifecycleError("allowed preview digest is invalid")
        self._preview_digest = preview_digest
        self._record: AttachmentLifecycleRecord | None = None

    def publish_new(self, record: AttachmentLifecycleRecord) -> None:
        validate_lifecycle(record)
        if self._record is not None:
            raise AttachmentLifecycleError("attachment lifecycle already exists")
        if record.preview_digest != self._preview_digest or record.sequence != 0:
            raise AttachmentLifecycleError("record is not the exact allowed initial lifecycle")
        self._record = record

    def compare_and_swap(
        self, record: AttachmentLifecycleRecord, *, expected_digest: str
    ) -> None:
        validate_lifecycle(record)
        if self._record is None or self._record.record_digest != expected_digest:
            raise AttachmentLifecycleError("stale lifecycle writer")
        if (
            record.previous_digest != self._record.record_digest
            or record.sequence != self._record.sequence + 1
            or record.preview_digest != self._preview_digest
        ):
            raise AttachmentLifecycleError("lifecycle transition is not one exact next record")
        self._record = record

    def read(self) -> AttachmentLifecycleRecord | None:
        return self._record
