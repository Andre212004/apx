#!/usr/bin/env python3
"""Bounded APX headless runtime used only by the disposable C0-C6 VM.

This is deliberately a closed laboratory adapter: it accepts registered names,
roles and plan digests, never caller-supplied paths or commands.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import uuid


STATE = Path("/var/lib/apx")
RELEASES = STATE / "releases"
ENVIRONMENTS = STATE / "environments"
PLANS = STATE / "plans"
JOURNAL = STATE / "journal" / "operations.jsonl"
SNAPSHOTS = STATE / "snapshots"
ARCHIVES = STATE / "archives"
NAME_RE = re.compile(r"[a-z][a-z0-9-]{0,31}")
ROLES = {"hub", "development", "minimal", "graphical-h0"}
HEADLESS_START_ROLES = {"hub", "development", "minimal"}
RELEASE_IDS = {
    "hub": "hub-headless-v3",
    "development": "development-headless-v1",
    "minimal": "minimal-headless-v1",
    "graphical-h0": "hyprland-h0-v1",
}
QUOTA_LIMITS = {
    "hub": {"root": "4G", "home": "2G"},
    "minimal": {"root": "4G", "home": "2G"},
    "development": {"root": "16G", "home": "8G"},
    "graphical-h0": {"root": "16G", "home": "8G"},
}
EFFECTS = {
    "create": ("root", "home", "configure", "publish"),
    "destroy": ("stop", "unpublish", "remove-home", "remove-root"),
}


class Refusal(RuntimeError):
    pass


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def run(arguments: list[str], *, check: bool = True, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        arguments,
        check=check,
        text=True,
        capture_output=capture,
        env={**os.environ, "LC_ALL": "C"},
    )


def require_root() -> None:
    if os.geteuid() != 0:
        raise Refusal("this laboratory effect requires the host executor identity")


def validate_name(name: str) -> str:
    if not NAME_RE.fullmatch(name):
        raise Refusal("invalid Environment name")
    return name


def validate_role(role: str) -> str:
    if role not in ROLES:
        raise Refusal("role is not admitted")
    return role


def environment_dir(name: str) -> Path:
    return ENVIRONMENTS / validate_name(name)


def registration_path(name: str) -> Path:
    return environment_dir(name) / "registration.json"


def read_json(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise Refusal(f"cannot read authoritative state: {error}") from error
    if not isinstance(value, dict):
        raise Refusal("authoritative state is not an object")
    return value


def atomic_json(path: Path, value: object, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(canonical(value))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        temporary.unlink(missing_ok=True)


def append_event(operation: str, action: str, effect: str, status: str, **extra: object) -> None:
    JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    previous = "0" * 64
    if JOURNAL.exists():
        lines = JOURNAL.read_text().splitlines()
        if lines:
            previous_record = json.loads(lines[-1])
            previous = digest(previous_record)
    event = {
        "schema": 1,
        "operation": operation,
        "action": action,
        "effect": effect,
        "status": status,
        "at": now(),
        "previous": previous,
        **extra,
    }
    with JOURNAL.open("ab") as stream:
        stream.write(canonical(event))
        stream.flush()
        os.fsync(stream.fileno())


def admitted_release(role: str) -> Path:
    release = RELEASES / RELEASE_IDS[validate_role(role)] / "root"
    if not release.is_dir():
        raise Refusal(f"admitted {role} release is absent")
    result = run(["btrfs", "property", "get", "-ts", str(release), "ro"], capture=True)
    if "ro=true" not in result.stdout:
        raise Refusal("release root is not immutable")
    return release


def make_plan(action: str, name: str, role: str | None = None) -> dict[str, object]:
    validate_name(name)
    generation = str(uuid.uuid4())
    if action == "create":
        validate_role(role or "")
        if environment_dir(name).exists():
            raise Refusal("Environment already exists")
        admitted_release(role or "")
    elif action == "destroy":
        generation = str(registration(name)["generation"])
    else:
        raise Refusal("unsupported plan family")
    plan: dict[str, object] = {
        "schema": 1,
        "action": action,
        "name": name,
        "generation": generation,
        "effects": list(EFFECTS[action]),
    }
    if role is not None:
        plan["role"] = role
    identity = digest(plan)
    plan["digest"] = identity
    atomic_json(PLANS / f"{identity}.json", plan)
    return plan


def load_plan(identity: str, action: str) -> dict[str, object]:
    if not re.fullmatch(r"[0-9a-f]{64}", identity):
        raise Refusal("invalid plan digest")
    plan = read_json(PLANS / f"{identity}.json")
    claimed = plan.pop("digest", None)
    actual = digest(plan)
    plan["digest"] = claimed
    if claimed != identity or actual != identity or plan.get("action") != action:
        raise Refusal("plan identity or family mismatch")
    return plan


def registration(name: str) -> dict[str, object]:
    record = read_json(registration_path(name))
    if record.get("name") != name or record.get("state") not in {"stopped", "running"}:
        raise Refusal("invalid registration")
    return record


def machine(name: str) -> str:
    return f"apx-{validate_name(name)}"


def machine_running(name: str) -> bool:
    result = run(["machinectl", "show", machine(name), "--property=State", "--value"], check=False, capture=True)
    return result.returncode == 0 and result.stdout.strip() in {"running", "degraded"}


def create(plan_identity: str, approval: str) -> None:
    require_root()
    plan = load_plan(plan_identity, "create")
    name = str(plan["name"])
    role = str(plan["role"])
    if approval != f"CREATE {name} AS {role}":
        raise Refusal("exact creation approval is absent")
    target = environment_dir(name)
    if target.exists():
        raise Refusal("Environment path already exists")
    operation = str(uuid.uuid4())
    append_event(operation, "create", "operation", "started", name=name, plan=plan_identity)
    target.mkdir(mode=0o700)
    try:
        root = target / "root"
        append_event(operation, "create", "root", "started", name=name)
        run(["btrfs", "subvolume", "snapshot", str(admitted_release(role)), str(root)])
        append_event(operation, "create", "root", "complete", name=name)
        fault("root")

        home = target / "home"
        append_event(operation, "create", "home", "started", name=name)
        run(["btrfs", "subvolume", "create", str(home)])
        apply_limits(name, role)
        if role == "graphical-h0":
            graphical_home = home / "apx"
            graphical_home.mkdir(mode=0o700)
            os.chown(graphical_home, 1000, 1000)
        append_event(operation, "create", "home", "complete", name=name)
        fault("home")

        append_event(operation, "create", "configure", "started", name=name)
        (root / "etc" / "hostname").write_text(machine(name) + "\n")
        (root / "etc" / "machine-id").write_text("")
        if role == "hub":
            (root / "run" / "apx").mkdir(parents=True, exist_ok=True)
        append_event(operation, "create", "configure", "complete", name=name)
        fault("configure")

        record = {
            "schema": 1,
            "name": name,
            "role": role,
            "generation": plan["generation"],
            "release": RELEASE_IDS[role],
            "state": "stopped",
            "created_at": now(),
        }
        append_event(operation, "create", "publish", "started", name=name)
        atomic_json(registration_path(name), record)
        append_event(operation, "create", "publish", "complete", name=name)
        append_event(operation, "create", "operation", "complete", name=name)
    except BaseException:
        append_event(operation, "create", "operation", "uncertain", name=name)
        raise


def fault(effect: str) -> None:
    if os.environ.get("APX_LAB_FAULT_AFTER") == effect:
        os._exit(86)


def apply_limits(name: str, role: str) -> None:
    limits = QUOTA_LIMITS[validate_role(role)]
    for label, limit in limits.items():
        path = environment_dir(name) / label
        identity = run(["btrfs", "inspect-internal", "rootid", str(path)], capture=True).stdout.strip()
        if not identity.isdigit():
            raise Refusal("cannot identify Environment qgroup")
        run(["btrfs", "qgroup", "limit", limit, f"0/{identity}", str(STATE)])
        run(["btrfs", "qgroup", "limit", "-e", limit, f"0/{identity}", str(STATE)])


def start(name: str) -> None:
    require_root()
    record = registration(name)
    if record.get("role") not in HEADLESS_START_ROLES:
        raise Refusal("graphical Environment activation requires the separate H0 device and recovery adapter")
    if machine_running(name):
        print(f"{name}: already running")
        return
    target = environment_dir(name)
    unit = f"apx-environment-{name}.service"
    command = [
        "systemd-run", "--unit", unit, "--collect", "--property=Delegate=yes",
        "--property=KillMode=mixed", "--",
        "systemd-nspawn", "--quiet", "--keep-unit", "--boot",
        f"--machine={machine(name)}", f"--directory={target / 'root'}",
        "--private-users=pick", "--private-users-ownership=chown",
        "--private-network", "--network-veth", "--link-journal=no", "--settings=no",
        f"--bind={target / 'home'}:/home:idmap",
    ]
    if record["role"] == "hub":
        executor_socket = Path("/run/apx/executor.sock")
        if not executor_socket.is_socket():
            raise Refusal("Hub executor endpoint is unavailable")
        command.append("--bind-ro=/run/apx/executor.sock:/run/apx/executor.sock")
    operation = str(uuid.uuid4())
    append_event(operation, "activate", "runtime", "started", name=name)
    run(command, capture=True)
    for _ in range(100):
        if machine_running(name):
            break
        import time
        time.sleep(0.1)
    if not machine_running(name):
        append_event(operation, "activate", "runtime", "uncertain", name=name)
        raise Refusal("Environment did not register as running")
    for _ in range(300):
        readiness = run(
            ["systemctl", "-M", machine(name), "is-system-running"],
            check=False,
            capture=True,
        )
        if readiness.stdout.strip() in {"running", "degraded"}:
            break
        import time
        time.sleep(0.1)
    else:
        append_event(operation, "activate", "runtime", "uncertain", name=name)
        raise Refusal("Environment registered but did not reach a usable system state")
    record["state"] = "running"
    atomic_json(registration_path(name), record)
    append_event(operation, "activate", "runtime", "complete", name=name)


def stop(name: str) -> None:
    require_root()
    record = registration(name)
    operation = str(uuid.uuid4())
    append_event(operation, "stop", "runtime", "started", name=name)
    if machine_running(name):
        run(["machinectl", "poweroff", machine(name)], check=False, capture=True)
        for _ in range(200):
            if not machine_running(name):
                break
            import time
            time.sleep(0.1)
    if machine_running(name):
        append_event(operation, "stop", "runtime", "uncertain", name=name)
        raise Refusal("runtime residue remains")
    run(["systemctl", "reset-failed", f"apx-environment-{name}.service"], check=False)
    record["state"] = "stopped"
    atomic_json(registration_path(name), record)
    append_event(operation, "stop", "runtime", "complete", name=name)


def shell(name: str) -> None:
    require_root()
    registration(name)
    if not machine_running(name):
        start(name)
    os.execvp("machinectl", ["machinectl", "shell", f"root@{machine(name)}"])


def destroy(plan_identity: str, approval: str) -> None:
    require_root()
    plan = load_plan(plan_identity, "destroy")
    name = str(plan["name"])
    if approval != f"DESTROY {name}":
        raise Refusal("exact destruction approval is absent")
    record = registration(name)
    if plan.get("generation") != record.get("generation"):
        raise Refusal("destruction plan generation is stale")
    operation = str(uuid.uuid4())
    append_event(operation, "destroy", "operation", "started", name=name, plan=plan_identity)
    stop(name)
    record_path = registration_path(name)
    append_event(operation, "destroy", "unpublish", "started", name=name)
    record_path.unlink()
    append_event(operation, "destroy", "unpublish", "complete", name=name)
    target = environment_dir(name)
    for label in ("home", "root"):
        path = target / label
        append_event(operation, "destroy", f"remove-{label}", "started", name=name)
        delete_subvolume_tree(path)
        append_event(operation, "destroy", f"remove-{label}", "complete", name=name)
    target.rmdir()
    append_event(operation, "destroy", "operation", "complete", name=name)


def delete_subvolume_tree(path: Path) -> None:
    if not path.exists():
        return
    run(["btrfs", "subvolume", "delete", "-R", str(path)])


def snapshot(name: str) -> str:
    require_root()
    record = registration(name)
    if machine_running(name):
        raise Refusal("snapshot requires a stopped Environment")
    identity = f"{name}-{record['generation']}-{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    target = SNAPSHOTS / identity
    target.mkdir(parents=True)
    run(["btrfs", "subvolume", "snapshot", "-r", str(environment_dir(name) / "root"), str(target / "root")])
    run(["btrfs", "subvolume", "snapshot", "-r", str(environment_dir(name) / "home"), str(target / "home")])
    manifest = {"schema": 1, "snapshot": identity, "name": name, "generation": record["generation"], "created_at": now()}
    atomic_json(target / "manifest.json", manifest, 0o400)
    append_event(str(uuid.uuid4()), "snapshot", "publish", "complete", name=name, snapshot=identity)
    print(identity)
    return identity


def archive(name: str) -> str:
    require_root()
    record = registration(name)
    if machine_running(name):
        raise Refusal("archive requires a stopped Environment")
    snapshot_identity = snapshot(name)
    snapshot_dir = SNAPSHOTS / snapshot_identity
    archive_identity = f"archive-{name}-{record['generation']}-{uuid.uuid4()}"
    target = ARCHIVES / archive_identity
    target.mkdir(parents=True, mode=0o700)
    operation = str(uuid.uuid4())
    append_event(operation, "archive", "streams", "started", name=name, archive=archive_identity)
    hashes: dict[str, str] = {}
    for label in ("root", "home"):
        output = target / f"{label}.btrfs.zst"
        sender = subprocess.Popen(["btrfs", "send", str(snapshot_dir / label)], stdout=subprocess.PIPE)
        assert sender.stdout is not None
        compressor = subprocess.run(["zstd", "-q", "-T0", "-o", str(output)], stdin=sender.stdout)
        sender.stdout.close()
        sender_result = sender.wait()
        if sender_result != 0 or compressor.returncode != 0:
            append_event(operation, "archive", "streams", "uncertain", name=name, archive=archive_identity)
            raise Refusal("archive stream creation failed")
        hashes[label] = hashlib.sha256(output.read_bytes()).hexdigest()
    manifest = {
        "schema": 1,
        "archive": archive_identity,
        "source_name": name,
        "source_generation": record["generation"],
        "role": record["role"],
        "release": record["release"],
        "snapshot": snapshot_identity,
        "streams": hashes,
        "created_at": now(),
    }
    atomic_json(target / "manifest.json", manifest, 0o400)
    append_event(operation, "archive", "publish", "complete", name=name, archive=archive_identity)
    print(archive_identity)
    return archive_identity


def validate_archive(identity: str) -> Path:
    if not re.fullmatch(r"archive-[a-z0-9-]{1,160}", identity):
        raise Refusal("invalid archive identity")
    path = ARCHIVES / identity
    manifest = read_json(path / "manifest.json")
    if manifest.get("archive") != identity or set(manifest.get("streams", {})) != {"root", "home"}:
        raise Refusal("archive manifest mismatch")
    for label in ("root", "home"):
        stream = path / f"{label}.btrfs.zst"
        if not stream.is_file() or hashlib.sha256(stream.read_bytes()).hexdigest() != manifest["streams"][label]:
            raise Refusal("archive stream identity mismatch")
    return path


def restore(archive_identity: str, name: str, approval: str) -> None:
    require_root()
    validate_name(name)
    if approval != f"RESTORE {archive_identity} AS {name}":
        raise Refusal("exact restore approval is absent")
    if environment_dir(name).exists():
        raise Refusal("restore destination already exists")
    archive_path = validate_archive(archive_identity)
    manifest = read_json(archive_path / "manifest.json")
    target = environment_dir(name)
    target.mkdir(mode=0o700)
    operation = str(uuid.uuid4())
    append_event(operation, "restore", "operation", "started", name=name, archive=archive_identity)
    try:
        for label in ("root", "home"):
            stream = subprocess.Popen(["zstd", "-q", "-d", "-c", str(archive_path / f"{label}.btrfs.zst")], stdout=subprocess.PIPE)
            assert stream.stdout is not None
            receiver = subprocess.run(["btrfs", "receive", str(target)], stdin=stream.stdout, capture_output=True, text=True)
            stream.stdout.close()
            stream_result = stream.wait()
            if stream_result != 0 or receiver.returncode != 0:
                raise Refusal(f"restore receive failed: {receiver.stderr.strip()}")
            run(["btrfs", "property", "set", "-f", "-ts", str(target / label), "ro", "false"])
        apply_limits(name, str(manifest["role"]))
        root = target / "root"
        (root / "etc" / "hostname").write_text(machine(name) + "\n")
        (root / "etc" / "machine-id").write_text("")
        record = {
            "schema": 1,
            "name": name,
            "role": manifest["role"],
            "generation": str(uuid.uuid4()),
            "release": manifest["release"],
            "state": "stopped",
            "created_at": now(),
            "restored_from": archive_identity,
        }
        atomic_json(registration_path(name), record)
        append_event(operation, "restore", "operation", "complete", name=name, archive=archive_identity)
    except BaseException:
        append_event(operation, "restore", "operation", "uncertain", name=name, archive=archive_identity)
        raise


def list_environments(as_json: bool) -> None:
    values: list[dict[str, object]] = []
    if ENVIRONMENTS.exists():
        for child in sorted(ENVIRONMENTS.iterdir()):
            if not NAME_RE.fullmatch(child.name) or not (child / "registration.json").is_file():
                continue
            record = registration(child.name)
            record = {**record, "observed_running": machine_running(child.name)}
            values.append(record)
    if as_json:
        print(json.dumps(values, sort_keys=True, indent=2))
    elif not values:
        print("No APX Environments are registered.")
    else:
        for value in values:
            print(f"{value['name']}\t{value['role']}\t{value['state']}\t{value['generation']}")


def status() -> None:
    failures = run(["systemctl", "--failed", "--no-legend"], check=False, capture=True).stdout.strip()
    print("APX disposable headless runtime")
    print(f"state={STATE} filesystem={run(['findmnt', '-n', '-o', 'FSTYPE', str(STATE)], capture=True).stdout.strip()}")
    print(f"host_system={'healthy' if not failures else 'degraded'}")
    list_environments(False)


def recover() -> None:
    require_root()
    uncertain: set[str] = set()
    if JOURNAL.exists():
        operations: dict[str, str] = {}
        for line in JOURNAL.read_text().splitlines():
            event = json.loads(line)
            if event.get("effect") == "operation":
                operations[str(event["operation"])] = str(event["status"])
        uncertain = {operation for operation, state in operations.items() if state != "complete"}
    print(json.dumps({"uncertain_operations": sorted(uncertain), "policy": "preserve-and-inspect"}, indent=2))


def recover_unpublished(name: str, approval: str) -> None:
    require_root()
    validate_name(name)
    if approval != f"CLEAN UNPUBLISHED {name}":
        raise Refusal("exact recovery cleanup approval is absent")
    target = environment_dir(name)
    if registration_path(name).exists() or machine_running(name) or not target.is_dir():
        raise Refusal("recovery target is published, running, or absent")
    operation: str | None = None
    action: str | None = None
    if JOURNAL.exists():
        for line in reversed(JOURNAL.read_text().splitlines()):
            event = json.loads(line)
            if (
                event.get("name") == name
                and event.get("action") in {"create", "restore"}
                and event.get("effect") == "operation"
                and event.get("status") in {"started", "uncertain"}
            ):
                operation = str(event["operation"])
                action = str(event["action"])
                break
    if operation is None:
        raise Refusal("no matching uncertain unpublished operation")
    for label in ("home", "root"):
        delete_subvolume_tree(target / label)
    remaining = list(target.iterdir())
    if remaining:
        raise Refusal("unrecognized recovery content is preserved")
    target.rmdir()
    append_event(operation, action or "recovery", "operation", "complete", name=name, recovery="approved-clean-unpublished")


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="apx")
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser("status")
    commands.add_parser("recovery-status")
    recovery_clean = commands.add_parser("recovery-clean-unpublished")
    recovery_clean.add_argument("name")
    recovery_clean.add_argument("--approve", required=True)
    environment = commands.add_parser("environment")
    sub = environment.add_subparsers(dest="environment_command", required=True)
    listing = sub.add_parser("list")
    listing.add_argument("--json", action="store_true")
    create_plan = sub.add_parser("create-plan")
    create_plan.add_argument("name")
    create_plan.add_argument("--role", required=True, choices=sorted(ROLES))
    create_apply = sub.add_parser("create")
    create_apply.add_argument("--plan", required=True)
    create_apply.add_argument("--approve", required=True)
    for command in ("start", "stop", "shell", "snapshot", "archive"):
        item = sub.add_parser(command)
        item.add_argument("name")
    destroy_plan = sub.add_parser("destroy-plan")
    destroy_plan.add_argument("name")
    destroy_apply = sub.add_parser("destroy")
    destroy_apply.add_argument("--plan", required=True)
    destroy_apply.add_argument("--approve", required=True)
    restore_apply = sub.add_parser("restore")
    restore_apply.add_argument("--archive", required=True)
    restore_apply.add_argument("--name", required=True)
    restore_apply.add_argument("--approve", required=True)
    return root


def main() -> int:
    arguments = parser().parse_args()
    if arguments.command == "status":
        status()
    elif arguments.command == "recovery-status":
        recover()
    elif arguments.command == "recovery-clean-unpublished":
        recover_unpublished(arguments.name, arguments.approve)
    elif arguments.environment_command == "list":
        list_environments(arguments.json)
    elif arguments.environment_command == "create-plan":
        print(json.dumps(make_plan("create", arguments.name, arguments.role), sort_keys=True, indent=2))
    elif arguments.environment_command == "create":
        create(arguments.plan, arguments.approve)
    elif arguments.environment_command == "start":
        start(arguments.name)
    elif arguments.environment_command == "stop":
        stop(arguments.name)
    elif arguments.environment_command == "shell":
        shell(arguments.name)
    elif arguments.environment_command == "snapshot":
        snapshot(arguments.name)
    elif arguments.environment_command == "archive":
        archive(arguments.name)
    elif arguments.environment_command == "destroy-plan":
        print(json.dumps(make_plan("destroy", arguments.name), sort_keys=True, indent=2))
    elif arguments.environment_command == "destroy":
        destroy(arguments.plan, arguments.approve)
    elif arguments.environment_command == "restore":
        restore(arguments.archive, arguments.name, arguments.approve)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (Refusal, subprocess.CalledProcessError) as error:
        print(f"APX refused: {error}", file=sys.stderr)
        raise SystemExit(2)
