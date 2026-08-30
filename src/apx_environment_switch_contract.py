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
    "catalog.get", "identity.get", "status.get", "management.status", "storage.get",
    "environment.create", "environment.destroy", "environment.update-metadata",
    "switch.to-workload", "native.boot", "native.retry", "native.discard", "return.to-hub",
}
NAME = re.compile(r"[a-z](?:[a-z0-9]|-(?=[a-z0-9])){0,26}")
GENERATION = re.compile(r"[0-9a-f]{8}-[0-9a-f-]{27}")
SYSTEM_KINDS = ("arch", "windows-native")
NATIVE_WINDOWS_SIZES_GIB = (80, 120, 160)


def valid_description(value: object) -> bool:
    return type(value) is str and len(value) <= 120 \
        and value == value.strip() and not any(ord(character) < 32 for character in value)


def valid_display_name(value: object) -> bool:
    return type(value) is str and 1 <= len(value) <= 64 \
        and value == value.strip() and not any(ord(character) < 32 for character in value)


def request_bytes(
    operation: str, target: str | None = None, generation: str | None = None,
    description: str | None = None, preset: str | None = None,
    modules: list[str] | tuple[str, ...] | None = None,
    system_kind: str | None = None,
    size_gib: int | None = None,
    display_name: str | None = None,
) -> bytes:
    if operation not in OPERATIONS:
        raise ValueError("unsupported Environment-switch operation")
    if operation in {"switch.to-workload", "native.boot", "environment.create"}:
        if type(target) is not str or NAME.fullmatch(target) is None or target == "hub":
            raise ValueError("invalid Environment-switch target")
        if operation == "native.boot" and target != "windows":
            raise ValueError("invalid native Environment target")
        payload = {"target": target}
        if operation == "environment.create":
            if display_name is not None:
                raise ValueError("Environment creation takes no display name")
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
            selected_system = "arch" if system_kind is None else system_kind
            if type(selected_system) is not str or selected_system not in SYSTEM_KINDS:
                raise ValueError("invalid Environment system kind")
            payload["system_kind"] = selected_system
            selected_size = (120 if selected_system == "windows-native" else 0) if size_gib is None else size_gib
            if type(selected_size) is not int or (selected_system == "arch" and selected_size != 0) \
                    or (selected_system == "windows-native" and selected_size not in NATIVE_WINDOWS_SIZES_GIB) \
                    or (selected_system == "arch" and target == "windows") \
                    or (selected_system == "windows-native" and target != "windows") \
                    or (selected_system == "windows-native" and
                        (selected_preset != "basic" or list(selected_modules) != ["system"])):
                raise ValueError("invalid native Windows size or identity")
            payload["size_gib"] = selected_size
        elif description is not None or preset is not None or modules is not None or system_kind is not None \
                or size_gib is not None or display_name is not None:
            raise ValueError("Environment operation takes no description")
        if generation is not None:
            raise ValueError("Environment operation takes no generation")
    elif operation in {"native.retry", "native.discard"}:
        if target != "windows" or type(generation) is not str \
                or GENERATION.fullmatch(generation) is None or description is not None \
                or preset is not None or modules is not None or system_kind is not None \
                or size_gib is not None or display_name is not None:
            raise ValueError("invalid native Windows recovery identity")
        payload = {"generation": generation, "target": "windows"}
    elif operation == "environment.update-metadata":
        if type(target) is not str or NAME.fullmatch(target) is None or target == "hub" \
                or type(generation) is not str or GENERATION.fullmatch(generation) is None \
                or not valid_display_name(display_name) or not valid_description(description) \
                or preset is not None or modules is not None or system_kind is not None or size_gib is not None:
            raise ValueError("invalid Environment metadata update")
        payload = {"description": description, "display_name": display_name,
                   "generation": generation, "target": target}
    elif operation == "environment.destroy":
        if type(target) is not str or NAME.fullmatch(target) is None or target == "hub" \
                or type(generation) is not str or GENERATION.fullmatch(generation) is None \
                or description is not None or preset is not None or modules is not None \
                or system_kind is not None or size_gib is not None or display_name is not None:
            raise ValueError("invalid Environment destruction identity")
        payload = {"generation": generation, "target": target}
    else:
        if target is not None or generation is not None or description is not None \
                or preset is not None or modules is not None or system_kind is not None or size_gib is not None \
                or display_name is not None:
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
    if operation in {"switch.to-workload", "native.boot", "environment.create"}:
        target = payload.get("target") if type(payload) is dict else None
        expected = {"description", "modules", "preset", "size_gib", "system_kind", "target"} if operation == "environment.create" else {"target"}
        description = payload.get("description") if type(payload) is dict else None
        if set(payload) != expected or type(target) is not str or NAME.fullmatch(target) is None or target == "hub" \
                or (operation == "environment.create" and not valid_description(description)):
            raise ValueError("invalid Environment-switch target")
        if operation == "native.boot" and target != "windows":
            raise ValueError("invalid native Environment target")
        if operation == "environment.create":
            if payload.get("system_kind") not in SYSTEM_KINDS:
                raise ValueError("invalid Environment system kind")
            selected_system, selected_size = payload["system_kind"], payload.get("size_gib")
            if type(selected_size) is not int or (selected_system == "arch" and selected_size != 0) \
                    or (selected_system == "windows-native" and selected_size not in NATIVE_WINDOWS_SIZES_GIB) \
                    or (selected_system == "arch" and target == "windows") \
                    or (selected_system == "windows-native" and target != "windows") \
                    or (selected_system == "windows-native" and
                        (payload.get("preset") != "basic" or payload.get("modules") != ["system"])):
                raise ValueError("invalid native Windows size or identity")
            preset, modules = validate_selection(payload.get("preset"), payload.get("modules"))
            if list(modules) != payload.get("modules"):
                raise ValueError("Environment modules are not dependency-complete")
    elif operation in {"native.retry", "native.discard"}:
        if type(payload) is not dict or set(payload) != {"generation", "target"} \
                or payload.get("target") != "windows" \
                or type(payload.get("generation")) is not str \
                or GENERATION.fullmatch(payload["generation"]) is None:
            raise ValueError("invalid native Windows recovery identity")
    elif operation == "environment.update-metadata":
        if type(payload) is not dict or set(payload) != {
            "description", "display_name", "generation", "target",
        } or type(payload.get("target")) is not str or NAME.fullmatch(payload["target"]) is None \
                or payload["target"] == "hub" or type(payload.get("generation")) is not str \
                or GENERATION.fullmatch(payload["generation"]) is None \
                or not valid_display_name(payload.get("display_name")) \
                or not valid_description(payload.get("description")):
            raise ValueError("invalid Environment metadata update")
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
