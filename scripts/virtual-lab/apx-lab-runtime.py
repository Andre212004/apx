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
import stat
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
ROLES = {"hub", "development", "minimal", "graphical-h0", "graphical-base", "hub-graphical"}
HEADLESS_START_ROLES = {"hub", "development", "minimal"}
GRAPHICAL_ROLES = {"graphical-h0", "graphical-base", "hub-graphical"}
HUB_ROLES = {"hub", "hub-graphical"}
GRAPHICAL_CONFIG_ASSETS = {
    "alacritty/alacritty.toml": "14f9191aec4f69568e4c12bba0b96c3cf90989f0a2295eb79bf1a277b7b6a3be",
    "fastfetch/apx-logo.txt": "cd7ae1943f3b4da9c751e93a1f19f5c12594ae35a28dce0d80fcfaa8f7149077",
    "fastfetch/config.jsonc": "9c8f7b3184452b42c3e8670805cf7215fa073a7fe32f25d9251a17e08bc4c736",
    "hyprland/hyprland.conf": "3e143678ca6b19711d71a716a2f8411997772a841614cc800e9b9db070c4cbef",
    "rofi/config.rasi": "2894cd7636fcf0f03f1a7c19a1008cb8b0c162ac5fae4e9fa85dfe7484a2aa78",
    "waybar/config.json": "7a045de24f89c69be7e373cc7dc82bb06b62b0a8ee15ec41719fbce0f0de2d2f",
    "waybar/style.css": "4e649de831c068be9ff05d0c9d6ad03351e1b1a1c44ad752b44a8c353bcd90ca",
}
MAX_GRAPHICAL_CONFIG_BYTES = 1024 * 1024
RELEASE_IDS = {
    "hub": "hub-headless-v4",
    "development": "development-headless-v1",
    "minimal": "minimal-headless-v1",
    "graphical-h0": "hyprland-h0-v1",
    "graphical-base": "hyprland-base-v1",
    "hub-graphical": "hyprland-base-v1",
}
HOST_STORAGE_RESERVE_BYTES = 32 * 1024**3
STORAGE_POLICY = "shared-flexible-pool-with-host-reserve"
LOCAL_ADMIN_MARKER = "/etc/apx/local-admin-v1"
NETWORK_ADAPTER = "/usr/lib/apx/apx-environment-network-v1.py"
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
    if name.startswith("apx-"):
        raise Refusal("logical Environment name must not use the derived apx- prefix")
    return name


def validate_role(role: str) -> str:
    if role not in ROLES:
        raise Refusal("role is not admitted")
    return role


def validate_role_assignment(name: str, role: str) -> tuple[str, str]:
    """Reserve every Hub role for the canonical Hub logical identity."""
    validate_name(name)
    validate_role(role)
    if name == "hub" and role not in HUB_ROLES:
        raise Refusal("the Hub name requires an admitted Hub role")
    if name != "hub" and role in HUB_ROLES:
        raise Refusal("Hub roles are reserved for the canonical Hub name")
    return name, role


