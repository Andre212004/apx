from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_graphical_acquisition as acquisition
import apx_graphical_resolution as resolution
from apx_downloader import DownloadRequest


class GraphicalAcquisitionTests(unittest.TestCase):
    def test_real_manifest_round_trips_and_matches_authorization(self):
        if not acquisition.MANIFEST_PATH.exists():
            self.skipTest("external graphical manifest was not retained across reboot")
        manifest = resolution.parse_graphical_manifest(acquisition.MANIFEST_PATH.read_text())
        self.assertEqual(manifest.manifest_digest, acquisition.AUTHORIZED_MANIFEST)
        self.assertEqual(len(manifest.role_packages), 194)

    def test_requests_are_exact_package_signature_pairs(self):
        if not acquisition.MANIFEST_PATH.exists():
            self.skipTest("external graphical manifest was not retained across reboot")
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

    def test_resume_reopens_existing_package_by_exact_identity(self):
        payload = b"verified-package"
        import hashlib
        request = DownloadRequest(
            "https://archive.archlinux.org/repos/2026/07/11/core/os/x86_64/test.pkg.tar.zst",
            "test.pkg.tar.zst", 1024, len(payload), hashlib.sha256(payload).hexdigest(),
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / request.filename
            path.write_bytes(payload)
            path.chmod(0o600)
            self.assertEqual(acquisition._validated_existing_bytes(request, path), len(payload))
            path.write_bytes(b"changed-package")
            with self.assertRaises(RuntimeError):
                acquisition._validated_existing_bytes(request, path)

    def test_resume_code_removes_only_validated_partial_names(self):
        source = Path(acquisition.__file__).read_text(encoding="utf-8")
        self.assertIn('name.removesuffix(".partial")', source)
        self.assertIn('os.unlink(name, dir_fd=files_fd)', source)
        self.assertIn('arguments == ["--resume"]', source)


if __name__ == "__main__":
    unittest.main()
