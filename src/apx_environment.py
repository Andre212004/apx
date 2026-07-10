"""Pure Environment identity and creation-plan policy."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import json
import re
import uuid


REGISTRATION_SCHEMA_VERSION = 1
PLAN_SCHEMA_VERSION = 2
PRIVILEGED_REQUEST_PROTOCOL_VERSION = None
REGISTRATION_ROOT = "/var/lib/apx/environments"
MAX_LOGICAL_NAME_LENGTH = 27
LOGICAL_NAME_PATTERN = re.compile(
    rf"[a-z](?:[a-z0-9]|-(?=[a-z0-9])){{0,{MAX_LOGICAL_NAME_LENGTH - 1}}}"
)
RESERVED_LOGICAL_NAMES = frozenset({"root", "nobody", "system"})


class ContractError(ValueError):
    """A machine-readable APX contract value is invalid."""


class LifecycleState(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class ObservationClassification(str, Enum):
    CONFIRMED = "confirmed"
    NOT_SATISFIED = "not-satisfied"
    UNAVAILABLE = "unavailable"
    AMBIGUOUS = "ambiguous"


class EnvironmentClassification(str, Enum):
    CANDIDATE = "candidate"
    REGISTERED = "registered"
    CONSISTENT = "consistent"
    INCOMPLETE = "incomplete"
    UNCONFIRMED = "unavailable-or-unconfirmed"
    ARCHIVED = "archived"
    ABSENT = "absent"


class CreationStep(str, Enum):
    VALIDATE_IDENTITY = "validate_identity"
    LOAD_REGISTRATION_STATE = "load_registration_state"
    OBSERVE_PRECONDITIONS = "observe_preconditions"
    RESERVE_INCOMPLETE_OPERATION = "reserve_incomplete_operation"
    CREATE_BTRFS_SUBVOLUME = "create_btrfs_subvolume"
    CREATE_LINUX_ACCOUNT = "create_linux_account"
    SET_HOME_OWNERSHIP = "set_home_ownership"
    SET_HOME_PERMISSIONS = "set_home_permissions"
    STAGE_REGISTRATION = "stage_registration"
    VERIFY_RESOURCES = "verify_environment_resources"
    WRITE_REGISTRATION = "write_registration"
    VERIFY_PUBLISHED_ENVIRONMENT = "verify_published_environment"
    COMPLETE_OPERATION = "complete_operation"
    VERIFY_CONSISTENT_ENVIRONMENT = "verify_consistent_environment"


CREATION_STEPS = tuple(CreationStep)


class RollbackClassification(str, Enum):
    NONE_REQUIRED = "none-required"
    AUTOMATICALLY_ELIGIBLE = "automatically-eligible"
    PRESERVE_INCOMPLETE = "preserve-incomplete"


@dataclass(frozen=True)
class StorageIdentity:
    filesystem_type: str
    subvolume_id: int
    subvolume_uuid: str
    parent_uuid: str | None

    def __post_init__(self) -> None:
        if self.filesystem_type != "btrfs":
            raise ContractError("storage filesystem_type must be 'btrfs'")
        if (
            isinstance(self.subvolume_id, bool)
            or not isinstance(self.subvolume_id, int)
            or self.subvolume_id <= 0
        ):
            raise ContractError("storage subvolume_id must be a positive integer")
        for field_name in ("subvolume_uuid", "parent_uuid"):
            value = getattr(self, field_name)
            if value is not None:
                try:
                    canonical = str(uuid.UUID(value))
                except (ValueError, AttributeError) as error:
                    raise ContractError(f"storage {field_name} must be a UUID") from error
                if value != canonical:
                    raise ContractError(f"storage {field_name} must be canonical")


@dataclass(frozen=True)
class EnvironmentRegistration:
    schema_version: int
    logical_name: str
    role: str
    account_name: str
    home_path: str
    lifecycle_state: str
    storage: StorageIdentity

    def __post_init__(self) -> None:
        if self.schema_version != REGISTRATION_SCHEMA_VERSION:
            raise ContractError("unsupported registration schema_version")
        identity = derive_identity(self.logical_name)
        if self.role != identity.role:
            raise ContractError("registration role does not match logical name")
        if self.account_name != identity.account:
            raise ContractError("registration account_name does not match logical name")
        if self.home_path != identity.home:
            raise ContractError("registration home_path does not match logical name")
        if self.lifecycle_state != LifecycleState.ACTIVE.value:
            raise ContractError("registration schema v1 supports only active lifecycle")


REGISTRATION_FIELDS = {
    "schema_version", "logical_name", "role", "account_name",
    "home_path", "lifecycle_state", "storage",
}
STORAGE_FIELDS = {
    "filesystem_type", "subvolume_id", "subvolume_uuid", "parent_uuid",
}


def registration_to_data(registration: EnvironmentRegistration) -> dict[str, object]:
    return {
        "schema_version": registration.schema_version,
        "logical_name": registration.logical_name,
        "role": registration.role,
        "account_name": registration.account_name,
        "home_path": registration.home_path,
        "lifecycle_state": registration.lifecycle_state,
        "storage": asdict(registration.storage),
    }


def serialize_registration(registration: EnvironmentRegistration) -> str:
    return json.dumps(
        registration_to_data(registration),
        ensure_ascii=True,
        indent=2,
        sort_keys=True,
    ) + "\n"


def parse_registration_json(value: str) -> EnvironmentRegistration:
    def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, item in pairs:
            if key in result:
                raise ContractError(f"duplicate registration field: {key}")
            result[key] = item
        return result

    try:
        data = json.loads(value, object_pairs_hook=unique_object)
    except (json.JSONDecodeError, TypeError) as error:
        raise ContractError("registration is not valid JSON") from error
    if not isinstance(data, dict) or set(data) != REGISTRATION_FIELDS:
        raise ContractError("registration fields are missing or unknown")
    storage_data = data.get("storage")
    if not isinstance(storage_data, dict) or set(storage_data) != STORAGE_FIELDS:
        raise ContractError("registration storage fields are missing or unknown")
    expected_types = {
        "schema_version": int,
        "logical_name": str,
        "role": str,
        "account_name": str,
        "home_path": str,
        "lifecycle_state": str,
    }
    if any(
        isinstance(data[field], bool) or not isinstance(data[field], expected)
        for field, expected in expected_types.items()
    ):
        raise ContractError("registration field has the wrong type")
    if (
        not isinstance(storage_data["filesystem_type"], str)
        or isinstance(storage_data["subvolume_id"], bool)
        or not isinstance(storage_data["subvolume_id"], int)
        or not isinstance(storage_data["subvolume_uuid"], str)
        or (
            storage_data["parent_uuid"] is not None
            and not isinstance(storage_data["parent_uuid"], str)
        )
    ):
        raise ContractError("registration storage field has the wrong type")
    storage = StorageIdentity(**storage_data)
    return EnvironmentRegistration(storage=storage, **{
        field: data[field] for field in expected_types
    })


def classify_environment(
    *,
    candidate_present: bool,
    registration: EnvironmentRegistration | None,
    incomplete_operation: bool,
    observations: str,
    confirmed_mismatch: bool,
) -> EnvironmentClassification:
    if incomplete_operation:
        return EnvironmentClassification.INCOMPLETE
    if registration is None:
        return (
            EnvironmentClassification.CANDIDATE
            if candidate_present
            else EnvironmentClassification.ABSENT
        )
    if registration.lifecycle_state == LifecycleState.ARCHIVED.value:
        return EnvironmentClassification.ARCHIVED
    if observations in {
        ObservationClassification.UNAVAILABLE.value,
        ObservationClassification.AMBIGUOUS.value,
    }:
        return EnvironmentClassification.UNCONFIRMED
    if confirmed_mismatch:
        return EnvironmentClassification.INCOMPLETE
    if observations == ObservationClassification.CONFIRMED.value:
        return EnvironmentClassification.CONSISTENT
    raise ContractError("invalid environment observation classification")


def classify_rollback(
    *,
    resource_created_by_operation: bool,
    resource_empty: bool,
    externally_modified: bool,
    user_used: bool,
    registration_published: bool,
) -> RollbackClassification:
    if not resource_created_by_operation:
        return RollbackClassification.NONE_REQUIRED
    if (
        resource_empty
        and not externally_modified
        and not user_used
        and not registration_published
    ):
        return RollbackClassification.AUTOMATICALLY_ELIGIBLE
    return RollbackClassification.PRESERVE_INCOMPLETE


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
    candidate_absent: str
    filesystem_type: str
    filesystem_status: str
    host_confirmation_required: bool
    registration_absent: str = ObservationClassification.UNAVAILABLE.value
    malformed_registration_absent: str = ObservationClassification.UNAVAILABLE.value
    registration_target_absent: str = ObservationClassification.UNAVAILABLE.value
    parent_paths_valid: str = ObservationClassification.UNAVAILABLE.value
    btrfs_context: str = ObservationClassification.UNAVAILABLE.value
    host_observation_authoritative: str = ObservationClassification.UNAVAILABLE.value
    helper_compatible: str = ObservationClassification.UNAVAILABLE.value
    approved_plan_current: str = ObservationClassification.UNAVAILABLE.value
    human_authorization_valid: str = ObservationClassification.UNAVAILABLE.value

    def __post_init__(self) -> None:
        allowed = {item.value for item in ObservationClassification}
        classification_fields = (
            "account_absent", "home_absent", "candidate_absent",
            "filesystem_status", "registration_absent",
            "malformed_registration_absent", "registration_target_absent",
            "parent_paths_valid", "btrfs_context",
            "host_observation_authoritative", "helper_compatible",
            "approved_plan_current", "human_authorization_valid",
        )
        if any(getattr(self, field) not in allowed for field in classification_fields):
            raise ContractError("invalid precondition classification")


@dataclass(frozen=True)
class CreationPostconditions:
    registration_valid: str
    account_exists: str
    account_name_matches: str
    account_home_matches: str
    role_matches: str
    home_directory_exists: str
    dedicated_btrfs_subvolume: str
    storage_identity_matches: str
    ownership_matches: str
    group_matches: str
    mode_matches: str
    registration_host_owned: str
    incomplete_marker_absent: str

    def classification(self) -> EnvironmentClassification:
        values = tuple(asdict(self).values())
        if ObservationClassification.NOT_SATISFIED.value in values:
            return EnvironmentClassification.INCOMPLETE
        if any(
            value in {
                ObservationClassification.UNAVAILABLE.value,
                ObservationClassification.AMBIGUOUS.value,
            }
            for value in values
        ):
            return EnvironmentClassification.UNCONFIRMED
        if all(value == ObservationClassification.CONFIRMED.value for value in values):
            return EnvironmentClassification.CONSISTENT
        raise ContractError("invalid postcondition classification")


@dataclass(frozen=True)
class CreationPlan:
    operation: str
    schema_version: int
    mode: str
    identity: EnvironmentIdentity
    preconditions: CreationPreconditions
    steps: tuple[CreationStep, ...]
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
    values = (
        preconditions.account_absent,
        preconditions.home_absent,
        preconditions.candidate_absent,
        preconditions.filesystem_status,
        preconditions.registration_absent,
        preconditions.malformed_registration_absent,
        preconditions.registration_target_absent,
        preconditions.parent_paths_valid,
        preconditions.btrfs_context,
        preconditions.host_observation_authoritative,
        preconditions.helper_compatible,
        preconditions.approved_plan_current,
        preconditions.human_authorization_valid,
    )
    if ObservationClassification.NOT_SATISFIED.value in values:
        return "blocked"
    if (
        preconditions.filesystem_status == ObservationClassification.CONFIRMED.value
        and preconditions.filesystem_type != "btrfs"
    ):
        return "blocked"
    if any(value != ObservationClassification.CONFIRMED.value for value in values):
        return "requires-host-confirmation"
    return "eligible-for-future-apply"


def create_plan(
    identity: EnvironmentIdentity, preconditions: CreationPreconditions
) -> CreationPlan:
    return CreationPlan(
        operation="environment.create",
        schema_version=PLAN_SCHEMA_VERSION,
        mode="dry-run",
        identity=identity,
        preconditions=preconditions,
        steps=CREATION_STEPS,
        architectural_eligibility=architectural_eligibility(preconditions),
        apply_availability="blocked",
        reason="privileged apply mode is not implemented",
    )


def plan_digest(plan: CreationPlan) -> str:
    digest_contract = {
        "operation": plan.operation,
        "schema_version": plan.schema_version,
        "mode": plan.mode,
        "identity": asdict(plan.identity),
        "preconditions": asdict(plan.preconditions),
        "steps": tuple(step.value for step in plan.steps),
    }
    canonical = json.dumps(
        digest_contract,
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
            f"  Candidate absent: {preconditions.candidate_absent}",
            f"  Registration absent: {preconditions.registration_absent}",
            f"  Malformed registration absent: {preconditions.malformed_registration_absent}",
            f"  Home filesystem: {preconditions.filesystem_type}",
            f"  Filesystem observation: {preconditions.filesystem_status}",
            f"  Host confirmation required: {host_confirmation}",
            "",
            "Planned changes:",
            f"  - Create dedicated Btrfs home subvolume at {identity.home}.",
            f"  - Create Linux account {identity.account}.",
            "  - Apply APX ownership and permission policy.",
            "  - Register the Environment in APX metadata.",
            "  - Verify account, storage, ownership, and registration.",
            f"Typed steps: {', '.join(step.value for step in plan.steps)}",
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
