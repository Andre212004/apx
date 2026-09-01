"""Pure APX Hub-to-executor request and approval contracts.

This module performs no observation or mutation.  Authenticity and host-state
evidence are inputs from future trusted components, not claims made here.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import re

from apx_environment import validate_logical_name


REQUEST_SCHEMA_VERSION = 1
PROTOCOL_VERSION = "apx-executor-v1"
MAX_REQUEST_BYTES = 4096
MAX_APPROVAL_LIFETIME_SECONDS = 300

OPERATION_KINDS = (
    "activate",
    "archive",
    "configure-capabilities",
    "create",
    "destroy",
    "force-stop",
    "recover-cleanup",
    "recover-complete",
    "restore",
    "snapshot",
    "stop",
)

HUB_ROLES = ("hub", "hub-graphical")
REQUESTER_ROLES = (
    "development", "graphical-base", "graphical-h0", "hub", "hub-graphical",
    "minimal", "standard",
)
HUB_ONLY_OPERATIONS = tuple(kind for kind in OPERATION_KINDS if kind != "stop")

APPROVAL_CLASSES = (
    "unlocked-session",
    "explicit-confirmation",
    "strong-confirmation",
)

APPROVAL_BY_OPERATION = {
    "activate": "unlocked-session",
    "archive": "explicit-confirmation",
    "configure-capabilities": "explicit-confirmation",
    "create": "explicit-confirmation",
    "destroy": "strong-confirmation",
    "force-stop": "strong-confirmation",
    "recover-cleanup": "strong-confirmation",
    "recover-complete": "explicit-confirmation",
    "restore": "explicit-confirmation",
    "snapshot": "explicit-confirmation",
    "stop": "unlocked-session",
}

EFFECTS_BY_OPERATION = {
    "activate": (
        "verify-inactive-generation",
        "create-bounded-runtime",
        "apply-fixed-isolation-policy",
        "verify-active-runtime",
    ),
    "archive": (
        "verify-immutable-snapshot-set",
        "create-bounded-archive-staging",
        "verify-complete-archive",
        "publish-immutable-archive",
    ),
    "configure-capabilities": (
        "verify-stopped-generation-and-current-capability-policy",
        "write-generation-bound-capability-policy",
        "verify-policy-before-next-activation",
        "atomically-publish-capability-policy",
    ),
    "create": (
        "verify-absence-and-approved-release",
        "reserve-operation-journal",
        "create-fresh-root-home-and-identity",
        "apply-fixed-policy-and-limits",
        "verify-and-publish-registration",
    ),
    "destroy": (
        "verify-inactive-generation-and-data-loss-scope",
        "delete-approved-environment-owned-leaves",
        "verify-protected-neighbours",
        "remove-registration-last",
        "verify-logical-absence",
    ),
    "force-stop": (
        "verify-active-generation-and-work-loss-warning",
        "terminate-approved-environment-runtime",
        "verify-complete-teardown",
    ),
    "recover-cleanup": (
        "classify-incomplete-operation-resources",
        "delete-only-approved-proven-operation-owned-resources",
        "verify-protected-neighbours-and-result",
    ),
    "recover-complete": (
        "revalidate-incomplete-operation",
        "perform-only-approved-remaining-effects",
        "verify-and-finalize-result",
    ),
    "restore": (
        "verify-source-artifact-and-target-absence",
        "create-fresh-target-identities",
        "restore-and-sanitize-persistent-state",
        "verify-and-publish-new-registration",
    ),
    "snapshot": (
        "verify-inactive-generation-and-quota-health",
        "create-read-only-root-home-snapshots",
        "verify-consistent-snapshot-set",
        "publish-immutable-snapshot-manifest",
    ),
    "stop": (
        "verify-active-generation",
        "request-graceful-environment-stop",
        "verify-complete-teardown",
    ),
}

CONSEQUENCES_BY_OPERATION = {
    "activate": ("opens-selected-environment", "uses-declared-resources"),
    "archive": ("uses-additional-storage", "creates-retained-copy"),
    "configure-capabilities": (
        "changes-devices-available-on-next-activation",
        "may-grant-camera-microphone-controller-or-removable-storage",
    ),
    "create": ("uses-additional-storage", "creates-new-independent-environment"),
    "destroy": (
        "deletes-environment-root-and-home",
        "cannot-be-undone-without-retained-artifact",
        "retained-artifacts-are-not-deleted",
    ),
    "force-stop": ("may-lose-unsaved-work", "terminates-environment-processes"),
    "recover-cleanup": ("deletes-listed-incomplete-resources",),
    "recover-complete": ("continues-previously-interrupted-operation",),
    "restore": ("uses-additional-storage", "creates-new-environment-identity"),
    "snapshot": ("requires-environment-stopped", "uses-additional-storage"),
    "stop": ("closes-selected-environment",),
}

_HEX_32 = re.compile(r"[0-9a-f]{32}")
_HEX_64 = re.compile(r"[0-9a-f]{64}")
_UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}")
Generation = int | str


class ExecutorContractError(ValueError):
    """A request is malformed or outside the closed executor protocol."""


@dataclass(frozen=True)
class OperationPlan:
    schema_version: int
    protocol_version: str
    operation_kind: str
    logical_name: str
    expected_generation: Generation
    policy_version: str
    effects: tuple[str, ...]
    consequences: tuple[str, ...]
    required_approval_class: str
    consequence_digest: str
    plan_digest: str


@dataclass(frozen=True)
class ExecutorRequest:
    schema_version: int
    protocol_version: str
    operation_id: str
    operation_kind: str
    logical_name: str
    expected_generation: Generation
    plan_digest: str
    approval_id: str
    nonce: str
    expires_at: int


@dataclass(frozen=True)
class ApprovalEvidence:
    approval_id: str
    operation_id: str
    operation_kind: str
    logical_name: str
    expected_generation: Generation
    plan_digest: str
    consequence_digest: str
    approval_class: str
    session_id: str
    nonce: str
    issued_at: int
    not_before: int
    expires_at: int
    authenticity_verified: bool


@dataclass(frozen=True)
class RequesterContext:
    """Trusted session facts supplied by the executor, never by the UI request."""

    session_id: str
    logical_name: str
    role: str
    generation: Generation
    authenticated: bool
    active: bool
    authoritative: bool


@dataclass(frozen=True)
class RequestAssessment:
    classification: str
    issues: tuple[str, ...]
    request_digest: str


REQUEST_FIELDS = {
    "approval_id",
    "expected_generation",
    "expires_at",
    "logical_name",
    "nonce",
    "operation_id",
    "operation_kind",
    "plan_digest",
    "protocol_version",
    "schema_version",
}


def _canonical_digest(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _valid_generation(value: object, *, allow_absent: bool) -> bool:
    """Accept legacy lab serials and exact physical UUIDv4 generations."""
    if type(value) is int:
        return value == 0 if allow_absent and value == 0 else value > 0
    return isinstance(value, str) and _UUID.fullmatch(value) is not None


def build_operation_plan(
    operation_kind: str,
    logical_name: str,
    expected_generation: Generation,
    *,
    policy_version: str = "environment-boundary-v1",
) -> OperationPlan:
    if operation_kind not in OPERATION_KINDS:
        raise ExecutorContractError("unsupported executor operation")
    name_issue = validate_logical_name(logical_name)
    if name_issue is not None:
        raise ExecutorContractError(f"invalid Environment name: {name_issue}")
    if not _valid_generation(expected_generation, allow_absent=True):
        raise ExecutorContractError("expected generation must be zero or a canonical physical UUID")
    if operation_kind in {"create", "restore"} and expected_generation != 0:
        raise ExecutorContractError("creation and restore require absent generation zero")
    if operation_kind not in {"create", "restore"} and expected_generation == 0:
        raise ExecutorContractError("existing Environment operation requires a generation")
    if policy_version != "environment-boundary-v1":
        raise ExecutorContractError("unsupported isolation policy version")

    effects = EFFECTS_BY_OPERATION[operation_kind]
    consequences = CONSEQUENCES_BY_OPERATION[operation_kind]
    consequence_digest = _canonical_digest(consequences)
    subject = {
        "consequence_digest": consequence_digest,
        "consequences": consequences,
        "effects": effects,
        "expected_generation": expected_generation,
        "logical_name": logical_name,
        "operation_kind": operation_kind,
        "policy_version": policy_version,
        "protocol_version": PROTOCOL_VERSION,
        "required_approval_class": APPROVAL_BY_OPERATION[operation_kind],
        "schema_version": REQUEST_SCHEMA_VERSION,
    }
    return OperationPlan(
        schema_version=REQUEST_SCHEMA_VERSION,
        protocol_version=PROTOCOL_VERSION,
        operation_kind=operation_kind,
        logical_name=logical_name,
        expected_generation=expected_generation,
        policy_version=policy_version,
        effects=effects,
        consequences=consequences,
        required_approval_class=APPROVAL_BY_OPERATION[operation_kind],
        consequence_digest=consequence_digest,
        plan_digest=_canonical_digest(subject),
    )


def request_to_json(request: ExecutorRequest) -> str:
    return json.dumps(asdict(request), sort_keys=True, separators=(",", ":")) + "\n"


def parse_executor_request_json(text: str) -> ExecutorRequest:
    if not isinstance(text, str):
        raise ExecutorContractError("executor request must be text")
    try:
        size = len(text.encode("utf-8"))
    except UnicodeEncodeError as error:
        raise ExecutorContractError("executor request is not valid UTF-8") from error
    if size > MAX_REQUEST_BYTES:
        raise ExecutorContractError("executor request exceeds size limit")

    def unique_fields(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ExecutorContractError(f"duplicate executor request field: {key}")
            result[key] = value
        return result

    try:
        payload = json.loads(text, object_pairs_hook=unique_fields)
    except (json.JSONDecodeError, UnicodeError) as error:
        raise ExecutorContractError("executor request is not valid JSON") from error
    if not isinstance(payload, dict) or set(payload) != REQUEST_FIELDS:
        raise ExecutorContractError("executor request fields are missing or unknown")

    string_fields = REQUEST_FIELDS - {"schema_version", "expected_generation", "expires_at"}
    for field in string_fields:
        if type(payload[field]) is not str:
            raise ExecutorContractError(f"executor request field {field} has wrong type")
    for field in ("schema_version", "expires_at"):
        if type(payload[field]) is not int:
            raise ExecutorContractError(f"executor request field {field} has wrong type")
    if not _valid_generation(payload["expected_generation"], allow_absent=True):
        raise ExecutorContractError("executor request generation has wrong type or format")
    request = ExecutorRequest(**payload)
    _validate_request_structure(request)
    return request


def _validate_request_structure(request: ExecutorRequest) -> None:
    if request.schema_version != REQUEST_SCHEMA_VERSION:
        raise ExecutorContractError("unsupported executor request schema")
    if request.protocol_version != PROTOCOL_VERSION:
        raise ExecutorContractError("unsupported executor protocol")
    if request.operation_kind not in OPERATION_KINDS:
        raise ExecutorContractError("unsupported executor operation")
    if validate_logical_name(request.logical_name) is not None:
        raise ExecutorContractError("invalid Environment name")
    if not _valid_generation(request.expected_generation, allow_absent=True):
        raise ExecutorContractError("expected generation is not zero or a canonical physical UUID")
    if not request.operation_id.startswith("op-") or not _HEX_32.fullmatch(request.operation_id[3:]):
        raise ExecutorContractError("operation ID is not canonical")
    if not request.approval_id.startswith("approval-") or not _HEX_32.fullmatch(request.approval_id[9:]):
        raise ExecutorContractError("approval ID is not canonical")
    if not _HEX_64.fullmatch(request.plan_digest):
        raise ExecutorContractError("plan digest is malformed")
    if not _HEX_64.fullmatch(request.nonce):
        raise ExecutorContractError("nonce is malformed")
    if request.expires_at <= 0:
        raise ExecutorContractError("request expiry is invalid")


def assess_executor_request(
    request: ExecutorRequest,
    plan: OperationPlan,
    approval: ApprovalEvidence,
    *,
    current_generation: Generation,
    current_time: int,
    current_session_id: str,
    nonce_state: str,
    authoritative_state: str,
    requester_context: RequesterContext,
) -> RequestAssessment:
    """Assess exact binding only; perform no authentication, observation, or effect."""

    issues: list[str] = []
    try:
        _validate_request_structure(request)
    except ExecutorContractError as error:
        issues.append(str(error))

    try:
        expected_plan = build_operation_plan(
            plan.operation_kind,
            plan.logical_name,
            plan.expected_generation,
            policy_version=plan.policy_version,
        )
        if plan != expected_plan:
            issues.append("plan differs from the fixed reviewed operation")
    except ExecutorContractError:
        issues.append("plan is not a supported fixed operation")

    if request.operation_kind != plan.operation_kind:
        issues.append("request operation does not match plan")
    if request.logical_name != plan.logical_name:
        issues.append("request Environment does not match plan")
    if request.expected_generation != plan.expected_generation:
        issues.append("request generation does not match plan")
    if request.plan_digest != plan.plan_digest:
        issues.append("request digest does not match plan")
    if not _valid_generation(current_generation, allow_absent=True):
        issues.append("current generation evidence is malformed")
    elif current_generation != request.expected_generation:
        issues.append("current Environment generation is stale or different")
    if authoritative_state != "confirmed-compatible":
        issues.append("current authoritative state is not confirmed compatible")

    context_session_valid = (
        type(requester_context.session_id) is str
        and requester_context.session_id.startswith("session-")
        and _HEX_32.fullmatch(requester_context.session_id[8:]) is not None
    )
    if not context_session_valid:
        issues.append("requester session ID is not canonical")
    if requester_context.session_id != current_session_id:
        issues.append("requester is not the current session")
    if validate_logical_name(requester_context.logical_name) is not None:
        issues.append("requester Environment name is invalid")
    if requester_context.role not in REQUESTER_ROLES:
        issues.append("requester Environment role is unsupported")
    elif (
        (requester_context.logical_name == "hub")
        != (requester_context.role in HUB_ROLES)
    ):
        issues.append("requester Hub identity and role are inconsistent")
    if not _valid_generation(requester_context.generation, allow_absent=False):
        issues.append("requester generation evidence is malformed")
    if requester_context.authenticated is not True:
        issues.append("requester session is not authenticated")
    if requester_context.active is not True:
        issues.append("requester Environment is not active")
    if requester_context.authoritative is not True:
        issues.append("requester context is not authoritative")

    requester_is_hub = requester_context.role in HUB_ROLES
    if request.operation_kind in HUB_ONLY_OPERATIONS and not requester_is_hub:
        issues.append("operation is restricted to the active Hub")
    if request.operation_kind == "stop" and not requester_is_hub:
        if (
            requester_context.logical_name != request.logical_name
            or requester_context.generation != request.expected_generation
        ):
            issues.append("non-Hub requester may stop only its own active generation")
    if nonce_state != "unused":
        issues.append("nonce is unavailable or already used")
    current_time_valid = type(current_time) is int and current_time >= 0
    if not current_time_valid:
        issues.append("current trusted time is malformed")
    elif current_time > request.expires_at:
        issues.append("request has expired")

    bindings = (
        (approval.approval_id, request.approval_id, "approval ID"),
        (approval.operation_id, request.operation_id, "operation ID"),
        (approval.operation_kind, request.operation_kind, "operation"),
        (approval.logical_name, request.logical_name, "Environment"),
        (approval.expected_generation, request.expected_generation, "generation"),
        (approval.plan_digest, request.plan_digest, "plan digest"),
        (approval.consequence_digest, plan.consequence_digest, "consequence digest"),
        (approval.approval_class, plan.required_approval_class, "approval class"),
        (approval.nonce, request.nonce, "nonce"),
        (approval.expires_at, request.expires_at, "expiry"),
    )
    for actual, expected, label in bindings:
        if actual != expected:
            issues.append(f"approval {label} does not match")

    if approval.authenticity_verified is not True:
        issues.append("approval authenticity is not verified")
    if (
        type(approval.session_id) is not str
        or not approval.session_id.startswith("session-")
        or not _HEX_32.fullmatch(approval.session_id[8:])
    ):
        issues.append("approval session ID is not canonical")
    if approval.session_id != current_session_id:
        issues.append("approval does not belong to the current unlocked session")
    if approval.session_id != requester_context.session_id:
        issues.append("approval does not belong to the requester session")
    approval_times_valid = all(
        type(value) is int and value >= 0
        for value in (approval.issued_at, approval.not_before, approval.expires_at)
    )
    if not approval_times_valid:
        issues.append("approval timing evidence is malformed")
    else:
        if approval.issued_at > approval.not_before:
            issues.append("approval timing is internally inconsistent")
        if approval.not_before > approval.expires_at:
            issues.append("approval expiry precedes its validity window")
        if approval.expires_at - approval.issued_at > MAX_APPROVAL_LIFETIME_SECONDS:
            issues.append("approval lifetime exceeds the fixed limit")
        if current_time_valid and current_time < approval.not_before:
            issues.append("approval is not valid yet")
        if current_time_valid and current_time > approval.expires_at:
            issues.append("approval has expired")

    request_digest = _canonical_digest(asdict(request))
    return RequestAssessment(
        classification="authorized-contract" if not issues else "rejected",
        issues=tuple(dict.fromkeys(issues)),
        request_digest=request_digest,
    )
