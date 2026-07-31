"""Pure minimum-authority broker plan for exclusive APX graphical handoff."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import re


PROFILE = "apx-exclusive-graphical-broker-v1"
SEAT = "seat0"
RECOVERY_VT = 1
TRANSITION_VT = 2
MAX_HANDOFF_SECONDS = 30
_SHA = re.compile(r"[0-9a-f]{64}")


class GraphicalBrokerError(ValueError):
    pass


@dataclass(frozen=True)
class GraphicalBrokerEvidence:
    profile: str
    boot_id_digest: str
    seat: str
    hub_session_id: str
    hub_generation: int
    recovery_vt: int
    transition_vt: int
    recovery_console_verified: bool
    independent_watchdog_verified: bool
    typed_executor_endpoint_verified: bool
    single_graphical_owner_verified: bool
    no_uncertain_handoff: bool
    graphical_release_admitted: bool
    production_hub_client_admitted: bool
    mediated_device_adapter_verified: bool


@dataclass(frozen=True)
class GraphicalBrokerPlan:
    profile: str
    classification: str
    blockers: tuple[str, ...]
    seat: str
    recovery_vt: int
    transition_vt: int
    max_handoff_seconds: int
    authority: tuple[str, ...]
    effects: tuple[str, ...]
    forbidden_effects: tuple[str, ...]
    evidence_digest: str
    plan_digest: str


def build_broker_plan(evidence: GraphicalBrokerEvidence) -> GraphicalBrokerPlan:
    if type(evidence) is not GraphicalBrokerEvidence:
        raise GraphicalBrokerError("broker evidence has wrong type")
    if evidence.profile != PROFILE:
        raise GraphicalBrokerError("broker profile differs")
    if not _SHA.fullmatch(evidence.boot_id_digest):
        raise GraphicalBrokerError("boot identity digest is malformed")
    if type(evidence.hub_session_id) is not str or not evidence.hub_session_id or len(evidence.hub_session_id) > 80:
        raise GraphicalBrokerError("Hub session identity is malformed")
    if type(evidence.hub_generation) is not int or evidence.hub_generation <= 0:
        raise GraphicalBrokerError("Hub generation is malformed")
    if (evidence.seat, evidence.recovery_vt, evidence.transition_vt) != (SEAT, RECOVERY_VT, TRANSITION_VT):
        raise GraphicalBrokerError("seat or VT boundary differs from the fixed broker")

    gates = {
        "recovery console is unverified": evidence.recovery_console_verified,
        "independent watchdog is unverified": evidence.independent_watchdog_verified,
        "typed executor endpoint is unverified": evidence.typed_executor_endpoint_verified,
        "single graphical owner is unverified": evidence.single_graphical_owner_verified,
        "another handoff is uncertain": evidence.no_uncertain_handoff,
        "graphical release is not admitted": evidence.graphical_release_admitted,
        "production Hub client is not admitted": evidence.production_hub_client_admitted,
        "mediated device adapter is unverified": evidence.mediated_device_adapter_verified,
    }
    if any(type(value) is not bool for value in gates.values()):
        raise GraphicalBrokerError("broker gate has wrong type")
    blockers = tuple(message for message, passed in gates.items() if not passed)
    evidence_digest = hashlib.sha256(
        json.dumps(asdict(evidence), sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    draft = {
        "profile": PROFILE,
        "classification": "ready-for-fake-integration" if not blockers else "blocked",
        "blockers": blockers,
        "seat": SEAT,
        "recovery_vt": RECOVERY_VT,
        "transition_vt": TRANSITION_VT,
        "max_handoff_seconds": MAX_HANDOFF_SECONDS,
        "authority": (
            "show-fixed-transition-state", "own-transition-vt",
            "request-typed-executor-operation", "enter-fixed-recovery-state",
        ),
        "effects": (
            "verify-recovery-before-outgoing-stop",
            "show-transition-on-fixed-vt",
            "request-generation-bound-stop-and-activate",
            "reveal-incoming-only-after-readiness",
            "return-to-recovery-on-timeout-or-uncertainty",
        ),
        "forbidden_effects": (
            "execute-command-from-ui", "open-general-shell", "read-environment-data",
            "grant-device", "modify-registration", "force-stop", "reboot", "poweroff",
            "report-success-with-two-graphical-owners",
        ),
        "evidence_digest": evidence_digest,
    }
    plan_digest = hashlib.sha256(
        json.dumps(draft, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return GraphicalBrokerPlan(**draft, plan_digest=plan_digest)
