from dataclasses import replace
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_external_model_lifecycle as lifecycle
import apx_external_model_storage as storage
from tests.test_apx_external_model_storage import evidence


def preview() -> storage.AttachmentPreview:
    return storage.build_attach_preview(storage.assess_attachment(evidence()))


def initial() -> lifecycle.AttachmentLifecycleRecord:
    return lifecycle.create_lifecycle(preview())


def advance(
    record: lifecycle.AttachmentLifecycleRecord, count: int, *, prefix: str = "a"
) -> lifecycle.AttachmentLifecycleRecord:
    current = record
    for index in range(count):
        current = lifecycle.prepare_next_step(current)
        current = lifecycle.record_step_success(
            current, evidence_digest=f"{(int(prefix, 16) + index) % 16:x}" * 64
        )
    return current


class AttachmentLifecycleTests(unittest.TestCase):
    def test_complete_attach_activate_and_detach_are_ordered(self) -> None:
        record = advance(initial(), len(lifecycle.ATTACH_STEPS))
        self.assertEqual(record.status, "attached-stopped")
        record = lifecycle.record_activation(record, evidence_digest="b" * 64)
        self.assertEqual(record.status, "active")
        record = lifecycle.begin_detach(record, detach_approval_digest="c" * 64)
        self.assertEqual(record.status, "detach-planned")
        record = advance(record, len(lifecycle.DETACH_STEPS), prefix="1")
        self.assertEqual(record.status, "detached")
        recovery = lifecycle.assess_recovery(record)
        self.assertEqual(recovery.classification, "complete-detached")
        self.assertFalse(recovery.automatic_cleanup_allowed)

    def test_effect_must_be_prepared_and_receive_exact_evidence(self) -> None:
        record = initial()
        with self.assertRaises(lifecycle.AttachmentLifecycleError):
            lifecycle.record_step_success(record, evidence_digest="a" * 64)
        prepared = lifecycle.prepare_next_step(record)
        self.assertEqual(prepared.prepared_step, lifecycle.ATTACH_STEPS[0])
        with self.assertRaises(lifecycle.AttachmentLifecycleError):
            lifecycle.record_step_success(prepared, evidence_digest="short")
        completed = lifecycle.record_step_success(prepared, evidence_digest="a" * 64)
        self.assertEqual(completed.completed_attach_steps, lifecycle.ATTACH_STEPS[:1])

    def test_activation_and_detach_cannot_happen_early(self) -> None:
        with self.assertRaises(lifecycle.AttachmentLifecycleError):
            lifecycle.record_activation(initial(), evidence_digest="a" * 64)
        with self.assertRaises(lifecycle.AttachmentLifecycleError):
            lifecycle.begin_detach(initial(), detach_approval_digest="b" * 64)
        attached = advance(initial(), len(lifecycle.ATTACH_STEPS))
        with self.assertRaises(lifecycle.AttachmentLifecycleError):
            lifecycle.begin_detach(attached, detach_approval_digest="short")

    def test_interruption_never_allows_cleanup_or_activation(self) -> None:
        attached = advance(initial(), len(lifecycle.ATTACH_STEPS))
        active = lifecycle.record_activation(attached, evidence_digest="b" * 64)
        detaching = lifecycle.begin_detach(active, detach_approval_digest="c" * 64)
        cases = (
            (initial(), "no-effect-recorded"),
            (lifecycle.prepare_next_step(initial()), "preserve-effect-outcome-uncertain"),
            (advance(initial(), 2), "preserve-partial-attach"),
            (lifecycle.prepare_next_step(detaching), "preserve-effect-outcome-uncertain"),
            (advance(detaching, 2, prefix="1"), "preserve-partial-detach"),
            (lifecycle.mark_uncertain(active, reason="external device disconnected"), "preserve-and-inspect"),
        )
        for record, expected in cases:
            with self.subTest(expected=expected):
                result = lifecycle.assess_recovery(record)
                self.assertEqual(result.classification, expected)
                self.assertFalse(result.automatic_cleanup_allowed)
                self.assertFalse(result.development_activation_allowed)

    def test_tampering_status_steps_identity_and_digest_are_rejected(self) -> None:
        record = initial()
        variants = (
            replace(record, status="active"),
            replace(record, attachment_id="attachment-" + "f" * 32),
            replace(record, completed_attach_steps=(lifecycle.ATTACH_STEPS[1],)),
            replace(record, attach_steps=tuple(reversed(lifecycle.ATTACH_STEPS))),
            replace(record, record_digest="f" * 64),
        )
        for value in variants:
            with self.subTest(value=value):
                with self.assertRaises(lifecycle.AttachmentLifecycleError):
                    lifecycle.validate_lifecycle(value)

    def test_uncertain_state_is_terminal_and_preserved(self) -> None:
        uncertain = lifecycle.mark_uncertain(
            advance(initial(), 1), reason="fixture interruption"
        )
        self.assertEqual(uncertain.status, "preserved-uncertain")
        with self.assertRaises(lifecycle.AttachmentLifecycleError):
            lifecycle.prepare_next_step(uncertain)
        with self.assertRaises(lifecycle.AttachmentLifecycleError):
            lifecycle.mark_uncertain(uncertain, reason="again")


class FixtureAttachmentStoreTests(unittest.TestCase):
    def test_compare_and_swap_rejects_replay_stale_and_jump(self) -> None:
        first = initial()
        store = lifecycle.FixtureAttachmentStore(preview_digest=first.preview_digest)
        store.publish_new(first)
        with self.assertRaises(lifecycle.AttachmentLifecycleError):
            store.publish_new(first)
        second = lifecycle.prepare_next_step(first)
        store.compare_and_swap(second, expected_digest=first.record_digest)
        with self.assertRaisesRegex(lifecycle.AttachmentLifecycleError, "stale"):
            store.compare_and_swap(second, expected_digest=first.record_digest)
        jumped = lifecycle.record_step_success(second, evidence_digest="a" * 64)
        jumped = lifecycle.prepare_next_step(jumped)
        with self.assertRaises(lifecycle.AttachmentLifecycleError):
            store.compare_and_swap(jumped, expected_digest=second.record_digest)
        self.assertEqual(store.read(), second)

    def test_store_accepts_only_bound_preview_and_initial_record(self) -> None:
        first = initial()
        wrong = lifecycle.FixtureAttachmentStore(preview_digest="f" * 64)
        with self.assertRaises(lifecycle.AttachmentLifecycleError):
            wrong.publish_new(first)
        proper = lifecycle.FixtureAttachmentStore(preview_digest=first.preview_digest)
        with self.assertRaises(lifecycle.AttachmentLifecycleError):
            proper.publish_new(lifecycle.prepare_next_step(first))


if __name__ == "__main__":
    unittest.main()
