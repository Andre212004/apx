"""Bind a Host-services Unix peer to the exact official graphical Hub."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path


ACTIVE = Path("/run/apx/official-hub-graphical-v1.json")
ACTIVE_ENVIRONMENT = Path("/run/apx/active-graphical-environment-v1.json")
ENVIRONMENTS = Path("/var/lib/apx/environments")
REGISTRATION = Path("/var/lib/apx/environments/hub/registration.json")
PROFILE = "apx-official-hub-graphical-v1"
GENERATION = "6f63f9a9-daea-40d1-969f-e25ff0752f4d"
UNIT = "apx-official-hub-graphical-6f63f9a9.service"
MAX_STATE_BYTES = 4096
USER_NAMESPACE_LENGTH = 65536


class HostServicesPeerError(RuntimeError):
    pass


@dataclass(frozen=True)
class HostServicesPeer:
    pid: int
    uid: int
    gid: int


@dataclass(frozen=True)
class ActiveEnvironmentPeer:
    name: str
    role: str
    generation: str


def authorize_shared_service_peer(peer: HostServicesPeer) -> ActiveEnvironmentPeer:
    """Accept the exact legacy Hub session or the general active-session record."""
    try:
        authorize_official_hub_peer(peer)
        return ActiveEnvironmentPeer("hub", "hub", GENERATION)
    except HostServicesPeerError as legacy_error:
        try:
            return authorize_active_environment_peer(peer)
        except HostServicesPeerError as active_error:
            raise HostServicesPeerError(
                f"peer is neither the official Hub nor the active graphical Environment: {active_error}"
            ) from legacy_error


def _container_id(pid: int, host_id: int, map_name: str, proc: Path) -> int:
    if map_name not in {"uid_map", "gid_map"} or type(host_id) is not int or host_id < 0:
        raise HostServicesPeerError("Host-services peer ID map request differs")
    try:
        lines = (proc / str(pid) / map_name).read_text().splitlines()
    except OSError as error:
        raise HostServicesPeerError("Host-services peer ID map is unavailable") from error
    if len(lines) != 1:
        raise HostServicesPeerError("Host-services peer ID map is ambiguous")
    fields = lines[0].split()
    if len(fields) != 3 or not all(field.isdecimal() for field in fields):
        raise HostServicesPeerError("Host-services peer ID map is malformed")
    container_start, host_start, length = (int(field) for field in fields)
    if container_start != 0 or host_start < USER_NAMESPACE_LENGTH \
            or length != USER_NAMESPACE_LENGTH:
        raise HostServicesPeerError("Host-services peer user namespace differs")
    if not host_start <= host_id < host_start + length:
        raise HostServicesPeerError("Host-services peer ID is outside its user namespace")
    return container_start + host_id - host_start


def _json(path: Path) -> dict[str, object]:
    try:
        metadata = path.lstat()
        data = path.read_bytes()
    except OSError as error:
        raise HostServicesPeerError("trusted Host-services state is unavailable") from error
    if path.is_symlink() or not path.is_file() or metadata.st_uid != 0 or metadata.st_gid != 0:
        raise HostServicesPeerError("trusted Host-services state ownership differs")
    if not data or len(data) > MAX_STATE_BYTES:
        raise HostServicesPeerError("trusted Host-services state is empty or oversized")
    try:
        value = json.loads(data)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise HostServicesPeerError("trusted Host-services state is malformed") from error
    if type(value) is not dict:
        raise HostServicesPeerError("trusted Host-services state is not an object")
    return value


def authorize_official_hub_peer(
    peer: HostServicesPeer, *, active: Path = ACTIVE, registration: Path = REGISTRATION,
    proc: Path = Path("/proc"),
) -> None:
    if type(peer) is not HostServicesPeer or peer.pid <= 1 or peer.uid < 0 or peer.gid < 0:
        raise HostServicesPeerError("Host-services peer credentials differ")
    if _container_id(peer.pid, peer.uid, "uid_map", proc) != 1000 \
            or _container_id(peer.pid, peer.gid, "gid_map", proc) != 1000:
        raise HostServicesPeerError("Host-services peer is not Hub user apx")
    state = _json(active)
    if set(state) != {"generation", "pid", "profile", "unit"} or (
        state.get("profile"), state.get("generation"), state.get("unit")
    ) != (PROFILE, GENERATION, UNIT):
        raise HostServicesPeerError("official graphical Hub state differs")
    if type(state.get("pid")) is not int or state["pid"] <= 1:
        raise HostServicesPeerError("official graphical Hub compositor identity differs")
    record = _json(registration)
    if (
        record.get("name"), record.get("role"), record.get("generation"), record.get("state")
    ) != ("hub", "hub", GENERATION, "running"):
        raise HostServicesPeerError("official Hub registration differs")
    try:
        cgroups = (proc / str(peer.pid) / "cgroup").read_text().splitlines()
        compositor_cgroups = (proc / str(state["pid"]) / "cgroup").read_text().splitlines()
        compositor_name = (proc / str(state["pid"]) / "comm").read_text().strip()
    except OSError as error:
        raise HostServicesPeerError("Host-services peer process state is unavailable") from error
    unit_path = f"/system.slice/{UNIT}"
    if not any(unit_path in line and line.split(":", 2)[-1].startswith(unit_path) for line in cgroups):
        raise HostServicesPeerError("Host-services peer is outside the official graphical unit")
    if compositor_name != "Hyprland" or not any(
        unit_path in line and line.split(":", 2)[-1].startswith(unit_path)
        for line in compositor_cgroups
    ):
        raise HostServicesPeerError("official graphical compositor process differs")


def authorize_active_environment_peer(
    peer: HostServicesPeer, *, active: Path = ACTIVE_ENVIRONMENT,
    environments: Path = ENVIRONMENTS, proc: Path = Path("/proc"),
) -> ActiveEnvironmentPeer:
    """Authorize user ``apx`` in the one root-published active graphical Environment."""
    if type(peer) is not HostServicesPeer or peer.pid <= 1 or peer.uid < 0 or peer.gid < 0:
        raise HostServicesPeerError("Host-services peer credentials differ")
    if _container_id(peer.pid, peer.uid, "uid_map", proc) != 1000 \
            or _container_id(peer.pid, peer.gid, "gid_map", proc) != 1000:
        raise HostServicesPeerError("Host-services peer is not active Environment user apx")
    state = _json(active)
    required = {"schema", "profile", "name", "role", "generation", "unit", "pid"}
    if set(state) != required or state.get("schema") != 1 \
            or state.get("profile") != "apx-active-graphical-environment-v1":
        raise HostServicesPeerError("active graphical Environment state differs")
    name, role, generation, unit, compositor_pid = (
        state.get("name"), state.get("role"), state.get("generation"),
        state.get("unit"), state.get("pid"),
    )
    if type(name) is not str or not name or "/" in name or name in {".", ".."} \
            or type(role) is not str or role not in {"hub", "graphical-base"} \
            or type(generation) is not str or not generation \
            or type(unit) is not str or not unit.startswith("apx-") or not unit.endswith(".service") \
            or type(compositor_pid) is not int or compositor_pid <= 1:
        raise HostServicesPeerError("active graphical Environment identity differs")
    registration = environments / name / "registration.json"
    record = _json(registration)
    if (record.get("name"), record.get("role"), record.get("generation"), record.get("state")) \
            != (name, role, generation, "running"):
        raise HostServicesPeerError("active Environment registration differs")
    try:
        peer_cgroups = (proc / str(peer.pid) / "cgroup").read_text().splitlines()
        compositor_cgroups = (proc / str(compositor_pid) / "cgroup").read_text().splitlines()
        compositor_name = (proc / str(compositor_pid) / "comm").read_text().strip()
    except OSError as error:
        raise HostServicesPeerError("active Environment process state is unavailable") from error
    unit_path = f"/system.slice/{unit}"
    in_unit = lambda lines: any(  # noqa: E731
        unit_path in line and line.split(":", 2)[-1].startswith(unit_path) for line in lines
    )
    if not in_unit(peer_cgroups) or compositor_name != "Hyprland" or not in_unit(compositor_cgroups):
        raise HostServicesPeerError("active Environment process lineage differs")
    return ActiveEnvironmentPeer(name, role, generation)
