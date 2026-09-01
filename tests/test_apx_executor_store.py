from dataclasses import replace
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import apx_executor_store as store
from apx_executor_contract import ApprovalEvidence, build_operation_plan


GENERATION = "69b56acc-fd4d-4499-8009-e1d0108466f4"


def approval(plan):
    return ApprovalEvidence(
        "approval-" + "2" * 32, "op-" + "1" * 32, plan.operation_kind,
        plan.logical_name, plan.expected_generation, plan.plan_digest,
        plan.consequence_digest, plan.required_approval_class,
        "session-" + "3" * 32, "4" * 64, 100, 100, 200, True,
    )


class ExecutorStoreTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "executor-v1"
        self.patch = patch.object(store, "STORE_ROOT", self.root)
        self.patch.start()
        store.initialize_store()

    def tearDown(self):
        self.patch.stop(); self.temporary.cleanup()

    def test_plan_and_approval_round_trip_preserves_physical_uuid(self):
        plan = build_operation_plan("activate", "test", GENERATION)
        item = approval(plan)
        store.publish_plan(plan); store.publish_approval(item)
        self.assertEqual(store.load_plan(plan.plan_digest), plan)
        self.assertEqual(store.load_approval(item.approval_id), item)
        self.assertEqual(store.load_plan(plan.plan_digest).expected_generation, GENERATION)

    def test_records_are_immutable_and_nonce_is_single_use(self):
        plan = build_operation_plan("activate", "test", GENERATION)
        store.publish_plan(plan)
        with self.assertRaises(FileExistsError):
            store.publish_plan(plan)
        self.assertTrue(store.reserve_nonce("4" * 64, "5" * 64))
        self.assertFalse(store.reserve_nonce("4" * 64, "6" * 64))

    def test_changed_plan_unverified_approval_and_bad_identity_are_rejected(self):
        plan = build_operation_plan("activate", "test", GENERATION)
        with self.assertRaises(store.ExecutorStoreError):
            store.publish_plan(replace(plan, logical_name="other"))
        with self.assertRaises(store.ExecutorStoreError):
            store.publish_approval(replace(approval(plan), authenticity_verified=False))
        with self.assertRaises(store.ExecutorStoreError):
            store.load_plan("bad")

    def test_symlink_record_is_rejected(self):
        plan = build_operation_plan("activate", "test", GENERATION)
        target = self.root / "outside"
        target.write_text("{}\n")
        (self.root / "plans" / f"{plan.plan_digest}.json").symlink_to(target)
        with self.assertRaises(store.ExecutorStoreError):
            store.load_plan(plan.plan_digest)


if __name__ == "__main__":
    unittest.main()
