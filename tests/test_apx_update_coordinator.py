from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import apx_update_coordinator as subject  # noqa: E402


def env(name="work", **changes):
    values = {"name": name, "role": "graphical-base", "generation": "11111111-1111-4111-8111-111111111111",
              "state": "stopped", "policy": "follow-host", "package_database_ready": True, "snapshot_ready": True}
    values.update(changes); return subject.EnvironmentUpdateEvidence(**values)


class UpdateCoordinatorTests(unittest.TestCase):
    def test_creation_default_follows_host_and_legacy_registration_is_enrolled(self):
        self.assertEqual(subject.default_policy("work").policy, "follow-host")
        self.assertEqual(subject.policy_from_registration({"name": "old"}).policy, "follow-host")

    def test_owner_can_exclude_one_environment(self):
        plan = subject.build_plan((env("private", policy="excluded"), env("work")), host_snapshot_ready=True,
                                  repository_snapshot_ready=True, package_cache_ready=True)
        self.assertEqual(plan.classification, "ready-for-approval")
        self.assertEqual(plan.excluded_environments, ("private",))
        self.assertEqual(tuple(item.name for item in plan.targets), ("host", "work"))

    def test_running_or_unsnapshottable_target_blocks_whole_transaction(self):
        plan = subject.build_plan((env(state="running"),), host_snapshot_ready=True,
                                  repository_snapshot_ready=True, package_cache_ready=True)
        self.assertEqual(plan.classification, "blocked")
        self.assertIn("environment-running:work", plan.blockers)

    def test_one_frozen_repository_and_offline_apply_are_mandatory(self):
        plan = subject.build_plan((env(),), host_snapshot_ready=True,
                                  repository_snapshot_ready=True, package_cache_ready=True)
        self.assertIn("freeze-one-signed-repository-snapshot", plan.effects)
        self.assertIn("apply-offline-host-first-then-included-environments", plan.effects)
        self.assertTrue(all(target.snapshot_required for target in plan.targets))


if __name__ == "__main__": unittest.main()
