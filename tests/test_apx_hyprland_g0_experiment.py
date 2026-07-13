from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import apx_hyprland_g0_experiment as g0


class HyprlandG0Tests(unittest.TestCase):
    def test_exact_device_and_limits(self):
        self.assertEqual(str(g0.AMD_PCI), "/sys/bus/pci/devices/0000:05:00.0")
        self.assertEqual(g0.EXPECTED_VENDOR, "0x1002")
        self.assertEqual(g0.TIMEOUT_SECONDS, 120)
        self.assertEqual(g0.MAX_BYTES, 3 * 1024**3)
        self.assertEqual(g0.BUILD_REPORT_DIGEST, "79aec029862f03c169afde83c97a1eb3fc67918b5826823f6c5b3e1f64831f56")

    def test_command_denies_network_and_opens_only_resolved_device(self):
        device = Path("/dev/dri/renderD129")
        command = g0.fixed_nspawn_command(device)
        self.assertIn("--private-network", command)
        self.assertIn("--property=DevicePolicy=closed", command)
        self.assertIn("--property=DeviceAllow=/dev/dri/renderD129 rw", command)
        self.assertNotIn("--bind=/dev/dri/renderD129", command)
        joined = " ".join(command)
        for forbidden in ("card2", "renderD128", "/dev/input", "pipewire", "--network-veth"):
            self.assertNotIn(forbidden, joined.lower())

    def test_headless_environment_and_cleanup_are_explicit(self):
        source = Path(g0.__file__).read_text(encoding="utf-8")
        self.assertIn('"AQ_NO_KMS_REQUIREMENT=1"', source)
        self.assertIn('"HEADLESS-0"', source)
        self.assertIn("shutil.rmtree(RUNTIME_PARENT)", source)
        self.assertIn("source_digest == after_digest", source)
        self.assertIn('"--reuid=1000"', source)
        self.assertIn('"/tmp/apx-hyprland-g0-evidence-v13"', source)
        self.assertIn("OUTPUT_LIMIT", source)
        self.assertIn('"AQ_TRACE=1"', source)
        self.assertIn('"HYPRLAND_TRACE=1"', source)
        self.assertNotIn('"LIBSEAT_BACKEND=noop"', source)
        self.assertIn("hyprlandCrashReport", source)
        self.assertIn('"/usr/bin/seatd", "-u", "apx-g0"', source)
        self.assertNotIn('"-s", "/run/seatd.sock"', source)
        self.assertIn("_executable_descendant", source)
        self.assertIn("atexit.register(_emergency_cleanup", source)
        self.assertIn('"SEATD_VTBOUND=0"', source)
        self.assertIn('Path("/dev/dri/renderD129")', source)
        self.assertIn("os.mknod(internal_device", source)
        self.assertIn("os.chmod(internal_device, 0o666)", source)
        self.assertIn("APX INTERNAL DEVICE PROBE", source)
        self.assertIn('"progress-v13.log"', source)
        self.assertIn('_progress("evidence-created")', source)
        self.assertIn("os.chown(EVIDENCE_ROOT, 0, DEVELOPMENT_GID)", source)
        self.assertIn("os.O_APPEND | os.O_NOFOLLOW", source)
        self.assertIn("stat.S_IMODE(info.st_mode) != 0o640", source)
        self.assertIn("render_fd = render_fd or any", source)
        self.assertNotIn('RUNTIME_ROOT / "root/.config/hypr/g0.conf"', source)

    def test_unprivileged_run_refuses_before_effect(self):
        if __import__("os").geteuid() == 0: self.skipTest("runner is root")
        with self.assertRaises(g0.HyprlandG0Error): g0.execute_g0()


if __name__ == "__main__": unittest.main()
