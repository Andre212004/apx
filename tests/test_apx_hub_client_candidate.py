from dataclasses import replace
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import apx_hub_client_candidate as subject


def evidence():
    return subject.HubClientCandidateEvidence(
        subject.PROFILE, subject.REQUIRED_PACKAGES, "1" * 64, "1" * 64,
        True, True, True, True, True, True, True, True, True,
    )


class HubClientCandidateTests(unittest.TestCase):
    def test_all_evidence_reaches_manifest_freeze_not_release_admission(self) -> None:
        result = subject.assess_candidate(evidence())
        self.assertEqual(result.classification, "ready-for-separate-manifest-freeze")
        self.assertNotIn("admitted", result.classification)
        self.assertEqual(len(result.candidate_digest), 64)

    def test_every_behavior_and_trust_gate_blocks_independently(self) -> None:
        fields = (
            "source_reviewed", "no_privileged_effect_adapter",
            "no_arbitrary_command_or_path", "role_derived_by_trusted_launcher",
            "workload_management_refusal_passed", "fake_executor_suite_passed",
            "typed_executor_suite_passed", "accessibility_keyboard_passed",
            "deterministic_build_passed",
        )
        for field in fields:
            result = subject.assess_candidate(replace(evidence(), **{field: False}))
            self.assertEqual(result.classification, "blocked", field)

    def test_non_reproducible_build_blocks(self) -> None:
        result = subject.assess_candidate(replace(evidence(), second_artifact_digest="2" * 64))
        self.assertEqual(result.classification, "blocked")
        self.assertIn("independent Hub client builds differ", result.blockers)

    def test_profile_packages_digest_and_boolean_types_fail_closed(self) -> None:
        invalid = (
            replace(evidence(), profile="caller-profile"),
            replace(evidence(), package_names=("gtk4",)),
            replace(evidence(), first_artifact_digest="bad"),
            replace(evidence(), source_reviewed=1),
        )
        for value in invalid:
            with self.assertRaises(subject.HubClientCandidateError):
                subject.assess_candidate(value)
