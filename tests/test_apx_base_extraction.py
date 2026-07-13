from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_base_extraction as extraction


class BaseExtractionTests(unittest.TestCase):
    def test_safe_member_paths_are_counted(self):
        self.assertEqual(extraction.validate_member_listing(b"usr/\nusr/bin/tool\netc/file\n"), 3)

    def test_absolute_parent_empty_and_non_utf8_paths_are_rejected(self):
        for listing in (b"/etc/passwd\n", b"usr/../etc/passwd\n", b"\n", b"usr/\xff\n"):
            with self.subTest(listing=listing):
                with self.assertRaises(extraction.BaseExtractionError):
                    extraction.validate_member_listing(listing)

    def test_listing_bound_is_enforced(self):
        with self.assertRaises(extraction.BaseExtractionError):
            extraction.validate_member_listing(b"a" * (extraction.MAX_LISTING_BYTES + 1))

    def test_effects_are_fixed_to_tmp_and_bsdtar(self):
        source = Path(extraction.__file__).read_text(encoding="utf-8")
        self.assertEqual(extraction.MAX_EXTRACTED_BYTES, 1024**3)
        self.assertTrue(str(extraction.ROOT).startswith("/tmp/"))
        self.assertIn('"/usr/bin/bsdtar"', source)
        for forbidden in ("sudo", "pacman", "systemctl"):
            self.assertNotIn(forbidden, source.lower())


if __name__ == "__main__":
    unittest.main()
