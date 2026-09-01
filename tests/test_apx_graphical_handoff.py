from dataclasses import replace
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import apx_graphical_handoff as subject


def initial():
    return subject.new_handoff("handoff-" + "1" * 64, 3, "university", 8)


class GraphicalHandoffTests(unittest.TestCase):
    def test_complete_hub_workload_hub_cycle_has_one_seat_owner(self) -> None:
        record = subject.advance_handoff(initial(), "request-open", recovery_verified=True, watchdog_active=True)
        self.assertEqual((record.phase, record.seat_owner), ("stopping-hub", "hub"))
        record = subject.advance_handoff(record, "outgoing-stopped", outgoing_release_verified=True)
        self.assertEqual(record.seat_owner, "broker")
        record = subject.advance_handoff(record, "start-workload")
        self.assertEqual((record.phase, record.seat_owner), ("starting-workload", "broker"))
        record = subject.advance_handoff(record, "workload-ready", incoming_readiness_verified=True)
        self.assertEqual((record.phase, record.seat_owner), ("workload-active", "university"))
        record = subject.advance_handoff(record, "request-return")
        record = subject.advance_handoff(record, "workload-stopped", outgoing_release_verified=True)
        self.assertEqual(record.seat_owner, "broker")
        record = subject.advance_handoff(record, "start-hub")
        record = subject.advance_handoff(record, "hub-ready", incoming_readiness_verified=True)
        self.assertEqual((record.phase, record.seat_owner), ("hub-active", "hub"))
        self.assertEqual(record.sequence, 8)

    def test_hub_cannot_stop_before_recovery_and_watchdog(self) -> None:
        for changes in ({}, {"recovery_verified": True}, {"watchdog_active": True}):
            with self.assertRaises(subject.GraphicalHandoffError):
                subject.advance_handoff(initial(), "request-open", **changes)

    def test_no_incoming_session_is_revealed_without_readiness(self) -> None:
        record = subject.advance_handoff(initial(), "request-open", recovery_verified=True, watchdog_active=True)
        record = subject.advance_handoff(record, "outgoing-stopped", outgoing_release_verified=True)
        record = subject.advance_handoff(record, "start-workload")
        with self.assertRaisesRegex(subject.GraphicalHandoffError, "readiness"):
            subject.advance_handoff(record, "workload-ready")

    def test_readiness_cannot_be_replayed_for_hub_return(self) -> None:
        record = subject.advance_handoff(initial(), "request-open", recovery_verified=True, watchdog_active=True)
        record = subject.advance_handoff(record, "outgoing-stopped", outgoing_release_verified=True)
        record = subject.advance_handoff(record, "start-workload")
        record = subject.advance_handoff(record, "workload-ready", incoming_readiness_verified=True)
        record = subject.advance_handoff(record, "request-return")
        record = subject.advance_handoff(record, "workload-stopped", outgoing_release_verified=True)
        record = subject.advance_handoff(record, "start-hub")
        with self.assertRaisesRegex(subject.GraphicalHandoffError, "readiness"):
            subject.advance_handoff(record, "hub-ready")

    def test_lost_watchdog_blocks_progress_but_allows_recovery(self) -> None:
        record = subject.advance_handoff(initial(), "request-open", recovery_verified=True, watchdog_active=True)
        with self.assertRaisesRegex(subject.GraphicalHandoffError, "watchdog"):
            subject.advance_handoff(record, "outgoing-stopped", watchdog_active=False, outgoing_release_verified=True)
        recovered = subject.advance_handoff(record, "fail", watchdog_active=False)
        self.assertEqual(recovered.phase, "recovery")

    def test_failure_enters_terminal_broker_owned_recovery(self) -> None:
        record = subject.advance_handoff(initial(), "fail")
        self.assertEqual((record.phase, record.seat_owner), ("recovery", "broker"))
        with self.assertRaisesRegex(subject.GraphicalHandoffError, "terminal"):
            subject.advance_handoff(record, "hub-ready", incoming_readiness_verified=True)

    def test_tampering_replay_wrong_order_and_hub_target_fail_closed(self) -> None:
        with self.assertRaises(subject.GraphicalHandoffError):
            subject.new_handoff("handoff-" + "1" * 64, 3, "hub", 8)
        with self.assertRaises(subject.GraphicalHandoffError):
            subject.advance_handoff(replace(initial(), seat_owner="university"), "fail")
        with self.assertRaises(subject.GraphicalHandoffError):
            subject.advance_handoff(initial(), "hub-ready", incoming_readiness_verified=True)

    def test_fake_executor_rehearses_complete_button_cycle(self) -> None:
        result = subject.rehearse_handoff_cycle(initial())
        self.assertEqual(result.classification, "passed-fake-cycle")
        self.assertEqual((result.final_phase, result.final_seat_owner), ("hub-active", "hub"))
        self.assertIn("workload-active", result.phases)
        self.assertEqual(len(result.record_digest), 64)

    def test_fake_executor_failure_at_every_effect_enters_safe_recovery(self) -> None:
        for event in (
            "request-open", "outgoing-stopped", "start-workload", "workload-ready",
            "request-return", "workload-stopped", "start-hub", "hub-ready",
        ):
            result = subject.rehearse_handoff_cycle(initial(), fail_before=event)
            self.assertEqual(result.classification, "safe-recovery", event)
            self.assertEqual((result.final_phase, result.final_seat_owner), ("recovery", "broker"))

    def test_fake_executor_rejects_unknown_failure_point(self) -> None:
        with self.assertRaises(subject.GraphicalHandoffError):
            subject.rehearse_handoff_cycle(initial(), fail_before="run-caller-command")
