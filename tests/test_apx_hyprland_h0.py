from dataclasses import asdict, replace
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_hyprland_h0 as h0


def evidence() -> h0.H0Evidence:
    return h0.H0Evidence(
        1,
        h0.PROFILE,
        "h0-" + "1" * 32,
        "2" * 64,
        True,
        "3" * 64,
        "4" * 64,
        True,
        True,
        True,
        True,
        True,
        "5" * 64,
        True,
        True,
        True,
        True,
        True,
        h0.AMD_PCI,
        "amdgpu",
        "6" * 64,
        "7" * 64,
        "8" * 64,
        "9" * 64,
        h0.NVIDIA_PCI,
        True,
        h0.INPUT_KINDS,
        ("a" * 64, "b" * 64),
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        "c" * 64,
        "d" * 64,
        "e" * 64,
        "f" * 64,
        "12345678-1234-4123-8123-123456789abc",
        180,
        True,
        "0" * 64,
    )


class HyprlandH0Tests(unittest.TestCase):
    def test_complete_evidence_reaches_only_separate_physical_approval(self) -> None:
        preview = h0.build_h0_preview(evidence())
        self.assertEqual(preview.classification, "ready-for-separate-physical-approval")
        self.assertEqual(preview.blockers, ())
        self.assertEqual(preview.amd_pci, h0.AMD_PCI)
        self.assertEqual(preview.input_kinds, h0.INPUT_KINDS)
        self.assertTrue(preview.separate_physical_approval_required)
        self.assertTrue(preview.cleanup_not_authorized)
        self.assertEqual(preview.effects, h0.H0_EFFECTS)

    def test_every_safety_gate_blocks_independently(self) -> None:
        fields = (
            "physical_audit_reconciled", "no_display_manager_installed",
            "no_display_manager_enabled", "no_display_manager_active",
            "no_graphical_session_owner", "no_stale_graphical_lease",
            "recovery_vt_verified", "recovery_vt_independent", "headless_hub_healthy",
            "development_healthy", "no_uncertain_apx_operation", "nvidia_excluded",
            "input_mediation_verified", "broad_input_access_absent", "audio_access_absent",
            "camera_access_absent", "microphone_access_absent",
            "host_filesystem_access_absent", "executor_access_absent", "watchdog_verified",
        )
        for field in fields:
            with self.subTest(field=field):
                preview = h0.build_h0_preview(replace(evidence(), **{field: False}))
                self.assertEqual(preview.classification, "blocked")

    def test_nvidia_broad_input_audio_camera_microphone_and_executor_are_denied(self) -> None:
        preview = h0.build_h0_preview(
            replace(
                evidence(),
                nvidia_excluded=False,
                broad_input_access_absent=False,
                audio_access_absent=False,
                camera_access_absent=False,
                microphone_access_absent=False,
                executor_access_absent=False,
            )
        )
        self.assertEqual(
            set(preview.blockers),
            {
                "nvidia-not-excluded", "broad-input-access-present",
                "audio-access-present", "camera-access-present",
                "microphone-access-present", "executor-access-present",
            },
        )

    def test_target_gpu_input_identity_and_timeout_are_closed(self) -> None:
        cases = (
            ("amd_pci", h0.NVIDIA_PCI),
            ("amd_driver", "nouveau"),
            ("nvidia_pci", "0000:02:00.0"),
            ("input_kinds", ("built-in-keyboard",)),
            ("input_identity_digests", ("a" * 64, "a" * 64)),
            ("timeout_seconds", 29),
            ("timeout_seconds", h0.MAX_RUNTIME_SECONDS + 1),
        )
        for field, value in cases:
            with self.subTest(field=field):
                with self.assertRaises(h0.H0Error):
                    h0.build_h0_preview(replace(evidence(), **{field: value}))

    def test_wrong_types_profiles_digests_and_generation_are_rejected(self) -> None:
        cases = (
            ("schema_version", True),
            ("profile", "g2"),
            ("experiment_id", "h0-current"),
            ("physical_audit_digest", "short"),
            ("physical_audit_reconciled", 1),
            ("disposable_environment_generation", "current"),
        )
        for field, value in cases:
            with self.subTest(field=field):
                with self.assertRaises(h0.H0Error):
                    h0.build_h0_preview(replace(evidence(), **{field: value}))

    def test_json_is_closed_duplicate_safe_and_round_trips(self) -> None:
        payload = asdict(evidence())
        self.assertEqual(h0.parse_h0_evidence_json(json.dumps(payload)), evidence())
        payload["device_path"] = "/dev/dri/card0"
        with self.assertRaises(h0.H0Error):
            h0.parse_h0_evidence_json(json.dumps(payload))
        canonical = json.dumps(asdict(evidence()), separators=(",", ":"))
        duplicate = canonical[:-1] + ',"schema_version":1}'
        with self.assertRaises(h0.H0Error):
            h0.parse_h0_evidence_json(duplicate)

    def test_security_relevant_change_changes_plan_identity(self) -> None:
        original = h0.build_h0_preview(evidence())
        changed_input = h0.build_h0_preview(
            replace(evidence(), input_identity_digests=("a" * 64, "c" * 64))
        )
        changed_config = h0.build_h0_preview(
            replace(evidence(), hyprland_config_digest="1" * 64)
        )
        self.assertNotEqual(original.plan_digest, changed_input.plan_digest)
        self.assertNotEqual(original.plan_digest, changed_config.plan_digest)


if __name__ == "__main__":
    unittest.main()
