"""Pure final gate for the first bounded APX Stage 2 host experiment."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import re


_SHA256 = re.compile(r"[0-9a-f]{64}")
GATE_POLICY = "stage2-final-gate-v1"


@dataclass(frozen=True)
class Stage2Evidence:
    dossier_digest: str
    acquisition_plan_digest: str
    snapshot_assessment: str
    snapshot_assessment_digest: str
    trust_seal_state: str
    trust_seal_digest: str
    trust_seal_plan_digest: str
    capacity_decision: str
    capacity_evidence_digest: str
    intended_identities_absent: bool
    parent_identities_verified: bool
    subordinate_ids_verified: bool
    quota_hierarchy_verified: bool
    host_invariants_captured: bool
    network_acquisition_approved: bool
    approval_authenticated: bool
    approval_unexpired: bool
    approval_unused: bool
    journal_store_authoritative: bool
    cleanup_separately_scoped: bool


@dataclass(frozen=True)
class Stage2GateDecision:
    policy: str
    decision: str
    blockers: tuple[str, ...]
    allowed_effects: tuple[str, ...]
    evidence_digest: str


ALLOWED_EFFECTS = (
    "bounded fixed-origin acquisition into operation-owned staging",
    "publish verified immutable base evidence",
    "create one unpublished isolation-trial root and home",
    "apply the fixed Stage 2 quota hierarchy and limits",
    "publish isolation-trial registration only after every postcondition",
)


def _digest(evidence: Stage2Evidence) -> str:
    canonical = json.dumps(asdict(evidence), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def assess_stage2_gate(
    evidence: Stage2Evidence,
    *,
    expected_dossier_digest: str,
    expected_acquisition_plan_digest: str,
) -> Stage2GateDecision:
    blockers: list[str] = []
    if type(evidence) is not Stage2Evidence:
        return Stage2GateDecision(
            GATE_POLICY,
            "blocked",
            ("Stage 2 evidence has wrong type",),
            (),
            "0" * 64,
        )
    digest_fields = (
        "dossier_digest",
        "acquisition_plan_digest",
        "snapshot_assessment_digest",
        "trust_seal_digest",
        "trust_seal_plan_digest",
        "capacity_evidence_digest",
    )
    for name in digest_fields:
        if not isinstance(getattr(evidence, name), str) or not _SHA256.fullmatch(getattr(evidence, name)):
            blockers.append(f"{name} is malformed")
    if not _SHA256.fullmatch(expected_dossier_digest):
        blockers.append("expected dossier digest is malformed")
    elif evidence.dossier_digest != expected_dossier_digest:
        blockers.append("evidence does not match the approved dossier")
    if not _SHA256.fullmatch(expected_acquisition_plan_digest):
        blockers.append("expected acquisition plan digest is malformed")
    else:
        if evidence.acquisition_plan_digest != expected_acquisition_plan_digest:
            blockers.append("snapshot evidence does not match the acquisition plan")
        if evidence.trust_seal_plan_digest != expected_acquisition_plan_digest:
            blockers.append("trust evidence does not match the acquisition plan")
    if evidence.snapshot_assessment != "verified":
        blockers.append("base snapshot assessment is not verified")
    if evidence.trust_seal_state != "verified":
        blockers.append("host trust evidence is not authoritatively verified")
    if evidence.capacity_decision != "ready-for-stage2-capacity-gate":
        blockers.append("storage capacity gate is not ready")

    boolean_requirements = (
        ("intended_identities_absent", "an intended account, path, machine, image, marker, or registration may exist"),
        ("parent_identities_verified", "storage parent identities are not verified"),
        ("subordinate_ids_verified", "subordinate UID/GID allocation is not verified"),
        ("quota_hierarchy_verified", "Stage 2 quota hierarchy is not verified"),
        ("host_invariants_captured", "pre-operation host invariants are not captured"),
        ("network_acquisition_approved", "bounded network acquisition is not approved"),
        ("approval_authenticated", "human approval is not authenticated"),
        ("approval_unexpired", "human approval is expired"),
        ("approval_unused", "human approval or nonce was already used"),
        ("journal_store_authoritative", "operation journal is not authoritative"),
        ("cleanup_separately_scoped", "creation and cleanup authority are not separated"),
    )
    for field, message in boolean_requirements:
        value = getattr(evidence, field)
        if type(value) is not bool:
            blockers.append(f"{field} has wrong type")
        elif not value:
            blockers.append(message)

    digest = _digest(evidence)
    if blockers:
        return Stage2GateDecision(GATE_POLICY, "blocked", tuple(blockers), (), digest)
    return Stage2GateDecision(
        GATE_POLICY,
        "ready-for-separate-stage2-execution-approval",
        (),
        ALLOWED_EFFECTS,
        digest,
    )


def render_stage2_gate(decision: Stage2GateDecision) -> str:
    lines = [
        "APX first real Environment gate",
        f"Decision: {decision.decision}",
    ]
    if decision.blockers:
        lines.append("Still required:")
        lines.extend(f"- {blocker}" for blocker in decision.blockers)
    if decision.allowed_effects:
        lines.append("Exact effects eligible for a separate approval:")
        lines.extend(f"- {effect}" for effect in decision.allowed_effects)
    lines.extend((
        "Graphical Environment: not included in Stage 2",
        "KDE removal: not included",
        "Cleanup: separate approval only",
        f"Evidence digest: {decision.evidence_digest}",
    ))
    return "\n".join(lines)
