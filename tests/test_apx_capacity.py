from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_capacity as capacity


class CapacityGateTests(unittest.TestCase):
    def evidence(self, **changes):
        values = {
            "filesystem_identity": "btrfs-device-57",
            "total_bytes": 476 * capacity.GIB,
            "free_bytes": 382 * capacity.GIB,
            "metadata_free_bytes": 8 * capacity.GIB,
            "quota": capacity.QuotaEvidence(True, True, False, False, False, True),
            "authoritative": True,
        }
        values.update(changes)
        return capacity.CapacityEvidence(**values)

    def test_complete_authoritative_evidence_passes(self):
        result = capacity.assess_trial_capacity(self.evidence())
        self.assertEqual(result.decision, "ready-for-stage2-capacity-gate")
        self.assertEqual(result.required_headroom_bytes, 16 * capacity.GIB)
        self.assertEqual(result.host_reserve_bytes, 64 * capacity.GIB)

    def test_real_current_gap_is_enforcement_fixture(self):
        quota = capacity.QuotaEvidence(True, True, False, False, False, False)
        result = capacity.assess_trial_capacity(self.evidence(quota=quota))
        self.assertEqual(result.decision, "blocked")
        self.assertIn("bounded quota enforcement fixture has not passed", result.reasons)

    def test_restricted_positive_evidence_remains_pending(self):
        result = capacity.assess_trial_capacity(self.evidence(authoritative=False))
        self.assertEqual(result.decision, "pending-authoritative-confirmation")

    def test_every_unhealthy_quota_condition_blocks(self):
        healthy = self.evidence().quota
        for field, value in (
            ("enabled", False),
            ("full_accounting", False),
            ("inconsistent", True),
            ("override_limits", True),
            ("rescan_running", True),
            ("bounded_enforcement_passed", False),
        ):
            with self.subTest(field=field):
                result = capacity.assess_trial_capacity(
                    self.evidence(quota=replace(healthy, **{field: value}))
                )
                self.assertEqual(result.decision, "blocked")

    def test_capacity_and_metadata_reserves_are_independent(self):
        low_space = capacity.assess_trial_capacity(
            self.evidence(free_bytes=79 * capacity.GIB)
        )
        low_metadata = capacity.assess_trial_capacity(
            self.evidence(metadata_free_bytes=capacity.GIB)
        )
        self.assertIn("free space would cross the Stage 2 host reserve", low_space.reasons)
        self.assertIn("metadata safety margin is insufficient", low_metadata.reasons)

    def test_invalid_or_impossible_numbers_block(self):
        for changes in (
            {"free_bytes": -1},
            {"free_bytes": True},
            {"free_bytes": 500 * capacity.GIB},
            {"filesystem_identity": ""},
        ):
            with self.subTest(changes=changes):
                self.assertEqual(
                    capacity.assess_trial_capacity(self.evidence(**changes)).decision,
                    "blocked",
                )

    def test_evidence_digest_changes_with_any_safety_fact(self):
        first = capacity.assess_trial_capacity(self.evidence())
        second = capacity.assess_trial_capacity(
            self.evidence(free_bytes=381 * capacity.GIB)
        )
        self.assertNotEqual(first.evidence_digest, second.evidence_digest)


class ElasticGrowthTests(unittest.TestCase):
    def assess(self, **changes):
        values = {
            "requested_growth_bytes": 30 * capacity.GIB,
            "domain_headroom_bytes": 100 * capacity.GIB,
            "pool_headroom_bytes": 200 * capacity.GIB,
            "physical_free_bytes": 382 * capacity.GIB,
            "host_reserve_bytes": 64 * capacity.GIB,
            "quota_healthy": True,
        }
        values.update(changes)
        return capacity.assess_elastic_growth(**values)

    def test_growth_is_dynamic_not_preallocated(self):
        result = self.assess()
        self.assertEqual(result.decision, "allowed")
        self.assertEqual(result.allowed_growth_bytes, 30 * capacity.GIB)

    def test_each_independent_ceiling_can_block(self):
        for field in (
            "domain_headroom_bytes",
            "pool_headroom_bytes",
        ):
            with self.subTest(field=field):
                self.assertEqual(self.assess(**{field: 20 * capacity.GIB}).decision, "blocked")
        self.assertEqual(
            self.assess(physical_free_bytes=80 * capacity.GIB).decision, "blocked"
        )

    def test_unhealthy_quota_and_invalid_values_fail_closed(self):
        self.assertEqual(self.assess(quota_healthy=False).allowed_growth_bytes, 0)
        self.assertEqual(self.assess(requested_growth_bytes=-1).decision, "blocked")


if __name__ == "__main__":
    unittest.main()
