from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_stage2_gate as gate


DOSSIER = "a" * 64
PLAN = "b" * 64


class Stage2GateTests(unittest.TestCase):
    def evidence(self, **changes):
        values = {
            "dossier_digest": DOSSIER,
            "acquisition_plan_digest": PLAN,
            "snapshot_assessment": "verified",
            "snapshot_assessment_digest": "c" * 64,
            "trust_seal_state": "verified",
            "trust_seal_digest": "d" * 64,
            "trust_seal_plan_digest": PLAN,
            "capacity_decision": "ready-for-stage2-capacity-gate",
            "capacity_evidence_digest": "e" * 64,
            "intended_identities_absent": True,
            "parent_identities_verified": True,
            "subordinate_ids_verified": True,
            "quota_hierarchy_verified": True,
            "host_invariants_captured": True,
            "network_acquisition_approved": True,
            "approval_authenticated": True,
            "approval_unexpired": True,
            "approval_unused": True,
            "journal_store_authoritative": True,
            "cleanup_separately_scoped": True,
        }
        values.update(changes)
        return gate.Stage2Evidence(**values)

    def assess(self, evidence=None, **expected):
        return gate.assess_stage2_gate(
            evidence or self.evidence(),
            expected_dossier_digest=expected.get("dossier", DOSSIER),
            expected_acquisition_plan_digest=expected.get("plan", PLAN),
        )

    def test_complete_evidence_only_reaches_separate_execution_approval(self):
        result = self.assess()
        self.assertEqual(result.decision, "ready-for-separate-stage2-execution-approval")
        self.assertTrue(result.allowed_effects)
        self.assertFalse(any("cleanup" in effect for effect in result.allowed_effects))

    def test_every_boolean_gate_fails_closed(self):
        boolean_fields = [
            name for name, value in self.evidence().__dict__.items() if type(value) is bool
        ]
        for field in boolean_fields:
            with self.subTest(field=field):
                result = self.assess(replace(self.evidence(), **{field: False}))
                self.assertEqual(result.decision, "blocked")
                self.assertEqual(result.allowed_effects, ())

    def test_wrong_typed_boolean_fails_closed(self):
        result = self.assess(replace(self.evidence(), approval_unused=1))
        self.assertEqual(result.decision, "blocked")
        self.assertIn("approval_unused has wrong type", result.blockers)

    def test_dossier_snapshot_and_trust_plan_must_all_match(self):
        cases = (
            self.evidence(dossier_digest="f" * 64),
            self.evidence(acquisition_plan_digest="f" * 64),
            self.evidence(trust_seal_plan_digest="f" * 64),
        )
        for evidence in cases:
            with self.subTest(evidence=evidence):
                self.assertEqual(self.assess(evidence).decision, "blocked")

    def test_malformed_digests_and_expected_values_block(self):
        self.assertEqual(
            self.assess(self.evidence(trust_seal_digest="bad")).decision, "blocked"
        )
        self.assertEqual(self.assess(dossier="bad").decision, "blocked")
        self.assertEqual(self.assess(plan="bad").decision, "blocked")

    def test_snapshot_trust_and_capacity_states_are_exact(self):
        for field, value in (
            ("snapshot_assessment", "pending"),
            ("trust_seal_state", "pending-authoritative-confirmation"),
            ("capacity_decision", "pending-authoritative-confirmation"),
        ):
            with self.subTest(field=field):
                self.assertEqual(
                    self.assess(replace(self.evidence(), **{field: value})).decision,
                    "blocked",
                )

    def test_malformed_evidence_object_blocks_without_crash(self):
        result = gate.assess_stage2_gate(
            object(), expected_dossier_digest=DOSSIER, expected_acquisition_plan_digest=PLAN
        )
        self.assertEqual(result.decision, "blocked")

    def test_render_is_plain_and_keeps_graphics_cleanup_out(self):
        output = gate.render_stage2_gate(self.assess())
        self.assertIn("Graphical Environment: not included", output)
        self.assertIn("KDE removal: not included", output)
        self.assertIn("Cleanup: separate approval only", output)


if __name__ == "__main__":
    unittest.main()
