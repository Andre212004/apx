from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "scripts/physical-pilot/apx-graphical-environment-v1.py"


class GraphicalEnvironmentLauncherTests(unittest.TestCase):
    def test_launcher_reuses_proven_engine_without_merging_homes(self):
        source = LAUNCHER.read_text()
        compile(source, str(LAUNCHER), "exec")
        for value in (
            'record.get("role") != "graphical-base"',
            'record.get("release") != "hyprland-base-v2"',
            'engine.HOME = environment / "home"',
            'engine.CONFIG = engine.HOME / "apx/.config/hyprland/hyprland.conf"',
            "APX_HYPRLAND_CONFIG=/home/apx/.config/hypr/hyprland.lua",
            "APX_GPU_POLICY", "APX_DISPLAY_CARD", "APX_DISPLAY_RENDER",
            "APX_NVIDIA_CARD_DEVICE",
            "graphics['offload_render']",
            "apx-active-graphical-environment-v1",
            "engine.launch(args.test, args.authenticated_handoff)",
            'engine.HOME / "apx/.config/quickshell/apx/shell.qml"',
            '"desktop_shell": "quickshell", "quickshell": True',
            '"/home/apx/.local/bin/apx-shell-v1"',
            'engine.compositor_state()',
            '"dispatch", "exec"',
        ):
            self.assertIn(value, source)

    def test_launcher_does_not_claim_new_watchdog_or_recovery(self):
        source = LAUNCHER.read_text()
        self.assertIn("No new recovery/watchdog mechanism", source)
        self.assertNotIn('mode.add_argument("--watchdog"', source)


if __name__ == "__main__":
    unittest.main()
