from dataclasses import replace
from dataclasses import asdict
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_hyprland_release_promotion as promotion


def evidence() -> promotion.HyprlandReleasePromotionEvidence:
    return promotion.HyprlandReleasePromotionEvidence(
        1, promotion.PROFILE, "1" * 64, "2" * 64, "3" * 64, "4" * 64,
        promotion.SOURCE_TREE_DIGEST, promotion.FINAL_REPORT_DIGEST,
        promotion.PACKAGE_COUNT, True, True, True, True, True, True, True,
        True, True, True,
        "12345678-1234-4123-8123-123456789abc",
        "22345678-1234-4123-8123-123456789abc",
        True, 100 * 1024**3,
    )


class HyprlandReleasePromotionTests(unittest.TestCase):
    def test_complete_evidence_reaches_only_separate_promotion_approval(self) -> None:
        result = promotion.build_promotion_preview(evidence())
        self.assertEqual(result.classification, "ready-for-separate-promotion-approval")
        self.assertEqual(result.blockers, ())
        self.assertEqual(result.release_id, "hyprland-h0-v1")
        self.assertEqual(result.target_root, "/var/lib/apx/releases/hyprland-h0-v1/root")
        self.assertTrue(result.environment_creation_not_authorized)
        self.assertTrue(result.graphical_activation_not_authorized)
        self.assertTrue(result.automatic_cleanup_not_authorized)

    def test_every_safety_gate_blocks_independently(self) -> None:
        fields = (
            "source_reverified", "source_identity_neutral", "private_material_absent",
            "runtime_residue_absent", "source_special_files_absent",
            "source_development_ownership_absent", "destination_absent",
            "destination_parent_real_btrfs", "btrfs_quota_healthy",
            "no_uncertain_apx_operation", "disposable_hold_unchanged",
        )
        for field in fields:
            with self.subTest(field=field):
                result = promotion.build_promotion_preview(replace(evidence(), **{field: False}))
                self.assertEqual(result.classification, "blocked")
        small = promotion.build_promotion_preview(replace(evidence(), host_free_bytes=promotion.MINIMUM_FREE_BYTES - 1))
        self.assertIn("host-free-space-below-4-gib", small.blockers)

    def test_source_digests_package_count_generations_and_types_are_closed(self) -> None:
        cases = (
            ("source_tree_digest", "0" * 64),
            ("final_report_digest", "0" * 64),
            ("package_count", 331),
            ("hub_generation", "current"),
            ("source_reverified", 1),
            ("host_free_bytes", True),
        )
        for field, value in cases:
            with self.subTest(field=field):
                with self.assertRaises(promotion.HyprlandReleasePromotionError):
                    promotion.build_promotion_preview(replace(evidence(), **{field: value}))

    def test_plan_paths_account_effects_and_scope_are_fixed(self) -> None:
        result = promotion.build_promotion_preview(evidence())
        self.assertEqual(result.source_root, "/tmp/apx-hyprland-build-v1/rootfs")
        self.assertEqual(result.target_directory, "/var/lib/apx/releases/hyprland-h0-v1")
        self.assertEqual(result.account, ("apx", 1000, 1000, "/home/apx", "/usr/bin/bash", True))
        self.assertEqual(result.effects, promotion.PROMOTION_EFFECTS)

    def test_security_relevant_evidence_changes_plan_identity(self) -> None:
        original = promotion.build_promotion_preview(evidence())
        changed_machine = promotion.build_promotion_preview(
            replace(evidence(), machine_identity_digest="a" * 64)
        )
        changed_generation = promotion.build_promotion_preview(
            replace(evidence(), hub_generation="32345678-1234-4123-8123-123456789abc")
        )
        self.assertNotEqual(original.plan_digest, changed_machine.plan_digest)
        self.assertNotEqual(original.plan_digest, changed_generation.plan_digest)

    def test_module_contains_no_effect_adapter_or_caller_paths(self) -> None:
        source = Path(promotion.__file__).read_text(encoding="utf-8")
        for forbidden in ("subprocess", "os.open", "shutil", "systemctl", "btrfs ", "/dev/dri", "/dev/input"):
            self.assertNotIn(forbidden, source)

    def test_json_is_closed_duplicate_safe_and_type_strict(self) -> None:
        payload = asdict(evidence())
        self.assertEqual(promotion.parse_promotion_evidence_json(json.dumps(payload)), evidence())
        payload["command"] = "copy"
        with self.assertRaises(promotion.HyprlandReleasePromotionError):
            promotion.parse_promotion_evidence_json(json.dumps(payload))
        canonical = json.dumps(asdict(evidence()), separators=(",", ":"))
        duplicate = canonical[:-1] + ',"schema_version":1}'
        with self.assertRaises(promotion.HyprlandReleasePromotionError):
            promotion.parse_promotion_evidence_json(duplicate)
        with self.assertRaises(promotion.HyprlandReleasePromotionError):
            promotion.build_promotion_preview(replace(evidence(), destination_absent=1))


if __name__ == "__main__":
    unittest.main()
