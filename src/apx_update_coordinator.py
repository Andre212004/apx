"""Pure policy and transaction plan for coordinated APX package updates."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import re


SCHEMA = 1
PROFILE = "apx-coordinated-updates-v1"
DEFAULT_POLICY = "follow-host"
POLICIES = ("excluded", "follow-host")
_NAME = re.compile(r"[a-z](?:[a-z0-9]|-(?=[a-z0-9])){0,26}")
_GENERATION = re.compile(r"[0-9a-f-]{36}")


class UpdateCoordinatorError(ValueError):
    pass


@dataclass(frozen=True)
class EnvironmentUpdatePolicy:
    schema: int
    profile: str
    environment: str
    policy: str
    source: str


@dataclass(frozen=True)
class EnvironmentUpdateEvidence:
    name: str
    role: str
    generation: str
    state: str
    policy: str
    package_database_ready: bool
    snapshot_ready: bool


@dataclass(frozen=True)
class UpdateTarget:
    kind: str
    name: str
    generation: str | None
    snapshot_required: bool
    offline_apply_required: bool


@dataclass(frozen=True)
class CoordinatedUpdatePlan:
    schema: int
    profile: str
    classification: str
    targets: tuple[UpdateTarget, ...]
    excluded_environments: tuple[str, ...]
    blockers: tuple[str, ...]
    effects: tuple[str, ...]
    plan_digest: str


def default_policy(environment: str) -> EnvironmentUpdatePolicy:
    return validate_policy(EnvironmentUpdatePolicy(SCHEMA, PROFILE, environment, DEFAULT_POLICY, "creation-default"))


def validate_policy(policy: EnvironmentUpdatePolicy) -> EnvironmentUpdatePolicy:
    if type(policy) is not EnvironmentUpdatePolicy or policy.schema != SCHEMA or policy.profile != PROFILE \
            or type(policy.environment) is not str or _NAME.fullmatch(policy.environment) is None \
            or policy.policy not in POLICIES or policy.source not in {"creation-default", "owner-selection"}:
        raise UpdateCoordinatorError("Environment update policy is invalid")
    return policy


def policy_from_registration(record: dict[str, object]) -> EnvironmentUpdatePolicy:
    if type(record) is not dict or type(record.get("name")) is not str:
        raise UpdateCoordinatorError("registration is invalid")
    raw = record.get("update_policy", DEFAULT_POLICY)
    source = "owner-selection" if "update_policy" in record else "creation-default"
    return validate_policy(EnvironmentUpdatePolicy(SCHEMA, PROFILE, str(record["name"]), str(raw), source))


def _validate_environment(item: EnvironmentUpdateEvidence) -> None:
    if type(item) is not EnvironmentUpdateEvidence or _NAME.fullmatch(item.name) is None \
            or item.policy not in POLICIES or item.state not in {"running", "stopped"} \
            or _GENERATION.fullmatch(item.generation) is None \
            or type(item.package_database_ready) is not bool or type(item.snapshot_ready) is not bool:
        raise UpdateCoordinatorError("Environment update evidence is invalid")


def build_plan(environments: tuple[EnvironmentUpdateEvidence, ...], *, host_snapshot_ready: bool,
               repository_snapshot_ready: bool, package_cache_ready: bool) -> CoordinatedUpdatePlan:
    if type(environments) is not tuple or tuple(sorted(environments, key=lambda item: item.name)) != environments \
            or len({item.name for item in environments}) != len(environments):
        raise UpdateCoordinatorError("Environment inventory is not canonical")
    for item in environments: _validate_environment(item)
    blockers = []
    if host_snapshot_ready is not True: blockers.append("host-snapshot-unavailable")
    if repository_snapshot_ready is not True: blockers.append("repository-snapshot-unavailable")
    # Kept as a compatibility parameter for v1 callers. This is operation-private
    # staging, never a reusable or Environment-visible cache.
    if package_cache_ready is not True: blockers.append("complete-private-staging-unavailable")
    included = tuple(item for item in environments if item.policy == DEFAULT_POLICY)
    excluded = tuple(item.name for item in environments if item.policy == "excluded")
    for item in included:
        if item.state != "stopped": blockers.append(f"environment-running:{item.name}")
        if not item.package_database_ready: blockers.append(f"package-database-unavailable:{item.name}")
        if not item.snapshot_ready: blockers.append(f"snapshot-unavailable:{item.name}")
    targets = (UpdateTarget("host", "host", None, True, True),) + tuple(
        UpdateTarget("environment", item.name, item.generation, True, True) for item in included
    )
    effects = (
        "freeze-one-signed-repository-snapshot",
        "resolve-each-target-against-the-same-repository-snapshot",
        "download-and-verify-the-complete-package-set-before-mutation",
        "stop-included-environments-and-hub-before-activation",
        "snapshot-host-and-each-included-environment-independently",
        "apply-offline-host-first-then-included-environments",
        "stop-on-first-failure-and-retain-all-rollback-sets",
        "verify-boot-runtime-audio-network-and-registration-before-publication",
        "retain-rollbacks-until-separate-retirement",
    )
    raw = {"schema": SCHEMA, "profile": PROFILE, "classification": "blocked" if blockers else "ready-for-approval",
           "targets": [asdict(item) for item in targets], "excluded_environments": list(excluded),
           "blockers": blockers, "effects": list(effects)}
    digest = hashlib.sha256(json.dumps(raw, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return CoordinatedUpdatePlan(SCHEMA, PROFILE, raw["classification"], targets, excluded,
                                 tuple(blockers), effects, digest)
