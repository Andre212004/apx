"""Host observation that binds a Unix peer to the active APX graphical session."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re

from apx_executor_contract import RequesterContext


ACTIVE_SESSION = Path("/run/apx/active-session-v1.json")
ENVIRONMENTS = Path("/var/lib/apx/environments")
PROFILE = "apx-active-session-v1"
MAX_STATE_BYTES = 4096
_SESSION = re.compile(r"session-[0-9a-f]{32}")
_UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}")
_NAME = re.compile(r"[a-z][a-z0-9-]{0,31}")


class ExecutorPeerError(RuntimeError):
    pass


@dataclass(frozen=True)
class PeerCredentials:
    pid: int
    uid: int
    gid: int


def _read_json(path: Path, limit: int) -> dict[str, object]:
    try:
        info = path.lstat()
        if path.is_symlink() or not path.is_file() or info.st_uid != 0 or info.st_gid != 0:
            raise ExecutorPeerError("trusted peer state type or ownership differs")
        data = path.read_bytes()
    except OSError as error:
        raise ExecutorPeerError("trusted peer state is unavailable") from error
    if not data or len(data) > limit:
        raise ExecutorPeerError("trusted peer state is empty or oversized")
    try:
        value = json.loads(data)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ExecutorPeerError("trusted peer state is malformed") from error
    if type(value) is not dict:
        raise ExecutorPeerError("trusted peer state is not an object")
    return value


def observe_peer(credentials: PeerCredentials, *,
                 active_session: Path = ACTIVE_SESSION,
                 environments: Path = ENVIRONMENTS,
                 proc: Path = Path("/proc")) -> RequesterContext:
    if type(credentials) is not PeerCredentials or credentials.uid != 1000:
        raise ExecutorPeerError("Unix peer is not the fixed Environment user")
    if credentials.pid <= 1 or credentials.gid < 0:
        raise ExecutorPeerError("Unix peer credentials are malformed")
    state = _read_json(active_session, MAX_STATE_BYTES)
    required = {"profile", "session_id", "logical_name", "role", "generation", "unit"}
    if set(state) != required or state["profile"] != PROFILE:
        raise ExecutorPeerError("active session schema differs")
    session_id, name, role, generation, unit = (
        state["session_id"], state["logical_name"], state["role"],
        state["generation"], state["unit"],
    )
    if not isinstance(session_id, str) or not _SESSION.fullmatch(session_id):
        raise ExecutorPeerError("active session identity is malformed")
    if not isinstance(name, str) or not _NAME.fullmatch(name) or name.startswith("apx-"):
        raise ExecutorPeerError("active Environment name is malformed")
    if role not in {"hub-graphical", "graphical-base"} or (name == "hub") != (role == "hub-graphical"):
        raise ExecutorPeerError("active Environment role is inconsistent")
    if not isinstance(generation, str) or not _UUID.fullmatch(generation):
        raise ExecutorPeerError("active Environment generation is malformed")
    expected_unit = f"apx-graphical-{name}-{generation[:8]}.service"
    if unit != expected_unit:
        raise ExecutorPeerError("active graphical unit identity differs")
    registration = _read_json(environments / name / "registration.json", MAX_STATE_BYTES)
    if (
        registration.get("name"), registration.get("role"),
        registration.get("generation"), registration.get("state")
    ) != (name, role, generation, "running"):
        raise ExecutorPeerError("active session does not match registration")
    try:
        cgroups = (proc / str(credentials.pid) / "cgroup").read_text().splitlines()
    except OSError as error:
        raise ExecutorPeerError("Unix peer process disappeared") from error
    expected_suffix = f"/system.slice/{unit}"
    if not any(line.endswith(expected_suffix) for line in cgroups):
        raise ExecutorPeerError("Unix peer is outside the active graphical unit")
    return RequesterContext(session_id, name, role, generation, True, True, True)
