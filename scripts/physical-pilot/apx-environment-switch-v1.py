#!/usr/bin/env python3
"""Authenticated Host endpoint for one bounded Hub/workload handoff trial."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import secrets
import select
import socket
import stat
import struct
import subprocess
import sys
import threading

sys.path.insert(0, "/usr/lib/apx")
from apx_environment_switch_contract import MAX_MESSAGE_BYTES, PROFILE, parse_message  # noqa: E402
from apx_host_services_peer import (  # noqa: E402
    HostServicesPeer, HostServicesPeerError, authorize_active_environment_peer,
    authorize_official_hub_peer,
)


SOCKET = Path("/run/apx/environment-switch-v1.sock")
LIVE_SOCKET = Path("/var/lib/apx/environments/hub/home/.apx-host-bridge/environment-switch-v1.sock")
ENVIRONMENTS = Path("/var/lib/apx/environments")
RUNNER = "/usr/lib/apx/apx-environment-switch-runner-v1.py"
MANAGEMENT_RUNNER = "/usr/lib/apx/apx-environment-management-runner-v1.py"
LOCK = Path("/run/apx/environment-handoff-v1.lock")
MANAGEMENT_LOCK = Path("/run/apx/environment-management-v1.lock")
MANAGEMENT_STATE = Path("/run/apx/environment-management-v1.json")
OFFICIAL_UNIT = "apx-official-hub-graphical-6f63f9a9.service"
SERVER_LOCK = threading.Lock()


def trusted_environment(name: str) -> dict[str, object]:
    if not re.fullmatch(r"[a-z](?:[a-z0-9]|-(?=[a-z0-9])){0,26}", name) or name == "hub":
        raise PermissionError("a identidade do Environment é inválida")
    registration = ENVIRONMENTS / name / "registration.json"
    metadata = registration.lstat(); data = registration.read_bytes()
    if registration.is_symlink() or not registration.is_file() \
            or metadata.st_uid != 0 or metadata.st_gid != 0 or len(data) > 8192:
        raise PermissionError("o registo do Environment não é confiável")
    value = json.loads(data)
    if type(value) is not dict or (value.get("name"), value.get("role"), value.get("release")) != (
        name, "graphical-base", "hyprland-base-v2",
    ) or value.get("state") not in {"stopped", "running"}:
        raise PermissionError("a identidade do Environment difere")
    return value


def trusted_hub() -> dict[str, object]:
    registration = ENVIRONMENTS / "hub" / "registration.json"
    metadata = registration.lstat(); data = registration.read_bytes()
    if registration.is_symlink() or not registration.is_file() or metadata.st_uid != 0 \
            or metadata.st_gid != 0 or not data or len(data) > 8192:
        raise PermissionError("o registo do HUB não é confiável")
    value = json.loads(data)
    if type(value) is not dict or (value.get("name"), value.get("role")) != ("hub", "hub") \
            or value.get("state") not in {"stopped", "running"}:
        raise PermissionError("a identidade do HUB difere")
    return value


def environment_view(record: dict[str, object]) -> dict[str, object]:
    name = str(record["name"])
    display_name = record.get("display_name", name.replace("-", " ").title())
    description = record.get("description", "")
    category = record.get("category", "general")
    if type(display_name) is not str or not 1 <= len(display_name) <= 64 \
            or type(description) is not str or len(description) > 120 \
            or type(category) is not str or not re.fullmatch(r"[a-z][a-z0-9-]{0,31}", category):
        raise PermissionError("a apresentação do Environment difere")
    return {"category": category, "description": description, "display_name": display_name, "generation": record["generation"],
            "name": name, "release": record["release"], "role": record["role"], "state": record["state"],
            "session_restore": record.get("session_restore") is True,
            "update_policy": record.get("update_policy", "follow-host")}


def catalog() -> list[dict[str, object]]:
    values = []
    for directory in sorted(ENVIRONMENTS.iterdir()):
        if not directory.is_dir() or directory.name == "hub": continue
        try: values.append(environment_view(trusted_environment(directory.name)))
        except (OSError, ValueError, KeyError, json.JSONDecodeError, PermissionError): continue
        if len(values) >= 64: break
    return values


def management_state() -> dict[str, object]:
    try:
        metadata = MANAGEMENT_STATE.lstat()
        data = MANAGEMENT_STATE.read_bytes()
        if MANAGEMENT_STATE.is_symlink() or not MANAGEMENT_STATE.is_file() \
                or metadata.st_uid != 0 or metadata.st_gid != 0 or len(data) > 8192:
            raise PermissionError("o estado de gestão não é confiável")
        value = json.loads(data)
        if type(value) is not dict or value.get("profile") != "apx-environment-management-v1" \
                or value.get("phase") not in {"planning", "applying", "complete", "failed"}:
            raise PermissionError("o estado de gestão difere")
        value["busy"] = MANAGEMENT_LOCK.exists()
        return value
    except FileNotFoundError:
        return {"schema": 1, "profile": "apx-environment-management-v1", "phase": "idle",
                "progress": 0, "message": "", "target": "", "action": "", "busy": False}


def completed_destroy(target: str, generation: str) -> bool:
    """Recognize a duplicate UI request after the original deletion completed."""
    state = management_state()
    return not (ENVIRONMENTS / target).exists() and state.get("busy") is False \
        and (state.get("phase"), state.get("action"), state.get("target")) == (
            "complete", "destroy", target,
        ) and type(generation) is str


def quickshell_parent(peer_pid: int, unit: str, proc: Path = Path("/proc")) -> int:
    try:
        fields = dict(line.split(":", 1) for line in (proc / str(peer_pid) / "status").read_text().splitlines() if ":" in line)
        parent = int(fields["PPid"].strip())
        comm = (proc / str(parent) / "comm").read_text().strip()
        executable = os.readlink(proc / str(parent) / "exe")
        cgroups = (proc / str(parent) / "cgroup").read_text().splitlines()
    except (OSError, KeyError, ValueError) as error:
        raise PermissionError("a origem QuickShell não pôde ser provada") from error
    unit_path = f"/system.slice/{unit}"
    if parent <= 1 or comm != "quickshell" or executable != "/usr/bin/quickshell" \
            or not any(unit_path in line and line.split(":", 2)[-1].startswith(unit_path) for line in cgroups):
        raise PermissionError("o pedido não é filho direto da QuickShell ativa")
    return parent


def authorize(peer: HostServicesPeer, operation: str, target: str | None = None) -> str:
    if operation == "switch.to-workload":
        authorize_official_hub_peer(peer)
        quickshell_parent(peer.pid, OFFICIAL_UNIT)
        if target is None or trusted_environment(target).get("state") != "stopped" or LOCK.exists():
            raise RuntimeError("a troca já está ativa ou o destino não está parado")
        return "hub"
    active = authorize_active_environment_peer(peer)
    record = trusted_environment(active.name)
    if active.name == "hub" or active.role != "graphical-base" or active.generation != record.get("generation"):
        raise HostServicesPeerError("apenas o workload ativo pode regressar")
    # authorize_active_environment_peer already proves that this exact client
    # is user apx inside the root-published active Environment unit.  Do not
    # require a QuickShell parent here: both the environment-aware QuickShell
    # action and the Hyprland shortcut launch the fixed client directly.
    return active.name


def authorize_hub_management(peer: HostServicesPeer) -> None:
    authorize_official_hub_peer(peer)
    quickshell_parent(peer.pid, OFFICIAL_UNIT)
    if LOCK.exists() or MANAGEMENT_LOCK.exists():
        raise RuntimeError("já existe uma operação de Environment em curso")


def start_management(action: str, target: str, generation: str | None = None,
                     description: str = "", preset: str = "intermediate",
                     modules: list[str] | None = None) -> dict[str, object]:
    unit = "apx-environment-management-" + secrets.token_hex(5)
    descriptor = os.open(MANAGEMENT_LOCK, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        os.write(descriptor, (unit + "\n").encode())
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    command = [
        "/usr/bin/systemd-run", f"--unit={unit}", "--collect", "--property=Type=simple",
        "--property=TimeoutStopSec=15s", MANAGEMENT_RUNNER, "--action", action,
        "--environment", target, "--lock-token", unit,
    ]
    if generation is not None:
        command.extend(("--generation", generation))
    if action == "create":
        command.extend(("--description", description, "--desktop-preset", preset,
                        "--desktop-modules", ",".join(modules or [])))
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    if result.returncode:
        MANAGEMENT_LOCK.unlink(missing_ok=True)
        raise RuntimeError("o executor de Environments não arrancou")
    return {"accepted": True, "action": action, "target": target, "unit": unit + ".service"}


def prime_return_screen() -> None:
    """Prepare tty1 before the workload exits so no Host prompt can flash."""
    payload = ("\033[2J\033[H\033[?25l\n\n\n\n"
               "                  APX ENVIRONMENTS\n\n"
               "                  A REGRESSAR AO HUB\n\n"
               "                  [######------------------------]  20%\n").encode()
    descriptor = os.open("/dev/tty1", os.O_WRONLY | os.O_NOCTTY)
    try:
        os.write(descriptor, payload)
    finally:
        os.close(descriptor)


def request_environment_stop(name: str) -> str:
    """Ask systemd to end the authenticated workload; the runner restores Hub.

    The return action must not depend on the unprivileged client inheriting a
    usable Hyprland control environment.  Peer admission above proves the
    caller belongs to the exact active workload, and its trusted registration
    binds the stop target to the expected generation-scoped outer unit.
    """
    record = trusted_environment(name)
    generation = str(record.get("generation", ""))
    if re.fullmatch(r"[0-9a-f]{8}-[0-9a-f-]{27}", generation) is None:
        raise RuntimeError("a geração do Environment ativo difere")
    unit = f"apx-graphical-{name}-{generation[:8]}.service"
    result = subprocess.run(
        ("/usr/bin/systemctl", "--no-block", "stop", unit),
        text=True, capture_output=True, check=False,
    )
    if result.returncode:
        raise RuntimeError("o Host não conseguiu iniciar o regresso ao HUB")
    return unit


def active_identity(peer: HostServicesPeer) -> dict[str, object]:
    try:
        authorize_official_hub_peer(peer)
        record = trusted_hub()
        return {"category": "system", "display_name": "HUB", "generation": record["generation"],
                "name": "hub", "release": record["release"], "role": "hub", "state": record["state"],
                "session_restore": False, "update_policy": "host-only"}
    except HostServicesPeerError:
        active = authorize_active_environment_peer(peer)
        return environment_view(trusted_environment(active.name))


def apply(operation: str, payload: dict[str, object], peer: HostServicesPeer) -> dict[str, object] | list[dict[str, object]]:
    if operation == "catalog.get":
        authorize_official_hub_peer(peer); return catalog()
    if operation == "identity.get": return active_identity(peer)
    if operation == "management.status":
        authorize_official_hub_peer(peer); return management_state()
    if operation == "status.get":
        try:
            authorize_official_hub_peer(peer); active = "hub"
        except HostServicesPeerError:
            active = authorize(peer, "return.to-hub")
        return {"active": active, "handoff_running": LOCK.exists(), "identity": active_identity(peer)}
    if operation == "environment.create":
        authorize_hub_management(peer)
        target = str(payload["target"])
        return start_management("create", target, description=str(payload["description"]),
                                preset=str(payload["preset"]), modules=list(payload["modules"]))
    if operation == "environment.destroy":
        authorize_hub_management(peer)
        target, generation = str(payload["target"]), str(payload["generation"])
        if completed_destroy(target, generation):
            return {"accepted": True, "action": "destroy", "target": target,
                    "already_complete": True}
        record = trusted_environment(target)
        if record.get("state") != "stopped" or record.get("generation") != generation:
            raise RuntimeError("o Environment selecionado não está parado ou mudou")
        return start_management("destroy", target, generation)
    target = str(payload["target"]) if operation == "switch.to-workload" else None
    source = authorize(peer, operation, target)
    if operation == "return.to-hub":
        if not LOCK.exists():
            raise RuntimeError("não existe uma troca supervisionada para concluir")
        prime_return_screen()
        unit = request_environment_stop(source)
        return {"accepted": True, "direction": "workload-to-hub", "source": source,
                "unit": unit}
    unit = "apx-environment-handoff-" + secrets.token_hex(5)
    result = subprocess.run((
        "/usr/bin/systemd-run", f"--unit={unit}", "--collect", "--property=Type=simple",
        "--property=TimeoutStopSec=15s", RUNNER, "--environment", str(target),
    ), text=True, capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError("o supervisor da troca não arrancou")
    return {"accepted": True, "direction": "hub-to-workload", "unit": unit + ".service"}


def receive(connection: socket.socket) -> bytes:
    data = bytearray()
    while b"\n" not in data and len(data) <= MAX_MESSAGE_BYTES:
        chunk = connection.recv(min(4096, MAX_MESSAGE_BYTES + 1 - len(data)))
        if not chunk: break
        data.extend(chunk)
    return bytes(data)


def respond(connection: socket.socket) -> None:
    operation = "unknown"
    pid = -1
    try:
        pid, uid, gid = struct.unpack("3i", connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
        request = parse_message(receive(connection))
        operation = str(request["operation"])
        with SERVER_LOCK:
            result = apply(operation, dict(request["payload"]), HostServicesPeer(pid, uid, gid))
        response = {"schema": 1, "profile": PROFILE, "ok": True, "result": result, "error": None}
        print(f"APX Environment switch accepted operation={operation} peer_pid={pid}", flush=True)
    except Exception as error:
        response = {"schema": 1, "profile": PROFILE, "ok": False, "result": None,
                    "error": {"code": "request_rejected", "message": str(error)[:300]}}
        print(f"APX Environment switch rejected operation={operation} peer_pid={pid}: {error}",
              file=sys.stderr, flush=True)
    connection.sendall((json.dumps(response, sort_keys=True, separators=(",", ":")) + "\n").encode())


def admit_existing_session() -> None:
    for active in (Path("/run/apx/official-hub-graphical-v1.json"), Path("/run/apx/active-graphical-environment-v1.json")):
        try:
            pid = int(json.loads(active.read_text())["pid"])
            fields = Path(f"/proc/{pid}/uid_map").read_text().split()
            if len(fields) == 3 and fields[0] == "0" and int(fields[2]) == 65536:
                translated = int(fields[1]) + 1000
                os.chown(SOCKET, translated, translated); os.chmod(SOCKET, 0o660)
                return
        except (OSError, ValueError, KeyError, json.JSONDecodeError):
            pass


def serve() -> None:
    SOCKET.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
    live_parent = LIVE_SOCKET.parent
    metadata = live_parent.stat()
    if metadata.st_uid != 0 or metadata.st_gid != 0 or metadata.st_mode & 0o022:
        raise RuntimeError("a ponte viva do HUB não é confiável")
    servers: list[socket.socket] = []
    try:
        for endpoint in (SOCKET, LIVE_SOCKET):
            endpoint.unlink(missing_ok=True)
            server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            server.bind(str(endpoint))
            os.chmod(endpoint, 0o600 if endpoint == SOCKET else 0o666)
            server.listen(8)
            servers.append(server)
        admit_existing_session()
        while True:
            readable, _, _ = select.select(servers, [], [])
            for server in readable:
                connection, _ = server.accept()
                with connection:
                    respond(connection)
    finally:
        for server in servers:
            server.close()


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--serve", action="store_true", required=True)
    serve(); return 0


if __name__ == "__main__":
    raise SystemExit(main())
