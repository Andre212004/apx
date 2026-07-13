from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_release_candidate as candidate
import apx_release_promotion as promotion
from tests.test_apx_release_candidate import valid_candidate


OPERATION = "promotion-" + "e" * 32
IMPORT_APPROVAL = "f" * 64
ADMISSION_APPROVAL = "0" * 64


def initial() -> promotion.PromotionRecord:
    return promotion.create_promotion_record(
        candidate.build_import_plan(valid_candidate()),
        operation_id=OPERATION,
        import_approval_digest=IMPORT_APPROVAL,
    )


def advance(record: promotion.PromotionRecord, count: int) -> promotion.PromotionRecord:
    current = record
    for index in range(count):
        current = promotion.prepare_next_step(current)
        current = promotion.record_step_success(current, evidence_digest=f"{index + 1:x}" * 64)
    return current


class PromotionStateMachineTests(unittest.TestCase):
    def test_import_verification_and_admission_are_separate(self) -> None:
        record = advance(initial(), promotion.IMPORT_STEP_COUNT)
        self.assertEqual(record.status, "quarantined")
        record = advance(record, promotion.VERIFICATION_STEP_COUNT - promotion.IMPORT_STEP_COUNT)
        self.assertEqual(record.status, "verified-awaiting-admission")
        with self.assertRaisesRegex(promotion.PromotionError, "separate admission"):
            promotion.prepare_next_step(record)
        record = promotion.bind_admission_approval(record, admission_approval_digest=ADMISSION_APPROVAL)
        record = advance(record, len(record.steps) - len(record.completed_steps))
        self.assertEqual(record.status, "admitted")
        release = promotion.build_catalogue_release(record)
        self.assertEqual(release.release_id, "release-" + record.candidate_digest)
        self.assertEqual(len(release.catalogue_digest), 64)

    def test_effect_order_prepare_and_evidence_are_mandatory(self) -> None:
        record = initial()
        with self.assertRaises(promotion.PromotionError):
            promotion.record_step_success(record, evidence_digest="1" * 64)
        prepared = promotion.prepare_next_step(record)
        self.assertEqual(prepared.prepared_step, record.steps[0])
        with self.assertRaises(promotion.PromotionError):
            promotion.record_step_success(prepared, evidence_digest="short")
        completed = promotion.record_step_success(prepared, evidence_digest="1" * 64)
        self.assertEqual(completed.completed_steps, record.steps[:1])
        self.assertEqual(completed.previous_digest, prepared.record_digest)

    def test_tampering_direct_transition_and_early_approval_fail(self) -> None:
        record = initial()
        variants = (
            replace(record, candidate_digest="9" * 64),
            replace(record, completed_steps=(record.steps[1],)),
            replace(record, status="admitted"),
            replace(record, admission_approval_digest=ADMISSION_APPROVAL),
        )
        for value in variants:
            with self.assertRaises(promotion.PromotionError):
                promotion.validate_promotion_record(value)

    def test_interruption_recovery_never_auto_deletes(self) -> None:
        cases = (
            (initial(), "no-effect"),
            (promotion.prepare_next_step(initial()), "preserve-effect-outcome-uncertain"),
            (advance(initial(), 1), "preserve-partial-import"),
            (advance(initial(), 4), "preserve-quarantine-review"),
            (advance(initial(), 8), "verified-awaiting-new-admission-approval"),
        )
        for record, expected in cases:
            with self.subTest(expected=expected):
                recovery = promotion.assess_promotion_recovery(record)
                self.assertEqual(recovery.classification, expected)
                self.assertFalse(recovery.automatic_deletion_allowed)

    def test_incomplete_is_terminal_and_preserved(self) -> None:
        incomplete = promotion.mark_promotion_incomplete(
            advance(initial(), 2), reason="fixture interruption"
        )
        self.assertEqual(incomplete.status, "incomplete")
        with self.assertRaises(promotion.PromotionError):
            promotion.prepare_next_step(incomplete)
        with self.assertRaises(promotion.PromotionError):
            promotion.mark_promotion_incomplete(incomplete, reason="again")


class FixturePromotionStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.plan = candidate.build_import_plan(valid_candidate())
        self.store = promotion.FixturePromotionStore(self.plan)

    def test_compare_and_swap_rejects_replay_and_stale_writer(self) -> None:
        first = initial()
        self.store.publish_new(first)
        with self.assertRaises(promotion.PromotionError):
            self.store.publish_new(first)
        second = promotion.prepare_next_step(first)
        self.store.compare_and_swap(second, expected_digest=first.record_digest)
        with self.assertRaisesRegex(promotion.PromotionError, "stale"):
            self.store.compare_and_swap(second, expected_digest=first.record_digest)
        self.assertEqual(self.store.read(OPERATION), second)

    def test_store_rejects_forged_initial_completion_and_multi_step_jump(self) -> None:
        forged_initial = advance(initial(), 1)
        with self.assertRaisesRegex(promotion.PromotionError, "exact initial"):
            self.store.publish_new(forged_initial)

        first = initial()
        self.store.publish_new(first)
        jumped = advance(first, 2)
        forged_jump = promotion._with_digest(
            replace(
                jumped,
                sequence=first.sequence + 1,
                previous_digest=first.record_digest,
                record_digest="",
            )
        )
        with self.assertRaisesRegex(promotion.PromotionError, "single step"):
            self.store.compare_and_swap(
                forged_jump, expected_digest=first.record_digest
            )

    def test_store_rejects_initial_record_for_another_plan(self) -> None:
        other_candidate = replace(valid_candidate(), artifact_sha256="c" * 64)
        other_record = promotion.create_promotion_record(
            candidate.build_import_plan(other_candidate),
            operation_id=OPERATION,
            import_approval_digest=IMPORT_APPROVAL,
        )
        with self.assertRaisesRegex(promotion.PromotionError, "allowed import plan"):
            self.store.publish_new(other_record)

    def test_catalogue_requires_exact_admitted_record_and_no_overwrite(self) -> None:
        record = initial()
        self.store.publish_new(record)
        while len(record.completed_steps) < promotion.VERIFICATION_STEP_COUNT:
            next_record = promotion.prepare_next_step(record)
            self.store.compare_and_swap(next_record, expected_digest=record.record_digest)
            record = next_record
            next_record = promotion.record_step_success(record, evidence_digest="a" * 64)
            self.store.compare_and_swap(next_record, expected_digest=record.record_digest)
            record = next_record
        next_record = promotion.bind_admission_approval(record, admission_approval_digest=ADMISSION_APPROVAL)
        self.store.compare_and_swap(next_record, expected_digest=record.record_digest)
        record = next_record
        while len(record.completed_steps) < len(record.steps):
            next_record = promotion.prepare_next_step(record)
            self.store.compare_and_swap(next_record, expected_digest=record.record_digest)
            record = next_record
            next_record = promotion.record_step_success(record, evidence_digest="b" * 64)
            self.store.compare_and_swap(next_record, expected_digest=record.record_digest)
            record = next_record
        release = promotion.build_catalogue_release(record)
        self.store.publish_catalogue(release)
        self.assertEqual(self.store.catalogue_release(release.release_id), release)
        with self.assertRaises(promotion.PromotionError):
            self.store.publish_catalogue(release)
        with self.assertRaises(promotion.PromotionError):
            self.store.publish_catalogue(replace(release, candidate_digest="c" * 64))


if __name__ == "__main__":
    unittest.main()
