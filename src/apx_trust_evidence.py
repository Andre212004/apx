"""Canonical, non-secret trust-evidence seal for APX base preparation.

This module never observes the host and never downloads anything. It converts a
supplied read-only readiness report into a bounded record tied to one exact
acquisition plan. Raw command output is represented only by SHA-256 digests.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime
import hashlib
import json
import re
from typing import Sequence


EVIDENCE_SCHEMA_VERSION = 1
MAX_EVIDENCE_BYTES = 64 * 1024
MAX_CHECKS = 64
CONTEXTS = ("restricted-observer", "authoritative-executor")
CLASSIFICATIONS = (
    "satisfied",
    "requires-host-confirmation",
    "unavailable",
    "blocked",
    "not-applicable",
)
SEAL_STATES = ("verified", "pending-authoritative-confirmation", "blocked")
_SHA256 = re.compile(r"[0-9a-f]{64}")
_SAFE_LABEL = re.compile(r"[A-Za-z0-9][A-Za-z0-9 ./_:+()-]{0,159}")
_UTC = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")


class TrustEvidenceError(ValueError):
    """The evidence record is malformed, ambiguous, or unsafe."""


@dataclass(frozen=True)
class SealedCheck:
    section: str
    name: str
    classification: str
    evidence_digest: str


@dataclass(frozen=True)
class TrustEvidenceSeal:
    schema_version: int
    acquisition_plan_digest: str
    experiment: str
    observed_at: str
    observer_context: str
    checks: tuple[SealedCheck, ...]
    state: str
    previous_seal_digest: str | None
    seal_digest: str


def _canonical(payload: object) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _payload(seal: TrustEvidenceSeal) -> dict[str, object]:
    payload = asdict(seal)
    payload.pop("seal_digest", None)
    return payload


def compute_seal_digest(seal: TrustEvidenceSeal) -> str:
    return hashlib.sha256(_canonical(_payload(seal)).encode("utf-8")).hexdigest()


def _evidence_digest(value: str) -> str:
    if not isinstance(value, str):
        raise TrustEvidenceError("check evidence must be text")
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _state(checks: Sequence[SealedCheck], context: str) -> str:
    states = {check.classification for check in checks if check.classification != "not-applicable"}
    if "blocked" in states:
        return "blocked"
    if context != "authoritative-executor" or states & {
        "requires-host-confirmation", "unavailable"
    }:
        return "pending-authoritative-confirmation"
    return "verified"


def create_trust_evidence_seal(
    *,
    report: object,
    acquisition_plan_digest: str,
    observed_at: str,
    observer_context: str,
    previous_seal_digest: str | None = None,
) -> TrustEvidenceSeal:
    source_checks = tuple(getattr(report, "checks", ()))
    if not source_checks or len(source_checks) > MAX_CHECKS:
        raise TrustEvidenceError("evidence must contain a bounded non-empty check set")
    checks = tuple(
        SealedCheck(
            section=getattr(check, "section", ""),
            name=getattr(check, "name", ""),
            classification=getattr(check, "classification", ""),
            evidence_digest=_evidence_digest(getattr(check, "evidence", None)),
        )
        for check in source_checks
    )
    draft = TrustEvidenceSeal(
        schema_version=EVIDENCE_SCHEMA_VERSION,
        acquisition_plan_digest=acquisition_plan_digest,
        experiment="system-container-v1",
        observed_at=observed_at,
        observer_context=observer_context,
        checks=checks,
        state=_state(checks, observer_context),
        previous_seal_digest=previous_seal_digest,
        seal_digest="0" * 64,
    )
    sealed = replace(draft, seal_digest=compute_seal_digest(draft))
    validate_trust_evidence_seal(sealed)
    return sealed


def validate_trust_evidence_seal(seal: TrustEvidenceSeal) -> None:
    if type(seal.schema_version) is not int or seal.schema_version != EVIDENCE_SCHEMA_VERSION:
        raise TrustEvidenceError("unsupported evidence schema")
    if not _SHA256.fullmatch(seal.acquisition_plan_digest):
        raise TrustEvidenceError("invalid acquisition plan digest")
    if seal.experiment != "system-container-v1":
        raise TrustEvidenceError("unexpected experiment")
    if not isinstance(seal.observed_at, str) or not _UTC.fullmatch(seal.observed_at):
        raise TrustEvidenceError("observation time must be canonical UTC")
    try:
        datetime.strptime(seal.observed_at, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as error:
        raise TrustEvidenceError("invalid observation time") from error
    if seal.observer_context not in CONTEXTS:
        raise TrustEvidenceError("unknown observer context")
    if not isinstance(seal.checks, tuple) or not seal.checks or len(seal.checks) > MAX_CHECKS:
        raise TrustEvidenceError("invalid check count")
    identities: set[tuple[str, str]] = set()
    for check in seal.checks:
        if not isinstance(check, SealedCheck):
            raise TrustEvidenceError("invalid check record")
        if not _SAFE_LABEL.fullmatch(check.section) or not _SAFE_LABEL.fullmatch(check.name):
            raise TrustEvidenceError("unsafe check identity")
        identity = (check.section, check.name)
        if identity in identities:
            raise TrustEvidenceError("duplicate check identity")
        identities.add(identity)
        if check.classification not in CLASSIFICATIONS:
            raise TrustEvidenceError("unknown check classification")
        if not _SHA256.fullmatch(check.evidence_digest):
            raise TrustEvidenceError("invalid check evidence digest")
    expected_state = _state(seal.checks, seal.observer_context)
    if seal.state not in SEAL_STATES or seal.state != expected_state:
        raise TrustEvidenceError("seal state does not match evidence")
    if seal.previous_seal_digest is not None and not _SHA256.fullmatch(seal.previous_seal_digest):
        raise TrustEvidenceError("invalid previous seal digest")
    if not _SHA256.fullmatch(seal.seal_digest) or seal.seal_digest != compute_seal_digest(seal):
        raise TrustEvidenceError("evidence seal digest mismatch")


def serialize_trust_evidence_seal(seal: TrustEvidenceSeal) -> str:
    validate_trust_evidence_seal(seal)
    return _canonical(asdict(seal)) + "\n"


def _no_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise TrustEvidenceError(f"duplicate field: {key}")
        result[key] = value
    return result


def parse_trust_evidence_seal(text: str) -> TrustEvidenceSeal:
    if not isinstance(text, str) or len(text.encode("utf-8")) > MAX_EVIDENCE_BYTES:
        raise TrustEvidenceError("evidence document is invalid or oversized")
    try:
        payload = json.loads(text, object_pairs_hook=_no_duplicates)
    except (json.JSONDecodeError, UnicodeError) as error:
        raise TrustEvidenceError("invalid evidence JSON") from error
    expected = set(TrustEvidenceSeal.__dataclass_fields__)
    if not isinstance(payload, dict) or set(payload) != expected:
        raise TrustEvidenceError("evidence fields do not match schema")
    raw_checks = payload["checks"]
    check_fields = set(SealedCheck.__dataclass_fields__)
    if not isinstance(raw_checks, list):
        raise TrustEvidenceError("checks must be a list")
    checks: list[SealedCheck] = []
    for raw in raw_checks:
        if not isinstance(raw, dict) or set(raw) != check_fields:
            raise TrustEvidenceError("check fields do not match schema")
        if not all(isinstance(raw[field], str) for field in check_fields):
            raise TrustEvidenceError("check fields must be text")
        checks.append(SealedCheck(**raw))
    scalar_types = {
        "schema_version": int,
        "acquisition_plan_digest": str,
        "experiment": str,
        "observed_at": str,
        "observer_context": str,
        "state": str,
        "seal_digest": str,
    }
    if any(type(payload[name]) is not expected_type for name, expected_type in scalar_types.items()):
        raise TrustEvidenceError("evidence field has wrong type")
    if payload["previous_seal_digest"] is not None and not isinstance(payload["previous_seal_digest"], str):
        raise TrustEvidenceError("previous seal digest has wrong type")
    seal = TrustEvidenceSeal(
        schema_version=payload["schema_version"],
        acquisition_plan_digest=payload["acquisition_plan_digest"],
        experiment=payload["experiment"],
        observed_at=payload["observed_at"],
        observer_context=payload["observer_context"],
        checks=tuple(checks),
        state=payload["state"],
        previous_seal_digest=payload["previous_seal_digest"],
        seal_digest=payload["seal_digest"],
    )
    validate_trust_evidence_seal(seal)
    return seal
