"""Pure readiness dossier for the first APX clean-install profile."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
import hashlib
import json
import re


SCHEMA_VERSION = 1
PROFILE_VERSION = "apx-clean-install-x86_64-uefi-v1"
MINIMUM_DISK_BYTES = 64 * 1024**3
MAX_SERIALIZED_BYTES = 64 * 1024

BASE_PACKAGES = (
    "base",
    "btrfs-progs",
    "cryptsetup",
    "gnupg",
    "iwd",
    "linux",
    "linux-firmware",
    "python",
)
STAGES = (
    "observe",
    "dossier",
    "approve-disk",
    "storage",
    "arch",
    "boot",
    "apx-bootstrap",
    "hub",
    "development",
    "separation",
)
CONSEQUENCES = (
    "selected-target-disk-will-be-fully-destroyed",
    "rollback-after-format-requires-verified-backup",
    "secure-boot-and-hibernation-are-not-provided",
    "graphics-are-not-installed",
    "fresh-strong-disk-approval-is-still-required",
)

_HEX_32 = re.compile(r"[0-9a-f]{32}")
_HEX_40_OR_64 = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})")
_HEX_64 = re.compile(r"[0-9a-f]{64}")
_LOCALE = re.compile(r"[A-Za-z]{2,3}_[A-Za-z]{2,3}\.UTF-8")
_KEYMAP = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}")
_TIMEZONE = re.compile(r"[A-Za-z0-9_+-]+(?:/[A-Za-z0-9_+-]+){1,3}")
_HOSTNAME = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?")


class CleanInstallDossierError(ValueError):
    """Input is malformed or outside the fixed clean-install profile."""


@dataclass(frozen=True)
class TargetEvidence:
    schema_version: int
    target_id: str
    architecture: str
    firmware_mode: str
    disk_identity_digest: str
    disk_size_bytes: int
    disk_not_running_system: bool
    disk_unmounted: bool
    unsupported_topology_absent: bool
    backup_manifest_digest: str
    backup_sample_restore_passed: bool
    recovery_media_digest: str
    recovery_media_boot_passed: bool
    network_ready: bool
    trusted_time_ready: bool
    locale: str
    keymap: str
    timezone: str
    hostname: str
    cpu_vendor: str


@dataclass(frozen=True)
class SupplyChainEvidence:
    schema_version: int
    arch_snapshot_date: str
    package_manifest_digest: str
    package_signatures_verified: bool
    apx_source_revision: str
    apx_package_sha256: str
    apx_root_fingerprint: str
    apx_release_signer_fingerprint: str
    apx_signature_verified: bool
    apx_key_custody_ready: bool
    executor_boundary_reviewed: bool
    disposable_install_rehearsal_passed: bool


@dataclass(frozen=True)
class CleanInstallDossier:
    schema_version: int
    profile_version: str
    classification: str
    blockers: tuple[str, ...]
    target_id: str
    target_evidence_digest: str
    supply_chain_evidence_digest: str
    arch_snapshot_uri: str
    packages: tuple[str, ...]
    stages: tuple[str, ...]
    consequences: tuple[str, ...]
    separate_strong_approval_required: bool
    plan_digest: str


def _reject_duplicate_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise CleanInstallDossierError("evidence JSON has duplicate fields")
        result[key] = value
    return result


def _parse_json(text: str, expected: frozenset[str], label: str) -> dict[str, object]:
    if not isinstance(text, str) or not text:
        raise CleanInstallDossierError(f"{label} JSON is empty or oversized")
    try:
        encoded = text.encode("utf-8")
    except UnicodeEncodeError as error:
        raise CleanInstallDossierError(f"{label} JSON is not valid UTF-8") from error
    if len(encoded) > MAX_SERIALIZED_BYTES:
        raise CleanInstallDossierError(f"{label} JSON is empty or oversized")
    try:
        payload = json.loads(text, object_pairs_hook=_reject_duplicate_pairs)
    except json.JSONDecodeError as error:
        raise CleanInstallDossierError(f"{label} JSON is invalid") from error
    if not isinstance(payload, dict) or set(payload) != expected:
        raise CleanInstallDossierError(f"{label} fields do not match schema")
    return payload


def parse_target_evidence_json(text: str) -> TargetEvidence:
    try:
        target = TargetEvidence(**_parse_json(text, frozenset(TargetEvidence.__dataclass_fields__), "target evidence"))
    except TypeError as error:
        raise CleanInstallDossierError("target evidence values are malformed") from error
    _validate_target(target)
    return target


def parse_supply_chain_evidence_json(text: str) -> SupplyChainEvidence:
    try:
        supply = SupplyChainEvidence(**_parse_json(text, frozenset(SupplyChainEvidence.__dataclass_fields__), "supply-chain evidence"))
    except TypeError as error:
        raise CleanInstallDossierError("supply-chain evidence values are malformed") from error
    _validate_supply(supply)
    return supply


def _digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _validate_digest(value: object, field: str) -> None:
    if not isinstance(value, str) or not _HEX_64.fullmatch(value):
        raise CleanInstallDossierError(f"{field} is not a canonical SHA-256")


def _validate_target(target: TargetEvidence) -> None:
    if type(target) is not TargetEvidence or type(target.schema_version) is not int or target.schema_version != 1:
        raise CleanInstallDossierError("target evidence schema is invalid")
    if not isinstance(target.target_id, str) or not target.target_id.startswith("target-") or not _HEX_32.fullmatch(target.target_id[7:]):
        raise CleanInstallDossierError("target identity is invalid")
    if target.architecture != "x86_64" or target.firmware_mode != "uefi":
        raise CleanInstallDossierError("target is outside x86_64 UEFI profile")
    _validate_digest(target.disk_identity_digest, "disk identity digest")
    _validate_digest(target.backup_manifest_digest, "backup manifest digest")
    _validate_digest(target.recovery_media_digest, "recovery media digest")
    if type(target.disk_size_bytes) is not int or target.disk_size_bytes <= 0:
        raise CleanInstallDossierError("target disk size is invalid")
    for field in (
        "disk_not_running_system",
        "disk_unmounted",
        "unsupported_topology_absent",
        "backup_sample_restore_passed",
        "recovery_media_boot_passed",
        "network_ready",
        "trusted_time_ready",
    ):
        if type(getattr(target, field)) is not bool:
            raise CleanInstallDossierError(f"{field} must be boolean evidence")
    if not isinstance(target.locale, str) or not _LOCALE.fullmatch(target.locale):
        raise CleanInstallDossierError("locale is invalid")
    if not isinstance(target.keymap, str) or not _KEYMAP.fullmatch(target.keymap):
        raise CleanInstallDossierError("keymap is invalid")
    if not isinstance(target.timezone, str) or not _TIMEZONE.fullmatch(target.timezone):
        raise CleanInstallDossierError("timezone is invalid")
    if not isinstance(target.hostname, str) or not _HOSTNAME.fullmatch(target.hostname):
        raise CleanInstallDossierError("hostname is invalid")
    if target.cpu_vendor not in {"amd", "intel"}:
        raise CleanInstallDossierError("CPU vendor is unsupported")


def _validate_supply(supply: SupplyChainEvidence) -> None:
    if type(supply) is not SupplyChainEvidence or type(supply.schema_version) is not int or supply.schema_version != 1:
        raise CleanInstallDossierError("supply-chain evidence schema is invalid")
    if not isinstance(supply.arch_snapshot_date, str):
        raise CleanInstallDossierError("Arch snapshot date is invalid")
    try:
        parsed_date = date.fromisoformat(supply.arch_snapshot_date)
    except ValueError as error:
        raise CleanInstallDossierError("Arch snapshot date is invalid") from error
    if parsed_date.year < 2020 or supply.arch_snapshot_date != parsed_date.isoformat():
        raise CleanInstallDossierError("Arch snapshot date is invalid")
    for field in (
        "package_manifest_digest",
        "apx_package_sha256",
    ):
        _validate_digest(getattr(supply, field), field)
    for field in ("apx_source_revision", "apx_root_fingerprint", "apx_release_signer_fingerprint"):
        value = getattr(supply, field)
        if not isinstance(value, str) or not _HEX_40_OR_64.fullmatch(value):
            raise CleanInstallDossierError(f"{field} is invalid")
    for field in (
        "package_signatures_verified",
        "apx_signature_verified",
        "apx_key_custody_ready",
        "executor_boundary_reviewed",
        "disposable_install_rehearsal_passed",
    ):
        if type(getattr(supply, field)) is not bool:
            raise CleanInstallDossierError(f"{field} must be boolean evidence")


def build_dossier(target: TargetEvidence, supply: SupplyChainEvidence) -> CleanInstallDossier:
    _validate_target(target)
    _validate_supply(supply)
    blockers: list[str] = []
    gates = {
        "target-disk-is-running-system": target.disk_not_running_system,
        "target-disk-has-mounted-content": target.disk_unmounted,
        "unsupported-storage-or-boot-topology": target.unsupported_topology_absent,
        "backup-sample-restore-not-passed": target.backup_sample_restore_passed,
        "recovery-media-boot-not-passed": target.recovery_media_boot_passed,
        "network-not-ready": target.network_ready,
        "trusted-time-not-ready": target.trusted_time_ready,
        "package-signatures-not-verified": supply.package_signatures_verified,
        "apx-signature-not-verified": supply.apx_signature_verified,
        "apx-key-custody-not-ready": supply.apx_key_custody_ready,
        "executor-boundary-not-reviewed": supply.executor_boundary_reviewed,
        "disposable-install-rehearsal-not-passed": supply.disposable_install_rehearsal_passed,
    }
    for blocker, passed in gates.items():
        if not passed:
            blockers.append(blocker)
    if target.disk_size_bytes < MINIMUM_DISK_BYTES:
        blockers.append("target-disk-smaller-than-64-gib")

    packages = tuple(sorted(BASE_PACKAGES + (f"{target.cpu_vendor}-ucode",)))
    target_digest = _digest(asdict(target))
    supply_digest = _digest(asdict(supply))
    snapshot_uri = "https://archive.archlinux.org/repos/" + supply.arch_snapshot_date.replace("-", "/")
    subject = {
        "arch_snapshot_uri": snapshot_uri,
        "consequences": CONSEQUENCES,
        "packages": packages,
        "profile_version": PROFILE_VERSION,
        "schema_version": SCHEMA_VERSION,
        "separate_strong_approval_required": True,
        "stages": STAGES,
        "supply_chain_evidence_digest": supply_digest,
        "target_evidence_digest": target_digest,
        "target_id": target.target_id,
    }
    return CleanInstallDossier(
        SCHEMA_VERSION,
        PROFILE_VERSION,
        "ready-for-separate-approval" if not blockers else "blocked",
        tuple(sorted(blockers)),
        target.target_id,
        target_digest,
        supply_digest,
        snapshot_uri,
        packages,
        STAGES,
        CONSEQUENCES,
        True,
        _digest(subject),
    )
