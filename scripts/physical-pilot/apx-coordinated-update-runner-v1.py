#!/usr/bin/env python3
"""Fail-closed runner for one approved APX coordinated package update."""

from __future__ import annotations

import argparse
import atexit
import fcntl
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
from urllib.parse import urlparse
from urllib.request import urlopen

BASE = Path("/var/lib/apx/coordinated-updates-v1")
TRANSITION_LOCK = Path("/run/apx/machine-transition-v1.lock")
POWER_RESERVATION = Path("/run/apx/system-power-v1.reserved")
ENVIRONMENTS = Path("/var/lib/apx/environments")
NAME = re.compile(r"[a-z](?:[a-z0-9]|-(?=[a-z0-9])){0,26}")
OPERATION = re.compile(r"[0-9]{8}T[0-9]{6}Z-[0-9a-f]{12}")


class UpdateError(RuntimeError): pass


def run(arguments: tuple[str, ...], *, timeout: int | None = None) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(arguments, text=True, capture_output=True, check=False, timeout=timeout,
                            env={"PATH": "/usr/bin", "LC_ALL": "C", "SYSTEMD_COLORS": "0"})
    if result.returncode: raise UpdateError((result.stderr or result.stdout or "command failed")[-1200:])
    return result


def atomic(path: Path, value: dict[str, object]) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        os.write(descriptor, (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()); os.fsync(descriptor)
    finally: os.close(descriptor)
    os.replace(temporary, path)


def target_root(name: str) -> Path:
    return Path("/") if name == "host" else ENVIRONMENTS / name / "root"


def prepare_repository(directory: Path) -> Path:
    database = directory / "repository-db"; database.mkdir(mode=0o711)
    os.chmod(database, 0o711)
    run(("/usr/bin/pacman", "-Sy", "--noconfirm", "--dbpath", str(database),
         "--logfile", str(directory / "repository-sync.log")))
    if not any((database / "sync").glob("*.db")): raise UpdateError("signed repository view is empty")
    return database


def resolve_and_stage(directory: Path, repository: Path, name: str) -> list[Path]:
    root = target_root(name); resolver = directory / "resolver" / name; packages = directory / "packages" / name
    (resolver / "local").mkdir(parents=True, mode=0o700); packages.mkdir(parents=True, mode=0o700)
    local = root / "var/lib/pacman/local"
    if not local.is_dir(): raise UpdateError(f"package database unavailable: {name}")
    shutil.copytree(local, resolver / "local", dirs_exist_ok=True)
    shutil.copytree(repository / "sync", resolver / "sync")
    result = run(("/usr/bin/pacman", "--root", str(root), "--dbpath", str(resolver),
                  "-Sup", "--noconfirm", "--print-format", "%l"))
    urls = [line.strip() for line in result.stdout.splitlines() if line.strip().startswith(("http://", "https://"))]
    staged = []
    for url in urls:
        filename = Path(urlparse(url).path).name
        if not filename or "/" in filename: raise UpdateError("unsafe package URL")
        destination = packages / filename
        if not destination.exists():
            with urlopen(url, timeout=90) as source, destination.open("xb") as output:
                shutil.copyfileobj(source, output)
        staged.append(destination)
    # Pacman verifies every staged archive and signature against the frozen database.
    if staged:
        run(("/usr/bin/pacman", "--root", str(root), "--dbpath", str(resolver),
             "--cachedir", str(packages), "-Sw", "--noconfirm"), timeout=1800)
    return staged


def stop_environments(names: list[str]) -> None:
    if "hub" in names:
        time.sleep(2)
        run(("/var/lib/apx/official-hub-v1/apx-official-hub-graphical-v1.py", "--recover"))
    for name in names:
        if name == "hub": continue
        subprocess.run(("/usr/bin/apx", "environment", "stop", name),
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        record = json.loads((ENVIRONMENTS / name / "registration.json").read_text())
        if record.get("state") != "stopped": raise UpdateError(f"Environment did not stop: {name}")


def snapshots(directory: Path, names: list[str]) -> dict[str, list[str]]:
    rollback = BASE / "rollbacks" / directory.name; rollback.mkdir(parents=True, mode=0o700)
    result: dict[str, list[str]] = {}
    source = run(("/usr/bin/findmnt", "-no", "SOURCE", "/")).stdout.strip().split("[", 1)[0]
    mount = directory / "btrfs-top"; mount.mkdir(mode=0o700)
    run(("/usr/bin/mount", "-o", "subvolid=5,ro", source, str(mount)))
    try:
        host = rollback / "host-root"
        run(("/usr/bin/btrfs", "subvolume", "snapshot", "-r", str(mount / "@"), str(host)))
        result["host"] = [str(host)]
    finally: run(("/usr/bin/umount", str(mount)))
    for name in names:
        paths = []
        for label in ("root", "home"):
            source_path = ENVIRONMENTS / name / label; destination = rollback / f"{name}-{label}"
            run(("/usr/bin/btrfs", "subvolume", "snapshot", "-r", str(source_path), str(destination)))
            paths.append(str(destination))
        result[name] = paths
    return result


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--operation", required=True); args = parser.parse_args()
    if OPERATION.fullmatch(args.operation) is None: raise UpdateError("operation identity differs")
    if POWER_RESERVATION.exists(): raise UpdateError("a Host power confirmation is pending")
    TRANSITION_LOCK.touch(mode=0o600, exist_ok=True)
    transition_descriptor = os.open(TRANSITION_LOCK, os.O_RDWR | os.O_NOFOLLOW)
    atexit.register(os.close, transition_descriptor)
    try: fcntl.flock(transition_descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as error: raise UpdateError("another machine transition is active") from error
    if POWER_RESERVATION.exists(): raise UpdateError("a Host power confirmation became active")
    directory = BASE / "operations" / args.operation
    metadata = directory.lstat()
    if directory.is_symlink() or metadata.st_uid != 0 or metadata.st_gid != 0: raise UpdateError("operation directory is untrusted")
    plan = json.loads((directory / "approved-plan.json").read_text())
    status = {"schema": 1, "operation": args.operation, "state": "preparing", "reboot_required": False}
    atomic(directory / "status.json", status)
    names = [item["name"] for item in plan["targets"] if item["kind"] == "environment"]
    if any(type(name) is not str or NAME.fullmatch(name) is None for name in names): raise UpdateError("target list differs")
    try:
        repository = prepare_repository(directory)
        manifests = {name: resolve_and_stage(directory, repository, name) for name in ["host", *names]}
        status.update({"state": "staged", "package_counts": {name: len(paths) for name, paths in manifests.items()}}); atomic(directory / "status.json", status)
        stop_environments(names)
        status["snapshots"] = snapshots(directory, names); status["state"] = "applying"; atomic(directory / "status.json", status)
        for name in ["host", *names]:
            if manifests[name]: run(("/usr/bin/pacman", "--root", str(target_root(name)), "-U", "--noconfirm",
                                     *(str(path) for path in manifests[name])), timeout=3600)
        status.update({"state": "complete", "reboot_required": bool(manifests["host"]),
                       "message": "Atualização concluída; reinicie quando for conveniente."})
        atomic(directory / "status.json", status)
        subprocess.run(("/usr/bin/wall", "APX: atualização concluída. Abra UPDATE no Hub para ver o resultado; o reinício nunca é automático."), check=False)
        return 0
    except Exception as error:
        status.update({"state": "failed", "error": str(error)[-1000:],
                       "message": "A operação parou; as cópias de segurança foram preservadas e não houve reversão automática."})
        atomic(directory / "status.json", status)
        subprocess.run(("/usr/bin/wall", "APX: a atualização parou. As cópias de segurança foram preservadas; não reinicie antes de verificar."), check=False)
        raise


if __name__ == "__main__": raise SystemExit(main())
