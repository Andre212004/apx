from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_graphical_acquisition as acquisition
import apx_graphical_resolution as resolution


class GraphicalAcquisitionTests(unittest.TestCase):
    def test_real_manifest_round_trips_and_matches_authorization(self):
        manifest = resolution.parse_graphical_manifest(acquisition.MANIFEST_PATH.read_text())
        self.assertEqual(manifest.manifest_digest, acquisition.AUTHORIZED_MANIFEST)
        self.assertEqual(len(manifest.role_packages), 194)

    def test_requests_are_exact_package_signature_pairs(self):
        requests = acquisition.fixed_requests()
        self.assertEqual(len(requests), 388)
        for package, signature in zip(requests[::2], requests[1::2]):
            self.assertEqual(signature.uri, package.uri + ".sig")
            self.assertEqual(signature.filename, package.filename + ".sig")
            self.assertIsNotNone(package.expected_sha256)

    def test_existing_destination_refuses_before_network(self):
        with tempfile.TemporaryDirectory() as directory:
            original = acquisition.ROOT
            acquisition.ROOT = Path(directory)
            try:
                with self.assertRaises(RuntimeError):
                    acquisition.acquire_graphical_packages(
                        opener=lambda uri, timeout: self.fail("network must not run")
                    )
            finally:
                acquisition.ROOT = original


if __name__ == "__main__":
    unittest.main()
