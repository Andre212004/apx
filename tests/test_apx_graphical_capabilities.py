from dataclasses import replace
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import apx_graphical_capabilities as subject


def evidence(**changes):
    value = subject.CapabilityChangeEvidence(
        "hub", "hub-graphical", True, True, True,
        "university", 7, "stopped", (), ("microphone-mediated",), True,
    )
    return replace(value, **changes)


class GraphicalCapabilityTests(unittest.TestCase):
    def test_canonical_hub_can_prepare_explicit_stopped_target_change(self) -> None:
        plan = subject.build_capability_change_plan(evidence())
        self.assertEqual(plan.classification, "ready-for-explicit-confirmation")
        self.assertEqual(plan.added, ("microphone-mediated",))
        self.assertEqual(plan.removed, ())
        self.assertEqual(plan.approval_class, "explicit-confirmation")
        self.assertIn("activate-target-environment", plan.forbidden_effects)
        self.assertEqual(len(plan.plan_digest), 64)

    def test_non_hub_forged_hub_role_and_untrusted_sessions_block(self) -> None:
        variants = (
            evidence(requester_logical_name="university"),
            evidence(requester_role="graphical-base"),
            evidence(requester_authenticated=False),
            evidence(requester_active=False),
            evidence(requester_authoritative=False),
        )
        for variant in variants:
            self.assertEqual(subject.build_capability_change_plan(variant).classification, "blocked")

    def test_running_target_and_uncertain_operation_block(self) -> None:
        for variant in (evidence(target_state="running"), evidence(no_uncertain_operation=False)):
            self.assertEqual(subject.build_capability_change_plan(variant).classification, "blocked")

    def test_only_closed_sorted_unique_optional_capabilities_are_accepted(self) -> None:
        invalid = (
            ("microphone-mediated", "microphone-mediated"),
            ("removable-storage-mediated", "camera-mediated"),
            ("host-root",),
        )
        for selection in invalid:
            with self.assertRaises(subject.GraphicalCapabilityError):
                subject.build_capability_change_plan(evidence(requested_optional_capabilities=selection))

    def test_removal_is_generation_bound_and_keeps_essential_capabilities(self) -> None:
        plan = subject.build_capability_change_plan(evidence(
            current_optional_capabilities=("camera-mediated", "microphone-mediated"),
            requested_optional_capabilities=("camera-mediated",),
        ))
        self.assertEqual(plan.removed, ("microphone-mediated",))
        self.assertEqual(plan.retained_essential_capabilities, subject.ESSENTIAL_CAPABILITIES)
        self.assertEqual(plan.target_generation, 7)
