from __future__ import annotations

from dataclasses import asdict, replace
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_executor_contract as contract


OPERATION_ID = "op-" + "1" * 32
APPROVAL_ID = "approval-" + "2" * 32
SESSION_ID = "session-" + "3" * 32
NONCE = "4" * 64


def valid_subject(kind: str = "activate", generation: int = 7):
    plan = contract.build_operation_plan(kind, "university", generation)
    request = contract.ExecutorRequest(
        schema_version=contract.REQUEST_SCHEMA_VERSION,
        protocol_version=contract.PROTOCOL_VERSION,
        operation_id=OPERATION_ID,
        operation_kind=kind,
        logical_name="university",
        expected_generation=generation,
        plan_digest=plan.plan_digest,
        approval_id=APPROVAL_ID,
        nonce=NONCE,
        expires_at=200,
    )
    approval = contract.ApprovalEvidence(
        approval_id=APPROVAL_ID,
        operation_id=OPERATION_ID,
        operation_kind=kind,
        logical_name="university",
        expected_generation=generation,
        plan_digest=plan.plan_digest,
        consequence_digest=plan.consequence_digest,
        approval_class=plan.required_approval_class,
        session_id=SESSION_ID,
        nonce=NONCE,
        issued_at=100,
        not_before=100,
        expires_at=200,
        authenticity_verified=True,
    )
    return plan, request, approval


class OperationPlanTests(unittest.TestCase):
    def test_catalogue_is_closed_and_has_no_commands_or_paths(self) -> None:
        self.assertEqual(set(contract.OPERATION_KINDS), set(contract.EFFECTS_BY_OPERATION))
        self.assertEqual(set(contract.OPERATION_KINDS), set(contract.CONSEQUENCES_BY_OPERATION))
        for kind in contract.OPERATION_KINDS:
            generation = 0 if kind in {"create", "restore"} else 1
            plan = contract.build_operation_plan(kind, "games", generation)
            self.assertFalse(hasattr(plan, "command"))
            self.assertFalse(hasattr(plan, "path"))
            self.assertFalse(hasattr(plan, "arguments"))
            self.assertTrue(plan.effects)
            self.assertTrue(plan.consequences)
            self.assertEqual(len(plan.plan_digest), 64)

    def test_unknown_operation_name_and_policy_are_rejected(self) -> None:
        with self.assertRaises(contract.ExecutorContractError):
            contract.build_operation_plan("run-command", "games", 1)
        with self.assertRaises(contract.ExecutorContractError):
            contract.build_operation_plan("activate", "games", 1, policy_version="caller-policy")

    def test_generation_rules_separate_absence_from_existing_environment(self) -> None:
        for kind in ("create", "restore"):
            self.assertEqual(contract.build_operation_plan(kind, "new-env", 0).expected_generation, 0)
            with self.assertRaises(contract.ExecutorContractError):
                contract.build_operation_plan(kind, "new-env", 1)
        with self.assertRaises(contract.ExecutorContractError):
            contract.build_operation_plan("destroy", "games", 0)

    def test_dangerous_actions_require_strong_confirmation(self) -> None:
        for kind in ("destroy", "force-stop", "recover-cleanup"):
            plan = contract.build_operation_plan(kind, "games", 2)
            self.assertEqual(plan.required_approval_class, "strong-confirmation")
        self.assertIn(
            "deletes-environment-root-and-home",
            contract.build_operation_plan("destroy", "games", 2).consequences,
        )

    def test_plan_digest_changes_with_security_relevant_subject(self) -> None:
        first = contract.build_operation_plan("activate", "games", 2)
        variants = (
            contract.build_operation_plan("stop", "games", 2),
            contract.build_operation_plan("activate", "work", 2),
            contract.build_operation_plan("activate", "games", 3),
        )
        for variant in variants:
            self.assertNotEqual(first.plan_digest, variant.plan_digest)


