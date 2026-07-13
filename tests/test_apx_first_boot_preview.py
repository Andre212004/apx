from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_first_boot_preview as preview


class FirstBootPreviewTests(unittest.TestCase):
    def test_preview_is_deterministic_and_nonexecuting(self):
        first = preview.build_preview()
        second = preview.build_preview()
        self.assertEqual(first, second)
        self.assertEqual(len(first.preview_digest), 64)

    def test_command_has_closed_runtime_limits(self):
        command = preview.fixed_command()
        required = (
            "--private-network", "--settings=no",
            "--register=no", "--private-users=pick",
            "--private-users-ownership=chown", "--property=MemoryMax=512M",
            "--property=TasksMax=256", "--property=CPUQuota=50%",
            "--property=DevicePolicy=closed", "120s",
        )
        for value in required:
            self.assertIn(value, command)
        self.assertNotIn("--volatile=overlay", command)

    def test_command_exposes_no_host_path_network_or_port(self):
        command = preview.fixed_command()
        joined = " ".join(command)
        for forbidden in ("--bind=", "--bind-ro=", "--network-veth", "--port=", "/home/"):
            self.assertNotIn(forbidden, joined)

    def test_runtime_copy_is_separate_and_bounded(self):
        self.assertNotEqual(preview.RUNTIME_ROOT, preview.ROOTFS)
        self.assertTrue(str(preview.RUNTIME_ROOT).startswith("/tmp/"))
        self.assertEqual(preview.RUNTIME_MAX_BYTES, 1024**3)

    def test_module_cannot_execute_nspawn(self):
        source = Path(preview.__file__).read_text(encoding="utf-8")
        self.assertNotIn("subprocess", source)
        self.assertNotIn("os.system", source)


if __name__ == "__main__":
    unittest.main()
