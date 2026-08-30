#!/usr/bin/env python3
"""Authenticated Host endpoint for one bounded Hub/workload handoff trial."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import secrets
import select
import socket
import stat
import struct
import subprocess
import sys
import threading
import uuid

sys.path.insert(0, "/usr/lib/apx")
from apx_environment_switch_contract import (  # noqa: E402
    MAX_MESSAGE_BYTES, PROFILE, parse_message, valid_description, valid_display_name,
)
from apx_host_services_peer import (  # noqa: E402
    HostServicesPeer, HostServicesPeerError, authorize_active_environment_peer,
    authorize_official_hub_peer, authorize_shared_service_peer,
)


SOCKET = Path("/run/apx/environment-switch-v1.sock")
LIVE_SOCKET = Path("/var/lib/apx/environments/hub/home/.apx-host-bridge/environment-switch-v1.sock")
ENVIRONMENTS = Path("/var/lib/apx/environments")
NATIVE_ENVIRONMENTS = Path("/var/lib/apx/native-environments")
WINDOWS_PENDING = NATIVE_ENVIRONMENTS / "windows-pending.json"
RUNNER = "/usr/lib/apx/apx-environment-switch-runner-v1.py"
MANAGEMENT_RUNNER = "/usr/lib/apx/apx-environment-management-runner-v1.py"
NATIVE_BOOT_RUNNER = "/usr/lib/apx/apx-native-boot-runner-v1.py"
NATIVE_LIFECYCLE_RUNNER = "/usr/lib/apx/apx-native-windows-lifecycle-v1.py"
NATIVE_RECOVERY_RUNNER = "/usr/lib/apx/apx-native-windows-recovery-v1.py"
METADATA_RUNNER = "/usr/lib/apx/apx-environment-metadata-runner-v1.py"
STORAGE_RUNNER = "/usr/lib/apx/apx-environment-storage-runner-v1.py"
LOCK = Path("/run/apx/environment-handoff-v1.lock")
MANAGEMENT_LOCK = Path("/run/apx/environment-management-v1.lock")
NEXT_ENVIRONMENT = Path("/run/apx/environment-switch-next-v1.json")
MANAGEMENT_STATE = Path("/run/apx/environment-management-v1.json")
OFFICIAL_UNIT = "apx-official-hub-graphical-6f63f9a9.service"
SERVER_LOCK = threading.Lock()
SYSTEM_METADATA = "system-environment-v1.json"
WINDOWS_STORAGE = NATIVE_ENVIRONMENTS / "windows-storage-v1.json"
NAME = re.compile(r"[a-z](?:[a-z0-9]|-(?=[a-z0-9])){0,26}")
GENERATION = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}")


def trusted_environment(name: str) -> dict[str, object]:
    if not re.fullmatch(r"[a-z](?:[a-z0-9]|-(?=[a-z0-9])){0,26}", name) or name == "hub":
        raise PermissionError("a identidade do Environment é inválida")
    registration = ENVIRONMENTS / name / "registration.json"
    metadata = registration.lstat(); data = registration.read_bytes()
    if registration.is_symlink() or not registration.is_file() \
            or metadata.st_uid != 0 or metadata.st_gid != 0 or len(data) > 8192:
        raise PermissionError("o registo do Environment não é confiável")
    value = json.loads(data)
    if type(value) is not dict or (value.get("name"), value.get("role"), value.get("release")) != (
        name, "graphical-base", "hyprland-base-v2",
    ) or value.get("state") not in {"stopped", "running"}:
        raise PermissionError("a identidade do Environment difere")
    return value


def trusted_hub() -> dict[str, object]:
    registration = ENVIRONMENTS / "hub" / "registration.json"
    metadata = registration.lstat(); data = registration.read_bytes()
    if registration.is_symlink() or not registration.is_file() or metadata.st_uid != 0 \
            or metadata.st_gid != 0 or not data or len(data) > 8192:
        raise PermissionError("o registo do HUB não é confiável")
    value = json.loads(data)
    if type(value) is not dict or (value.get("name"), value.get("role")) != ("hub", "hub") \
            or value.get("state") not in {"stopped", "running"}:
        raise PermissionError("a identidade do HUB difere")
    return value


def environment_view(record: dict[str, object]) -> dict[str, object]:
    name = str(record["name"])
    display_name = record.get("display_name", name.replace("-", " ").title())
    description = record.get("description", "")
    category = record.get("category", "general")
    if not valid_display_name(display_name) or not valid_description(description) \
            or type(category) is not str or not re.fullmatch(r"[a-z][a-z0-9-]{0,31}", category):
        raise PermissionError("a apresentação do Environment difere")
    system_kind, system_label = "arch", "ARCH"
    marker = ENVIRONMENTS / name / SYSTEM_METADATA
    try:
        metadata = marker.lstat(); raw = marker.read_bytes(); value = json.loads(raw)
        if marker.is_symlink() or not marker.is_file() or metadata.st_uid != 0 or metadata.st_gid != 0 \
                or stat.S_IMODE(metadata.st_mode) != 0o400 or len(raw) > 2048 \
                or type(value) is not dict or value.get("schema") != 1 \
                or value.get("profile") != "apx-system-environment-v1" \
                or value.get("system_kind") not in {"windows11", "ubuntu"}:
            raise PermissionError("os metadados do sistema não são confiáveis")
        system_kind = str(value["system_kind"])
        system_label = "WINDOWS" if system_kind == "windows11" else "UBUNTU"
    except FileNotFoundError:
        pass
    return {"category": category, "description": description, "display_name": display_name, "generation": record["generation"],
            "name": name, "release": record["release"], "role": record["role"], "state": record["state"],
            "system_kind": system_kind, "system_label": system_label,
            "session_restore": record.get("session_restore") is True,
            "update_policy": record.get("update_policy", "follow-host")}


def trusted_native_environment(name: str) -> dict[str, object]:
    if name != "windows":
        raise PermissionError("a identidade do sistema nativo é inválida")
    marker = NATIVE_ENVIRONMENTS / f"{name}.json"
    metadata = marker.lstat(); raw = marker.read_bytes()
    value = json.loads(raw)
    expected = {
        "boot_entry": "firmware-windows", "category": "system",
        "disk_id": "AC9FC0BD-2162-43A9-AAE6-3F654FF6F275",
        "disk_serial": "S4DYNX0R253702",
        "environment_kind": "native-boot",
        "name": "windows", "profile": "apx-native-environment-v2",
        "release": "windows-11-native-v1", "schema": 2, "state": "ready",
        "system_kind": "windows-native", "system_label": "NATIVO",
        "windows_esp_partuuid": "9625F250-9ACC-453A-AE63-0C863ADE440F",
    }
    if marker.is_symlink() or not marker.is_file() or metadata.st_uid != 0 or metadata.st_gid != 0 \
            or stat.S_IMODE(metadata.st_mode) != 0o400 or not raw or len(raw) > 2048 \
            or type(value) is not dict or any(value.get(key) != expected_value for key, expected_value in expected.items()) \
            or set(value) != set(expected) | {"description", "display_name", "generation", "linux_boot_entry",
                                               "requested_size_gib", "reserved_bytes",
                                               "windows_boot_entry", "windows_bytes", "windows_partuuid"} \
            or not valid_display_name(value.get("display_name")) \
            or not valid_description(value.get("description")):
        raise PermissionError("os metadados do sistema nativo não são confiáveis")
    size = value.get("requested_size_gib")
    if re.fullmatch(r"[0-9a-f]{8}-[0-9a-f-]{27}", str(value.get("generation", ""))) is None \
            or size not in {80, 120, 160} \
            or value.get("reserved_bytes") != (1000215183 - ((1000215183 - size * 2097152) // 2048 * 2048)) * 512 \
            or not re.fullmatch(r"[0-9A-F]{4}", str(value.get("linux_boot_entry", ""))) \
            or not re.fullmatch(r"[0-9A-F]{4}", str(value.get("windows_boot_entry", ""))) \
            or not re.fullmatch(r"[0-9A-F]{8}(?:-[0-9A-F]{4}){3}-[0-9A-F]{12}", str(value.get("windows_partuuid", ""))) \
            or type(value.get("windows_bytes")) is not int or not 64 * 1024**3 <= value["windows_bytes"] <= 160 * 1024**3:
        raise PermissionError("a geração do sistema nativo difere")
    return value


def windows_storage_reserved() -> bool:
    try:
        metadata = WINDOWS_STORAGE.lstat(); raw = WINDOWS_STORAGE.read_bytes(); value = json.loads(raw)
        return WINDOWS_STORAGE.is_file() and not WINDOWS_STORAGE.is_symlink() \
            and metadata.st_uid == 0 and metadata.st_gid == 0 \
            and stat.S_IMODE(metadata.st_mode) == 0o400 and len(raw) <= 2048 \
            and type(value) is dict and value.get("profile") == "apx-native-windows-storage-v1" \
            and value.get("disk_id") == "AC9FC0BD-2162-43A9-AAE6-3F654FF6F275" \
            and value.get("disk_serial") == "S4DYNX0R253702" \
            and value.get("free_start_sector") == 748556288 \
            and value.get("free_end_sector") == 1000215182 \
            and value.get("reserved_bytes") == 128849354240
    except (OSError, json.JSONDecodeError):
        return False


def trusted_windows_pending() -> dict[str, object]:
    metadata = WINDOWS_PENDING.lstat(); raw = WINDOWS_PENDING.read_bytes(); value = json.loads(raw)
    allowed = {"action", "boot_attempts", "created_at", "explicit_attempts", "failed_at", "failure_code", "failure_reason",
               "failure_step", "generation", "name", "profile", "requested_size_gib",
               "resume_attempts", "schema", "stage"}
    if WINDOWS_PENDING.is_symlink() or not WINDOWS_PENDING.is_file() \
            or metadata.st_uid != 0 or metadata.st_gid != 0 \
            or stat.S_IMODE(metadata.st_mode) != 0o400 or not raw or len(raw) > 4096 \
            or type(value) is not dict or not set(value).issubset(allowed) \
            or value.get("schema") != 1 or value.get("profile") != "apx-native-windows-pending-v1" \
            or value.get("action") not in {"create", "delete"} or value.get("name") != "windows" \
            or value.get("stage") not in {"maintenance", "preparing-installer", "prepared",
                                                "installing", "boot-prepared", "failed",
                                                "recovery-required", "finalizing"} \
            or value.get("requested_size_gib") not in {80, 120, 160} \
            or GENERATION.fullmatch(str(value.get("generation", ""))) is None \
            or type(value.get("created_at")) is not int or value["created_at"] <= 0:
        raise PermissionError("a operação Windows pendente não é confiável")
    attempts = value.get("resume_attempts")
    if attempts is not None and (type(attempts) is not int or not 0 <= attempts <= 12):
        raise PermissionError("as retomas Windows pendentes diferem")
    explicit_attempts = value.get("explicit_attempts", 0)
    if type(explicit_attempts) is not int or not 0 <= explicit_attempts <= 2:
        raise PermissionError("as tentativas Windows explícitas diferem")
    boot_attempts = value.get("boot_attempts", 0)
    if type(boot_attempts) is not int or not 0 <= boot_attempts <= 4:
        raise PermissionError("as continuações do primeiro arranque Windows diferem")
    return value


def native_environment_view(record: dict[str, object]) -> dict[str, object]:
    return {
        "boot_entry": record["boot_entry"], "category": record["category"],
        "description": record["description"],
        "display_name": record["display_name"],
        "environment_kind": record["environment_kind"], "generation": record["generation"],
        "name": record["name"], "release": record["release"],
        "reserved_bytes": record["reserved_bytes"], "role": "native-boot",
        "session_restore": False, "state": record["state"],
        "system_kind": record["system_kind"], "system_label": record["system_label"],
        "update_policy": "native-system",
    }


def catalog() -> list[dict[str, object]]:
    values = []
    for directory in sorted(ENVIRONMENTS.iterdir()):
        if not directory.is_dir() or directory.name == "hub": continue
        try: values.append(environment_view(trusted_environment(directory.name)))
        except (OSError, ValueError, KeyError, json.JSONDecodeError, PermissionError): continue
        if len(values) >= 64: break
    try:
        values.append(native_environment_view(trusted_native_environment("windows")))
    except (OSError, ValueError, KeyError, json.JSONDecodeError, PermissionError):
        pass
    return values


def request_native_boot() -> dict[str, object]:
    runner = Path(NATIVE_BOOT_RUNNER)
    metadata = runner.lstat()
    if runner.is_symlink() or not runner.is_file() or metadata.st_uid != 0 or metadata.st_gid != 0 \
            or stat.S_IMODE(metadata.st_mode) != 0o755:
        raise RuntimeError("o executor de arranque nativo não é confiável")
    unit = "apx-native-boot-" + secrets.token_hex(5)
    result = subprocess.run((
        "/usr/bin/systemd-run", f"--unit={unit}", "--collect", "--property=Type=oneshot",
        NATIVE_BOOT_RUNNER, "--target", "windows",
    ), text=True, capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError("o executor de arranque nativo não arrancou")
    return {"accepted": True, "direction": "hub-to-native", "target": "windows",
            "unit": unit + ".service"}


def request_metadata_update(target: str, generation: str, display_name: str,
                            description: str) -> dict[str, object]:
    runner = Path(METADATA_RUNNER)
    info = runner.lstat()
    if runner.is_symlink() or not runner.is_file() or info.st_uid != 0 or info.st_gid != 0 \
            or stat.S_IMODE(info.st_mode) != 0o755:
        raise RuntimeError("o executor de edição não é confiável")
    unit = "apx-environment-metadata-" + secrets.token_hex(5)
    result = subprocess.run((
        "/usr/bin/systemd-run", "--quiet", "--wait", "--pipe", "--collect",
        f"--unit={unit}", "--property=Type=exec", "--property=NoNewPrivileges=yes",
        "--property=ProtectSystem=strict", "--property=ProtectHome=yes",
        "--property=PrivateTmp=yes", "--property=PrivateDevices=yes",
        "--property=CapabilityBoundingSet=",
        "--property=ReadWritePaths=/var/lib/apx/environments",
        "--property=ReadWritePaths=/var/lib/apx/native-environments",
        METADATA_RUNNER, "--target", target, "--generation", generation,
        "--display-name", display_name, "--description", description,
    ), text=True, capture_output=True, check=False)
    if result.returncode:
        detail = (result.stderr.strip() or result.stdout.strip() or
                  "o Host recusou a edição")[-300:]
        raise RuntimeError(detail)
    return {"accepted": True, "action": "update-metadata", "target": target,
            "generation": generation, "display_name": display_name,
            "description": description}


def request_storage_status() -> dict[str, object]:
    runner = Path(STORAGE_RUNNER)
    info = runner.lstat()
    if runner.is_symlink() or not runner.is_file() or info.st_uid != 0 or info.st_gid != 0 \
            or stat.S_IMODE(info.st_mode) != 0o755:
        raise RuntimeError("o medidor de armazenamento não é confiável")
    unit = "apx-environment-storage-" + secrets.token_hex(5)
    result = subprocess.run((
        "/usr/bin/systemd-run", "--quiet", "--wait", "--pipe", "--collect",
        f"--unit={unit}", "--property=Type=exec", "--property=NoNewPrivileges=yes",
        "--property=ProtectSystem=strict", "--property=ProtectHome=yes",
        "--property=PrivateTmp=yes", "--property=PrivateDevices=yes",
        "--property=CapabilityBoundingSet=CAP_SYS_ADMIN",
        "--property=ProtectKernelTunables=yes", "--property=ProtectKernelModules=yes",
        STORAGE_RUNNER,
    ), text=True, capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError((result.stderr.strip() or result.stdout.strip() or
                            "o Host recusou a medição")[-300:])
    value = json.loads(result.stdout)
    sizes = value.get("sizes") if type(value) is dict else None
    if type(value) is not dict or set(value) != {
        "available_bytes", "profile", "schema", "sizes", "total_bytes",
    } or value.get("schema") != 1 or value.get("profile") != "apx-environment-storage-v1" \
            or type(value.get("total_bytes")) is not int \
            or type(value.get("available_bytes")) is not int \
            or not 128 * 1024**3 <= value["total_bytes"] <= 1024**4 \
            or not 0 <= value["available_bytes"] <= value["total_bytes"] \
            or type(sizes) is not dict or len(sizes) > 64 \
            or any(type(name) is not str or NAME.fullmatch(name) is None
                   or type(size) is not int or not 0 <= size <= 256 * 1024**3
                   for name, size in sizes.items()):
        raise RuntimeError("a resposta de armazenamento difere")
    return value


def management_state() -> dict[str, object]:
    try:
        metadata = MANAGEMENT_STATE.lstat()
        data = MANAGEMENT_STATE.read_bytes()
        if MANAGEMENT_STATE.is_symlink() or not MANAGEMENT_STATE.is_file() \
                or metadata.st_uid != 0 or metadata.st_gid != 0 or len(data) > 8192:
            raise PermissionError("o estado de gestão não é confiável")
        value = json.loads(data)
        if type(value) is not dict or value.get("profile") != "apx-environment-management-v1" \
                or value.get("phase") not in {"planning", "applying", "prepared",
                                                "recovery-required", "complete", "failed"}:
            raise PermissionError("o estado de gestão difere")
        # A failed presentation state does not cancel a durable native-Windows
        # lifecycle. Keep the menu locked while its authenticated pending
        # marker exists, so recovery cannot overlap the same reserved range.
        value["busy"] = MANAGEMENT_LOCK.exists() or WINDOWS_PENDING.exists()
        try:
            pending = trusted_windows_pending()
            recoverable_idle = value.get("phase") in {"failed", "prepared", "recovery-required"} \
                and not MANAGEMENT_LOCK.exists()
            install_attempts = pending.get("explicit_attempts", 0)
            boot_attempts = pending.get("boot_attempts", 0)
            stage = pending.get("stage")
            can_retry = recoverable_idle and pending.get("action") == "create" and (
                (stage == "boot-prepared" and type(boot_attempts) is int and boot_attempts < 4)
                or (stage in {"prepared", "failed", "recovery-required"}
                    and type(install_attempts) is int and install_attempts < 2)
            )
            can_discard = recoverable_idle and (
                (pending.get("action") == "create" and pending.get("stage") in {
                    "prepared", "installing", "boot-prepared", "failed", "recovery-required",
                })
                or (pending.get("action") == "delete" and pending.get("stage") == "maintenance")
            )
            value.update({
                "native_recovery": can_retry or can_discard,
                "native_retry": can_retry,
                "native_discard": can_discard,
                "pending_generation": pending["generation"],
                "pending_stage": stage,
                "pending_size_gib": pending["requested_size_gib"],
                "pending_install_attempts": install_attempts,
                "pending_boot_attempts": boot_attempts,
            })
        except (OSError, ValueError, KeyError, json.JSONDecodeError, PermissionError):
            value["native_recovery"] = False
        return value
    except FileNotFoundError:
        value = {"schema": 1, "profile": "apx-environment-management-v1", "phase": "idle",
                 "progress": 0, "message": "", "target": "", "action": "",
                 "busy": WINDOWS_PENDING.exists(), "native_recovery": False}
        return value


def completed_destroy(target: str, generation: str) -> bool:
    """Recognize a duplicate UI request after the original deletion completed."""
    state = management_state()
    return not (ENVIRONMENTS / target).exists() and state.get("busy") is False \
        and (state.get("phase"), state.get("action"), state.get("target")) == (
            "complete", "destroy", target,
        ) and type(generation) is str


def quickshell_parent(peer_pid: int, unit: str, proc: Path = Path("/proc")) -> int:
    try:
        fields = dict(line.split(":", 1) for line in (proc / str(peer_pid) / "status").read_text().splitlines() if ":" in line)
        parent = int(fields["PPid"].strip())
        comm = (proc / str(parent) / "comm").read_text().strip()
        executable = os.readlink(proc / str(parent) / "exe")
        cgroups = (proc / str(parent) / "cgroup").read_text().splitlines()
    except (OSError, KeyError, ValueError) as error:
        raise PermissionError("a origem QuickShell não pôde ser provada") from error
    unit_path = f"/system.slice/{unit}"
    if parent <= 1 or comm != "quickshell" or executable != "/usr/bin/quickshell" \
            or not any(unit_path in line and line.split(":", 2)[-1].startswith(unit_path) for line in cgroups):
        raise PermissionError("o pedido não é filho direto da QuickShell ativa")
    return parent


def authorize(peer: HostServicesPeer, operation: str, target: str | None = None) -> str:
    if operation == "switch.to-workload":
        try:
            authorize_official_hub_peer(peer)
            quickshell_parent(peer.pid, OFFICIAL_UNIT)
            if target is None or trusted_environment(target).get("state") != "stopped" or LOCK.exists():
                raise RuntimeError("a troca já está ativa ou o destino não está parado")
            return "hub"
        except HostServicesPeerError:
            active = authorize_active_environment_peer(peer)
            if target is None or target == active.name or not LOCK.exists() \
                    or NEXT_ENVIRONMENT.exists() \
                    or trusted_environment(target).get("state") != "stopped":
                raise RuntimeError("a troca direta já está ativa ou o destino não está parado")
            return active.name
    active = authorize_active_environment_peer(peer)
    record = trusted_environment(active.name)
    if active.name == "hub" or active.role != "graphical-base" or active.generation != record.get("generation"):
        raise HostServicesPeerError("apenas o workload ativo pode regressar")
    # authorize_active_environment_peer already proves that this exact client
    # is user apx inside the root-published active Environment unit.  Do not
    # require a QuickShell parent here: both the environment-aware QuickShell
    # action and the Hyprland shortcut launch the fixed client directly.
    return active.name


def authorize_hub_management(peer: HostServicesPeer) -> None:
    authorize_official_hub_peer(peer)
    quickshell_parent(peer.pid, OFFICIAL_UNIT)
    if LOCK.exists() or MANAGEMENT_LOCK.exists():
        raise RuntimeError("já existe uma operação de Environment em curso")


def start_management(action: str, target: str, generation: str | None = None,
                     description: str = "", preset: str = "intermediate",
                     modules: list[str] | None = None, system_kind: str = "arch") -> dict[str, object]:
    unit = "apx-environment-management-" + secrets.token_hex(5)
    descriptor = os.open(MANAGEMENT_LOCK, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        os.write(descriptor, (unit + "\n").encode())
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    command = [
        "/usr/bin/systemd-run", f"--unit={unit}", "--collect", "--property=Type=simple",
        "--property=TimeoutStopSec=15s", MANAGEMENT_RUNNER, "--action", action,
        "--environment", target, "--lock-token", unit,
    ]
    if generation is not None:
        command.extend(("--generation", generation))
    if action == "create":
        command.extend(("--description", description, "--desktop-preset", preset,
                        "--desktop-modules", ",".join(modules or []), "--system", system_kind))
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    if result.returncode:
        MANAGEMENT_LOCK.unlink(missing_ok=True)
        raise RuntimeError("o executor de Environments não arrancou")
    return {"accepted": True, "action": action, "target": target, "unit": unit + ".service"}


def start_native_management(action: str, size_gib: int, generation: str) -> dict[str, object]:
    if action not in {"create", "delete"} or size_gib not in {80, 120, 160} \
            or re.fullmatch(r"[0-9a-f]{8}-[0-9a-f-]{27}", generation) is None:
        raise RuntimeError("a operação Windows nativa difere")
    unit = "apx-native-windows-management-" + secrets.token_hex(5)
    descriptor = os.open(MANAGEMENT_LOCK, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        os.write(descriptor, (unit + "\n").encode()); os.fsync(descriptor)
    finally:
        os.close(descriptor)
    result = subprocess.run((
        "/usr/bin/systemd-run", f"--unit={unit}", "--collect", "--property=Type=simple",
        "--property=TimeoutStopSec=15s", NATIVE_LIFECYCLE_RUNNER,
        "--action", action, "--size-gib", str(size_gib), "--generation", generation,
        "--lock-token", unit,
    ), text=True, capture_output=True, check=False)
    if result.returncode:
        MANAGEMENT_LOCK.unlink(missing_ok=True)
        raise RuntimeError("o executor Windows nativo não arrancou")
    return {"accepted": True, "action": f"native-{action}", "target": "windows",
            "generation": generation, "size_gib": size_gib, "unit": unit + ".service"}


def start_native_recovery(action: str, generation: str) -> dict[str, object]:
    if action not in {"retry", "discard"} or GENERATION.fullmatch(generation) is None:
        raise RuntimeError("a recuperação Windows nativa difere")
    runner = Path(NATIVE_RECOVERY_RUNNER); info = runner.lstat()
    if runner.is_symlink() or not runner.is_file() or info.st_uid != 0 or info.st_gid != 0 \
            or stat.S_IMODE(info.st_mode) != 0o755:
        raise RuntimeError("o executor de recuperação Windows não é confiável")
    pending = trusted_windows_pending()
    install_attempts = pending.get("explicit_attempts", 0)
    boot_attempts = pending.get("boot_attempts", 0)
    stage = pending.get("stage")
    retryable = pending.get("action") == "create" and (
        (stage == "boot-prepared" and type(boot_attempts) is int and boot_attempts < 4)
        or (stage in {"prepared", "failed", "recovery-required"}
            and type(install_attempts) is int and install_attempts < 2)
    )
    discardable = (pending.get("action") == "create" and pending.get("stage") in {
        "prepared", "installing", "boot-prepared", "failed", "recovery-required",
    }) or (pending.get("action") == "delete" and pending.get("stage") == "maintenance")
    if pending.get("generation") != generation or (action == "retry" and not retryable) \
            or (action == "discard" and not discardable):
        raise RuntimeError("a criação Windows pendente mudou")
    unit = "apx-native-windows-recovery-" + secrets.token_hex(5)
    descriptor = os.open(MANAGEMENT_LOCK, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        os.write(descriptor, (unit + "\n").encode()); os.fsync(descriptor)
    finally:
        os.close(descriptor)
    result = subprocess.run((
        "/usr/bin/systemd-run", f"--unit={unit}", "--collect", "--property=Type=simple",
        "--property=TimeoutStopSec=15s", NATIVE_RECOVERY_RUNNER,
        "--action", action, "--generation", generation, "--lock-token", unit,
    ), text=True, capture_output=True, check=False)
    if result.returncode:
        MANAGEMENT_LOCK.unlink(missing_ok=True)
        raise RuntimeError("o executor de recuperação Windows não arrancou")
    return {"accepted": True, "action": f"native-{action}", "target": "windows",
            "generation": generation, "unit": unit + ".service"}


def prime_return_screen() -> None:
    """Prepare tty1 before the workload exits so no Host prompt can flash."""
    payload = ("\033[2J\033[H\033[?25l\n\n\n\n"
               "                  APX ENVIRONMENTS\n\n"
               "                  A REGRESSAR AO HUB\n\n"
               "                  [######------------------------]  20%\n").encode()
    descriptor = os.open("/dev/tty1", os.O_WRONLY | os.O_NOCTTY)
    try:
        os.write(descriptor, payload)
    finally:
        os.close(descriptor)


def request_environment_stop(name: str) -> str:
    """Ask systemd to end the authenticated workload; the runner restores Hub.

    The return action must not depend on the unprivileged client inheriting a
    usable Hyprland control environment.  Peer admission above proves the
    caller belongs to the exact active workload, and its trusted registration
    binds the stop target to the expected generation-scoped outer unit.
    """
    record = trusted_environment(name)
    generation = str(record.get("generation", ""))
    if re.fullmatch(r"[0-9a-f]{8}-[0-9a-f-]{27}", generation) is None:
        raise RuntimeError("a geração do Environment ativo difere")
    unit = f"apx-graphical-{name}-{generation[:8]}.service"
    result = subprocess.run(
        ("/usr/bin/systemctl", "--no-block", "stop", unit),
        text=True, capture_output=True, check=False,
    )
    if result.returncode:
        raise RuntimeError("o Host não conseguiu iniciar o regresso ao HUB")
    return unit


def request_direct_switch(source: str, target: str) -> str:
    record = trusted_environment(target)
    payload = json.dumps({"schema": 1, "profile": "apx-environment-next-v1",
                          "source": source, "target": target,
                          "generation": record["generation"]},
                         sort_keys=True, separators=(",", ":")) + "\n"
    descriptor = os.open(NEXT_ENVIRONMENT, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        os.write(descriptor, payload.encode())
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    try:
        return request_environment_stop(source)
    except Exception:
        NEXT_ENVIRONMENT.unlink(missing_ok=True)
        raise


def active_identity(peer: HostServicesPeer) -> dict[str, object]:
    try:
        authorize_official_hub_peer(peer)
        record = trusted_hub()
        return {"category": "system", "display_name": "HUB", "generation": record["generation"],
                "name": "hub", "release": record["release"], "role": "hub", "state": record["state"],
                "session_restore": False, "update_policy": "host-only"}
    except HostServicesPeerError:
        active = authorize_active_environment_peer(peer)
        return environment_view(trusted_environment(active.name))


def apply(operation: str, payload: dict[str, object], peer: HostServicesPeer) -> dict[str, object] | list[dict[str, object]]:
    if operation == "catalog.get":
        authorize_shared_service_peer(peer); return catalog()
    if operation == "storage.get":
        authorize_shared_service_peer(peer); return request_storage_status()
    if operation == "identity.get": return active_identity(peer)
    if operation == "management.status":
        authorize_official_hub_peer(peer); return management_state()
    if operation == "status.get":
        try:
            authorize_official_hub_peer(peer); active = "hub"
        except HostServicesPeerError:
            active = authorize(peer, "return.to-hub")
        return {"active": active, "handoff_running": LOCK.exists(), "identity": active_identity(peer)}
    if operation == "environment.create":
        authorize_hub_management(peer)
        target = str(payload["target"])
        if payload["system_kind"] == "windows-native":
            return start_native_management("create", int(payload["size_gib"]), str(uuid.uuid4()))
        return start_management("create", target, description=str(payload["description"]),
                                preset=str(payload["preset"]), modules=list(payload["modules"]),
                                system_kind=str(payload["system_kind"]))
    if operation in {"native.retry", "native.discard"}:
        authorize_hub_management(peer)
        if payload.get("target") != "windows":
            raise RuntimeError("a recuperação Windows selecionada difere")
        return start_native_recovery(operation.removeprefix("native."), str(payload["generation"]))
    if operation == "environment.update-metadata":
        authorize_hub_management(peer)
        target, generation = str(payload["target"]), str(payload["generation"])
        display_name, description = str(payload["display_name"]), str(payload["description"])
        if target == "windows":
            record = trusted_native_environment(target)
        else:
            record = trusted_environment(target)
        if record.get("generation") != generation \
                or record.get("state") not in {"stopped", "ready"}:
            raise RuntimeError("o Environment selecionado mudou")
        return request_metadata_update(target, generation, display_name, description)
    if operation == "environment.destroy":
        authorize_hub_management(peer)
        target, generation = str(payload["target"]), str(payload["generation"])
        if target == "windows":
            record = trusted_native_environment("windows")
            if record.get("state") != "ready" or record.get("generation") != generation:
                raise RuntimeError("o Windows selecionado mudou")
            return start_native_management("delete", int(record["requested_size_gib"]), generation)
        if completed_destroy(target, generation):
            return {"accepted": True, "action": "destroy", "target": target,
                    "already_complete": True}
        record = trusted_environment(target)
        if record.get("state") != "stopped" or record.get("generation") != generation:
            raise RuntimeError("o Environment selecionado não está parado ou mudou")
        return start_management("destroy", target, generation)
    if operation == "native.boot":
        authorize_hub_management(peer)
        if payload.get("target") != "windows":
            raise RuntimeError("o sistema nativo selecionado difere")
        trusted_native_environment("windows")
        return request_native_boot()
    target = str(payload["target"]) if operation == "switch.to-workload" else None
    source = authorize(peer, operation, target)
    if operation == "return.to-hub":
        if not LOCK.exists():
            raise RuntimeError("não existe uma troca supervisionada para concluir")
        prime_return_screen()
        unit = request_environment_stop(source)
        return {"accepted": True, "direction": "workload-to-hub", "source": source,
                "unit": unit}
    if source != "hub":
        assert target is not None
        prime_return_screen()
        unit = request_direct_switch(source, target)
        return {"accepted": True, "direction": "workload-to-workload",
                "source": source, "target": target, "unit": unit}
    unit = "apx-environment-handoff-" + secrets.token_hex(5)
    result = subprocess.run((
        "/usr/bin/systemd-run", f"--unit={unit}", "--collect", "--property=Type=simple",
        "--property=TimeoutStopSec=15s", RUNNER, "--environment", str(target),
    ), text=True, capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError("o supervisor da troca não arrancou")
    return {"accepted": True, "direction": "hub-to-workload", "unit": unit + ".service"}


def receive(connection: socket.socket) -> bytes:
    data = bytearray()
    while b"\n" not in data and len(data) <= MAX_MESSAGE_BYTES:
        chunk = connection.recv(min(4096, MAX_MESSAGE_BYTES + 1 - len(data)))
        if not chunk: break
        data.extend(chunk)
    return bytes(data)


def respond(connection: socket.socket) -> None:
    operation = "unknown"
    pid = -1
    try:
        pid, uid, gid = struct.unpack("3i", connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
        request = parse_message(receive(connection))
        operation = str(request["operation"])
        with SERVER_LOCK:
            result = apply(operation, dict(request["payload"]), HostServicesPeer(pid, uid, gid))
        response = {"schema": 1, "profile": PROFILE, "ok": True, "result": result, "error": None}
        print(f"APX Environment switch accepted operation={operation} peer_pid={pid}", flush=True)
    except Exception as error:
        response = {"schema": 1, "profile": PROFILE, "ok": False, "result": None,
                    "error": {"code": "request_rejected", "message": str(error)[:300]}}
        print(f"APX Environment switch rejected operation={operation} peer_pid={pid}: {error}",
              file=sys.stderr, flush=True)
    try:
        connection.sendall((json.dumps(response, sort_keys=True, separators=(",", ":")) + "\n").encode())
    except (BrokenPipeError, ConnectionResetError):
        # A GUI client may close its short-lived status request during a
        # reload or popup transition. Never let that client take down the
        # shared Host service and make the next progress read look invalid.
        print(f"APX Environment switch response dropped peer_pid={pid}", file=sys.stderr, flush=True)


def admit_existing_session() -> None:
    for active in (Path("/run/apx/official-hub-graphical-v1.json"), Path("/run/apx/active-graphical-environment-v1.json")):
        try:
            pid = int(json.loads(active.read_text())["pid"])
            fields = Path(f"/proc/{pid}/uid_map").read_text().split()
            if len(fields) == 3 and fields[0] == "0" and int(fields[2]) == 65536:
                translated = int(fields[1]) + 1000
                os.chown(SOCKET, translated, translated); os.chmod(SOCKET, 0o660)
                return
        except (OSError, ValueError, KeyError, json.JSONDecodeError):
            pass


def serve() -> None:
    SOCKET.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
    live_parent = LIVE_SOCKET.parent
    metadata = live_parent.stat()
    if metadata.st_uid != 0 or metadata.st_gid != 0 or metadata.st_mode & 0o022:
        raise RuntimeError("a ponte viva do HUB não é confiável")
    servers: list[socket.socket] = []
    try:
        for endpoint in (SOCKET, LIVE_SOCKET):
            endpoint.unlink(missing_ok=True)
            server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            server.bind(str(endpoint))
            os.chmod(endpoint, 0o600 if endpoint == SOCKET else 0o666)
            server.listen(8)
            servers.append(server)
        admit_existing_session()
        while True:
            readable, _, _ = select.select(servers, [], [])
            for server in readable:
                connection, _ = server.accept()
                with connection:
                    respond(connection)
    finally:
        for server in servers:
            server.close()


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--serve", action="store_true", required=True)
    serve(); return 0


if __name__ == "__main__":
    raise SystemExit(main())
