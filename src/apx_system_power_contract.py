"""Typed wire contract for the APX Host system-power service."""

from __future__ import annotations

import json

SCHEMA = 1
PROFILE = "apx-system-power-v1"
MAX_MESSAGE_BYTES = 8192
OPERATIONS = {
    "capabilities.get", "system.reboot.prepare", "system.poweroff.prepare", "system.suspend.prepare",
    "system.action.confirm", "system.action.cancel", "system.action.status",
    "hardware.profile.status", "hardware.platform.set", "hardware.gpu.prepare",
    "hardware.gpu.confirm", "hardware.gpu.cancel",
    "hardware.display.set", "hardware.keyboard.cycle",
}


def request_bytes(operation: str, payload: dict[str, object]) -> bytes:
    if operation not in OPERATIONS or type(payload) is not dict:
        raise ValueError("invalid system-power request")
    value = {"schema": SCHEMA, "profile": PROFILE, "operation": operation, "payload": payload}
    data = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
    if len(data) > MAX_MESSAGE_BYTES: raise ValueError("system-power request is oversized")
    return data


def parse_message(data: bytes) -> dict[str, object]:
    if not data.endswith(b"\n") or len(data) > MAX_MESSAGE_BYTES or b"\n" in data[:-1]:
        raise ValueError("invalid system-power framing")
    value = json.loads(data)
    if type(value) is not dict or value.get("schema") != SCHEMA or value.get("profile") != PROFILE:
        raise ValueError("invalid system-power message")
    return value
