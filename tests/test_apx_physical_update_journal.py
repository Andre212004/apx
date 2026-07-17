from dataclasses import replace
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_physical_update as update
import apx_physical_update_journal as journal
from tests.test_apx_physical_update import candidate, installed


IMPORT_APPROVAL = "a" * 64
ACTIVATION_APPROVAL = "b" * 64


def preview() -> update.PhysicalUpdatePreview:
    return update.build_update_preview(candidate(), installed())


def initial() -> journal.PhysicalUpdateRecord:
    return journal.create_update_record(
        preview(), import_approval_digest=IMPORT_APPROVAL
    )


def advance(record: journal.PhysicalUpdateRecord, count: int) -> journal.PhysicalUpdateRecord:
    current = record
    for index in range(count):
        current = journal.prepare_next_effect(current)
        current = journal.record_effect_success(
            current, evidence_digest=f"{(index + 1) % 16:x}" * 64
        )
    return current


class PhysicalUpdateJournalTests(unittest.TestCase):
    def test_import_and_activation_approvals_are_separate(self) -> None:
        record = advance(initial(), journal.ACTIVATION_BOUNDARY)
        self.assertEqual(record.status, "verified-awaiting-activation-approval")
        with self.assertRaisesRegex(journal.PhysicalUpdateJournalError, "activation approval"):
            journal.prepare_next_effect(record)
        record = journal.bind_activation_approval(
            record, activation_approval_digest=ACTIVATION_APPROVAL
        )
        record = advance(record, len(record.effects) - len(record.completed_effects))
        self.assertEqual(record.status, "installed-rollback-retained")
        recovery = journal.assess_update_recovery(record)
        self.assertEqual(recovery.classification, "complete-with-rollback-retained")
        self.assertFalse(recovery.automatic_rollback_allowed)

    def test_prepare_and_evidence_are_required_for_every_effect(self) -> None:
        record = initial()
        with self.assertRaises(journal.PhysicalUpdateJournalError):
            journal.record_effect_success(record, evidence_digest="1" * 64)
        prepared = journal.prepare_next_effect(record)
        self.assertEqual(prepared.prepared_effect, update.UPDATE_EFFECTS[0])
        with self.assertRaises(journal.PhysicalUpdateJournalError):
            journal.record_effect_success(prepared, evidence_digest="short")
        completed = journal.record_effect_success(prepared, evidence_digest="1" * 64)
        self.assertEqual(completed.completed_effects, update.UPDATE_EFFECTS[:1])

    def test_blocked_preview_and_malformed_approvals_are_rejected(self) -> None:
        blocked = update.build_update_preview(candidate(), replace(installed(), audit_reconciled=False))
        with self.assertRaises(journal.PhysicalUpdateJournalError):
            journal.create_update_record(blocked, import_approval_digest=IMPORT_APPROVAL)
        with self.assertRaises(journal.PhysicalUpdateJournalError):
            journal.create_update_record(preview(), import_approval_digest="short")
        verified = advance(initial(), journal.ACTIVATION_BOUNDARY)
        with self.assertRaises(journal.PhysicalUpdateJournalError):
            journal.bind_activation_approval(verified, activation_approval_digest="short")

    def test_interruption_recovery_never_auto_rolls_back_or_cleans(self) -> None:
        verified = advance(initial(), journal.ACTIVATION_BOUNDARY)
        approved = journal.bind_activation_approval(
            verified, activation_approval_digest=ACTIVATION_APPROVAL
        )
        cases = (
            (initial(), "no-effect-recorded"),
            (journal.prepare_next_effect(initial()), "preserve-effect-outcome-uncertain"),
            (advance(initial(), 2), "preserve-private-staging"),
            (verified, "verified-awaiting-new-activation-approval"),
            (advance(approved, 2), "preserve-partial-activation-with-rollback"),
            (journal.mark_update_uncertain(approved, reason="power loss"), "preserve-and-inspect"),
        )
        for record, expected in cases:
            with self.subTest(expected=expected):
                result = journal.assess_update_recovery(record)
                self.assertEqual(result.classification, expected)
                self.assertFalse(result.automatic_rollback_allowed)
                self.assertFalse(result.automatic_cleanup_allowed)

    def test_tampering_steps_status_progress_and_digests_is_rejected(self) -> None:
        record = initial()
        variants = (
            replace(record, status="installed-rollback-retained"),
            replace(record, completed_effects=(record.effects[1],)),
            replace(record, effects=tuple(reversed(record.effects))),
            replace(record, candidate_digest="f" * 64),
            replace(record, record_digest="f" * 64),
        )
        for value in variants:
            with self.subTest(value=value):
                with self.assertRaises(journal.PhysicalUpdateJournalError):
                    journal.validate_update_record(value)

    def test_uncertain_is_terminal_and_preserved(self) -> None:
        uncertain = journal.mark_update_uncertain(
            advance(initial(), 1), reason="fixture interruption"
        )
        with self.assertRaises(journal.PhysicalUpdateJournalError):
            journal.prepare_next_effect(uncertain)
        with self.assertRaises(journal.PhysicalUpdateJournalError):
            journal.mark_update_uncertain(uncertain, reason="again")


class FixturePhysicalUpdateStoreTests(unittest.TestCase):
    def test_compare_and_swap_rejects_replay_stale_and_jump(self) -> None:
        first = initial()
        store = journal.FixturePhysicalUpdateStore(plan_digest=first.plan_digest)
        store.publish_new(first)
        with self.assertRaises(journal.PhysicalUpdateJournalError):
            store.publish_new(first)
        second = journal.prepare_next_effect(first)
        store.compare_and_swap(second, expected_digest=first.record_digest)
        with self.assertRaisesRegex(journal.PhysicalUpdateJournalError, "stale"):
            store.compare_and_swap(second, expected_digest=first.record_digest)
        jumped = journal.record_effect_success(second, evidence_digest="1" * 64)
        jumped = journal.prepare_next_effect(jumped)
        with self.assertRaises(journal.PhysicalUpdateJournalError):
            store.compare_and_swap(jumped, expected_digest=second.record_digest)

    def test_store_accepts_only_exact_bound_initial_record(self) -> None:
        first = initial()
        wrong = journal.FixturePhysicalUpdateStore(plan_digest="f" * 64)
        with self.assertRaises(journal.PhysicalUpdateJournalError):
            wrong.publish_new(first)
        proper = journal.FixturePhysicalUpdateStore(plan_digest=first.plan_digest)
        with self.assertRaises(journal.PhysicalUpdateJournalError):
            proper.publish_new(journal.prepare_next_effect(first))


if __name__ == "__main__":
    unittest.main()
