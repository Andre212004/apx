import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import apx_graphical_effect_adapter as subject
from apx_executor_contract import build_operation_plan


def completed(direction="hub-to-test", returncode=0, **changes):
    outgoing = subject.HUB_GENERATION if direction == "hub-to-test" else subject.TEST_GENERATION
    incoming = subject.TEST_GENERATION if direction == "hub-to-test" else subject.HUB_GENERATION
    value = {"classification": "handoff-complete", "direction": direction,
             "outgoing_generation": outgoing, "incoming_generation": incoming,
             "single_owner": True, "watchdog_active": True, "recovery_verified": True,
             **changes}
    return subprocess.CompletedProcess([], returncode, json.dumps(value), "")


class GraphicalEffectAdapterTests(unittest.TestCase):
    def test_hub_activate_maps_only_to_fixed_hub_to_test_broker_command(self):
        plan = build_operation_plan("activate", "test", subject.TEST_GENERATION)
        runner = Mock(return_value=completed())
        self.assertEqual(subject.apply_graphical_effect(plan, "1" * 64, runner).classification, "accepted")
        self.assertEqual(runner.call_args.args[0], subject.COMMANDS[("activate", "test", subject.TEST_GENERATION)])

    def test_workload_stop_maps_only_to_fixed_return_command(self):
        plan = build_operation_plan("stop", "test", subject.TEST_GENERATION)
        runner = Mock(return_value=completed("test-to-hub"))
        self.assertEqual(subject.apply_graphical_effect(plan, "1" * 64, runner).classification, "accepted")

    def test_other_operation_name_generation_and_changed_plan_are_refused(self):
        cases = (
            build_operation_plan("activate", "other", subject.TEST_GENERATION),
            build_operation_plan("snapshot", "test", subject.TEST_GENERATION),
            build_operation_plan("activate", "test", "11111111-1111-4111-8111-111111111111"),
        )
        for plan in cases:
            with self.assertRaises(subject.GraphicalEffectError):
                subject.apply_graphical_effect(plan, "1" * 64, Mock())

    def test_failure_or_contradictory_completion_is_incomplete(self):
        plan = build_operation_plan("activate", "test", subject.TEST_GENERATION)
        for result in (completed(returncode=1), completed(single_owner=False)):
            self.assertEqual(subject.apply_graphical_effect(plan, "1" * 64,
                             Mock(return_value=result)).classification, "incomplete")


if __name__ == "__main__":
    unittest.main()
