"""Closed desktop-session descriptor consumed by the unprivileged APX UI."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from apx_environment import validate_logical_name
from apx_executor_client import ExecutorResponse, exchange_executor_request
from apx_executor_contract import (
    ExecutorContractError, ExecutorRequest, parse_executor_request_json,
)
from apx_session_control import ROLES


SESSION_DESCRIPTOR = Path("/run/apx/session-ui-v1.json")
MAX_DESCRIPTOR_BYTES = 64 * 1024
PROFILE = "apx-session-ui-v1"
TOP_FIELDS = {"active_environment", "actions", "profile", "role", "session_id"}
ACTION_FIELDS = {"action_id", "label", "request"}
ACTION_IDS = {"activate", "return-to-hub"}


class DesktopSessionError(ValueError):
    pass


@dataclass(frozen=True)
class DesktopAction:
    action_id: str
    label: str
    request: ExecutorRequest


@dataclass(frozen=True)
class DesktopSession:
    session_id: str
    active_environment: str
    role: str
    actions: tuple[DesktopAction, ...]


def parse_desktop_session(data: bytes) -> DesktopSession:
    if type(data) is not bytes or not data or len(data) > MAX_DESCRIPTOR_BYTES:
        raise DesktopSessionError("desktop session descriptor is absent or oversized")
    try:
        value = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DesktopSessionError("desktop session descriptor is invalid") from error
    if type(value) is not dict or set(value) != TOP_FIELDS or value["profile"] != PROFILE:
        raise DesktopSessionError("desktop session descriptor schema differs")
    session_id = value["session_id"]
    active = value["active_environment"]
    role = value["role"]
    if type(session_id) is not str or not session_id or len(session_id) > 80:
        raise DesktopSessionError("desktop session identity is malformed")
    if type(active) is not str or validate_logical_name(active) is not None:
        raise DesktopSessionError("active Environment identity is malformed")
    if role not in ROLES or (active == "hub") != (role in {"hub", "hub-graphical"}):
        raise DesktopSessionError("desktop session role is inconsistent")
    raw_actions = value["actions"]
    if type(raw_actions) is not list or not 1 <= len(raw_actions) <= 64:
        raise DesktopSessionError("desktop action catalogue is malformed")
    actions: list[DesktopAction] = []
    seen: set[tuple[str, str]] = set()
    for item in raw_actions:
        if type(item) is not dict or set(item) != ACTION_FIELDS:
            raise DesktopSessionError("desktop action schema differs")
        action_id, label = item["action_id"], item["label"]
        if action_id not in ACTION_IDS or type(label) is not str or not label or len(label) > 80:
            raise DesktopSessionError("desktop action identity or label is invalid")
        try:
            request = parse_executor_request_json(json.dumps(item["request"], separators=(",", ":")))
        except (ExecutorContractError, TypeError) as error:
            raise DesktopSessionError("desktop action request is invalid") from error
        if action_id == "activate" and request.operation_kind != "activate":
            raise DesktopSessionError("activate button request differs")
        if action_id == "return-to-hub" and (
            request.operation_kind != "stop" or request.logical_name != active or role in {"hub", "hub-graphical"}
        ):
            raise DesktopSessionError("return button request differs")
        key = (action_id, request.logical_name)
        if key in seen:
            raise DesktopSessionError("desktop action is duplicated")
        seen.add(key)
        actions.append(DesktopAction(action_id, label, request))
    if role in {"hub", "hub-graphical"}:
        if any(action.action_id != "activate" for action in actions):
            raise DesktopSessionError("Hub session contains a workload-only action")
    elif len(actions) != 1 or actions[0].action_id != "return-to-hub":
        raise DesktopSessionError("workload session must contain only return-to-Hub")
    return DesktopSession(session_id, active, role, tuple(actions))


def load_desktop_session(path: Path = SESSION_DESCRIPTOR) -> DesktopSession:
    if path != SESSION_DESCRIPTOR:
        raise DesktopSessionError("desktop session descriptor path differs")
    try:
        data = path.read_bytes()
    except OSError as error:
        raise DesktopSessionError("desktop session descriptor is unavailable") from error
    return parse_desktop_session(data)


def execute_desktop_action(action: DesktopAction) -> ExecutorResponse:
    if type(action) is not DesktopAction:
        raise DesktopSessionError("desktop action has wrong type")
    return exchange_executor_request(action.request)
