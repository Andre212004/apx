from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_recovery_console as recovery
import apx_hyprland_release_promotion as h0_promotion


STATE = (ROOT / "PROJECT_STATE.md").read_text()
HANDOFF = (ROOT / "docs" / "physical-headless-development-handoff-v1.md").read_text()
AUDIT = (ROOT / "docs" / "physical-pilot-state-and-cleanup-audit-v1.md").read_text()
EXTERNAL_STORAGE = (ROOT / "docs" / "external-development-model-storage-v1.md").read_text()
HOST_LOCAL_MODEL = (
    ROOT / "docs" / "host-local-coder-external-ssd-v1-2026-08-05.md"
).read_text()
CURRENT_HANDOFF = (ROOT / "CURRENT_HANDOFF.md").read_text()
UPDATE_CONTRACT = (ROOT / "docs" / "physical-pilot-update-contract-v1.md").read_text()
H0_CONTRACT = (ROOT / "docs" / "hyprland-h0-clean-host-v1.md").read_text()
ROOT_HOST_MODE = (ROOT / "docs" / "temporary-root-host-development-mode-v1.md").read_text()
ROOT_HOST_PREPARE = (
    ROOT / "scripts" / "physical-pilot" / "prepare-root-host-development-mode-v1.sh"
).read_text()
RUNTIME_FIX_UPDATE = (
    ROOT / "docs" / "physical-runtime-generation-fix-update-2026-07-18.md"
).read_text()
RECOVERY_RECEIPT = (
    ROOT / "docs" / "physical-recovery-console-rehearsal-2026-07-18.json"
).read_text()
H0_OBSERVATION = (
    ROOT / "docs" / "hyprland-h0-read-only-observation-2026-07-18.md"
).read_text()
H0_PROMOTION_CONTRACT = (
    ROOT / "docs" / "hyprland-h0-release-promotion-v1.md"
).read_text()
H0_PROMOTION_EVIDENCE = (
    ROOT / "docs" / "hyprland-h0-release-promotion-preview-2026-07-18.json"
).read_text()
H0_PROMOTION_RESULT = (
    ROOT / "docs" / "hyprland-h0-release-promotion-result-2026-07-18.json"
).read_text()


