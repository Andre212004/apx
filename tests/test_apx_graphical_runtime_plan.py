from dataclasses import replace
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import apx_graphical_runtime_plan as subject


def observation():
    return subject.GraphicalRuntimeObservation(
        subject.TEST_GENERATION, subject.RELEASE_MANIFEST_DIGEST,
        "card2-eDP-2", True, True, True, True, True, True, True, True, True,
        subject.DEVICES,
    )


class GraphicalRuntimePlanTests(unittest.TestCase):
    def test_exact_clean_observation_builds_bounded_single_owner_plan(self):
        plan = subject.build_graphical_runtime_plan(observation())
        self.assertEqual(plan.deadline_seconds, 15)
        self.assertEqual([item[0] for item in plan.session_subjects], ["hub", "test"])
        self.assertIn("verify-deadline-active-before-granting-devices", plan.ordered_effects)
        self.assertIn("never-automatically-restart-graphics", plan.recovery_effects)
        self.assertIn("run-two-graphical-environments", plan.forbidden_effects)

    def test_every_clean_host_gate_blocks(self):
        for field in ("connector_connected", "tty1_active", "tty2_inactive",
                      "no_graphical_owner", "no_display_manager", "no_failed_units",
                      "no_uncertain_operation", "hub_candidate_present", "test_stopped"):
            with self.assertRaises(subject.GraphicalRuntimePlanError, msg=field):
                subject.build_graphical_runtime_plan(replace(observation(), **{field: False}))

    def test_stale_generation_release_connector_or_devices_blocks(self):
        cases = (
            replace(observation(), test_generation="changed"),
            replace(observation(), release_manifest_digest="0" * 64),
            replace(observation(), connector="card1-eDP-1"),
            replace(observation(), devices=()),
        )
        for value in cases:
            with self.assertRaises(subject.GraphicalRuntimePlanError):
                subject.build_graphical_runtime_plan(value)


if __name__ == "__main__":
    unittest.main()
