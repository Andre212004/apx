from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_installation as installation


class InstallationTests(unittest.TestCase):
    def evidence(self, **changes):
        values = {
            "project_pushed": True,
            "personal_backup_verified": True,
            "recovery_media_verified": True,
            "current_desktop_preserved": True,
            "headless_environment_passed": True,
            "two_environment_isolation_passed": True,
            "graphical_hub_passed": True,
            "graphical_handoff_passed": True,
            "package_isolation_passed": True,
            "destructive_recovery_passed": True,
            "authoritative": True,
        }
        values.update(changes)
        return installation.InstallationEvidence(**values)

    def test_plan_is_fixed_and_requires_parallel_recovery(self):
        first = installation.build_installation_plan()
        second = installation.build_installation_plan()
        self.assertEqual(first, second)
        self.assertEqual(len(first.digest), 64)
        self.assertIn("parallel", " ".join(first.invariants))
        self.assertIn("current desktop", " ".join(first.cleanup_exclusions))

    def test_unpushed_project_or_missing_desktop_recovery_hard_blocks(self):
        for field in ("project_pushed", "current_desktop_preserved"):
            with self.subTest(field=field):
                result = installation.assess_installation(self.evidence(**{field: False}))
                self.assertEqual(result.decision, "blocked")

    def test_backup_and_recovery_media_precede_host_test(self):
        result = installation.assess_installation(
            self.evidence(personal_backup_verified=False, recovery_media_verified=False)
        )
        self.assertEqual(result.decision, "waiting")
        self.assertEqual(len(result.blockers), 2)

    def test_headless_test_requires_authoritative_evidence(self):
        pending = installation.assess_installation(
            self.evidence(headless_environment_passed=False, authoritative=False)
        )
        ready = installation.assess_installation(
            self.evidence(headless_environment_passed=False)
        )
        self.assertEqual(pending.decision, "waiting")
        self.assertEqual(ready.decision, "eligible-for-bounded-headless-test")

    def test_each_validation_stage_advances_only_one_boundary(self):
        isolation = installation.assess_installation(
            self.evidence(two_environment_isolation_passed=False)
        )
        graphical = installation.assess_installation(
            self.evidence(graphical_hub_passed=False)
        )
        package = installation.assess_installation(
            self.evidence(package_isolation_passed=False)
        )
        self.assertEqual(isolation.decision, "eligible-for-isolation-test")
        self.assertEqual(graphical.decision, "eligible-for-parallel-graphical-test")
        self.assertEqual(package.decision, "eligible-for-package-isolation-test")

    def test_cutover_never_implies_cleanup(self):
        result = installation.assess_installation(
            self.evidence(destructive_recovery_passed=False)
        )
        self.assertEqual(result.decision, "cutover-allowed-cleanup-forbidden")
        self.assertIn("cleanup", " ".join(result.blockers))

    def test_complete_evidence_allows_only_cleanup_review(self):
        result = installation.assess_installation(self.evidence())
        self.assertEqual(result.decision, "cleanup-review-only")
        self.assertNotIn("cleanup-approved", result.decision)

    def test_malformed_evidence_fails_closed(self):
        malformed = replace(self.evidence(), authoritative=1)
        self.assertEqual(installation.assess_installation(malformed).decision, "blocked")
        self.assertEqual(installation.assess_installation(object()).decision, "blocked")

    def test_plain_render_always_states_kde_is_not_authorized_for_removal(self):
        assessment = installation.assess_installation(self.evidence())
        rendered = installation.render_installation_assessment(assessment)
        self.assertIn("KDE removal: not authorized", rendered)
        self.assertIn("cleanup-review-only", rendered)


if __name__ == "__main__":
    unittest.main()
