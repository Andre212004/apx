from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_hyprland_release_promote as promote


class HyprlandReleasePromoteTests(unittest.TestCase):
    def test_effect_targets_are_exact_and_new(self) -> None:
        self.assertEqual(promote.SOURCE, Path("/tmp/apx-hyprland-build-v1/rootfs"))
        self.assertEqual(promote.DESTINATION, Path("/var/lib/apx/releases/hyprland-h0-v1"))
        self.assertEqual(promote.TARGET_ROOT, promote.DESTINATION / "root")
        self.assertEqual(promote.RELEASE_ID, "hyprland-h0-v1")

    def test_adapter_has_no_delete_service_device_or_graphical_effect(self) -> None:
        source = Path(promote.__file__).read_text(encoding="utf-8")
        for forbidden in (
            "rmtree", "unlink(", "systemctl", "machinectl", "/dev/dri",
            "/dev/input", "/usr/bin/Hyprland", "reboot", "poweroff", "pkill",
        ):
            self.assertNotIn(forbidden, source)
        self.assertIn('os.path.lexists(DESTINATION)', source)
        self.assertIn('"ro", "true"', source)

    def test_account_and_manifest_are_fixed_inside_release(self) -> None:
        source = Path(promote.__file__).read_text(encoding="utf-8")
        self.assertIn("apx:x:1000:1000:APX graphical Environment:/home/apx:/usr/bin/bash", source)
        self.assertIn('"identity": "empty-until-environment-creation"', source)
        self.assertIn('"role": "graphical-h0"', source)

    def test_preconditions_bind_current_generations_and_hold(self) -> None:
        self.assertEqual(promote.EXPECTED_HUB_GENERATION, "d68ee7a2-268a-4534-b033-8f5313943fcf")
        self.assertEqual(promote.EXPECTED_DEVELOPMENT_GENERATION, "b90155f6-ece2-44ae-91fc-42d91d6b35a5")
        self.assertEqual(promote.EXPECTED_HOLD_GENERATION, "1ec52013-e715-413a-bb48-b4691cf31ee9")

    def test_recovery_accepts_only_exact_known_partial_and_never_deletes(self) -> None:
        self.assertEqual(
            promote.EXPECTED_ACCOUNT_PARTIAL_DIGEST,
            "b1bb42da33a9df56b39a28ec84bc11a0cbf14670e2c97efbb805dc294d997664",
        )
        source = Path(promote.__file__).read_text(encoding="utf-8")
        self.assertIn("resume_exact_account_partial", source)
        self.assertIn("partial release content is not the reviewed account boundary", source)
        self.assertNotIn("rmtree", source)


if __name__ == "__main__":
    unittest.main()
