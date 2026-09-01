"""Pure guarded cutover from the disposable graphical Hub to official headless Hub."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json


PROFILE = "apx-official-hub-cutover-v1"
OLD_GENERATION = "2c3dbacc-106f-4053-8603-f649552f5513"
OLD_RELEASE = "hyprland-base-v1"
NEW_RELEASE = "hub-headless-v4"
TEST_NAME = "hub-testes"


class OfficialHubCutoverError(ValueError):
    pass


@dataclass(frozen=True)
class OfficialHubCutoverEvidence:
    current_generation: str
    current_release: str
    current_role: str
    current_stopped: bool
    hub_testes_absent: bool
    official_candidate_ready: bool
    official_release_manifest_digest: str
    tty1_active: bool
    no_running_machines: bool
    no_uncertain_operation: bool
    rollback_paths_available: bool


@dataclass(frozen=True)
class OfficialHubCutoverPlan:
    profile: str
    classification: str
    blockers: tuple[str, ...]
    effects: tuple[str, ...]
    forbidden_effects: tuple[str, ...]
    plan_digest: str


def build_cutover_plan(evidence: OfficialHubCutoverEvidence) -> OfficialHubCutoverPlan:
    if type(evidence) is not OfficialHubCutoverEvidence:
        raise OfficialHubCutoverError("Hub cutover evidence has wrong type")
    if len(evidence.official_release_manifest_digest) != 64 or any(
        character not in "0123456789abcdef"
        for character in evidence.official_release_manifest_digest
    ):
        raise OfficialHubCutoverError("official release manifest digest is malformed")
    booleans = (
        evidence.current_stopped, evidence.hub_testes_absent,
        evidence.official_candidate_ready, evidence.tty1_active,
        evidence.no_running_machines, evidence.no_uncertain_operation,
        evidence.rollback_paths_available,
    )
    if any(type(value) is not bool for value in booleans):
        raise OfficialHubCutoverError("Hub cutover gate is not boolean")
    blockers: list[str] = []
    if (
        evidence.current_generation, evidence.current_release, evidence.current_role
    ) != (OLD_GENERATION, OLD_RELEASE, "hub-graphical"):
        blockers.append("current graphical Hub identity changed")
    gates = (
        ("current graphical Hub is not stopped", evidence.current_stopped),
        ("hub-testes destination already exists", evidence.hub_testes_absent),
        ("official Hub candidate is not ready", evidence.official_candidate_ready),
        ("tty1 recovery console is not active", evidence.tty1_active),
        ("an Environment machine is running", evidence.no_running_machines),
        ("an uncertain APX operation exists", evidence.no_uncertain_operation),
        ("rollback paths are unavailable", evidence.rollback_paths_available),
    )
    blockers.extend(label for label, passed in gates if not passed)
    effects = (
        "journal-prepared-cutover",
        "rename-current-hub-to-hub-testes",
        "reclassify-hub-testes-as-graphical-base",
        "rename-official-candidate-to-hub",
        "publish-new-headless-hub-registration",
        "journal-complete-cutover",
    )
    forbidden = (
        "delete-current-hub-root-or-home", "delete-existing-test",
        "copy-current-hub-into-official-hub", "grant-hub-authority-to-hub-testes",
        "start-graphical-session", "install-hyprland-or-terminal",
    )
    payload = {
        "profile": PROFILE, "old_generation": OLD_GENERATION,
        "old_release": OLD_RELEASE, "new_release": NEW_RELEASE,
        "test_name": TEST_NAME, "manifest_digest": evidence.official_release_manifest_digest,
        "effects": effects, "forbidden": forbidden,
    }
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return OfficialHubCutoverPlan(
        profile=PROFILE,
        classification="ready-for-cutover" if not blockers else "blocked",
        blockers=tuple(blockers), effects=effects,
        forbidden_effects=forbidden, plan_digest=digest,
    )
