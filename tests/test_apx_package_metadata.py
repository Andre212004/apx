from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_package_metadata as metadata


class PackageMetadataTests(unittest.TestCase):
    SAMPLE = """# generated
pkgname = demo
pkgver = 1.2-3
arch = x86_64
size = 42
packager = APX Test
builddate = 1780000000
depend = zlib
depend = glibc
depend = glibc
provides = demo.so=1-64
"""

    def test_parses_identity_and_canonical_multiple_values(self):
        item = metadata.parse_pkginfo(self.SAMPLE, filename="demo.pkg.tar.zst")
        self.assertEqual((item.name, item.version, item.architecture), ("demo", "1.2-3", "x86_64"))
        self.assertEqual(item.dependencies, ("glibc", "zlib"))

    def test_missing_duplicate_or_malformed_identity_is_rejected(self):
        cases = (self.SAMPLE.replace("pkgname = demo\n", ""), self.SAMPLE + "pkgname = other\n", self.SAMPLE + "bad row\n")
        for value in cases:
            with self.subTest(value=value):
                with self.assertRaises(metadata.PackageMetadataError):
                    metadata.parse_pkginfo(value, filename="demo")

    def test_bad_numbers_and_oversize_are_rejected(self):
        with self.assertRaises(metadata.PackageMetadataError):
            metadata.parse_pkginfo(self.SAMPLE.replace("size = 42", "size = no"), filename="demo")
        with self.assertRaises(metadata.PackageMetadataError):
            metadata.parse_pkginfo("x" * (metadata.MAX_METADATA_BYTES + 1), filename="demo")

    def test_inspection_is_fixed_offline_and_metadata_only(self):
        source = Path(metadata.__file__).read_text(encoding="utf-8")
        self.assertIn('"/usr/bin/bsdtar", "-xOf"', source)
        for forbidden in ("curl", "wget", "pacman", "sudo"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
