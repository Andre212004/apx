from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_graphical_signature_verification as verification


class GraphicalSignatureVerificationTests(unittest.TestCase):
    def test_verifier_is_bound_to_graphical_manifest_and_194_packages(self):
        source = Path(verification.__file__).read_text(encoding="utf-8")
        self.assertEqual(len(verification.AUTHORIZED_MANIFEST), 64)
        self.assertIn("len(manifest.role_packages) != 194", source)

    def test_two_fixed_crypto_tools_and_no_network_are_used(self):
        source = Path(verification.__file__).read_text(encoding="utf-8").lower()
        self.assertIn('"/usr/bin/gpg"', Path(__import__("apx_signature_verification").__file__).read_text())
        self.assertIn('"/usr/bin/gpgv"', source)
        for forbidden in ("curl", "wget", "urllib", "requests"):
            self.assertNotIn(forbidden, source)

    def test_verification_root_is_fixed_and_under_tmp(self):
        self.assertTrue(str(verification.ROOT).startswith("/tmp/"))
        self.assertEqual(verification.ROOT.name, "apx-hyprland-signature-verification-20260711-v2")


if __name__ == "__main__":
    unittest.main()
