from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_hyprland_g1_experiment as g1


class HyprlandG1ExperimentTests(unittest.TestCase):
    def test_fixed_nested_boundary(self):
        command = g1.fixed_nspawn_command()
        joined = " ".join(command).lower()
        self.assertIn("--private-network", command)
        self.assertIn("--property=devicepolicy=closed", joined)
        self.assertIn("--bind-ro=/run/user/1002/wayland-0:/run/apx-host-wayland/wayland-0", command)
        self.assertIn("--property=DeviceAllow=/dev/dri/renderD129 rw", command)
        for forbidden in ("/dev/dri/card", "/dev/input", "pipewire", "dbus", "--network-veth"):
            self.assertNotIn(forbidden, joined)

    def test_runtime_is_bounded_and_cleanup_is_mandatory(self):
        source = Path(g1.__file__).read_text(encoding="utf-8")
        self.assertIn("atexit.register(_cleanup, nspawn)", source)
        self.assertIn("_tree_content_digest(SOURCE_ROOT)", source)
        self.assertIn("shutil.rmtree(RUNTIME_PARENT)", source)
        self.assertIn("os.mknod(internal_device", source)
        self.assertIn('"AQ_DRM_DEVICES=" + str(INTERNAL_RENDER)', source)
        self.assertIn('"direct_drm_nodes_visible"', source)
        self.assertIn("atexit.register(_restore_wayland_acl, acl_snapshot)", source)
        self.assertIn("restored_acl.stdout == baseline.stdout", source)
        self.assertIn('f"u:{mapped_uid}:w"', source)
        self.assertIn('path.name.startswith("wayland-")', source)
        self.assertIn("except subprocess.TimeoutExpired", source)
        self.assertIn("os.kill(hypr_pid, signal.SIGTERM)", source)
        self.assertIn("apx-hyprland-g1-controller-v5.log", source)
        self.assertEqual(g1.TIMEOUT_SECONDS, 120)
        self.assertEqual(g1.MAX_BYTES, 3 * 1024**3)

    def test_unprivileged_execution_refuses_before_effect(self):
        if __import__("os").geteuid() == 0:
            self.skipTest("runner is root")
        with self.assertRaises(g1.HyprlandG1Error):
            g1.execute_g1()


if __name__ == "__main__":
    unittest.main()
