from dataclasses import replace
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import apx_executor_contract as executor
import apx_hub
import apx_hub_action_protocol as subject


def requester(name="hub", role="hub-graphical", generation=3):
    return executor.RequesterContext("session-" + "1" * 32, name, role, generation, True, True, True)


def action(action_id, operation, approval="explicit-confirmation", enabled=True):
    return apx_hub.HubAction(action_id, "Test", enabled, "Test", operation, approval)


class HubActionProtocolTests(unittest.TestCase):
    def test_each_fixed_hub_control_builds_the_exact_executor_plan(self) -> None:
        cases = (
            ("open", "activate", "unlocked-session"),
            ("capabilities", "configure-capabilities", "explicit-confirmation"),
            ("snapshot", "snapshot", "explicit-confirmation"),
            ("archive", "archive", "explicit-confirmation"),
            ("destroy", "destroy", "strong-confirmation"),
            ("recover", "recover-complete", "explicit-confirmation"),
        )
        for action_id, operation, approval in cases:
            intent = subject.build_hub_action_intent(
                action(action_id, operation, approval), requester(), "university", 7,
            )
            self.assertEqual(intent.operation_kind, operation)
            self.assertEqual(intent.plan_digest, intent.operation_plan.plan_digest)
            self.assertEqual(intent.approval_class, approval)

    def test_disabled_mismatched_or_forged_hub_action_is_rejected(self) -> None:
        variants = (
            (action("open", "activate", "unlocked-session", False), requester()),
            (action("open", "destroy", "strong-confirmation"), requester()),
            (action("open", "activate", "explicit-confirmation"), requester()),
            (action("open", "activate", "unlocked-session"), requester("university", "hub-graphical")),
            (action("open", "activate", "unlocked-session"), replace(requester(), authoritative=False)),
        )
        for control, context in variants:
            with self.assertRaises(subject.HubActionProtocolError):
                subject.build_hub_action_intent(control, context, "university", 7)

    def test_workload_return_is_typed_stop_for_its_own_generation(self) -> None:
        context = requester("university", "graphical-base", 7)
        intent = subject.build_workload_return_intent(context)
        self.assertEqual((intent.operation_kind, intent.target_logical_name, intent.target_generation),
                         ("stop", "university", 7))
        self.assertEqual(intent.approval_class, "unlocked-session")

    def test_hub_or_untrusted_workload_cannot_use_return_control(self) -> None:
        for context in (requester(), replace(requester("university", "graphical-base", 7), active=False)):
            with self.assertRaises(subject.HubActionProtocolError):
                subject.build_workload_return_intent(context)
