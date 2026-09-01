#!/usr/bin/env python3
"""Root-owned audio settings handoff and global microphone-use indicator."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import socket
import struct
import sys
import threading

sys.path.insert(0, "/usr/lib/apx")
from apx_audio_handoff import AudioState, validate_state  # noqa: E402
from apx_audio_state_contract import MAX_MESSAGE_BYTES, parse_message  # noqa: E402
from apx_host_services_peer import HostServicesPeer, authorize_shared_service_peer  # noqa: E402

SOCKET = Path("/run/apx/audio-state-v1.sock")
STATE = Path("/var/lib/apx/audio-state-v1/state.json")
LOCK = threading.Lock()
DEFAULT = {"schema": 1, "profile": "apx-active-audio-handoff-v1", "output_volume": 80,
           "output_muted": False, "input_volume": 80, "input_muted": False,
           "output_name": None, "input_name": None, "microphone_active": False,
           "active_environment": None}


def atomic_write(value: dict[str, object]) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = STATE.with_name(f".{STATE.name}.{os.getpid()}.tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        os.write(descriptor, (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode())
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    os.replace(temporary, STATE)


def read_state() -> dict[str, object]:
    if not STATE.exists():
        atomic_write(dict(DEFAULT))
    metadata = STATE.lstat(); data = STATE.read_bytes()
    if STATE.is_symlink() or metadata.st_uid != 0 or metadata.st_gid != 0 or len(data) > 4096:
        raise RuntimeError("untrusted audio state")
    value = json.loads(data)
    state = AudioState(1, "apx-active-audio-handoff-v1", int(value["output_volume"]),
                       bool(value["output_muted"]), int(value["input_volume"]),
                       bool(value["input_muted"]), value.get("output_name"), value.get("input_name"))
    validate_state(state)
    if type(value.get("microphone_active")) is not bool:
        raise RuntimeError("invalid microphone activity state")
    return value


def receive(connection: socket.socket) -> bytes:
    data = bytearray()
    while b"\n" not in data and len(data) <= MAX_MESSAGE_BYTES:
        chunk = connection.recv(min(4096, MAX_MESSAGE_BYTES + 1 - len(data)))
        if not chunk: break
        data.extend(chunk)
    return bytes(data)


def respond(connection: socket.socket) -> None:
    try:
        pid, uid, gid = struct.unpack("3i", connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
        active_peer = authorize_shared_service_peer(HostServicesPeer(pid, uid, gid))
        request = parse_message(receive(connection)); operation = request.get("operation"); payload = request.get("payload")
        if operation not in {"state.get", "state.put", "activity.put"} or type(payload) is not dict:
            raise ValueError("unsupported audio-state operation")
        with LOCK:
            value = read_state()
            if operation == "state.put":
                permitted = {"output_volume", "output_muted", "input_volume", "input_muted", "output_name", "input_name"}
                if set(payload) != permitted: raise ValueError("audio settings fields differ")
                candidate = AudioState(1, "apx-active-audio-handoff-v1", **payload)
                validate_state(candidate); value.update(payload); value["active_environment"] = active_peer.name; atomic_write(value)
            elif operation == "activity.put":
                if set(payload) != {"microphone_active"} or type(payload["microphone_active"]) is not bool:
                    raise ValueError("microphone activity differs")
                value["microphone_active"] = payload["microphone_active"]
                value["active_environment"] = active_peer.name; atomic_write(value)
        response = {"ok": True, "result": value, "error": None}
    except Exception as error:
        response = {"ok": False, "result": None, "error": str(error)[:240]}
    connection.sendall((json.dumps(response, sort_keys=True, separators=(",", ":")) + "\n").encode())


def serve() -> None:
    SOCKET.parent.mkdir(parents=True, exist_ok=True, mode=0o755); SOCKET.unlink(missing_ok=True)
    read_state()
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
        server.bind(str(SOCKET)); os.chmod(SOCKET, 0o600); server.listen(16)
        while True:
            connection, _ = server.accept()
            with connection: respond(connection)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--serve", action="store_true"); mode.add_argument("--clear", action="store_true")
    arguments = parser.parse_args()
    if arguments.clear:
        if os.geteuid() != 0: raise SystemExit(2)
        value = read_state(); value["microphone_active"] = False; value["active_environment"] = None; atomic_write(value)
    else: serve()
