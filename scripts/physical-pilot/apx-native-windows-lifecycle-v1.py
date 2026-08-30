#!/usr/bin/env python3
"""Prepare one authenticated, reboot-bound native Windows create/delete."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import time


POLICY = Path("/usr/share/apx/native-environments/windows-policy-v1.json")
METADATA = Path("/var/lib/apx/native-environments/windows.json")
PENDING = Path("/var/lib/apx/native-environments/windows-pending.json")
STATE = Path("/run/apx/environment-management-v1.json")
LOCK = Path("/run/apx/environment-management-v1.lock")
BUILD = "/usr/lib/apx/build-native-windows-lifecycle-uki-v1.sh"
ENTRY = "apx-native-windows-lifecycle-v1.conf"
UKI = Path("/boot/EFI/APX/apx-native-windows-lifecycle-v1.efi")
ENTRY_FILE = Path("/boot/loader/entries/apx-native-windows-lifecycle-v1.conf")
MAINTENANCE_LABEL = "APX Windows Maintenance"
GENERATION = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}")


def run(arguments: tuple[str, ...]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(arguments, text=True, capture_output=True, check=False,
                          env={"PATH": "/usr/bin", "LC_ALL": "C"}, cwd=Path("/"))


def checked(arguments: tuple[str, ...]) -> str:
    result = run(arguments)
    if result.returncode:
        raise RuntimeError((result.stderr.strip() or result.stdout.strip() or "operação recusada")[-1000:])
    return result.stdout.strip()


def trusted_json(path: Path, profile: str, maximum: int = 4096) -> dict[str, object]:
    info = path.lstat(); raw = path.read_bytes(); value = json.loads(raw)
    if path.is_symlink() or not path.is_file() or info.st_uid != 0 or info.st_gid != 0 \
            or not raw or len(raw) > maximum or type(value) is not dict or value.get("profile") != profile:
        raise RuntimeError(f"os metadados {path.name} não são confiáveis")
    return value


def policy() -> dict[str, object]:
    value = trusted_json(POLICY, "apx-native-windows-policy-v1")
    if value.get("schema") != 1 or value.get("size_choices_gib") != [80, 120, 160] \
            or value.get("disk_id") != "AC9FC0BD-2162-43A9-AAE6-3F654FF6F275" \
            or value.get("disk_serial") != "S4DYNX0R253702" or value.get("max_instances") != 1:
        raise RuntimeError("a política Windows nativa difere")
    return value


def write_json(path: Path, value: dict[str, object], mode: int) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode)
    try:
        os.write(descriptor, (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode())
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    os.replace(temporary, path)


def write_state(action: str, phase: str, progress: int, message: str) -> None:
    write_json(STATE, {
        "schema": 1, "profile": "apx-environment-management-v1",
        "action": f"native-{action}", "target": "windows", "phase": phase,
        "progress": progress, "message": message, "updated_at": int(time.time()),
    }, 0o600)


def block_size(path: str) -> int:
    return int(checked(("/usr/bin/blockdev", "--getsize64", path)))


def maintenance_entries() -> list[str]:
    output = checked(("/usr/bin/efibootmgr", "-v"))
    matches = []
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
    output = checked(("/usr/bin/efibootmgr",))
    match = re.search(r"^BootOrder:\s*(\S+)$", output, re.MULTILINE)
    if match is None:
        raise RuntimeError("a ordem UEFI permanente não pôde ser confirmada")
    return match.group(1)


def validate_host() -> None:
    if os.geteuid() != 0 or Path("/etc/hostname").read_text().strip() != "apx-host" \
            or Path("/sys/class/dmi/id/product_name").read_text().strip() != "82JU":
        raise RuntimeError("a identidade do computador difere")
    if Path("/sys/block/nvme0n1/device/serial").read_text().strip() != "S4DYNX0R253702" \
            or checked(("/usr/bin/sfdisk", "--disk-id", "/dev/nvme0n1")) != "AC9FC0BD-2162-43A9-AAE6-3F654FF6F275":
        raise RuntimeError("a identidade do disco difere")
    if Path("/sys/class/power_supply/ADP0/online").read_text().strip() != "1" \
            or int(Path("/sys/class/power_supply/BAT0/capacity").read_text()) < 40:
        raise RuntimeError("liga o carregador e mantém pelo menos 40% de bateria")
    firmware = checked(("/usr/bin/efibootmgr",))
    if "BootCurrent: 0005" not in firmware or not re.search(r"^BootOrder: 0005(?:,|$)", firmware, re.MULTILINE) \
            or "BootNext:" in firmware:
        raise RuntimeError("o Linux não é o arranque principal ou já existe um BootNext")


def validate_create(size_gib: int) -> None:
    if METADATA.exists() or PENDING.exists() or any(Path(f"/dev/nvme0n1p{number}").exists() for number in range(3, 7)):
        raise RuntimeError("já existe um Windows nativo ou uma operação pendente")
    if block_size("/dev/nvme0n1p2") != 511035383296:
        raise RuntimeError("a partição APX não ocupa o disco completo")
    usage = checked(("/usr/bin/btrfs", "filesystem", "usage", "-b", "/"))
    match = re.search(r"^\s*Used:\s*(\d+)", usage, re.MULTILINE)
    if match is None:
        raise RuntimeError("a utilização Btrfs não pôde ser medida")
    tail_start = ((1000215183 - size_gib * 2097152) // 2048) * 2048
    target_bytes = (tail_start - 2099200 - 32768) * 512
    if int(match.group(1)) + 32 * 1024**3 > target_bytes:
        raise RuntimeError("o APX não tem margem suficiente para este tamanho Windows")


def validate_delete(size_gib: int, generation: str) -> None:
    value = trusted_json(METADATA, "apx-native-environment-v2")
    if value.get("state") != "ready" or value.get("generation") != generation \
            or value.get("requested_size_gib") != size_gib or PENDING.exists():
        raise RuntimeError("o Windows selecionado mudou ou já existe uma operação pendente")
    if not Path("/dev/nvme0n1p3").is_block_device() or not Path("/dev/nvme0n1p4").is_block_device() \
            or Path("/dev/nvme0n1p5").exists() or Path("/dev/nvme0n1p6").exists() \
            or checked(("/usr/bin/blkid", "-s", "PARTUUID", "-o", "value", "/dev/nvme0n1p3")).upper() \
            != "099C31D8-313A-4ABA-B0E0-2B59502C9674" \
            or checked(("/usr/bin/blkid", "-s", "PARTUUID", "-o", "value", "/dev/nvme0n1p4")).upper() \
            != "309BEBB6-5C32-4E21-9C92-6D758E51389D":
        raise RuntimeError("a disposição física do Windows difere")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--action", choices=("create", "delete"), required=True)
    parser.add_argument("--size-gib", type=int, choices=(80, 120, 160), required=True)
    parser.add_argument("--generation", required=True)
    parser.add_argument("--lock-token", required=True)
    arguments = parser.parse_args()
    if GENERATION.fullmatch(arguments.generation) is None:
        parser.error("invalid generation")
    lock_descriptor = os.open(LOCK, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    lock_info = os.fstat(lock_descriptor)
    token = os.read(lock_descriptor, 256).decode().strip()
    if lock_info.st_uid != 0 or lock_info.st_gid != 0 or token != arguments.lock_token:
        os.close(lock_descriptor)
        raise RuntimeError("a reserva da operação não é confiável")
    pending_written = False
    try:
        policy()
        validate_host()
        write_state(arguments.action, "planning", 8, "A validar o disco e a recuperação…")
        if arguments.action == "create":
            validate_create(arguments.size_gib)
        else:
            validate_delete(arguments.size_gib, arguments.generation)
        pending = {
            "schema": 1, "profile": "apx-native-windows-pending-v1",
            "action": arguments.action, "stage": "maintenance",
            "name": "windows", "generation": arguments.generation,
            "requested_size_gib": arguments.size_gib, "created_at": int(time.time()),
        }
        if arguments.action == "create":
            pending["explicit_attempts"] = 0
        write_json(PENDING, pending, 0o400); pending_written = True
        write_state(arguments.action, "applying", 24, "A construir a manutenção assinada…")
        checked((BUILD, arguments.action, str(arguments.size_gib), arguments.generation))
        if maintenance_entries():
            raise RuntimeError("já existe uma entrada temporária de manutenção")
        permanent_order = boot_order()
        checked(("/usr/bin/efibootmgr", "--create-only", "--disk", "/dev/nvme0n1", "--part", "1",
                 "--label", MAINTENANCE_LABEL,
                 "--loader", "\\EFI\\APX\\apx-native-windows-lifecycle-v1.efi"))
        temporary_entries = maintenance_entries()
        if len(temporary_entries) != 1:
            raise RuntimeError("a entrada UEFI temporária não ficou inequívoca")
        if boot_order() != permanent_order:
            raise RuntimeError("a manutenção tentou alterar a ordem UEFI permanente")
        ENTRY_FILE.unlink()
        checked(("/usr/bin/efibootmgr", "-n", temporary_entries[0]))
        if f"BootNext: {temporary_entries[0]}" not in checked(("/usr/bin/efibootmgr",)):
            raise RuntimeError("o arranque UEFI único de manutenção não ficou confirmado")
        if boot_order() != permanent_order:
            raise RuntimeError("BootNext alterou a ordem UEFI permanente")
        write_state(arguments.action, "applying", 36, "A reiniciar para a manutenção segura do disco…")
        result = run(("/usr/bin/systemctl", "--no-block", "reboot"))
        if result.returncode:
            raise RuntimeError("o reinício de manutenção foi recusado")
        return 0
    except Exception as error:
        run(("/usr/bin/efibootmgr", "-N"))
        try:
            for number in maintenance_entries():
                run(("/usr/bin/efibootmgr", "-b", number, "-B"))
        except Exception:
            pass
        if pending_written:
            PENDING.unlink(missing_ok=True)
        UKI.unlink(missing_ok=True); ENTRY_FILE.unlink(missing_ok=True)
        write_state(arguments.action, "failed", 100, str(error)[-300:])
        raise
    finally:
        os.close(lock_descriptor)
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
        print(f"APX native Windows lifecycle failed: {error}", file=__import__("sys").stderr)
        raise SystemExit(2)
