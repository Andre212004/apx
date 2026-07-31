from dataclasses import replace
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import apx_executor_contract as executor
import apx_graphical_broker as broker
import apx_graphical_integration_rehearsal as subject
import apx_hub
from apx_hub_action_protocol import build_hub_action_intent, build_workload_return_intent


def context(name, role, generation, marker):
    return executor.RequesterContext("session-" + marker * 32, name, role, generation, True, True, True)


def broker_plan():
    evidence = broker.GraphicalBrokerEvidence(
        broker.PROFILE, "4" * 64, broker.SEAT, "session-hub", 3,
        broker.RECOVERY_VT, broker.TRANSITION_VT,
        True, True, True, True, True, True, True, True,
    )
    return broker.build_broker_plan(evidence)


def subjects():
    hub = context("hub", "hub-graphical", 3, "1")
    workload = context("university", "graphical-base", 7, "2")
    control = apx_hub.HubAction("open", "Abrir", True, "Abrir", "activate", "unlocked-session")
    return (
        build_hub_action_intent(control, hub, "university", 7),
        build_workload_return_intent(workload), hub, workload,
    )


class GraphicalIntegrationRehearsalTests(unittest.TestCase):
    def test_buttons_executor_broker_and_handoff_pass_together_without_effects(self) -> None:
        opened, returned, hub, workload = subjects()
        result = subject.rehearse_typed_button_cycle(
            broker_plan(), opened, returned, hub, workload,
        )
        self.assertEqual(result.classification, "passed-effect-free-integration")
        self.assertEqual(result.open_executor_classification, "authorized-contract")
        self.assertEqual(result.return_executor_classification, "authorized-contract")
        self.assertEqual((result.final_phase, result.final_seat_owner), ("hub-active", "hub"))
        self.assertIn("workload-active", result.trace)

    def test_blocked_broker_prevents_integration(self) -> None:
        opened, returned, hub, workload = subjects()
        blocked = replace(broker_plan(), classification="blocked")
        with self.assertRaisesRegex(subject.GraphicalIntegrationError, "broker"):
            subject.rehearse_typed_button_cycle(blocked, opened, returned, hub, workload)

    def test_changed_return_generation_or_forged_requester_fails(self) -> None:
        opened, returned, hub, workload = subjects()
        with self.assertRaisesRegex(subject.GraphicalIntegrationError, "generations differ"):
            subject.rehearse_typed_button_cycle(
                broker_plan(), opened, replace(returned, target_generation=8), hub, workload,
            )
        with self.assertRaisesRegex(subject.GraphicalIntegrationError, "executor rejected"):
            subject.rehearse_typed_button_cycle(
                broker_plan(), opened, returned, replace(hub, logical_name="games"), workload,
            )
