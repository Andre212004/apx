#!/usr/bin/env python3
"""Run one fixed APX Environment create/destroy plan with observable progress."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import time


APX = "/usr/bin/apx"
STATE = Path("/run/apx/environment-management-v1.json")
LOCK = Path("/run/apx/environment-management-v1.lock")
ENVIRONMENTS = Path("/var/lib/apx/environments")
NAME = re.compile(r"[a-z](?:[a-z0-9]|-(?=[a-z0-9])){0,26}")
GENERATION = re.compile(r"[0-9a-f]{8}-[0-9a-f-]{27}")


def write_state(action: str, target: str, phase: str, progress: int, message: str) -> None:
    value = {
        "schema": 1,
        "profile": "apx-environment-management-v1",
        "action": action,
        "target": target,
        "phase": phase,
        "progress": progress,
        "message": message,
        "updated_at": int(time.time()),
    }
    temporary = STATE.with_name(f".{STATE.name}.{os.getpid()}.tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        os.write(descriptor, (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode())
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    os.replace(temporary, STATE)


def run(arguments: tuple[str, ...]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(arguments, text=True, capture_output=True, check=False,
                            env={"PATH": "/usr/bin:/usr/local/bin", "LC_ALL": "C"})
    if result.returncode:
        detail = (result.stderr.strip() or result.stdout.strip() or "sem detalhes")[-1200:]
        raise RuntimeError(detail)
    return result


def plan(action: str, target: str, description: str = "", preset: str = "intermediate",
         modules: str = "") -> dict[str, object]:
    arguments = (APX, "environment", action + "-plan", target)
    if action == "create":
        arguments += ("--role", "graphical-base", "--description", description,
                      "--desktop-preset", preset, "--desktop-modules", modules)
    value = json.loads(run(arguments).stdout)
    if type(value) is not dict or not re.fullmatch(r"[0-9a-f]{64}", str(value.get("digest", ""))):
        raise RuntimeError("o plano APX devolvido é inválido")
    return value


def recover_failed_create(target: str) -> None:
    """Remove only a journal-proven, unpublished residue before an exact retry."""
    if not (ENVIRONMENTS / target).exists():
        return
    run((APX, "recovery-clean-unpublished", target,
         "--approve", f"CLEAN UNPUBLISHED {target}"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--action", required=True, choices=("create", "destroy"))
    parser.add_argument("--environment", required=True)
    parser.add_argument("--generation")
    parser.add_argument("--description", default="")
    parser.add_argument("--desktop-preset", default="intermediate",
                        choices=("basic", "intermediate", "complete"))
    parser.add_argument("--desktop-modules", default="")
    parser.add_argument("--lock-token", required=True)
    arguments = parser.parse_args()
    action, target = arguments.action, arguments.environment
    if NAME.fullmatch(target) is None or target == "hub":
        parser.error("invalid Environment")
    if action == "destroy" and (type(arguments.generation) is not str
                                 or GENERATION.fullmatch(arguments.generation) is None):
        parser.error("invalid generation")
    if action == "create" and arguments.generation is not None:
        parser.error("creation takes no generation")

    lock_descriptor = os.open(LOCK, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    lock_metadata = os.fstat(lock_descriptor)
    lock_value = os.read(lock_descriptor, 256).decode().strip()
    if lock_metadata.st_uid != 0 or lock_metadata.st_gid != 0 or lock_value != arguments.lock_token:
        os.close(lock_descriptor)
        raise RuntimeError("a reserva da operação não é confiável")
    try:
        if action == "create":
            write_state(action, target, "planning", 4, "A verificar uma criação anterior…")
            recover_failed_create(target)
        write_state(action, target, "planning", 8, "A validar o plano…")
        operation_plan = plan(action, target, arguments.description,
                              arguments.desktop_preset, arguments.desktop_modules)
        if action == "destroy" and operation_plan.get("generation") != arguments.generation:
            raise RuntimeError("o Environment selecionado mudou; atualiza a lista")
        write_state(action, target, "applying", 28,
                    "A criar o Environment…" if action == "create" else "A apagar os dados do Environment…")
        approval = f"CREATE {target} AS graphical-base" if action == "create" else f"DESTROY {target}"
        run((APX, "environment", action, "--plan", str(operation_plan["digest"]),
             "--approve", approval))
        write_state(action, target, "complete", 100,
                    "Environment criado." if action == "create" else "Environment apagado.")
    except Exception as error:
        write_state(action, target, "failed", 100, str(error)[:300])
        raise
    finally:
        os.close(lock_descriptor)
        try:
            current = LOCK.lstat()
            if not LOCK.is_symlink() and (current.st_dev, current.st_ino) == (lock_metadata.st_dev, lock_metadata.st_ino):
                LOCK.unlink()
        except FileNotFoundError:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
