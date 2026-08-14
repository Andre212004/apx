"""Wire contract for the APX machine-continuous audio state service."""

from __future__ import annotations

import json

MAX_MESSAGE_BYTES = 8192
OPERATIONS = {"state.get", "state.put", "activity.put"}


def request_bytes(operation: str, payload: dict[str, object]) -> bytes:
    if operation not in OPERATIONS or type(payload) is not dict:
        raise ValueError("invalid audio-state request")
    data = (json.dumps({"operation": operation, "payload": payload}, sort_keys=True,
                       separators=(",", ":")) + "\n").encode()
    if len(data) > MAX_MESSAGE_BYTES:
        raise ValueError("audio-state request is oversized")
    return data


def parse_message(data: bytes) -> dict[str, object]:
    if not data.endswith(b"\n") or len(data) > MAX_MESSAGE_BYTES or b"\n" in data[:-1]:
        raise ValueError("invalid audio-state framing")
    value = json.loads(data)
    if type(value) is not dict:
        raise ValueError("invalid audio-state message")
    return value
