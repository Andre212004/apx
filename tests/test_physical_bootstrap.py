import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "scripts" / "physical-pilot" / "bootstrap-apx-headless-pilot.sh"
HANDOFF = ROOT / "docs" / "physical-headless-development-handoff-v1.md"


class PhysicalBootstrapRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.script = BOOTSTRAP.read_text(encoding="utf-8")
        cls.handoff = HANDOFF.read_text(encoding="utf-8")

    def test_development_nspawn_uses_uplink_dns_not_host_stub(self) -> None:
        self.assertIn("--resolv-conf=replace-uplink", self.script)
        self.assertNotIn("--resolv-conf=copy-host", self.script)
        self.assertNotIn("--resolv-conf=copy-stub", self.script)

    def test_existing_release_must_be_explicitly_complete(self) -> None:
        self.assertNotIn("[[ -e $release ]] || return 0", self.script)
        self.assertIn("release_complete()", self.script)
        self.assertIn("manifest.json", self.script)
        self.assertIn("btrfs property get -ts", self.script)
        self.assertIn("ro=true", self.script)

    def test_recovery_is_limited_to_known_partial_development_release(self) -> None:
        self.assertIn("INCOMPLETE_DEVELOPMENT_RELEASE=$STATE/releases/development-headless-v1", self.script)
        self.assertIn("DELETE-INCOMPLETE-development-headless-v1", self.script)
        self.assertIn("--recover-incomplete-development-release", self.script)
        self.assertIn("development-headless-v1 is complete and must not be deleted", self.script)
        self.assertIn("has a manifest and is not the known no-manifest partial state", self.script)

    def test_handoff_documents_new_tag_and_exact_recovery_path(self) -> None:
        self.assertIn("physical-headless-pilot-recovery-v1", self.handoff)
        self.assertIn("Do not rerun the old `physical-headless-pilot-v1` bootstrap", self.handoff)
        self.assertIn("--recover-incomplete-development-release", self.handoff)
        self.assertIn("DELETE-INCOMPLETE-development-headless-v1", self.handoff)
        self.assertIn("APX_INCOMPLETE_DEVELOPMENT_RELEASE_REMOVED", self.handoff)


if __name__ == "__main__":
    unittest.main()
