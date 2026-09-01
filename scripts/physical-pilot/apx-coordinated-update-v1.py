#!/usr/bin/env python3
"""Authenticated Hub endpoint for coordinated APX update policy and execution."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import os
from pathlib import Path
import re
import socket
import struct
import subprocess
import sys
import threading
import time

sys.path.insert(0, "/usr/lib/apx")
from apx_host_services_peer import HostServicesPeer, authorize_official_hub_peer  # noqa: E402
from apx_update_coordinator import EnvironmentUpdateEvidence, build_plan, policy_from_registration  # noqa: E402

SOCKET = Path("/run/apx/coordinated-update-v1.sock")
ENVIRONMENTS = Path("/var/lib/apx/environments")
RUNNER = "/usr/lib/apx/apx-coordinated-update-runner-v1.py"
MAX = 65536
NAME = re.compile(r"[a-z](?:[a-z0-9]|-(?=[a-z0-9])){0,26}")
LOCK = threading.Lock()


def trusted_json(path: Path) -> dict[str, object]:
    metadata = path.lstat(); data = path.read_bytes()
    if path.is_symlink() or not path.is_file() or metadata.st_uid != 0 or metadata.st_gid != 0 or len(data) > 8192:
        raise RuntimeError("untrusted Environment registration")
    value = json.loads(data)
    if type(value) is not dict: raise RuntimeError("invalid Environment registration")
    return value


def subvolume(path: Path) -> bool:
    return subprocess.run(("/usr/bin/btrfs", "subvolume", "show", str(path)),
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0


def inventory() -> tuple[EnvironmentUpdateEvidence, ...]:
    values = []
    for child in sorted(ENVIRONMENTS.iterdir()):
        registration = child / "registration.json"
        if not registration.is_file() or NAME.fullmatch(child.name) is None: continue
        record = trusted_json(registration); policy = policy_from_registration(record)
        # The authenticated Hub is the control surface and is deliberately
        # stopped by the runner after confirmation, so its current session is
        # not an external running-target blocker.
        planned_state = "stopped" if child.name == "hub" else str(record.get("state"))
        values.append(EnvironmentUpdateEvidence(child.name, str(record.get("role")),
                      str(record.get("generation")), planned_state, policy.policy,
                      (child / "root/var/lib/pacman/local").is_dir(),
                      subvolume(child / "root") and subvolume(child / "home")))
    return tuple(values)


def preview() -> dict[str, object]:
    root_source = subprocess.run(("/usr/bin/findmnt", "-no", "FSTYPE", "/"), text=True,
                                 capture_output=True, check=False).stdout.strip()
    sync_ready = any(Path("/var/lib/pacman/sync").glob("*.db"))
    plan = build_plan(inventory(), host_snapshot_ready=root_source == "btrfs",
                      repository_snapshot_ready=sync_ready, package_cache_ready=True)
    value = asdict(plan)
    value["notice"] = "O Hub ativo será fechado após confirmação. Pacotes continuam separados; cada alvo resolve apenas o que tem instalado."
    return value


def latest_status() -> dict[str, object]:
    operations = Path("/var/lib/apx/coordinated-updates-v1/operations")
    candidates = sorted(operations.glob("*/status.json"), reverse=True)
    return trusted_json(candidates[0]) if candidates else {"state": "idle", "reboot_required": False}


def atomic_registration(path: Path, value: dict[str, object]) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        os.write(descriptor, (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()); os.fsync(descriptor)
    finally: os.close(descriptor)
    os.replace(temporary, path)


def apply(operation: str, payload: dict[str, object]) -> dict[str, object]:
    if operation == "preview": return preview()
    if operation == "status": return latest_status()
    if operation == "policy.set":
        name, policy = payload.get("environment"), payload.get("policy")
        if type(name) is not str or NAME.fullmatch(name) is None or policy not in {"follow-host", "excluded"}:
            raise ValueError("invalid update policy selection")
        path = ENVIRONMENTS / name / "registration.json"; record = trusted_json(path)
        if record.get("name") != name: raise ValueError("Environment identity differs")
        record["update_policy"] = policy; atomic_registration(path, record)
        return {"environment": name, "policy": policy}
    if operation == "apply":
        if Path("/run/apx/system-power-v1.reserved").exists():
            raise RuntimeError("a Host power confirmation is pending")
        current = preview()
        if payload != {"plan_digest": current["plan_digest"], "confirmation": "CONFIRMAR"}:
            raise ValueError("preview digest or explicit confirmation differs")
        if current["classification"] != "ready-for-approval":
            raise RuntimeError("update plan is blocked")
        operation_id = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()) + "-" + str(current["plan_digest"])[:12]
        base = Path("/var/lib/apx/coordinated-updates-v1")
        operations = base / "operations"
        operations.mkdir(parents=True, exist_ok=True)
        # Pacman downloads as the unprivileged `alpm` account. Grant only
        # directory traversal; operation files remain root-only (0600).
        os.chmod(base, 0o711)
        os.chmod(operations, 0o711)
        directory = operations / operation_id
        directory.mkdir(mode=0o711)
        os.chmod(directory, 0o711)
        atomic_registration(directory / "approved-plan.json", current)
        unit = "apx-coordinated-update-" + operation_id.replace("T", "-").replace("Z", "-").lower()
        result = subprocess.run(("/usr/bin/systemd-run", f"--unit={unit}", "--collect",
                                 "--property=Type=oneshot", "--property=TimeoutStartSec=infinity",
                                 RUNNER, "--operation", operation_id),
                                text=True, capture_output=True, check=False)
        if result.returncode: raise RuntimeError("could not launch Host update operation")
        return {"accepted": True, "unit": unit + ".service", "operation": operation_id,
                "plan_digest": current["plan_digest"],
                "message": "A operação continuará no Host; reinicie apenas quando o resultado pedir."}
    raise ValueError("unsupported coordinated-update operation")


def receive(connection: socket.socket) -> bytes:
    data = bytearray()
    while b"\n" not in data and len(data) <= MAX:
        chunk = connection.recv(min(4096, MAX + 1 - len(data)))
        if not chunk: break
        data.extend(chunk)
    if not data.endswith(b"\n") or len(data) > MAX or b"\n" in data[:-1]: raise ValueError("request framing differs")
    return bytes(data)


def respond(connection: socket.socket) -> None:
    try:
        pid, uid, gid = struct.unpack("3i", connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
        authorize_official_hub_peer(HostServicesPeer(pid, uid, gid))
        request = json.loads(receive(connection)); operation = request.get("operation"); payload = request.get("payload", {})
        if type(operation) is not str or type(payload) is not dict: raise ValueError("request differs")
        with LOCK: result = apply(operation, payload)
        response = {"ok": True, "result": result, "error": None}
    except Exception as error: response = {"ok": False, "result": None, "error": str(error)[:300]}
    connection.sendall((json.dumps(response, sort_keys=True, separators=(",", ":")) + "\n").encode())


def serve() -> None:
    SOCKET.parent.mkdir(parents=True, exist_ok=True, mode=0o755); SOCKET.unlink(missing_ok=True)
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
        server.bind(str(SOCKET)); os.chmod(SOCKET, 0o600); server.listen(8)
        while True:
            connection, _ = server.accept()
            with connection: respond(connection)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--serve", action="store_true", required=True); serve()
