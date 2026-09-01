from dataclasses import fields, replace
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import apx_manual_graphical_test as subject


class ManualGraphicalTestTests(unittest.TestCase):
    def test_current_observed_state_truthfully_blocks_physical_button_test(self) -> None:
        result = subject.assess_manual_test(subject.CURRENT_OBSERVED_EVIDENCE)
        self.assertEqual(result.classification, "blocked")
        for blocker in (
            "production Hub client is not admitted",
            "graphical Hub is not installed",
            "exclusive session broker is not installed",
            "physical H0 execution remains locked",
        ):
            self.assertIn(blocker, result.blockers)

    def test_every_boolean_gate_blocks_independently(self) -> None:
        boolean_fields = [field.name for field in fields(subject.ManualGraphicalTestEvidence)
                          if field.type == "bool"]
        ready = replace(subject.CURRENT_OBSERVED_EVIDENCE, **{name: True for name in boolean_fields})
        self.assertEqual(subject.assess_manual_test(ready).classification,
                         "ready-for-separate-owner-approval")
        for name in boolean_fields:
            result = subject.assess_manual_test(replace(ready, **{name: False}))
            self.assertEqual(result.classification, "blocked", name)

    def test_ready_state_still_does_not_authorize_execution(self) -> None:
        boolean_fields = [field.name for field in fields(subject.ManualGraphicalTestEvidence)
                          if field.type == "bool"]
        ready = replace(subject.CURRENT_OBSERVED_EVIDENCE, **{name: True for name in boolean_fields})
        result = subject.assess_manual_test(ready)
        self.assertNotIn("authorized", result.classification)
        self.assertEqual(result.max_visible_seconds, 30)
        self.assertIn("disable-watchdog", result.forbidden_actions)

    def test_changed_target_wrong_type_and_non_boolean_fail_closed(self) -> None:
        with self.assertRaises(ValueError):
            subject.assess_manual_test(replace(subject.CURRENT_OBSERVED_EVIDENCE,
                                               target_logical_name="games"))
        with self.assertRaises(ValueError):
            subject.assess_manual_test(replace(subject.CURRENT_OBSERVED_EVIDENCE,
                                               graphical_hub_installed=1))
        with self.assertRaises(ValueError):
            subject.assess_manual_test("ready")
