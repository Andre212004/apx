from __future__ import annotations

from dataclasses import replace
from dataclasses import asdict
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_clean_install_dossier as dossier


def target() -> dossier.TargetEvidence:
    return dossier.TargetEvidence(
        1, "target-" + "1" * 32, "x86_64", "uefi", "2" * 64,
        512 * 1024**3, True, True, True, "3" * 64, True, "4" * 64,
        True, True, True, "pt_PT.UTF-8", "pt-latin1", "Europe/Lisbon",
        "apx-host", "amd",
    )


def supply() -> dossier.SupplyChainEvidence:
    return dossier.SupplyChainEvidence(
        1, "2026-07-13", "5" * 64, True, "6" * 40, "7" * 64,
        "8" * 40, "9" * 40, True, True, True, True,
    )


class CleanInstallDossierTests(unittest.TestCase):
    def test_complete_evidence_is_ready_only_for_separate_approval(self) -> None:
        result = dossier.build_dossier(target(), supply())
        self.assertEqual(result.classification, "ready-for-separate-approval")
        self.assertEqual(result.blockers, ())
        self.assertTrue(result.separate_strong_approval_required)
        self.assertIn("amd-ucode", result.packages)
        self.assertNotIn("git", result.packages)
        self.assertNotIn("codex", result.packages)
        self.assertEqual(len(result.plan_digest), 64)

    def test_every_boolean_gate_blocks_independently(self) -> None:
        target_fields = (
            "disk_not_running_system", "disk_unmounted",
            "unsupported_topology_absent", "backup_sample_restore_passed",
            "recovery_media_boot_passed", "network_ready", "trusted_time_ready",
        )
        supply_fields = (
            "package_signatures_verified", "apx_signature_verified",
            "apx_key_custody_ready", "executor_boundary_reviewed",
            "disposable_install_rehearsal_passed",
        )
        for field in target_fields:
            with self.subTest(field=field):
                self.assertEqual(dossier.build_dossier(replace(target(), **{field: False}), supply()).classification, "blocked")
        for field in supply_fields:
            with self.subTest(field=field):
                self.assertEqual(dossier.build_dossier(target(), replace(supply(), **{field: False})).classification, "blocked")

    def test_small_disk_and_cpu_select_exact_result(self) -> None:
        small = dossier.build_dossier(replace(target(), disk_size_bytes=dossier.MINIMUM_DISK_BYTES - 1), supply())
        self.assertIn("target-disk-smaller-than-64-gib", small.blockers)
        intel = dossier.build_dossier(replace(target(), cpu_vendor="intel"), supply())
        self.assertIn("intel-ucode", intel.packages)
        self.assertNotIn("amd-ucode", intel.packages)

    def test_malformed_types_digests_configuration_and_profile_fail(self) -> None:
        target_cases = (
            ("schema_version", True), ("target_id", "../disk"),
            ("architecture", "aarch64"), ("firmware_mode", "bios"),
            ("disk_identity_digest", "short"), ("disk_size_bytes", True),
            ("disk_unmounted", 1), ("locale", "bad"), ("keymap", "../bad"),
            ("timezone", "/etc/localtime"), ("hostname", "Bad_Host"),
            ("cpu_vendor", "unknown"),
        )
        for field, value in target_cases:
            with self.subTest(field=field):
                with self.assertRaises(dossier.CleanInstallDossierError):
                    dossier.build_dossier(replace(target(), **{field: value}), supply())
        supply_cases = (
            ("arch_snapshot_date", "latest"),
            ("package_manifest_digest", "short"),
            ("apx_source_revision", "main"),
            ("apx_signature_verified", 1),
        )
        for field, value in supply_cases:
            with self.subTest(field=field):
                with self.assertRaises(dossier.CleanInstallDossierError):
                    dossier.build_dossier(target(), replace(supply(), **{field: value}))

    def test_json_parsers_reject_unknown_missing_duplicate_and_bad_dates(self) -> None:
        target_payload = asdict(target())
        supply_payload = asdict(supply())
        self.assertEqual(dossier.parse_target_evidence_json(json.dumps(target_payload)), target())
        self.assertEqual(dossier.parse_supply_chain_evidence_json(json.dumps(supply_payload)), supply())

        target_payload["command"] = "wipe-disk"
        with self.assertRaises(dossier.CleanInstallDossierError):
            dossier.parse_target_evidence_json(json.dumps(target_payload))
        del target_payload["command"]
        del target_payload["disk_unmounted"]
        with self.assertRaises(dossier.CleanInstallDossierError):
            dossier.parse_target_evidence_json(json.dumps(target_payload))

        canonical = json.dumps(asdict(supply()), separators=(",", ":"))
        duplicate = canonical[:-1] + ',"schema_version":1}'
        with self.assertRaises(dossier.CleanInstallDossierError):
            dossier.parse_supply_chain_evidence_json(duplicate)
        for invalid_date in ("2026-19-39", "2019-01-01", "latest"):
            with self.assertRaises(dossier.CleanInstallDossierError):
                dossier.parse_supply_chain_evidence_json(
                    json.dumps(asdict(replace(supply(), arch_snapshot_date=invalid_date)))
                )

    def test_plan_changes_with_target_or_supply_identity(self) -> None:
        initial = dossier.build_dossier(target(), supply()).plan_digest
        variants = (
            dossier.build_dossier(replace(target(), disk_identity_digest="a" * 64), supply()),
            dossier.build_dossier(target(), replace(supply(), apx_package_sha256="b" * 64)),
            dossier.build_dossier(replace(target(), hostname="other-host"), supply()),
        )
        for variant in variants:
            self.assertNotEqual(initial, variant.plan_digest)


if __name__ == "__main__":
    unittest.main()
