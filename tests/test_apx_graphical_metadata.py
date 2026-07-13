from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_graphical_metadata as metadata


class GraphicalMetadataTests(unittest.TestCase):
    def test_inspection_is_bound_to_signature_evidence_and_count(self):
        source = Path(metadata.__file__).read_text(encoding="utf-8")
        self.assertEqual(len(metadata.AUTHORIZED_SIGNATURE_EVIDENCE), 64)
        self.assertIn("len(signed) != 194", source)

    def test_only_pkginfo_is_read_and_output_is_bounded(self):
        source = Path(metadata.__file__).read_text(encoding="utf-8")
        self.assertIn('"/usr/bin/bsdtar", "-xOf"', source)
        self.assertIn('".PKGINFO"', source)
        self.assertIn("MAX_METADATA_BYTES", source)
        for forbidden in ("pacman", "systemd-nspawn", "curl", "wget"):
            self.assertNotIn(forbidden, source)

    def test_output_root_is_fixed_under_tmp(self):
        self.assertTrue(str(metadata.ROOT).startswith("/tmp/"))
        self.assertEqual(metadata.ROOT.name, "apx-hyprland-metadata-20260711-v1")


if __name__ == "__main__":
    unittest.main()