class RequestParserTests(unittest.TestCase):
    def test_canonical_round_trip(self) -> None:
        _, request, _ = valid_subject()
        self.assertEqual(
            contract.parse_executor_request_json(contract.request_to_json(request)),
            request,
        )

    def test_unknown_command_field_and_missing_field_are_rejected(self) -> None:
        _, request, _ = valid_subject()
        payload = asdict(request)
        payload["command"] = "rm -rf /"
        with self.assertRaises(contract.ExecutorContractError):
            contract.parse_executor_request_json(json.dumps(payload))
        del payload["command"]
        del payload["nonce"]
        with self.assertRaises(contract.ExecutorContractError):
            contract.parse_executor_request_json(json.dumps(payload))

    def test_duplicate_wrong_type_oversized_and_noncanonical_values_are_rejected(self) -> None:
        _, request, _ = valid_subject()
        canonical = contract.request_to_json(request).strip()
        duplicate = canonical[:-1] + ',"nonce":"' + NONCE + '"}'
        with self.assertRaises(contract.ExecutorContractError):
            contract.parse_executor_request_json(duplicate)

        payload = asdict(request)
        payload["expected_generation"] = True
        with self.assertRaises(contract.ExecutorContractError):
            contract.parse_executor_request_json(json.dumps(payload))

        with self.assertRaises(contract.ExecutorContractError):
            contract.parse_executor_request_json(" " * (contract.MAX_REQUEST_BYTES + 1))

        for field, value in (
            ("operation_id", "op-not-safe"),
            ("approval_id", "approval-not-safe"),
            ("nonce", "short"),
            ("plan_digest", "short"),
            ("logical_name", "../host"),
        ):
            payload = asdict(request)
            payload[field] = value
            with self.assertRaises(contract.ExecutorContractError):
                contract.parse_executor_request_json(json.dumps(payload))


class RequestAssessmentTests(unittest.TestCase):
    def assess(self, request=None, plan=None, approval=None, **changes):
        default_plan, default_request, default_approval = valid_subject()
        values = {
            "request": request or default_request,
            "plan": plan or default_plan,
            "approval": approval or default_approval,
            "current_generation": 7,
            "current_time": 150,
            "current_session_id": SESSION_ID,
            "nonce_state": "unused",
            "authoritative_state": "confirmed-compatible",
        }
        values.update(changes)
        return contract.assess_executor_request(**values)

    def test_exact_fresh_verified_request_is_authorized_at_contract_level(self) -> None:
        first = self.assess()
        second = self.assess()
        self.assertEqual(first, second)
        self.assertEqual(first.classification, "authorized-contract")
        self.assertEqual(first.issues, ())
        self.assertEqual(len(first.request_digest), 64)

    def test_expired_replayed_stale_or_unconfirmed_state_is_rejected(self) -> None:
        cases = (
            {"current_time": 201},
            {"nonce_state": "used"},
            {"current_generation": 8},
            {"authoritative_state": "unavailable"},
        )
        for changes in cases:
            self.assertEqual(self.assess(**changes).classification, "rejected")

    def test_unverified_or_weaker_approval_is_rejected(self) -> None:
        plan, request, approval = valid_subject()
        unverified = replace(approval, authenticity_verified=False)
        self.assertEqual(self.assess(approval=unverified).classification, "rejected")

        destroy_plan, destroy_request, destroy_approval = valid_subject("destroy", 7)
        weaker = replace(destroy_approval, approval_class="unlocked-session")
        self.assertEqual(
            self.assess(
                plan=destroy_plan,
                request=destroy_request,
                approval=weaker,
            ).classification,
            "rejected",
        )

    def test_wrong_session_or_excessive_approval_lifetime_is_rejected(self) -> None:
        plan, request, approval = valid_subject()
        self.assertEqual(
            self.assess(current_session_id="session-" + "9" * 32).classification,
            "rejected",
        )
        long_request = replace(request, expires_at=1000)
        long_approval = replace(approval, expires_at=1000)
        self.assertEqual(
            self.assess(request=long_request, approval=long_approval).classification,
            "rejected",
        )

    def test_plan_effects_cannot_be_changed_behind_a_matching_request(self) -> None:
        plan, request, approval = valid_subject()
        changed = replace(plan, effects=plan.effects + ("run-caller-command",))
        self.assertEqual(
            self.assess(plan=changed, request=request, approval=approval).classification,
            "rejected",
        )

    def test_every_approval_binding_is_enforced(self) -> None:
        plan, request, approval = valid_subject()
        variants = (
            replace(approval, approval_id="approval-" + "9" * 32),
            replace(approval, operation_id="op-" + "9" * 32),
            replace(approval, operation_kind="stop"),
            replace(approval, logical_name="work"),
            replace(approval, expected_generation=8),
            replace(approval, plan_digest="9" * 64),
            replace(approval, consequence_digest="9" * 64),
            replace(approval, nonce="9" * 64),
            replace(approval, expires_at=199),
        )
        for variant in variants:
            self.assertEqual(self.assess(approval=variant).classification, "rejected")

    def test_request_cannot_change_operation_environment_generation_or_plan(self) -> None:
        plan, request, approval = valid_subject()
        variants = (
            replace(request, operation_kind="stop"),
            replace(request, logical_name="work"),
            replace(request, expected_generation=8),
            replace(request, plan_digest="9" * 64),
        )
        for variant in variants:
            self.assertEqual(self.assess(request=variant).classification, "rejected")


if __name__ == "__main__":
    unittest.main()
