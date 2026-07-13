from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_signature_verification as verification


class SignatureVerificationTests(unittest.TestCase):
    TRUSTED = frozenset({"A" * 40, "B" * 40, "C" * 40, "D" * 40, "E" * 40})

    def test_validsig_returns_signer_and_primary(self):
        signer, primary = "1" * 40, "2" * 40
        output = f"[GNUPG:] GOODSIG key user\n[GNUPG:] VALIDSIG {signer} 2026 0 0 0 0 0 0 0 {primary}\n"
        self.assertEqual(verification.parse_valid_signature(output), (signer, primary))

    def test_rejection_status_or_missing_validsig_blocks(self):
        for output in ("", "[GNUPG:] BADSIG 123 user\n", "[GNUPG:] NO_PUBKEY 123\n"):
            with self.subTest(output=output):
                with self.assertRaises(verification.SignatureVerificationError):
                    verification.parse_valid_signature(output)

    def test_unrelated_expired_subkey_warning_does_not_override_valid_signer(self):
        signer, primary = "1" * 40, "2" * 40
        output = (
            "[GNUPG:] KEYEXPIRED 1642399435\n"
            f"[GNUPG:] VALIDSIG {signer} 2026 0 0 0 0 0 0 0 {primary}\n"
        )
        self.assertEqual(verification.parse_valid_signature(output), (signer, primary))
        with self.assertRaises(verification.SignatureVerificationError):
            verification.parse_valid_signature(
                f"[GNUPG:] EXPKEYSIG dead user\n[GNUPG:] VALIDSIG {signer} 2026 0 0 0 0 0 0 0 {primary}\n"
            )

    def test_only_valid_unique_current_master_certifications_count(self):
        def row(validity, issuer):
            return ":".join(["sig", validity] + [""] * 10 + [issuer])
        output = "\n".join((row("!", "A" * 40), row("!", "A" * 40), row("-", "B" * 40), row("!", "C" * 40), row("!", "F" * 40)))
        self.assertEqual(verification.parse_master_certifications(output, self.TRUSTED), ("A" * 40, "C" * 40))

    def test_three_masters_or_direct_master_are_required(self):
        self.assertTrue(verification.trust_is_sufficient("F" * 40, ("A" * 40, "B" * 40, "C" * 40), self.TRUSTED))
        self.assertFalse(verification.trust_is_sufficient("F" * 40, ("A" * 40, "B" * 40), self.TRUSTED))
        self.assertTrue(verification.trust_is_sufficient("A" * 40, (), self.TRUSTED))

    def test_fixed_verifiers_and_no_network_program_are_present(self):
        source = Path(verification.__file__).read_text(encoding="utf-8")
        self.assertIn('"/usr/bin/gpg"', source)
        self.assertIn('"/usr/bin/gpgv"', source)
        for forbidden in ("curl", "wget", "urllib", "requests"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
