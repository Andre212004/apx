from dataclasses import replace
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import apx_executor_client as client
import apx_executor_contract as contract
import apx_executor_endpoint as endpoint


def subject():
    plan = contract.build_operation_plan("activate", "development", 7)
    request = contract.ExecutorRequest(
        1, contract.PROTOCOL_VERSION, "op-" + "1" * 32, "activate",
        "development", 7, plan.plan_digest, "approval-" + "2" * 32,
        "3" * 64, 200,
    )
    requester = contract.RequesterContext(
        "session-" + "4" * 32, "hub", "hub-graphical", 3, True, True, True,
    )
    approval = contract.ApprovalEvidence(
        request.approval_id, request.operation_id, request.operation_kind,
        request.logical_name, request.expected_generation, request.plan_digest,
        plan.consequence_digest, plan.required_approval_class,
        requester.session_id, request.nonce, 100, 100, 200, True,
    )
    state = endpoint.AuthoritativeRequestState(
        7, 150, requester.session_id, "unused", "confirmed-compatible", requester,
    )
    authorities = endpoint.EndpointAuthorities(
        Mock(return_value=plan), Mock(return_value=approval), Mock(return_value=state),
        Mock(return_value=True), Mock(return_value=endpoint.EffectResult("accepted", ())),
    )
    return plan, request, approval, state, authorities


class ExecutorEndpointTests(unittest.TestCase):
    def test_authorized_request_reserves_nonce_then_applies_fixed_plan(self) -> None:
        plan, request, _, _, authorities = subject()
        raw = endpoint.handle_executor_request(contract.request_to_json(request).encode(), authorities)
        response = client.parse_executor_response(raw, request)
        self.assertEqual(response.classification, "accepted")
        authorities.reserve_nonce.assert_called_once_with(request.nonce, response.request_digest)
        authorities.apply_effects.assert_called_once_with(plan, response.request_digest)

    def test_contract_rejection_never_reserves_nonce_or_applies_effect(self) -> None:
        _, request, _, state, authorities = subject()
        authorities.observe_state.return_value = replace(state, requester_context=replace(
            state.requester_context, logical_name="games",
        ))
        raw = endpoint.handle_executor_request(contract.request_to_json(request).encode(), authorities)
        self.assertEqual(client.parse_executor_response(raw, request).classification, "rejected")
        authorities.reserve_nonce.assert_not_called()
        authorities.apply_effects.assert_not_called()

    def test_nonce_race_rejects_before_effect(self) -> None:
        _, request, _, _, authorities = subject()
        authorities.reserve_nonce.return_value = False
        raw = endpoint.handle_executor_request(contract.request_to_json(request).encode(), authorities)
        response = client.parse_executor_response(raw, request)
        self.assertEqual(response.classification, "rejected")
        self.assertIn("atomically reserved", response.issues[0])
        authorities.apply_effects.assert_not_called()

    def test_effect_failure_or_invalid_success_becomes_incomplete(self) -> None:
        _, request, _, _, authorities = subject()
        variants = (
            RuntimeError("adapter crashed"),
            endpoint.EffectResult("accepted", ("contradiction",)),
            endpoint.EffectResult("caller-result", ()),
        )
        for value in variants:
            _, request, _, _, authorities = subject()
            if isinstance(value, Exception):
                authorities.apply_effects.side_effect = value
            else:
                authorities.apply_effects.return_value = value
            raw = endpoint.handle_executor_request(contract.request_to_json(request).encode(), authorities)
            self.assertEqual(client.parse_executor_response(raw, request).classification, "incomplete")

    def test_missing_trusted_evidence_and_malformed_request_raise_without_effect(self) -> None:
        _, request, _, _, authorities = subject()
        authorities.load_plan.side_effect = KeyError("absent")
        with self.assertRaises(endpoint.ExecutorEndpointError):
            endpoint.handle_executor_request(contract.request_to_json(request).encode(), authorities)
        authorities.apply_effects.assert_not_called()
        with self.assertRaises(endpoint.ExecutorEndpointError):
            endpoint.handle_executor_request(b'{"command":"x"}\n', authorities)

    def test_workload_self_stop_is_accepted_but_sibling_stop_is_rejected(self) -> None:
        plan, request, approval, state, authorities = subject()
        plan = contract.build_operation_plan("stop", "development", 7)
        request = replace(
            request, operation_kind="stop", plan_digest=plan.plan_digest,
        )
        workload = replace(
            state.requester_context, logical_name="development", role="graphical-base", generation=7,
        )
        approval = replace(
            approval, operation_kind="stop", plan_digest=plan.plan_digest,
            consequence_digest=plan.consequence_digest, logical_name="development",
            approval_class=plan.required_approval_class,
        )
        authorities.load_plan.return_value = plan
        authorities.load_approval.return_value = approval
        authorities.observe_state.return_value = replace(state, requester_context=workload)
        raw = endpoint.handle_executor_request(contract.request_to_json(request).encode(), authorities)
        self.assertEqual(client.parse_executor_response(raw, request).classification, "accepted")
        authorities.observe_state.return_value = replace(
            state, requester_context=replace(workload, logical_name="university"),
        )
        raw = endpoint.handle_executor_request(contract.request_to_json(request).encode(), authorities)
        self.assertEqual(client.parse_executor_response(raw, request).classification, "rejected")
