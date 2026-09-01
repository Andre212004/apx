from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_cleanup as cleanup


DIGEST = "a" * 64


def resource(name, kind, disposition="delete"):
    return cleanup.CleanupResource(name, kind, DIGEST, disposition)


class CleanupTests(unittest.TestCase):
    def resources(self, scope="complete-purge"):
        copies = "delete" if scope == "complete-purge" else "preserve"
        return tuple(sorted((
            resource("account", "account"),
            resource("archive-1", "archive", copies),
            resource("home", "home"),
            resource("network", "network"),
            resource("qgroup-home", "qgroup"),
            resource("registration", "registration"),
            resource("root", "root"),
            resource("runtime", "runtime"),
            resource("snapshot-1", "snapshot", copies),
        ), key=lambda item: item.resource_id))

    def plan(self, scope="complete-purge"):
        return cleanup.build_cleanup_plan(
            environment_id="env-" + "b" * 32,
            generation=3,
            scope=scope,
            resources=self.resources(scope),
        )

    def evidence(self, plan=None, state="absent", **changes):
        plan = plan or self.plan()
        values = {
            "observations": tuple(
                cleanup.ResourceObservation(item.resource_id, None if state == "absent" else item.identity_digest, state)
                for item in plan.resources
            ),
            "stopped": True,
            "processes_absent": True,
            "open_handles_absent": True,
            "mounts_absent": True,
            "network_absent": True,
            "account_absent": True,
            "registration_absent": True,
            "quota_consistent": True,
            "protected_neighbors_unchanged": True,
            "free_bytes_before": 1000,
            "free_bytes_after": 2000,
            "authoritative": True,
        }
        values.update(changes)
        return cleanup.CleanupEvidence(**values)

    def test_complete_purge_requires_every_resource_absent(self):
        plan = self.plan()
        result = cleanup.assess_cleanup(plan, self.evidence(plan), approved=True)
        self.assertEqual(result.state, "complete")
        self.assertTrue(result.reusable_identity)
        self.assertEqual(result.progress_completed, result.progress_total)

    def test_under_deletion_stale_and_deletion_requested_remain_freeing_space(self):
        plan = self.plan()
        for state in ("under-deletion", "stale", "deletion-requested"):
            observations = list(self.evidence(plan).observations)
            observations[0] = cleanup.ResourceObservation(
                observations[0].resource_id, DIGEST, state
            )
            result = cleanup.assess_cleanup(
                plan, self.evidence(plan, observations=tuple(observations)), approved=True
            )
            self.assertEqual(result.state, "freeing-space")
            self.assertFalse(result.reusable_identity)

    def test_path_absence_cannot_hide_pending_qgroup(self):
        plan = self.plan()
        observations = tuple(
            cleanup.ResourceObservation(
                item.resource_id,
                DIGEST if item.resource_id == "qgroup-home" else None,
                "under-deletion" if item.resource_id == "qgroup-home" else "absent",
            )
            for item in plan.resources
        )
        result = cleanup.assess_cleanup(
            plan, self.evidence(plan, observations=observations), approved=True
        )
        self.assertEqual(result.state, "freeing-space")
        self.assertIn("qgroup-home", result.pending)

    def test_environment_only_scope_is_not_available(self):
        with self.assertRaisesRegex(cleanup.CleanupError, "unsupported cleanup scope"):
            self.plan("environment-only")

    def test_complete_purge_cannot_mark_a_listed_copy_for_preservation(self):
        resources = list(self.resources())
        index = next(i for i, item in enumerate(resources) if item.kind == "archive")
        resources[index] = replace(resources[index], disposition="preserve")
        with self.assertRaises(cleanup.CleanupError):
            cleanup.build_cleanup_plan(
                environment_id="env-" + "b" * 32,
                generation=1,
                scope="complete-purge",
                resources=resources,
            )

    def test_no_approval_has_no_cleanup_authority(self):
        plan = self.plan()
        result = cleanup.assess_cleanup(plan, self.evidence(plan, state="present"), approved=False)
        self.assertEqual(result.state, "awaiting-approval")
        self.assertEqual(result.progress_completed, 0)

    def test_identity_change_or_unavailable_authority_preserves(self):
        plan = self.plan()
        observations = list(self.evidence(plan, state="present").observations)
        observations[0] = replace(observations[0], identity_digest="c" * 64)
        changed = cleanup.assess_cleanup(
            plan, self.evidence(plan, observations=tuple(observations)), approved=True
        )
        unavailable = cleanup.assess_cleanup(
            plan, self.evidence(plan, authoritative=False), approved=True
        )
        self.assertEqual(changed.state, "preserved-uncertain")
        self.assertEqual(unavailable.state, "preserved-uncertain")

    def test_runtime_or_neighbor_safety_failure_stops(self):
        plan = self.plan()
        for field in (
            "stopped", "processes_absent", "open_handles_absent", "mounts_absent", "network_absent",
            "quota_consistent", "protected_neighbors_unchanged",
        ):
            with self.subTest(field=field):
                result = cleanup.assess_cleanup(
                    plan, self.evidence(plan, state="present", **{field: False}), approved=True
                )
                self.assertEqual(result.state, "failed")

    def test_account_and_registration_must_be_absent(self):
        plan = self.plan()
        result = cleanup.assess_cleanup(
            plan,
            self.evidence(plan, account_absent=False, registration_absent=False),
            approved=True,
        )
        self.assertNotEqual(result.state, "complete")
        self.assertFalse(result.reusable_identity)

    def test_observation_set_must_match_plan_exactly(self):
        plan = self.plan()
        evidence = self.evidence(plan)
        for observations in (evidence.observations[:-1], evidence.observations + (evidence.observations[0],)):
            with self.assertRaises(cleanup.CleanupError):
                cleanup.assess_cleanup(plan, replace(evidence, observations=observations), approved=True)

    def test_reclaimed_bytes_are_factual_and_never_negative(self):
        plan = self.plan()
        positive = cleanup.assess_cleanup(plan, self.evidence(plan), approved=True)
        lower = cleanup.assess_cleanup(
            plan, self.evidence(plan, free_bytes_after=500), approved=True
        )
        self.assertEqual(positive.reclaimed_bytes_observed, 1000)
        self.assertEqual(lower.reclaimed_bytes_observed, 0)

    def test_render_explains_pending_and_identity_reuse(self):
        plan = self.plan()
        result = cleanup.assess_cleanup(plan, self.evidence(plan, state="under-deletion"), approved=True)
        output = cleanup.render_cleanup_assessment(result)
        self.assertIn("A libertar espaço", output)
        self.assertIn("Identidade reutilizável: não", output)

    def test_plan_digest_order_and_required_resources_are_enforced(self):
        plan = self.plan()
        with self.assertRaises(cleanup.CleanupError):
            cleanup.validate_cleanup_plan(replace(plan, plan_digest="c" * 64))
        with self.assertRaises(cleanup.CleanupError):
            cleanup.build_cleanup_plan(
                environment_id=plan.environment_id,
                generation=plan.generation,
                scope=plan.scope,
                resources=tuple(reversed(plan.resources)),
            )
        without_home = tuple(item for item in plan.resources if item.kind != "home")
        with self.assertRaises(cleanup.CleanupError):
            cleanup.build_cleanup_plan(
                environment_id=plan.environment_id,
                generation=plan.generation,
                scope=plan.scope,
                resources=without_home,
            )


if __name__ == "__main__":
    unittest.main()
