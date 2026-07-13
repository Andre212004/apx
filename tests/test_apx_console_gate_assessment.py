from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_console_gate_assessment as assessment


class ConsoleGateAssessmentTests(unittest.TestCase):
    def test_assessment_is_bound_to_real_v9_report(self):
        self.assertEqual(len(assessment.AUTHORIZED_REPORT), 64)
        self.assertEqual(assessment.REPORT.name, "first-boot-report-v9.json")

    def test_each_required_proof_is_explicit(self):
        fields = set(assessment.ConsoleGateAssessment.__dataclass_fields__)
        for field in (
            "boot_proven", "isolation_proven", "package_boundary_proven",
            "session_readiness_proven", "clean_lifecycle_proven",
            "source_preservation_proven",
        ):
            self.assertIn(field, fields)

    def test_assessor_contains_no_runtime_or_mutation_command(self):
        source = Path(assessment.__file__).read_text(encoding="utf-8").lower()
        for forbidden in ("subprocess", "systemd-nspawn", "nsenter", "systemctl", "shutil", "unlink", "rmtree"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
