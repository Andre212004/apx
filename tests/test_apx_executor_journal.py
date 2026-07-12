from __future__ import annotations

from dataclasses import asdict, replace
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_executor_contract
import apx_executor_journal as journal


OPERATION_ID = "op-" + "1" * 32
APPROVAL_ID = "approval-" + "2" * 32
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64
DIGEST_C = "c" * 64


def new_journal():
    plan = apx_executor_contract.build_operation_plan("create", "trial", 0)
    return journal.create_journal(
        plan,
        operation_id=OPERATION_ID,
        request_digest=DIGEST_A,
        approval_id=APPROVAL_ID,
        nonce_digest=DIGEST_B,
    )


def resource(
    resource_id="trial-root",
    *,
    state="owned-empty",
    published=False,
    used=False,
    modified=False,
    identity=DIGEST_C,
):
    return journal.JournalResource(
        resource_id=resource_id,
        resource_type="root",
        identity_digest=identity,
        state=state,
        published=published,
        used=used,
        modified=modified,
    )


class JournalStateMachineTests(unittest.TestCase):
    def test_new_journal_is_deterministic_valid_and_contains_no_raw_nonce(self) -> None:
        first = new_journal()
        second = new_journal()
        self.assertEqual(first, second)
        self.assertEqual(first.status, "reserved")
        self.assertEqual(first.sequence, 0)
        self.assertEqual(len(first.journal_digest), 64)
        serialized = journal.serialize_journal(first)
        self.assertNotIn("nonce\"", serialized)
        self.assertIn("nonce_digest", serialized)

    def test_effect_must_be_prepared_before_success_and_order_is_exact(self) -> None:
        initial = new_journal()
        with self.assertRaises(journal.JournalError):
            journal.record_effect_success(initial)
        prepared = journal.prepare_next_effect(initial)
        self.assertEqual(prepared.prepared_effect, initial.effects[0])
        complete = journal.record_effect_success(prepared)
        self.assertEqual(complete.completed_effects, initial.effects[:1])
        self.assertIsNone(complete.prepared_effect)

    def test_full_operation_requires_every_effect_and_final_evidence(self) -> None:
        current = new_journal()
        with self.assertRaises(journal.JournalError):
            journal.begin_final_verification(current)
        for _ in current.effects:
            current = journal.prepare_next_effect(current)
            current = journal.record_effect_success(current)
        current = journal.begin_final_verification(current)
        self.assertEqual(current.status, "verifying-final")
        completed = journal.complete_journal(current, final_evidence_digest=DIGEST_C)
        self.assertEqual(completed.status, "complete")
        self.assertEqual(completed.completed_effects, completed.effects)
        self.assertEqual(completed.recovery_class, "none")

    def test_each_transition_binds_previous_digest_and_increments_sequence(self) -> None:
        first = new_journal()
        second = journal.prepare_next_effect(first)
        third = journal.record_effect_success(second)
        self.assertEqual(second.previous_digest, first.journal_digest)
        self.assertEqual(third.previous_digest, second.journal_digest)
        self.assertEqual((first.sequence, second.sequence, third.sequence), (0, 1, 2))
        self.assertEqual(len({first.journal_digest, second.journal_digest, third.journal_digest}), 3)

    def test_tampered_content_digest_order_and_prepared_effect_are_rejected(self) -> None:
        initial = new_journal()
        variants = (
            replace(initial, logical_name="other"),
            replace(initial, completed_effects=(initial.effects[1],)),
            replace(initial, status="effect-prepared", prepared_effect=initial.effects[1]),
        )
        for variant in variants:
            with self.assertRaises(journal.JournalError):
                journal.validate_journal(variant)

    def test_resource_identity_cannot_change_during_operation(self) -> None:
        prepared = journal.prepare_next_effect(new_journal())
        current = journal.record_effect_success(prepared, resources=(resource(),))
        prepared = journal.prepare_next_effect(current)
        with self.assertRaisesRegex(journal.JournalError, "identity changed"):
            journal.record_effect_success(
                prepared,
                resources=(resource(identity="d" * 64),),
            )

    def test_terminal_state_cannot_continue_or_be_reclassified(self) -> None:
        incomplete = journal.mark_incomplete(new_journal(), reason="fixture interruption")
        with self.assertRaises(journal.JournalError):
            journal.prepare_next_effect(incomplete)
        with self.assertRaises(journal.JournalError):
            journal.mark_incomplete(incomplete, reason="again")


