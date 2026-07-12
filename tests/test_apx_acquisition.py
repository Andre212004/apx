from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_acquisition as acquisition


HASH = "a" * 64


class AcquisitionTests(unittest.TestCase):
    def item(self, **changes):
        values = {
            "kind": "package",
            "repository": "core",
            "architecture": "x86_64",
            "filename": "bash-5.3-1-x86_64.pkg.tar.zst",
            "uri": acquisition.ARCHIVE_ORIGIN + acquisition.ARCHIVE_PREFIX + "core/os/x86_64/bash-5.3-1-x86_64.pkg.tar.zst",
            "expected_bytes": 1024,
            "expected_sha256": HASH,
        }
        values.update(changes)
        return acquisition.AcquisitionItem(**values)

    def transfer(self, item=None, **changes):
        item = item or self.item()
        values = {
            "requested_uri": item.uri,
            "final_uri": item.uri,
            "filename": item.filename,
            "bytes_received": item.expected_bytes,
            "sha256": item.expected_sha256 or HASH,
            "regular_file": True,
            "symlink": False,
            "complete": True,
        }
        values.update(changes)
        return acquisition.ObservedTransfer(**values)

    def test_fixed_item_is_accepted_without_downloading(self):
        result = acquisition.assess_acquisition_manifest((self.item(),))
        self.assertEqual(result.decision, "accepted-boundary-only")
        self.assertEqual(len(result.manifest_digest), 64)

    def test_origin_scheme_credentials_port_query_fragment_and_redirect_are_rejected(self):
        bad_uris = (
            self.item().uri.replace("https://", "http://"),
            self.item().uri.replace("archive.archlinux.org", "mirror.example"),
            self.item().uri.replace("archive.archlinux.org", "user@archive.archlinux.org"),
            self.item().uri.replace("archive.archlinux.org", "archive.archlinux.org:443"),
            self.item().uri + "?x=1",
            self.item().uri + "#x",
        )
        for uri in bad_uris:
            with self.subTest(uri=uri):
                self.assertEqual(
                    acquisition.assess_acquisition_manifest((self.item(uri=uri),)).decision,
                    "blocked",
                )

    def test_traversal_encoded_path_and_unsafe_filename_are_rejected(self):
        for filename in ("../pkg", "..", "pkg/name", " pkg"):
            with self.subTest(filename=filename):
                item = self.item(filename=filename, uri=self.item().uri.rsplit("/", 1)[0] + "/" + filename)
                self.assertEqual(acquisition.assess_acquisition_manifest((item,)).decision, "blocked")
        encoded = self.item(uri=self.item().uri.replace("bash-", "%2e%2e/bash-"))
        self.assertEqual(acquisition.assess_acquisition_manifest((encoded,)).decision, "blocked")

    def test_repository_architecture_kind_and_digest_are_closed(self):
        for changes in (
            {"repository": "testing"},
            {"architecture": "aarch64"},
            {"kind": "script"},
            {"expected_sha256": "bad"},
        ):
            self.assertEqual(acquisition.assess_acquisition_manifest((self.item(**changes),)).decision, "blocked")

    def test_per_file_aggregate_count_duplicate_and_order_limits(self):
        too_large = self.item(expected_bytes=acquisition.PACKAGE_MAX + 1)
        self.assertEqual(acquisition.assess_acquisition_manifest((too_large,)).decision, "blocked")
        duplicate = (self.item(), self.item())
        self.assertEqual(acquisition.assess_acquisition_manifest(duplicate).decision, "blocked")
        second = self.item(
            repository="extra",
            filename="z.pkg.tar.zst",
            uri=acquisition.ARCHIVE_ORIGIN + acquisition.ARCHIVE_PREFIX + "extra/os/x86_64/z.pkg.tar.zst",
            expected_bytes=acquisition.AGGREGATE_MAX,
        )
        self.assertEqual(acquisition.assess_acquisition_manifest((self.item(), second)).decision, "blocked")
        self.assertEqual(acquisition.assess_acquisition_manifest((second, self.item())).decision, "blocked")

    def test_empty_wrong_typed_and_malformed_sizes_block(self):
        self.assertEqual(acquisition.assess_acquisition_manifest(()).decision, "blocked")
        self.assertEqual(acquisition.assess_acquisition_manifest("x").decision, "blocked")
        self.assertEqual(acquisition.assess_acquisition_manifest((object(),)).decision, "blocked")
        for value in (-1, True):
            self.assertEqual(acquisition.assess_acquisition_manifest((self.item(expected_bytes=value),)).decision, "blocked")

    def test_matching_transfer_evidence_passes(self):
        item = self.item()
        self.assertEqual(acquisition.verify_transfer(item, self.transfer(item)), ())

    def test_every_transfer_identity_and_completion_mismatch_fails(self):
        item = self.item()
        cases = (
            {"requested_uri": "https://example.invalid/x"},
            {"final_uri": "https://example.invalid/x"},
            {"filename": "other"},
            {"bytes_received": 1},
            {"sha256": "b" * 64},
            {"regular_file": False},
            {"symlink": True},
            {"complete": False},
        )
        for changes in cases:
            with self.subTest(changes=changes):
                self.assertTrue(acquisition.verify_transfer(item, self.transfer(item, **changes)))

    def test_transfer_wrong_types_fail_closed(self):
        self.assertTrue(acquisition.verify_transfer(object(), object()))
        self.assertTrue(acquisition.verify_transfer(self.item(), replace(self.transfer(), bytes_received=True)))


if __name__ == "__main__":
    unittest.main()
