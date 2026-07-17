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


def model_manifest() -> storage.ModelArtifactManifest:
    return storage.ModelArtifactManifest(
        1,
        "qwen2.5-coder-7b-instruct",
        "qwen2.5-coder:7b",
        "ollama-library",
        "apache-2.0",
        "ollama",
        "0.12.1",
        4_700_000_000,
        "6" * 64,
        ("7" * 64, "8" * 64),
        True,
        True,
        True,
    )


class ExternalModelStorageTests(unittest.TestCase):
    def test_attach_preview_is_exact_deterministic_and_nonexecuting(self) -> None:
        readiness = storage.assess_attachment(evidence())
        first = storage.build_attach_preview(readiness)
        second = storage.build_attach_preview(readiness)
        self.assertEqual(first, second)
        self.assertEqual(first.classification, "preview-only")
        self.assertEqual(first.host_private_mount, f"/run/apx/model-stores/{evidence().attachment_id}")
        self.assertEqual(first.development_model_path, "/var/lib/ollama")
        self.assertTrue(first.separate_implementation_and_approval_required)
        self.assertNotIn("mount ", " ".join(first.effects))

    def test_blocked_or_forged_readiness_cannot_produce_preview(self) -> None:
        blocked = storage.assess_attachment(replace(evidence(), hub_visibility_absent=False))
        with self.assertRaises(storage.ExternalModelStorageError):
            storage.build_attach_preview(blocked)
        ready = storage.assess_attachment(evidence())
        for forged in (
            replace(ready, classification="preview-only"),
            replace(ready, blockers=("ignored",)),
            replace(ready, evidence_digest="short"),
            replace(ready, separate_destructive_dossier_required=False),
        ):
            with self.subTest(forged=forged):
                with self.assertRaises(storage.ExternalModelStorageError):
                    storage.build_attach_preview(forged)

    def test_attach_preview_identity_changes_with_bound_evidence(self) -> None:
        initial = storage.build_attach_preview(storage.assess_attachment(evidence()))
        changed = storage.build_attach_preview(
            storage.assess_attachment(replace(evidence(), device_identity_digest="a" * 64))
        )
        self.assertNotEqual(initial.operation_id, changed.operation_id)
        self.assertNotEqual(initial.preview_digest, changed.preview_digest)

    def test_model_manifest_is_canonical_and_digest_bound(self) -> None:
        digest = storage.validate_model_manifest(model_manifest())
        self.assertEqual(len(digest), 64)
        changed = storage.validate_model_manifest(replace(model_manifest(), total_bytes=4_700_000_001))
        self.assertNotEqual(digest, changed)

    def test_model_manifest_json_is_closed_duplicate_safe_and_round_trips(self) -> None:
        payload = asdict(model_manifest())
        self.assertEqual(storage.parse_model_manifest_json(json.dumps(payload)), model_manifest())
        payload["command"] = "ollama pull"
        with self.assertRaises(storage.ExternalModelStorageError):
            storage.parse_model_manifest_json(json.dumps(payload))
        canonical = json.dumps(asdict(model_manifest()), separators=(",", ":"))
        duplicate = canonical[:-1] + ',"schema_version":1}'
        with self.assertRaises(storage.ExternalModelStorageError):
            storage.parse_model_manifest_json(duplicate)

    def test_model_manifest_rejects_partial_secret_mutable_and_bad_blob_state(self) -> None:
        cases = (
            ("partial_download_absent", False),
            ("credentials_absent", False),
            ("conversations_absent", False),
            ("blob_sha256", ("8" * 64, "7" * 64)),
            ("blob_sha256", ("7" * 64, "7" * 64)),
            ("blob_sha256", ()),
            ("source", "https://example.invalid/model"),
            ("tool", "curl"),
        )
        for field, value in cases:
            with self.subTest(field=field, value=value):
                with self.assertRaises(storage.ExternalModelStorageError):
                    storage.validate_model_manifest(replace(model_manifest(), **{field: value}))

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
