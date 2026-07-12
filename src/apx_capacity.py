"""Pure APX elastic-capacity and Stage 2 storage-gate contract."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json


GIB = 1024**3
TRIAL_ROOT_LIMIT = 8 * GIB
TRIAL_HOME_LIMIT = 2 * GIB
TRIAL_ACQUISITION_LIMIT = 4 * GIB
TRIAL_WORKING_MARGIN = 2 * GIB
TRIAL_REQUIRED_HEADROOM = (
    TRIAL_ROOT_LIMIT
    + TRIAL_HOME_LIMIT
    + TRIAL_ACQUISITION_LIMIT
    + TRIAL_WORKING_MARGIN
)
TRIAL_HOST_RESERVE = 64 * GIB


@dataclass(frozen=True)
class QuotaEvidence:
    enabled: bool
    full_accounting: bool
    inconsistent: bool
    override_limits: bool
    rescan_running: bool
    bounded_enforcement_passed: bool


@dataclass(frozen=True)
class CapacityEvidence:
    filesystem_identity: str
    total_bytes: int
    free_bytes: int
    metadata_free_bytes: int
    quota: QuotaEvidence
    authoritative: bool


@dataclass(frozen=True)
class CapacityAssessment:
    decision: str
    reasons: tuple[str, ...]
    required_headroom_bytes: int
    host_reserve_bytes: int
    evidence_digest: str


@dataclass(frozen=True)
class GrowthAssessment:
    decision: str
    allowed_growth_bytes: int
    reasons: tuple[str, ...]


def _valid_bytes(value: object) -> bool:
    return type(value) is int and value >= 0


def _digest(evidence: CapacityEvidence) -> str:
    payload = {
        "authoritative": evidence.authoritative,
        "filesystem_identity": evidence.filesystem_identity,
        "free_bytes": evidence.free_bytes,
        "metadata_free_bytes": evidence.metadata_free_bytes,
        "quota": {
            "bounded_enforcement_passed": evidence.quota.bounded_enforcement_passed,
            "enabled": evidence.quota.enabled,
            "full_accounting": evidence.quota.full_accounting,
            "inconsistent": evidence.quota.inconsistent,
            "override_limits": evidence.quota.override_limits,
            "rescan_running": evidence.quota.rescan_running,
        },
        "total_bytes": evidence.total_bytes,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def assess_trial_capacity(evidence: CapacityEvidence) -> CapacityAssessment:
    """Fail closed unless every fixed Stage 2 storage gate is satisfied."""
    reasons: list[str] = []
    if not isinstance(evidence.filesystem_identity, str) or not evidence.filesystem_identity:
        reasons.append("filesystem identity is unavailable")
    for name in ("total_bytes", "free_bytes", "metadata_free_bytes"):
        if not _valid_bytes(getattr(evidence, name)):
            reasons.append(f"{name} is invalid")
    if reasons:
        decision = "blocked"
    else:
        if evidence.free_bytes > evidence.total_bytes:
            reasons.append("free space exceeds filesystem size")
        quota = evidence.quota
        if type(quota) is not QuotaEvidence:
            reasons.append("quota evidence has wrong type")
        else:
            if not quota.enabled:
                reasons.append("quota accounting is disabled")
            if not quota.full_accounting:
                reasons.append("quota accounting is not traditional full mode")
            if quota.inconsistent:
                reasons.append("quota accounting is inconsistent")
            if quota.override_limits:
                reasons.append("quota limits are being overridden")
            if quota.rescan_running:
                reasons.append("quota rescan is still running")
            if not quota.bounded_enforcement_passed:
                reasons.append("bounded quota enforcement fixture has not passed")
        required_free = TRIAL_REQUIRED_HEADROOM + TRIAL_HOST_RESERVE
        if evidence.free_bytes < required_free:
            reasons.append("free space would cross the Stage 2 host reserve")
        if evidence.metadata_free_bytes < TRIAL_WORKING_MARGIN:
            reasons.append("metadata safety margin is insufficient")
        if reasons:
            decision = "blocked"
        elif not evidence.authoritative:
            decision = "pending-authoritative-confirmation"
            reasons.append("capacity evidence is not authoritative")
        else:
            decision = "ready-for-stage2-capacity-gate"
    return CapacityAssessment(
        decision=decision,
        reasons=tuple(reasons),
        required_headroom_bytes=TRIAL_REQUIRED_HEADROOM,
        host_reserve_bytes=TRIAL_HOST_RESERVE,
        evidence_digest=_digest(evidence),
    )


def assess_elastic_growth(
    *,
    requested_growth_bytes: int,
    domain_headroom_bytes: int,
    pool_headroom_bytes: int,
    physical_free_bytes: int,
    host_reserve_bytes: int,
    quota_healthy: bool,
) -> GrowthAssessment:
    """Assess growth without reserving or changing any storage."""
    values = (
        requested_growth_bytes,
        domain_headroom_bytes,
        pool_headroom_bytes,
        physical_free_bytes,
        host_reserve_bytes,
    )
    if not all(_valid_bytes(value) for value in values) or type(quota_healthy) is not bool:
        return GrowthAssessment("blocked", 0, ("growth evidence is invalid",))
    if not quota_healthy:
        return GrowthAssessment("blocked", 0, ("quota health is not confirmed",))
    physical_headroom = max(0, physical_free_bytes - host_reserve_bytes)
    allowed = min(domain_headroom_bytes, pool_headroom_bytes, physical_headroom)
    if requested_growth_bytes <= allowed:
        return GrowthAssessment("allowed", requested_growth_bytes, ())
    reasons: list[str] = []
    if requested_growth_bytes > domain_headroom_bytes:
        reasons.append("Environment safety ceiling would be crossed")
    if requested_growth_bytes > pool_headroom_bytes:
        reasons.append("APX pool safety ceiling would be crossed")
    if requested_growth_bytes > physical_headroom:
        reasons.append("host storage reserve would be crossed")
    return GrowthAssessment("blocked", allowed, tuple(reasons))
