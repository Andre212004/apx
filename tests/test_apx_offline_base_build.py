from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_offline_base_build as build


class OfflineBaseBuildTests(unittest.TestCase):
    def test_command_is_fixed_offline_and_points_only_at_disposable_root(self):
        command = build.fixed_pacman_command((Path("/tmp/pkg-one"), Path("/tmp/pkg-two")))
        self.assertEqual(command[:5], ("/usr/bin/unshare", "--net", "--", "/usr/bin/pacman", "-U"))
        self.assertIn(str(build.ROOTFS), command)
        self.assertIn(str(build.PACMAN_DB), command)
        self.assertIn(str(build.GPGDIR), command)
        self.assertNotIn("-S", command)

    def test_fixed_limits_and_identity(self):
        self.assertEqual(build.ROOT, Path("/tmp/apx-first-console-build-v1"))
        self.assertEqual(build.EXPECTED_PACKAGES, 138)
        self.assertEqual(build.MAX_BYTES, 1024**3)

    def test_builder_refuses_unprivileged_execution_before_creating_root(self):
        if __import__("os").geteuid() == 0:
            self.skipTest("test runner is root")
        with self.assertRaises(build.OfflineBaseBuildError):
            build.build_offline_base()

    def test_no_host_management_or_download_commands_exist(self):
        source = Path(build.__file__).read_text(encoding="utf-8").lower()
        for forbidden in ("sudo", "systemctl", "machinectl", "curl", "wget"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
