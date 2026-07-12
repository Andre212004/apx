"""Durable-operation journal contract and repository-only fixture store.

The state machine is production-oriented.  ``FixtureJournalStore`` exists only
for Level 2 tests in caller-provided disposable directories; it never selects a
host APX path or performs an APX lifecycle effect.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
from typing import Sequence

from apx_executor_contract import OperationPlan, PROTOCOL_VERSION


JOURNAL_SCHEMA_VERSION = 1
MAX_JOURNAL_BYTES = 64 * 1024
MAX_RESOURCES = 64
MAX_EFFECTS = 32

JOURNAL_STATUSES = (
    "reserved",
    "executing",
    "effect-prepared",
    "verifying-final",
    "complete",
    "incomplete",
)
RECOVERY_CLASSES = (
    "none",
    "no-effect",
    "continuation-eligible",
    "automatic-rollback-eligible",
    "preserve-recovery-required",
    "preserve-identity-uncertain",
    "preserve-effect-outcome-uncertain",
)
RESOURCE_TYPES = (
    "account",
    "archive",
    "home",
    "metadata",
    "network",
    "registration",
    "root",
    "runtime",
    "snapshot",
)
RESOURCE_STATES = (
    "not-created",
    "owned-empty",
    "owned-modified",
    "published",
    "foreign-or-conflicting",
    "identity-uncertain",
)

_OPERATION_ID = re.compile(r"op-[0-9a-f]{32}")
_APPROVAL_ID = re.compile(r"approval-[0-9a-f]{32}")
_SAFE_ID = re.compile(r"[a-z0-9][a-z0-9.-]{0,127}")
_SHA256 = re.compile(r"[0-9a-f]{64}")


class JournalError(ValueError):
    """Journal content or transition is unsafe or invalid."""


class JournalStoreError(RuntimeError):
    """Fixture storage could not prove a safe atomic operation."""


@dataclass(frozen=True)
class JournalResource:
    resource_id: str
    resource_type: str
    identity_digest: str | None
    state: str
    published: bool
    used: bool
    modified: bool


@dataclass(frozen=True)
class OperationJournal:
    schema_version: int
    protocol_version: str
    operation_id: str
    operation_kind: str
    logical_name: str
    expected_generation: int
    plan_digest: str
    request_digest: str
    approval_id: str
    nonce_digest: str
    policy_version: str
    effects: tuple[str, ...]
    completed_effects: tuple[str, ...]
    prepared_effect: str | None
    resources: tuple[JournalResource, ...]
    status: str
    recovery_class: str
    final_evidence_digest: str | None
    failure_reason: str | None
    sequence: int
    previous_digest: str | None
    journal_digest: str


@dataclass(frozen=True)
class RecoveryAssessment:
    classification: str
    explanation: str
    automatic_deletion_allowed: bool
    continuation_allowed: bool


JOURNAL_FIELDS = frozenset(OperationJournal.__dataclass_fields__)
RESOURCE_FIELDS = frozenset(JournalResource.__dataclass_fields__)


def _digest_payload(journal: OperationJournal) -> dict[str, object]:
    payload = asdict(journal)
    payload.pop("journal_digest")
    return payload


def compute_journal_digest(journal: OperationJournal) -> str:
    encoded = json.dumps(
        _digest_payload(journal), sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _with_digest(journal: OperationJournal) -> OperationJournal:
    return replace(journal, journal_digest=compute_journal_digest(journal))


def _next(journal: OperationJournal, **changes: object) -> OperationJournal:
    candidate = replace(
        journal,
        sequence=journal.sequence + 1,
        previous_digest=journal.journal_digest,
        journal_digest="",
        **changes,
    )
    candidate = _with_digest(candidate)
    validate_journal(candidate)
    return candidate


def create_journal(
    plan: OperationPlan,
    *,
    operation_id: str,
    request_digest: str,
    approval_id: str,
    nonce_digest: str,
) -> OperationJournal:
    if not _OPERATION_ID.fullmatch(operation_id):
        raise JournalError("operation ID is not canonical")
    if not _APPROVAL_ID.fullmatch(approval_id):
        raise JournalError("approval ID is not canonical")
    for label, value in (
        ("plan", plan.plan_digest),
        ("request", request_digest),
        ("nonce", nonce_digest),
    ):
        if not _SHA256.fullmatch(value):
            raise JournalError(f"{label} digest is malformed")
    journal = OperationJournal(
        schema_version=JOURNAL_SCHEMA_VERSION,
        protocol_version=PROTOCOL_VERSION,
        operation_id=operation_id,
        operation_kind=plan.operation_kind,
        logical_name=plan.logical_name,
        expected_generation=plan.expected_generation,
        plan_digest=plan.plan_digest,
        request_digest=request_digest,
        approval_id=approval_id,
        nonce_digest=nonce_digest,
        policy_version=plan.policy_version,
        effects=plan.effects,
        completed_effects=(),
        prepared_effect=None,
        resources=(),
        status="reserved",
        recovery_class="none",
        final_evidence_digest=None,
        failure_reason=None,
        sequence=0,
        previous_digest=None,
        journal_digest="",
    )
    journal = _with_digest(journal)
    validate_journal(journal)
    return journal


def prepare_next_effect(journal: OperationJournal) -> OperationJournal:
    validate_journal(journal)
    if journal.status not in {"reserved", "executing"}:
        raise JournalError("journal is not eligible to prepare an effect")
    if journal.prepared_effect is not None:
        raise JournalError("an effect is already prepared")
    index = len(journal.completed_effects)
    if index >= len(journal.effects):
        raise JournalError("all effects are already complete")
    return _next(
        journal,
        status="effect-prepared",
        prepared_effect=journal.effects[index],
    )


def record_effect_success(
    journal: OperationJournal,
    *,
    resources: Sequence[JournalResource] = (),
) -> OperationJournal:
    validate_journal(journal)
    if journal.status != "effect-prepared" or journal.prepared_effect is None:
        raise JournalError("no prepared effect can be completed")
    merged = _merge_resources(journal.resources, tuple(resources))
    return _next(
        journal,
        status="executing",
        completed_effects=journal.completed_effects + (journal.prepared_effect,),
        prepared_effect=None,
        resources=merged,
    )


def begin_final_verification(journal: OperationJournal) -> OperationJournal:
    validate_journal(journal)
    if journal.status != "executing":
        raise JournalError("journal is not ready for final verification")
    if journal.prepared_effect is not None or journal.completed_effects != journal.effects:
        raise JournalError("all ordered effects must complete before verification")
    return _next(journal, status="verifying-final")


def complete_journal(
    journal: OperationJournal, *, final_evidence_digest: str
) -> OperationJournal:
    validate_journal(journal)
    if journal.status != "verifying-final":
        raise JournalError("journal is not in final verification")
    if not _SHA256.fullmatch(final_evidence_digest):
        raise JournalError("final evidence digest is malformed")
    return _next(
        journal,
        status="complete",
        recovery_class="none",
        final_evidence_digest=final_evidence_digest,
    )


def mark_incomplete(journal: OperationJournal, *, reason: str) -> OperationJournal:
    validate_journal(journal)
    if journal.status in {"complete", "incomplete"}:
        raise JournalError("terminal journal cannot be marked incomplete again")
    if not reason or len(reason) > 160 or any(not char.isprintable() for char in reason):
        raise JournalError("failure reason is invalid")
    recovery = assess_recovery(journal, approval_still_valid=False, gates_confirmed=False)
    return _next(
        journal,
        status="incomplete",
        recovery_class=recovery.classification,
        failure_reason=reason,
    )


def _merge_resources(
    current: tuple[JournalResource, ...], new: tuple[JournalResource, ...]
) -> tuple[JournalResource, ...]:
    merged = {resource.resource_id: resource for resource in current}
    for resource in new:
        validate_resource(resource)
        existing = merged.get(resource.resource_id)
        if existing is not None and existing.identity_digest != resource.identity_digest:
            raise JournalError("resource identity changed during operation")
        merged[resource.resource_id] = resource
    result = tuple(sorted(merged.values(), key=lambda item: item.resource_id))
    if len(result) > MAX_RESOURCES:
        raise JournalError("journal resource count exceeds limit")
    return result


def validate_resource(resource: JournalResource) -> None:
    if not _SAFE_ID.fullmatch(resource.resource_id):
        raise JournalError("resource ID is unsafe")
    if resource.resource_type not in RESOURCE_TYPES:
        raise JournalError("resource type is unsupported")
    if resource.identity_digest is not None and not _SHA256.fullmatch(resource.identity_digest):
        raise JournalError("resource identity digest is malformed")
    if resource.state not in RESOURCE_STATES:
        raise JournalError("resource state is unsupported")
    if any(type(value) is not bool for value in (resource.published, resource.used, resource.modified)):
        raise JournalError("resource flags must be booleans")
    if resource.state == "not-created" and any((resource.published, resource.used, resource.modified)):
        raise JournalError("not-created resource cannot have lifecycle flags")
    if resource.published and resource.state != "published":
        raise JournalError("published resource state does not match flag")
    if resource.state == "published" and not resource.published:
        raise JournalError("published resource must set published flag")


def validate_journal(journal: OperationJournal) -> None:
    if journal.schema_version != JOURNAL_SCHEMA_VERSION:
        raise JournalError("unsupported journal schema")
    if journal.protocol_version != PROTOCOL_VERSION:
        raise JournalError("unsupported executor protocol")
    if not _OPERATION_ID.fullmatch(journal.operation_id):
        raise JournalError("operation ID is not canonical")
    if not _APPROVAL_ID.fullmatch(journal.approval_id):
        raise JournalError("approval ID is not canonical")
    for value in (
        journal.plan_digest,
        journal.request_digest,
        journal.nonce_digest,
        journal.journal_digest,
    ):
        if not _SHA256.fullmatch(value):
            raise JournalError("journal contains malformed digest")
    for value in (journal.previous_digest, journal.final_evidence_digest):
        if value is not None and not _SHA256.fullmatch(value):
            raise JournalError("journal contains malformed optional digest")
    if journal.status not in JOURNAL_STATUSES:
        raise JournalError("unsupported journal status")
    if journal.recovery_class not in RECOVERY_CLASSES:
        raise JournalError("unsupported recovery class")
    if type(journal.expected_generation) is not int or journal.expected_generation < 0:
        raise JournalError("journal generation is invalid")
    if type(journal.sequence) is not int or journal.sequence < 0:
        raise JournalError("journal sequence is invalid")
    if len(journal.effects) == 0 or len(journal.effects) > MAX_EFFECTS:
        raise JournalError("journal effect count is invalid")
    if len(set(journal.effects)) != len(journal.effects):
        raise JournalError("journal effects must be unique")
    if journal.completed_effects != journal.effects[: len(journal.completed_effects)]:
        raise JournalError("completed effects are not an exact ordered prefix")
    if journal.prepared_effect is not None:
        index = len(journal.completed_effects)
        if index >= len(journal.effects) or journal.prepared_effect != journal.effects[index]:
            raise JournalError("prepared effect is not the exact next effect")
    if (journal.status == "effect-prepared") != (journal.prepared_effect is not None):
        raise JournalError("prepared effect and journal status disagree")
    if journal.status == "complete":
        if journal.completed_effects != journal.effects or journal.final_evidence_digest is None:
            raise JournalError("complete journal lacks effects or final evidence")
    if journal.status != "complete" and journal.final_evidence_digest is not None:
        raise JournalError("non-complete journal cannot have final evidence")
    if journal.status == "incomplete" and journal.failure_reason is None:
        raise JournalError("incomplete journal lacks failure reason")
    if journal.status != "incomplete" and journal.failure_reason is not None:
        raise JournalError("non-incomplete journal cannot have failure reason")
    if len(journal.resources) > MAX_RESOURCES:
        raise JournalError("journal resource count exceeds limit")
    resource_ids = [resource.resource_id for resource in journal.resources]
    if resource_ids != sorted(resource_ids) or len(resource_ids) != len(set(resource_ids)):
        raise JournalError("journal resources are duplicated or non-canonical")
    for resource in journal.resources:
        validate_resource(resource)
    if compute_journal_digest(journal) != journal.journal_digest:
        raise JournalError("journal digest does not match content")


def assess_recovery(
    journal: OperationJournal,
    *,
    approval_still_valid: bool,
    gates_confirmed: bool,
) -> RecoveryAssessment:
    validate_journal(journal)
    if journal.status == "complete":
        return RecoveryAssessment("none", "Operation is already complete.", False, False)
    if journal.prepared_effect is not None:
        return RecoveryAssessment(
            "preserve-effect-outcome-uncertain",
            "A prepared effect may or may not have changed external state.",
            False,
            False,
        )
    if not journal.completed_effects and not journal.resources:
        return RecoveryAssessment("no-effect", "No external effect is recorded.", False, False)
    if any(resource.state in {"foreign-or-conflicting", "identity-uncertain"} for resource in journal.resources):
        return RecoveryAssessment(
            "preserve-identity-uncertain",
            "At least one resource identity or ownership is uncertain.",
            False,
            False,
        )
    if any(resource.published or resource.used or resource.modified for resource in journal.resources):
        return RecoveryAssessment(
            "preserve-recovery-required",
            "Published, used, or modified resources require explicit recovery.",
            False,
            False,
        )
    if journal.resources and all(resource.state == "owned-empty" for resource in journal.resources):
        return RecoveryAssessment(
            "automatic-rollback-eligible",
            "All observed resources are operation-owned, empty, and unpublished.",
            True,
            False,
        )
    if approval_still_valid is True and gates_confirmed is True and journal.status in {"reserved", "executing", "verifying-final"}:
        return RecoveryAssessment(
            "continuation-eligible",
            "The exact approval and all current gates permit continuation.",
            False,
            True,
        )
    return RecoveryAssessment(
        "preserve-recovery-required",
        "Current evidence does not permit automatic deletion or continuation.",
        False,
        False,
    )


def serialize_journal(journal: OperationJournal) -> str:
    validate_journal(journal)
    return json.dumps(asdict(journal), sort_keys=True, separators=(",", ":")) + "\n"


def _unique_fields(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise JournalError(f"duplicate journal field: {key}")
        result[key] = value
    return result


def parse_journal(text: str) -> OperationJournal:
    if not isinstance(text, str):
        raise JournalError("journal must be text")
    if len(text.encode("utf-8")) > MAX_JOURNAL_BYTES:
        raise JournalError("journal exceeds size limit")
    try:
        payload = json.loads(text, object_pairs_hook=_unique_fields)
    except (json.JSONDecodeError, UnicodeError) as error:
        raise JournalError("journal is not valid JSON") from error
    if not isinstance(payload, dict) or set(payload) != JOURNAL_FIELDS:
        raise JournalError("journal fields are missing or unknown")
    resources = payload.get("resources")
    if not isinstance(resources, list) or len(resources) > MAX_RESOURCES:
        raise JournalError("journal resources are malformed or excessive")
    parsed_resources: list[JournalResource] = []
    for item in resources:
        if not isinstance(item, dict) or set(item) != RESOURCE_FIELDS:
            raise JournalError("journal resource fields are missing or unknown")
        parsed_resources.append(JournalResource(**item))
    for field in ("effects", "completed_effects"):
        value = payload[field]
        if not isinstance(value, list) or any(type(item) is not str for item in value):
            raise JournalError(f"journal {field} is malformed")
        payload[field] = tuple(value)
    payload["resources"] = tuple(parsed_resources)
    try:
        journal = OperationJournal(**payload)
    except TypeError as error:
        raise JournalError("journal field types are invalid") from error
    validate_journal(journal)
    return journal


class FixtureJournalStore:
    """Atomic journal storage for disposable repository tests only."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)

    def _open_root(self) -> int:
        flags = os.O_RDONLY | os.O_DIRECTORY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            return os.open(self.root, flags)
        except OSError as error:
            raise JournalStoreError("fixture journal root is unavailable or unsafe") from error

    @staticmethod
    def _filename(operation_id: str) -> str:
        if not _OPERATION_ID.fullmatch(operation_id):
            raise JournalStoreError("operation ID cannot form a fixture filename")
        return f"{operation_id}.json"

    @staticmethod
    def _write_temp(directory_fd: int, filename: str, content: bytes) -> str:
        temp_name = f".{filename}.{os.getpid()}.tmp"
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        fd = os.open(temp_name, flags, 0o600, dir_fd=directory_fd)
        try:
            view = memoryview(content)
            while view:
                written = os.write(fd, view)
                if written <= 0:
                    raise JournalStoreError("fixture journal write did not progress")
                view = view[written:]
            os.fsync(fd)
        except BaseException:
            try:
                os.unlink(temp_name, dir_fd=directory_fd)
            except OSError:
                pass
            raise
        finally:
            os.close(fd)
        return temp_name

    def create(self, journal: OperationJournal) -> None:
        content = serialize_journal(journal).encode("utf-8")
        filename = self._filename(journal.operation_id)
        directory_fd = self._open_root()
        try:
            fcntl.flock(directory_fd, fcntl.LOCK_EX)
            temp_name = self._write_temp(directory_fd, filename, content)
            try:
                os.link(
                    temp_name,
                    filename,
                    src_dir_fd=directory_fd,
                    dst_dir_fd=directory_fd,
                    follow_symlinks=False,
                )
            except FileExistsError as error:
                raise JournalStoreError("fixture journal already exists") from error
            finally:
                os.unlink(temp_name, dir_fd=directory_fd)
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)

    def read(self, operation_id: str) -> OperationJournal:
        filename = self._filename(operation_id)
        directory_fd = self._open_root()
        try:
            return self._read_locked(directory_fd, filename)
        finally:
            os.close(directory_fd)

    @staticmethod
    def _read_locked(directory_fd: int, filename: str) -> OperationJournal:
        flags = os.O_RDONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            fd = os.open(filename, flags, dir_fd=directory_fd)
        except OSError as error:
            raise JournalStoreError("fixture journal cannot be opened safely") from error
        try:
            metadata = os.fstat(fd)
            if not stat.S_ISREG(metadata.st_mode):
                raise JournalStoreError("fixture journal is not a regular file")
            if stat.S_IMODE(metadata.st_mode) != 0o600:
                raise JournalStoreError("fixture journal mode is not 0600")
            chunks: list[bytes] = []
            total = 0
            while True:
                chunk = os.read(fd, min(8192, MAX_JOURNAL_BYTES + 1 - total))
                if not chunk:
                    break
                chunks.append(chunk)
                total += len(chunk)
                if total > MAX_JOURNAL_BYTES:
                    raise JournalStoreError("fixture journal exceeds size limit")
        finally:
            os.close(fd)
        try:
            return parse_journal(b"".join(chunks).decode("utf-8"))
        except (UnicodeDecodeError, JournalError) as error:
            raise JournalStoreError("fixture journal content is invalid") from error

    def update(self, journal: OperationJournal, *, expected_previous_digest: str) -> None:
        if journal.previous_digest != expected_previous_digest:
            raise JournalStoreError("new journal does not bind expected prior state")
        content = serialize_journal(journal).encode("utf-8")
        filename = self._filename(journal.operation_id)
        directory_fd = self._open_root()
        try:
            fcntl.flock(directory_fd, fcntl.LOCK_EX)
            current = self._read_locked(directory_fd, filename)
            if current.journal_digest != expected_previous_digest:
                raise JournalStoreError("fixture journal changed since it was read")
            temp_name = self._write_temp(directory_fd, filename, content)
            try:
                os.replace(
                    temp_name,
                    filename,
                    src_dir_fd=directory_fd,
                    dst_dir_fd=directory_fd,
                )
            finally:
                try:
                    os.unlink(temp_name, dir_fd=directory_fd)
                except FileNotFoundError:
                    pass
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
