"""Pure ten-stage clean-install journal and in-memory fixture store.

This module models ordering, approvals, evidence, interruption, and recovery.
It has no disk, package, boot, account, service, network, or host effect code.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import hashlib
import json
import re

from apx_clean_install_dossier import CleanInstallDossier, STAGES


SCHEMA_VERSION = 1
_OPERATION_ID = re.compile(r"install-[0-9a-f]{32}")
_TARGET_ID = re.compile(r"target-[0-9a-f]{32}")
_SHA256 = re.compile(r"[0-9a-f]{64}")

EFFECTS_BY_STAGE = {
    "observe": (
        "capture-target-identity-and-topology",
        "publish-read-only-target-evidence",
    ),
    "dossier": (
        "validate-target-and-supply-evidence",
        "publish-immutable-install-dossier",
    ),
    "approve-disk": (
        "authenticate-fresh-strong-approval",
        "bind-approval-to-target-and-plan",
    ),
    "storage": (
        "revalidate-target-unused-and-unchanged",
        "create-gpt-and-efi-system-partition",
        "create-luks2-container",
        "create-btrfs-and-flat-subvolumes",
        "enable-and-verify-qgroups",
        "verify-complete-storage-identity",
    ),
    "arch": (
        "install-closed-dated-package-manifest",
        "apply-fixed-host-configuration",
        "verify-packages-and-host-boundary",
    ),
    "boot": (
        "install-systemd-boot-and-entry",
        "build-and-verify-initramfs",
        "reboot-and-verify-locked-recovery-surface",
    ),
    "apx-bootstrap": (
        "verify-apx-package-signature-and-identity",
        "install-reviewed-apx-host-package",
        "initialize-empty-trusted-state",
        "verify-executor-broker-and-recovery-boundary",
    ),
    "hub": (
        "import-and-verify-first-hub-candidate",
        "admit-first-hub-release",
        "create-and-test-headless-hub",
        "verify-hub-recreation-and-recovery",
    ),
    "development": (
        "admit-development-role-release",
        "create-headless-development-environment",
        "verify-codex-git-and-build-tools-only-in-development",
        "verify-development-stop-and-zero-residue",
    ),
    "separation": (
        "create-second-disposable-environment",
        "install-package-independently-in-two-environments",
        "run-hostile-local-root-denial-tests",
        "verify-independent-delete-reboot-and-recovery",
        "publish-c0-c6-result",
    ),
}
if tuple(EFFECTS_BY_STAGE) != STAGES:
    raise RuntimeError("clean-install journal stages disagree with dossier")

REQUIRED_APPROVAL = {
    "observe": None,
    "dossier": None,
    "approve-disk": "strong-confirmation",
    "storage": "strong-confirmation",
    "arch": "explicit-confirmation",
    "boot": "explicit-confirmation",
    "apx-bootstrap": "explicit-confirmation",
    "hub": "explicit-confirmation",
    "development": "explicit-confirmation",
    "separation": "explicit-confirmation",
}
FLAT_EFFECTS = tuple(
    f"{stage}:{effect}" for stage in STAGES for effect in EFFECTS_BY_STAGE[stage]
)


class CleanInstallJournalError(ValueError):
    """Journal content, approval, transition, or fixture action is invalid."""


@dataclass(frozen=True)
class StageApproval:
    stage: str
    approval_class: str
    approval_digest: str


@dataclass(frozen=True)
class CleanInstallRecord:
    schema_version: int
    operation_id: str
    target_id: str
    dossier_plan_digest: str
    effects: tuple[str, ...]
    completed_effects: tuple[str, ...]
    effect_evidence_digests: tuple[str, ...]
    prepared_effect: str | None
    approvals: tuple[StageApproval, ...]
    status: str
    failure_reason: str | None
    final_evidence_digest: str | None
    sequence: int
    previous_digest: str | None
    record_digest: str


@dataclass(frozen=True)
class InstallRecovery:
    classification: str
    automatic_deletion_allowed: bool
    continuation_allowed: bool
    explanation: str


def _digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _record_digest(record: CleanInstallRecord) -> str:
    payload = asdict(record)
    payload.pop("record_digest")
    return _digest(payload)


def _with_digest(record: CleanInstallRecord) -> CleanInstallRecord:
    return replace(record, record_digest=_record_digest(record))


def create_install_record(
    dossier: CleanInstallDossier, *, operation_id: str
) -> CleanInstallRecord:
    if type(dossier) is not CleanInstallDossier:
        raise CleanInstallJournalError("clean-install dossier has wrong type")
    if dossier.classification != "ready-for-separate-approval":
        raise CleanInstallJournalError("blocked dossier cannot start installation")
    if not dossier.separate_strong_approval_required:
        raise CleanInstallJournalError("dossier lost separate approval requirement")
    if not _SHA256.fullmatch(dossier.plan_digest):
        raise CleanInstallJournalError("dossier plan digest is invalid")
    if not _OPERATION_ID.fullmatch(operation_id):
        raise CleanInstallJournalError("installation operation ID is invalid")
    record = CleanInstallRecord(
        SCHEMA_VERSION,
        operation_id,
        dossier.target_id,
        dossier.plan_digest,
        FLAT_EFFECTS,
        (),
        (),
        None,
        (),
        "reserved",
        None,
        None,
        0,
        None,
        "",
    )
    record = _with_digest(record)
    validate_install_record(record)
    return record


def _next(record: CleanInstallRecord, **changes: object) -> CleanInstallRecord:
    updated = replace(
        record,
        sequence=record.sequence + 1,
        previous_digest=record.record_digest,
        record_digest="",
        **changes,
    )
    updated = _with_digest(updated)
    validate_install_record(updated)
    return updated


def current_stage(record: CleanInstallRecord) -> str | None:
    validate_install_record(record)
    index = len(record.completed_effects)
    if index >= len(record.effects):
        return None
    return record.effects[index].split(":", 1)[0]


def bind_stage_approval(
    record: CleanInstallRecord,
    *,
    stage: str,
    approval_class: str,
    approval_digest: str,
) -> CleanInstallRecord:
    validate_install_record(record)
    if record.prepared_effect is not None or record.status in {"complete", "incomplete"}:
        raise CleanInstallJournalError("installation cannot bind approval now")
    if current_stage(record) != stage:
        raise CleanInstallJournalError("approval is not for the exact current stage")
    required = REQUIRED_APPROVAL.get(stage)
    if required is None or approval_class != required:
        raise CleanInstallJournalError("approval class does not match stage")
    if not _SHA256.fullmatch(approval_digest):
        raise CleanInstallJournalError("stage approval digest is invalid")
    if any(item.stage == stage for item in record.approvals):
        raise CleanInstallJournalError("stage approval is already bound")
    return _next(
        record,
        approvals=record.approvals + (StageApproval(stage, approval_class, approval_digest),),
    )


def prepare_next_effect(record: CleanInstallRecord) -> CleanInstallRecord:
    validate_install_record(record)
    if record.status in {"complete", "incomplete", "verifying-final"} or record.prepared_effect is not None:
        raise CleanInstallJournalError("installation cannot prepare another effect")
    index = len(record.completed_effects)
    if index >= len(record.effects):
        raise CleanInstallJournalError("all installation effects are complete")
    stage = current_stage(record)
    required = REQUIRED_APPROVAL[stage]
    if required is not None and not any(
        item.stage == stage and item.approval_class == required for item in record.approvals
    ):
        raise CleanInstallJournalError("exact current-stage approval is required")
    return _next(record, prepared_effect=record.effects[index], status="effect-prepared")


def record_effect_success(
    record: CleanInstallRecord, *, evidence_digest: str
) -> CleanInstallRecord:
    validate_install_record(record)
    if record.status != "effect-prepared" or record.prepared_effect is None:
        raise CleanInstallJournalError("no prepared installation effect can complete")
    if not _SHA256.fullmatch(evidence_digest):
        raise CleanInstallJournalError("installation evidence digest is invalid")
    completed = record.completed_effects + (record.prepared_effect,)
    status = "verifying-final" if len(completed) == len(record.effects) else "executing"
    return _next(
        record,
        completed_effects=completed,
        effect_evidence_digests=record.effect_evidence_digests + (evidence_digest,),
        prepared_effect=None,
        status=status,
    )


def complete_install(
    record: CleanInstallRecord, *, final_evidence_digest: str
) -> CleanInstallRecord:
    validate_install_record(record)
    if record.status != "verifying-final" or record.completed_effects != record.effects:
        raise CleanInstallJournalError("installation is not ready for final completion")
    if not _SHA256.fullmatch(final_evidence_digest):
        raise CleanInstallJournalError("final installation evidence is invalid")
    return _next(
        record, status="complete", final_evidence_digest=final_evidence_digest
    )


def mark_install_incomplete(
    record: CleanInstallRecord, *, reason: str
) -> CleanInstallRecord:
    validate_install_record(record)
    if record.status in {"complete", "incomplete"}:
        raise CleanInstallJournalError("terminal installation cannot become incomplete")
    if not isinstance(reason, str) or not reason or len(reason) > 160 or any(not char.isprintable() for char in reason):
        raise CleanInstallJournalError("installation failure reason is invalid")
    return _next(record, status="incomplete", failure_reason=reason)


def assess_install_recovery(record: CleanInstallRecord) -> InstallRecovery:
    validate_install_record(record)
    if record.status == "complete":
        return InstallRecovery("complete", False, False, "C0-C6 final evidence is complete")
    if record.prepared_effect is not None:
        return InstallRecovery(
            "preserve-effect-outcome-uncertain", False, False,
            "prepared effect requires authoritative inspection before continuation",
        )
    if not record.completed_effects:
        return InstallRecovery("no-effect", False, False, "no installation effect is recorded")
    storage_started = any(item.startswith("storage:") for item in record.completed_effects)
    if not storage_started:
        return InstallRecovery(
            "restart-read-only-foundation", False, True,
            "only observation/dossier/approval evidence exists; revalidate before continuing",
        )
    return InstallRecovery(
        "destructive-recovery-required", False, False,
        "storage effects began; preserve state and use target-bound recovery",
    )


def validate_install_record(record: CleanInstallRecord) -> None:
    if type(record) is not CleanInstallRecord or record.schema_version != SCHEMA_VERSION:
        raise CleanInstallJournalError("installation record schema is invalid")
    if (
        not _OPERATION_ID.fullmatch(record.operation_id)
        or not _TARGET_ID.fullmatch(record.target_id)
        or not _SHA256.fullmatch(record.dossier_plan_digest)
    ):
        raise CleanInstallJournalError("installation identity is invalid")
    if record.effects != FLAT_EFFECTS or record.completed_effects != record.effects[: len(record.completed_effects)]:
        raise CleanInstallJournalError("installation effects changed or are out of order")
    if len(record.effect_evidence_digests) != len(record.completed_effects):
        raise CleanInstallJournalError("installation evidence count disagrees with progress")
    for value in (record.record_digest, *record.effect_evidence_digests):
        if not isinstance(value, str) or not _SHA256.fullmatch(value):
            raise CleanInstallJournalError("installation record contains malformed digest")
    for value in (record.previous_digest, record.final_evidence_digest):
        if value is not None and not _SHA256.fullmatch(value):
            raise CleanInstallJournalError("installation optional digest is malformed")
    if type(record.sequence) is not int or record.sequence < 0:
        raise CleanInstallJournalError("installation sequence is invalid")
    stages = [item.stage for item in record.approvals]
    if len(stages) != len(set(stages)) or stages != sorted(stages, key=STAGES.index):
        raise CleanInstallJournalError("installation approvals are duplicated or out of order")
    for approval in record.approvals:
        if REQUIRED_APPROVAL.get(approval.stage) != approval.approval_class or not _SHA256.fullmatch(approval.approval_digest):
            raise CleanInstallJournalError("installation approval is invalid")
    completed_stages = {item.split(":", 1)[0] for item in record.completed_effects}
    current_index = len(record.completed_effects)
    allowed_approval_stages = set(completed_stages)
    if current_index < len(record.effects):
        allowed_approval_stages.add(record.effects[current_index].split(":", 1)[0])
    if any(item.stage not in allowed_approval_stages for item in record.approvals):
        raise CleanInstallJournalError("approval was bound before its stage")
    if record.prepared_effect is not None:
        if current_index >= len(record.effects) or record.prepared_effect != record.effects[current_index]:
            raise CleanInstallJournalError("prepared installation effect is not exact next effect")
    expected_status = "incomplete" if record.failure_reason is not None else (
        "complete" if record.final_evidence_digest is not None else
        "effect-prepared" if record.prepared_effect is not None else
        "verifying-final" if len(record.completed_effects) == len(record.effects) else
        "reserved" if not record.completed_effects else "executing"
    )
    if record.status != expected_status:
        raise CleanInstallJournalError("installation status disagrees with progress")
    if record.status == "complete" and record.completed_effects != record.effects:
        raise CleanInstallJournalError("complete installation lacks all effects")
    if record.failure_reason is not None and (not record.failure_reason or len(record.failure_reason) > 160):
        raise CleanInstallJournalError("installation failure reason is invalid")
    if record.record_digest != _record_digest(record):
        raise CleanInstallJournalError("installation record digest does not match")


class FixtureInstallStore:
    """In-memory exact-transition store for repository tests only."""

    def __init__(self, allowed_dossier: CleanInstallDossier) -> None:
        if (
            type(allowed_dossier) is not CleanInstallDossier
            or allowed_dossier.classification != "ready-for-separate-approval"
        ):
            raise CleanInstallJournalError("fixture store requires one ready dossier")
        self._allowed_target_id = allowed_dossier.target_id
        self._allowed_plan_digest = allowed_dossier.plan_digest
        self._records: dict[str, CleanInstallRecord] = {}

    def publish_new(self, record: CleanInstallRecord) -> None:
        validate_install_record(record)
        if record.status != "reserved" or record.sequence != 0 or record.previous_digest is not None or record.approvals:
            raise CleanInstallJournalError("fixture install must begin from exact initial state")
        if (
            record.target_id != self._allowed_target_id
            or record.dossier_plan_digest != self._allowed_plan_digest
        ):
            raise CleanInstallJournalError("fixture install does not match allowed dossier")
        if record.operation_id in self._records:
            raise CleanInstallJournalError("fixture install already exists")
        self._records[record.operation_id] = record

    def compare_and_swap(self, record: CleanInstallRecord, *, expected_digest: str) -> None:
        validate_install_record(record)
        current = self._records.get(record.operation_id)
        if current is None or current.record_digest != expected_digest:
            raise CleanInstallJournalError("fixture install writer is stale")
        if record.previous_digest != expected_digest or record.sequence != current.sequence + 1:
            raise CleanInstallJournalError("fixture install chain is invalid")
        if not _is_exact_transition(current, record):
            raise CleanInstallJournalError("fixture install transition is not one allowed step")
        self._records[record.operation_id] = record

    def read(self, operation_id: str) -> CleanInstallRecord:
        try:
            record = self._records[operation_id]
        except KeyError as error:
            raise CleanInstallJournalError("fixture install is absent") from error
        validate_install_record(record)
        return record


def _is_exact_transition(current: CleanInstallRecord, candidate: CleanInstallRecord) -> bool:
    possibilities: list[CleanInstallRecord] = []
    try:
        stage = current_stage(current)
        if stage is not None and REQUIRED_APPROVAL[stage] is not None and candidate.approvals:
            last = candidate.approvals[-1]
            if last.stage == stage:
                possibilities.append(bind_stage_approval(
                    current, stage=last.stage, approval_class=last.approval_class,
                    approval_digest=last.approval_digest,
                ))
        if current.prepared_effect is None and current.status not in {"complete", "incomplete", "verifying-final"}:
            try:
                possibilities.append(prepare_next_effect(current))
            except CleanInstallJournalError:
                pass
        if current.prepared_effect is not None and candidate.effect_evidence_digests:
            possibilities.append(record_effect_success(
                current, evidence_digest=candidate.effect_evidence_digests[-1]
            ))
        if current.status == "verifying-final" and candidate.final_evidence_digest is not None:
            possibilities.append(complete_install(
                current, final_evidence_digest=candidate.final_evidence_digest
            ))
        if candidate.failure_reason is not None:
            possibilities.append(mark_install_incomplete(current, reason=candidate.failure_reason))
    except CleanInstallJournalError:
        return False
    return candidate in possibilities
