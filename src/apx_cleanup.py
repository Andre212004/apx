"""Pure complete-cleanup contract for APX Environment destruction."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import re
from typing import Sequence


CLEANUP_POLICY = "complete-cleanup-v1"
SCOPES = ("complete-purge",)
RESOURCE_KINDS = (
    "root", "home", "runtime", "account", "registration", "qgroup",
    "snapshot", "archive", "backup", "capability", "plan", "metadata", "network",
)
DISPOSITIONS = ("delete", "preserve")
OBSERVED_STATES = (
    "present", "deletion-requested", "under-deletion", "stale", "absent", "uncertain"
)
ASSESSMENT_STATES = (
    "awaiting-approval", "deleting", "freeing-space", "complete",
    "preserved-uncertain", "failed",
)
_SAFE_ID = re.compile(r"[a-z0-9][a-z0-9._:/-]{0,159}")
_SHA256 = re.compile(r"[0-9a-f]{64}")


class CleanupError(ValueError):
    """Cleanup plan or evidence is ambiguous or outside policy."""


@dataclass(frozen=True)
class CleanupResource:
    resource_id: str
    kind: str
    identity_digest: str
    disposition: str


@dataclass(frozen=True)
class CleanupPlan:
    policy: str
    environment_id: str
    generation: int
    scope: str
    resources: tuple[CleanupResource, ...]
    plan_digest: str


@dataclass(frozen=True)
class ResourceObservation:
    resource_id: str
    identity_digest: str | None
    state: str


@dataclass(frozen=True)
class CleanupEvidence:
    observations: tuple[ResourceObservation, ...]
    stopped: bool
    processes_absent: bool
    open_handles_absent: bool
    mounts_absent: bool
    network_absent: bool
    account_absent: bool
    registration_absent: bool
    quota_consistent: bool
    protected_neighbors_unchanged: bool
    free_bytes_before: int
    free_bytes_after: int
    authoritative: bool


@dataclass(frozen=True)
class CleanupAssessment:
    state: str
    progress_completed: int
    progress_total: int
    pending: tuple[str, ...]
    preserved: tuple[str, ...]
    reclaimed_bytes_observed: int
    reusable_identity: bool
    evidence_digest: str


def _resource_payload(resource: CleanupResource) -> dict[str, object]:
    return asdict(resource)


def _plan_digest(plan: CleanupPlan) -> str:
    payload = {
        "environment_id": plan.environment_id,
        "generation": plan.generation,
        "policy": plan.policy,
        "resources": [_resource_payload(item) for item in plan.resources],
        "scope": plan.scope,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def build_cleanup_plan(
    *,
    environment_id: str,
    generation: int,
    scope: str,
    resources: Sequence[CleanupResource],
) -> CleanupPlan:
    if not isinstance(resources, Sequence) or isinstance(resources, (str, bytes)):
        raise CleanupError("cleanup resources have wrong type")
    draft = CleanupPlan(
        CLEANUP_POLICY, environment_id, generation, scope, tuple(resources), "0" * 64
    )
    plan = CleanupPlan(
        draft.policy, draft.environment_id, draft.generation, draft.scope,
        draft.resources, _plan_digest(draft),
    )
    validate_cleanup_plan(plan)
    return plan


def validate_cleanup_plan(plan: CleanupPlan) -> None:
    if type(plan) is not CleanupPlan or plan.policy != CLEANUP_POLICY:
        raise CleanupError("unsupported cleanup plan")
    if not isinstance(plan.environment_id, str) or not _SAFE_ID.fullmatch(plan.environment_id):
        raise CleanupError("invalid Environment identity")
    if type(plan.generation) is not int or plan.generation < 1:
        raise CleanupError("invalid Environment generation")
    if plan.scope not in SCOPES:
        raise CleanupError("unsupported cleanup scope")
    if not plan.resources or len(plan.resources) > 256:
        raise CleanupError("cleanup resource count is invalid")
    ids: list[str] = []
    kinds = {resource.kind for resource in plan.resources}
    for resource in plan.resources:
        if type(resource) is not CleanupResource:
            raise CleanupError("invalid cleanup resource")
        if not _SAFE_ID.fullmatch(resource.resource_id):
            raise CleanupError("unsafe cleanup resource identity")
        if resource.kind not in RESOURCE_KINDS:
            raise CleanupError("unsupported cleanup resource kind")
        if not _SHA256.fullmatch(resource.identity_digest):
            raise CleanupError("invalid cleanup identity digest")
        if resource.disposition not in DISPOSITIONS:
            raise CleanupError("invalid cleanup disposition")
        ids.append(resource.resource_id)
        if plan.scope == "complete-purge" and resource.disposition != "delete":
            raise CleanupError("complete purge cannot preserve listed Environment resources")
    if ids != sorted(ids) or len(ids) != len(set(ids)):
        raise CleanupError("cleanup resources are duplicate or non-canonical")
    required = {"root", "home", "account", "registration", "qgroup"}
    if not required.issubset(kinds):
        raise CleanupError("cleanup plan omits mandatory Environment resources")
    if not _SHA256.fullmatch(plan.plan_digest) or plan.plan_digest != _plan_digest(plan):
        raise CleanupError("cleanup plan digest mismatch")


def _evidence_digest(evidence: CleanupEvidence) -> str:
    encoded = json.dumps(asdict(evidence), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def assess_cleanup(
    plan: CleanupPlan,
    evidence: CleanupEvidence,
    *,
    approved: bool,
) -> CleanupAssessment:
    validate_cleanup_plan(plan)
    if type(evidence) is not CleanupEvidence or type(approved) is not bool:
        raise CleanupError("cleanup evidence or approval has wrong type")
    if not all(type(value) is bool for name, value in evidence.__dict__.items() if name not in {
        "observations", "free_bytes_before", "free_bytes_after"
    }):
        raise CleanupError("cleanup evidence boolean has wrong type")
    if any(type(value) is not int or value < 0 for value in (
        evidence.free_bytes_before, evidence.free_bytes_after
    )):
        raise CleanupError("cleanup capacity evidence is invalid")
    expected_ids = {item.resource_id for item in plan.resources}
    observations = {item.resource_id: item for item in evidence.observations}
    if len(observations) != len(evidence.observations) or set(observations) != expected_ids:
        raise CleanupError("cleanup observations do not exactly match the plan")
    for observation in evidence.observations:
        if type(observation) is not ResourceObservation or observation.state not in OBSERVED_STATES:
            raise CleanupError("invalid cleanup observation")
    digest = _evidence_digest(evidence)
    delete_resources = tuple(item for item in plan.resources if item.disposition == "delete")
    preserve_resources = tuple(item for item in plan.resources if item.disposition == "preserve")
    preserved_ids = tuple(item.resource_id for item in preserve_resources)
    if not approved:
        return CleanupAssessment(
            "awaiting-approval", 0, len(delete_resources), ("strong cleanup approval required",),
            preserved_ids, 0, False, digest,
        )
    identity_uncertain: list[str] = []
    for resource in plan.resources:
        observed = observations[resource.resource_id]
        if observed.state == "uncertain" or (
            observed.state != "absent" and observed.identity_digest != resource.identity_digest
        ):
            identity_uncertain.append(resource.resource_id)
    if identity_uncertain or not evidence.authoritative:
        pending = tuple(identity_uncertain) or ("authoritative cleanup evidence unavailable",)
        return CleanupAssessment(
            "preserved-uncertain", 0, len(delete_resources), pending, preserved_ids,
            max(0, evidence.free_bytes_after - evidence.free_bytes_before), False, digest,
        )
    safety = {
        "Environment is not stopped": evidence.stopped,
        "processes remain": evidence.processes_absent,
        "open file handles remain": evidence.open_handles_absent,
        "mounts remain": evidence.mounts_absent,
        "network state remains": evidence.network_absent,
        "quota accounting is inconsistent": evidence.quota_consistent,
        "a protected neighbor changed": evidence.protected_neighbors_unchanged,
    }
    failed = tuple(message for message, satisfied in safety.items() if not satisfied)
    if failed:
        return CleanupAssessment(
            "failed", 0, len(delete_resources), failed, preserved_ids,
            max(0, evidence.free_bytes_after - evidence.free_bytes_before), False, digest,
        )
    completed = sum(observations[item.resource_id].state == "absent" for item in delete_resources)
    pending_resources = tuple(
        item.resource_id for item in delete_resources
        if observations[item.resource_id].state != "absent"
    )
    freeing = any(
        observations[item.resource_id].state in {"deletion-requested", "under-deletion", "stale"}
        for item in delete_resources
    )
    account_and_registration_done = evidence.account_absent and evidence.registration_absent
    all_done = completed == len(delete_resources) and account_and_registration_done
    if all_done:
        state = "complete"
        pending = ()
    else:
        state = "freeing-space" if freeing else "deleting"
        pending = pending_resources
        if not evidence.account_absent:
            pending += ("internal account",)
        if not evidence.registration_absent:
            pending += ("Environment registration",)
    return CleanupAssessment(
        state,
        completed,
        len(delete_resources),
        pending,
        preserved_ids,
        max(0, evidence.free_bytes_after - evidence.free_bytes_before),
        state == "complete",
        digest,
    )


def render_cleanup_assessment(assessment: CleanupAssessment) -> str:
    labels = {
        "awaiting-approval": "A aguardar autorização",
        "deleting": "A eliminar recursos",
        "freeing-space": "A libertar espaço",
        "complete": "Limpeza concluída",
        "preserved-uncertain": "Preservado por segurança",
        "failed": "Limpeza interrompida",
    }
    lines = [
        "APX cleanup",
        f"Estado: {labels[assessment.state]}",
        f"Progresso: {assessment.progress_completed}/{assessment.progress_total}",
        f"Espaço recuperado observado: {assessment.reclaimed_bytes_observed} bytes",
    ]
    if assessment.pending:
        lines.append("Ainda pendente:")
        lines.extend(f"- {item}" for item in assessment.pending)
    if assessment.preserved:
        lines.append("Cópias preservadas:")
        lines.extend(f"- {item}" for item in assessment.preserved)
    lines.append("Identidade reutilizável: sim" if assessment.reusable_identity else "Identidade reutilizável: não")
    return "\n".join(lines)
