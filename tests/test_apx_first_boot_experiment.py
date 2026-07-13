from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_first_boot_experiment as experiment


class FirstBootExperimentTests(unittest.TestCase):
    def test_executor_is_bound_to_authorized_preview(self):
        self.assertNotEqual(experiment.AUTHORIZED_PREVIEW, experiment.build_preview().preview_digest)
        self.assertEqual(experiment.FINAL_REPORT_DIGEST, "741fe1c332c334f9f0667b295ae98e7de686c752c3f415e169e0e48912535b68")

    def test_corrected_preview_cannot_run_before_new_authorization(self):
        with self.assertRaises(experiment.FirstBootExperimentError):
            experiment.execute_first_boot()

    def test_output_and_outer_timeout_are_bounded(self):
        source = Path(experiment.__file__).read_text(encoding="utf-8")
        self.assertEqual(experiment.OUTPUT_LIMIT, 4 * 1024**2)
        self.assertIn("timeout=150", source)
        self.assertIn("time.monotonic() + 15", source)

    def test_unprivileged_execution_refuses_before_boot(self):
        if __import__("os").geteuid() == 0:
            self.skipTest("test runner is root")
        with self.assertRaises(experiment.FirstBootExperimentError):
            experiment.execute_first_boot()

    def test_no_install_download_or_persistent_management_commands(self):
        source = Path(experiment.__file__).read_text(encoding="utf-8").lower()
        for forbidden in ("pacman", "curl", "wget", "systemctl enable", "machinectl", "btrfs"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
