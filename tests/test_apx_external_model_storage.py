from dataclasses import asdict, replace
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_external_model_storage as storage


def evidence() -> storage.AttachmentEvidence:
    gib = 1024**3
    return storage.AttachmentEvidence(
        1,
        storage.PROFILE,
        "attachment-" + "1" * 32,
        "development",
        "12345678-1234-4123-8123-123456789abc",
        True,
        "2" * 64,
        "3" * 64,
        512 * gib,
        True,
        True,
        "11111111-2222-4333-8444-555555555555",
        True,
        True,
        "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee",
        "btrfs",
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        200 * gib,
        450 * gib,
        400 * gib,
        40 * gib,
        "4" * 64,
        True,
        True,
        "5" * 64,
    )


class ExternalModelStorageTests(unittest.TestCase):
    def test_complete_evidence_reaches_only_separate_design_review(self) -> None:
        result = storage.assess_attachment(evidence())
        self.assertEqual(result.classification, "ready-for-separate-design-review")
        self.assertEqual(result.blockers, ())
        self.assertTrue(result.separate_destructive_dossier_required)
        self.assertEqual(len(result.no_effect_plan_digest), 64)

    def test_every_boolean_safety_gate_blocks_independently(self) -> None:
        fields = (
            "development_stopped", "device_is_not_internal_apx_disk",
            "device_is_not_backup_disk", "luks2_verified", "recovery_unlock_tested",
            "filesystem_healthy", "attachment_detached", "host_private_mount_absent",
            "hub_visibility_absent", "other_environment_visibility_absent",
            "service_identity_verified", "ownership_mapping_verified",
            "partial_download_absent", "disconnect_fixture_passed",
        )
        for field in fields:
            with self.subTest(field=field):
                result = storage.assess_attachment(replace(evidence(), **{field: False}))
                self.assertEqual(result.classification, "blocked")

    def test_capacity_reserves_block_independently(self) -> None:
        gib = 1024**3
        cases = (
            replace(evidence(), device_size_bytes=63 * gib, store_free_bytes=63 * gib, store_limit_bytes=60 * gib),
            replace(evidence(), host_free_bytes=31 * gib),
            replace(evidence(), store_free_bytes=55 * gib, expected_model_bytes=40 * gib),
        )
        for value in cases:
            with self.subTest(value=value):
                self.assertEqual(storage.assess_attachment(value).classification, "blocked")

    def test_identity_profile_type_and_capacity_malformed_values_are_rejected(self) -> None:
        cases = (
            ("schema_version", True),
            ("profile", "latest"),
            ("attachment_id", "../disk"),
            ("development_name", "hub"),
            ("development_generation", "current"),
            ("device_identity_digest", "short"),
            ("luks_uuid", "not-a-uuid"),
            ("filesystem_type", "ext4"),
            ("device_size_bytes", True),
            ("development_stopped", 1),
            ("store_limit_bytes", evidence().device_size_bytes + 1),
            ("expected_model_bytes", evidence().store_limit_bytes + 1),
        )
        for field, value in cases:
            with self.subTest(field=field):
                with self.assertRaises(storage.ExternalModelStorageError):
                    storage.assess_attachment(replace(evidence(), **{field: value}))

    def test_json_is_closed_duplicate_safe_and_round_trips(self) -> None:
        payload = asdict(evidence())
        self.assertEqual(storage.parse_attachment_evidence_json(json.dumps(payload)), evidence())
        payload["mount_command"] = "mount /dev/x"
        with self.assertRaises(storage.ExternalModelStorageError):
            storage.parse_attachment_evidence_json(json.dumps(payload))
        canonical = json.dumps(asdict(evidence()), separators=(",", ":"))
        duplicate = canonical[:-1] + ',"schema_version":1}'
        with self.assertRaises(storage.ExternalModelStorageError):
            storage.parse_attachment_evidence_json(duplicate)

    def test_any_security_fact_changes_evidence_or_plan_identity(self) -> None:
        initial = storage.assess_attachment(evidence())
        changed_device = storage.assess_attachment(replace(evidence(), device_identity_digest="a" * 64))
        changed_model = storage.assess_attachment(replace(evidence(), model_manifest_digest="b" * 64))
        self.assertNotEqual(initial.evidence_digest, changed_device.evidence_digest)
        self.assertNotEqual(initial.no_effect_plan_digest, changed_device.no_effect_plan_digest)
        self.assertNotEqual(initial.no_effect_plan_digest, changed_model.no_effect_plan_digest)


if __name__ == "__main__":
    unittest.main()
