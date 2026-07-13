"""Pure definition and rebuild-evidence contract for the APX development package."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import hashlib
import json
import re


SCHEMA_VERSION = 1
PACKAGE_NAME = "apx-contracts-development"
ARCHITECTURE = "any"
LICENSE_ID = "Apache-2.0"
RUNTIME_DEPENDENCIES = ("python",)
FORBIDDEN_FEATURES = (
    "caller-selected-target",
    "credential-or-private-key",
    "device-or-special-file",
    "executable-command",
    "generated-bytecode-or-cache",
    "host-effect",
    "install-script-hook-or-service",
    "source-checkout-metadata",
)
MAX_PACKAGE_BYTES = 2 * 1024 * 1024
MAX_ENTRY_BYTES = 1024 * 1024

SOURCE_TARGETS = {
    "LICENSE": "usr/share/licenses/apx-contracts-development/LICENSE",
    "docs/bootstrap-development-package-v1.md": (
        "usr/share/doc/apx-contracts-development/bootstrap-development-package-v1.md"
    ),
    "docs/clean-install-dossier-schema-v1.md": (
        "usr/share/doc/apx-contracts-development/clean-install-dossier-schema-v1.md"
    ),
    "docs/release-artifact-manifest-v1.md": (
        "usr/share/doc/apx-contracts-development/release-artifact-manifest-v1.md"
    ),
    "docs/release-candidate-schema-v1.md": (
        "usr/share/doc/apx-contracts-development/release-candidate-schema-v1.md"
    ),
    "src/apx_clean_install_dossier.py": "usr/lib/apx/apx_clean_install_dossier.py",
    "src/apx_release_artifact.py": "usr/lib/apx/apx_release_artifact.py",
    "src/apx_release_candidate.py": "usr/lib/apx/apx_release_candidate.py",
}

_SHA256 = re.compile(r"[0-9a-f]{64}")
_REVISION = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})")
_VERSION = re.compile(r"[0-9][0-9A-Za-z._+]*")


class ContractsPackageError(ValueError):
    """A package definition or rebuild claim is outside the closed contract."""


@dataclass(frozen=True)
class PackageEntry:
    source_path: str
    target_path: str
    size: int
    mode: int
    sha256: str


@dataclass(frozen=True)
class ContractsPackageDefinition:
    schema_version: int
    package_name: str
    package_version: str
    package_release: int
    architecture: str
    license_id: str
    source_revision: str
    source_tree_sha256: str
    source_date_epoch: int
    runtime_dependencies: tuple[str, ...]
    forbidden_features: tuple[str, ...]
    entries: tuple[PackageEntry, ...]
    definition_digest: str


@dataclass(frozen=True)
class PackageBuildEvidence:
    schema_version: int
    definition_digest: str
    package_sha256: str
    package_size: int
    pkginfo_sha256: str
    mtree_sha256: str
    member_manifest_sha256: str
    classification: str


@dataclass(frozen=True)
class PackageRebuildAssessment:
    classification: str
    issues: tuple[str, ...]


def _digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    ).hexdigest()


def _definition_digest(definition: ContractsPackageDefinition) -> str:
    payload = asdict(definition)
    payload.pop("definition_digest")
    return _digest(payload)


def _validate_entry(entry: PackageEntry) -> None:
    if type(entry) is not PackageEntry:
        raise ContractsPackageError("package entry has wrong type")
    if SOURCE_TARGETS.get(entry.source_path) != entry.target_path:
        raise ContractsPackageError("package source-to-target mapping is not allowed")
    if type(entry.size) is not int or not 1 <= entry.size <= MAX_ENTRY_BYTES:
        raise ContractsPackageError("package entry size is outside policy")
    if type(entry.mode) is not int or entry.mode not in (0o644,):
        raise ContractsPackageError("package entry mode is not the fixed non-executable mode")
    if not isinstance(entry.sha256, str) or not _SHA256.fullmatch(entry.sha256):
        raise ContractsPackageError("package entry digest is malformed")


def validate_definition(definition: ContractsPackageDefinition) -> None:
    if type(definition) is not ContractsPackageDefinition:
        raise ContractsPackageError("package definition has wrong type")
    if type(definition.schema_version) is not int or definition.schema_version != SCHEMA_VERSION:
        raise ContractsPackageError("package definition schema is unsupported")
    if definition.package_name != PACKAGE_NAME or definition.architecture != ARCHITECTURE:
        raise ContractsPackageError("package identity is not the development contract")
    if definition.license_id != LICENSE_ID:
        raise ContractsPackageError("package license is not the repository license")
    if not isinstance(definition.package_version, str) or not _VERSION.fullmatch(
        definition.package_version
    ):
        raise ContractsPackageError("package version is invalid")
    if type(definition.package_release) is not int or not 1 <= definition.package_release <= 999:
        raise ContractsPackageError("package release is invalid")
    if not isinstance(definition.source_revision, str) or not _REVISION.fullmatch(
        definition.source_revision
    ):
        raise ContractsPackageError("source revision is invalid")
    if not isinstance(definition.source_tree_sha256, str) or not _SHA256.fullmatch(
        definition.source_tree_sha256
    ):
        raise ContractsPackageError("source tree digest is invalid")
    if type(definition.source_date_epoch) is not int or not 1_600_000_000 <= definition.source_date_epoch <= 4_102_444_800:
        raise ContractsPackageError("SOURCE_DATE_EPOCH is invalid")
    if definition.runtime_dependencies != RUNTIME_DEPENDENCIES:
        raise ContractsPackageError("runtime dependencies are not the closed set")
    if definition.forbidden_features != FORBIDDEN_FEATURES:
        raise ContractsPackageError("forbidden package features are not the closed set")
    if not isinstance(definition.entries, tuple):
        raise ContractsPackageError("package entries are not an immutable tuple")
    for entry in definition.entries:
        _validate_entry(entry)
    expected_sources = tuple(sorted(SOURCE_TARGETS, key=lambda path: SOURCE_TARGETS[path]))
    actual_sources = tuple(entry.source_path for entry in definition.entries)
    if actual_sources != expected_sources or len(set(actual_sources)) != len(actual_sources):
        raise ContractsPackageError("package entries are missing, duplicated, or not canonical")
    if sum(entry.size for entry in definition.entries) > MAX_PACKAGE_BYTES:
        raise ContractsPackageError("package entry bytes exceed policy")
    if not isinstance(definition.definition_digest, str) or not _SHA256.fullmatch(
        definition.definition_digest
    ):
        raise ContractsPackageError("package definition digest is malformed")
    if definition.definition_digest != _definition_digest(definition):
        raise ContractsPackageError("package definition digest disagrees")


def build_definition(
    *,
    package_version: str,
    source_revision: str,
    source_tree_sha256: str,
    source_date_epoch: int,
    entries: tuple[PackageEntry, ...],
) -> ContractsPackageDefinition:
    draft = ContractsPackageDefinition(
        SCHEMA_VERSION,
        PACKAGE_NAME,
        package_version,
        1,
        ARCHITECTURE,
        LICENSE_ID,
        source_revision,
        source_tree_sha256,
        source_date_epoch,
        RUNTIME_DEPENDENCIES,
        FORBIDDEN_FEATURES,
        entries,
        "",
    )
    result = replace(draft, definition_digest=_definition_digest(draft))
    validate_definition(result)
    return result


def validate_build_evidence(evidence: PackageBuildEvidence) -> None:
    if type(evidence) is not PackageBuildEvidence or evidence.schema_version != SCHEMA_VERSION:
        raise ContractsPackageError("package build evidence schema is invalid")
    for value in (
        evidence.definition_digest,
        evidence.package_sha256,
        evidence.pkginfo_sha256,
        evidence.mtree_sha256,
        evidence.member_manifest_sha256,
    ):
        if not isinstance(value, str) or not _SHA256.fullmatch(value):
            raise ContractsPackageError("package build evidence digest is malformed")
    if type(evidence.package_size) is not int or not 1 <= evidence.package_size <= MAX_PACKAGE_BYTES:
        raise ContractsPackageError("package build size is outside policy")
    if evidence.classification != "unsigned-development-only":
        raise ContractsPackageError("package build classification is unsafe")


def compare_rebuilds(
    definition: ContractsPackageDefinition,
    first: PackageBuildEvidence,
    second: PackageBuildEvidence,
) -> PackageRebuildAssessment:
    validate_definition(definition)
    validate_build_evidence(first)
    validate_build_evidence(second)
    issues = []
    if first.definition_digest != definition.definition_digest or second.definition_digest != definition.definition_digest:
        issues.append("definition-identity-mismatch")
    for field in (
        "package_sha256",
        "package_size",
        "pkginfo_sha256",
        "mtree_sha256",
        "member_manifest_sha256",
    ):
        if getattr(first, field) != getattr(second, field):
            issues.append(f"rebuild-{field}-mismatch")
    return PackageRebuildAssessment("exact-match" if not issues else "mismatch", tuple(issues))
