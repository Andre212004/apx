"""Pure parser and non-mutating import plan for APX release candidates."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import re


SCHEMA_VERSION = 1
MAX_METADATA_BYTES = 64 * 1024
MAX_ARTIFACT_BYTES = 4 * 1024**3
MAX_ARTIFACT_MEMBERS = 500_000

ROLE = "hub-headless"
ARCHITECTURE = "x86_64"
ARTIFACT_FORMAT = "apx-root-tar-zst-v1"
BACKEND = "systemd-nspawn-headless-v1"
POLICY = "apx-hub-headless-v1"
EXECUTOR_PROTOCOL = "apx-executor-v1"
PREFERENCES_SCHEMA = "apx-hub-preferences-empty-v1"
QUARANTINE_POLICY = "apx-quarantine-v1"

_HEX_32_ID = re.compile(r"[0-9a-f]{32}")
_HEX_40_OR_64 = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})")
_HEX_64 = re.compile(r"[0-9a-f]{64}")
_RELEASE_ID = re.compile(r"[a-z0-9](?:[a-z0-9._-]{0,126}[a-z0-9])?")


class ReleaseCandidateError(ValueError):
    """Candidate metadata is malformed or outside the closed v1 schema."""


@dataclass(frozen=True)
class ReleaseCandidate:
    schema_version: int
    candidate_id: str
    build_operation_id: str
    role: str
    architecture: str
    source_revision: str
    source_tree_sha256: str
    base_release_id: str
    base_release_digest: str
    role_definition_digest: str
    package_manifest_digest: str
    normalized_root_digest: str
    build_evidence_digest: str
    test_evidence_digest: str
    reproducibility_evidence_digest: str
    sanitization_evidence_digest: str
    artifact_format: str
    artifact_size: int
    artifact_member_count: int
    artifact_sha256: str
    backend: str
    policy: str
    executor_protocol: str
    preferences_schema: str


@dataclass(frozen=True)
class CandidateAssessment:
    classification: str
    candidate_digest: str
    issues: tuple[str, ...]


@dataclass(frozen=True)
class ImportPlan:
    schema_version: int
    candidate_id: str
    build_operation_id: str
    candidate_digest: str
    artifact_format: str
    artifact_size: int
    artifact_member_count: int
    artifact_sha256: str
    quarantine_policy: str
    effects: tuple[str, ...]
    forbidden_effects: tuple[str, ...]
    plan_digest: str


FIELDS = frozenset(ReleaseCandidate.__dataclass_fields__)
DIGEST_FIELDS = (
    "source_tree_sha256",
    "base_release_digest",
    "role_definition_digest",
    "package_manifest_digest",
    "normalized_root_digest",
    "build_evidence_digest",
    "test_evidence_digest",
    "reproducibility_evidence_digest",
    "sanitization_evidence_digest",
    "artifact_sha256",
)
IMPORT_EFFECTS = (
    "reserve-new-executor-owned-quarantine-identity",
    "copy-bounded-immutable-candidate-bytes",
    "verify-complete-copied-artifact-digest",
    "publish-quarantine-object-only",
)
FORBIDDEN_IMPORT_EFFECTS = (
    "execute-or-extract-candidate",
    "overwrite-existing-object",
    "admit-release-to-catalogue",
    "create-or-replace-hub",
    "change-host-packages-or-policy",
    "accept-caller-selected-destination",
)


def _reject_duplicate_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ReleaseCandidateError("candidate metadata has duplicate fields")
        result[key] = value
    return result


def _canonical_bytes(candidate: ReleaseCandidate) -> bytes:
    return json.dumps(
        asdict(candidate), sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")


def candidate_digest(candidate: ReleaseCandidate) -> str:
    _validate_candidate(candidate)
    return hashlib.sha256(_canonical_bytes(candidate)).hexdigest()


def candidate_to_json(candidate: ReleaseCandidate) -> str:
    _validate_candidate(candidate)
    return _canonical_bytes(candidate).decode("ascii") + "\n"


def parse_candidate_json(text: str) -> ReleaseCandidate:
    if not isinstance(text, str):
        raise ReleaseCandidateError("candidate metadata must be text")
    try:
        encoded = text.encode("utf-8")
    except UnicodeEncodeError as error:
        raise ReleaseCandidateError("candidate metadata is not valid UTF-8") from error
    if not encoded or len(encoded) > MAX_METADATA_BYTES:
        raise ReleaseCandidateError("candidate metadata is empty or oversized")
    try:
        payload = json.loads(text, object_pairs_hook=_reject_duplicate_pairs)
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ReleaseCandidateError("candidate metadata JSON is invalid") from error
    if not isinstance(payload, dict) or set(payload) != FIELDS:
        raise ReleaseCandidateError("candidate metadata fields do not match schema")
    try:
        candidate = ReleaseCandidate(**payload)
    except TypeError as error:
        raise ReleaseCandidateError("candidate metadata values are malformed") from error

    _validate_candidate(candidate)
    return candidate


def _validate_candidate(candidate: ReleaseCandidate) -> None:
    if type(candidate) is not ReleaseCandidate:
        raise ReleaseCandidateError("candidate object has wrong type")
    if type(candidate.schema_version) is not int or candidate.schema_version != SCHEMA_VERSION:
        raise ReleaseCandidateError("candidate schema version is unsupported")
    if not isinstance(candidate.candidate_id, str) or not candidate.candidate_id.startswith("candidate-") or not _HEX_32_ID.fullmatch(candidate.candidate_id[10:]):
        raise ReleaseCandidateError("candidate ID is invalid")
    if not isinstance(candidate.build_operation_id, str) or not candidate.build_operation_id.startswith("build-") or not _HEX_32_ID.fullmatch(candidate.build_operation_id[6:]):
        raise ReleaseCandidateError("build operation ID is invalid")
    fixed = {
        "role": ROLE,
        "architecture": ARCHITECTURE,
        "artifact_format": ARTIFACT_FORMAT,
        "backend": BACKEND,
        "policy": POLICY,
        "executor_protocol": EXECUTOR_PROTOCOL,
        "preferences_schema": PREFERENCES_SCHEMA,
    }
    for field, expected in fixed.items():
        if getattr(candidate, field) != expected:
            raise ReleaseCandidateError(f"candidate {field} is unsupported")
    if not isinstance(candidate.source_revision, str) or not _HEX_40_OR_64.fullmatch(candidate.source_revision):
        raise ReleaseCandidateError("source revision is invalid")
    if not isinstance(candidate.base_release_id, str) or not _RELEASE_ID.fullmatch(candidate.base_release_id):
        raise ReleaseCandidateError("base release ID is invalid")
    for field in DIGEST_FIELDS:
        value = getattr(candidate, field)
        if not isinstance(value, str) or not _HEX_64.fullmatch(value):
            raise ReleaseCandidateError(f"candidate {field} is invalid")
    if type(candidate.artifact_size) is not int or not 1 <= candidate.artifact_size <= MAX_ARTIFACT_BYTES:
        raise ReleaseCandidateError("artifact size is outside policy")
    if type(candidate.artifact_member_count) is not int or not 1 <= candidate.artifact_member_count <= MAX_ARTIFACT_MEMBERS:
        raise ReleaseCandidateError("artifact member count is outside policy")


def assess_candidate(candidate: ReleaseCandidate) -> CandidateAssessment:
    digest = candidate_digest(candidate)
    return CandidateAssessment("parsed-untrusted", digest, ("verification-and-admission-required",))


def build_import_plan(candidate: ReleaseCandidate) -> ImportPlan:
    digest = candidate_digest(candidate)
    subject = {
        "artifact_format": candidate.artifact_format,
        "artifact_member_count": candidate.artifact_member_count,
        "artifact_sha256": candidate.artifact_sha256,
        "artifact_size": candidate.artifact_size,
        "build_operation_id": candidate.build_operation_id,
        "candidate_digest": digest,
        "candidate_id": candidate.candidate_id,
        "effects": IMPORT_EFFECTS,
        "forbidden_effects": FORBIDDEN_IMPORT_EFFECTS,
        "quarantine_policy": QUARANTINE_POLICY,
        "schema_version": SCHEMA_VERSION,
    }
    plan_digest = hashlib.sha256(
        json.dumps(subject, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return ImportPlan(
        SCHEMA_VERSION,
        candidate.candidate_id,
        candidate.build_operation_id,
        digest,
        candidate.artifact_format,
        candidate.artifact_size,
        candidate.artifact_member_count,
        candidate.artifact_sha256,
        QUARANTINE_POLICY,
        IMPORT_EFFECTS,
        FORBIDDEN_IMPORT_EFFECTS,
        plan_digest,
    )
