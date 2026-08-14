"""Closed wire contract for the APX Host console broker."""

from __future__ import annotations

import json

SCHEMA = 1
PROFILE = "apx-host-console-v1"
MAX_MESSAGE_BYTES = 8192
OPERATIONS = {
    "capabilities.get", "console.open",
}


def request_bytes(operation: str, payload: dict[str, object]) -> bytes:
    if operation not in OPERATIONS or type(payload) is not dict:
        raise ValueError("invalid Host-console request")
    data = (json.dumps({"schema": SCHEMA, "profile": PROFILE, "operation": operation,
                        "payload": payload}, sort_keys=True, separators=(",", ":")) + "\n").encode()
    if len(data) > MAX_MESSAGE_BYTES:
        raise ValueError("Host-console request is oversized")
    return data


def parse_message(data: bytes) -> dict[str, object]:
    if not data.endswith(b"\n") or len(data) > MAX_MESSAGE_BYTES or b"\n" in data[:-1]:
        raise ValueError("invalid Host-console framing")
    value = json.loads(data)
    if type(value) is not dict or value.get("schema") != SCHEMA or value.get("profile") != PROFILE:
        raise ValueError("invalid Host-console message")
    return value
