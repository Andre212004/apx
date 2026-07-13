from __future__ import annotations

from dataclasses import asdict, replace
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_release_candidate as candidate


def valid_candidate() -> candidate.ReleaseCandidate:
    return candidate.ReleaseCandidate(
        1,
        "candidate-" + "1" * 32,
        "build-" + "2" * 32,
        candidate.ROLE,
        candidate.ARCHITECTURE,
        "3" * 40,
        "4" * 64,
        "arch-base-20260713-v1",
        "5" * 64,
        "6" * 64,
        "7" * 64,
        "8" * 64,
        "9" * 64,
        "a" * 64,
        "b" * 64,
        "c" * 64,
        candidate.ARTIFACT_FORMAT,
        123456,
        321,
        "d" * 64,
        candidate.BACKEND,
        candidate.POLICY,
        candidate.EXECUTOR_PROTOCOL,
        candidate.PREFERENCES_SCHEMA,
    )


class ReleaseCandidateTests(unittest.TestCase):
    def test_canonical_round_trip_and_untrusted_classification(self) -> None:
        subject = valid_candidate()
        encoded = candidate.candidate_to_json(subject)
        self.assertEqual(candidate.parse_candidate_json(encoded), subject)
        self.assertEqual(encoded, candidate.candidate_to_json(subject))
        assessment = candidate.assess_candidate(subject)
        self.assertEqual(assessment.classification, "parsed-untrusted")
        self.assertEqual(assessment.issues, ("verification-and-admission-required",))
        self.assertEqual(len(assessment.candidate_digest), 64)

    def test_unknown_missing_duplicate_and_command_fields_fail(self) -> None:
        payload = asdict(valid_candidate())
        for mutation in ("unknown", "command", "destination_path", "signature"):
            changed = dict(payload)
            changed[mutation] = "unsafe"
            with self.assertRaises(candidate.ReleaseCandidateError):
                candidate.parse_candidate_json(json.dumps(changed))
        changed = dict(payload)
        del changed["artifact_sha256"]
        with self.assertRaises(candidate.ReleaseCandidateError):
            candidate.parse_candidate_json(json.dumps(changed))
        canonical = candidate.candidate_to_json(valid_candidate()).strip()
        duplicate = canonical[:-1] + ',"role":"hub-headless"}'
        with self.assertRaises(candidate.ReleaseCandidateError):
            candidate.parse_candidate_json(duplicate)

    def test_wrong_types_bounds_and_noncanonical_identifiers_fail(self) -> None:
        cases = (
            ("schema_version", True),
            ("candidate_id", "candidate-../hub"),
            ("build_operation_id", "build-not-hex"),
            ("source_revision", "ABC"),
            ("base_release_id", "../base"),
            ("artifact_size", 0),
            ("artifact_size", candidate.MAX_ARTIFACT_BYTES + 1),
            ("artifact_member_count", True),
            ("artifact_member_count", candidate.MAX_ARTIFACT_MEMBERS + 1),
        )
        for field, value in cases:
            payload = asdict(valid_candidate())
            payload[field] = value
            with self.subTest(field=field, value=value):
                with self.assertRaises(candidate.ReleaseCandidateError):
                    candidate.parse_candidate_json(json.dumps(payload))
        with self.assertRaises(candidate.ReleaseCandidateError):
            candidate.parse_candidate_json(" " * (candidate.MAX_METADATA_BYTES + 1))

    def test_every_fixed_boundary_and_digest_is_closed(self) -> None:
        subject = valid_candidate()
        fixed = {
            "role": "development",
            "architecture": "aarch64",
            "artifact_format": "tar",
            "backend": "privileged-container",
            "policy": "caller-policy",
            "executor_protocol": "shell-v1",
            "preferences_schema": "arbitrary-json",
        }
        for field, value in fixed.items():
            with self.subTest(field=field):
                with self.assertRaises(candidate.ReleaseCandidateError):
                    candidate.parse_candidate_json(
                        json.dumps(asdict(replace(subject, **{field: value})))
                    )
        for field in candidate.DIGEST_FIELDS:
            with self.subTest(field=field):
                with self.assertRaises(candidate.ReleaseCandidateError):
                    candidate.parse_candidate_json(
                        json.dumps(asdict(replace(subject, **{field: "0" * 63})))
                    )

    def test_import_plan_has_references_not_instructions(self) -> None:
        first = candidate.build_import_plan(valid_candidate())
        second = candidate.build_import_plan(valid_candidate())
        self.assertEqual(first, second)
        self.assertEqual(first.quarantine_policy, candidate.QUARANTINE_POLICY)
        self.assertIn("execute-or-extract-candidate", first.forbidden_effects)
        self.assertFalse(hasattr(first, "source_path"))
        self.assertFalse(hasattr(first, "destination_path"))
        self.assertFalse(hasattr(first, "command"))
        self.assertFalse(hasattr(first, "url"))
        self.assertEqual(len(first.plan_digest), 64)

    def test_security_relevant_changes_change_digests(self) -> None:
        subject = valid_candidate()
        initial_candidate_digest = candidate.candidate_digest(subject)
        initial_plan_digest = candidate.build_import_plan(subject).plan_digest
        for changed in (
            replace(subject, source_tree_sha256="e" * 64),
            replace(subject, artifact_sha256="e" * 64),
            replace(subject, artifact_size=subject.artifact_size + 1),
            replace(subject, artifact_member_count=subject.artifact_member_count + 1),
        ):
            self.assertNotEqual(candidate.candidate_digest(changed), initial_candidate_digest)
            self.assertNotEqual(candidate.build_import_plan(changed).plan_digest, initial_plan_digest)

    def test_direct_invalid_object_cannot_bypass_parser(self) -> None:
        invalid = replace(valid_candidate(), policy="caller-policy")
        for operation in (
            candidate.candidate_digest,
            candidate.candidate_to_json,
            candidate.build_import_plan,
        ):
            with self.subTest(operation=operation.__name__):
                with self.assertRaises(candidate.ReleaseCandidateError):
                    operation(invalid)


if __name__ == "__main__":
    unittest.main()
