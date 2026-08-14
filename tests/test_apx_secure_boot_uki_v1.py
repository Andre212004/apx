from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class SecureBootUkiV1Tests(unittest.TestCase):
    def test_recovery_uki_is_signed_but_does_not_request_tpm_unlock(self):
        config = (ROOT / "config/kernel/uki.conf").read_text()
        cmdline = (ROOT / "config/kernel/cmdline-luks-v1").read_text().strip()
        self.assertIn("SecureBootPrivateKey=/etc/kernel/secure-boot-private-key.pem", config)
        self.assertIn("SecureBootCertificate=/etc/kernel/secure-boot-certificate.pem", config)
        self.assertIn("SecureBootSigningTool=systemd-sbsign", config)
        self.assertIn("SignKernel=no", config)
        self.assertIn("PCRBanks=sha256", config)
        self.assertIn("rd.luks.name=3ad5fc06-c4eb-4bb2-936b-f75eff3bc1c4=cryptroot", cmdline)
        self.assertIn("quiet splash", cmdline)
        self.assertNotIn("tpm2", cmdline)

    def test_boot_entry_points_only_to_fixed_recovery_uki(self):
        entry = (ROOT / "config/systemd-boot/apx-secure-boot-v1.conf").read_text()
        self.assertEqual(entry, "title APX System\nefi /EFI/APX/apx-system-v1.efi\n")

    def test_only_tty1_is_reserved_for_host_recovery(self):
        config = (ROOT / "config/systemd-logind/10-apx-virtual-terminals-v1.conf").read_text()
        self.assertEqual(config, "[Login]\nNAutoVTs=1\nReserveVT=1\n")

    def test_documented_sequence_never_wipes_password_before_proof(self):
        document = (ROOT / "docs/secure-boot-measured-uki-tpm-unlock-v1-2026-08-03.md").read_text()
        for required in (
            "Only then enroll a TPM2 token bound to PCR 7",
            "Preserve the signed LUKS-only recovery UKI",
            "The password slot is never wiped",
            "TPM enrollment is not performed from the current unverified boot",
        ):
            self.assertIn(required, document)


if __name__ == "__main__":
    unittest.main()
