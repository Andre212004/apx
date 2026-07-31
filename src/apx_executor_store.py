"""Atomic Host-owned durable stores for executor plans, approvals, and nonces."""

from __future__ import annotations

from dataclasses import asdict
import json
import os
from pathlib import Path
import re

from apx_executor_contract import (
    ApprovalEvidence, OperationPlan, build_operation_plan,
)


STORE_ROOT = Path("/var/lib/apx/executor-v1")
MAX_RECORD_BYTES = 16 * 1024
_SHA = re.compile(r"[0-9a-f]{64}")
_APPROVAL = re.compile(r"approval-[0-9a-f]{32}")


class ExecutorStoreError(RuntimeError):
    pass


def initialize_store(root: Path | None = None) -> None:
    root = STORE_ROOT if root is None else root
    if root != STORE_ROOT:
        raise ExecutorStoreError("executor store path differs")
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(root, 0o700)
    for name in ("plans", "approvals", "nonces"):
        path = root / name
        path.mkdir(mode=0o700, exist_ok=True)
        os.chmod(path, 0o700)


def _encode(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def _write_once(path: Path, data: bytes) -> None:
    if not data or len(data) > MAX_RECORD_BYTES or path.parent.parent != STORE_ROOT:
        raise ExecutorStoreError("executor record destination or size differs")
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o400)
    try:
        os.write(descriptor, data)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def publish_plan(plan: OperationPlan) -> None:
    if type(plan) is not OperationPlan:
        raise ExecutorStoreError("executor plan has wrong type")
    expected = build_operation_plan(
        plan.operation_kind, plan.logical_name, plan.expected_generation,
        policy_version=plan.policy_version,
    )
    if plan != expected:
        raise ExecutorStoreError("executor plan differs from fixed policy")
    _write_once(STORE_ROOT / "plans" / f"{plan.plan_digest}.json", _encode(asdict(plan)))


def publish_approval(approval: ApprovalEvidence) -> None:
    if type(approval) is not ApprovalEvidence or not _APPROVAL.fullmatch(approval.approval_id):
        raise ExecutorStoreError("executor approval identity differs")
    if approval.authenticity_verified is not True:
        raise ExecutorStoreError("unverified approval cannot be published")
    _write_once(STORE_ROOT / "approvals" / f"{approval.approval_id}.json", _encode(asdict(approval)))


def _read(path: Path) -> dict[str, object]:
    try:
        metadata = path.lstat()
        if not path.is_file() or path.is_symlink() or metadata.st_uid != 0 or metadata.st_gid != 0:
            raise ExecutorStoreError("executor record ownership or type differs")
        data = path.read_bytes()
    except OSError as error:
        raise ExecutorStoreError("executor record is unavailable") from error
    if not data or len(data) > MAX_RECORD_BYTES or not data.endswith(b"\n"):
        raise ExecutorStoreError("executor record framing differs")
    try:
        value = json.loads(data)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ExecutorStoreError("executor record is malformed") from error
    if type(value) is not dict:
        raise ExecutorStoreError("executor record is not an object")
    return value


def load_plan(digest: str) -> OperationPlan:
    if type(digest) is not str or not _SHA.fullmatch(digest):
        raise ExecutorStoreError("plan digest is malformed")
    try:
        value = _read(STORE_ROOT / "plans" / f"{digest}.json")
        value["effects"] = tuple(value["effects"])
        value["consequences"] = tuple(value["consequences"])
        plan = OperationPlan(**value)
        expected = build_operation_plan(
            plan.operation_kind, plan.logical_name, plan.expected_generation,
            policy_version=plan.policy_version,
        )
    except (TypeError, ValueError) as error:
        raise ExecutorStoreError("stored plan schema differs") from error
    if plan != expected or plan.plan_digest != digest:
        raise ExecutorStoreError("stored plan identity differs")
    return plan


def load_approval(identity: str) -> ApprovalEvidence:
    if type(identity) is not str or not _APPROVAL.fullmatch(identity):
        raise ExecutorStoreError("approval identity is malformed")
    try:
        approval = ApprovalEvidence(**_read(STORE_ROOT / "approvals" / f"{identity}.json"))
    except TypeError as error:
        raise ExecutorStoreError("stored approval schema differs") from error
    if approval.approval_id != identity or approval.authenticity_verified is not True:
        raise ExecutorStoreError("stored approval identity differs")
    return approval


def reserve_nonce(nonce: str, request_digest: str) -> bool:
    if not isinstance(nonce, str) or not _SHA.fullmatch(nonce) or not _SHA.fullmatch(request_digest):
        raise ExecutorStoreError("nonce reservation identity is malformed")
    try:
        _write_once(STORE_ROOT / "nonces" / nonce, (request_digest + "\n").encode())
    except FileExistsError:
        return False
    return True
