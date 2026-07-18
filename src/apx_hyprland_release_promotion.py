"""Pure promotion preview for the finalized Hyprland H0 release root."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import re


SCHEMA_VERSION = 1
PROFILE = "apx-hyprland-h0-release-promotion-v1"
RELEASE_ID = "hyprland-h0-v1"
SOURCE_ROOT = "/tmp/apx-hyprland-build-v1/rootfs"
TARGET_DIRECTORY = "/var/lib/apx/releases/hyprland-h0-v1"
TARGET_ROOT = TARGET_DIRECTORY + "/root"
PACKAGE_COUNT = 332
SOURCE_TREE_DIGEST = "83c58deaa56c83c23eee57dc02ecd3a67ccaede0d75918932f7f3b9557ab3401"
FINAL_REPORT_DIGEST = "fb8a06d588b3dbf0f48b8626a1effc0df95e4c6dd12bfa995f167fe0376c530a"
MINIMUM_FREE_BYTES = 4 * 1024**3
MAX_JSON_BYTES = 64 * 1024
ACCOUNT = ("apx", 1000, 1000, "/home/apx", "/usr/bin/bash", True)
PROMOTION_EFFECTS = (
    "reverify-finalized-source-and-report",
    "reserve-exact-new-release-directory",
    "create-one-btrfs-release-root-subvolume",
    "copy-normalized-tree-with-source-preserved",
    "configure-fixed-environment-account-and-empty-identity",
    "write-canonical-graphical-role-manifest",
    "set-release-root-read-only",
    "remeasure-and-publish-release-identity",
)
_SHA256 = re.compile(r"[0-9a-f]{64}")
_UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}")


class HyprlandReleasePromotionError(ValueError):
    """Promotion evidence is malformed or outside the fixed H0 release."""


@dataclass(frozen=True)
class HyprlandReleasePromotionEvidence:
    schema_version: int
    profile: str
    observation_digest: str
    recovery_receipt_digest: str
    machine_identity_digest: str
    physical_marker_digest: str
    source_tree_digest: str
    final_report_digest: str
    package_count: int
    source_reverified: bool
    source_identity_neutral: bool
    private_material_absent: bool
    runtime_residue_absent: bool
    source_special_files_absent: bool
    source_development_ownership_absent: bool
    destination_absent: bool
    destination_parent_real_btrfs: bool
    btrfs_quota_healthy: bool
    no_uncertain_apx_operation: bool
    hub_generation: str
    development_generation: str
    disposable_hold_unchanged: bool
    host_free_bytes: int


@dataclass(frozen=True)
class HyprlandReleasePromotionPreview:
    schema_version: int
    profile: str
    classification: str
    blockers: tuple[str, ...]
    release_id: str
    source_root: str
    target_directory: str
    target_root: str
    package_count: int
    account: tuple[object, ...]
    effects: tuple[str, ...]
    evidence_digest: str
    consequence_digest: str
    plan_digest: str
    separate_promotion_approval_required: bool
    environment_creation_not_authorized: bool
    graphical_activation_not_authorized: bool
    automatic_cleanup_not_authorized: bool


def _reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise HyprlandReleasePromotionError("promotion JSON has duplicate fields")
        result[key] = value
    return result


def parse_promotion_evidence_json(text: str) -> HyprlandReleasePromotionEvidence:
    if not isinstance(text, str) or not text:
        raise HyprlandReleasePromotionError("promotion JSON is empty or oversized")
    try:
        encoded = text.encode("utf-8")
    except UnicodeEncodeError as error:
        raise HyprlandReleasePromotionError("promotion JSON is not UTF-8") from error
    if len(encoded) > MAX_JSON_BYTES:
        raise HyprlandReleasePromotionError("promotion JSON is empty or oversized")
    try:
        raw = json.loads(text, object_pairs_hook=_reject_duplicates)
    except json.JSONDecodeError as error:
        raise HyprlandReleasePromotionError("promotion JSON is invalid") from error
    expected = frozenset(HyprlandReleasePromotionEvidence.__dataclass_fields__)
    if not isinstance(raw, dict) or set(raw) != expected:
        raise HyprlandReleasePromotionError("promotion fields do not match schema")
    try:
        evidence = HyprlandReleasePromotionEvidence(**raw)
    except TypeError as error:
        raise HyprlandReleasePromotionError("promotion values are malformed") from error
    validate_promotion_evidence(evidence)
    return evidence


def _digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def validate_promotion_evidence(evidence: HyprlandReleasePromotionEvidence) -> None:
    if type(evidence) is not HyprlandReleasePromotionEvidence:
        raise HyprlandReleasePromotionError("promotion evidence type is invalid")
    if evidence.schema_version != SCHEMA_VERSION or evidence.profile != PROFILE:
        raise HyprlandReleasePromotionError("promotion schema or profile is invalid")
    for field in (
        "observation_digest", "recovery_receipt_digest", "machine_identity_digest",
        "physical_marker_digest", "source_tree_digest", "final_report_digest",
    ):
        value = getattr(evidence, field)
        if not isinstance(value, str) or not _SHA256.fullmatch(value):
            raise HyprlandReleasePromotionError(f"{field} is not a canonical SHA-256")
    if evidence.source_tree_digest != SOURCE_TREE_DIGEST or evidence.final_report_digest != FINAL_REPORT_DIGEST:
        raise HyprlandReleasePromotionError("finalized source identity changed")
    if type(evidence.package_count) is not int or evidence.package_count != PACKAGE_COUNT:
        raise HyprlandReleasePromotionError("graphical package count changed")
    boolean_fields = (
        "source_reverified", "source_identity_neutral", "private_material_absent",
        "runtime_residue_absent", "source_special_files_absent",
        "source_development_ownership_absent", "destination_absent",
        "destination_parent_real_btrfs", "btrfs_quota_healthy",
        "no_uncertain_apx_operation", "disposable_hold_unchanged",
    )
    for field in boolean_fields:
        if type(getattr(evidence, field)) is not bool:
            raise HyprlandReleasePromotionError(f"{field} must be boolean evidence")
    for field in ("hub_generation", "development_generation"):
        value = getattr(evidence, field)
        if not isinstance(value, str) or not _UUID.fullmatch(value):
            raise HyprlandReleasePromotionError(f"{field} is not a canonical generation")
    if type(evidence.host_free_bytes) is not int or evidence.host_free_bytes < 0:
        raise HyprlandReleasePromotionError("host free bytes are invalid")


def build_promotion_preview(
    evidence: HyprlandReleasePromotionEvidence,
) -> HyprlandReleasePromotionPreview:
    validate_promotion_evidence(evidence)
    gates = {
        "source-not-reverified": evidence.source_reverified,
        "source-not-identity-neutral": evidence.source_identity_neutral,
        "private-material-present": evidence.private_material_absent,
        "runtime-residue-present": evidence.runtime_residue_absent,
        "source-special-file-present": evidence.source_special_files_absent,
        "development-owned-source-entry-present": evidence.source_development_ownership_absent,
        "release-destination-exists": evidence.destination_absent,
        "release-parent-not-real-btrfs": evidence.destination_parent_real_btrfs,
        "btrfs-quota-unhealthy": evidence.btrfs_quota_healthy,
        "uncertain-apx-operation-present": evidence.no_uncertain_apx_operation,
        "disposable-hold-changed": evidence.disposable_hold_unchanged,
    }
    blockers = [label for label, passed in gates.items() if not passed]
    if evidence.host_free_bytes < MINIMUM_FREE_BYTES:
        blockers.append("host-free-space-below-4-gib")
    evidence_digest = _digest(asdict(evidence))
    consequences = (
        "one-new-immutable-graphical-release-would-be-created",
        "host-packages-and-existing-environments-remain-unchanged",
        "no-graphical-environment-or-session-would-be-created",
        "partial-state-is-preserved-and-never-cleaned-automatically",
    )
    consequence_digest = _digest(consequences)
    plan = {
        "profile": PROFILE, "release_id": RELEASE_ID,
        "source_root": SOURCE_ROOT, "target_directory": TARGET_DIRECTORY,
        "target_root": TARGET_ROOT, "package_count": PACKAGE_COUNT,
        "source_tree_digest": SOURCE_TREE_DIGEST,
        "final_report_digest": FINAL_REPORT_DIGEST,
        "account": ACCOUNT, "effects": PROMOTION_EFFECTS,
        "evidence_digest": evidence_digest, "consequence_digest": consequence_digest,
        "authority": "none-preview-only",
    }
    return HyprlandReleasePromotionPreview(
        SCHEMA_VERSION, PROFILE,
        "ready-for-separate-promotion-approval" if not blockers else "blocked",
        tuple(blockers), RELEASE_ID, SOURCE_ROOT, TARGET_DIRECTORY, TARGET_ROOT,
        PACKAGE_COUNT, ACCOUNT, PROMOTION_EFFECTS, evidence_digest,
        consequence_digest, _digest(plan), True, True, True, True,
    )
