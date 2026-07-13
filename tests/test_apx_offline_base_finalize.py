from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_offline_base_finalize as finalize


class OfflineBaseFinalizeTests(unittest.TestCase):
    def test_finalizer_is_bound_to_completed_build(self):
        self.assertEqual(len(finalize.AUTHORIZED_BUILD_REPORT), 64)
        self.assertEqual(finalize.EXPECTED_PACKAGES, 138)
        self.assertEqual(finalize.MAX_BYTES, 1024**3)

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
