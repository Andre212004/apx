"""Pure guarded replacement plan from the headless Hub to the graphical Hub."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import re


PROFILE = "apx-graphical-hub-replacement-v1"
CURRENT_GENERATION = "d68ee7a2-268a-4534-b033-8f5313943fcf"
CURRENT_RELEASE = "hub-headless-v3"
TARGET_TEMPLATE = "hub-hyprland-v1"
TARGET_RELEASE = "hyprland-base-v1"
_SHA = re.compile(r"[0-9a-f]{64}")


class GraphicalHubReplacementError(ValueError):
    pass


@dataclass(frozen=True)
class GraphicalHubReplacementEvidence:
    current_generation: str
    current_release: str
    current_state: str
    current_home_bytes: int
    current_root_preservable: bool
    graphical_release_evidence_digest: str
    graphical_release_verified: bool
    recovery_v2_tests_passed: bool
    recovery_v2_non_graphical_rehearsal_passed: bool
    package_isolation_passed: bool
    disposable_graphical_environment_passed: bool
    hub_gtk_fake_executor_passed: bool
    hub_typed_executor_passed: bool
    exclusive_handoff_passed: bool
    tty1_recovery_verified: bool
    no_uncertain_apx_operation: bool


@dataclass(frozen=True)
class GraphicalHubReplacementPlan:
    profile: str
    classification: str
    blockers: tuple[str, ...]
    current_generation: str
    retained_release: str
    target_template: str
    target_release: str
    effects: tuple[str, ...]
    forbidden_effects: tuple[str, ...]
    evidence_digest: str
    plan_digest: str


def build_replacement_plan(evidence: GraphicalHubReplacementEvidence) -> GraphicalHubReplacementPlan:
    if type(evidence) is not GraphicalHubReplacementEvidence:
        raise GraphicalHubReplacementError("Hub replacement evidence has wrong type")
    blockers: list[str] = []
    if (evidence.current_generation, evidence.current_release, evidence.current_state) != (
        CURRENT_GENERATION, CURRENT_RELEASE, "stopped"
    ):
        blockers.append("current Hub identity or state changed")
    if type(evidence.current_home_bytes) is not int or evidence.current_home_bytes < 0:
        raise GraphicalHubReplacementError("current Hub home measurement is invalid")
    if evidence.current_home_bytes != 0:
        blockers.append("current Hub home requires an explicit migration decision")
    if not _SHA.fullmatch(evidence.graphical_release_evidence_digest):
        raise GraphicalHubReplacementError("graphical release evidence digest is malformed")
    gates = {
        "current Hub cannot be preserved": evidence.current_root_preservable,
        "graphical release is unverified": evidence.graphical_release_verified,
        "recovery v2 pure tests are incomplete": evidence.recovery_v2_tests_passed,
        "recovery v2 rehearsal is incomplete": evidence.recovery_v2_non_graphical_rehearsal_passed,
        "local package isolation is incomplete": evidence.package_isolation_passed,
        "disposable graphical gate is incomplete": evidence.disposable_graphical_environment_passed,
        "Hub fake-executor UI gate is incomplete": evidence.hub_gtk_fake_executor_passed,
        "Hub typed-executor gate is incomplete": evidence.hub_typed_executor_passed,
        "exclusive Hub handoff is incomplete": evidence.exclusive_handoff_passed,
        "tty1 recovery is unverified": evidence.tty1_recovery_verified,
        "APX has an uncertain operation": evidence.no_uncertain_apx_operation,
    }
    if any(type(value) is not bool for value in gates.values()):
        raise GraphicalHubReplacementError("Hub replacement gate is not boolean evidence")
    blockers.extend(message for message, passed in gates.items() if not passed)
    evidence_digest = hashlib.sha256(
        json.dumps(asdict(evidence), sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    draft = {
        "profile": PROFILE,
        "classification": "ready-for-separate-replacement-approval" if not blockers else "blocked",
        "blockers": tuple(blockers),
        "current_generation": CURRENT_GENERATION,
        "retained_release": CURRENT_RELEASE,
        "target_template": TARGET_TEMPLATE,
        "target_release": TARGET_RELEASE,
        "effects": (
            "create-separate-stopped-graphical-hub-candidate",
            "verify-candidate-without-changing-current-hub-registration",
            "snapshot-current-headless-hub-for-rollback",
            "atomically-publish-new-hub-generation",
            "retain-headless-hub-until-separate-retirement-approval",
        ),
        "forbidden_effects": (
            "delete-or-overwrite-current-hub",
            "copy-live-hub-root-into-new-generation",
            "activate-two-graphical-environments",
            "retire-headless-recovery-path",
            "replace-hub-with-any-unverified-release",
        ),
        "evidence_digest": evidence_digest,
    }
    digest = hashlib.sha256(json.dumps(draft, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return GraphicalHubReplacementPlan(**draft, plan_digest=digest)
