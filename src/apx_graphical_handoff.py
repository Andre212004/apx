"""Pure exclusive graphical handoff state machine for Hub and workloads."""

from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import json
import re

from apx_environment import validate_logical_name


PHASES = (
    "hub-active", "stopping-hub", "transition-to-workload",
    "starting-workload", "workload-active", "stopping-workload",
    "transition-to-hub", "starting-hub", "recovery",
)
EVENTS = (
    "request-open", "outgoing-stopped", "start-workload", "workload-ready",
    "request-return", "workload-stopped", "start-hub", "hub-ready", "fail",
)
_SHA = re.compile(r"[0-9a-f]{64}")


class GraphicalHandoffError(ValueError):
    pass


@dataclass(frozen=True)
class GraphicalHandoffRecord:
    operation_id: str
    hub_generation: int
    workload_logical_name: str
    workload_generation: int
    phase: str
    seat_owner: str
    recovery_verified: bool
    watchdog_active: bool
    outgoing_release_verified: bool
    incoming_readiness_verified: bool
    sequence: int
    previous_digest: str
    record_digest: str


@dataclass(frozen=True)
class GraphicalHandoffRehearsal:
    classification: str
    injected_failure_before: str | None
    phases: tuple[str, ...]
    final_phase: str
    final_seat_owner: str
    record_digest: str


def _digest(record: GraphicalHandoffRecord) -> str:
    value = {key: item for key, item in record.__dict__.items() if key != "record_digest"}
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def new_handoff(operation_id: str, hub_generation: int, workload_name: str,
                workload_generation: int) -> GraphicalHandoffRecord:
    if not operation_id.startswith("handoff-") or not _SHA.fullmatch(operation_id[8:]):
        raise GraphicalHandoffError("handoff operation ID is not canonical")
    if validate_logical_name(workload_name) is not None or workload_name == "hub":
        raise GraphicalHandoffError("workload Environment name is invalid")
    if any(type(value) is not int or value <= 0 for value in (hub_generation, workload_generation)):
        raise GraphicalHandoffError("handoff generation is invalid")
    draft = GraphicalHandoffRecord(
        operation_id, hub_generation, workload_name, workload_generation,
        "hub-active", "hub", False, False, False, False, 0, "0" * 64, "",
    )
    return replace(draft, record_digest=_digest(draft))


def advance_handoff(record: GraphicalHandoffRecord, event: str, *,
                    recovery_verified: bool | None = None,
                    watchdog_active: bool | None = None,
                    outgoing_release_verified: bool | None = None,
                    incoming_readiness_verified: bool | None = None) -> GraphicalHandoffRecord:
    if type(record) is not GraphicalHandoffRecord or record.phase not in PHASES:
        raise GraphicalHandoffError("handoff record is malformed")
    if record.record_digest != _digest(record):
        raise GraphicalHandoffError("handoff record digest differs")
    if event not in EVENTS:
        raise GraphicalHandoffError("unsupported handoff event")
    if record.phase == "recovery":
        raise GraphicalHandoffError("recovery is terminal for this handoff")

    updates = {
        "recovery_verified": record.recovery_verified if recovery_verified is None else recovery_verified,
        "watchdog_active": record.watchdog_active if watchdog_active is None else watchdog_active,
        "outgoing_release_verified": record.outgoing_release_verified if outgoing_release_verified is None else outgoing_release_verified,
        "incoming_readiness_verified": record.incoming_readiness_verified if incoming_readiness_verified is None else incoming_readiness_verified,
    }
    if any(type(value) is not bool for value in updates.values()):
        raise GraphicalHandoffError("handoff evidence has wrong type")

    # Release/readiness proofs belong to one transition and cannot be replayed
    # for the next outgoing or incoming graphical owner.
    if event in {"request-open", "request-return"}:
        updates["outgoing_release_verified"] = False
        updates["incoming_readiness_verified"] = False
    if event in {"start-workload", "start-hub"}:
        updates["incoming_readiness_verified"] = False

    if event == "fail":
        next_phase, seat_owner = "recovery", "broker"
    else:
        if record.phase != "hub-active" and not updates["watchdog_active"]:
            raise GraphicalHandoffError("handoff watchdog is no longer active")
        if record.phase != "hub-active" and not updates["recovery_verified"]:
            raise GraphicalHandoffError("handoff recovery path is no longer verified")
        transitions = {
            ("hub-active", "request-open"): ("stopping-hub", "hub"),
            ("stopping-hub", "outgoing-stopped"): ("transition-to-workload", "broker"),
            ("transition-to-workload", "start-workload"): ("starting-workload", "broker"),
            ("starting-workload", "workload-ready"): ("workload-active", record.workload_logical_name),
            ("workload-active", "request-return"): ("stopping-workload", record.workload_logical_name),
            ("stopping-workload", "workload-stopped"): ("transition-to-hub", "broker"),
            ("transition-to-hub", "start-hub"): ("starting-hub", "broker"),
            ("starting-hub", "hub-ready"): ("hub-active", "hub"),
        }
        try:
            next_phase, seat_owner = transitions[(record.phase, event)]
        except KeyError as error:
            raise GraphicalHandoffError("event is invalid for the current handoff phase") from error

        if event == "request-open" and not (updates["recovery_verified"] and updates["watchdog_active"]):
            raise GraphicalHandoffError("recovery and watchdog must be verified before Hub stop")
        if event == "outgoing-stopped" and not updates["outgoing_release_verified"]:
            raise GraphicalHandoffError("outgoing Hub release is not verified")
        if event in {"workload-ready", "hub-ready"} and not updates["incoming_readiness_verified"]:
            raise GraphicalHandoffError("incoming graphical readiness is not verified")
        if event == "workload-stopped" and not updates["outgoing_release_verified"]:
            raise GraphicalHandoffError("outgoing workload release is not verified")

    draft = replace(
        record, phase=next_phase, seat_owner=seat_owner, sequence=record.sequence + 1,
        previous_digest=record.record_digest, record_digest="", **updates,
    )
    return replace(draft, record_digest=_digest(draft))


def rehearse_handoff_cycle(record: GraphicalHandoffRecord, *,
                           fail_before: str | None = None) -> GraphicalHandoffRehearsal:
    """Exercise the button-to-state flow with no device, session, or host effect."""
    ordered = (
        ("request-open", {"recovery_verified": True, "watchdog_active": True}),
        ("outgoing-stopped", {"outgoing_release_verified": True}),
        ("start-workload", {}),
        ("workload-ready", {"incoming_readiness_verified": True}),
        ("request-return", {}),
        ("workload-stopped", {"outgoing_release_verified": True}),
        ("start-hub", {}),
        ("hub-ready", {"incoming_readiness_verified": True}),
    )
    if fail_before is not None and fail_before not in {event for event, _ in ordered}:
        raise GraphicalHandoffError("fake failure point is unsupported")
    phases = [record.phase]
    current = record
    for event, evidence in ordered:
        if event == fail_before:
            current = advance_handoff(current, "fail")
            phases.append(current.phase)
            return GraphicalHandoffRehearsal(
                "safe-recovery", fail_before, tuple(phases), current.phase,
                current.seat_owner, current.record_digest,
            )
        current = advance_handoff(current, event, **evidence)
        phases.append(current.phase)
    return GraphicalHandoffRehearsal(
        "passed-fake-cycle", None, tuple(phases), current.phase,
        current.seat_owner, current.record_digest,
    )
