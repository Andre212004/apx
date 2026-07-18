from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import apx_hyprland_h0_stage as stage


class H0StageTests(unittest.TestCase):
    def test_stage_is_fixed_to_three_assets_and_private_destination(self) -> None:
        self.assertEqual(set(stage.SOURCES), {"hyprland.conf", "session", "watchdog"})
        self.assertEqual(str(stage.DESTINATION), "/var/lib/apx/h0/h0-3ef21d19a2518d4fcea9d51513cc1eee-v2")
        self.assertEqual(tuple(mode for _, _, mode in stage.ASSETS), (0o400, 0o500, 0o500))

    def test_stage_preserves_partial_and_has_no_graphical_or_lifecycle_effect(self) -> None:
        source = Path(stage.__file__).read_text()
        self.assertIn("Preserve any partial exact destination", source)
        for forbidden in ("systemctl", "machinectl", "systemd-run", "Hyprland", "/dev/", "chvt", "rmtree", "unlink("):
            self.assertNotIn(forbidden, source)
        self.assertIn('"graphical_activation": False', source)


if __name__ == "__main__":
    unittest.main()
