"""Pure contract for installing APX beside an existing desktop safely."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Sequence


INSTALLATION_POLICY = "parallel-installation-v1"
PHASES = (
    "inventory",
    "backup-verified",
    "parallel-bootstrap",
    "headless-validated",
    "graphical-validated",
    "cutover-eligible",
    "legacy-cleanup-eligible",
)


@dataclass(frozen=True)
class InstallationPlan:
    policy: str
    phases: tuple[str, ...]
    invariants: tuple[str, ...]
    recovery_requirements: tuple[str, ...]
    cleanup_exclusions: tuple[str, ...]
    digest: str


@dataclass(frozen=True)
class InstallationEvidence:
    project_pushed: bool
    personal_backup_verified: bool
    recovery_media_verified: bool
    current_desktop_preserved: bool
    headless_environment_passed: bool
    two_environment_isolation_passed: bool
    graphical_hub_passed: bool
    graphical_handoff_passed: bool
    package_isolation_passed: bool
    destructive_recovery_passed: bool
    authoritative: bool


@dataclass(frozen=True)
class InstallationAssessment:
    current_phase: str
    decision: str
    blockers: tuple[str, ...]
    allowed_next_actions: tuple[str, ...]
    plan_digest: str


INVARIANTS = (
    "the current working graphical desktop remains available through parallel validation",
    "APX never reuses or modifies the manually created apx-trial candidate",
    "Hub and workload Environments receive no development repository or credentials",
    "no legacy package or desktop cleanup is bundled with APX bootstrap or cutover",
    "every host mutation has a bounded preview, approval, journal, and postcondition",
    "a failed validation returns to the current desktop without deleting evidence",
)

RECOVERY_REQUIREMENTS = (
    "project history exists on a separately reachable remote",
    "personal backup has been restored in a disposable verification context",
    "Arch recovery media boots and can access the installation storage",
    "the current display manager entry remains selectable before cutover",
    "APX failure leaves a documented non-APX login and repair path",
)

CLEANUP_EXCLUSIONS = (
    "personal files and unclassified home content",
    "APX source history and recovery material",
    "bootloader, kernel, firmware, networking, authentication, and storage tooling",
    "the current desktop until graphical APX and rollback acceptance gates pass",
    "any package whose ownership or dependency purpose is unconfirmed",
)


def _plan_payload() -> dict[str, object]:
    return {
        "cleanup_exclusions": CLEANUP_EXCLUSIONS,
        "invariants": INVARIANTS,
        "phases": PHASES,
        "policy": INSTALLATION_POLICY,
        "recovery_requirements": RECOVERY_REQUIREMENTS,
    }


def build_installation_plan() -> InstallationPlan:
    canonical = json.dumps(_plan_payload(), sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return InstallationPlan(
        policy=INSTALLATION_POLICY,
        phases=PHASES,
        invariants=INVARIANTS,
        recovery_requirements=RECOVERY_REQUIREMENTS,
        cleanup_exclusions=CLEANUP_EXCLUSIONS,
        digest=digest,
    )


def assess_installation(evidence: InstallationEvidence) -> InstallationAssessment:
    plan = build_installation_plan()
    if type(evidence) is not InstallationEvidence:
        return InstallationAssessment(
            "inventory", "blocked", ("installation evidence has wrong type",), (), plan.digest
        )
    if not all(type(value) is bool for value in evidence.__dict__.values()):
        return InstallationAssessment(
            "inventory", "blocked", ("installation evidence is malformed",), (), plan.digest
        )

    blockers: list[str] = []
    if not evidence.project_pushed:
        blockers.append("project history is not backed up remotely")
    if not evidence.current_desktop_preserved:
        blockers.append("current graphical recovery path is not preserved")
    if blockers:
        return InstallationAssessment("inventory", "blocked", tuple(blockers), (), plan.digest)

    if not evidence.personal_backup_verified or not evidence.recovery_media_verified:
        if not evidence.personal_backup_verified:
            blockers.append("personal backup has not been restore-tested")
        if not evidence.recovery_media_verified:
            blockers.append("Arch recovery media has not been boot-tested")
        return InstallationAssessment(
            "backup-verified",
            "waiting",
            tuple(blockers),
            ("verify backup restoration", "boot-test recovery media"),
            plan.digest,
        )

    if not evidence.headless_environment_passed:
        return InstallationAssessment(
            "parallel-bootstrap",
            "eligible-for-bounded-headless-test" if evidence.authoritative else "waiting",
            () if evidence.authoritative else ("host evidence is not authoritative",),
            ("run one bounded headless Environment test",),
            plan.digest,
        )

    if not evidence.two_environment_isolation_passed:
        return InstallationAssessment(
            "headless-validated",
            "eligible-for-isolation-test",
            ("two-Environment isolation has not passed",),
            ("run hostile two-Environment denial tests",),
            plan.digest,
        )

    graphical_missing = not (
        evidence.graphical_hub_passed and evidence.graphical_handoff_passed
    )
    if graphical_missing:
        return InstallationAssessment(
            "headless-validated",
            "eligible-for-parallel-graphical-test",
            ("Hub or graphical handoff has not passed",),
            ("install and test APX graphical session beside the current desktop",),
            plan.digest,
        )

    if not evidence.package_isolation_passed:
        return InstallationAssessment(
            "graphical-validated",
            "eligible-for-package-isolation-test",
            ("application installation isolation has not passed",),
            ("install a test application in exactly one disposable Environment",),
            plan.digest,
        )

    if not evidence.destructive_recovery_passed:
        return InstallationAssessment(
            "cutover-eligible",
            "cutover-allowed-cleanup-forbidden",
            ("destructive recovery and cleanup have not passed",),
            ("offer APX as default while preserving the current desktop",),
            plan.digest,
        )

    return InstallationAssessment(
        "legacy-cleanup-eligible",
        "cleanup-review-only",
        ("legacy cleanup still requires a separate package-by-package approval",),
        ("render classified legacy cleanup preview",),
        plan.digest,
    )


def render_installation_assessment(assessment: InstallationAssessment) -> str:
    lines = [
        "APX installation path",
        f"Current phase: {assessment.current_phase}",
        f"Decision: {assessment.decision}",
    ]
    if assessment.blockers:
        lines.append("What still blocks progress:")
        lines.extend(f"- {item}" for item in assessment.blockers)
    if assessment.allowed_next_actions:
        lines.append("Safe next actions:")
        lines.extend(f"- {item}" for item in assessment.allowed_next_actions)
    lines.extend((
        "KDE removal: not authorized by this assessment",
        f"Plan digest: {assessment.plan_digest}",
    ))
    return "\n".join(lines)
