"""Pure conversion of reviewed Hub controls into typed executor plan intents."""

from __future__ import annotations

from dataclasses import dataclass

from apx_executor_contract import OperationPlan, RequesterContext, build_operation_plan
from apx_hub import HubAction


ACTION_TO_OPERATION = {
    "open": "activate",
    "capabilities": "configure-capabilities",
    "snapshot": "snapshot",
    "archive": "archive",
    "destroy": "destroy",
    "recover": "recover-complete",
}


class HubActionProtocolError(ValueError):
    pass


@dataclass(frozen=True)
class HubActionIntent:
    action_id: str
    requester_logical_name: str
    requester_role: str
    target_logical_name: str
    target_generation: int | str
    operation_kind: str
    approval_class: str
    consequence_digest: str
    plan_digest: str
    operation_plan: OperationPlan


def build_hub_action_intent(action: HubAction, requester: RequesterContext,
                            target_logical_name: str,
                            target_generation: int | str) -> HubActionIntent:
    if type(action) is not HubAction:
        raise HubActionProtocolError("Hub action has wrong type")
    if not action.enabled:
        raise HubActionProtocolError("disabled Hub action cannot create an executor intent")
    expected_operation = ACTION_TO_OPERATION.get(action.action_id)
    if expected_operation is None or action.request_kind != expected_operation:
        raise HubActionProtocolError("Hub action is not bound to its fixed executor operation")
    if (requester.logical_name, requester.role) not in {
        ("hub", "hub"), ("hub", "hub-graphical")
    }:
        raise HubActionProtocolError("executor intent requires the canonical active Hub")
    if not (requester.authenticated and requester.active and requester.authoritative):
        raise HubActionProtocolError("Hub requester evidence is incomplete")
    plan = build_operation_plan(expected_operation, target_logical_name, target_generation)
    if action.approval_class != plan.required_approval_class:
        raise HubActionProtocolError("Hub action approval differs from executor policy")
    return HubActionIntent(
        action.action_id, requester.logical_name, requester.role,
        target_logical_name, target_generation, expected_operation,
        plan.required_approval_class, plan.consequence_digest, plan.plan_digest,
        plan,
    )


def build_workload_return_intent(requester: RequesterContext) -> HubActionIntent:
    if requester.role in {"hub", "hub-graphical"}:
        raise HubActionProtocolError("Hub does not use the workload return control")
    if not (requester.authenticated and requester.active and requester.authoritative):
        raise HubActionProtocolError("workload requester evidence is incomplete")
    plan = build_operation_plan("stop", requester.logical_name, requester.generation)
    return HubActionIntent(
        "return-to-hub", requester.logical_name, requester.role,
        requester.logical_name, requester.generation, "stop",
        plan.required_approval_class, plan.consequence_digest, plan.plan_digest,
        plan,
    )
