from __future__ import annotations

from dataclasses import asdict, replace
import json
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_package_acquisition as acquisition
import apx_resolution


class PackageAcquisitionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.real_manifest = apx_resolution.parse_resolution_manifest(
            acquisition.MANIFEST_PATH.read_text(encoding="utf-8")
        )

    def test_request_set_is_exactly_package_signature_pairs(self):
        requests = acquisition.fixed_requests(self.real_manifest)
        self.assertEqual(len(requests), 276)
        for package, signature in zip(requests[::2], requests[1::2]):
            self.assertEqual(signature.uri, package.uri + ".sig")
            self.assertEqual(signature.filename, package.filename + ".sig")
            self.assertEqual(signature.maximum_bytes, acquisition.SIGNATURE_MAX)
            self.assertIsNotNone(package.expected_sha256)

    def test_manifest_identity_change_blocks_all_requests(self):
        changed = replace(self.real_manifest, manifest_digest="a" * 64)
        with self.assertRaises(ValueError):
            acquisition.fixed_requests(changed)

    def test_existing_root_and_outside_tmp_refuse_before_network(self):
        with tempfile.TemporaryDirectory() as directory:
            existing = Path(directory) / "existing"
            existing.mkdir()
            with self.assertRaises(RuntimeError):
                acquisition.acquire_fixed_packages(
                    root=existing,
                    opener=lambda uri, timeout: self.fail("network must not run"),
                )
        with self.assertRaises(ValueError):
            acquisition.acquire_fixed_packages(
                root=Path("/var/lib/apx/not-authorized"),
                opener=lambda uri, timeout: self.fail("network must not run"),
            )

    def test_serialized_manifest_tampering_blocks_before_root_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            payload = asdict(self.real_manifest)
            payload["packages"][0]["sha256"] = "a" * 64
            manifest_path = Path(directory) / "manifest.json"
            manifest_path.write_text(json.dumps(payload), encoding="utf-8")
            root = Path(directory) / "new-root"
            with self.assertRaises(apx_resolution.ResolutionError):
                acquisition.acquire_fixed_packages(
                    root=root,
                    manifest_path=manifest_path,
                    opener=lambda uri, timeout: self.fail("network must not run"),
                )
            self.assertFalse(root.exists())


if __name__ == "__main__":
    unittest.main()
