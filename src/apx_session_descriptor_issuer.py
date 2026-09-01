"""Trusted Host-side construction of closed APX desktop session actions."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json

from apx_desktop_session import PROFILE, parse_desktop_session
from apx_executor_contract import (
    ApprovalEvidence, ExecutorRequest, OperationPlan, RequesterContext,
)


class SessionDescriptorIssuerError(ValueError):
    pass


@dataclass(frozen=True)
class IssuedDesktopAction:
    action_id: str
    label: str
    plan: OperationPlan
    operation_id: str
    approval_id: str
    nonce: str


@dataclass(frozen=True)
class IssuedSessionBundle:
    descriptor: bytes
    plans: tuple[OperationPlan, ...]
    approvals: tuple[ApprovalEvidence, ...]
    requests: tuple[ExecutorRequest, ...]


def issue_session_descriptor(requester: RequesterContext,
                             actions: tuple[IssuedDesktopAction, ...], *,
                             issued_at: int, expires_at: int) -> IssuedSessionBundle:
    if type(requester) is not RequesterContext or not (
        requester.authenticated and requester.active and requester.authoritative
    ):
        raise SessionDescriptorIssuerError("trusted active session evidence is incomplete")
    if type(issued_at) is not int or type(expires_at) is not int or not issued_at < expires_at <= issued_at + 300:
        raise SessionDescriptorIssuerError("desktop action lifetime is invalid")
    if type(actions) is not tuple or not actions:
        raise SessionDescriptorIssuerError("desktop action catalogue is empty")
    requests: list[ExecutorRequest] = []
    approvals: list[ApprovalEvidence] = []
    rendered: list[dict[str, object]] = []
    for action in actions:
        if type(action) is not IssuedDesktopAction:
            raise SessionDescriptorIssuerError("desktop action has wrong type")
        plan = action.plan
        if requester.role in {"hub", "hub-graphical"}:
            if action.action_id != "activate" or plan.operation_kind != "activate":
                raise SessionDescriptorIssuerError("Hub switcher accepts only activate plans")
        elif (
            action.action_id != "return-to-hub" or plan.operation_kind != "stop"
            or plan.logical_name != requester.logical_name
            or plan.expected_generation != requester.generation
            or len(actions) != 1
        ):
            raise SessionDescriptorIssuerError("workload may receive only its own return action")
        request = ExecutorRequest(
            plan.schema_version, plan.protocol_version, action.operation_id,
            plan.operation_kind, plan.logical_name, plan.expected_generation,
            plan.plan_digest, action.approval_id, action.nonce, expires_at,
        )
        approval = ApprovalEvidence(
            action.approval_id, action.operation_id, plan.operation_kind,
            plan.logical_name, plan.expected_generation, plan.plan_digest,
            plan.consequence_digest, plan.required_approval_class,
            requester.session_id, action.nonce, issued_at, issued_at,
            expires_at, True,
        )
        requests.append(request); approvals.append(approval)
        rendered.append({"action_id": action.action_id, "label": action.label,
                         "request": asdict(request)})
    descriptor = (json.dumps({
        "profile": PROFILE, "session_id": requester.session_id,
        "active_environment": requester.logical_name, "role": requester.role,
        "actions": rendered,
    }, sort_keys=True, separators=(",", ":")) + "\n").encode()
    parse_desktop_session(descriptor)
    return IssuedSessionBundle(descriptor, tuple(action.plan for action in actions),
                               tuple(approvals), tuple(requests))
