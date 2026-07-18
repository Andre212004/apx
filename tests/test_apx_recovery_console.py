from dataclasses import asdict, replace
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_recovery_console as recovery


def evidence() -> recovery.RecoveryConsoleEvidence:
    return recovery.RecoveryConsoleEvidence(
        1,
        recovery.PROFILE,
        "recovery-" + "1" * 32,
        "2" * 64,
        "3" * 64,
        "4" * 64,
        "5" * 64,
        "6" * 64,
        "12345678-1234-4123-8123-123456789abc",
        "22345678-1234-4123-8123-123456789abc",
        "2026-07-18T14:00:00+00:00",
        "owner-physical-plus-root-host-reconciliation",
        *([True] * 15),
    )


class RecoveryConsoleTests(unittest.TestCase):
    def test_complete_physical_and_reconciled_evidence_verifies(self) -> None:
        result = recovery.assess_recovery_console(evidence())
        self.assertEqual(result.classification, "verified")
        self.assertTrue(result.update_gate_satisfied)
        self.assertEqual(result.blockers, ())

    def test_every_physical_reconciliation_and_no_effect_gate_blocks(self) -> None:
        fields = (
            "physical_presence_confirmed", "built_in_keyboard_confirmed",
            "encrypted_root_unlock_confirmed", "root_console_confirmed",
            "apx_status_reconciled_after_boot", "hub_generation_unchanged",
            "development_generation_unchanged", "disposable_hold_unchanged",
            "no_uncertain_apx_operation", "no_disk_layout_change",
            "no_encryption_change", "no_bootloader_change", "no_package_change",
            "no_apx_lifecycle_effect", "secrets_absent_from_receipt",
        )
        for field in fields:
            with self.subTest(field=field):
                result = recovery.assess_recovery_console(replace(evidence(), **{field: False}))
                self.assertEqual(result.classification, "blocked")
                self.assertFalse(result.update_gate_satisfied)

    def test_same_boot_nonphysical_observer_and_naive_time_fail_closed(self) -> None:
        cases = (
            replace(evidence(), recovery_boot_id=evidence().before_boot_id),
            replace(evidence(), observer_kind="bootctl-metadata"),
            replace(evidence(), observed_at="2026-07-18T14:00:00"),
        )
        for changed in cases:
            with self.subTest(changed=changed):
                with self.assertRaises(recovery.RecoveryConsoleError):
                    recovery.assess_recovery_console(changed)

    def test_json_is_closed_duplicate_safe_and_type_strict(self) -> None:
        payload = asdict(evidence())
        self.assertEqual(recovery.parse_recovery_evidence_json(json.dumps(payload)), evidence())
        payload["command"] = "reboot"
        with self.assertRaises(recovery.RecoveryConsoleError):
            recovery.parse_recovery_evidence_json(json.dumps(payload))
        canonical = json.dumps(asdict(evidence()), separators=(",", ":"))
        duplicate = canonical[:-1] + ',"schema_version":1}'
        with self.assertRaises(recovery.RecoveryConsoleError):
            recovery.parse_recovery_evidence_json(duplicate)
        with self.assertRaises(recovery.RecoveryConsoleError):
            recovery.assess_recovery_console(replace(evidence(), physical_presence_confirmed=1))

    def test_security_relevant_change_changes_evidence_digest(self) -> None:
        original = recovery.assess_recovery_console(evidence())
        changed = recovery.assess_recovery_console(
            replace(evidence(), machine_identity_digest="a" * 64)
        )
        self.assertNotEqual(original.evidence_digest, changed.evidence_digest)


if __name__ == "__main__":
    unittest.main()
