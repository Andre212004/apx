from dataclasses import replace
import unittest

from src.apx_official_hub_cutover import (
    OfficialHubCutoverEvidence,
    build_cutover_plan,
)


class OfficialHubCutoverTests(unittest.TestCase):
    def evidence(self) -> OfficialHubCutoverEvidence:
        return OfficialHubCutoverEvidence(
            current_generation="2c3dbacc-106f-4053-8603-f649552f5513",
            current_release="hyprland-base-v1",
            current_role="hub-graphical",
            current_stopped=True,
            hub_testes_absent=True,
            official_candidate_ready=True,
            official_release_manifest_digest="a" * 64,
            tty1_active=True,
            no_running_machines=True,
            no_uncertain_operation=True,
            rollback_paths_available=True,
        )

    def test_ready_plan_preserves_old_hub_and_publishes_new(self) -> None:
        plan = build_cutover_plan(self.evidence())
        self.assertEqual(plan.classification, "ready-for-cutover")
        self.assertIn("rename-current-hub-to-hub-testes", plan.effects)
        self.assertIn("delete-current-hub-root-or-home", plan.forbidden_effects)
        self.assertIn("grant-hub-authority-to-hub-testes", plan.forbidden_effects)

    def test_each_safety_gate_blocks(self) -> None:
        for field in (
            "current_stopped", "hub_testes_absent", "official_candidate_ready",
            "tty1_active", "no_running_machines", "no_uncertain_operation",
            "rollback_paths_available",
        ):
            with self.subTest(field=field):
                plan = build_cutover_plan(replace(self.evidence(), **{field: False}))
                self.assertEqual(plan.classification, "blocked")

    def test_changed_current_identity_blocks(self) -> None:
        plan = build_cutover_plan(replace(self.evidence(), current_generation="changed"))
        self.assertIn("current graphical Hub identity changed", plan.blockers)


if __name__ == "__main__":
    unittest.main()
