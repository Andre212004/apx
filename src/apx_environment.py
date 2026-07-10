"""Pure Environment identity and creation-plan policy."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import re


SCHEMA_VERSION = 1
MAX_LOGICAL_NAME_LENGTH = 27
LOGICAL_NAME_PATTERN = re.compile(
    rf"[a-z](?:[a-z0-9]|-(?=[a-z0-9])){{0,{MAX_LOGICAL_NAME_LENGTH - 1}}}"
)
RESERVED_LOGICAL_NAMES = frozenset({"root", "nobody", "system"})


@dataclass(frozen=True)
class EnvironmentIdentity:
    logical_name: str
    account: str
    home: str
    role: str


@dataclass(frozen=True)
class CreationPreconditions:
    account_absent: str
    home_absent: str
    candidate_exists: str
    filesystem_type: str
    filesystem_status: str
    host_confirmation_required: bool


@dataclass(frozen=True)
class CreationPlan:
    operation: str
    schema_version: int
    mode: str
    identity: EnvironmentIdentity
    preconditions: CreationPreconditions
    architectural_eligibility: str
    apply_availability: str
    reason: str


def validate_logical_name(logical_name: str) -> str | None:
    if len(logical_name) > MAX_LOGICAL_NAME_LENGTH:
        return f"must contain at most {MAX_LOGICAL_NAME_LENGTH} characters"
    if logical_name.startswith("apx-"):
        return "must not begin with the derived 'apx-' prefix"
    if logical_name in RESERVED_LOGICAL_NAMES:
        return "is reserved"
    if not LOGICAL_NAME_PATTERN.fullmatch(logical_name):
        return (
            "must begin with a lowercase ASCII letter, contain only lowercase "
            "ASCII letters, digits, or single internal hyphens, and end with "
            "a letter or digit"
        )
    return None


def derive_identity(logical_name: str) -> EnvironmentIdentity:
    error = validate_logical_name(logical_name)
    if error:
        raise ValueError(error)
    role = {
        "hub": "hub",
        "development": "development",
    }.get(logical_name, "standard")
    account = f"apx-{logical_name}"
    return EnvironmentIdentity(
        logical_name=logical_name,
        account=account,
        home=f"/home/{account}",
        role=role,
    )


def architectural_eligibility(preconditions: CreationPreconditions) -> str:
    if (
        preconditions.account_absent == "no"
        or preconditions.home_absent == "no"
        or preconditions.candidate_exists == "yes"
        or (
            preconditions.filesystem_status == "confirmed"
            and preconditions.filesystem_type != "btrfs"
        )
    ):
        return "blocked"
    if (
        preconditions.account_absent != "confirmed"
        or preconditions.home_absent != "confirmed"
        or preconditions.filesystem_status != "confirmed"
        or preconditions.filesystem_type == "unavailable"
    ):
        return "requires-host-confirmation"
    return "eligible-for-future-apply"


def create_plan(
    identity: EnvironmentIdentity, preconditions: CreationPreconditions
) -> CreationPlan:
    return CreationPlan(
        operation="environment.create",
        schema_version=SCHEMA_VERSION,
        mode="dry-run",
        identity=identity,
        preconditions=preconditions,
        architectural_eligibility=architectural_eligibility(preconditions),
        apply_availability="blocked",
        reason="privileged apply mode is not implemented",
    )


def plan_digest(plan: CreationPlan) -> str:
    canonical = json.dumps(
        asdict(plan),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")
    return f"sha256:{hashlib.sha256(canonical).hexdigest()}"


def render_creation_plan(plan: CreationPlan) -> str:
    identity = plan.identity
    preconditions = plan.preconditions
    host_confirmation = "yes" if preconditions.host_confirmation_required else "no"
    return "\n".join(
        (
            "APX Environment creation plan",
            "",
            f"Operation: {plan.operation}",
            f"Schema version: {plan.schema_version}",
            f"Mode: {plan.mode}",
            "",
            "Environment:",
            f"  Logical name: {identity.logical_name}",
            f"  Role: {identity.role}",
            f"  Account: {identity.account}",
            f"  Home: {identity.home}",
            "",
            "Preconditions:",
            "  Name valid: yes",
            f"  Account absent: {preconditions.account_absent}",
            f"  Home absent: {preconditions.home_absent}",
            f"  Candidate exists: {preconditions.candidate_exists}",
            f"  Home filesystem: {preconditions.filesystem_type}",
            f"  Filesystem observation: {preconditions.filesystem_status}",
            f"  Host confirmation required: {host_confirmation}",
            "",
            "Planned changes:",
            f"  - Create Linux account {identity.account}.",
            f"  - Create dedicated Btrfs home subvolume at {identity.home}.",
            "  - Apply APX ownership and permission policy.",
            "  - Register the Environment in APX metadata.",
            "  - Verify account, storage, ownership, and registration.",
            "",
            "Postconditions:",
            f"  - Account resolves to {identity.home}.",
            "  - Home is a dedicated Btrfs subvolume.",
            "  - Ownership matches the derived account.",
            "  - APX registration exists and matches observed state.",
            "",
            "Rollback:",
            "  - Remove only resources created by the incomplete operation when safe.",
            "  - Do not delete pre-existing or user-owned data.",
            "",
            f"Architectural eligibility: {plan.architectural_eligibility}",
            f"Apply availability: {plan.apply_availability}",
            f"Reason: {plan.reason}.",
            f"Plan digest: {plan_digest(plan)}",
            "Digest purpose: future plan binding only; this digest is not authorization.",
        )
    )