def copy_graphical_config_seed(seed: Path, destination: Path, uid: int = 1000, gid: int = 1000) -> None:
    """Copy exactly the admitted regular files from an immutable release seed."""
    if not seed.is_dir() or seed.is_symlink() or destination.exists():
        raise Refusal("graphical configuration seed is absent or unsafe")
    config_directories = {relative.split("/", 1)[0] for relative in GRAPHICAL_CONFIG_ASSETS}
    expected_entries = set(GRAPHICAL_CONFIG_ASSETS) | config_directories
    observed_entries: set[str] = set()
    for entry in seed.rglob("*"):
        relative = entry.relative_to(seed).as_posix()
        observed_entries.add(relative)
        metadata = entry.lstat()
        if relative in GRAPHICAL_CONFIG_ASSETS:
            if not stat.S_ISREG(metadata.st_mode):
                raise Refusal("graphical configuration asset is not a regular file")
        elif relative in config_directories:
            if not stat.S_ISDIR(metadata.st_mode) or entry.is_symlink():
                raise Refusal("graphical configuration directory is unsafe")
        else:
            raise Refusal("graphical configuration seed contains an unapproved entry")
    if observed_entries != expected_entries:
        raise Refusal("graphical configuration seed is incomplete")

    content: dict[str, bytes] = {}
    for relative, expected_digest in GRAPHICAL_CONFIG_ASSETS.items():
        path = seed / relative
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
        try:
            value = os.read(descriptor, MAX_GRAPHICAL_CONFIG_BYTES + 1)
            if os.read(descriptor, 1) or len(value) > MAX_GRAPHICAL_CONFIG_BYTES:
                raise Refusal("graphical configuration asset exceeds the size limit")
        finally:
            os.close(descriptor)
        if hashlib.sha256(value).hexdigest() != expected_digest:
            raise Refusal("graphical configuration asset digest differs")
        content[relative] = value

    destination.mkdir(mode=0o700)
    os.chown(destination, uid, gid)
    for directory in sorted(config_directories):
        target_directory = destination / directory
        target_directory.mkdir(mode=0o700)
        os.chown(target_directory, uid, gid)
    for relative, value in content.items():
        target = destination / relative
        descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC, 0o600)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(value)
                stream.flush()
                os.fsync(stream.fileno())
        except BaseException:
            target.unlink(missing_ok=True)
            raise
        os.chown(target, uid, gid)


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
        validate_role_assignment(name, role or "")
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
    validate_role_assignment(name, str(record.get("role", "")))
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
    validate_role_assignment(name, role)
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
        verify_shared_storage_reserve()
        user_home = home / "apx"
        user_home.mkdir(mode=0o700)
        os.chown(user_home, 1000, 1000)
        skeleton = root / "etc/skel"
        if skeleton.is_dir() and not skeleton.is_symlink():
            for source in sorted(skeleton.iterdir()):
                metadata = source.lstat()
                if not stat.S_ISREG(metadata.st_mode) or source.is_symlink():
                    raise Refusal("release skeleton contains a non-regular entry")
                destination = user_home / source.name
                shutil.copy2(source, destination, follow_symlinks=False)
                os.chown(destination, 1000, 1000)
        append_event(operation, "create", "home", "complete", name=name)
        fault("home")

        append_event(operation, "create", "configure", "started", name=name)
        (root / "etc" / "hostname").write_text(machine(name) + "\n")
        (root / "etc" / "machine-id").write_text("")
        if role in {"graphical-base", "hub-graphical"}:
            seed = root / "usr/share/apx/config-seeds/hyprland-minimal-v1"
            destination = home / "apx/.config"
            copy_graphical_config_seed(seed, destination)
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


def verify_shared_storage_reserve() -> None:
    """Refuse new growth when the Host recovery reserve would be crossed."""
    stats = os.statvfs(STATE)
    available = stats.f_bavail * stats.f_frsize
    if available < HOST_STORAGE_RESERVE_BYTES:
        raise Refusal("shared Environment pool reached the protected Host reserve")


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
        run([NETWORK_ADAPTER, "apply", "--environment", "hub"])
    operation = str(uuid.uuid4())
    append_event(operation, "activate", "runtime", "started", name=name)
    try:
        run(command, capture=True)
    except BaseException:
        if record["role"] == "hub":
            run([NETWORK_ADAPTER, "remove", "--environment", "hub"], check=False)
        raise
    for _ in range(100):
        if machine_running(name):
            break
        import time
        time.sleep(0.1)
    if not machine_running(name):
        append_event(operation, "activate", "runtime", "uncertain", name=name)
        if record["role"] == "hub":
            run([NETWORK_ADAPTER, "remove", "--environment", "hub"], check=False)
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
        run(["systemctl", "stop", unit], check=False, capture=True)
        if record["role"] == "hub":
            run([NETWORK_ADAPTER, "remove", "--environment", "hub"], check=False)
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
    run(
        ["systemctl", "reset-failed", f"apx-environment-{name}.service"],
        check=False, capture=True,
    )
    if record.get("role") == "hub":
        run([NETWORK_ADAPTER, "remove", "--environment", "hub"], check=False)
    record["state"] = "stopped"
    atomic_json(registration_path(name), record)
    append_event(operation, "stop", "runtime", "complete", name=name)


def shell(name: str, *, recovery_root: bool = False) -> None:
    require_root()
    registration(name)
    if not machine_running(name):
        start(name)
    user = "root" if recovery_root else "apx"
    border = "=" * 72
    print(f"\n{border}")
    print(f"APX >>> ESTÁS A ENTRAR NO ENVIRONMENT '{name}' COMO '{user}'")
    print("APX >>> O PRÓXIMO PROMPT NÃO É O HOST. Alterações ficam neste Environment.")
    if recovery_root:
        print("APX >>> MODO ROOT DE RECUPERAÇÃO: usa apenas para reparar este Environment.")
    print(f"{border}\n", flush=True)
    result: subprocess.CompletedProcess[str] | None = None
    try:
        result = run(["machinectl", "shell", f"{user}@{machine(name)}"], check=False)
    finally:
        print(f"\n{border}")
        print(f"APX <<< SAÍSTE DO ENVIRONMENT '{name}'")
        print("APX <<< ESTÁS DE VOLTA AO HOST 'apx-host' COMO ROOT.")
        print("APX <<< Confirma o prompt antes de executar o próximo comando.")
        print(f"{border}\n", flush=True)
    if result is None or result.returncode:
        raise Refusal("Environment terminal session ended with an error")


