#!/usr/bin/env python3
"""Atomically update only the visible title and description of one Environment."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import stat
import sys


ENVIRONMENTS = Path("/var/lib/apx/environments")
NATIVE_ENVIRONMENTS = Path("/var/lib/apx/native-environments")
NAME = re.compile(r"[a-z](?:[a-z0-9]|-(?=[a-z0-9])){0,26}")
GENERATION = re.compile(r"[0-9a-f]{8}-[0-9a-f-]{27}")


def valid_text(value: str, minimum: int, maximum: int) -> bool:
    return minimum <= len(value) <= maximum and value == value.strip() \
        and not any(ord(character) < 32 for character in value)


def trusted_parent(path: Path) -> None:
    info = path.lstat()
    if path.is_symlink() or not path.is_dir() or info.st_uid != 0 or info.st_gid != 0 \
            or stat.S_IMODE(info.st_mode) != 0o700:
        raise RuntimeError("a pasta de metadados do Environment não é confiável")


def trusted_json(path: Path, maximum: int, mode: int) -> dict[str, object]:
    trusted_parent(path.parent)
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        info = os.fstat(descriptor)
        raw = os.read(descriptor, maximum + 1)
    finally:
        os.close(descriptor)
    if not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or info.st_gid != 0 \
            or stat.S_IMODE(info.st_mode) != mode or not raw or len(raw) > maximum:
        raise RuntimeError("os metadados do Environment não são confiáveis")
    value = json.loads(raw)
    if type(value) is not dict:
        raise RuntimeError("os metadados do Environment diferem")
    return value


def ordinary_record(target: str, generation: str) -> tuple[Path, dict[str, object], int]:
    path = ENVIRONMENTS / target / "registration.json"
    value = trusted_json(path, 8192, 0o600)
    if (value.get("schema"), value.get("name"), value.get("role"), value.get("release"),
            value.get("state"), value.get("generation")) != (
            1, target, "graphical-base", "hyprland-base-v2", "stopped", generation,
    ):
        raise RuntimeError("o Environment selecionado mudou ou não está parado")
    return path, value, 0o600


def native_record(target: str, generation: str) -> tuple[Path, dict[str, object], int]:
    if target != "windows":
        raise RuntimeError("o Environment nativo selecionado difere")
    path = NATIVE_ENVIRONMENTS / "windows.json"
    value = trusted_json(path, 4096, 0o400)
    expected = {
        "schema": 2, "profile": "apx-native-environment-v2", "name": "windows",
        "category": "system", "environment_kind": "native-boot",
        "system_kind": "windows-native", "system_label": "NATIVO",
        "release": "windows-11-native-v1", "state": "ready",
    }
    if any(value.get(key) != wanted for key, wanted in expected.items()) \
            or value.get("generation") != generation:
        raise RuntimeError("o Windows selecionado mudou ou não está pronto")
    return path, value, 0o400


def atomic_write(path: Path, value: dict[str, object], mode: int) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.metadata.tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode)
    try:
        payload = (json.dumps(value, ensure_ascii=False, sort_keys=True,
                              separators=(",", ":")) + "\n").encode()
        os.write(descriptor, payload)
        os.fsync(descriptor)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    finally:
        os.close(descriptor)
    try:
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def update_metadata(target: str, generation: str, display_name: str, description: str) -> None:
    if os.geteuid() != 0 or NAME.fullmatch(target) is None or target == "hub" \
            or GENERATION.fullmatch(generation) is None \
            or not valid_text(display_name, 1, 64) or not valid_text(description, 0, 120):
        raise RuntimeError("a edição pedida não é válida")
    path, value, mode = native_record(target, generation) if target == "windows" \
        else ordinary_record(target, generation)
    value["display_name"] = display_name
    value["description"] = description
    atomic_write(path, value, mode)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True)
    parser.add_argument("--generation", required=True)
    parser.add_argument("--display-name", required=True)
    parser.add_argument("--description", required=True)
    arguments = parser.parse_args()
    update_metadata(arguments.target, arguments.generation,
                    arguments.display_name, arguments.description)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as error:
        print(f"APX recusou a edição: {error}", file=sys.stderr)
        raise SystemExit(2)
