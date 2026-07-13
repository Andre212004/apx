"""Pure APX release member-manifest and reproducibility contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import hashlib
import json
import posixpath
import re
import unicodedata

from apx_release_candidate import ReleaseCandidate, candidate_digest


SCHEMA_VERSION = 1
MAX_MEMBERS = 500_000
MAX_TOTAL_REGULAR_BYTES = 16 * 1024**3
MAX_PATH_BYTES = 4096
MAX_SERIALIZED_BYTES = 64 * 1024**2
MAX_NUMERIC_ID = 65_535
KINDS = ("directory", "regular", "symlink", "hardlink")
REQUIRED_DIRECTORIES = ("etc", "home", "usr", "var")

_SHA256 = re.compile(r"[0-9a-f]{64}")
_FORBIDDEN_EXACT = {
    "etc/hostname",
    "etc/machine-id",
    "var/lib/dbus/machine-id",
    "var/lib/systemd/random-seed",
}
_FORBIDDEN_CONTENT_PREFIXES = (
    "home/",
    "root/",
    "run/",
    "tmp/",
    "var/tmp/",
    "var/lib/apx/",
    "etc/pacman.d/gnupg/private-keys-v1.d/",
)
_FORBIDDEN_SEGMENTS = {".cache", ".codex", ".git", ".gnupg", ".ssh"}


class ReleaseArtifactError(ValueError):
    """Release member metadata or reproducibility evidence is invalid."""


@dataclass(frozen=True)
class ArchiveMember:
    path: str
    kind: str
    size: int
    mode: int
    uid: int
    gid: int
    content_sha256: str | None
    link_target: str | None


@dataclass(frozen=True)
class ReleaseArtifactManifest:
    schema_version: int
    candidate_digest: str
    artifact_sha256: str
    member_count: int
    total_regular_bytes: int
    members: tuple[ArchiveMember, ...]
    normalized_root_digest: str
    manifest_digest: str


@dataclass(frozen=True)
class ReproducibilityAssessment:
    classification: str
    issues: tuple[str, ...]
    first_manifest_digest: str
    second_manifest_digest: str


def _digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()


def _validate_path(path: object, *, label: str = "member path") -> str:
    if not isinstance(path, str) or not path:
        raise ReleaseArtifactError(f"{label} is empty or not text")
    if unicodedata.normalize("NFC", path) != path:
        raise ReleaseArtifactError(f"{label} is not Unicode NFC")
    if any(not character.isprintable() for character in path):
        raise ReleaseArtifactError(f"{label} contains non-printable content")
    if len(path.encode("utf-8")) > MAX_PATH_BYTES or path.startswith("/"):
        raise ReleaseArtifactError(f"{label} is absolute or oversized")
    parts = path.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise ReleaseArtifactError(f"{label} is not normalized")
    if posixpath.normpath(path) != path:
        raise ReleaseArtifactError(f"{label} is not canonical")
    return path


def _validate_link_target(member_path: str, target: object) -> str:
    if not isinstance(target, str) or not target:
        raise ReleaseArtifactError("link target is empty or not text")
    if unicodedata.normalize("NFC", target) != target or any(
        not character.isprintable() for character in target
    ):
        raise ReleaseArtifactError("link target is not canonical text")
    if len(target.encode("utf-8")) > MAX_PATH_BYTES:
        raise ReleaseArtifactError("link target is oversized")
    if target.startswith("/"):
        resolved = posixpath.normpath(target.lstrip("/"))
    else:
        resolved = posixpath.normpath(posixpath.join(posixpath.dirname(member_path), target))
    if resolved in {"", ".", ".."} or resolved.startswith("../") or "/../" in f"/{resolved}/":
        raise ReleaseArtifactError("link target escapes or does not identify a member path")
    _validate_path(resolved, label="resolved link target")
    return target


def _validate_member_shape(member: ArchiveMember) -> None:
    if type(member) is not ArchiveMember:
        raise ReleaseArtifactError("archive member has wrong type")
    _validate_path(member.path)
    if member.kind not in KINDS:
        raise ReleaseArtifactError("archive member kind is unsupported")
    if type(member.size) is not int or not 0 <= member.size <= MAX_TOTAL_REGULAR_BYTES:
        raise ReleaseArtifactError("archive member size is invalid")
    if type(member.mode) is not int or not 0 <= member.mode <= 0o1777 or member.mode & 0o6000:
        raise ReleaseArtifactError("archive member mode is invalid or privileged")
    if any(type(value) is not int or not 0 <= value <= MAX_NUMERIC_ID for value in (member.uid, member.gid)):
        raise ReleaseArtifactError("archive member owner is invalid")
    if member.kind == "regular":
        if not isinstance(member.content_sha256, str) or not _SHA256.fullmatch(member.content_sha256):
            raise ReleaseArtifactError("regular member lacks canonical content digest")
        if member.link_target is not None:
            raise ReleaseArtifactError("regular member cannot have link target")
    elif member.kind == "directory":
        if member.size != 0 or member.content_sha256 is not None or member.link_target is not None:
            raise ReleaseArtifactError("directory member has file or link content")
    elif member.kind == "symlink":
        if member.size != 0 or member.content_sha256 is not None:
            raise ReleaseArtifactError("link member has file content")
        _validate_link_target(member.path, member.link_target)
        if member.mode & 0o1000:
            raise ReleaseArtifactError("link member cannot use sticky mode")
    else:
        if member.size != 0 or member.content_sha256 is not None:
            raise ReleaseArtifactError("link member has file content")
        _validate_path(member.link_target, label="hardlink target")
        if member.mode & 0o1000:
            raise ReleaseArtifactError("link member cannot use sticky mode")
    if member.kind != "directory" and member.mode & 0o1000:
        raise ReleaseArtifactError("non-directory member cannot use sticky mode")


def _check_forbidden_path(member: ArchiveMember) -> None:
    path = member.path
    if path in _FORBIDDEN_EXACT or any(path.startswith(prefix) for prefix in _FORBIDDEN_CONTENT_PREFIXES):
        raise ReleaseArtifactError("release contains forbidden mutable or identity path")
    if any(segment in _FORBIDDEN_SEGMENTS for segment in path.split("/")):
        raise ReleaseArtifactError("release contains Development, credential, or cache path")


def validate_members(members: tuple[ArchiveMember, ...]) -> None:
    if not isinstance(members, tuple) or not 1 <= len(members) <= MAX_MEMBERS:
        raise ReleaseArtifactError("archive member count is outside policy")
    for member in members:
        _validate_member_shape(member)
        _check_forbidden_path(member)
    paths = tuple(member.path for member in members)
    if paths != tuple(sorted(paths)) or len(set(paths)) != len(paths):
        raise ReleaseArtifactError("archive members are duplicated or not canonical order")
    by_path = {member.path: member for member in members}
    for required in REQUIRED_DIRECTORIES:
        member = by_path.get(required)
        if member is None or member.kind != "directory":
            raise ReleaseArtifactError("release lacks required root directory")
    for member in members:
        parent = posixpath.dirname(member.path)
        if parent:
            parent_member = by_path.get(parent)
            if parent_member is None or parent_member.kind != "directory":
                raise ReleaseArtifactError("archive member parent is not a declared directory")
        if member.kind == "hardlink":
            target_member = by_path.get(member.link_target)
            if target_member is None or target_member.kind != "regular":
                raise ReleaseArtifactError("hardlink target is not a regular manifest member")
    total = sum(member.size for member in members if member.kind == "regular")
    if total > MAX_TOTAL_REGULAR_BYTES:
        raise ReleaseArtifactError("archive regular bytes exceed policy")


def normalized_root_digest(members: tuple[ArchiveMember, ...]) -> str:
    validate_members(members)
    return _digest([asdict(member) for member in members])


def _manifest_digest(manifest: ReleaseArtifactManifest) -> str:
    payload = asdict(manifest)
    payload.pop("manifest_digest")
    return _digest(payload)


def build_artifact_manifest(
    candidate: ReleaseCandidate, members: tuple[ArchiveMember, ...]
) -> ReleaseArtifactManifest:
    root_digest = normalized_root_digest(members)
    digest = candidate_digest(candidate)
    if candidate.artifact_member_count != len(members):
        raise ReleaseArtifactError("candidate member count disagrees with manifest")
    if candidate.normalized_root_digest != root_digest:
        raise ReleaseArtifactError("candidate normalized root digest disagrees with manifest")
    draft = ReleaseArtifactManifest(
        SCHEMA_VERSION,
        digest,
        candidate.artifact_sha256,
        len(members),
        sum(member.size for member in members if member.kind == "regular"),
        members,
        root_digest,
        "",
    )
    return replace(draft, manifest_digest=_manifest_digest(draft))


def validate_artifact_manifest(manifest: ReleaseArtifactManifest) -> None:
    if type(manifest) is not ReleaseArtifactManifest or manifest.schema_version != SCHEMA_VERSION:
        raise ReleaseArtifactError("artifact manifest schema is invalid")
    for value in (
        manifest.candidate_digest,
        manifest.artifact_sha256,
        manifest.normalized_root_digest,
        manifest.manifest_digest,
    ):
        if not isinstance(value, str) or not _SHA256.fullmatch(value):
            raise ReleaseArtifactError("artifact manifest digest is malformed")
    validate_members(manifest.members)
    if type(manifest.member_count) is not int or manifest.member_count != len(manifest.members):
        raise ReleaseArtifactError("artifact manifest member count disagrees")
    total = sum(member.size for member in manifest.members if member.kind == "regular")
    if type(manifest.total_regular_bytes) is not int or manifest.total_regular_bytes != total:
        raise ReleaseArtifactError("artifact manifest byte total disagrees")
    if manifest.normalized_root_digest != normalized_root_digest(manifest.members):
        raise ReleaseArtifactError("artifact normalized root digest disagrees")
    if manifest.manifest_digest != _manifest_digest(manifest):
        raise ReleaseArtifactError("artifact manifest digest disagrees")


def _reject_duplicate_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ReleaseArtifactError("artifact manifest JSON has duplicate fields")
        result[key] = value
    return result


def manifest_to_json(manifest: ReleaseArtifactManifest) -> str:
    validate_artifact_manifest(manifest)
    encoded = json.dumps(
        asdict(manifest), sort_keys=True, separators=(",", ":"), ensure_ascii=True
    )
    if len(encoded.encode("utf-8")) > MAX_SERIALIZED_BYTES:
        raise ReleaseArtifactError("serialized artifact manifest is oversized")
    return encoded + "\n"


def parse_artifact_manifest_json(text: str) -> ReleaseArtifactManifest:
    if not isinstance(text, str) or not text:
        raise ReleaseArtifactError("artifact manifest JSON is empty or not text")
    try:
        encoded = text.encode("utf-8")
    except UnicodeEncodeError as error:
        raise ReleaseArtifactError("artifact manifest JSON is not valid UTF-8") from error
    if len(encoded) > MAX_SERIALIZED_BYTES:
        raise ReleaseArtifactError("artifact manifest JSON is oversized")
    try:
        payload = json.loads(text, object_pairs_hook=_reject_duplicate_pairs)
    except json.JSONDecodeError as error:
        raise ReleaseArtifactError("artifact manifest JSON is invalid") from error
    expected = frozenset(ReleaseArtifactManifest.__dataclass_fields__)
    if not isinstance(payload, dict) or set(payload) != expected:
        raise ReleaseArtifactError("artifact manifest fields do not match schema")
    raw_members = payload.get("members")
    if not isinstance(raw_members, list):
        raise ReleaseArtifactError("artifact manifest members must be a list")
    member_fields = frozenset(ArchiveMember.__dataclass_fields__)
    parsed_members: list[ArchiveMember] = []
    for raw_member in raw_members:
        if not isinstance(raw_member, dict) or set(raw_member) != member_fields:
            raise ReleaseArtifactError("archive member fields do not match schema")
        try:
            parsed_members.append(ArchiveMember(**raw_member))
        except TypeError as error:
            raise ReleaseArtifactError("archive member values are malformed") from error
    try:
        manifest = ReleaseArtifactManifest(
            schema_version=payload["schema_version"],
            candidate_digest=payload["candidate_digest"],
            artifact_sha256=payload["artifact_sha256"],
            member_count=payload["member_count"],
            total_regular_bytes=payload["total_regular_bytes"],
            members=tuple(parsed_members),
            normalized_root_digest=payload["normalized_root_digest"],
            manifest_digest=payload["manifest_digest"],
        )
    except TypeError as error:
        raise ReleaseArtifactError("artifact manifest values are malformed") from error
    validate_artifact_manifest(manifest)
    return manifest


def compare_rebuilds(
    first: ReleaseArtifactManifest, second: ReleaseArtifactManifest
) -> ReproducibilityAssessment:
    validate_artifact_manifest(first)
    validate_artifact_manifest(second)
    issues: list[str] = []
    if first.members != second.members:
        issues.append("member-manifests-differ")
    if first.normalized_root_digest != second.normalized_root_digest:
        issues.append("normalized-root-digests-differ")
    if first.artifact_sha256 != second.artifact_sha256:
        issues.append("compressed-artifact-digests-differ")
    if first.member_count != second.member_count:
        issues.append("member-counts-differ")
    if first.total_regular_bytes != second.total_regular_bytes:
        issues.append("regular-byte-totals-differ")
    return ReproducibilityAssessment(
        "exact-match" if not issues else "mismatch",
        tuple(issues),
        first.manifest_digest,
        second.manifest_digest,
    )
