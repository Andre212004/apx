"""Pure fixed staging and target plan for a future physical APX update.

This module emits evidence-bound descriptions only. It has no filesystem,
service, Environment lifecycle, installation, rollback, or cleanup adapter.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import re

from apx_physical_update import (
    InstalledPilotEvidence,
    PhysicalUpdateCandidate,
    PhysicalUpdatePreview,
    PROFILE,
    SCHEMA_VERSION,
    build_update_preview,
    validate_candidate,
    validate_installed_evidence,
)
from apx_physical_update_artifact import PhysicalUpdateArtifactEvidence


STAGING_ROOT = "/var/lib/apx/updates/staging"
ARTIFACT_NAME = "candidate.tar"
RUNTIME_TARGET = "/usr/lib/apx/apx-lab-runtime.py"
RUNTIME_ALIAS = "/usr/bin/apx"
SUPPORTED_PHYSICAL_COMPONENTS = ("host-runtime",)
_SHA256 = re.compile(r"[0-9a-f]{64}")
_UPDATE_ID = re.compile(r"update-[0-9a-f]{32}")


class PhysicalUpdateEffectError(ValueError):
    """A physical effect plan is ambiguous, stale, or outside policy."""


@dataclass(frozen=True)
class FixedComponentTarget:
    component: str
    destination: str
    mode: int
    before_sha256: str
    after_sha256: str
    rollback_sha256: str
    required_alias: str
    required_alias_target: str


@dataclass(frozen=True)
class PhysicalUpdateImportPlan:
    schema_version: int
    profile: str
    update_id: str
    staging_root: str
    operation_directory: str
    artifact_name: str
    artifact_bytes: int
    artifact_sha256: str
    candidate_digest: str
    installed_evidence_digest: str
    preview_plan_digest: str
    import_approval_digest: str
    targets: tuple[FixedComponentTarget, ...]
    effects_absent: tuple[str, ...]
    plan_digest: str


def _digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _with_plan_digest(plan: PhysicalUpdateImportPlan) -> PhysicalUpdateImportPlan:
    values = asdict(plan)
    values.pop("plan_digest")
    return PhysicalUpdateImportPlan(
        **{
            **values,
            "targets": plan.targets,
            "effects_absent": plan.effects_absent,
            "plan_digest": _digest(values),
        }
    )


def build_import_plan(
    candidate: PhysicalUpdateCandidate,
    installed: InstalledPilotEvidence,
    preview: PhysicalUpdatePreview,
    artifact: PhysicalUpdateArtifactEvidence,
    *,
    import_approval_digest: str,
) -> PhysicalUpdateImportPlan:
    validate_candidate(candidate)
    validate_installed_evidence(installed)
    if type(preview) is not PhysicalUpdatePreview:
        raise PhysicalUpdateEffectError("physical update preview type is invalid")
    if type(artifact) is not PhysicalUpdateArtifactEvidence:
        raise PhysicalUpdateEffectError("artifact evidence type is invalid")
    if candidate.components != SUPPORTED_PHYSICAL_COMPONENTS:
        raise PhysicalUpdateEffectError("component set has no reviewed physical target mapping")
    candidate_digest = _digest(asdict(candidate))
    installed_digest = _digest(asdict(installed))
    expected_preview = build_update_preview(candidate, installed)
    if (
        preview != expected_preview
        or preview.schema_version != SCHEMA_VERSION
        or preview.profile != PROFILE
        or preview.classification != "ready-for-separate-import-approval"
        or preview.blockers
        or preview.update_id != candidate.update_id
        or preview.installed_source_revision != installed.installed_source_revision
        or preview.next_source_revision != candidate.source_revision
        or preview.components != candidate.components
        or preview.candidate_digest != candidate_digest
        or preview.installed_evidence_digest != installed_digest
        or preview.separate_import_approval_required is not True
        or preview.separate_activation_approval_required is not True
        or preview.rollback_retirement_requires_later_approval is not True
    ):
        raise PhysicalUpdateEffectError("preview is blocked, stale, or disagrees with supplied evidence")
    if (
        artifact.artifact_sha256 != candidate.artifact_sha256
        or artifact.artifact_bytes != candidate.artifact_bytes
        or artifact.manifest_digest != candidate.member_manifest_digest
        or artifact.member_count != candidate.member_count
        or tuple(name for name, _ in artifact.component_digests) != candidate.components
    ):
        raise PhysicalUpdateEffectError("artifact evidence disagrees with candidate")
    if not isinstance(import_approval_digest, str) or not _SHA256.fullmatch(import_approval_digest):
        raise PhysicalUpdateEffectError("import approval digest is invalid")
    after_digest = artifact.component_digests[0][1]
    if not _SHA256.fullmatch(after_digest):
        raise PhysicalUpdateEffectError("component evidence digest is invalid")
    target = FixedComponentTarget(
        "host-runtime",
        RUNTIME_TARGET,
        0o755,
        installed.installed_runtime_sha256,
        after_digest,
        installed.installed_runtime_sha256,
        RUNTIME_ALIAS,
        RUNTIME_TARGET,
    )
    plan = PhysicalUpdateImportPlan(
        SCHEMA_VERSION,
        PROFILE,
        candidate.update_id,
        STAGING_ROOT,
        f"{STAGING_ROOT}/{candidate.update_id}",
        ARTIFACT_NAME,
        candidate.artifact_bytes,
        candidate.artifact_sha256,
        candidate_digest,
        installed_digest,
        preview.plan_digest,
        import_approval_digest,
        (target,),
        (
            "no-filesystem-write",
            "no-service-control",
            "no-environment-lifecycle",
            "no-install-or-rollback",
            "no-cleanup",
        ),
        "",
    )
    plan = _with_plan_digest(plan)
    validate_import_plan(plan)
    return plan


def validate_import_plan(plan: PhysicalUpdateImportPlan) -> None:
    if type(plan) is not PhysicalUpdateImportPlan:
        raise PhysicalUpdateEffectError("import plan type is invalid")
    if plan.schema_version != SCHEMA_VERSION or plan.profile != PROFILE:
        raise PhysicalUpdateEffectError("import plan schema or profile is invalid")
    if not isinstance(plan.update_id, str) or not _UPDATE_ID.fullmatch(plan.update_id):
        raise PhysicalUpdateEffectError("import plan update identity is invalid")
    if plan.staging_root != STAGING_ROOT or plan.operation_directory != f"{STAGING_ROOT}/{plan.update_id}":
        raise PhysicalUpdateEffectError("import staging path is not fixed")
    if plan.artifact_name != ARTIFACT_NAME or plan.targets != (
        FixedComponentTarget(
            "host-runtime", RUNTIME_TARGET, 0o755,
            plan.targets[0].before_sha256 if len(plan.targets) == 1 else "",
            plan.targets[0].after_sha256 if len(plan.targets) == 1 else "",
            plan.targets[0].rollback_sha256 if len(plan.targets) == 1 else "",
            RUNTIME_ALIAS, RUNTIME_TARGET,
        ),
    ):
        raise PhysicalUpdateEffectError("component target mapping is not fixed")
    target = plan.targets[0]
    if target.before_sha256 != target.rollback_sha256:
        raise PhysicalUpdateEffectError("rollback identity differs from installed-before identity")
    for value in (
        plan.artifact_sha256, plan.candidate_digest, plan.installed_evidence_digest,
        plan.preview_plan_digest, plan.import_approval_digest, target.before_sha256,
        target.after_sha256, target.rollback_sha256, plan.plan_digest,
    ):
        if not isinstance(value, str) or not _SHA256.fullmatch(value):
            raise PhysicalUpdateEffectError("import plan contains a malformed digest")
    if type(plan.artifact_bytes) is not int or plan.artifact_bytes <= 0:
        raise PhysicalUpdateEffectError("import plan artifact size is invalid")
    expected_absent = (
        "no-filesystem-write", "no-service-control", "no-environment-lifecycle",
        "no-install-or-rollback", "no-cleanup",
    )
    if plan.effects_absent != expected_absent:
        raise PhysicalUpdateEffectError("import plan effect boundary changed")
    values = asdict(plan)
    claimed = values.pop("plan_digest")
    if claimed != _digest(values):
        raise PhysicalUpdateEffectError("import plan digest mismatch")
