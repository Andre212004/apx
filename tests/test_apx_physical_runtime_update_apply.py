from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import apx_physical_runtime_update_apply as subject


class PhysicalRuntimeUpdateApplyTests(unittest.TestCase):
    def test_adapter_is_fixed_to_one_artifact_target_and_rollback(self) -> None:
        self.assertEqual(subject.UPDATE_ID, "update-a1b55982d14fb0bdf7afa8f1dd7991ca")
        self.assertEqual(subject.TARGET, Path("/usr/lib/apx/apx-lab-runtime.py"))
        self.assertEqual(subject.ALIAS, Path("/usr/bin/apx"))
        self.assertEqual(subject.CANDIDATE.components, ("host-runtime",))
        self.assertEqual(subject.CANDIDATE.artifact_sha256, subject.ARTIFACT_SHA256)

    def test_adapter_has_no_service_start_stop_delete_or_package_effect(self) -> None:
        source = Path(subject.__file__).read_text()
        for forbidden in ("systemctl stop", "systemctl start", "machinectl poweroff", "rmtree", "pacman", "reboot"):
            self.assertNotIn(forbidden, source)
        self.assertIn('value.get("state") != "stopped"', source)
        self.assertIn('"rollback_retained": True', source)

    def test_runtime_identities_are_distinct_and_canonical(self) -> None:
        self.assertNotEqual(subject.BEFORE_SHA256, subject.AFTER_SHA256)
        for value in (subject.BEFORE_SHA256, subject.AFTER_SHA256, subject.ARTIFACT_SHA256, subject.MANIFEST_SHA256):
            self.assertEqual(len(value), 64)
            int(value, 16)


if __name__ == "__main__":
    unittest.main()
