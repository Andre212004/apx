"""Pure release-promotion state machine and in-memory fixture stores.

Nothing in this module imports bytes, extracts archives, verifies signatures,
writes host state, or creates a Hub. Evidence and approvals are future trusted
inputs. ``FixturePromotionStore`` exists only for repository tests.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import hashlib
import json
import re

from apx_release_candidate import ImportPlan


SCHEMA_VERSION = 1
MAX_FAILURE_REASON = 160
PROMOTION_STEPS = (
    "reserve-quarantine-identity",
    "copy-bounded-candidate-bytes",
    "verify-copied-candidate-identity",
    "publish-quarantine-object",
    "verify-candidate-schema-and-archive",
    "verify-provenance-and-signatures",
    "verify-packages-root-and-sanitization",
    "publish-verification-evidence",
    "reserve-catalogue-release-identity",
    "publish-immutable-catalogue-release",
)
IMPORT_STEP_COUNT = 4
VERIFICATION_STEP_COUNT = 8

_OPERATION_ID = re.compile(r"promotion-[0-9a-f]{32}")
_SHA256 = re.compile(r"[0-9a-f]{64}")


class PromotionError(ValueError):
    """Promotion state, transition, or fixture-store action is invalid."""


@dataclass(frozen=True)
class PromotionRecord:
    schema_version: int
    operation_id: str
    candidate_id: str
    candidate_digest: str
    import_plan_digest: str
    artifact_sha256: str
    import_approval_digest: str
    admission_approval_digest: str | None
    steps: tuple[str, ...]
    completed_steps: tuple[str, ...]
    step_evidence_digests: tuple[str, ...]
    prepared_step: str | None
    status: str
    failure_reason: str | None
    sequence: int
    previous_digest: str | None
    record_digest: str


@dataclass(frozen=True)
class CatalogueRelease:
    schema_version: int
    release_id: str
    candidate_id: str
    candidate_digest: str
    verification_evidence_digest: str
    promotion_operation_id: str
    promotion_record_digest: str
    catalogue_digest: str


@dataclass(frozen=True)
class PromotionRecovery:
    classification: str
    continuation_allowed: bool
    automatic_deletion_allowed: bool
    explanation: str


def _digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _record_digest(record: PromotionRecord) -> str:
    payload = asdict(record)
    payload.pop("record_digest")
    return _digest(payload)


def _with_digest(record: PromotionRecord) -> PromotionRecord:
    return replace(record, record_digest=_record_digest(record))


def _status_for(completed: int, prepared: bool = False) -> str:
    if prepared:
        return "effect-prepared"
    if completed == 0:
        return "reserved"
    if completed < IMPORT_STEP_COUNT:
        return "importing"
    if completed == IMPORT_STEP_COUNT:
        return "quarantined"
    if completed < VERIFICATION_STEP_COUNT:
        return "verifying"
    if completed == VERIFICATION_STEP_COUNT:
        return "verified-awaiting-admission"
    if completed < len(PROMOTION_STEPS):
        return "admitting"
    return "admitted"


def create_promotion_record(
    plan: ImportPlan,
    *,
    operation_id: str,
    import_approval_digest: str,
) -> PromotionRecord:
    if type(plan) is not ImportPlan:
        raise PromotionError("import plan has wrong type")
    if not _OPERATION_ID.fullmatch(operation_id):
        raise PromotionError("promotion operation ID is invalid")
    if not _SHA256.fullmatch(import_approval_digest):
        raise PromotionError("import approval digest is invalid")
    record = PromotionRecord(
        SCHEMA_VERSION,
        operation_id,
        plan.candidate_id,
        plan.candidate_digest,
        plan.plan_digest,
        plan.artifact_sha256,
        import_approval_digest,
        None,
        PROMOTION_STEPS,
        (),
        (),
        None,
        "reserved",
        None,
        0,
        None,
        "",
    )
    record = _with_digest(record)
    validate_promotion_record(record)
    return record


def _next(record: PromotionRecord, **changes: object) -> PromotionRecord:
    candidate = replace(
        record,
        sequence=record.sequence + 1,
        previous_digest=record.record_digest,
        record_digest="",
        **changes,
    )
    candidate = _with_digest(candidate)
    validate_promotion_record(candidate)
    return candidate


def prepare_next_step(record: PromotionRecord) -> PromotionRecord:
    validate_promotion_record(record)
    if record.status in {"admitted", "incomplete"} or record.prepared_step is not None:
        raise PromotionError("promotion cannot prepare another step")
    index = len(record.completed_steps)
    if index >= len(record.steps):
        raise PromotionError("all promotion steps are complete")
    if index >= VERIFICATION_STEP_COUNT and record.admission_approval_digest is None:
        raise PromotionError("separate admission approval is required")
    return _next(record, prepared_step=record.steps[index], status="effect-prepared")


def record_step_success(record: PromotionRecord, *, evidence_digest: str) -> PromotionRecord:
    validate_promotion_record(record)
    if record.status != "effect-prepared" or record.prepared_step is None:
        raise PromotionError("no exact prepared step can be completed")
    if not _SHA256.fullmatch(evidence_digest):
        raise PromotionError("step evidence digest is invalid")
    completed = record.completed_steps + (record.prepared_step,)
    return _next(
        record,
        completed_steps=completed,
        step_evidence_digests=record.step_evidence_digests + (evidence_digest,),
        prepared_step=None,
        status=_status_for(len(completed)),
    )


def bind_admission_approval(
    record: PromotionRecord, *, admission_approval_digest: str
) -> PromotionRecord:
    validate_promotion_record(record)
    if record.status != "verified-awaiting-admission" or record.prepared_step is not None:
        raise PromotionError("promotion is not ready for admission approval")
    if record.admission_approval_digest is not None:
        raise PromotionError("admission approval is already bound")
    if not _SHA256.fullmatch(admission_approval_digest):
        raise PromotionError("admission approval digest is invalid")
    return _next(record, admission_approval_digest=admission_approval_digest)


def mark_promotion_incomplete(record: PromotionRecord, *, reason: str) -> PromotionRecord:
    validate_promotion_record(record)
    if record.status in {"admitted", "incomplete"}:
        raise PromotionError("terminal promotion cannot become incomplete")
    if not isinstance(reason, str) or not reason or len(reason) > MAX_FAILURE_REASON or any(not char.isprintable() for char in reason):
        raise PromotionError("promotion failure reason is invalid")
    return _next(record, status="incomplete", failure_reason=reason)


def assess_promotion_recovery(record: PromotionRecord) -> PromotionRecovery:
    validate_promotion_record(record)
    if record.status == "admitted":
        return PromotionRecovery("complete", False, False, "catalogue release is immutable")
    if record.prepared_step is not None:
        return PromotionRecovery(
            "preserve-effect-outcome-uncertain", False, False,
            "prepared effect may have occurred and requires authoritative inspection",
        )
    completed = len(record.completed_steps)
    if completed == 0:
        return PromotionRecovery("no-effect", False, False, "no effect was recorded")
    if completed < IMPORT_STEP_COUNT:
        return PromotionRecovery(
            "preserve-partial-import", False, False,
            "partial import remains operation-owned and unpublished",
        )
    if completed < VERIFICATION_STEP_COUNT:
        return PromotionRecovery(
            "preserve-quarantine-review", True, False,
            "published quarantine may continue only after fresh checks",
        )
    return PromotionRecovery(
        "verified-awaiting-new-admission-approval", False, False,
        "verified candidate requires a separate current admission approval",
    )


def build_catalogue_release(record: PromotionRecord) -> CatalogueRelease:
    validate_promotion_record(record)
    if record.status != "admitted" or len(record.step_evidence_digests) != len(record.steps):
        raise PromotionError("only a complete admitted promotion can publish a release")
    verification_digest = _digest(record.step_evidence_digests[IMPORT_STEP_COUNT:VERIFICATION_STEP_COUNT])
    draft = CatalogueRelease(
        SCHEMA_VERSION,
        "release-" + record.candidate_digest,
        record.candidate_id,
        record.candidate_digest,
        verification_digest,
        record.operation_id,
        record.record_digest,
        "",
    )
    return replace(draft, catalogue_digest=_digest(asdict(draft) | {"catalogue_digest": ""}))


def validate_promotion_record(record: PromotionRecord) -> None:
    if type(record) is not PromotionRecord or record.schema_version != SCHEMA_VERSION:
        raise PromotionError("promotion record schema is invalid")
    if not _OPERATION_ID.fullmatch(record.operation_id):
        raise PromotionError("promotion operation ID is invalid")
    if record.steps != PROMOTION_STEPS:
        raise PromotionError("promotion steps changed")
    if record.completed_steps != record.steps[: len(record.completed_steps)]:
        raise PromotionError("completed promotion steps are not an exact prefix")
    if len(record.step_evidence_digests) != len(record.completed_steps):
        raise PromotionError("step evidence count disagrees with completed steps")
    for value in (
        record.candidate_digest,
        record.import_plan_digest,
        record.artifact_sha256,
        record.import_approval_digest,
        record.record_digest,
        *record.step_evidence_digests,
    ):
        if not isinstance(value, str) or not _SHA256.fullmatch(value):
            raise PromotionError("promotion contains malformed digest")
    for value in (record.admission_approval_digest, record.previous_digest):
        if value is not None and not _SHA256.fullmatch(value):
            raise PromotionError("promotion contains malformed optional digest")
    if type(record.sequence) is not int or record.sequence < 0:
        raise PromotionError("promotion sequence is invalid")
    expected_status = "incomplete" if record.failure_reason is not None else _status_for(
        len(record.completed_steps), record.prepared_step is not None
    )
    if record.status != expected_status:
        raise PromotionError("promotion status disagrees with progress")
    index = len(record.completed_steps)
    if record.prepared_step is not None:
        if index >= len(record.steps) or record.prepared_step != record.steps[index]:
            raise PromotionError("prepared promotion step is not exact next step")
    if index > VERIFICATION_STEP_COUNT and record.admission_approval_digest is None:
        raise PromotionError("admission effects lack separate approval")
    if record.admission_approval_digest is not None and index < VERIFICATION_STEP_COUNT:
        raise PromotionError("admission approval was bound before verification")
    if record.failure_reason is not None and (
        not record.failure_reason or len(record.failure_reason) > MAX_FAILURE_REASON
    ):
        raise PromotionError("promotion failure reason is invalid")
    if record.record_digest != _record_digest(record):
        raise PromotionError("promotion record digest does not match")


class FixturePromotionStore:
    """In-memory compare-and-swap fixture, never an authoritative APX store."""

    def __init__(self, allowed_plan: ImportPlan) -> None:
        if type(allowed_plan) is not ImportPlan:
            raise PromotionError("fixture store requires one exact import plan")
        self._allowed_plan = allowed_plan
        self._records: dict[str, PromotionRecord] = {}
        self._catalogue: dict[str, CatalogueRelease] = {}

    def publish_new(self, record: PromotionRecord) -> None:
        validate_promotion_record(record)
        if (
            record.status != "reserved"
            or record.sequence != 0
            or record.previous_digest is not None
            or record.completed_steps
            or record.prepared_step is not None
            or record.admission_approval_digest is not None
            or record.failure_reason is not None
        ):
            raise PromotionError("fixture promotion must begin from exact initial state")
        if (
            record.candidate_id != self._allowed_plan.candidate_id
            or record.candidate_digest != self._allowed_plan.candidate_digest
            or record.import_plan_digest != self._allowed_plan.plan_digest
            or record.artifact_sha256 != self._allowed_plan.artifact_sha256
        ):
            raise PromotionError("fixture promotion does not match allowed import plan")
        if record.operation_id in self._records:
            raise PromotionError("fixture promotion operation already exists")
        self._records[record.operation_id] = record

    def compare_and_swap(self, record: PromotionRecord, *, expected_digest: str) -> None:
        validate_promotion_record(record)
        current = self._records.get(record.operation_id)
        if current is None or current.record_digest != expected_digest:
            raise PromotionError("fixture promotion writer is stale")
        if record.previous_digest != expected_digest or record.sequence != current.sequence + 1:
            raise PromotionError("fixture promotion chain is invalid")
        if not _is_exact_next_transition(current, record):
            raise PromotionError("fixture promotion transition is not an allowed single step")
        self._records[record.operation_id] = record

    def read(self, operation_id: str) -> PromotionRecord:
        try:
            record = self._records[operation_id]
        except KeyError as error:
            raise PromotionError("fixture promotion operation is absent") from error
        validate_promotion_record(record)
        return record

    def publish_catalogue(self, release: CatalogueRelease) -> None:
        if type(release) is not CatalogueRelease or not _SHA256.fullmatch(release.catalogue_digest):
            raise PromotionError("fixture catalogue release is invalid")
        if release.release_id in self._catalogue:
            raise PromotionError("fixture catalogue release already exists")
        record = self.read(release.promotion_operation_id)
        if record.status != "admitted" or record.record_digest != release.promotion_record_digest:
            raise PromotionError("fixture catalogue release lacks admitted promotion")
        if release != build_catalogue_release(record):
            raise PromotionError("fixture catalogue release content changed")
        self._catalogue[release.release_id] = release

    def catalogue_release(self, release_id: str) -> CatalogueRelease:
        try:
            return self._catalogue[release_id]
        except KeyError as error:
            raise PromotionError("fixture catalogue release is absent") from error


def _is_exact_next_transition(
    current: PromotionRecord, candidate: PromotionRecord
) -> bool:
    possibilities: list[PromotionRecord] = []
    try:
        if current.prepared_step is None and current.status not in {"admitted", "incomplete"}:
            if len(current.completed_steps) < VERIFICATION_STEP_COUNT or current.admission_approval_digest is not None:
                possibilities.append(prepare_next_step(current))
        if current.prepared_step is not None and candidate.step_evidence_digests:
            possibilities.append(
                record_step_success(
                    current, evidence_digest=candidate.step_evidence_digests[-1]
                )
            )
        if (
            current.status == "verified-awaiting-admission"
            and current.admission_approval_digest is None
            and candidate.admission_approval_digest is not None
        ):
            possibilities.append(
                bind_admission_approval(
                    current,
                    admission_approval_digest=candidate.admission_approval_digest,
                )
            )
        if candidate.failure_reason is not None:
            possibilities.append(
                mark_promotion_incomplete(current, reason=candidate.failure_reason)
            )
    except PromotionError:
        return False
    return candidate in possibilities
