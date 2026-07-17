from dataclasses import asdict, replace
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_physical_update as update


def candidate() -> update.PhysicalUpdateCandidate:
    return update.PhysicalUpdateCandidate(
        1,
        update.PROFILE,
        "update-" + "1" * 32,
        "2" * 40,
        "3" * 40,
        "4" * 64,
        8 * 1024**2,
        "5" * 64,
        40,
        ("host-executor", "host-runtime", "hub-client"),
        "6" * 64,
        601,
        4,
        "7" * 64,
        "8" * 64,
        "9" * 64,
        True,
        True,
        True,
        True,
        True,
    )


def installed() -> update.InstalledPilotEvidence:
    return update.InstalledPilotEvidence(
        1,
        update.PROFILE,
        "a" * 64,
        "b" * 64,
        candidate().parent_revision,
        "c" * 64,
        "d" * 64,
        "e" * 64,
        "hub-headless-v3",
        "12345678-1234-4123-8123-123456789abc",
        "22345678-1234-4123-8123-123456789abc",
        "f" * 64,
        True,
        True,
        True,
        True,
        True,
        True,
        100 * 1024**3,
    )


class PhysicalUpdateTests(unittest.TestCase):
    def test_complete_evidence_reaches_only_separate_import_approval(self) -> None:
        preview = update.build_update_preview(candidate(), installed())
        self.assertEqual(preview.classification, "ready-for-separate-import-approval")
        self.assertEqual(preview.blockers, ())
        self.assertTrue(preview.separate_import_approval_required)
        self.assertTrue(preview.separate_activation_approval_required)
        self.assertTrue(preview.rollback_retirement_requires_later_approval)
        self.assertEqual(preview.effects, update.UPDATE_EFFECTS)
        self.assertEqual(len(preview.plan_digest), 64)

    def test_candidate_parent_must_match_installed_revision(self) -> None:
        preview = update.build_update_preview(
            replace(candidate(), parent_revision="0" * 40), installed()
        )
        self.assertIn("candidate-parent-does-not-match-installed-revision", preview.blockers)

    def test_every_installed_safety_gate_blocks_independently(self) -> None:
        fields = (
            "audit_reconciled", "recovery_console_verified",
            "github_source_recovery_verified", "no_uncertain_apx_operation",
            "hub_clean", "development_repository_healthy",
        )
        for field in fields:
            with self.subTest(field=field):
                preview = update.build_update_preview(candidate(), replace(installed(), **{field: False}))
                self.assertEqual(preview.classification, "blocked")
        small = update.build_update_preview(candidate(), replace(installed(), host_free_bytes=15 * 1024**3))
        self.assertIn("host-reserve-below-16-gib", small.blockers)

    def test_candidate_rejects_commands_secrets_unknown_components_and_bad_bounds(self) -> None:
        cases = (
            ("credentials_absent", False),
            ("private_keys_absent", False),
            ("arbitrary_commands_absent", False),
            ("package_hooks_absent", False),
            ("candidate_is_untrusted", False),
            ("components", ("host-runtime", "shell-command")),
            ("components", ("hub-client", "hub-client")),
            ("artifact_bytes", update.MAX_ARTIFACT_BYTES + 1),
            ("member_count", update.MAX_MEMBERS + 1),
            ("tests_passed", 0),
        )
        for field, value in cases:
            with self.subTest(field=field):
                with self.assertRaises(update.PhysicalUpdateError):
                    update.build_update_preview(replace(candidate(), **{field: value}), installed())

    def test_installed_identity_types_and_profile_are_closed(self) -> None:
        cases = (
            ("profile", "production"),
            ("machine_identity_digest", "short"),
            ("installed_source_revision", "master"),
            ("hub_release", "latest"),
            ("hub_generation", "current"),
            ("audit_reconciled", 1),
            ("host_free_bytes", True),
        )
        for field, value in cases:
            with self.subTest(field=field):
                with self.assertRaises(update.PhysicalUpdateError):
                    update.build_update_preview(candidate(), replace(installed(), **{field: value}))

    def test_candidate_and_installed_json_are_closed_and_duplicate_safe(self) -> None:
        candidate_payload = asdict(candidate())
        installed_payload = asdict(installed())
        self.assertEqual(update.parse_candidate_json(json.dumps(candidate_payload)), candidate())
        self.assertEqual(update.parse_installed_evidence_json(json.dumps(installed_payload)), installed())
        candidate_payload["command"] = "install"
        with self.assertRaises(update.PhysicalUpdateError):
            update.parse_candidate_json(json.dumps(candidate_payload))
        canonical = json.dumps(asdict(installed()), separators=(",", ":"))
        duplicate = canonical[:-1] + ',"schema_version":1}'
        with self.assertRaises(update.PhysicalUpdateError):
            update.parse_installed_evidence_json(duplicate)

    def test_security_relevant_changes_change_the_plan(self) -> None:
        original = update.build_update_preview(candidate(), installed())
        changed_candidate = update.build_update_preview(
            replace(candidate(), artifact_sha256="0" * 64), installed()
        )
        changed_machine = update.build_update_preview(
            candidate(), replace(installed(), machine_identity_digest="1" * 64)
        )
        self.assertNotEqual(original.plan_digest, changed_candidate.plan_digest)
        self.assertNotEqual(original.plan_digest, changed_machine.plan_digest)


if __name__ == "__main__":
    unittest.main()
