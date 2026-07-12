from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_trust_evidence as evidence


PLAN = "a" * 64
TIME = "2026-07-12T23:00:00Z"


def check(name: str, classification: str = "satisfied", detail: str = "observed"):
    return SimpleNamespace(
        section="Trust tools", name=name, classification=classification, evidence=detail
    )


def report(*checks):
    return SimpleNamespace(checks=checks)


class TrustEvidenceTests(unittest.TestCase):
    def seal(self, **changes):
        values = {
            "report": report(check("pacman"), check("GnuPG")),
            "acquisition_plan_digest": PLAN,
            "observed_at": TIME,
            "observer_context": "authoritative-executor",
        }
        values.update(changes)
        return evidence.create_trust_evidence_seal(**values)

    def test_authoritative_satisfied_evidence_is_verified_and_deterministic(self):
        first = self.seal()
        second = self.seal()
        self.assertEqual(first, second)
        self.assertEqual(first.state, "verified")

    def test_restricted_or_unavailable_evidence_remains_pending(self):
        restricted = self.seal(observer_context="restricted-observer")
        unavailable = self.seal(report=report(check("pacman", "unavailable")))
        self.assertEqual(restricted.state, "pending-authoritative-confirmation")
        self.assertEqual(unavailable.state, "pending-authoritative-confirmation")

    def test_blocked_evidence_blocks_in_every_context(self):
        seal = self.seal(
            report=report(check("pacman", "blocked")),
            observer_context="restricted-observer",
        )
        self.assertEqual(seal.state, "blocked")

    def test_raw_evidence_is_not_stored(self):
        seal = self.seal(report=report(check("pacman", detail="private diagnostic")))
        serialized = evidence.serialize_trust_evidence_seal(seal)
        self.assertNotIn("private diagnostic", serialized)
        self.assertEqual(len(seal.checks[0].evidence_digest), 64)

    def test_round_trip_is_canonical(self):
        serialized = evidence.serialize_trust_evidence_seal(self.seal())
        parsed = evidence.parse_trust_evidence_seal(serialized)
        self.assertEqual(parsed, self.seal())
        self.assertEqual(evidence.serialize_trust_evidence_seal(parsed), serialized)

    def test_tampering_and_wrong_state_are_rejected(self):
        seal = self.seal()
        with self.assertRaises(evidence.TrustEvidenceError):
            evidence.validate_trust_evidence_seal(replace(seal, acquisition_plan_digest="b" * 64))
        with self.assertRaises(evidence.TrustEvidenceError):
            evidence.validate_trust_evidence_seal(replace(seal, state="blocked"))

    def test_duplicate_checks_are_rejected(self):
        with self.assertRaisesRegex(evidence.TrustEvidenceError, "duplicate"):
            self.seal(report=report(check("pacman"), check("pacman")))

    def test_empty_oversized_and_malformed_input_are_rejected(self):
        with self.assertRaises(evidence.TrustEvidenceError):
            self.seal(report=report())
        with self.assertRaises(evidence.TrustEvidenceError):
            evidence.parse_trust_evidence_seal("x" * (evidence.MAX_EVIDENCE_BYTES + 1))
        with self.assertRaises(evidence.TrustEvidenceError):
            evidence.parse_trust_evidence_seal("not json")

    def test_unknown_duplicate_missing_and_wrong_typed_fields_are_rejected(self):
        payload = json.loads(evidence.serialize_trust_evidence_seal(self.seal()))
        payload["extra"] = True
        with self.assertRaises(evidence.TrustEvidenceError):
            evidence.parse_trust_evidence_seal(json.dumps(payload))
        original = evidence.serialize_trust_evidence_seal(self.seal()).strip()
        duplicate = original[:-1] + ',"state":"verified"}'
        with self.assertRaises(evidence.TrustEvidenceError):
            evidence.parse_trust_evidence_seal(duplicate)
        payload = json.loads(original)
        del payload["state"]
        with self.assertRaises(evidence.TrustEvidenceError):
            evidence.parse_trust_evidence_seal(json.dumps(payload))
        payload = json.loads(original)
        payload["schema_version"] = True
        with self.assertRaises(evidence.TrustEvidenceError):
            evidence.parse_trust_evidence_seal(json.dumps(payload))

    def test_invalid_time_context_labels_and_previous_digest_are_rejected(self):
        for changes in (
            {"observed_at": "2026-02-30T00:00:00Z"},
            {"observer_context": "hub"},
            {"previous_seal_digest": "bad"},
        ):
            with self.assertRaises(evidence.TrustEvidenceError):
                self.seal(**changes)


if __name__ == "__main__":
    unittest.main()