class PhysicalPilotDocumentationTests(unittest.TestCase):
    def test_reconciled_development_drift_and_pending_phases_are_consistent(self) -> None:
        for source in (STATE, HANDOFF, AUDIT):
            self.assertIn("Phases 1 through 8", source)
            self.assertIn("Phase 9", source)
        self.assertNotIn("Neither script has been executed on the physical target", STATE)
        self.assertIn("complete stop and destroy", STATE)
        self.assertIn("empty home", STATE)
        self.assertIn("delays Phase 10 removal", STATE)
        self.assertIn("does not block repository development", STATE)
        self.assertIn("Owner-Confirmed Lifecycle Test", CURRENT_HANDOFF)
        self.assertIn("No registered APX snapshot", CURRENT_HANDOFF)
        self.assertIn("intentional lifecycle test", STATE)
        self.assertIn("codex-test-*", CURRENT_HANDOFF)

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

    def test_external_storage_records_the_owner_authorized_host_deviation(self) -> None:
        self.assertIn("historical Development-local proposal", EXTERNAL_STORAGE)
        self.assertIn("Host-local coder on target-bound external SSD", STATE)
        self.assertIn("owner-authorized physical implementation", HOST_LOCAL_MODEL)
        self.assertIn("TPM2 automatic unlock bound to SHA-256 PCR 7", HOST_LOCAL_MODEL)
        self.assertIn("uses a second-click confirmation", HOST_LOCAL_MODEL)
        self.assertIn("read-only during normal inference", HOST_LOCAL_MODEL)

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
            "2026-07-18 root-host reconciliation",
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

    def test_temporary_root_host_mode_is_explicit_and_bounded(self) -> None:
        compact = " ".join(ROOT_HOST_MODE.split())
        for required in (
            "temporary root-host development mode",
            "not the APX production design",
            "disposable test Environments that it created",
            "changing or destroying Hub or Development requires fresh owner approval",
            "Do not clean anything yet",
            "Exit and complete removal",
            "reinstall Arch",
        ):
            self.assertIn(required, compact)

    def test_root_host_prepare_is_identity_bound_and_has_no_cleanup(self) -> None:
        for required in (
            'EXPECTED_HOSTNAME="apx-host"',
            'EXPECTED_VENDOR="LENOVO"',
            'EXPECTED_PRODUCT="82JU"',
            'EXPECTED_BOARD="LNVNB161216"',
            'EXPECTED_PROFILE="profile=apx-physical-headless-pilot-v1"',
            "ENABLE TEMPORARY ROOT CODEX ON APX-HOST",
            "https://chatgpt.com/codex/install.sh",
            "codex login --device-auth",
        ):
            self.assertIn(required, ROOT_HOST_PREPARE)
        for forbidden in (
            "pacman -R",
            "btrfs subvolume delete",
            "apx environment destroy",
        ):
            self.assertNotIn(forbidden, ROOT_HOST_PREPARE)

    def test_runtime_generation_fix_candidate_is_exact_and_still_blocked(self) -> None:
        compact = " ".join(RUNTIME_FIX_UPDATE.split())
        for required in (
            "host-runtime",
            "30720",
            "recovery-console-not-verified",
            "Separately authorized recovery-console rehearsal",
            "distinct before/recovery boot IDs",
            "fresh approval for the exact reboot window",
            "Minimum-privilege effect map",
            "No automatic rollback is allowed",
            "do not destroy",
        ):
            self.assertIn(required, compact)

    def test_physical_update_mapping_is_fixed_but_non_executing(self) -> None:
        compact = " ".join(UPDATE_CONTRACT.split())
        for required in (
            "/var/lib/apx/updates/staging",
            "candidate.tar",
            "/usr/lib/apx/apx-lab-runtime.py",
            "/usr/bin/apx",
            "host-executor",
            "hub-client",
            "fails closed",
            "does not create staging",
        ):
            self.assertIn(required, compact)

    def test_physical_recovery_receipt_is_verified_but_old_preview_is_stale(self) -> None:
        evidence = recovery.parse_recovery_evidence_json(RECOVERY_RECEIPT)
        assessment = recovery.assess_recovery_console(evidence)
        self.assertEqual(assessment.classification, "verified")
        self.assertEqual(assessment.blockers, ())
        self.assertEqual(
            assessment.evidence_digest,
            "db70438f786c3282755c44940bc27a5b18095bd31eeb4a904dbce62003634ad2",
        )
        compact = " ".join(RUNTIME_FIX_UPDATE.split())
        self.assertIn("Recovery-console result — 2026-07-18", compact)
        self.assertIn("original preview", compact)
        self.assertIn("are now stale", compact)

    def test_current_h0_observation_is_headless_sanitized_and_not_promoted(self) -> None:
        compact = " ".join(H0_OBSERVATION.split())
        for required in (
            "/dev/dri/card2",
            "/dev/dri/renderD129",
            "card2-eDP-2",
            "platform-i8042-serio-0",
            "platform-AMDI0010:01",
            "built package count: 332",
            "private-key, random-seed, pacman-trust",
            "83c58deaa56c83c23eee57dc02ecd3a67ccaede0d75918932f7f3b9557ab3401",
            "must not be copied into `/var/lib/apx`",
        ):
            self.assertIn(required, compact)

    def test_h0_release_promotion_preview_is_ready_but_grants_no_graphics(self) -> None:
        evidence = h0_promotion.parse_promotion_evidence_json(H0_PROMOTION_EVIDENCE)
        preview = h0_promotion.build_promotion_preview(evidence)
        self.assertEqual(preview.classification, "ready-for-separate-promotion-approval")
        self.assertEqual(preview.blockers, ())
        self.assertEqual(
            preview.plan_digest,
            "dc15038fa6147f6f2ba098e90f880898ff4523586117bc0a338f9ea6e067146d",
        )
        self.assertTrue(preview.environment_creation_not_authorized)
        self.assertTrue(preview.graphical_activation_not_authorized)
        compact = " ".join(H0_PROMOTION_CONTRACT.split())
        self.assertIn("At preview time no promotion had run", " ".join(CURRENT_HANDOFF.split()))
        self.assertIn("not standing permission to execute promotion", compact)

    def test_h0_release_result_is_immutable_and_preserves_neighbours(self) -> None:
        result = __import__("json").loads(H0_PROMOTION_RESULT)
        self.assertEqual(result["release_id"], "hyprland-h0-v1")
        self.assertEqual(result["package_count"], 332)
        self.assertEqual(
            result["configured_tree_digest"],
            "4798a8f6a0396dfab94758a9bb2498364a72948c6b2587593eadc04faca15b92",
        )
        for field in (
            "root_read_only", "source_preserved", "hub_generation_unchanged",
            "development_generation_unchanged", "disposable_hold_unchanged",
            "no_uncertain_apx_operation",
        ):
            self.assertIs(result[field], True)
        compact = " ".join(H0_PROMOTION_CONTRACT.split())
        self.assertIn("No Environment was created", compact)


if __name__ == "__main__":
    unittest.main()
