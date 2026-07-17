from dataclasses import replace
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_hyprland_h0 as h0
import apx_hyprland_h0_journal as journal
from tests.test_apx_hyprland_h0 import evidence


APPROVAL = "a" * 64


def preview() -> h0.H0Preview:
    return h0.build_h0_preview(evidence())


def initial() -> journal.H0Record:
    return journal.create_h0_record(preview(), physical_approval_digest=APPROVAL)


def advance(record: journal.H0Record, count: int) -> journal.H0Record:
    current = record
    for index in range(count):
        current = journal.prepare_next_effect(current)
        current = journal.record_effect_success(
            current, evidence_digest=f"{(index + 1) % 16:x}" * 64
        )
    return current


class H0JournalTests(unittest.TestCase):
    def test_complete_experiment_returns_only_after_headless_restore(self) -> None:
        record = advance(initial(), len(h0.H0_EFFECTS))
        self.assertEqual(record.status, "headless-restored")
        recovery = journal.assess_h0_recovery(record)
        self.assertEqual(recovery.classification, "complete-headless-restored")
        self.assertTrue(recovery.headless_hub_restore_claimed)
        self.assertFalse(recovery.automatic_cleanup_allowed)

    def test_prepare_and_evidence_are_required_for_every_effect(self) -> None:
        record = initial()
        with self.assertRaises(journal.H0JournalError):
            journal.record_effect_success(record, evidence_digest="1" * 64)
        prepared = journal.prepare_next_effect(record)
        self.assertEqual(prepared.prepared_effect, h0.H0_EFFECTS[0])
        with self.assertRaises(journal.H0JournalError):
            journal.record_effect_success(prepared, evidence_digest="short")
        completed = journal.record_effect_success(prepared, evidence_digest="1" * 64)
        self.assertEqual(completed.completed_effects, h0.H0_EFFECTS[:1])

    def test_blocked_preview_and_bad_approval_are_rejected(self) -> None:
        blocked = h0.build_h0_preview(replace(evidence(), nvidia_excluded=False))
        with self.assertRaises(journal.H0JournalError):
            journal.create_h0_record(blocked, physical_approval_digest=APPROVAL)
        with self.assertRaises(journal.H0JournalError):
            journal.create_h0_record(preview(), physical_approval_digest="short")

    def test_every_interruption_uses_recovery_vt_and_never_restarts_graphics(self) -> None:
        cases = (
            (initial(), "no-effect-recorded", False),
            (journal.prepare_next_effect(initial()), "effect-outcome-unknown", True),
            (advance(initial(), 3), "partial-lease-preparation", True),
            (advance(initial(), 6), "graphical-session-may-be-active", True),
            (advance(initial(), 9), "partial-teardown", True),
            (
                journal.mark_h0_uncertain(
                    advance(initial(), 7), reason="compositor stopped responding"
                ),
                "preserve-and-inspect-from-recovery-vt",
                True,
            ),
        )
        for record, expected, recovery_required in cases:
            with self.subTest(expected=expected):
                result = journal.assess_h0_recovery(record)
                self.assertEqual(result.classification, expected)
                self.assertEqual(result.recovery_vt_required, recovery_required)
                self.assertFalse(result.automatic_graphical_restart_allowed)
                self.assertFalse(result.automatic_cleanup_allowed)
                self.assertFalse(result.headless_hub_restore_claimed)

    def test_tampering_steps_status_and_digests_is_rejected(self) -> None:
        record = initial()
        variants = (
            replace(record, status="headless-restored"),
            replace(record, completed_effects=(record.effects[1],)),
            replace(record, effects=tuple(reversed(record.effects))),
            replace(record, evidence_digest="f" * 64),
            replace(record, record_digest="f" * 64),
        )
        for value in variants:
            with self.subTest(value=value):
                with self.assertRaises(journal.H0JournalError):
                    journal.validate_h0_record(value)

    def test_uncertain_state_is_terminal(self) -> None:
        uncertain = journal.mark_h0_uncertain(
            advance(initial(), 1), reason="fixture interruption"
        )
        with self.assertRaises(journal.H0JournalError):
            journal.prepare_next_effect(uncertain)
        with self.assertRaises(journal.H0JournalError):
            journal.mark_h0_uncertain(uncertain, reason="again")


class FixtureH0StoreTests(unittest.TestCase):
    def test_compare_and_swap_rejects_replay_stale_and_jump(self) -> None:
        first = initial()
        store = journal.FixtureH0Store(plan_digest=first.plan_digest)
        store.publish_new(first)
        with self.assertRaises(journal.H0JournalError):
            store.publish_new(first)
        second = journal.prepare_next_effect(first)
        store.compare_and_swap(second, expected_digest=first.record_digest)
        with self.assertRaisesRegex(journal.H0JournalError, "stale"):
            store.compare_and_swap(second, expected_digest=first.record_digest)
        jumped = journal.record_effect_success(second, evidence_digest="1" * 64)
        jumped = journal.prepare_next_effect(jumped)
        with self.assertRaises(journal.H0JournalError):
            store.compare_and_swap(jumped, expected_digest=second.record_digest)

    def test_store_accepts_only_exact_bound_initial_record(self) -> None:
        first = initial()
        wrong = journal.FixtureH0Store(plan_digest="f" * 64)
        with self.assertRaises(journal.H0JournalError):
            wrong.publish_new(first)
        proper = journal.FixtureH0Store(plan_digest=first.plan_digest)
        with self.assertRaises(journal.H0JournalError):
            proper.publish_new(journal.prepare_next_effect(first))


if __name__ == "__main__":
    unittest.main()
