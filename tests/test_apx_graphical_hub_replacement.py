from dataclasses import replace
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import apx_graphical_hub_replacement as subject


def evidence():
    return subject.GraphicalHubReplacementEvidence(
        subject.CURRENT_GENERATION, subject.CURRENT_RELEASE, "stopped", 0, True,
        "1" * 64, True, True, True, True, True, True, True, True, True, True,
    )


class GraphicalHubReplacementTests(unittest.TestCase):
    def test_complete_evidence_reaches_only_separate_approval(self) -> None:
        plan = subject.build_replacement_plan(evidence())
        self.assertEqual(plan.classification, "ready-for-separate-replacement-approval")
        self.assertIn("retain-headless-hub-until-separate-retirement-approval", plan.effects)
        self.assertIn("delete-or-overwrite-current-hub", plan.forbidden_effects)

    def test_every_safety_gate_blocks_independently(self) -> None:
        for field in (
            "graphical_release_verified", "recovery_v2_tests_passed",
            "recovery_v2_non_graphical_rehearsal_passed", "package_isolation_passed",
            "disposable_graphical_environment_passed", "hub_gtk_fake_executor_passed",
            "hub_typed_executor_passed", "exclusive_handoff_passed",
            "tty1_recovery_verified", "no_uncertain_apx_operation",
        ):
            with self.subTest(field=field):
                self.assertEqual(subject.build_replacement_plan(replace(evidence(), **{field: False})).classification, "blocked")

    def test_nonempty_home_or_changed_current_hub_blocks(self) -> None:
        self.assertEqual(subject.build_replacement_plan(replace(evidence(), current_home_bytes=1)).classification, "blocked")
        self.assertEqual(subject.build_replacement_plan(replace(evidence(), current_state="running")).classification, "blocked")

    def test_malformed_evidence_is_rejected(self) -> None:
        for case in (
            replace(evidence(), current_home_bytes=-1),
            replace(evidence(), graphical_release_evidence_digest="bad"),
            replace(evidence(), tty1_recovery_verified=1),
        ):
            with self.assertRaises(subject.GraphicalHubReplacementError):
                subject.build_replacement_plan(case)


if __name__ == "__main__":
    unittest.main()
