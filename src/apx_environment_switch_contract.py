"""Closed wire contract for the first physical Environment handoff trial."""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apx_environment_features import PRESETS, validate_selection


SCHEMA = 1
PROFILE = "apx-environment-switch-v1"
MAX_MESSAGE_BYTES = 65536
OPERATIONS = {
    "catalog.get", "identity.get", "status.get", "management.status",
    "environment.create", "environment.destroy",
    "switch.to-workload", "return.to-hub",
}
NAME = re.compile(r"[a-z](?:[a-z0-9]|-(?=[a-z0-9])){0,26}")
GENERATION = re.compile(r"[0-9a-f]{8}-[0-9a-f-]{27}")


def valid_description(value: object) -> bool:
    return type(value) is str and len(value) <= 120 \
        and value == value.strip() and not any(ord(character) < 32 for character in value)


def request_bytes(
    operation: str, target: str | None = None, generation: str | None = None,
    description: str | None = None, preset: str | None = None,
    modules: list[str] | tuple[str, ...] | None = None,
) -> bytes:
    if operation not in OPERATIONS:
        raise ValueError("unsupported Environment-switch operation")
    if operation in {"switch.to-workload", "environment.create"}:
        if type(target) is not str or NAME.fullmatch(target) is None or target == "hub":
            raise ValueError("invalid Environment-switch target")
        payload = {"target": target}
        if operation == "environment.create":
            normalized = "" if description is None else description
            if not valid_description(normalized):
                raise ValueError("invalid Environment description")
            payload["description"] = normalized
            selected_preset, selected_modules = validate_selection(
                "intermediate" if preset is None else preset,
                PRESETS["intermediate"] if modules is None else modules,
            )
            payload["preset"] = selected_preset
            payload["modules"] = list(selected_modules)
        elif description is not None or preset is not None or modules is not None:
            raise ValueError("Environment operation takes no description")
        if generation is not None:
            raise ValueError("Environment operation takes no generation")
    elif operation == "environment.destroy":
        if type(target) is not str or NAME.fullmatch(target) is None or target == "hub" \
                or type(generation) is not str or GENERATION.fullmatch(generation) is None \
                or description is not None or preset is not None or modules is not None:
            raise ValueError("invalid Environment destruction identity")
        payload = {"generation": generation, "target": target}
    else:
        if target is not None or generation is not None or description is not None \
                or preset is not None or modules is not None:
            raise ValueError("Environment-switch operation takes no target")
        payload = {}
    return (json.dumps({
        "schema": SCHEMA, "profile": PROFILE, "operation": operation, "payload": payload,
    }, sort_keys=True, separators=(",", ":")) + "\n").encode()


def parse_message(data: bytes) -> dict[str, object]:
    if not data.endswith(b"\n") or len(data) > MAX_MESSAGE_BYTES or b"\n" in data[:-1]:
        raise ValueError("invalid Environment-switch framing")
    value = json.loads(data)
    if type(value) is not dict or value.get("schema") != SCHEMA \
            or value.get("profile") != PROFILE or value.get("operation") not in OPERATIONS:
        raise ValueError("invalid Environment-switch message")
    operation, payload = value["operation"], value.get("payload")
    if operation in {"switch.to-workload", "environment.create"}:
        target = payload.get("target") if type(payload) is dict else None
        expected = {"description", "modules", "preset", "target"} if operation == "environment.create" else {"target"}
        description = payload.get("description") if type(payload) is dict else None
        if set(payload) != expected or type(target) is not str or NAME.fullmatch(target) is None or target == "hub" \
                or (operation == "environment.create" and not valid_description(description)):
            raise ValueError("invalid Environment-switch target")
        if operation == "environment.create":
            preset, modules = validate_selection(payload.get("preset"), payload.get("modules"))
            if list(modules) != payload.get("modules"):
                raise ValueError("Environment modules are not dependency-complete")
    elif operation == "environment.destroy":
        target = payload.get("target") if type(payload) is dict else None
        generation = payload.get("generation") if type(payload) is dict else None
        if set(payload) != {"generation", "target"} or type(target) is not str \
                or NAME.fullmatch(target) is None or target == "hub" \
                or type(generation) is not str or GENERATION.fullmatch(generation) is None:
            raise ValueError("invalid Environment destruction identity")
    elif payload != {}:
        raise ValueError("invalid Environment-switch payload")
    return value
