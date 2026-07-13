from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_clean_install_dossier as dossier
import apx_clean_install_journal as journal
from tests.test_apx_clean_install_dossier import supply, target


OPERATION = "install-" + "1" * 32


def initial() -> journal.CleanInstallRecord:
    return journal.create_install_record(
        dossier.build_dossier(target(), supply()), operation_id=OPERATION
    )


def ready_dossier() -> dossier.CleanInstallDossier:
    return dossier.build_dossier(target(), supply())


def approval_for(record: journal.CleanInstallRecord) -> journal.CleanInstallRecord:
    stage = journal.current_stage(record)
    required = journal.REQUIRED_APPROVAL[stage]
    if required is None:
        return record
    if any(item.stage == stage for item in record.approvals):
        return record
    return journal.bind_stage_approval(
        record, stage=stage, approval_class=required,
        approval_digest=f"{journal.STAGES.index(stage) + 1:x}" * 64,
    )


def one_effect(record: journal.CleanInstallRecord, evidence="a" * 64):
    current = approval_for(record)
    current = journal.prepare_next_effect(current)
    return journal.record_effect_success(current, evidence_digest=evidence)


class InstallJournalTests(unittest.TestCase):
    def test_blocked_dossier_cannot_start(self) -> None:
        blocked = dossier.build_dossier(
            replace(target(), backup_sample_restore_passed=False), supply()
        )
        with self.assertRaises(journal.CleanInstallJournalError):
            journal.create_install_record(blocked, operation_id=OPERATION)

    def test_stage_order_and_approval_are_exact(self) -> None:
        record = initial()
        self.assertEqual(journal.current_stage(record), "observe")
        while journal.current_stage(record) in {"observe", "dossier"}:
            record = one_effect(record)
        self.assertEqual(journal.current_stage(record), "approve-disk")
        with self.assertRaisesRegex(journal.CleanInstallJournalError, "approval"):
            journal.prepare_next_effect(record)
        with self.assertRaises(journal.CleanInstallJournalError):
            journal.bind_stage_approval(
                record, stage="storage", approval_class="strong-confirmation",
                approval_digest="b" * 64,
            )
        approved = approval_for(record)
        record = journal.prepare_next_effect(approved)
        self.assertTrue(record.prepared_effect.startswith("approve-disk:"))

    def test_storage_needs_its_own_strong_approval(self) -> None:
        record = initial()
        while journal.current_stage(record) != "storage":
            record = one_effect(record)
        stages = {item.stage for item in record.approvals}
        self.assertIn("approve-disk", stages)
        self.assertNotIn("storage", stages)
        with self.assertRaises(journal.CleanInstallJournalError):
            journal.prepare_next_effect(record)
        self.assertEqual(approval_for(record).approvals[-1].stage, "storage")

    def test_full_fake_install_requires_every_effect_and_final_evidence(self) -> None:
        record = initial()
        counter = 1
        while journal.current_stage(record) is not None:
            record = one_effect(record, evidence=f"{counter % 15 + 1:x}" * 64)
            counter += 1
        self.assertEqual(record.status, "verifying-final")
        self.assertEqual(record.completed_effects, record.effects)
        completed = journal.complete_install(record, final_evidence_digest="f" * 64)
        self.assertEqual(completed.status, "complete")
        self.assertEqual(journal.assess_install_recovery(completed).classification, "complete")

    def test_recovery_changes_after_storage_and_never_auto_deletes(self) -> None:
        record = initial()
        self.assertEqual(journal.assess_install_recovery(record).classification, "no-effect")
        prepared = journal.prepare_next_effect(record)
        self.assertEqual(
            journal.assess_install_recovery(prepared).classification,
            "preserve-effect-outcome-uncertain",
        )
        record = initial()
        while journal.current_stage(record) != "storage":
            record = one_effect(record)
        before = journal.assess_install_recovery(record)
        self.assertEqual(before.classification, "restart-read-only-foundation")
        record = one_effect(record)
        after = journal.assess_install_recovery(record)
        self.assertEqual(after.classification, "destructive-recovery-required")
        self.assertFalse(after.automatic_deletion_allowed)

    def test_tampering_skip_and_early_approval_fail(self) -> None:
        record = initial()
        variants = (
            replace(record, target_id="other"),
            replace(record, completed_effects=(record.effects[1],), effect_evidence_digests=("a" * 64,)),
            replace(record, status="complete", final_evidence_digest="f" * 64),
            replace(record, approvals=(journal.StageApproval("storage", "strong-confirmation", "a" * 64),)),
        )
        for value in variants:
            with self.assertRaises(journal.CleanInstallJournalError):
                journal.validate_install_record(value)


class FixtureInstallStoreTests(unittest.TestCase):
    def test_store_accepts_only_exact_single_transitions(self) -> None:
        store = journal.FixtureInstallStore(ready_dossier())
        first = initial()
        store.publish_new(first)
        second = journal.prepare_next_effect(first)
        store.compare_and_swap(second, expected_digest=first.record_digest)
        with self.assertRaisesRegex(journal.CleanInstallJournalError, "stale"):
            store.compare_and_swap(second, expected_digest=first.record_digest)

        third = journal.record_effect_success(second, evidence_digest="a" * 64)
        fourth = journal.prepare_next_effect(third)
        forged = journal._with_digest(replace(
            fourth, sequence=second.sequence + 1,
            previous_digest=second.record_digest, record_digest="",
        ))
        with self.assertRaisesRegex(journal.CleanInstallJournalError, "one allowed"):
            store.compare_and_swap(forged, expected_digest=second.record_digest)

    def test_incomplete_is_terminal_and_preserved(self) -> None:
        store = journal.FixtureInstallStore(ready_dossier())
        first = initial()
        store.publish_new(first)
        incomplete = journal.mark_install_incomplete(first, reason="fixture stop")
        store.compare_and_swap(incomplete, expected_digest=first.record_digest)
        with self.assertRaises(journal.CleanInstallJournalError):
            journal.prepare_next_effect(incomplete)
        self.assertFalse(
            journal.assess_install_recovery(incomplete).automatic_deletion_allowed
        )

    def test_store_rejects_initial_record_for_another_dossier(self) -> None:
        store = journal.FixtureInstallStore(ready_dossier())
        other_dossier = dossier.build_dossier(
            replace(target(), hostname="other-host"), supply()
        )
        other_record = journal.create_install_record(
            other_dossier, operation_id=OPERATION
        )
        with self.assertRaisesRegex(journal.CleanInstallJournalError, "allowed dossier"):
            store.publish_new(other_record)


if __name__ == "__main__":
    unittest.main()
