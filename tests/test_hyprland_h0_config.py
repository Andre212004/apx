from pathlib import Path
import unittest


CONFIG = Path(__file__).parents[1] / "config" / "hyprland-h0.conf"


class HyprlandH0ConfigTests(unittest.TestCase):
    def test_config_is_fixed_to_internal_panel_and_portuguese_keyboard(self) -> None:
        source = CONFIG.read_text()
        self.assertIn("monitor = eDP-2, preferred, auto, 1", source)
        self.assertIn("kb_layout = pt", source)
        self.assertIn("bind = SUPER SHIFT, E, exit", source)

    def test_config_has_no_program_network_audio_or_host_integration(self) -> None:
        source = CONFIG.read_text()
        for forbidden in (
            "workspace", "socket", "portal", "pipewire", "audio",
            "network", "/home", "/run/user", "waybar", "fuzzel",
        ):
            self.assertNotIn(forbidden, source.lower())
        self.assertLess(len(source.encode()), 4096)

    def test_only_fixed_local_visual_marker_is_started(self) -> None:
        source = CONFIG.read_text()
        lines = [line.strip() for line in source.splitlines() if line.strip().startswith("exec-once")]
        self.assertEqual(len(lines), 1)
        self.assertIn("/usr/bin/foot --title=APX-H0", lines[0])
        self.assertIn("APX H0 - HYPRLAND ENVIRONMENT", lines[0])
        self.assertIn("sleep 40", lines[0])

    def test_visual_effects_are_minimized_for_first_kms_gate(self) -> None:
        source = CONFIG.read_text()
        self.assertGreaterEqual(source.count("enabled = false"), 3)
        self.assertIn("rounding = 0", source)
        self.assertIn("gaps_out = 0", source)


if __name__ == "__main__":
    unittest.main()
