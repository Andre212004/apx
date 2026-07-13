from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_graphical_resolution as resolution


class GraphicalResolutionTests(unittest.TestCase):
    def test_seeds_define_product_role_without_waybar_or_nvidia(self):
        self.assertIn("hyprland", resolution.GRAPHICAL_SEEDS)
        self.assertIn("vulkan-radeon", resolution.GRAPHICAL_SEEDS)
        self.assertIn("xdg-desktop-portal-hyprland", resolution.GRAPHICAL_SEEDS)
        self.assertNotIn("waybar", resolution.GRAPHICAL_SEEDS)
        self.assertNotIn("nvidia-utils", resolution.GRAPHICAL_SEEDS)

    def test_command_is_offline_print_only_and_uses_staged_paths(self):
        command = resolution.fixed_command(Path("/tmp/apx-test"), Path("/tmp/apx-test/config"))
        self.assertIn("-Sp", command)
        self.assertIn("--print-format", command)
        self.assertNotIn("-S", command)
        self.assertNotIn("-U", command)

    def test_resolution_has_fixed_bounds_and_new_root(self):
        self.assertTrue(str(resolution.ROOT).startswith("/tmp/"))
        self.assertEqual(resolution.MAX_PACKAGES, 512)
        self.assertEqual(resolution.MAX_BYTES, 4 * 1024**3)


if __name__ == "__main__":
    unittest.main()
