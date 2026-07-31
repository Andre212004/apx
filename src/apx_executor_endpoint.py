"""Typed production executor endpoint core with injected trusted authorities."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Callable

from apx_executor_contract import (
    ApprovalEvidence, ExecutorRequest, OperationPlan, RequesterContext,
    assess_executor_request, parse_executor_request_json,
)


@dataclass(frozen=True)
class AuthoritativeRequestState:
    current_generation: int | str
    current_time: int
    current_session_id: str
    nonce_state: str
    authoritative_state: str
    requester_context: RequesterContext


@dataclass(frozen=True)
class EffectResult:
    classification: str
    issues: tuple[str, ...]


@dataclass(frozen=True)
class EndpointAuthorities:
    load_plan: Callable[[str], OperationPlan]
    load_approval: Callable[[str], ApprovalEvidence]
    observe_state: Callable[[ExecutorRequest], AuthoritativeRequestState]
    reserve_nonce: Callable[[str, str], bool]
    apply_effects: Callable[[OperationPlan, str], EffectResult]


class ExecutorEndpointError(RuntimeError):
    pass


def _response(request: ExecutorRequest, classification: str,
              issues: tuple[str, ...], request_digest: str) -> bytes:
    value = {
        "schema_version": request.schema_version,
        "protocol_version": request.protocol_version,
        "operation_id": request.operation_id,
        "classification": classification,
        "issues": list(issues),
        "request_digest": request_digest,
    }
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def handle_executor_request(data: bytes, authorities: EndpointAuthorities) -> bytes:
    """Assess and apply one request; socket ownership/framing stays in the server."""
    if type(data) is not bytes:
        raise ExecutorEndpointError("executor endpoint input has wrong type")
    try:
        text = data.decode("utf-8")
        request = parse_executor_request_json(text)
    except (UnicodeDecodeError, ValueError) as error:
        raise ExecutorEndpointError("executor endpoint request is malformed") from error
    if type(authorities) is not EndpointAuthorities:
        raise ExecutorEndpointError("executor authorities have wrong type")
    try:
        plan = authorities.load_plan(request.plan_digest)
        approval = authorities.load_approval(request.approval_id)
        state = authorities.observe_state(request)
    except Exception as error:
        raise ExecutorEndpointError("trusted executor evidence is unavailable") from error
    if type(state) is not AuthoritativeRequestState:
        raise ExecutorEndpointError("trusted executor state has wrong type")
    assessment = assess_executor_request(
        request, plan, approval,
        current_generation=state.current_generation,
        current_time=state.current_time,
        current_session_id=state.current_session_id,
        nonce_state=state.nonce_state,
        authoritative_state=state.authoritative_state,
        requester_context=state.requester_context,
    )
    if assessment.classification != "authorized-contract":
        return _response(request, "rejected", assessment.issues, assessment.request_digest)
    try:
        reserved = authorities.reserve_nonce(request.nonce, assessment.request_digest)
    except Exception as error:
        raise ExecutorEndpointError("nonce authority is unavailable") from error
    if reserved is not True:
        return _response(
            request, "rejected", ("nonce could not be atomically reserved",),
            assessment.request_digest,
        )
    try:
        result = authorities.apply_effects(plan, assessment.request_digest)
    except Exception:
        return _response(
            request, "incomplete", ("typed effect adapter failed after nonce reservation",),
            assessment.request_digest,
        )
    if type(result) is not EffectResult or result.classification not in {"accepted", "incomplete"}:
        return _response(
            request, "incomplete", ("typed effect adapter returned invalid evidence",),
            assessment.request_digest,
        )
    if result.classification == "accepted" and result.issues:
        return _response(
            request, "incomplete", ("typed effect adapter returned contradictory success",),
            assessment.request_digest,
        )
    return _response(request, result.classification, result.issues, assessment.request_digest)
