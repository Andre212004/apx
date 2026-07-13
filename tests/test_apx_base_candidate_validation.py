from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_base_candidate_validation as validation


class CandidateValidationTests(unittest.TestCase):
    def test_policy_requires_core_runtime_and_clean_machine_identity(self):
        self.assertIn("usr/lib/systemd/systemd", validation.REQUIRED)
        self.assertIn("usr/bin/pacman", validation.REQUIRED)
        self.assertIn("etc/machine-id", validation.MACHINE_LOCAL)
        self.assertIn("var/lib/systemd/random-seed", validation.MACHINE_LOCAL)

    def test_real_fixture_is_truthfully_not_admitted(self):
        if not validation.RECEIPT.exists():
            self.skipTest("external extraction fixture was not retained across reboot")
        result = validation.assess_candidate()
        self.assertEqual(result.status, "not-admitted")
        joined = " ".join(result.blockers)
        self.assertIn("ownership", joined)
        self.assertIn("installed-package database", joined)
        self.assertIn("boot", joined)
        self.assertGreater(len(result.assessment_digest), 0)

    def test_validator_has_no_boot_or_host_mutation_commands(self):
        source = Path(validation.__file__).read_text(encoding="utf-8").lower()
        for forbidden in ("systemd-nspawn", "machinectl", "sudo", "chown", "pacman -"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
