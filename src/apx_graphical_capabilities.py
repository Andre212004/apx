"""Pure Hub-only plan for optional graphical Environment capabilities."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

from apx_environment import validate_logical_name
from apx_graphical_template import ESSENTIAL_CAPABILITIES, OPTIONAL_CAPABILITIES


PROFILE = "apx-graphical-capability-change-v1"


class GraphicalCapabilityError(ValueError):
    pass


@dataclass(frozen=True)
class CapabilityChangeEvidence:
    requester_logical_name: str
    requester_role: str
    requester_authenticated: bool
    requester_active: bool
    requester_authoritative: bool
    target_logical_name: str
    target_generation: int
    target_state: str
    current_optional_capabilities: tuple[str, ...]
    requested_optional_capabilities: tuple[str, ...]
    no_uncertain_operation: bool


@dataclass(frozen=True)
class CapabilityChangePlan:
    profile: str
    classification: str
    blockers: tuple[str, ...]
    target_logical_name: str
    target_generation: int
    retained_essential_capabilities: tuple[str, ...]
    current_optional_capabilities: tuple[str, ...]
    requested_optional_capabilities: tuple[str, ...]
    added: tuple[str, ...]
    removed: tuple[str, ...]
    approval_class: str
    effects: tuple[str, ...]
    forbidden_effects: tuple[str, ...]
    plan_digest: str


def _validate_selection(value: tuple[str, ...], label: str) -> None:
    if type(value) is not tuple or any(type(item) is not str for item in value):
        raise GraphicalCapabilityError(f"{label} capability selection has wrong type")
    if value != tuple(sorted(set(value))):
        raise GraphicalCapabilityError(f"{label} capability selection is not canonical")
    if not set(value) <= set(OPTIONAL_CAPABILITIES):
        raise GraphicalCapabilityError(f"{label} capability selection contains an unsupported capability")


def build_capability_change_plan(evidence: CapabilityChangeEvidence) -> CapabilityChangePlan:
    if type(evidence) is not CapabilityChangeEvidence:
        raise GraphicalCapabilityError("capability evidence has wrong type")
    if validate_logical_name(evidence.target_logical_name) is not None:
        raise GraphicalCapabilityError("target Environment name is invalid")
    if type(evidence.target_generation) is not int or evidence.target_generation <= 0:
        raise GraphicalCapabilityError("target generation is invalid")
    _validate_selection(evidence.current_optional_capabilities, "current")
    _validate_selection(evidence.requested_optional_capabilities, "requested")

    blockers: list[str] = []
    if (evidence.requester_logical_name, evidence.requester_role) not in {
        ("hub", "hub"), ("hub", "hub-graphical")
    }:
        blockers.append("capability changes are restricted to the canonical Hub")
    if evidence.requester_authenticated is not True:
        blockers.append("Hub session is not authenticated")
    if evidence.requester_active is not True:
        blockers.append("Hub session is not active")
    if evidence.requester_authoritative is not True:
        blockers.append("Hub session evidence is not authoritative")
    if evidence.target_state != "stopped":
        blockers.append("target Environment must be stopped")
    if evidence.no_uncertain_operation is not True:
        blockers.append("APX has an uncertain operation")

    current = set(evidence.current_optional_capabilities)
    requested = set(evidence.requested_optional_capabilities)
    draft = {
        "profile": PROFILE,
        "classification": "ready-for-explicit-confirmation" if not blockers else "blocked",
        "blockers": tuple(blockers),
        "target_logical_name": evidence.target_logical_name,
        "target_generation": evidence.target_generation,
        "retained_essential_capabilities": ESSENTIAL_CAPABILITIES,
        "current_optional_capabilities": evidence.current_optional_capabilities,
        "requested_optional_capabilities": evidence.requested_optional_capabilities,
        "added": tuple(sorted(requested - current)),
        "removed": tuple(sorted(current - requested)),
        "approval_class": "explicit-confirmation",
        "effects": (
            "write-new-generation-bound-capability-policy",
            "verify-optional-device-policy-before-next-activation",
            "atomically-publish-capability-policy",
        ),
        "forbidden_effects": (
            "activate-target-environment",
            "change-essential-capabilities",
            "grant-device-to-running-environment",
            "modify-host-device-ownership",
            "modify-another-environment-policy",
        ),
    }
    digest = hashlib.sha256(
        json.dumps(draft, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return CapabilityChangePlan(**draft, plan_digest=digest)