class RecoveryTests(unittest.TestCase):
    def test_no_recorded_effect_is_no_effect(self) -> None:
        result = journal.assess_recovery(
            new_journal(), approval_still_valid=False, gates_confirmed=False
        )
        self.assertEqual(result.classification, "no-effect")
        self.assertFalse(result.automatic_deletion_allowed)

    def test_prepared_effect_is_always_preserved_as_uncertain(self) -> None:
        prepared = journal.prepare_next_effect(new_journal())
        result = journal.assess_recovery(
            prepared, approval_still_valid=True, gates_confirmed=True
        )
        self.assertEqual(result.classification, "preserve-effect-outcome-uncertain")
        self.assertFalse(result.continuation_allowed)

    def test_only_owned_empty_unpublished_resources_allow_automatic_rollback(self) -> None:
        prepared = journal.prepare_next_effect(new_journal())
        current = journal.record_effect_success(prepared, resources=(resource(),))
        result = journal.assess_recovery(
            current, approval_still_valid=False, gates_confirmed=False
        )
        self.assertEqual(result.classification, "automatic-rollback-eligible")
        self.assertTrue(result.automatic_deletion_allowed)

    def test_modified_used_published_foreign_and_uncertain_are_preserved(self) -> None:
        cases = (
            resource(state="owned-modified", modified=True),
            resource(state="owned-modified", used=True),
            resource(state="published", published=True),
            resource(state="foreign-or-conflicting"),
            resource(state="identity-uncertain", identity=None),
        )
        for item in cases:
            prepared = journal.prepare_next_effect(new_journal())
            current = journal.record_effect_success(prepared, resources=(item,))
            result = journal.assess_recovery(
                current, approval_still_valid=True, gates_confirmed=True
            )
            self.assertFalse(result.automatic_deletion_allowed)
            self.assertFalse(result.continuation_allowed)
            self.assertTrue(result.classification.startswith("preserve-"))

    def test_continuation_requires_current_approval_and_gates(self) -> None:
        prepared = journal.prepare_next_effect(new_journal())
        current = journal.record_effect_success(prepared)
        accepted = journal.assess_recovery(
            current, approval_still_valid=True, gates_confirmed=True
        )
        rejected = journal.assess_recovery(
            current, approval_still_valid=False, gates_confirmed=True
        )
        self.assertTrue(accepted.continuation_allowed)
        self.assertEqual(rejected.classification, "preserve-recovery-required")


class ParserTests(unittest.TestCase):
    def test_canonical_round_trip(self) -> None:
        value = new_journal()
        self.assertEqual(journal.parse_journal(journal.serialize_journal(value)), value)

    def test_duplicate_unknown_missing_wrong_typed_and_oversized_data_are_rejected(self) -> None:
        value = new_journal()
        canonical = journal.serialize_journal(value).strip()
        duplicate = canonical[:-1] + ',"status":"reserved"}'
        with self.assertRaises(journal.JournalError):
            journal.parse_journal(duplicate)

        payload = asdict(value)
        payload["command"] = "rm -rf /"
        with self.assertRaises(journal.JournalError):
            journal.parse_journal(json.dumps(payload))
        del payload["command"]
        del payload["approval_id"]
        with self.assertRaises(journal.JournalError):
            journal.parse_journal(json.dumps(payload))

        payload = asdict(value)
        payload["sequence"] = True
        payload["journal_digest"] = value.journal_digest
        with self.assertRaises(journal.JournalError):
            journal.parse_journal(json.dumps(payload))

        with self.assertRaises(journal.JournalError):
            journal.parse_journal(" " * (journal.MAX_JOURNAL_BYTES + 1))

    def test_resource_extensions_and_non_boolean_flags_are_rejected(self) -> None:
        prepared = journal.prepare_next_effect(new_journal())
        value = journal.record_effect_success(prepared, resources=(resource(),))
        payload = asdict(value)
        payload["resources"][0]["path"] = "/host"
        with self.assertRaises(journal.JournalError):
            journal.parse_journal(json.dumps(payload))
        payload = asdict(value)
        payload["resources"][0]["used"] = 1
        with self.assertRaises(journal.JournalError):
            journal.parse_journal(json.dumps(payload))


class FixtureStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.store = journal.FixtureJournalStore(self.root)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_create_read_and_mode(self) -> None:
        value = new_journal()
        self.store.create(value)
        path = self.root / f"{OPERATION_ID}.json"
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
        self.assertEqual(self.store.read(OPERATION_ID), value)
        self.assertEqual(list(self.root.glob(".*.tmp")), [])

    def test_create_refuses_existing_journal(self) -> None:
        value = new_journal()
        self.store.create(value)
        with self.assertRaisesRegex(journal.JournalStoreError, "already exists"):
            self.store.create(value)

    def test_update_is_atomic_and_rejects_stale_writer(self) -> None:
        first = new_journal()
        self.store.create(first)
        second = journal.prepare_next_effect(first)
        self.store.update(second, expected_previous_digest=first.journal_digest)
        self.assertEqual(self.store.read(OPERATION_ID), second)
        third_from_stale = journal.prepare_next_effect(first)
        with self.assertRaisesRegex(journal.JournalStoreError, "changed since"):
            self.store.update(
                third_from_stale, expected_previous_digest=first.journal_digest
            )
        self.assertEqual(self.store.read(OPERATION_ID), second)

    def test_symlink_root_file_wrong_mode_and_corrupt_content_are_rejected(self) -> None:
        value = new_journal()
        outside = self.root / "outside"
        outside.mkdir()
        symlink = self.root / "link"
        symlink.symlink_to(outside, target_is_directory=True)
        with self.assertRaises(journal.JournalStoreError):
            journal.FixtureJournalStore(symlink).create(value)

        self.store.create(value)
        path = self.root / f"{OPERATION_ID}.json"
        path.chmod(0o644)
        with self.assertRaisesRegex(journal.JournalStoreError, "mode"):
            self.store.read(OPERATION_ID)
        path.chmod(0o600)
        path.write_text("{broken", encoding="utf-8")
        path.chmod(0o600)
        with self.assertRaisesRegex(journal.JournalStoreError, "content"):
            self.store.read(OPERATION_ID)

    def test_symlink_journal_is_not_followed(self) -> None:
        target = self.root / "target"
        target.write_text(journal.serialize_journal(new_journal()), encoding="utf-8")
        target.chmod(0o600)
        (self.root / f"{OPERATION_ID}.json").symlink_to(target)
        with self.assertRaises(journal.JournalStoreError):
            self.store.read(OPERATION_ID)


if __name__ == "__main__":
    unittest.main()
