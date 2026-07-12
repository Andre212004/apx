"""Read-only readiness model for the APX system-container experiment."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date
import hashlib
import json
import os
from pathlib import Path
import re
import stat
from typing import Callable, Sequence


EXPERIMENT_LOGICAL_NAME = "isolation-trial"
EXPERIMENT_ACCOUNT = "apx-isolation-trial"
EXPERIMENT_HOME = "/home/apx-isolation-trial"
COMMAND_TIMEOUT = 3.0


@dataclass(frozen=True)
class IsolationReadinessCheck:
    section: str
    name: str
    classification: str
    evidence: str


@dataclass(frozen=True)
class IsolationReadinessReport:
    experiment: str
    checks: tuple[IsolationReadinessCheck, ...]
    overall: str
    next_stage: str


@dataclass(frozen=True)
class IsolationExperimentPlan:
    schema_version: int
    policy_version: str
    experiment: str
    logical_name: str
    account_name: str
    home_path: str
    profile: str
    steps: tuple[str, ...]
    approval: str
    digest: str


@dataclass(frozen=True)
class SnapshotPackage:
    name: str
    version: str
    architecture: str
    filename: str
    sha256: str
    signature_verified: bool
    signer_fingerprint: str | None


@dataclass(frozen=True)
class BaseSnapshotManifest:
    schema_version: int
    snapshot_id: str
    source_kind: str
    source_uri: str
    snapshot_date: str
    database_sha256: tuple[tuple[str, str], ...]
    seed_packages: tuple[str, ...]
    packages: tuple[SnapshotPackage, ...]
    resolved_manifest_sha256: str
    acquisition_plan_digest: str
    keyring_artifact: str
    keyring_sha256: str
    trust_bootstrap_digest: str
    verification_tool: str
    independent_validation_completed: bool
    independent_validation_digest: str


@dataclass(frozen=True)
class SnapshotAssessment:
    classification: str
    issues: tuple[str, ...]
    digest: str


@dataclass(frozen=True)
class SnapshotTrustReadinessReport:
    checks: tuple[IsolationReadinessCheck, ...]
    overall: str
    next_stage: str


@dataclass(frozen=True)
class SnapshotAcquisitionPlan:
    schema_version: int
    policy_version: str
    snapshot_id: str
    snapshot_date: str
    source_uri: str
    repositories: tuple[str, ...]
    architectures: tuple[str, ...]
    seed_packages: tuple[str, ...]
    trust_bootstrap: str
    trust_bootstrap_digest: str
    host_keyring_package: str
    host_keyring_files: tuple[tuple[str, str], ...]
    keyring_artifact: str
    keyring_artifact_sha256: str
    keyring_signature_sha256: str
    keyring_signer_fingerprint: str
    keyring_signer_export_sha256: str
    keyring_metadata: tuple[tuple[str, str], ...]
    resolver_tool: str
    verification_tool: str
    independent_validation_tool: str
    staging_path: str
    evidence_path: str
    limits: tuple[tuple[str, str], ...]
    phases: tuple[str, ...]
    blockers: tuple[str, ...]
    approval: str
    digest: str


@dataclass(frozen=True)
class Stage2Resource:
    resource_type: str
    resource_id: str
    intended_path: str
    owner: str
    quota: str
    identity_evidence: tuple[str, ...]
    initial_state: str
    publication_state: str


@dataclass(frozen=True)
class Stage2ApprovalDossier:
    schema_version: int
    policy_version: str
    experiment: str
    acquisition_plan_digest: str
    resources: tuple[Stage2Resource, ...]
    downloads: tuple[str, ...]
    host_effects: tuple[str, ...]
    preconditions: tuple[str, ...]
    postconditions: tuple[str, ...]
    failure_states: tuple[str, ...]
    risks: tuple[str, ...]
    rollback_rules: tuple[str, ...]
    destructive_operations: tuple[str, ...]
    blockers: tuple[str, ...]
    approval: str
    digest: str


EXPERIMENT_STEPS = (
    "Reconfirm the fixed identity, registration, marker, machine, image, and storage preconditions.",
    "Verify the exact Arch source and immutable APX base manifest before any creation.",
    "Reserve a root-owned incomplete-operation record for this exact experiment.",
    "Create experiment-owned Btrfs root and home storage with recorded identities.",
    "Populate the minimal headless Arch base without Hub state, secrets, desktop, GPU, Odysseus, or Codex.",
    "Configure private identity, process, IPC, mount, and network boundaries from the fixed policy.",
    "Boot the headless container with no host home, GPU, audio, input, secrets, or arbitrary binds.",
    "Verify independent packages, namespaces, limits, network, storage, and cross-Environment denials.",
    "Shut down and verify that no process, mount, network interface, or runtime state survives.",
    "Preserve evidence and require separate approval before cleanup or any graphical stage.",
)

BASE_PACKAGES = (
    "base",
    "ca-certificates",
    "dbus-broker",
    "iproute2",
    "iputils",
    "sudo",
)

RESOURCE_POLICY = (
    ("virtual_cpus", "2"),
    ("memory_high", "2GiB"),
    ("memory_max", "3GiB"),
    ("tasks_max", "512"),
    ("root_budget", "8GiB"),
    ("home_budget", "2GiB"),
)

SNAPSHOT_ACQUISITION_LIMITS = (
    ("repository_database_max_each", "64MiB"),
    ("package_max_each", "1GiB"),
    ("aggregate_download_max", "4GiB"),
    ("resolved_package_max_count", "512"),
    ("connect_timeout", "15s"),
    ("transfer_timeout_each", "300s"),
    ("retry_max", "2"),
)

SNAPSHOT_ACQUISITION_PHASES = (
    "Verify fixed policy, approval binding, path absence, capacity, and trust-input selection.",
    "Create operation-owned staging and incomplete marker before the first download.",
    "Fetch dated core and extra databases without leaving the fixed archive origin.",
    "Resolve the closed dependency set using only staged databases.",
    "Fetch exactly the resolved packages and detached signatures within fixed limits.",
    "Verify hashes, signatures, signer identities, and package metadata without extraction.",
    "Repeat verification independently from reopened staged regular files.",
    "Atomically publish evidence only; preserve the Stage 2 execution block.",
)

STAGE2_PRECONDITIONS = (
    "snapshot evidence assessment is verified and matches the approved acquisition digest",
    "fixed account, home, machine, image, registration, marker, and storage identities are absent",
    "Btrfs quota support and required free capacity are authoritatively confirmed",
    "subordinate UID and GID ranges are valid, non-overlapping, and bound to apx-development",
    "all intended paths are absent and every parent identity matches policy without symlink traversal",
    "Stage 2 approval binds this exact dossier digest and has not expired or been reused",
)

STAGE2_POSTCONDITIONS = (
    "base, root, and home identities are freshly observed and mutually distinct",
    "base is immutable through the Environment and root/home quotas are enforced",
    "account and namespace ownership match the recorded allocation and private-group policy",
    "host package database, lock, package list, keyring, cache, and files are unchanged",
    "no Hub, Development, host-home, secret, GPU, audio, input, or arbitrary device is exposed",
    "registration is atomically published only after every preceding verification succeeds",
    "final verification includes published registration and the incomplete marker is then absent",
)

STAGE2_FAILURE_STATES = (
    "no-effect: no Stage 2 resource was created",
    "owned-empty: operation-owned unpublished resources exist and fresh evidence proves no use or modification",
    "owned-modified: operation-owned resources exist but package population or metadata mutation occurred",
    "published-incomplete: registration was published but a final postcondition failed",
    "ownership-uncertain: provenance, identity, use, or modification evidence is unavailable or ambiguous",
)

STAGE2_ROLLBACK_RULES = (
    "pathname, name, owner, or registration alone never proves operation ownership",
    "automatic rollback is limited to freshly proven operation-created, unpublished, unused, unmodified resources",
    "package population, first boot, login, user data, external modification, or publication ends automatic deletion eligibility",
    "uncertain or published resources are preserved and reported as incomplete for separately approved recovery",
    "cleanup requires fresh stopped-state, process, mount, namespace, network, and identity verification",
)

SNAPSHOT_TRUST_FILES = (
    "/usr/share/pacman/keyrings/archlinux.gpg",
    "/usr/share/pacman/keyrings/archlinux-trusted",
    "/usr/share/pacman/keyrings/archlinux-revoked",
)

OBSERVED_HOST_KEYRING_FILES = (
    ("archlinux.gpg", "4f9f55c7702ff580f808a86e4eeed7d471252684c03089427c69796e88253516"),
    ("archlinux-revoked", "aafbc33d6be7e200dd6226dbb467623a38a00db431826258bccfaf5cebfef6a1"),
    ("archlinux-trusted", "384c7daf07a89ec6610859142b009ca5c0b3062ed3ab2d3c50629fef9d002e8f"),
)

VERIFIED_KEYRING_METADATA = (
    ("pkgname", "archlinux-keyring"),
    ("pkgver", "20260707.1-1"),
    ("arch", "any"),
    ("packager", "Christian Hesse <eworm@archlinux.org>"),
)


def compute_trust_bootstrap_digest(
    package_identity: str, files: Sequence[tuple[str, str]]
) -> str:
    payload = {"package_identity": package_identity, "files": list(files)}
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()

_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_FINGERPRINT_PATTERN = re.compile(r"^[0-9A-F]{40}(?:[0-9A-F]{24})?$")
_SNAPSHOT_ID_PATTERN = re.compile(r"^apx-base-[0-9]{4}\.[0-9]{2}\.[0-9]{2}-v[1-9][0-9]*$")
_SNAPSHOT_DATE_PATTERN = re.compile(r"^[0-9]{4}/[0-9]{2}/[0-9]{2}$")
_PACKAGE_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9@._+-]*$")
SNAPSHOT_MANIFEST_MAX_BYTES = 2 * 1024 * 1024
SNAPSHOT_PACKAGE_MAX_COUNT = 2048
_MANIFEST_FIELDS = {
    "schema_version",
    "snapshot_id",
    "source_kind",
    "source_uri",
    "snapshot_date",
    "database_sha256",
    "seed_packages",
    "packages",
    "resolved_manifest_sha256",
    "acquisition_plan_digest",
    "keyring_artifact",
    "keyring_sha256",
    "trust_bootstrap_digest",
    "verification_tool",
    "independent_validation_completed",
    "independent_validation_digest",
}
_PACKAGE_FIELDS = {
    "name",
    "version",
    "architecture",
    "filename",
    "sha256",
    "signature_verified",
    "signer_fingerprint",
}


def _reject_duplicate_json_fields(pairs: Sequence[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON field: {key}")
        result[key] = value
    return result


def _snapshot_package_payload(package: SnapshotPackage) -> dict[str, object]:
    return {
        "architecture": package.architecture,
        "filename": package.filename,
        "name": package.name,
        "sha256": package.sha256,
        "signature_verified": package.signature_verified,
        "signer_fingerprint": package.signer_fingerprint,
        "version": package.version,
    }


def compute_resolved_manifest_sha256(packages: Sequence[SnapshotPackage]) -> str:
    """Digest canonical package evidence without reading files or invoking tools."""
    payload = [
        _snapshot_package_payload(package)
        for package in sorted(packages, key=lambda item: item.name)
    ]
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def compute_independent_validation_digest(
    *,
    resolved_manifest_sha256: str,
    acquisition_plan_digest: str,
    keyring_artifact: str,
    keyring_sha256: str,
    trust_bootstrap_digest: str,
    verification_tool: str,
) -> str:
    subject = {
        "acquisition_plan_digest": acquisition_plan_digest,
        "keyring_artifact": keyring_artifact,
        "keyring_sha256": keyring_sha256,
        "resolved_manifest_sha256": resolved_manifest_sha256,
        "trust_bootstrap_digest": trust_bootstrap_digest,
        "verification_tool": verification_tool,
    }
    return hashlib.sha256(
        json.dumps(subject, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def serialize_base_snapshot_manifest(manifest: BaseSnapshotManifest) -> str:
    payload = {
        "acquisition_plan_digest": manifest.acquisition_plan_digest,
        "database_sha256": [list(item) for item in manifest.database_sha256],
        "independent_validation_completed": manifest.independent_validation_completed,
        "independent_validation_digest": manifest.independent_validation_digest,
        "keyring_artifact": manifest.keyring_artifact,
        "keyring_sha256": manifest.keyring_sha256,
        "packages": [_snapshot_package_payload(item) for item in manifest.packages],
        "resolved_manifest_sha256": manifest.resolved_manifest_sha256,
        "schema_version": manifest.schema_version,
        "seed_packages": list(manifest.seed_packages),
        "snapshot_date": manifest.snapshot_date,
        "snapshot_id": manifest.snapshot_id,
        "source_kind": manifest.source_kind,
        "source_uri": manifest.source_uri,
        "trust_bootstrap_digest": manifest.trust_bootstrap_digest,
        "verification_tool": manifest.verification_tool,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n"


def parse_base_snapshot_manifest(text: str) -> BaseSnapshotManifest:
    """Parse bounded canonical evidence without accepting schema extensions."""
    if not isinstance(text, str):
        raise ValueError("snapshot manifest must be text")
    try:
        encoded_size = len(text.encode("utf-8"))
    except UnicodeEncodeError as error:
        raise ValueError("snapshot manifest is not valid UTF-8 text") from error
    if encoded_size > SNAPSHOT_MANIFEST_MAX_BYTES:
        raise ValueError("snapshot manifest exceeds size limit")
    try:
        payload = json.loads(text, object_pairs_hook=_reject_duplicate_json_fields)
    except (json.JSONDecodeError, UnicodeError) as error:
        raise ValueError("snapshot manifest is not valid JSON") from error
    if not isinstance(payload, dict) or set(payload) != _MANIFEST_FIELDS:
        raise ValueError("snapshot manifest fields do not match schema")

    scalar_types = {
        "schema_version": int,
        "snapshot_id": str,
        "source_kind": str,
        "source_uri": str,
        "snapshot_date": str,
        "resolved_manifest_sha256": str,
        "acquisition_plan_digest": str,
        "keyring_artifact": str,
        "keyring_sha256": str,
        "trust_bootstrap_digest": str,
        "verification_tool": str,
        "independent_validation_digest": str,
    }
    for field, expected_type in scalar_types.items():
        value = payload[field]
        if type(value) is not expected_type:
            raise ValueError(f"snapshot manifest field {field} has wrong type")
    if type(payload["independent_validation_completed"]) is not bool:
        raise ValueError("independent validation result has wrong type")

    database_value = payload["database_sha256"]
    if not isinstance(database_value, list):
        raise ValueError("database evidence must be a list")
    databases: list[tuple[str, str]] = []
    for item in database_value:
        if (
            not isinstance(item, list)
            or len(item) != 2
            or any(type(value) is not str for value in item)
        ):
            raise ValueError("database evidence entry is malformed")
        databases.append((item[0], item[1]))

    seeds_value = payload["seed_packages"]
    if not isinstance(seeds_value, list) or any(
        type(value) is not str for value in seeds_value
    ):
        raise ValueError("seed package evidence is malformed")

    packages_value = payload["packages"]
    if not isinstance(packages_value, list):
        raise ValueError("package evidence must be a list")
    if len(packages_value) > SNAPSHOT_PACKAGE_MAX_COUNT:
        raise ValueError("package evidence exceeds count limit")
    packages: list[SnapshotPackage] = []
    for item in packages_value:
        if not isinstance(item, dict) or set(item) != _PACKAGE_FIELDS:
            raise ValueError("package evidence fields do not match schema")
        for field in _PACKAGE_FIELDS - {"signature_verified", "signer_fingerprint"}:
            if type(item[field]) is not str:
                raise ValueError(f"package field {field} has wrong type")
        if type(item["signature_verified"]) is not bool:
            raise ValueError("package signature result has wrong type")
        if item["signer_fingerprint"] is not None and type(item["signer_fingerprint"]) is not str:
            raise ValueError("package signer fingerprint has wrong type")
        packages.append(SnapshotPackage(**item))

    return BaseSnapshotManifest(
        schema_version=payload["schema_version"],
        snapshot_id=payload["snapshot_id"],
        source_kind=payload["source_kind"],
        source_uri=payload["source_uri"],
        snapshot_date=payload["snapshot_date"],
        database_sha256=tuple(databases),
        seed_packages=tuple(seeds_value),
        packages=tuple(packages),
        resolved_manifest_sha256=payload["resolved_manifest_sha256"],
        acquisition_plan_digest=payload["acquisition_plan_digest"],
        keyring_artifact=payload["keyring_artifact"],
        keyring_sha256=payload["keyring_sha256"],
        trust_bootstrap_digest=payload["trust_bootstrap_digest"],
        verification_tool=payload["verification_tool"],
        independent_validation_completed=payload["independent_validation_completed"],
        independent_validation_digest=payload["independent_validation_digest"],
    )


def assess_base_snapshot(manifest: BaseSnapshotManifest) -> SnapshotAssessment:
    """Validate a closed snapshot manifest; never fetch or trust moving sources."""
    structural: list[str] = []
    verification: list[str] = []

    if manifest.schema_version != 1:
        structural.append("unsupported snapshot schema")
    if not _SNAPSHOT_ID_PATTERN.fullmatch(manifest.snapshot_id):
        structural.append("snapshot identity is not canonical")
    if manifest.source_kind != "arch-linux-archive":
        structural.append("source is not an immutable Arch Linux Archive snapshot")
    if not _SNAPSHOT_DATE_PATTERN.fullmatch(manifest.snapshot_date):
        structural.append("snapshot date is not canonical")
    else:
        try:
            date.fromisoformat(manifest.snapshot_date.replace("/", "-"))
        except ValueError:
            structural.append("snapshot date is not a real calendar date")
    expected_id_prefix = f"apx-base-{manifest.snapshot_date.replace('/', '.')}-v"
    if not manifest.snapshot_id.startswith(expected_id_prefix):
        structural.append("snapshot identity date does not match source date")
    expected_uri = (
        f"https://archive.archlinux.org/repos/{manifest.snapshot_date}/"
        "$repo/os/$arch"
    )
    if manifest.source_uri != expected_uri:
        structural.append("source URI does not match the declared archive date")

    databases = dict(manifest.database_sha256)
    if len(databases) != len(manifest.database_sha256):
        structural.append("repository database names are duplicated")
    if manifest.database_sha256 != tuple(sorted(manifest.database_sha256)):
        structural.append("repository database evidence is not canonically ordered")
    if set(databases) != {"core", "extra"}:
        structural.append("repository database set must be exactly core and extra")
    if any(not _SHA256_PATTERN.fullmatch(digest) for digest in databases.values()):
        structural.append("repository database digest is malformed")

    if manifest.seed_packages != BASE_PACKAGES:
        structural.append("seed package policy does not match the fixed base")

    if not _SHA256_PATTERN.fullmatch(manifest.acquisition_plan_digest):
        structural.append("acquisition plan digest is malformed")
    if (
        not manifest.keyring_artifact
        or manifest.keyring_artifact != Path(manifest.keyring_artifact).name
        or not manifest.keyring_artifact.startswith("archlinux-keyring-")
        or not manifest.keyring_artifact.endswith(".pkg.tar.zst")
    ):
        structural.append("keyring artifact identity is unsafe or unsupported")
    if not _SHA256_PATTERN.fullmatch(manifest.keyring_sha256):
        structural.append("keyring artifact digest is malformed")
    if not _SHA256_PATTERN.fullmatch(manifest.trust_bootstrap_digest):
        structural.append("trust bootstrap digest is malformed")
    if (
        not manifest.verification_tool
        or len(manifest.verification_tool) > 128
        or any(not character.isprintable() for character in manifest.verification_tool)
    ):
        structural.append("verification tool identity is malformed")
    if not isinstance(manifest.independent_validation_completed, bool):
        structural.append("independent validation result is not boolean")
    elif not manifest.independent_validation_completed:
        verification.append("independent validation is not complete")

    names = [package.name for package in manifest.packages]
    if not names:
        structural.append("resolved package set is empty")
    if len(set(names)) != len(names):
        structural.append("resolved package names are duplicated")
    if names != sorted(names):
        structural.append("resolved package set is not canonically ordered")
    missing_seeds = sorted(set(BASE_PACKAGES) - set(names))
    if missing_seeds:
        structural.append("resolved package set omits fixed seed packages")

    for package in manifest.packages:
        label = package.name or "<unnamed>"
        if not _PACKAGE_NAME_PATTERN.fullmatch(package.name):
            structural.append(f"package {label} has an invalid name")
        if not package.version or any(character.isspace() for character in package.version):
            structural.append(f"package {label} has an invalid version")
        if package.architecture not in {"any", "x86_64"}:
            structural.append(f"package {label} has an unsupported architecture")
        if (
            not package.filename
            or package.filename != Path(package.filename).name
            or not package.filename.endswith(".pkg.tar.zst")
        ):
            structural.append(f"package {label} has an unsafe filename")
        if not _SHA256_PATTERN.fullmatch(package.sha256):
            structural.append(f"package {label} has a malformed digest")
        if not isinstance(package.signature_verified, bool):
            structural.append(f"package {label} signature result is not boolean")
        elif not package.signature_verified:
            verification.append(f"package {label} signature is not verified")
        if package.signer_fingerprint is None:
            verification.append(f"package {label} signer is not recorded")
        elif not _FINGERPRINT_PATTERN.fullmatch(package.signer_fingerprint):
            structural.append(f"package {label} signer fingerprint is malformed")

    computed_manifest_digest = compute_resolved_manifest_sha256(manifest.packages)
    if not _SHA256_PATTERN.fullmatch(manifest.resolved_manifest_sha256):
        structural.append("resolved manifest digest is malformed")
    elif manifest.resolved_manifest_sha256 != computed_manifest_digest:
        structural.append("resolved manifest digest does not match package evidence")

    expected_validation_digest = compute_independent_validation_digest(
        resolved_manifest_sha256=manifest.resolved_manifest_sha256,
        acquisition_plan_digest=manifest.acquisition_plan_digest,
        keyring_artifact=manifest.keyring_artifact,
        keyring_sha256=manifest.keyring_sha256,
        trust_bootstrap_digest=manifest.trust_bootstrap_digest,
        verification_tool=manifest.verification_tool,
    )
    if not _SHA256_PATTERN.fullmatch(manifest.independent_validation_digest):
        structural.append("independent validation digest is malformed")
    elif manifest.independent_validation_digest != expected_validation_digest:
        structural.append("independent validation digest does not match provenance")

    canonical = {
        "acquisition_plan_digest": manifest.acquisition_plan_digest,
        "database_sha256": list(manifest.database_sha256),
        "independent_validation_completed": manifest.independent_validation_completed,
        "independent_validation_digest": manifest.independent_validation_digest,
        "keyring_artifact": manifest.keyring_artifact,
        "keyring_sha256": manifest.keyring_sha256,
        "packages": [_snapshot_package_payload(item) for item in manifest.packages],
        "resolved_manifest_sha256": manifest.resolved_manifest_sha256,
        "schema_version": manifest.schema_version,
        "seed_packages": list(manifest.seed_packages),
        "snapshot_date": manifest.snapshot_date,
        "snapshot_id": manifest.snapshot_id,
        "source_kind": manifest.source_kind,
        "source_uri": manifest.source_uri,
        "trust_bootstrap_digest": manifest.trust_bootstrap_digest,
        "verification_tool": manifest.verification_tool,
    }
    digest = hashlib.sha256(
        json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    issues = tuple(structural + verification)
    classification = (
        "rejected" if structural else "verification-incomplete" if verification else "verified"
    )
    return SnapshotAssessment(classification, issues, digest)


def render_snapshot_assessment(
    manifest: BaseSnapshotManifest, assessment: SnapshotAssessment
) -> str:
    lines = [
        "APX base snapshot assessment",
        "Mode: repository evidence only; no downloads or host changes",
        f"Snapshot: {manifest.snapshot_id}",
        f"Source: {manifest.source_uri}",
        f"Resolved packages: {len(manifest.packages)}",
        f"Classification: {assessment.classification}",
        f"Evidence digest: {assessment.digest}",
        "Issues:",
    ]
    lines.extend(f"- {issue}" for issue in assessment.issues)
    if not assessment.issues:
        lines.append("- none")
    lines.append("Stage 2 remains blocked pending explicit approval.")
    return "\n".join(lines)


def build_snapshot_acquisition_plan() -> SnapshotAcquisitionPlan:
    """Build the fixed, blocked acquisition plan without network or filesystem IO."""
    host_keyring_package = "archlinux-keyring 20260707.1-1"
    trust_bootstrap_digest = compute_trust_bootstrap_digest(
        host_keyring_package, OBSERVED_HOST_KEYRING_FILES
    )
    payload = {
        "schema_version": 1,
        "policy_version": "base-snapshot-acquisition-v1",
        "snapshot_id": "apx-base-2026.07.11-v1",
        "snapshot_date": "2026/07/11",
        "source_uri": "https://archive.archlinux.org/repos/2026/07/11/$repo/os/$arch",
        "repositories": ["core", "extra"],
        "architectures": ["any", "x86_64"],
        "seed_packages": list(BASE_PACKAGES),
        "trust_bootstrap": "trusted-host-installed-archlinux-keyring-explicitly-observed-and-frozen",
        "trust_bootstrap_digest": trust_bootstrap_digest,
        "host_keyring_package": host_keyring_package,
        "host_keyring_files": list(OBSERVED_HOST_KEYRING_FILES),
        "keyring_artifact": "archlinux-keyring-20260707.1-1-any.pkg.tar.zst",
        "keyring_artifact_sha256": "b47fc9c8066377e73d72bdb6a166bbbd829d5dcc745e424ef32436bd673cbc0d",
        "keyring_signature_sha256": "100aea3aa09b14e818e84ff26ffcaed5c340e638942bc8949c2bfba7a19ee091",
        "keyring_signer_fingerprint": "0429897DE5F3BDAC537A30696D42BDD116E0068F",
        "keyring_signer_export_sha256": "0fcc071d58801d83e29a68f0ac0008c142f675cdfd8d8b7a27362ac1ec578470",
        "keyring_metadata": list(VERIFIED_KEYRING_METADATA),
        "resolver_tool": "pacman-7.1.0.r9.g54d9411-2-sync-print-downloadonly-fixed-paths",
        "verification_tool": "pacman-key-7.1.0-verify-operation-owned-gpgdir",
        "independent_validation_tool": "gnupg-2.4.9-1-export-trusted-signer-then-gpgv-second-pass",
        "staging_path": "/var/lib/apx/staging/base-snapshot-2026.07.11-v1",
        "evidence_path": "/var/lib/apx/evidence/base-snapshot-2026.07.11-v1.json",
        "limits": list(SNAPSHOT_ACQUISITION_LIMITS),
        "phases": list(SNAPSHOT_ACQUISITION_PHASES),
        "blockers": [
            "trusted-host observation lacks future executor attestation and replay-resistant approval binding",
            "real resolved package manifest and signatures have not been acquired",
            "staging capacity, parent identities, and cleanup approval are not authoritatively confirmed",
            "network acquisition has no explicit bounded approval",
        ],
        "approval": "blocked-plan-only",
    }
    plan = SnapshotAcquisitionPlan(
        schema_version=payload["schema_version"],
        policy_version=payload["policy_version"],
        snapshot_id=payload["snapshot_id"],
        snapshot_date=payload["snapshot_date"],
        source_uri=payload["source_uri"],
        repositories=tuple(payload["repositories"]),
        architectures=tuple(payload["architectures"]),
        seed_packages=BASE_PACKAGES,
        trust_bootstrap=payload["trust_bootstrap"],
        trust_bootstrap_digest=payload["trust_bootstrap_digest"],
        host_keyring_package=payload["host_keyring_package"],
        host_keyring_files=OBSERVED_HOST_KEYRING_FILES,
        keyring_artifact=payload["keyring_artifact"],
        keyring_artifact_sha256=payload["keyring_artifact_sha256"],
        keyring_signature_sha256=payload["keyring_signature_sha256"],
        keyring_signer_fingerprint=payload["keyring_signer_fingerprint"],
        keyring_signer_export_sha256=payload["keyring_signer_export_sha256"],
        keyring_metadata=VERIFIED_KEYRING_METADATA,
        resolver_tool=payload["resolver_tool"],
        verification_tool=payload["verification_tool"],
        independent_validation_tool=payload["independent_validation_tool"],
        staging_path=payload["staging_path"],
        evidence_path=payload["evidence_path"],
        limits=SNAPSHOT_ACQUISITION_LIMITS,
        phases=SNAPSHOT_ACQUISITION_PHASES,
        blockers=tuple(payload["blockers"]),
        approval=payload["approval"],
        digest="",
    )
    return replace(plan, digest=compute_snapshot_acquisition_plan_digest(plan))


def compute_snapshot_acquisition_plan_digest(plan: SnapshotAcquisitionPlan) -> str:
    payload = {
        "schema_version": plan.schema_version,
        "policy_version": plan.policy_version,
        "snapshot_id": plan.snapshot_id,
        "snapshot_date": plan.snapshot_date,
        "source_uri": plan.source_uri,
        "repositories": list(plan.repositories),
        "architectures": list(plan.architectures),
        "seed_packages": list(plan.seed_packages),
        "trust_bootstrap": plan.trust_bootstrap,
        "trust_bootstrap_digest": plan.trust_bootstrap_digest,
        "host_keyring_package": plan.host_keyring_package,
        "host_keyring_files": list(plan.host_keyring_files),
        "keyring_artifact": plan.keyring_artifact,
        "keyring_artifact_sha256": plan.keyring_artifact_sha256,
        "keyring_signature_sha256": plan.keyring_signature_sha256,
        "keyring_signer_fingerprint": plan.keyring_signer_fingerprint,
        "keyring_signer_export_sha256": plan.keyring_signer_export_sha256,
        "keyring_metadata": list(plan.keyring_metadata),
        "resolver_tool": plan.resolver_tool,
        "verification_tool": plan.verification_tool,
        "independent_validation_tool": plan.independent_validation_tool,
        "staging_path": plan.staging_path,
        "evidence_path": plan.evidence_path,
        "limits": list(plan.limits),
        "phases": list(plan.phases),
        "blockers": list(plan.blockers),
        "approval": plan.approval,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def render_snapshot_acquisition_plan(plan: SnapshotAcquisitionPlan) -> str:
    lines = [
        "APX base snapshot acquisition plan",
        "Mode: plan only; no network, downloads, filesystem writes, or host changes",
        f"Policy: {plan.policy_version}",
        f"Candidate: {plan.snapshot_id}",
        f"Archive date: {plan.snapshot_date}",
        f"Source: {plan.source_uri}",
        f"Repositories: {', '.join(plan.repositories)}",
        f"Architectures: {', '.join(plan.architectures)}",
        f"Seeds: {', '.join(plan.seed_packages)}",
        f"Keyring artifact: {plan.keyring_artifact}",
        f"Keyring artifact SHA-256: {plan.keyring_artifact_sha256}",
        f"Keyring signature SHA-256: {plan.keyring_signature_sha256}",
        f"Keyring signer: {plan.keyring_signer_fingerprint}",
        f"Exported signer key SHA-256: {plan.keyring_signer_export_sha256}",
        "Verified keyring metadata:",
    ]
    lines.extend(f"- {name}: {value}" for name, value in plan.keyring_metadata)
    lines.extend([
        f"Trust bootstrap: {plan.trust_bootstrap}",
        f"Trust bootstrap digest: {plan.trust_bootstrap_digest}",
        f"Observed host keyring package: {plan.host_keyring_package}",
        "Observed host keyring files:",
    ])
    lines.extend(f"- {name}: {digest}" for name, digest in plan.host_keyring_files)
    lines.extend([
        f"Resolver/acquirer: {plan.resolver_tool}",
        f"Primary verifier: {plan.verification_tool}",
        f"Independent verifier: {plan.independent_validation_tool}",
        f"Future staging: {plan.staging_path}",
        f"Future evidence: {plan.evidence_path}",
        "Limits:",
    ])
    lines.extend(f"- {name}: {value}" for name, value in plan.limits)
    lines.append("Ordered phases:")
    lines.extend(f"{index}. {phase}" for index, phase in enumerate(plan.phases, 1))
    lines.append("Blockers:")
    lines.extend(f"- {blocker}" for blocker in plan.blockers)
    lines.extend((f"Approval: {plan.approval}", f"Plan digest: {plan.digest}"))
    return "\n".join(lines)


def _stage2_resources() -> tuple[Stage2Resource, ...]:
    return (
        Stage2Resource(
            "immutable-base",
            "apx-base-2026.07.11-v1",
            "/var/lib/apx/bases/apx-base-2026.07.11-v1/root",
            "root:root",
            "read-only-after-verification",
            ("Btrfs UUID", "subvolume ID", "parent UUID", "verified snapshot evidence digest"),
            "must-be-absent",
            "shared-base-unpublished",
        ),
        Stage2Resource(
            "environment-root",
            "isolation-trial-root",
            "/var/lib/apx/environments/isolation-trial/root",
            "mapped-container-root",
            "8GiB",
            ("Btrfs UUID", "subvolume ID", "parent UUID", "operation provenance"),
            "must-be-absent",
            "experiment-unpublished",
        ),
        Stage2Resource(
            "environment-home",
            "isolation-trial-home",
            EXPERIMENT_HOME,
            f"{EXPERIMENT_ACCOUNT}:private-group",
            "2GiB",
            ("Btrfs UUID", "subvolume ID", "parent UUID", "UID/GID mapping", "operation provenance"),
            "must-be-absent",
            "experiment-unpublished",
        ),
        Stage2Resource(
            "incomplete-operation",
            "isolation-trial-operation",
            "/var/lib/apx/operations/isolation-trial.json",
            "root:root",
            "bounded-json-record",
            ("regular-file identity", "owner/group/mode", "operation ID", "plan digest"),
            "must-be-absent",
            "published-before-first-mutation",
        ),
        Stage2Resource(
            "registration",
            "isolation-trial-registration",
            "/var/lib/apx/environments/isolation-trial.json",
            "root:root",
            "bounded-canonical-json",
            ("regular-file identity", "owner/group/mode", "canonical content", "storage UUID bindings"),
            "must-be-absent",
            "publish-only-after-postconditions",
        ),
    )


def build_stage2_approval_dossier() -> Stage2ApprovalDossier:
    acquisition = build_snapshot_acquisition_plan()
    resources = _stage2_resources()
    payload = {
        "schema_version": 1,
        "policy_version": "system-container-stage2-dossier-v1",
        "experiment": "system-container-v1",
        "acquisition_plan_digest": acquisition.digest,
        "resources": [
            {
                "resource_type": item.resource_type,
                "resource_id": item.resource_id,
                "intended_path": item.intended_path,
                "owner": item.owner,
                "quota": item.quota,
                "identity_evidence": list(item.identity_evidence),
                "initial_state": item.initial_state,
                "publication_state": item.publication_state,
            }
            for item in resources
        ],
        "downloads": [
            "dated core and extra repository databases",
            "exact closed set of at most 512 resolved package archives",
            "one detached signature for every resolved package",
            "archlinux-keyring archive matching the explicitly frozen trusted-host anchor",
        ],
        "host_effects": [
            "future bounded network reads from the fixed Arch Linux Archive origin",
            "future staging and evidence writes under fixed /var/lib/apx policy paths",
            "future creation of one base, one root, one home, one marker, one account, and one registration",
            "future UID/GID allocation, quota, ownership, and minimal root-filesystem configuration",
            "no graphical session, boot, GPU, audio, input, Hub data, Odysseus, or Codex in Stage 2",
        ],
        "preconditions": list(STAGE2_PRECONDITIONS),
        "postconditions": list(STAGE2_POSTCONDITIONS),
        "failure_states": list(STAGE2_FAILURE_STATES),
        "risks": [
            "host package or trust state contamination during base construction",
            "pathname collision or symlink substitution causing cross-resource mutation",
            "incorrect UID/GID mapping exposing host or another Environment data",
            "unenforced quota allowing host storage exhaustion",
            "partial publication creating ambiguous ownership or unsafe cleanup pressure",
            "system-container isolation proving weaker than the high-security-first profile requires",
        ],
        "rollback_rules": list(STAGE2_ROLLBACK_RULES),
        "destructive_operations": [
            "remove operation-owned staging after separate cleanup approval",
            "remove an unused unpublished root/home/base only after fresh provenance and identity proof",
            "remove account or registration only under a separately rendered cleanup scope",
            "never recursively delete by pathname or reuse Stage 2 creation approval for cleanup",
        ],
        "blockers": list(acquisition.blockers)
        + [
            "human approval authentication, lifetime, replay prevention, and executor protocol are unresolved",
            "exact Btrfs qgroup hierarchy and enforcement verification are unresolved",
            "Stage 2 creation and destructive cleanup approvals have not been granted",
        ],
        "approval": "blocked-pending-review-and-separate-explicit-stage2-approval",
    }
    dossier = Stage2ApprovalDossier(
        schema_version=payload["schema_version"],
        policy_version=payload["policy_version"],
        experiment=payload["experiment"],
        acquisition_plan_digest=payload["acquisition_plan_digest"],
        resources=resources,
        downloads=tuple(payload["downloads"]),
        host_effects=tuple(payload["host_effects"]),
        preconditions=STAGE2_PRECONDITIONS,
        postconditions=STAGE2_POSTCONDITIONS,
        failure_states=STAGE2_FAILURE_STATES,
        risks=tuple(payload["risks"]),
        rollback_rules=STAGE2_ROLLBACK_RULES,
        destructive_operations=tuple(payload["destructive_operations"]),
        blockers=tuple(payload["blockers"]),
        approval=payload["approval"],
        digest="",
    )
    return replace(dossier, digest=compute_stage2_dossier_digest(dossier))


def compute_stage2_dossier_digest(dossier: Stage2ApprovalDossier) -> str:
    payload = {
        "schema_version": dossier.schema_version,
        "policy_version": dossier.policy_version,
        "experiment": dossier.experiment,
        "acquisition_plan_digest": dossier.acquisition_plan_digest,
        "resources": [
            {
                "resource_type": item.resource_type,
                "resource_id": item.resource_id,
                "intended_path": item.intended_path,
                "owner": item.owner,
                "quota": item.quota,
                "identity_evidence": list(item.identity_evidence),
                "initial_state": item.initial_state,
                "publication_state": item.publication_state,
            }
            for item in dossier.resources
        ],
        "downloads": list(dossier.downloads),
        "host_effects": list(dossier.host_effects),
        "preconditions": list(dossier.preconditions),
        "postconditions": list(dossier.postconditions),
        "failure_states": list(dossier.failure_states),
        "risks": list(dossier.risks),
        "rollback_rules": list(dossier.rollback_rules),
        "destructive_operations": list(dossier.destructive_operations),
        "blockers": list(dossier.blockers),
        "approval": dossier.approval,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def render_stage2_approval_dossier(dossier: Stage2ApprovalDossier) -> str:
    lines = [
        "APX Stage 2 approval dossier",
        "Mode: review only; no downloads, creation, execution, or cleanup",
        f"Experiment: {dossier.experiment}",
        f"Policy: {dossier.policy_version}",
        f"Acquisition plan digest: {dossier.acquisition_plan_digest}",
        "Intended resources:",
    ]
    for resource in dossier.resources:
        lines.extend(
            (
                f"- {resource.resource_type} / {resource.resource_id}",
                f"  path: {resource.intended_path}",
                f"  owner: {resource.owner}; quota: {resource.quota}",
                f"  initial: {resource.initial_state}; publication: {resource.publication_state}",
                f"  identity proof: {', '.join(resource.identity_evidence)}",
            )
        )
    for heading, values in (
        ("Downloads", dossier.downloads),
        ("Host effects", dossier.host_effects),
        ("Preconditions", dossier.preconditions),
        ("Postconditions", dossier.postconditions),
        ("Failure states", dossier.failure_states),
        ("Risks", dossier.risks),
        ("Rollback rules", dossier.rollback_rules),
        ("Separately approved destructive operations", dossier.destructive_operations),
        ("Blockers", dossier.blockers),
    ):
        lines.append(f"{heading}:")
        lines.extend(f"- {value}" for value in values)
    lines.extend((f"Approval: {dossier.approval}", f"Dossier digest: {dossier.digest}"))
    return "\n".join(lines)


def build_isolation_experiment_plan() -> IsolationExperimentPlan:
    payload = {
        "schema_version": 1,
        "policy_version": "system-container-v1-headless-deny-default",
        "experiment": "system-container-v1",
        "logical_name": EXPERIMENT_LOGICAL_NAME,
        "account_name": EXPERIMENT_ACCOUNT,
        "home_path": EXPERIMENT_HOME,
        "profile": "high-security-first",
        "base_packages": list(BASE_PACKAGES),
        "resource_policy": dict(RESOURCE_POLICY),
        "steps": list(EXPERIMENT_STEPS),
        "approval": "blocked-pending-explicit-stage-2-approval",
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return IsolationExperimentPlan(
        schema_version=payload["schema_version"],
        policy_version=payload["policy_version"],
        experiment=payload["experiment"],
        logical_name=payload["logical_name"],
        account_name=payload["account_name"],
        home_path=payload["home_path"],
        profile=payload["profile"],
        steps=EXPERIMENT_STEPS,
        approval=payload["approval"],
        digest=hashlib.sha256(encoded).hexdigest(),
    )


def render_isolation_experiment_plan(plan: IsolationExperimentPlan) -> str:
    lines = [
        "APX system-container experiment plan",
        "Mode: plan only; no host changes",
        f"Experiment: {plan.experiment}",
        f"Policy: {plan.policy_version}",
        f"Environment: {plan.logical_name}",
        f"Account: {plan.account_name}",
        f"Home: {plan.home_path}",
        f"Profile: {plan.profile}",
        f"Base packages: {', '.join(BASE_PACKAGES)}",
        "Resource policy: "
        + ", ".join(f"{name}={value}" for name, value in RESOURCE_POLICY),
        f"Approval: {plan.approval}",
        f"Plan digest: {plan.digest}",
        "Ordered steps:",
    ]
    lines.extend(f"{index}. {step}" for index, step in enumerate(plan.steps, 1))
    return "\n".join(lines)


def _check(
    section: str, name: str, classification: str, evidence: str
) -> IsolationReadinessCheck:
    return IsolationReadinessCheck(section, name, classification, evidence)


def _positive(authoritative: bool) -> str:
    return "satisfied" if authoritative else "requires-host-confirmation"


def classify_isolation_readiness(
    checks: Sequence[IsolationReadinessCheck],
) -> str:
    mandatory = {
        check.classification
        for check in checks
        if check.classification != "not-applicable"
    }
    if "blocked" in mandatory:
        return "blocked"
    if mandatory & {"unavailable", "requires-host-confirmation"}:
        return "requires-host-confirmation"
    return "ready-for-stage-2-design-review"


def _quota_enabled_observation(
    *,
    command_runner: Callable[[Sequence[str], float], object],
    authoritative_host: bool,
) -> IsolationReadinessCheck:
    arguments = ("btrfs", "quota", "status", "/home")
    result = command_runner(arguments, COMMAND_TIMEOUT)
    failure = getattr(result, "failure", None)
    returncode = getattr(result, "returncode", None)
    output = str(getattr(result, "stdout", "")).strip()
    if failure or returncode is None:
        return _check("Storage limits", "Btrfs quota accounting enabled", "unavailable", f"observation {failure or 'unavailable'}")
    if returncode != 0:
        return _check("Storage limits", "Btrfs quota accounting enabled", "unavailable", f"observation failed with exit code {returncode}")
    enabled = any(
        line.strip().lower() == "enabled: yes" for line in output.splitlines()
    )
    if not enabled:
        return _check(
            "Storage limits",
            "Btrfs quota accounting enabled",
            "blocked",
            "quota status reports that accounting is not enabled",
        )
    return _check(
        "Storage limits",
        "Btrfs quota accounting enabled",
        _positive(authoritative_host),
        "traditional Btrfs quota accounting reports enabled",
    )


def observe_snapshot_trust_readiness(
    *,
    command_runner: Callable[[Sequence[str], float], object],
    which_func: Callable[[str], str | None],
    lstat_func: Callable[[str], os.stat_result] = os.lstat,
    authoritative_host: bool = False,
) -> SnapshotTrustReadinessReport:
    """Observe only fixed trust/tool identities needed before acquisition."""
    checks: list[IsolationReadinessCheck] = []
    tools = (
        ("pacman", "pacman resolver/acquirer"),
        ("pacman-key", "pacman-key primary verifier"),
        ("gpg", "GnuPG independent verifier"),
        ("sha256sum", "SHA-256 evidence tool"),
    )
    for executable, label in tools:
        path = which_func(executable)
        checks.append(
            _check(
                "Trust tools",
                label,
                _positive(authoritative_host) if path else "blocked",
                f"found {path}" if path else f"{executable} not found",
            )
        )

    for path in SNAPSHOT_TRUST_FILES:
        try:
            metadata = lstat_func(path)
        except FileNotFoundError:
            classification, evidence = "blocked", "fixed keyring file is absent"
        except OSError:
            classification, evidence = "unavailable", "fixed keyring file metadata unavailable"
        else:
            if not stat.S_ISREG(metadata.st_mode):
                classification, evidence = "blocked", "fixed keyring path is not a regular file"
            else:
                classification = _positive(authoritative_host)
                evidence = (
                    f"regular file; device {metadata.st_dev}; inode {metadata.st_ino}; "
                    f"size {metadata.st_size}; uid {metadata.st_uid}; gid {metadata.st_gid}; "
                    f"mode {stat.S_IMODE(metadata.st_mode):04o}"
                )
        checks.append(_check("Trust files", Path(path).name, classification, evidence))

    fixed_commands = (
        ("Trust packages", "installed trust/tool packages", ("pacman", "-Q", "--", "archlinux-keyring", "pacman", "gnupg")),
        ("Trust packages", "installed keyring file verification", ("pacman", "-Qkk", "archlinux-keyring")),
        ("Trust tools", "pacman version", ("pacman", "--version")),
        ("Trust tools", "pacman-key version", ("pacman-key", "--version")),
        ("Trust tools", "GnuPG version", ("gpg", "--version")),
        ("Trust files", "fixed keyring file hashes", ("sha256sum", *SNAPSHOT_TRUST_FILES)),
    )
    for section, name, arguments in fixed_commands:
        checks.append(
            _command_observation(
                section=section,
                name=name,
                arguments=arguments,
                command_runner=command_runner,
                authoritative_host=authoritative_host,
            )
        )

    overall = classify_isolation_readiness(checks)
    return SnapshotTrustReadinessReport(
        checks=tuple(checks),
        overall=overall,
        next_stage=(
            "Review and freeze this evidence in a new acquisition-plan revision; "
            "do not download or mutate trust state."
        ),
    )


def render_snapshot_trust_readiness(report: SnapshotTrustReadinessReport) -> str:
    lines = [
        "APX snapshot trust readiness",
        "Mode: read-only fixed observation; no downloads or trust mutation",
        f"Overall readiness: {report.overall}",
    ]
    current_section = None
    for check in report.checks:
        if check.section != current_section:
            current_section = check.section
            lines.append(f"{current_section}:")
        lines.append(f"- {check.name}: {check.classification} — {check.evidence}")
    lines.extend(("Next stage:", f"- {report.next_stage}"))
    return "\n".join(lines)


def _command_observation(
    *,
    section: str,
    name: str,
    arguments: Sequence[str],
    command_runner: Callable[[Sequence[str], float], object],
    authoritative_host: bool,
) -> IsolationReadinessCheck:
    result = command_runner(tuple(arguments), COMMAND_TIMEOUT)
    failure = getattr(result, "failure", None)
    returncode = getattr(result, "returncode", None)
    stdout = " ".join(str(getattr(result, "stdout", "")).split())[:512]
    if failure or returncode is None:
        return _check(section, name, "unavailable", failure or "observation unavailable")
    if returncode != 0:
        return _check(section, name, "unavailable", f"exit code {returncode}")
    return _check(
        section,
        name,
        _positive(authoritative_host),
        stdout or "command completed without output",
    )


def _read_subordinate_allocation(
    *,
    path: Path,
    account: str,
    read_text_func: Callable[[Path], str],
    authoritative_host: bool,
) -> IsolationReadinessCheck:
    try:
        content = read_text_func(path)
    except OSError:
        return _check(
            "Identity mapping", f"{path.name} allocation for {account}",
            "unavailable", "allocation file could not be read",
        )
    matches: list[tuple[int, int]] = []
    malformed = False
    for line in content.splitlines():
        fields = line.split(":")
        if not fields or fields[0] != account:
            continue
        if len(fields) != 3:
            malformed = True
            continue
        try:
            start, count = int(fields[1]), int(fields[2])
        except ValueError:
            malformed = True
            continue
        if start <= 0 or count <= 0:
            malformed = True
            continue
        matches.append((start, count))
    if malformed or len(matches) > 1:
        return _check(
            "Identity mapping", f"{path.name} allocation for {account}",
            "blocked", "allocation is malformed or ambiguous",
        )
    if not matches:
        return _check(
            "Identity mapping", f"{path.name} allocation for {account}",
            "blocked", "allocation is absent",
        )
    start, count = matches[0]
    return _check(
        "Identity mapping", f"{path.name} allocation for {account}",
        _positive(authoritative_host), f"range start {start}; count {count}",
    )


def _collision_observation(
    *,
    name: str,
    arguments: Sequence[str],
    command_runner: Callable[[Sequence[str], float], object],
    authoritative_host: bool,
) -> IsolationReadinessCheck:
    result = command_runner(tuple(arguments), COMMAND_TIMEOUT)
    failure = getattr(result, "failure", None)
    returncode = getattr(result, "returncode", None)
    stdout = str(getattr(result, "stdout", ""))
    if failure or returncode is None:
        return _check("Collision checks", name, "unavailable", failure or "observation unavailable")
    if returncode != 0:
        return _check("Collision checks", name, "unavailable", f"exit code {returncode}")
    tokens = {field for line in stdout.splitlines() for field in line.split()}
    if EXPERIMENT_LOGICAL_NAME in tokens:
        return _check("Collision checks", name, "blocked", "experiment name already exists")
    return _check(
        "Collision checks", name, _positive(authoritative_host),
        "experiment name is absent",
    )


def _gpu_observations(
    *,
    command_runner: Callable[[Sequence[str], float], object],
    authoritative_host: bool,
) -> tuple[IsolationReadinessCheck, ...]:
    result = command_runner(("lspci", "-Dnnk"), COMMAND_TIMEOUT)
    failure = getattr(result, "failure", None)
    returncode = getattr(result, "returncode", None)
    if failure or returncode is None or returncode != 0:
        evidence = failure or f"exit code {returncode}"
        return (
            _check("Graphics hardware", "AMD graphics", "unavailable", evidence),
            _check("Graphics hardware", "NVIDIA graphics", "unavailable", evidence),
        )
    output = str(getattr(result, "stdout", "")).lower()
    results = []
    for label, markers in (
        ("AMD graphics", ("amd", "1002:")),
        ("NVIDIA graphics", ("nvidia", "10de:")),
    ):
        present = any(marker in output for marker in markers)
        results.append(
            _check(
                "Graphics hardware", label,
                _positive(authoritative_host) if present else "blocked",
                "hardware reported by lspci" if present else "hardware not reported by lspci",
            )
        )
    return tuple(results)


def observe_isolation_readiness(
    *,
    accounts: Sequence[object],
    registration: object,
    incomplete_operation: object,
    command_runner: Callable[[Sequence[str], float], object],
    which_func: Callable[[str], str | None],
    lstat_func: Callable[[str], os.stat_result] = os.lstat,
    read_text_func: Callable[[Path], str] = lambda path: path.read_text(encoding="utf-8"),
    authoritative_host: bool = False,
) -> IsolationReadinessReport:
    """Observe fixed Stage 0 prerequisites without mutating the host."""
    checks: list[IsolationReadinessCheck] = []

    account_exists = any(
        getattr(account, "pw_name", None) == EXPERIMENT_ACCOUNT
        for account in accounts
    )
    checks.append(
        _check(
            "Identity conflicts",
            f"{EXPERIMENT_ACCOUNT} account absent",
            "blocked" if account_exists else _positive(authoritative_host),
            "account exists" if account_exists else "account is absent",
        )
    )

    for path in (Path("/etc/subuid"), Path("/etc/subgid")):
        checks.append(
            _read_subordinate_allocation(
                path=path,
                account="apx-development",
                read_text_func=read_text_func,
                authoritative_host=authoritative_host,
            )
        )
    try:
        lstat_func(EXPERIMENT_HOME)
    except FileNotFoundError:
        home_class, home_evidence = _positive(authoritative_host), "path is absent"
    except OSError:
        home_class, home_evidence = "unavailable", "path metadata unavailable"
    else:
        home_class, home_evidence = "blocked", "path exists"
    checks.append(
        _check(
            "Identity conflicts",
            f"{EXPERIMENT_HOME} absent",
            home_class,
            home_evidence,
        )
    )

    registration_state = str(getattr(registration, "state", "unavailable"))
    if registration_state == "absent":
        registration_class = _positive(authoritative_host)
    elif registration_state == "unavailable":
        registration_class = "unavailable"
    else:
        registration_class = "blocked"
    checks.append(
        _check(
            "Identity conflicts",
            "experiment registration absent",
            registration_class,
            f"registration observation: {registration_state}",
        )
    )

    marker_absent = str(getattr(incomplete_operation, "absent", "unavailable"))
    if marker_absent == "confirmed":
        marker_class = _positive(authoritative_host)
    elif marker_absent == "not-satisfied":
        marker_class = "blocked"
    else:
        marker_class = "unavailable"
    checks.append(
        _check(
            "Identity conflicts",
            "experiment incomplete marker absent",
            marker_class,
            f"marker absence: {marker_absent}",
        )
    )

    mandatory_tools = (
        ("systemd-nspawn", "system container runtime"),
        ("machinectl", "machine lifecycle client"),
        ("systemd-dissect", "image inspection tool"),
        ("btrfs", "Btrfs userspace tool"),
    )
    for executable, label in mandatory_tools:
        path = which_func(executable)
        checks.append(
            _check(
                "Mandatory tools",
                label,
                _positive(authoritative_host) if path else "blocked",
                f"found {path}" if path else f"{executable} not found",
            )
        )

    optional_tools = (
        ("podman", "Podman alternative backend"),
        ("crun", "OCI runtime"),
        ("fuse-overlayfs", "rootless overlay helper"),
        ("nvidia-ctk", "NVIDIA CDI tooling"),
    )
    for executable, label in optional_tools:
        path = which_func(executable)
        checks.append(
            _check(
                "Optional comparison tools",
                label,
                _positive(authoritative_host) if path else "not-applicable",
                f"found {path}" if path else f"{executable} not found",
            )
        )

    fixed_commands = (
        ("Host", "kernel and architecture", ("uname", "-srvmo")),
        (
            "Host",
            "systemd version and features",
            ("systemctl", "--version"),
        ),
        (
            "Isolation primitives",
            "cgroup filesystem",
            ("findmnt", "--json", "--output", "TARGET,FSTYPE,OPTIONS", "--target", "/sys/fs/cgroup"),
        ),
        (
            "Isolation primitives",
            "user namespace limit",
            ("sysctl", "-n", "user.max_user_namespaces"),
        ),
        (
            "Storage capacity",
            "filesystem containing /home",
            ("findmnt", "--json", "--output", "TARGET,SOURCE,FSTYPE,OPTIONS,AVAIL", "--target", "/home"),
        ),
    )
    for section, name, arguments in fixed_commands:
        checks.append(
            _command_observation(
                section=section,
                name=name,
                arguments=arguments,
                command_runner=command_runner,
                authoritative_host=authoritative_host,
            )
        )

    checks.append(
        _quota_enabled_observation(
            command_runner=command_runner,
            authoritative_host=authoritative_host,
        )
    )

    checks.append(
        _collision_observation(
            name="registered systemd machines",
            arguments=("machinectl", "list", "--no-legend", "--no-pager"),
            command_runner=command_runner,
            authoritative_host=authoritative_host,
        )
    )
    checks.append(
        _collision_observation(
            name="registered machine images",
            arguments=("machinectl", "list-images", "--no-legend", "--no-pager"),
            command_runner=command_runner,
            authoritative_host=authoritative_host,
        )
    )
    checks.extend(
        _gpu_observations(
            command_runner=command_runner,
            authoritative_host=authoritative_host,
        )
    )

    overall = classify_isolation_readiness(checks)
    return IsolationReadinessReport(
        experiment="system-container-v1",
        checks=tuple(checks),
        overall=overall,
        next_stage=(
            "Review Stage 0 evidence; do not create a container or modify the host."
        ),
    )


def render_isolation_readiness(report: IsolationReadinessReport) -> str:
    lines = [
        "APX system-container isolation readiness",
        "Mode: read-only Stage 0 observation",
        f"Experiment: {report.experiment}",
        f"Overall readiness: {report.overall}",
    ]
    current_section = None
    for check in report.checks:
        if check.section != current_section:
            current_section = check.section
            lines.append(f"{current_section}:")
        lines.append(
            f"- {check.name}: {check.classification} — {check.evidence}"
        )
    lines.extend(("Next stage:", f"- {report.next_stage}"))
    return "\n".join(lines)


def render_isolation_doctor(report: IsolationReadinessReport) -> str:
    """Explain Stage 0 readiness without exposing the full technical report."""
    blocked = tuple(check for check in report.checks if check.classification == "blocked")
    uncertain = tuple(
        check for check in report.checks
        if check.classification in {"requires-host-confirmation", "unavailable"}
    )
    lines = ["APX safety check", "Target: first disposable isolated Environment", ""]
    if blocked:
        lines.extend((
            "Result: STOP — the real test must not start.",
            "One or more safety requirements failed. Nothing was changed.",
            "",
            "What blocks the test:",
        ))
        lines.extend(f"- {check.name}: {check.evidence}" for check in blocked)
    elif uncertain:
        lines.extend((
            "Result: WAIT — the computer looks compatible, but the evidence is not yet approved for changes.",
            "Nothing was changed.",
            f"Checks awaiting trusted confirmation: {len(uncertain)}.",
        ))
    else:
        lines.extend((
            "Result: READY FOR DESIGN REVIEW — the safety checks passed.",
            "This does not authorize creating the Environment. Nothing was changed.",
        ))
    lines.extend((
        "",
        "Safe next step:",
        "Prepare and verify the exact disposable base, storage limits, rollback boundary, and approval preview.",
        "The existing apx-trial account will not be reused, changed, or deleted.",
    ))
    return "\n".join(lines)
