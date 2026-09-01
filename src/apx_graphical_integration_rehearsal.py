"""Effect-free integration of UI intents, typed executor, broker, and handoff."""

from __future__ import annotations

from dataclasses import dataclass

from apx_executor_contract import (
    ApprovalEvidence, ExecutorRequest, RequesterContext, assess_executor_request,
)
from apx_graphical_broker import GraphicalBrokerPlan
from apx_graphical_handoff import new_handoff, rehearse_handoff_cycle
from apx_hub_action_protocol import HubActionIntent


@dataclass(frozen=True)
class GraphicalIntegrationResult:
    classification: str
    open_executor_classification: str
    return_executor_classification: str
    handoff_classification: str
    final_phase: str
    final_seat_owner: str
    trace: tuple[str, ...]


class GraphicalIntegrationError(ValueError):
    pass


def assess_intent_for_rehearsal(intent: HubActionIntent, requester: RequesterContext, marker: str):
    """Assess one deterministic fake intent; marker is limited to a hex digit."""
    if marker not in "123456789abcdef":
        raise GraphicalIntegrationError("rehearsal marker is not a fixed hexadecimal digit")
    plan = intent.operation_plan
    operation_id = "op-" + marker * 32
    approval_id = "approval-" + marker * 32
    nonce = marker * 64
    request = ExecutorRequest(
        plan.schema_version, plan.protocol_version, operation_id,
        plan.operation_kind, plan.logical_name, plan.expected_generation,
        plan.plan_digest, approval_id, nonce, 200,
    )
    approval = ApprovalEvidence(
        approval_id, operation_id, plan.operation_kind, plan.logical_name,
        plan.expected_generation, plan.plan_digest, plan.consequence_digest,
        plan.required_approval_class, requester.session_id, nonce,
        100, 100, 200, True,
    )
    return assess_executor_request(
        request, plan, approval, current_generation=plan.expected_generation,
        current_time=150, current_session_id=requester.session_id,
        nonce_state="unused", authoritative_state="confirmed-compatible",
        requester_context=requester,
    )


def rehearse_typed_button_cycle(
    broker: GraphicalBrokerPlan,
    open_intent: HubActionIntent,
    return_intent: HubActionIntent,
    hub_requester: RequesterContext,
    workload_requester: RequesterContext,
) -> GraphicalIntegrationResult:
    if broker.classification != "ready-for-fake-integration":
        raise GraphicalIntegrationError("broker is not ready for fake integration")
    if open_intent.operation_kind != "activate":
        raise GraphicalIntegrationError("open button is not a typed activate intent")
    if return_intent.operation_kind != "stop":
        raise GraphicalIntegrationError("return button is not a typed stop intent")
    if (
        open_intent.target_logical_name != return_intent.target_logical_name
        or open_intent.target_generation != return_intent.target_generation
    ):
        raise GraphicalIntegrationError("open and return target generations differ")

    opened = assess_intent_for_rehearsal(open_intent, hub_requester, "1")
    returned = assess_intent_for_rehearsal(return_intent, workload_requester, "2")
    if opened.classification != "authorized-contract" or returned.classification != "authorized-contract":
        raise GraphicalIntegrationError("typed executor rejected a button intent")
    handoff = rehearse_handoff_cycle(new_handoff(
        "handoff-" + "3" * 64,
        hub_requester.generation,
        workload_requester.logical_name,
        workload_requester.generation,
    ))
    return GraphicalIntegrationResult(
        "passed-effect-free-integration",
        opened.classification,
        returned.classification,
        handoff.classification,
        handoff.final_phase,
        handoff.final_seat_owner,
        handoff.phases,
    )