def local_admin_state(target: str) -> tuple[str, str, str, str, str]:
    """Observe fixed enrollment facts without trusting machinectl's exit status."""
    observe = (
        "set -eu; "
        "marker=absent; test -e /etc/apx/local-admin-v1 && marker=present; "
        "sudo=absent; test -x /usr/bin/sudo && sudo=present; "
        "set -- $(/usr/bin/passwd -S apx); password=$2; "
        "wheel=absent; "
        "/usr/bin/id -nG apx | /usr/bin/tr ' ' '\\n' "
        "| /usr/bin/grep -Fxq wheel && wheel=present; "
        "policy=absent; "
        "if test -e /etc/sudoers.d/10-apx-local-admin; then "
        " policy=invalid; "
        " if test \"$(/usr/bin/stat -c '%a:%u:%g' "
        "/etc/sudoers.d/10-apx-local-admin)\" = '440:0:0' "
        " && /usr/bin/grep -Fxq '%wheel ALL=(ALL:ALL) ALL' "
        "/etc/sudoers.d/10-apx-local-admin; then policy=ready; fi; "
        "fi; "
        "/usr/bin/printf 'APX_LOCAL_ADMIN_V1:%s:%s:%s:%s:%s\\n' "
        "\"$marker\" \"$sudo\" \"$password\" \"$wheel\" \"$policy\""
    )
    result = run(
        ["machinectl", "shell", f"root@{target}", "/usr/bin/bash", "-lc", observe],
        check=False, capture=True,
    )
    prefix = "APX_LOCAL_ADMIN_V1:"
    lines = [line for line in result.stdout.splitlines() if line.startswith(prefix)]
    if len(lines) != 1:
        raise Refusal("Hub local administrator state is absent or ambiguous")
    fields = tuple(lines[0][len(prefix):].split(":"))
    if len(fields) != 5:
        raise Refusal("Hub local administrator state is malformed")
    marker, sudo, password, wheel, policy = fields
    if marker not in {"absent", "present"} \
            or sudo not in {"absent", "present"} \
            or password not in {"L", "P", "NP"} \
            or wheel not in {"absent", "present"} \
            or policy not in {"absent", "invalid", "ready"}:
        raise Refusal("Hub local administrator state contains an unknown value")
    return marker, sudo, password, wheel, policy


def enroll_local_admin(name: str) -> None:
    """Enroll one Environment-local password without copying a Host secret."""
    require_root()
    record = registration(name)
    if name != "hub" or record.get("role") != "hub":
        raise Refusal("local administrator enrollment is fixed to the canonical headless Hub")
    if not machine_running(name):
        start(name)
    target = machine(name)
    marker, sudo, password, wheel, policy = local_admin_state(target)
    if sudo != "present":
        raise Refusal("Hub release does not contain sudo")
    if (marker, password, wheel, policy) == ("present", "P", "present", "ready"):
        raise Refusal("Hub local administrator is already enrolled")
    if marker == "present":
        raise Refusal("Hub local administrator marker exists but enrollment is incomplete")
    fixed_prepare = (
        "set -eu; "
        "/usr/bin/usermod -aG wheel apx; "
        "/usr/bin/install -d -m 0755 /etc/apx /etc/sudoers.d; "
        "/usr/bin/printf '%s\\n' '%wheel ALL=(ALL:ALL) ALL' "
        "| /usr/bin/install -m 0440 /dev/stdin /etc/sudoers.d/10-apx-local-admin"
    )
    run(["machinectl", "shell", f"root@{target}", "/usr/bin/bash", "-lc", fixed_prepare])
    print("Define agora uma palavra-passe exclusiva deste Hub para o utilizador apx.")
    run(["machinectl", "shell", f"root@{target}", "/usr/bin/passwd", "apx"])
    marker, sudo, password, wheel, policy = local_admin_state(target)
    if (marker, sudo, password, wheel, policy) != (
        "absent", "present", "P", "present", "ready"
    ):
        raise Refusal("password enrollment did not complete; no enrollment marker was written")
    run(["machinectl", "shell", f"root@{target}", "/usr/bin/touch", LOCAL_ADMIN_MARKER])
    marker, sudo, password, wheel, policy = local_admin_state(target)
    if (marker, sudo, password, wheel, policy) != (
        "present", "present", "P", "present", "ready"
    ):
        raise Refusal("Hub local administrator final state differs")
    print("Hub local administrator enrolled; the Host password was not requested or copied.")


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
    validate_role_assignment(name, str(manifest.get("role", "")))
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
        verify_shared_storage_reserve()
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
    for command in ("start", "stop", "shell", "shell-root", "snapshot", "archive",
                    "enroll-local-admin"):
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
    elif arguments.environment_command == "shell-root":
        shell(arguments.name, recovery_root=True)
    elif arguments.environment_command == "enroll-local-admin":
        enroll_local_admin(arguments.name)
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
