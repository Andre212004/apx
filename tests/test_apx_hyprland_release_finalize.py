from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_hyprland_release_finalize as finalize


class HyprlandReleaseFinalizeTests(unittest.TestCase):
    def test_install_date_normalization_is_exact(self) -> None:
        source = "%NAME%\nfoo\n\n%INSTALLDATE%\n123456\n\n%REASON%\n0\n"
        normalized, count = finalize.normalize_local_database_desc(source)
        self.assertEqual(count, 1)
        self.assertIn("%INSTALLDATE%\n0\n\n", normalized)
        self.assertNotIn("123456", normalized)

    def test_missing_duplicate_and_malformed_install_dates_refuse(self) -> None:
        cases = (
            "%NAME%\nfoo\n",
            "%INSTALLDATE%\n1\n\n%INSTALLDATE%\n2\n\n",
            "%INSTALLDATE%\nnot-a-number\n\n",
            "%INSTALLDATE%\n1\nnext\n",
        )
        for source in cases:
            with self.subTest(source=source):
                with self.assertRaises(finalize.HyprlandReleaseFinalizeError):
                    finalize.normalize_local_database_desc(source)

    def test_finalizer_is_fixed_to_temporary_graphical_root(self) -> None:
        self.assertEqual(finalize.ROOT, Path("/tmp/apx-hyprland-build-v1"))
        self.assertEqual(finalize.ROOTFS, finalize.ROOT / "rootfs")
        self.assertEqual(finalize.GPGDIR, finalize.ROOTFS / "etc/pacman.d/gnupg")
        self.assertEqual(finalize.EXPECTED_TOTAL_PACKAGES, 332)

    def test_source_has_no_host_apx_service_or_device_effect(self) -> None:
        source = Path(finalize.__file__).read_text(encoding="utf-8")
        for forbidden in (
            "/var/lib/apx", "/dev/dri", "/dev/input", "systemctl", "machinectl",
            "pacman -", "subvolume", "mount(", "reboot",
        ):
            self.assertNotIn(forbidden, source)
        self.assertIn("shutil.rmtree(GPGDIR)", source)
        self.assertIn('GPGDIR.mkdir(mode=0o700)', source)

    def test_unprivileged_finalization_refuses(self) -> None:
        if __import__("os").geteuid() == 0:
            self.skipTest("test runner is root")
        with self.assertRaises(finalize.HyprlandReleaseFinalizeError):
            finalize.finalize_hyprland_release()


if __name__ == "__main__":
    unittest.main()
