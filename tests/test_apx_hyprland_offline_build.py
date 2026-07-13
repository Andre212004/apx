from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_hyprland_offline_build as build


class HyprlandOfflineBuildTests(unittest.TestCase):
    def test_command_is_offline_local_and_targets_only_copy(self):
        command = build.fixed_pacman_command((Path("/tmp/one.pkg.tar.zst"),))
        self.assertEqual(command[:5], ("/usr/bin/unshare", "--net", "--", "/usr/bin/pacman", "-U"))
        self.assertIn(str(build.ROOTFS), command)
        self.assertIn(str(build.PACMAN_DB), command)
        self.assertNotIn("-S", command)

    def test_fixed_scope_and_limits(self):
        self.assertEqual(build.ROOT, Path("/tmp/apx-hyprland-build-v1"))
        self.assertEqual(build.MAX_BYTES, 3 * 1024**3)
        self.assertEqual(build.EXPECTED_ROLE_PACKAGES, 194)
        self.assertEqual(build.EXPECTED_TOTAL_PACKAGES, 332)

    def test_builder_refuses_unprivileged_execution_before_creation(self):
        if __import__("os").geteuid() == 0:
            self.skipTest("test runner is root")
        with self.assertRaises(build.HyprlandOfflineBuildError):
            build.build_hyprland_role()

    def test_no_download_hardware_or_service_commands(self):
        source = Path(build.__file__).read_text(encoding="utf-8").lower()
        for forbidden in ("sudo", "curl", "wget", "systemctl", "machinectl", "/dev/dri", "pipewire"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
