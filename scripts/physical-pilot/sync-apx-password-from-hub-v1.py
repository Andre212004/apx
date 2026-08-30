#!/usr/bin/env python3
"""Copy the owner-changed Hub password hash to trusted APX accounts."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import time


ENVIRONMENTS = Path("/var/lib/apx/environments")
BACKUPS = Path("/var/lib/apx/backups")
NAME = re.compile(r"[a-z](?:[a-z0-9]|-(?=[a-z0-9])){0,26}")


def shadow(path: Path, account: str = "apx") -> tuple[list[str], str, os.stat_result]:
    if account not in {"apx", "root"}:
        raise RuntimeError("a conta de destino não é admitida")
    info = path.lstat(); raw = path.read_bytes()
    if path.is_symlink() or not path.is_file() or len(raw) > 128 * 1024 \
            or stat.S_IMODE(info.st_mode) != 0o600:
        raise RuntimeError(f"o shadow de {path} não é confiável")
    text = raw.decode(); lines = text.splitlines()
    prefix = account + ":"
    matches = [line for line in lines if line.startswith(prefix)]
    if len(matches) != 1:
        raise RuntimeError(f"a conta {account} de {path} é ambígua")
    password_hash = matches[0].split(":", 2)[1]
    if not (password_hash.startswith("$y$") or password_hash.startswith("$6$")) \
            or not 40 <= len(password_hash) <= 512:
        raise RuntimeError("a nova palavra-passe do HUB não tem um hash admitido")
    return lines, password_hash, info


def registration(directory: Path) -> dict[str, object]:
    path = directory / "registration.json"
    info = path.lstat(); raw = path.read_bytes(); value = json.loads(raw)
    if path.is_symlink() or not path.is_file() or info.st_uid != 0 or info.st_gid != 0 \
            or len(raw) > 8192 or type(value) is not dict or value.get("name") != directory.name:
        raise RuntimeError(f"o registo de {directory.name} não é confiável")
    return value


def replace_hash(path: Path, account: str, new_hash: str, backup: Path) -> None:
    lines, _old_hash, info = shadow(path, account)
    prefix = account + ":"
    updated = []
    for line in lines:
        if line.startswith(prefix):
            fields = line.split(":"); fields[1] = new_hash; line = ":".join(fields)
        updated.append(line)
    shutil.copy2(path, backup, follow_symlinks=False)
    os.chmod(backup, 0o600)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        os.write(descriptor, ("\n".join(updated) + "\n").encode()); os.fsync(descriptor)
        os.fchown(descriptor, info.st_uid, info.st_gid); os.fchmod(descriptor, 0o600)
    finally:
        os.close(descriptor)
    os.replace(temporary, path)
    _lines, verified_hash, verified = shadow(path, account)
    if verified_hash != new_hash or (verified.st_uid, verified.st_gid) != (info.st_uid, info.st_gid):
        raise RuntimeError(f"a palavra-passe de {path} não ficou sincronizada")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm", required=True)
    parser.add_argument("--include-host-root", action="store_true")
    arguments = parser.parse_args()
    if os.geteuid() != 0 or arguments.confirm != "SYNC APX PASSWORD" \
            or Path("/etc/hostname").read_text().strip() != "apx-host":
        raise RuntimeError("a confirmação ou a identidade do Host diferem")
    machines = subprocess.run(("/usr/bin/machinectl", "list", "--no-legend"),
                              text=True, capture_output=True, check=True).stdout.splitlines()
    if [line.split()[0] for line in machines if line.split()] != ["apx-hub"]:
        raise RuntimeError("o HUB não é o único Environment ativo")
    _hub_lines, hub_hash, _hub_info = shadow(ENVIRONMENTS / "hub/root/etc/shadow")
    targets: list[tuple[Path, str, str]] = []
    if arguments.include_host_root:
        targets.append((Path("/etc/shadow"), "host-root.shadow", "root"))
    for directory in sorted(ENVIRONMENTS.iterdir()):
        if not directory.is_dir() or directory.name == "hub" or NAME.fullmatch(directory.name) is None:
            continue
        try:
            record = registration(directory)
        except FileNotFoundError:
            continue
        if record.get("state") != "stopped" or record.get("role") != "graphical-base":
            raise RuntimeError(f"{directory.name} não está parado ou não é um Environment gráfico")
        targets.append((directory / "root/etc/shadow", f"{directory.name}.shadow", "apx"))
    backup = BACKUPS / (time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()) + "-apx-password-sync-v1")
    backup.mkdir(mode=0o700)
    for target, _backup_name, account in targets:
        shadow(target, account)
    attempted: list[tuple[Path, Path]] = []
    try:
        for target, backup_name, account in targets:
            saved = backup / backup_name
            attempted.append((target, saved))
            replace_hash(target, account, hub_hash, saved)
    except Exception:
        for target, saved in attempted:
            if saved.is_file():
                shutil.copy2(saved, target, follow_symlinks=False)
        raise
    environment_count = len(targets) - int(arguments.include_host_root)
    host_result = " and Host root" if arguments.include_host_root else ""
    print(f"APX password hash synchronized to {environment_count} stopped Environments"
          f"{host_result}; backup: {backup}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as error:
        print(f"APX password synchronization failed: {error}", file=__import__("sys").stderr)
        raise SystemExit(2)
