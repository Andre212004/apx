#!/usr/bin/env python3
"""Retry or discard one authenticated, incomplete native-Windows creation."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import time


PENDING = Path("/var/lib/apx/native-environments/windows-pending.json")
STATE = Path("/run/apx/environment-management-v1.json")
LOCK = Path("/run/apx/environment-management-v1.lock")
BUILD = "/usr/lib/apx/build-native-windows-lifecycle-uki-v1.sh"
REFRESH = "/usr/lib/apx/refresh-native-windows-installer-v2.sh"
UKI = Path("/boot/EFI/APX/apx-native-windows-lifecycle-v1.efi")
ENTRY_FILE = Path("/boot/loader/entries/apx-native-windows-lifecycle-v1.conf")
FINALIZER = "apx-native-windows-lifecycle-finalize-v1.service"
MAINTENANCE_LABEL = "APX Windows Maintenance"
MAX_EXPLICIT_INSTALL_ATTEMPTS = 2
# OOBE may legitimately restart for setup phase transitions, language changes,
# and zero-day patch (ZDP) updates. Every continuation remains a user-approved
# one-shot BootNext; this larger budget does not introduce automatic retries.
MAX_EXPLICIT_BOOT_ATTEMPTS = 8
GENERATION = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}")


def run(arguments: tuple[str, ...]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(arguments, text=True, capture_output=True, check=False,
                          env={"PATH": "/usr/bin", "LC_ALL": "C"}, cwd=Path("/"))


def checked(arguments: tuple[str, ...]) -> str:
    result = run(arguments)
    if result.returncode:
        raise RuntimeError((result.stderr.strip() or result.stdout.strip() or "operação recusada")[-1000:])
    return result.stdout.strip()


def trusted_pending() -> tuple[dict[str, object], bytes]:
    info = PENDING.lstat(); raw = PENDING.read_bytes(); value = json.loads(raw)
    allowed = {"action", "boot_attempts", "created_at", "explicit_attempts", "failed_at", "failure_code", "failure_reason",
               "failure_step", "generation", "name", "profile", "requested_size_gib",
               "resume_attempts", "schema", "stage"}
    if PENDING.is_symlink() or not PENDING.is_file() or (info.st_uid, info.st_gid) != (0, 0) \
            or stat.S_IMODE(info.st_mode) != 0o400 or not raw or len(raw) > 4096 \
            or type(value) is not dict or not set(value).issubset(allowed) \
            or value.get("schema") != 1 or value.get("profile") != "apx-native-windows-pending-v1" \
            or (value.get("action"), value.get("stage")) not in {
                ("create", "prepared"), ("create", "installing"),
                ("create", "boot-prepared"), ("create", "failed"),
                ("create", "recovery-required"), ("delete", "maintenance"),
            } \
            or value.get("name") != "windows" or value.get("requested_size_gib") not in {80, 120, 160} \
            or GENERATION.fullmatch(str(value.get("generation", ""))) is None \
            or type(value.get("created_at")) is not int or value["created_at"] <= 0:
        raise RuntimeError("a criação Windows pendente não é confiável")
    attempts = value.get("resume_attempts", 0)
    if type(attempts) is not int or not 0 <= attempts <= 12:
        raise RuntimeError("as retomas Windows pendentes diferem")
    explicit_attempts = value.get("explicit_attempts", 0)
    if type(explicit_attempts) is not int \
            or not 0 <= explicit_attempts <= MAX_EXPLICIT_INSTALL_ATTEMPTS:
        raise RuntimeError("as tentativas Windows explícitas diferem")
    boot_attempts = value.get("boot_attempts", 0)
    if type(boot_attempts) is not int or not 0 <= boot_attempts <= MAX_EXPLICIT_BOOT_ATTEMPTS:
        raise RuntimeError("as continuações do primeiro arranque Windows diferem")
    return value, raw


def write_json(path: Path, value: dict[str, object], mode: int) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode)
    try:
        os.write(descriptor, (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode())
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    os.replace(temporary, path)


def restore_pending(raw: bytes) -> None:
    temporary = PENDING.with_name(f".{PENDING.name}.{os.getpid()}.restore")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o400)
    try:
        os.write(descriptor, raw); os.fsync(descriptor)
    finally:
        os.close(descriptor)
    os.replace(temporary, PENDING)


def write_state(action: str, phase: str, progress: int, message: str) -> None:
    write_json(STATE, {
        "schema": 1, "profile": "apx-environment-management-v1",
        "action": f"native-{action}", "target": "windows", "phase": phase,
        "progress": progress, "message": message, "updated_at": int(time.time()),
    }, 0o600)


def maintenance_entries() -> list[str]:
    output = checked(("/usr/bin/efibootmgr", "-v")); matches = []
    for line in output.splitlines():
        found = re.match(r"^Boot([0-9A-F]{4})\*?\s+(.+)$", line)
        if found is None or not found.group(2).startswith(MAINTENANCE_LABEL + "\t"):
            continue
        lowered = found.group(2).lower()
        if "hd(1,gpt,9625f250-9acc-453a-ae63-0c863ade440f," not in lowered \
                or "\\efi\\apx\\apx-native-windows-lifecycle-v1.efi" not in lowered:
            raise RuntimeError("a entrada temporária de manutenção difere")
        matches.append(found.group(1))
    return matches


def boot_order() -> str:
    match = re.search(r"^BootOrder:\s*(\S+)$", checked(("/usr/bin/efibootmgr",)), re.MULTILINE)
    if match is None:
        raise RuntimeError("a ordem UEFI permanente não pôde ser confirmada")
    return match.group(1)


def exact_setup_entry() -> str:
    output = checked(("/usr/bin/efibootmgr", "-v"))
    matches = []
    for line in output.splitlines():
        found = re.match(r"^Boot([0-9A-F]{4})\*?\s+(.+)$", line)
        if found is None or not found.group(2).startswith("APX Windows Setup\t"):
            continue
        lowered = found.group(2).lower()
        if "hd(4,gpt,309bebb6-5c32-4e21-9c92-6d758e51389d," in lowered \
                and "\\efi\\boot\\bootx64.efi" in lowered:
            matches.append(found.group(1))
    if len(matches) != 1:
        raise RuntimeError("a entrada do instalador Windows não é inequívoca")
    return matches[0]


def exact_windows_entry(generation: str) -> str:
    if not Path("/dev/nvme0n1p3").is_block_device() \
            or checked(("/usr/bin/blkid", "-s", "PARTUUID", "-o", "value",
                        "/dev/nvme0n1p3")).upper() != "099C31D8-313A-4ABA-B0E0-2B59502C9674" \
            or checked(("/usr/bin/blkid", "-s", "TYPE", "-o", "value",
                        "/dev/nvme0n1p3")).lower() != "ntfs":
        raise RuntimeError("o alvo Windows aplicado difere")
    status = Path("/boot/EFI/APX/native-windows/install-status-v2.ini")
    raw = status.read_bytes()
    values: dict[str, str] = {}
    try:
        for line in raw.decode("ascii").splitlines():
            key, separator, value = line.partition("=")
            if not separator or key in values:
                raise ValueError("duplicate or malformed status field")
            values[key] = value
    except (UnicodeError, ValueError) as error:
        raise RuntimeError("o estado espelhado do primeiro arranque Windows difere") from error
    if status.is_symlink() or not status.is_file() or len(raw) > 4096 or set(values) != {
            "profile", "generation", "status", "image_index", "windows_partition_guid",
            "esp_partition_guid", "target_letter", "esp_letter",
    } or values != {
            "profile": "apx-native-windows-install-status-v2",
            "generation": generation,
            "status": "boot-prepared",
            "image_index": "6",
            "windows_partition_guid": "099C31D8-313A-4ABA-B0E0-2B59502C9674",
            "esp_partition_guid": "9625F250-9ACC-453A-AE63-0C863ADE440F",
            "target_letter": "R:",
            "esp_letter": "S:",
    }:
        raise RuntimeError("o estado espelhado do primeiro arranque Windows difere")
    output = checked(("/usr/bin/efibootmgr", "-v"))
    matches = []
    for line in output.splitlines():
        found = re.match(r"^Boot([0-9A-F]{4})\*?\s+(.+)$", line)
        if found is None or not found.group(2).startswith("Windows Boot Manager\t"):
            continue
        lowered = found.group(2).lower()
        if "hd(1,gpt,9625f250-9acc-453a-ae63-0c863ade440f," in lowered \
                and "\\efi\\microsoft\\boot\\bootmgfw.efi" in lowered:
            matches.append(found.group(1))
    if len(matches) != 1 or not Path("/boot/EFI/Microsoft/Boot/bootmgfw.efi").is_file() \
            or not Path("/boot/EFI/Microsoft/Boot/BCD").is_file():
        raise RuntimeError("a entrada Windows instalada não é inequívoca")
    return matches[0]


def validate_host() -> None:
    if os.geteuid() != 0 or Path("/etc/hostname").read_text().strip() != "apx-host" \
            or Path("/sys/class/dmi/id/product_name").read_text().strip() != "82JU":
        raise RuntimeError("a identidade do computador difere")
    if Path("/sys/block/nvme0n1/device/serial").read_text().strip() != "S4DYNX0R253702" \
            or checked(("/usr/bin/sfdisk", "--disk-id", "/dev/nvme0n1")) \
            != "AC9FC0BD-2162-43A9-AAE6-3F654FF6F275":
        raise RuntimeError("a identidade do disco difere")
    if Path("/sys/class/power_supply/ADP0/online").read_text().strip() != "1" \
            or int(Path("/sys/class/power_supply/BAT0/capacity").read_text()) < 40:
        raise RuntimeError("liga o carregador e mantém pelo menos 40% de bateria")
    firmware = checked(("/usr/bin/efibootmgr",))
    if "BootCurrent: 0005" not in firmware or not re.search(r"^BootOrder: 0005(?:,|$)", firmware, re.MULTILINE) \
            or "BootNext:" in firmware or maintenance_entries():
        raise RuntimeError("o arranque UEFI não está livre para a recuperação")
    service = run(("/usr/bin/systemctl", "is-active", FINALIZER))
    if service.returncode == 0 or service.stdout.strip() in {"activating", "deactivating"}:
        raise RuntimeError("o finalizador Windows ainda está ativo")
    info = STATE.lstat(); raw = STATE.read_bytes(); state = json.loads(raw)
    if STATE.is_symlink() or not STATE.is_file() or (info.st_uid, info.st_gid) != (0, 0) \
            or len(raw) > 8192 or state.get("profile") != "apx-environment-management-v1" \
            or state.get("phase") not in {"failed", "prepared", "recovery-required"} \
            or state.get("action") not in {"native-create", "native-delete", "native-retry", "native-discard"} \
            or state.get("target") != "windows":
        raise RuntimeError("a criação Windows não está numa falha recuperável")


def retry(pending: dict[str, object], original: bytes) -> None:
    if pending.get("action") != "create" or pending.get("stage") not in {
            "prepared", "failed", "recovery-required", "boot-prepared"}:
        raise RuntimeError("a criação Windows já não pode ser retomada")
    size, generation = int(pending["requested_size_gib"]), str(pending["generation"])
    install_attempts = pending.get("explicit_attempts", 0)
    boot_attempts = pending.get("boot_attempts", 0)
    previous_stage = str(pending["stage"])
    if previous_stage == "boot-prepared":
        if type(boot_attempts) is not int \
                or not 0 <= boot_attempts < MAX_EXPLICIT_BOOT_ATTEMPTS:
            raise RuntimeError("o limite de continuações do primeiro arranque Windows foi atingido")
    elif type(install_attempts) is not int \
            or not 0 <= install_attempts < MAX_EXPLICIT_INSTALL_ATTEMPTS:
        raise RuntimeError("o limite de duas tentativas explícitas de instalação foi atingido")
    try:
        if previous_stage == "boot-prepared":
            entry = exact_windows_entry(generation)
        else:
            write_state("retry", "applying", 18, "A validar e reconstruir o instalador Windows…")
            pending["stage"] = "installing"
            pending["explicit_attempts"] = install_attempts + 1
            pending.setdefault("boot_attempts", 0)
            for key in ("failed_at", "failure_code", "failure_reason", "failure_step"):
                pending.pop(key, None)
            write_json(PENDING, pending, 0o400)
            checked((REFRESH, str(size), generation))
            entry = exact_setup_entry()
        if previous_stage == "boot-prepared":
            pending["boot_attempts"] = boot_attempts + 1
            write_json(PENDING, pending, 0o400)
        checked(("/usr/bin/efibootmgr", "-n", entry))
        if f"BootNext: {entry}" not in checked(("/usr/bin/efibootmgr",)):
            raise RuntimeError("o arranque Windows explícito não ficou armado")
        message = (f"Continuação explícita do primeiro arranque Windows "
                   f"{boot_attempts + 1}/{MAX_EXPLICIT_BOOT_ATTEMPTS}…") \
            if previous_stage == "boot-prepared" else \
            (f"Tentativa explícita de instalação Windows "
             f"{install_attempts + 1}/{MAX_EXPLICIT_INSTALL_ATTEMPTS}…")
        write_state("retry", "applying", 86, message)
        result = run(("/usr/bin/systemctl", "--no-block", "reboot"))
        if result.returncode:
            raise RuntimeError("o reinício Windows explícito foi recusado")
    except Exception:
        run(("/usr/bin/efibootmgr", "-N"))
        restore_pending(original)
        raise


def discard(pending: dict[str, object], original: bytes) -> None:
    size, generation = int(pending["requested_size_gib"]), str(pending["generation"])
    write_state("discard", "applying", 16, "A preparar a remoção segura da criação incompleta…")
    checked((BUILD, "delete", str(size), generation))
    if maintenance_entries():
        raise RuntimeError("já existe uma entrada temporária de manutenção")
    permanent_order = boot_order()
    checked(("/usr/bin/efibootmgr", "--create-only", "--disk", "/dev/nvme0n1", "--part", "1",
             "--label", MAINTENANCE_LABEL, "--loader", "\\EFI\\APX\\apx-native-windows-lifecycle-v1.efi"))
    entries = maintenance_entries()
    if len(entries) != 1 or boot_order() != permanent_order:
        raise RuntimeError("a manutenção de remoção não ficou isolada")
    ENTRY_FILE.unlink()
    checked(("/usr/bin/efibootmgr", "-n", entries[0]))
    if f"BootNext: {entries[0]}" not in checked(("/usr/bin/efibootmgr",)) or boot_order() != permanent_order:
        raise RuntimeError("o arranque único de remoção não ficou confirmado")
    pending["action"] = "delete"; pending["stage"] = "maintenance"
    pending.pop("resume_attempts", None)
    pending.pop("explicit_attempts", None)
    pending.pop("boot_attempts", None)
    try:
        write_json(PENDING, pending, 0o400)
        write_state("discard", "applying", 38, "A reiniciar para devolver o espaço ao APX…")
        result = run(("/usr/bin/systemctl", "--no-block", "reboot"))
        if result.returncode:
            raise RuntimeError("o reinício de remoção foi recusado")
    except Exception:
        restore_pending(original)
        raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--action", choices=("retry", "discard"), required=True)
    parser.add_argument("--generation", required=True)
    parser.add_argument("--lock-token", required=True)
    arguments = parser.parse_args()
    if GENERATION.fullmatch(arguments.generation) is None:
        parser.error("invalid generation")
    descriptor = os.open(LOCK, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    lock_info = os.fstat(descriptor); token = os.read(descriptor, 256).decode().strip()
    if (lock_info.st_uid, lock_info.st_gid) != (0, 0) or token != arguments.lock_token:
        os.close(descriptor)
        raise RuntimeError("a reserva da recuperação não é confiável")
    try:
        pending, original = trusted_pending()
        if pending["generation"] != arguments.generation:
            raise RuntimeError("a geração Windows pendente mudou")
        validate_host()
        if arguments.action == "retry":
            retry(pending, original)
        else:
            discard(pending, original)
        return 0
    except Exception as error:
        if arguments.action == "discard":
            run(("/usr/bin/efibootmgr", "-N"))
            try:
                for number in maintenance_entries():
                    run(("/usr/bin/efibootmgr", "-b", number, "-B"))
            except Exception:
                pass
            UKI.unlink(missing_ok=True); ENTRY_FILE.unlink(missing_ok=True)
        write_state(arguments.action, "failed", 100, str(error)[-300:])
        raise
    finally:
        os.close(descriptor)
        try:
            current = LOCK.lstat()
            if not LOCK.is_symlink() and (current.st_dev, current.st_ino) == (lock_info.st_dev, lock_info.st_ino):
                LOCK.unlink()
        except FileNotFoundError:
            pass


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as error:
        print(f"APX native Windows recovery failed: {error}", file=__import__("sys").stderr)
        raise SystemExit(2)
