"""Closed, non-extracting reader for physical-pilot update artifacts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import io
import json
import re
import tarfile

from apx_physical_update import PhysicalUpdateCandidate, PROFILE, validate_candidate


SCHEMA_VERSION = 1
MANIFEST_PATH = "manifest.json"
COMPONENT_PATHS = {
    "host-runtime": "components/host-runtime",
    "host-executor": "components/host-executor",
    "hub-client": "components/hub-client",
}
MAX_MANIFEST_BYTES = 64 * 1024
MAX_COMPONENT_BYTES = 8 * 1024**2
_SHA256 = re.compile(r"[0-9a-f]{64}")


class PhysicalUpdateArtifactError(ValueError):
    """Artifact bytes or member metadata are malformed or outside policy."""


@dataclass(frozen=True)
class PhysicalUpdateArtifactMember:
    component: str
    path: str
    bytes: int
    mode: int
    sha256: str


@dataclass(frozen=True)
class PhysicalUpdateArtifactManifest:
    schema_version: int
    profile: str
    source_revision: str
    parent_revision: str
    components: tuple[str, ...]
    members: tuple[PhysicalUpdateArtifactMember, ...]


@dataclass(frozen=True)
class PhysicalUpdateArtifactEvidence:
    artifact_sha256: str
    artifact_bytes: int
    manifest_digest: str
    member_count: int
    component_digests: tuple[tuple[str, str], ...]


def _duplicate_safe(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise PhysicalUpdateArtifactError("manifest JSON has duplicate fields")
        result[key] = value
    return result


def _canonical_manifest(manifest: PhysicalUpdateArtifactManifest) -> bytes:
    return json.dumps(
        asdict(manifest), sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8") + b"\n"


def validate_manifest(manifest: PhysicalUpdateArtifactManifest) -> None:
    if type(manifest) is not PhysicalUpdateArtifactManifest:
        raise PhysicalUpdateArtifactError("manifest object type is invalid")
    if manifest.schema_version != SCHEMA_VERSION or manifest.profile != PROFILE:
        raise PhysicalUpdateArtifactError("manifest schema or profile is invalid")
    for value in (manifest.source_revision, manifest.parent_revision):
        if not isinstance(value, str) or not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", value):
            raise PhysicalUpdateArtifactError("manifest revision is invalid")
    if manifest.source_revision == manifest.parent_revision:
        raise PhysicalUpdateArtifactError("manifest revisions are identical")
    if (
        type(manifest.components) is not tuple
        or tuple(sorted(set(manifest.components))) != manifest.components
        or not manifest.components
        or any(component not in COMPONENT_PATHS for component in manifest.components)
    ):
        raise PhysicalUpdateArtifactError("manifest component set is invalid")
    if type(manifest.members) is not tuple or len(manifest.members) != len(manifest.components):
        raise PhysicalUpdateArtifactError("manifest member set is incomplete")
    if tuple(member.component for member in manifest.members) != manifest.components:
        raise PhysicalUpdateArtifactError("manifest members are not in component order")
    for member in manifest.members:
        if type(member) is not PhysicalUpdateArtifactMember:
            raise PhysicalUpdateArtifactError("manifest member type is invalid")
        if member.path != COMPONENT_PATHS.get(member.component):
            raise PhysicalUpdateArtifactError("component path is not canonical")
        if type(member.bytes) is not int or not 0 < member.bytes <= MAX_COMPONENT_BYTES:
            raise PhysicalUpdateArtifactError("component byte count is invalid")
        if member.mode != 0o755:
            raise PhysicalUpdateArtifactError("component mode is not canonical")
        if not isinstance(member.sha256, str) or not _SHA256.fullmatch(member.sha256):
            raise PhysicalUpdateArtifactError("component digest is invalid")
    if len(_canonical_manifest(manifest)) > MAX_MANIFEST_BYTES:
        raise PhysicalUpdateArtifactError("manifest is oversized")


def manifest_to_bytes(manifest: PhysicalUpdateArtifactManifest) -> bytes:
    validate_manifest(manifest)
    return _canonical_manifest(manifest)


def parse_manifest_bytes(data: bytes) -> PhysicalUpdateArtifactManifest:
    if not isinstance(data, bytes) or not data or len(data) > MAX_MANIFEST_BYTES:
        raise PhysicalUpdateArtifactError("manifest bytes are empty or oversized")
    try:
        raw = json.loads(data.decode("utf-8"), object_pairs_hook=_duplicate_safe)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise PhysicalUpdateArtifactError("manifest JSON is invalid") from error
    expected = frozenset(PhysicalUpdateArtifactManifest.__dataclass_fields__)
    if not isinstance(raw, dict) or set(raw) != expected:
        raise PhysicalUpdateArtifactError("manifest fields do not match schema")
    raw_members = raw.get("members")
    if not isinstance(raw.get("components"), list) or not isinstance(raw_members, list):
        raise PhysicalUpdateArtifactError("manifest collections are malformed")
    member_fields = frozenset(PhysicalUpdateArtifactMember.__dataclass_fields__)
    if any(not isinstance(item, dict) or set(item) != member_fields for item in raw_members):
        raise PhysicalUpdateArtifactError("manifest member fields do not match schema")
    try:
        manifest = PhysicalUpdateArtifactManifest(
            raw["schema_version"], raw["profile"], raw["source_revision"],
            raw["parent_revision"], tuple(raw["components"]),
            tuple(PhysicalUpdateArtifactMember(**item) for item in raw_members),
        )
    except TypeError as error:
        raise PhysicalUpdateArtifactError("manifest values are malformed") from error
    validate_manifest(manifest)
    if data != _canonical_manifest(manifest):
        raise PhysicalUpdateArtifactError("manifest encoding is not canonical")
    return manifest


def inspect_artifact(
    artifact: bytes, candidate: PhysicalUpdateCandidate
) -> PhysicalUpdateArtifactEvidence:
    validate_candidate(candidate)
    if not isinstance(artifact, bytes) or not artifact:
        raise PhysicalUpdateArtifactError("artifact bytes are empty or wrong type")
    if len(artifact) != candidate.artifact_bytes:
        raise PhysicalUpdateArtifactError("artifact byte count disagrees with candidate")
    artifact_digest = hashlib.sha256(artifact).hexdigest()
    if artifact_digest != candidate.artifact_sha256:
        raise PhysicalUpdateArtifactError("artifact digest disagrees with candidate")
    try:
        archive = tarfile.open(fileobj=io.BytesIO(artifact), mode="r:")
        entries = archive.getmembers()
    except (tarfile.TarError, OSError) as error:
        raise PhysicalUpdateArtifactError("artifact is not a readable uncompressed tar") from error
    try:
        if len(entries) != candidate.member_count:
            raise PhysicalUpdateArtifactError("artifact member count disagrees with candidate")
        names = tuple(entry.name for entry in entries)
        if not names or names[0] != MANIFEST_PATH or len(set(names)) != len(names):
            raise PhysicalUpdateArtifactError("artifact member names are invalid")
        for entry in entries:
            if (
                not entry.isfile() or entry.name.startswith("/") or ".." in entry.name.split("/")
                or entry.uid != 0 or entry.gid != 0 or entry.mtime != 0
                or entry.pax_headers or entry.uname or entry.gname
            ):
                raise PhysicalUpdateArtifactError("artifact member metadata is outside policy")
            expected_mode = 0o600 if entry.name == MANIFEST_PATH else 0o755
            if entry.mode != expected_mode:
                raise PhysicalUpdateArtifactError("artifact member mode is outside policy")
        manifest_entry = archive.extractfile(entries[0])
        if manifest_entry is None:
            raise PhysicalUpdateArtifactError("manifest member is unreadable")
        manifest_bytes = manifest_entry.read(MAX_MANIFEST_BYTES + 1)
        manifest = parse_manifest_bytes(manifest_bytes)
        if hashlib.sha256(manifest_bytes).hexdigest() != candidate.member_manifest_digest:
            raise PhysicalUpdateArtifactError("manifest digest disagrees with candidate")
        if manifest.source_revision != candidate.source_revision or manifest.parent_revision != candidate.parent_revision:
            raise PhysicalUpdateArtifactError("manifest revisions disagree with candidate")
        if manifest.components != candidate.components:
            raise PhysicalUpdateArtifactError("manifest components disagree with candidate")
        expected_names = (MANIFEST_PATH,) + tuple(member.path for member in manifest.members)
        if names != expected_names:
            raise PhysicalUpdateArtifactError("artifact members disagree with manifest")
        evidence: list[tuple[str, str]] = []
        for entry, member in zip(entries[1:], manifest.members, strict=True):
            stream = archive.extractfile(entry)
            if stream is None:
                raise PhysicalUpdateArtifactError("component member is unreadable")
            content = stream.read(MAX_COMPONENT_BYTES + 1)
            digest = hashlib.sha256(content).hexdigest()
            if len(content) != member.bytes or digest != member.sha256:
                raise PhysicalUpdateArtifactError("component content disagrees with manifest")
            evidence.append((member.component, digest))
        return PhysicalUpdateArtifactEvidence(
            artifact_digest, len(artifact), hashlib.sha256(manifest_bytes).hexdigest(),
            len(entries), tuple(evidence),
        )
    finally:
        archive.close()
