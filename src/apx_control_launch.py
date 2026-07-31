"""Pure trusted-session decision for launching the role-aware APX control UI."""

from __future__ import annotations

from dataclasses import dataclass

from apx_environment import validate_logical_name
from apx_session_control import HUB_ROLES, ROLES


MODES = ("switcher", "management")


@dataclass(frozen=True)
class ControlLaunchEvidence:
    session_id: str
    session_authenticated: bool
    session_active: bool
    session_graphical: bool
    observed_logical_name: str
    observed_role: str
    observed_generation: int
    registration_logical_name: str
    registration_role: str
    registration_generation: int
    registration_verified: bool
    observation_authoritative: bool


@dataclass(frozen=True)
class ControlLaunchDecision:
    classification: str
    effective_mode: str | None
    argv: tuple[str, ...]
    issues: tuple[str, ...]


def decide_control_launch(mode: str, evidence: ControlLaunchEvidence) -> ControlLaunchDecision:
    """Fail closed unless active session facts exactly match verified registration."""
    issues: list[str] = []
    if mode not in MODES:
        issues.append("unsupported APX control mode")
    if not evidence.session_id or len(evidence.session_id) > 80:
        issues.append("session identity is malformed")
    if validate_logical_name(evidence.observed_logical_name) is not None:
        issues.append("observed Environment name is invalid")
    if evidence.observed_role not in ROLES:
        issues.append("observed Environment role is unsupported")
    elif (
        (evidence.observed_logical_name == "hub")
        != (evidence.observed_role in HUB_ROLES)
    ):
        issues.append("observed Hub identity and role are inconsistent")
    if type(evidence.observed_generation) is not int or evidence.observed_generation <= 0:
        issues.append("observed generation is malformed")
    if evidence.registration_logical_name != evidence.observed_logical_name:
        issues.append("active Environment does not match registration")
    if evidence.registration_role != evidence.observed_role:
        issues.append("active role does not match registration")
    if evidence.registration_generation != evidence.observed_generation:
        issues.append("active generation does not match registration")
    if evidence.session_authenticated is not True:
        issues.append("session is not authenticated")
    if evidence.session_active is not True or evidence.session_graphical is not True:
        issues.append("session is not the active graphical session")
    if evidence.registration_verified is not True:
        issues.append("Environment registration is not verified")
    if evidence.observation_authoritative is not True:
        issues.append("session observation is not authoritative")
    if mode == "management" and evidence.observed_role not in HUB_ROLES:
        issues.append("management mode is restricted to the Hub")

    if issues:
        return ControlLaunchDecision("rejected", None, (), tuple(dict.fromkeys(issues)))
    return ControlLaunchDecision(
        "launch-approved",
        mode,
        ("/usr/bin/apx-hub-ui", f"--{mode}", "--role", evidence.observed_role),
        (),
    )
