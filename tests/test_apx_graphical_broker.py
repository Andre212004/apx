from dataclasses import replace
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import apx_graphical_broker as subject


def evidence():
    return subject.GraphicalBrokerEvidence(
        subject.PROFILE, "1" * 64, subject.SEAT, "session-hub-1", 3,
        subject.RECOVERY_VT, subject.TRANSITION_VT,
        True, True, True, True, True, True, True, True,
    )


class GraphicalBrokerTests(unittest.TestCase):
    def test_complete_evidence_reaches_fake_integration_only(self) -> None:
        plan = subject.build_broker_plan(evidence())
        self.assertEqual(plan.classification, "ready-for-fake-integration")
        self.assertNotIn("physical", plan.classification)
        self.assertEqual(plan.max_handoff_seconds, 30)
        self.assertIn("force-stop", plan.forbidden_effects)
        self.assertEqual(len(plan.plan_digest), 64)

    def test_every_gate_blocks_independently(self) -> None:
        fields = (
            "recovery_console_verified", "independent_watchdog_verified",
            "typed_executor_endpoint_verified", "single_graphical_owner_verified",
            "no_uncertain_handoff", "graphical_release_admitted",
            "production_hub_client_admitted", "mediated_device_adapter_verified",
        )
        for field in fields:
            plan = subject.build_broker_plan(replace(evidence(), **{field: False}))
            self.assertEqual(plan.classification, "blocked", field)

    def test_seat_vt_identity_generation_and_types_fail_closed(self) -> None:
        invalid = (
            replace(evidence(), seat="seat1"), replace(evidence(), recovery_vt=2),
            replace(evidence(), transition_vt=1), replace(evidence(), hub_generation=0),
            replace(evidence(), boot_id_digest="bad"),
            replace(evidence(), recovery_console_verified=1),
        )
        for value in invalid:
            with self.assertRaises(subject.GraphicalBrokerError):
                subject.build_broker_plan(value)

    def test_broker_has_no_device_or_arbitrary_effect_authority(self) -> None:
        plan = subject.build_broker_plan(evidence())
        joined = " ".join(plan.authority + plan.effects)
        for forbidden in ("shell", "grant-device", "caller-command", "mount", "package"):
            self.assertNotIn(forbidden, joined)
