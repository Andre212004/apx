from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_hyprland_g1_preview as preview


class HyprlandG1PreviewTests(unittest.TestCase):
    def test_fixed_host_and_internal_wayland_identity(self):
        self.assertEqual(preview.HOST_WAYLAND, Path("/run/user/1002/wayland-0"))
        self.assertEqual(preview.INTERNAL_WAYLAND, Path("/run/apx-host-wayland/wayland-0"))
        self.assertEqual(preview.MACHINE, "apx-hyprland-g1-v5")
        self.assertEqual(preview.TIMEOUT_SECONDS, 120)
        self.assertEqual(preview.MAX_BYTES, 3 * 1024**3)

    def test_command_has_no_direct_hardware_or_network(self):
        command = preview.fixed_nspawn_command()
        joined = " ".join(command).lower()
        self.assertIn("--private-network", command)
        self.assertIn("--property=devicepolicy=closed", joined)
        self.assertIn("--bind-ro=/run/user/1002/wayland-0:/run/apx-host-wayland/wayland-0", command)
        self.assertIn("--property=DeviceAllow=/dev/dri/renderD129 rw", command)
        for forbidden in ("/dev/dri/card", "/dev/input", "pipewire", "dbus", "--network-veth"):
            self.assertNotIn(forbidden, joined)

    def test_preview_is_nonexecuting_and_source_bound(self):
        source = Path(preview.__file__).read_text(encoding="utf-8")
        self.assertNotIn("subprocess", source)
        self.assertIn("BUILD_REPORT_DIGEST", source)
        self.assertIn('"direct_drm_devices": (str(HOST_RENDER),)', source)
        self.assertIn('"temporary_socket_acl": True', source)


if __name__ == "__main__":
    unittest.main()
