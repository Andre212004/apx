from pathlib import Path
import unittest


ROOT = Path(__file__).parents[1]
STATE = (ROOT / "PROJECT_STATE.md").read_text()
HANDOFF = (ROOT / "docs" / "physical-headless-development-handoff-v1.md").read_text()
AUDIT = (ROOT / "docs" / "physical-pilot-state-and-cleanup-audit-v1.md").read_text()
EXTERNAL_STORAGE = (ROOT / "docs" / "external-development-model-storage-v1.md").read_text()
CURRENT_HANDOFF = (ROOT / "CURRENT_HANDOFF.md").read_text()
UPDATE_CONTRACT = (ROOT / "docs" / "physical-pilot-update-contract-v1.md").read_text()
H0_CONTRACT = (ROOT / "docs" / "hyprland-h0-clean-host-v1.md").read_text()


class PhysicalPilotDocumentationTests(unittest.TestCase):
    def test_owner_report_and_pending_phases_are_consistent(self) -> None:
        for source in (STATE, HANDOFF, AUDIT):
            self.assertIn("Phases 1 through 8", source)
            self.assertIn("Phase 9", source)
        self.assertNotIn("Neither script has been executed on the physical target", STATE)
        self.assertIn("Ollama package is installed", STATE)
        self.assertIn("no local model has been downloaded", STATE)

    def test_handoff_blocks_replay_and_cleanup_before_audit(self) -> None:
        compact = " ".join(HANDOFF.split())
        self.assertIn("historical installed pilot", compact)
        self.assertIn("replayed on the current machine", compact)
        self.assertIn("do not substitute `master` for the frozen tag", compact)
        self.assertIn("Do not begin with `rm` or package removal", compact)
        self.assertIn("separately approved by the owner", compact)
        self.assertIn("Installing a local model is not a prerequisite", compact)

    def test_audit_is_read_only_and_separates_cleanup(self) -> None:
        compact = " ".join(AUDIT.split())
        self.assertIn("Never combine those sessions", AUDIT)
        self.assertIn("Unknown means preserve", AUDIT)
        self.assertIn("Separately Approved Cleanup Session", AUDIT)
        self.assertIn("This section is not standing authorization", AUDIT)
        self.assertIn("Do not download a model to make the audit complete", compact)

    def test_audit_covers_host_hub_development_and_sensitive_boundaries(self) -> None:
        for required in (
            "Establish the Host Context",
            "Inventory APX Host-Owned State",
            "Inspect Hub",
            "Inspect Development",
            "Phase 9 and Phase 10 Readiness",
            "UNEXPECTED_EXECUTOR_SOCKET",
        ):
            self.assertIn(required, AUDIT)
        for required in (
            "pacman -Q ollama qwen-code",
            "systemctl is-enabled ollama.service",
            "ollama list",
            "Known Ollama data locations",
            "Do not use `ollama pull`",
        ):
            self.assertIn(required, AUDIT)

    def test_external_storage_remains_a_non_implemented_proposal(self) -> None:
        self.assertIn("No external disk", EXTERNAL_STORAGE)
        self.assertIn("no shared writable host or Hub path", STATE)
        self.assertIn("External model storage remains blocked", EXTERNAL_STORAGE)
        self.assertIn("target-bound destructive formatting dossier", EXTERNAL_STORAGE)

    def test_current_handoff_and_update_contract_preserve_all_safety_blocks(self) -> None:
        for required in (
            "Owner-Reported Physical State",
            "Next Owner Action",
            "Current Repository Milestones",
            "Hard Stops",
            "Do not implement an external-SSD mount adapter",
        ):
            self.assertIn(required, CURRENT_HANDOFF)
        compact_update = " ".join(UPDATE_CONTRACT.split())
        for required in (
            "ready-for-separate-import-approval",
            "a second activation approval is required",
            "Rollback retirement is never included",
            "never automatically installs, rolls back, cleans, or deletes",
            "The current audit has not run",
        ):
            self.assertIn(required, compact_update)

    def test_h0_contract_is_clean_host_amd_only_and_recovery_first(self) -> None:
        compact_h0_contract = " ".join(H0_CONTRACT.split())
        for required in (
            "ready-for-separate-physical-approval",
            "AMD integrated GPU only",
            "built-in keyboard and touchpad only",
            "no NVIDIA GPU",
            "independent text recovery console",
            "never triggers an automatic graphical restart",
            "Only the final state may claim that the Hub path is restored",
            "Do not install Hyprland on the Host",
        ):
            self.assertIn(required, compact_h0_contract)


if __name__ == "__main__":
    unittest.main()
