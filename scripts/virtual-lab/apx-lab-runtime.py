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

try:
    from apx_environment_features import local_packages_for, packages_for, validate_selection
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
    from apx_environment_features import local_packages_for, packages_for, validate_selection


STATE = Path("/var/lib/apx")
RELEASES = STATE / "releases"
ENVIRONMENTS = STATE / "environments"
PLANS = STATE / "plans"
JOURNAL = STATE / "journal" / "operations.jsonl"
SNAPSHOTS = STATE / "snapshots"
ARCHIVES = STATE / "archives"
BACKUPS = STATE / "backups"
NAME_RE = re.compile(r"[a-z][a-z0-9-]{0,31}")
ROLES = {"hub", "development", "minimal", "graphical-h0", "graphical-base", "hub-graphical"}
HEADLESS_START_ROLES = {"hub", "development", "minimal"}
GRAPHICAL_ROLES = {"graphical-h0", "graphical-base", "hub-graphical"}
HUB_ROLES = {"hub", "hub-graphical"}
GRAPHICAL_CONFIG_ASSETS = {
    "alacritty/alacritty.toml": "14f9191aec4f69568e4c12bba0b96c3cf90989f0a2295eb79bf1a277b7b6a3be",
    "fastfetch/apx-logo.txt": "cd7ae1943f3b4da9c751e93a1f19f5c12594ae35a28dce0d80fcfaa8f7149077",
    "fastfetch/config.jsonc": "9c8f7b3184452b42c3e8670805cf7215fa073a7fe32f25d9251a17e08bc4c736",
    "hyprland/hyprland.conf": "8d793c51f1fb5195d12636ebc504d6c80cfac836245bacbcf5f90ac769a925ac",
    "rofi/config.rasi": "2894cd7636fcf0f03f1a7c19a1008cb8b0c162ac5fae4e9fa85dfe7484a2aa78",
    "waybar/config.json": "7a045de24f89c69be7e373cc7dc82bb06b62b0a8ee15ec41719fbce0f0de2d2f",
    "waybar/style.css": "4e649de831c068be9ff05d0c9d6ad03351e1b1a1c44ad752b44a8c353bcd90ca",
}
DESKTOP_CONFIG_SEED = Path("/usr/share/apx/config-seeds/desktop-essential-v1")
DESKTOP_CONFIG_ASSETS = {
    "environment-config.json": "eebaa9be26aaa5d120ec71d7d68c17c326714b51b46961fd4651f30bdb75da88",
    "hub-config.json": "eac4219dc026fab9ea2bfd34d51dc9bcb69418fa9b2a727b692112f2160c40eb",
    "style.css": "f26c8dec509c50ae56cf7f5fe2861266a2056ca4667493b94e186a801e58c80a",
}
ENVIRONMENT_SHELL_SEED = Path("/usr/share/apx/config-seeds/environment-shell-v1")
LOCAL_PACKAGE_ARTIFACTS = STATE / "package-artifacts"
LOCAL_PACKAGE_MANIFESTS = {
    "brave-bin": "brave-bin-v1.json",
    "nvidia-utils": "nvidia-utils-v1.json",
}
ENVIRONMENT_SHELL_ASSETS = {
    "hypr/hypridle.conf": "dc34b120018d969d9b873265179ac8013e175252fdb87d0e2fe3846795d2a0e9",
    "hypr/hyprlock.conf": "a3486791844e0e298a1a1a617dc8006ebb288a93f25c0619e57e2c2f72f53c99",
    "hypr/hyprland.lua": "ec60c435f182dfef77a9beaa90359e3a65802f6779867d9a4c955f2381d55cd3",
    "hyprland/hyprland.conf": "43e023a29d459692c7ff1b6b8178cf483d2c37db5b7f20ae9f3406a4771c55c8",
    "local/bin/apx-detached-launch": "40970a9ed235a6799913211dc135c66222ee55e15d5d38e5cfe5d2feafd785ef",
    "local/bin/apx-host-console-open": "ed33a55eb6ac1eb1682989efd41ad26c2b12549f0dcfd056252a4f239d94b229",
    "local/bin/apx-host-console-terminal": "187025f24fda099acc85a7b82b0e0cacfd979f86feca77219911e661e7ec963e",
    "local/bin/apx-laptop-action-v1": "0edd10c264318719007c59831c097ec9c8e3fa8b3068fb7494f06523e617c7f7",
    "local/bin/apx-shortcuts-v1": "c94ec111c09c46cfd58e4c74b400d224e736e593754c8e1b9896eca9ea288995",
    "local/bin/apx-shell-v1": "f5f8e6aeb729ea92c1561c6fe90c00e4692d17272e469f06ed7f7fbbccf5aca4",
    "quickshell/apx/calendar_store.py": "e23e6d4121f8b96647e2c0d8a8d1263e4d51f8f6d60dabebc9d3a6fce5379136",
    "quickshell/apx/shell.qml": "d2e40450ca599702197d3e4c14116bb943487bd59f36cf4ad4012b82efbb4cdd",
}
MAX_GRAPHICAL_CONFIG_BYTES = 1024 * 1024
RELEASE_IDS = {
    "hub": "hub-headless-v4",
    "development": "development-headless-v1",
    "minimal": "minimal-headless-v1",
    "graphical-h0": "hyprland-h0-v1",
    "graphical-base": "hyprland-base-v2",
    "hub-graphical": "hyprland-base-v2",
}
HOST_STORAGE_RESERVE_BYTES = 96 * 1024**3
STORAGE_POLICY = "bounded-environments-with-protected-host-reserve"
ENVIRONMENT_STORAGE_LIMITS = {
    "hub": ("16G", "32G"),
    "development": ("32G", "64G"),
    "minimal": ("8G", "16G"),
    "graphical-h0": ("32G", "64G"),
    "graphical-base": ("32G", "64G"),
    "hub-graphical": ("16G", "32G"),
}
ENVIRONMENT_RUNTIME_LIMITS = {
    "hub": ("600%", "10G", "12G", "4096"),
    "development": ("600%", "10G", "12G", "4096"),
    "minimal": ("200%", "3G", "4G", "1024"),
}
LOCAL_ADMIN_MARKER = "/etc/apx/local-admin-v1"
NETWORK_ADAPTER = "/usr/lib/apx/apx-environment-network-v1.py"
EFFECTS = {
    "create": ("root", "home", "configure", "publish"),
    "destroy": (
        "stop", "purge-snapshots", "purge-archives", "purge-backups", "remove-home",
        "remove-root", "purge-metadata", "unpublish", "purge-plans",
    ),
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


def copy_desktop_config_seed(
    seed: Path, destination: Path, role: str, uid: int = 1000, gid: int = 1000,
) -> None:
    """Overlay the exact reviewed Waybar profile into a newly copied config."""
    if role not in {"graphical-base", "hub-graphical"}:
        raise Refusal("desktop configuration role is unsupported")
    if not seed.is_dir() or seed.is_symlink():
        raise Refusal("desktop configuration seed is absent or unsafe")
    if {item.name for item in seed.iterdir()} != set(DESKTOP_CONFIG_ASSETS):
        raise Refusal("desktop configuration seed entries differ")
    content: dict[str, bytes] = {}
    for name, expected_digest in DESKTOP_CONFIG_ASSETS.items():
        source = seed / name
        descriptor = os.open(source, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
        try:
            value = os.read(descriptor, MAX_GRAPHICAL_CONFIG_BYTES + 1)
            if os.read(descriptor, 1) or len(value) > MAX_GRAPHICAL_CONFIG_BYTES:
                raise Refusal("desktop configuration asset exceeds the size limit")
        finally:
            os.close(descriptor)
        if hashlib.sha256(value).hexdigest() != expected_digest:
            raise Refusal("desktop configuration asset digest differs")
        content[name] = value
    waybar = destination / "waybar"
    if not waybar.is_dir() or waybar.is_symlink():
        raise Refusal("Waybar destination is absent or unsafe")
    selected = "hub-config.json" if role == "hub-graphical" else "environment-config.json"
    for source_name, destination_name in ((selected, "config.json"), ("style.css", "style.css")):
        target = waybar / destination_name
        metadata = target.lstat()
        if not stat.S_ISREG(metadata.st_mode) or target.is_symlink():
            raise Refusal("Waybar destination asset is unsafe")
        temporary = target.with_name(f".{target.name}.desktop-essential-{os.getpid()}.tmp")
        descriptor = os.open(
            temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC, 0o600,
        )
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(content[source_name])
                stream.flush()
                os.fsync(stream.fileno())
            os.chown(temporary, uid, gid)
            os.replace(temporary, target)
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise


def copy_environment_shell_seed(
    seed: Path, user_home: Path, uid: int = 1000, gid: int = 1000,
) -> None:
    """Overlay the reviewed QuickShell desktop shared by Hub and environments."""
    if not seed.is_dir() or seed.is_symlink():
        raise Refusal("environment shell seed is absent or unsafe")

    expected_directories: set[str] = set()
    for relative in ENVIRONMENT_SHELL_ASSETS:
        parent = Path(relative).parent
        while parent != Path("."):
            expected_directories.add(parent.as_posix())
            parent = parent.parent
    expected_entries = set(ENVIRONMENT_SHELL_ASSETS) | expected_directories
    observed_entries: set[str] = set()
    for entry in seed.rglob("*"):
        relative = entry.relative_to(seed).as_posix()
        observed_entries.add(relative)
        metadata = entry.lstat()
        if relative in ENVIRONMENT_SHELL_ASSETS:
            if not stat.S_ISREG(metadata.st_mode):
                raise Refusal("environment shell asset is not a regular file")
        elif relative in expected_directories:
            if not stat.S_ISDIR(metadata.st_mode) or entry.is_symlink():
                raise Refusal("environment shell directory is unsafe")
        else:
            raise Refusal("environment shell seed contains an unapproved entry")
    if observed_entries != expected_entries:
        raise Refusal("environment shell seed is incomplete")

    content: dict[str, bytes] = {}
    for relative, expected_digest in ENVIRONMENT_SHELL_ASSETS.items():
        source = seed / relative
        descriptor = os.open(source, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
        try:
            value = os.read(descriptor, MAX_GRAPHICAL_CONFIG_BYTES + 1)
            if os.read(descriptor, 1) or len(value) > MAX_GRAPHICAL_CONFIG_BYTES:
                raise Refusal("environment shell asset exceeds the size limit")
        finally:
            os.close(descriptor)
        if hashlib.sha256(value).hexdigest() != expected_digest:
            raise Refusal("environment shell asset digest differs")
        content[relative] = value

    if not user_home.is_dir() or user_home.is_symlink():
        raise Refusal("environment home is absent or unsafe")
    targets: dict[str, Path] = {}
    for relative in ENVIRONMENT_SHELL_ASSETS:
        parts = Path(relative).parts
        if parts[0] == "local":
            targets[relative] = user_home / ".local" / Path(*parts[1:])
        else:
            targets[relative] = user_home / ".config" / relative

    # mkdir(parents=True) creates missing ancestors with the runner's root
    # ownership.  Include every directory below user_home explicitly so a
    # fresh Home does not leave ~/.local root-owned and prevent the desktop
    # user from creating ~/.local/state when QuickShell starts.
    directories: set[Path] = set()
    for target in targets.values():
        directory = target.parent
        while directory != user_home:
            directories.add(directory)
            directory = directory.parent
    for directory in sorted(directories, key=lambda item: len(item.parts)):
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        metadata = directory.lstat()
        if not stat.S_ISDIR(metadata.st_mode) or directory.is_symlink():
            raise Refusal("environment shell destination directory is unsafe")
        os.chmod(directory, 0o700)
        os.chown(directory, uid, gid)

    for relative, value in content.items():
        target = targets[relative]
        if target.exists() or target.is_symlink():
            metadata = target.lstat()
            if not stat.S_ISREG(metadata.st_mode) or target.is_symlink():
                raise Refusal("environment shell destination asset is unsafe")
        temporary = target.with_name(f".{target.name}.environment-shell-{os.getpid()}.tmp")
        mode = 0o755 if relative.startswith("local/bin/") else 0o600
        descriptor = os.open(
            temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC, mode,
        )
        try:
            os.fchmod(descriptor, mode)
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(value)
                stream.flush()
                os.fsync(stream.fileno())
            os.chown(temporary, uid, gid)
            os.replace(temporary, target)
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise


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


def make_plan(action: str, name: str, role: str | None = None,
              update_policy: str = "follow-host", description: str = "",
              preset: str = "intermediate", modules: tuple[str, ...] | list[str] = ()) -> dict[str, object]:
    validate_name(name)
    generation = str(uuid.uuid4())
    if action == "create":
        validate_role_assignment(name, role or "")
        if update_policy not in {"follow-host", "excluded"}:
            raise Refusal("unsupported update policy")
        if len(description) > 120 or description != description.strip() \
                or any(ord(character) < 32 for character in description):
            raise Refusal("invalid Environment description")
        if environment_dir(name).exists():
            raise Refusal("Environment already exists")
        admitted_release(role or "")
        if role == "graphical-base":
            if not modules:
                from apx_environment_features import PRESETS
                modules = PRESETS["intermediate"]
            try:
                preset, modules = validate_selection(preset, modules)
            except ValueError as error:
                raise Refusal(str(error)) from error
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
        plan["update_policy"] = update_policy
        plan["description"] = description
        if role == "graphical-base":
            plan["desktop_preset"] = preset
            plan["desktop_modules"] = list(modules)
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
    verify_shared_storage_reserve()
    operation = str(uuid.uuid4())
    append_event(operation, "create", "operation", "started", name=name, plan=plan_identity)
    target.mkdir(mode=0o700)
    try:
        root = target / "root"
        append_event(operation, "create", "root", "started", name=name)
        run(["btrfs", "subvolume", "snapshot", str(admitted_release(role)), str(root)])
        apply_subvolume_storage_limit(root, ENVIRONMENT_STORAGE_LIMITS[role][0])
        append_event(operation, "create", "root", "complete", name=name)
        fault("root")

        home = target / "home"
        append_event(operation, "create", "home", "started", name=name)
        run(["btrfs", "subvolume", "create", str(home)])
        home.chmod(0o755)
        apply_subvolume_storage_limit(home, ENVIRONMENT_STORAGE_LIMITS[role][1])
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
            seed = root / "usr/share/apx/config-seeds/hyprland-minimal-v2"
            destination = home / "apx/.config"
            copy_graphical_config_seed(seed, destination)
            copy_desktop_config_seed(DESKTOP_CONFIG_SEED, destination, role)
            copy_environment_shell_seed(ENVIRONMENT_SHELL_SEED, user_home)
        if role == "graphical-base":
            configure_environment_features(root, plan)
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
            "update_policy": plan.get("update_policy", "follow-host"),
        }
        if role == "graphical-base":
            record["desktop_preset"] = plan["desktop_preset"]
            record["desktop_modules"] = plan["desktop_modules"]
        if plan.get("description"):
            record["description"] = plan["description"]
        append_event(operation, "create", "publish", "started", name=name)
        atomic_json(registration_path(name), record)
        append_event(operation, "create", "publish", "complete", name=name)
        append_event(operation, "create", "operation", "complete", name=name)
    except BaseException:
        append_event(operation, "create", "operation", "uncertain", name=name)
        raise


def configure_environment_features(root: Path, plan: dict[str, object]) -> None:
    """Apply the closed package selection and inherit only Hub's password hash."""
    preset, modules = validate_selection(plan.get("desktop_preset"), plan.get("desktop_modules"))
    feature_dir = root / "etc/apx"
    feature_dir.mkdir(parents=True, exist_ok=True, mode=0o755)
    atomic_json(feature_dir / "environment-features.json", {
        "schema": 1, "preset": preset, "modules": list(modules),
    }, 0o644)

    hub_shadow = ENVIRONMENTS / "hub/root/etc/shadow"
    target_shadow = root / "etc/shadow"
    source_lines = read_trusted_shadow(ENVIRONMENTS / "hub/root").splitlines()
    target_lines = read_trusted_shadow(root).splitlines()
    source = next((line.split(":", 2)[1] for line in source_lines if line.startswith("apx:")), None)
    if not source or source.startswith(("!", "*")):
        raise Refusal("Hub apx password is not enrolled")
    replaced = False
    for index, line in enumerate(target_lines):
        if line.startswith("apx:"):
            fields = line.split(":"); fields[1] = source
            target_lines[index] = ":".join(fields); replaced = True; break
    if not replaced:
        raise Refusal("Environment apx account is absent")
    write_trusted_shadow(root, "\n".join(target_lines) + "\n")

    packages = packages_for(modules)
    if packages:
        if any(package.startswith("lib32-") for package in packages):
            pacman_config = root / "etc/pacman.conf"
            metadata = pacman_config.lstat()
            content = pacman_config.read_text()
            disabled = "#[multilib]\n#Include = /etc/pacman.d/mirrorlist\n"
            enabled = "[multilib]\nInclude = /etc/pacman.d/mirrorlist\n"
            if pacman_config.is_symlink() or not pacman_config.is_file() \
                    or metadata.st_uid != 0 or metadata.st_gid != 0 or metadata.st_mode & 0o022 \
                    or (disabled not in content and enabled not in content):
                raise Refusal("Environment multilib configuration differs")
            if disabled in content:
                content = content.replace(disabled, enabled, 1)
                descriptor = os.open(pacman_config, os.O_WRONLY | os.O_TRUNC | os.O_NOFOLLOW)
                try:
                    os.write(descriptor, content.encode())
                    os.fsync(descriptor)
                finally:
                    os.close(descriptor)
        run(["pacman", "--root", str(root), "--dbpath", str(root / "var/lib/pacman"),
             "--cachedir", "/var/cache/pacman/pkg", "--config", str(root / "etc/pacman.conf"),
             "--disable-sandbox", "-Syu", "--needed", "--noconfirm", *packages])
    for package in local_packages_for(modules):
        artifact = validated_local_package_artifact(package)
        run(["pacman", "--root", str(root), "--dbpath", str(root / "var/lib/pacman"),
             "--cachedir", "/var/cache/pacman/pkg", "--config", str(root / "etc/pacman.conf"),
             "--disable-sandbox", "-U", "--needed", "--noconfirm", str(artifact)])


def validated_local_package_artifact(package: str) -> Path:
    """Resolve one Host-owned, digest-pinned non-repository package."""
    manifest_name = LOCAL_PACKAGE_MANIFESTS.get(package)
    if manifest_name is None:
        raise Refusal("Environment local package is unsupported")
    directory = LOCAL_PACKAGE_ARTIFACTS
    manifest = directory / manifest_name
    for path, expected_directory in ((directory, True), (manifest, False)):
        try:
            metadata = path.lstat()
        except OSError as error:
            raise Refusal("Environment local package metadata is absent") from error
        if path.is_symlink() or (expected_directory and not stat.S_ISDIR(metadata.st_mode)) \
                or (not expected_directory and not stat.S_ISREG(metadata.st_mode)) \
                or (metadata.st_uid, metadata.st_gid) != (0, 0) or metadata.st_mode & 0o022:
            raise Refusal("Environment local package metadata is not Host-owned")
    try:
        record = json.loads(manifest.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise Refusal("Environment local package manifest is invalid") from error
    if type(record) is not dict or record.get("schema") != 1 \
            or record.get("package") != package:
        raise Refusal("Environment local package manifest is unsupported")
    filename = record.get("filename")
    digest = record.get("sha256")
    if type(filename) is not str or Path(filename).name != filename \
            or not filename.startswith(package + "-") or not filename.endswith(".pkg.tar.zst") \
            or type(digest) is not str or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
        raise Refusal("Environment local package manifest fields are invalid")
    artifact = directory / filename
    try:
        metadata = artifact.lstat()
    except OSError as error:
        raise Refusal("Environment local package artifact is absent") from error
    if artifact.is_symlink() or not stat.S_ISREG(metadata.st_mode) \
            or (metadata.st_uid, metadata.st_gid) != (0, 0) or metadata.st_mode & 0o022 \
            or metadata.st_size <= 0 or metadata.st_size > 512 * 1024**2:
        raise Refusal("Environment local package artifact is not admitted")
    computed = hashlib.sha256()
    with artifact.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            computed.update(chunk)
    if computed.hexdigest() != digest:
        raise Refusal("Environment local package digest does not match")
    return artifact


def trusted_root_owner(root: Path) -> tuple[int, int]:
    """Resolve root ownership across stopped and private-user active roots."""
    container = root.parent
    container_metadata = container.lstat()
    root_metadata = root.lstat()
    etc_metadata = (root / "etc").lstat()
    if any(path.is_symlink() for path in (container, root, root / "etc")) \
            or not all(stat.S_ISDIR(value.st_mode) for value in (
                container_metadata, root_metadata, etc_metadata,
            )) \
            or (container_metadata.st_uid, container_metadata.st_gid) != (0, 0) \
            or container_metadata.st_mode & 0o022 \
            or (etc_metadata.st_uid, etc_metadata.st_gid) != (
                root_metadata.st_uid, root_metadata.st_gid,
            ) \
            or etc_metadata.st_mode & 0o022:
        raise Refusal("trusted password source is unavailable")
    return root_metadata.st_uid, root_metadata.st_gid


def open_trusted_shadow(root: Path, flags: int) -> int:
    owner = trusted_root_owner(root)
    path = root / "etc/shadow"
    try:
        descriptor = os.open(path, flags | os.O_NOFOLLOW | os.O_CLOEXEC)
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode) \
                or (metadata.st_uid, metadata.st_gid) != owner \
                or stat.S_IMODE(metadata.st_mode) != 0o600 \
                or metadata.st_size > 65536:
            raise Refusal("trusted password source is unavailable")
        return descriptor
    except BaseException:
        if "descriptor" in locals():
            os.close(descriptor)
        raise


def read_trusted_shadow(root: Path) -> str:
    descriptor = open_trusted_shadow(root, os.O_RDONLY)
    try:
        value = bytearray()
        while len(value) <= 65536:
            chunk = os.read(descriptor, min(8192, 65537 - len(value)))
            if not chunk:
                break
            value.extend(chunk)
        if len(value) > 65536:
            raise Refusal("trusted password source is unavailable")
        return value.decode()
    except (UnicodeDecodeError, OSError) as error:
        raise Refusal("trusted password source is unavailable") from error
    finally:
        os.close(descriptor)


def write_trusted_shadow(root: Path, value: str) -> None:
    encoded = value.encode()
    if len(encoded) > 65536:
        raise Refusal("trusted password target is unavailable")
    descriptor = open_trusted_shadow(root, os.O_WRONLY)
    try:
        os.ftruncate(descriptor, 0)
        view = memoryview(encoded)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise OSError("short shadow write")
            view = view[written:]
        os.fsync(descriptor)
    except OSError as error:
        raise Refusal("trusted password target is unavailable") from error
    finally:
        os.close(descriptor)


def fault(effect: str) -> None:
    if os.environ.get("APX_LAB_FAULT_AFTER") == effect:
        os._exit(86)


def verify_shared_storage_reserve() -> None:
    """Refuse new growth when the Host recovery reserve would be crossed."""
    stats = os.statvfs(STATE)
    available = stats.f_bavail * stats.f_frsize
    if available < HOST_STORAGE_RESERVE_BYTES:
        raise Refusal("shared Environment pool reached the protected Host reserve")


def apply_subvolume_storage_limit(path: Path, limit: str) -> None:
    """Bound both total referenced and exclusive growth for one Environment volume."""
    if not re.fullmatch(r"[1-9][0-9]*G", limit):
        raise Refusal("Environment storage limit is malformed")
    run(["btrfs", "qgroup", "limit", limit, str(path)])
    run(["btrfs", "qgroup", "limit", "-e", limit, str(path)])


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
    cpu_quota, memory_high, memory_max, tasks_max = ENVIRONMENT_RUNTIME_LIMITS[str(record["role"])]
    command = [
        "systemd-run", "--unit", unit, "--collect", "--property=Delegate=yes",
        "--property=KillMode=mixed", "--",
        "systemd-nspawn", "--quiet", "--keep-unit", "--boot",
        f"--machine={machine(name)}", f"--directory={target / 'root'}",
        "--private-users=pick", "--private-users-ownership=chown",
        "--private-network", "--network-veth", "--link-journal=no", "--settings=no",
        f"--bind={target / 'home'}:/home:idmap",
    ]
    command[6:6] = [
        f"--property=CPUQuota={cpu_quota}", "--property=CPUWeight=200",
        "--property=IOWeight=200", f"--property=MemoryHigh={memory_high}",
        f"--property=MemoryMax={memory_max}", f"--property=TasksMax={tasks_max}",
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
        "/etc/sudoers.d/10-apx-local-admin "
        " && /usr/bin/grep -Fxq 'apx ALL=(ALL:ALL) ALL' "
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
        raise Refusal("Environment local administrator state is absent or ambiguous")
    fields = tuple(lines[0][len(prefix):].split(":"))
    if len(fields) != 5:
        raise Refusal("Environment local administrator state is malformed")
    marker, sudo, password, wheel, policy = fields
    if marker not in {"absent", "present"} \
            or sudo not in {"absent", "present"} \
            or password not in {"L", "P", "NP"} \
            or wheel not in {"absent", "present"} \
            or policy not in {"absent", "invalid", "ready"}:
        raise Refusal("Environment local administrator state contains an unknown value")
    return marker, sudo, password, wheel, policy


def enroll_local_admin(name: str) -> None:
    """Enroll one Environment-local password without copying a Host secret."""
    require_root()
    record = registration(name)
    if not machine_running(name):
        if record.get("role") in HEADLESS_START_ROLES:
            start(name)
        else:
            raise Refusal("start the graphical Environment before enrolling its local administrator")
    target = machine(name)
    marker, sudo, password, wheel, policy = local_admin_state(target)
    if sudo != "present":
        raise Refusal("Environment release does not contain sudo")
    if (marker, password, wheel, policy) == ("present", "P", "present", "ready"):
        raise Refusal("Environment local administrator is already enrolled")
    if marker == "present":
        raise Refusal("Environment local administrator marker exists but enrollment is incomplete")
    fixed_prepare = (
        "set -eu; "
        "/usr/bin/usermod -aG wheel apx; "
        "/usr/bin/install -d -m 0755 /etc/apx /etc/sudoers.d; "
        "/usr/bin/printf '%s\\n' '%wheel ALL=(ALL:ALL) ALL' "
        "'apx ALL=(ALL:ALL) ALL' "
        "| /usr/bin/install -m 0440 /dev/stdin /etc/sudoers.d/10-apx-local-admin"
    )
    run(["machinectl", "shell", f"root@{target}", "/usr/bin/bash", "-lc", fixed_prepare])
    print(f"Define agora uma palavra-passe exclusiva do Environment {name} para o utilizador apx.")
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
        raise Refusal("Environment local administrator final state differs")
    print(f"Environment {name} local administrator enrolled; the Host password was not requested or copied.")


def destroy(plan_identity: str, approval: str) -> None:
    require_root()
    plan = load_plan(plan_identity, "destroy")
    name = str(plan["name"])
    if approval != f"DESTROY {name}":
        raise Refusal("exact destruction approval is absent")
    record = registration(name)
    if plan.get("generation") != record.get("generation"):
        raise Refusal("destruction plan generation is stale")
    if plan.get("effects") != list(EFFECTS["destroy"]):
        raise Refusal("destruction plan effects differ from complete purge policy")
    target = environment_dir(name)
    metadata = target.lstat()
    if not stat.S_ISDIR(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode) \
            or metadata.st_uid != 0 or metadata.st_gid != 0 \
            or stat.S_IMODE(metadata.st_mode) != 0o700:
        raise Refusal("Environment container is not a trusted root-owned directory")
    operation = str(uuid.uuid4())
    append_event(operation, "destroy", "operation", "started", name=name, plan=plan_identity)
    stop(name)
    for effect, count in purge_environment_copies(name):
        append_event(operation, "destroy", effect, "complete", name=name, removed=count)
    removed_backups = purge_environment_backups(name)
    append_event(
        operation, "destroy", "purge-backups", "complete", name=name,
        removed=removed_backups,
    )
    for label in ("home", "root"):
        path = target / label
        append_event(operation, "destroy", f"remove-{label}", "started", name=name)
        delete_subvolume_tree(path)
        append_event(operation, "destroy", f"remove-{label}", "complete", name=name)
    record_path = registration_path(name)
    append_event(operation, "destroy", "unpublish", "started", name=name)
    record_path.unlink()
    append_event(operation, "destroy", "unpublish", "complete", name=name)
    append_event(operation, "destroy", "purge-metadata", "started", name=name)
    shutil.rmtree(target)
    append_event(operation, "destroy", "purge-metadata", "complete", name=name)
    removed_plans = purge_environment_plans(name)
    append_event(
        operation, "destroy", "purge-plans", "complete", name=name,
        removed=removed_plans,
    )
    append_event(operation, "destroy", "operation", "complete", name=name)


def delete_subvolume_tree(path: Path) -> None:
    if not path.exists():
        return
    run(["btrfs", "subvolume", "delete", "-R", str(path)])


UUID_COMPONENT = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"


def _remove_exact_copy(path: Path, *, snapshot: bool) -> None:
    metadata = path.lstat()
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        path.unlink()
        return
    if snapshot:
        for label in ("home", "root"):
            delete_subvolume_tree(path / label)
    shutil.rmtree(path)


def purge_environment_copies(name: str) -> tuple[tuple[str, int], ...]:
    """Delete every APX snapshot/archive generation for one logical name."""
    validate_name(name)
    snapshot_name = re.compile(
        rf"{re.escape(name)}-{UUID_COMPONENT}-[0-9]{{8}}T[0-9]{{6}}Z"
    )
    archive_name = re.compile(
        rf"archive-{re.escape(name)}-{UUID_COMPONENT}-{UUID_COMPONENT}"
    )
    counts: list[tuple[str, int]] = []
    for parent, pattern, effect, is_snapshot in (
        (SNAPSHOTS, snapshot_name, "purge-snapshots", True),
        (ARCHIVES, archive_name, "purge-archives", False),
    ):
        removed = 0
        if parent.exists():
            for path in sorted(parent.iterdir()):
                if pattern.fullmatch(path.name):
                    _remove_exact_copy(path, snapshot=is_snapshot)
                    removed += 1
        counts.append((effect, removed))
    return tuple(counts)


def purge_environment_plans(name: str) -> int:
    """Remove stored operation plans that identify the deleted Environment."""
    validate_name(name)
    removed = 0
    if not PLANS.exists():
        return removed
    for path in sorted(PLANS.glob("*.json")):
        if re.fullmatch(r"[0-9a-f]{64}\.json", path.name) is None:
            continue
        try:
            value = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(value, dict) and value.get("name") == name:
            path.unlink()
            removed += 1
    return removed


def purge_environment_backups(name: str) -> int:
    """Remove legacy Host maintenance copies explicitly named for the target."""
    validate_name(name)
    if not BACKUPS.exists():
        return 0
    exact_names = {name, f"{name}-shell.qml"}
    candidates = sorted(
        (path for path in BACKUPS.rglob("*") if path.name in exact_names),
        key=lambda path: len(path.parts), reverse=True,
    )
    removed = 0
    for path in candidates:
        try:
            metadata = path.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISDIR(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode):
            shutil.rmtree(path)
        else:
            path.unlink()
        removed += 1
    return removed


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
    if registration_path(name).exists() or machine_running(name):
        raise Refusal("recovery target is published or running")
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
    if not target.exists():
        append_event(
            operation, action or "recovery", "operation", "complete", name=name,
            recovery="confirmed-already-absent",
        )
        return
    if not target.is_dir():
        raise Refusal("recovery target has an unexpected filesystem type")
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
    create_plan.add_argument("--exclude-host-updates", action="store_true",
                             help="opt out of coordinated Host update plans")
    create_plan.add_argument("--description", default="")
    create_plan.add_argument("--desktop-preset", default="intermediate",
                             choices=("basic", "intermediate", "complete"))
    create_plan.add_argument("--desktop-modules", default="")
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
        policy = "excluded" if arguments.exclude_host_updates else "follow-host"
        print(json.dumps(make_plan("create", arguments.name, arguments.role, policy,
                                   arguments.description, arguments.desktop_preset,
                                   tuple(filter(None, arguments.desktop_modules.split(",")))),
                         sort_keys=True, indent=2))
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
