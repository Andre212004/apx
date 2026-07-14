#!/usr/bin/env python3
"""Host-owned typed request endpoint for the disposable APX Hub."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import socket
import struct
import sys


SOCKET = Path("/run/apx/executor.sock")
RUNTIME = Path("/usr/lib/apx/apx-lab-runtime.py")
MAX_REQUEST = 8192


def load_runtime():
    spec = importlib.util.spec_from_file_location("apx_lab_runtime", RUNTIME)
    if spec is None or spec.loader is None:
        raise RuntimeError("runtime module cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


runtime = load_runtime()


FIELDS = {
    "status": {"schema", "operation"},
    "list": {"schema", "operation"},
    "create-plan": {"schema", "operation", "name", "role"},
    "create": {"schema", "operation", "plan", "approval"},
    "start": {"schema", "operation", "name"},
    "stop": {"schema", "operation", "name"},
    "snapshot": {"schema", "operation", "name"},
    "archive": {"schema", "operation", "name"},
    "destroy-plan": {"schema", "operation", "name"},
    "destroy": {"schema", "operation", "plan", "approval"},
    "restore": {"schema", "operation", "archive", "name", "approval"},
    "recovery-status": {"schema", "operation"},
}


def hub_uid_range() -> tuple[int, int]:
    result = runtime.run(
        ["machinectl", "show", "apx-hub", "--property=Leader", "--value"],
        check=False,
        capture=True,
    )
    if result.returncode != 0 or not result.stdout.strip().isdigit():
        raise runtime.Refusal("the active Hub identity cannot be verified")
    line = Path(f"/proc/{result.stdout.strip()}/uid_map").read_text().splitlines()[0]
    inside, outside, length = (int(value) for value in line.split())
    if inside != 0 or length != 65536:
        raise runtime.Refusal("the active Hub user namespace is unexpected")
    return outside, outside + length


def authorize(connection: socket.socket) -> None:
    _pid, uid, _gid = struct.unpack("3i", connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
    lower, upper = hub_uid_range()
    if not lower <= uid < upper:
        raise runtime.Refusal("caller is not inside the active Hub user namespace")


def dispatch(request: dict[str, object]) -> None:
    operation = request.get("operation")
    if request.get("schema") != 1 or not isinstance(operation, str) or operation not in FIELDS:
        raise runtime.Refusal("unknown request schema or operation")
    if set(request) != FIELDS[operation]:
        raise runtime.Refusal("request fields do not match the closed operation schema")
    if operation == "status":
        runtime.status()
    elif operation == "list":
        runtime.list_environments(bool(request.get("json", False)))
    elif operation == "create-plan":
        print(json.dumps(runtime.make_plan("create", str(request["name"]), str(request["role"])), sort_keys=True, indent=2))
    elif operation == "create":
        runtime.create(str(request["plan"]), str(request["approval"]))
    elif operation == "start":
        runtime.start(str(request["name"]))
    elif operation == "stop":
        runtime.stop(str(request["name"]))
    elif operation == "snapshot":
        runtime.snapshot(str(request["name"]))
    elif operation == "archive":
        runtime.archive(str(request["name"]))
    elif operation == "destroy-plan":
        print(json.dumps(runtime.make_plan("destroy", str(request["name"])), sort_keys=True, indent=2))
    elif operation == "destroy":
        runtime.destroy(str(request["plan"]), str(request["approval"]))
    elif operation == "restore":
        runtime.restore(str(request["archive"]), str(request["name"]), str(request["approval"]))
    elif operation == "recovery-status":
        runtime.recover()


def respond(connection: socket.socket) -> None:
    try:
        authorize(connection)
        data = b""
        while b"\n" not in data and len(data) <= MAX_REQUEST:
            chunk = connection.recv(4096)
            if not chunk:
                break
            data += chunk
        if len(data) > MAX_REQUEST or not data.endswith(b"\n"):
            raise runtime.Refusal("request is absent, oversized, or not framed")
        request = json.loads(data)
        if not isinstance(request, dict):
            raise runtime.Refusal("request is not an object")
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            dispatch(request)
        response = {"ok": True, "output": output.getvalue()}
    except Exception as error:
        response = {"ok": False, "error": str(error)}
    try:
        connection.sendall(runtime.canonical(response))
    except (BrokenPipeError, ConnectionResetError):
        # A request that stops its calling Environment can close the transport
        # before the already journaled result is returned.
        pass


def main() -> int:
    if os.geteuid() != 0:
        raise SystemExit("executor requires the host identity")
    SOCKET.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    SOCKET.unlink(missing_ok=True)
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
        server.bind(str(SOCKET))
        os.chmod(SOCKET, 0o666)
        server.listen(8)
        while True:
            connection, _ = server.accept()
            with connection:
                respond(connection)


if __name__ == "__main__":
    raise SystemExit(main())
