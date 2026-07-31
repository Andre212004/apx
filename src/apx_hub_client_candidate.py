"""Pure pre-freeze gate for a future production APX Hub graphical client."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import re

PROFILE = "apx-hub-client-candidate-v1"
REQUIRED_PACKAGES = ("gtk4", "libadwaita", "python-gobject")
_SHA = re.compile(r"[0-9a-f]{64}")


class HubClientCandidateError(ValueError):
    pass


@dataclass(frozen=True)
class HubClientCandidateEvidence:
    profile: str
    package_names: tuple[str, ...]
    first_artifact_digest: str
    second_artifact_digest: str
    source_reviewed: bool
    no_privileged_effect_adapter: bool
    no_arbitrary_command_or_path: bool
    role_derived_by_trusted_launcher: bool
    workload_management_refusal_passed: bool
    fake_executor_suite_passed: bool
    typed_executor_suite_passed: bool
    accessibility_keyboard_passed: bool
    deterministic_build_passed: bool


@dataclass(frozen=True)
class HubClientCandidateAssessment:
    classification: str
    blockers: tuple[str, ...]
    candidate_digest: str
    next_step: str


def assess_candidate(evidence: HubClientCandidateEvidence) -> HubClientCandidateAssessment:
    if type(evidence) is not HubClientCandidateEvidence:
        raise HubClientCandidateError("Hub client candidate evidence has wrong type")
    if evidence.profile != PROFILE:
        raise HubClientCandidateError("Hub client candidate profile differs")
    if evidence.package_names != REQUIRED_PACKAGES:
        raise HubClientCandidateError("Hub client package set differs from the closed runtime")
    for digest in (evidence.first_artifact_digest, evidence.second_artifact_digest):
        if type(digest) is not str or not _SHA.fullmatch(digest):
            raise HubClientCandidateError("Hub client artifact digest is malformed")

    blockers: list[str] = []
    if evidence.first_artifact_digest != evidence.second_artifact_digest:
        blockers.append("independent Hub client builds differ")
    gates = {
        "source review is incomplete": evidence.source_reviewed,
        "client contains or reaches a privileged effect adapter": evidence.no_privileged_effect_adapter,
        "client accepts an arbitrary command or path": evidence.no_arbitrary_command_or_path,
        "role is not derived by the trusted launcher": evidence.role_derived_by_trusted_launcher,
        "workload management refusal is unverified": evidence.workload_management_refusal_passed,
        "fake-executor suite is incomplete": evidence.fake_executor_suite_passed,
        "typed-executor suite is incomplete": evidence.typed_executor_suite_passed,
        "keyboard and accessibility gate is incomplete": evidence.accessibility_keyboard_passed,
        "deterministic build gate is incomplete": evidence.deterministic_build_passed,
    }
    if any(type(value) is not bool for value in gates.values()):
        raise HubClientCandidateError("Hub client candidate gate has wrong type")
    blockers.extend(message for message, passed in gates.items() if not passed)
    digest = hashlib.sha256(
        json.dumps(asdict(evidence), sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return HubClientCandidateAssessment(
        "ready-for-separate-manifest-freeze" if not blockers else "blocked",
        tuple(blockers),
        digest,
        "freeze-reviewed-artifact-in-a-new-hub-overlay-manifest" if not blockers else "complete-blocking-evidence",
    )
