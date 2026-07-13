from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_offline_base_finalize as finalize


class OfflineBaseFinalizeTests(unittest.TestCase):
    def test_finalizer_is_bound_to_completed_build_contract(self):
        self.assertIn("report_digest", finalize.BUILD_REPORT_FIELDS)
        self.assertEqual(finalize.AUTHORIZED_MANIFEST, "574f5d31e7c4ee46b1982fe2baf285d014ba0d712e91aea6d00413ba8fe5e3f9")
        self.assertEqual(finalize.AUTHORIZED_SIGNATURE_EVIDENCE, "468116fb5277d91a099d0d4adbc5ca6579a5962965b062c0b6a1f09db9e4ea84")
        self.assertEqual(finalize.EXPECTED_PACKAGES, 138)
        self.assertEqual(finalize.MAX_BYTES, 1024**3)

    def test_report_validation_is_canonical_and_fail_closed(self):
        source = Path(finalize.__file__).read_text(encoding="utf-8")
        self.assertIn("set(build) != BUILD_REPORT_FIELDS", source)
        self.assertIn("hashlib.sha256(canonical.encode()).hexdigest() != report_digest", source)
        self.assertIn('build["machine_identity_present"] is not True', source)
        self.assertIn('build["development_uid_entries"] != 0', source)

    def test_only_exact_gpg_runtime_sockets_are_removed(self):
        source = Path(finalize.__file__).read_text(encoding="utf-8")
        self.assertIn('GPGDIR.glob("S.gpg-agent*")', source)
        self.assertIn("stat.S_ISSOCK", source)
        self.assertNotIn("rmtree", source)

    def test_unprivileged_finalization_refuses(self):
        if __import__("os").geteuid() == 0:
            self.skipTest("test runner is root")
        with self.assertRaises(finalize.OfflineBaseFinalizeError):
            finalize.finalize_offline_base()


if __name__ == "__main__":
    unittest.main()
