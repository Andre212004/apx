#!/usr/bin/env python3
"""Finalize a signed offline native-Windows lifecycle result after Linux boots."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import tempfile
import time


PENDING = Path("/var/lib/apx/native-environments/windows-pending.json")
METADATA = Path("/var/lib/apx/native-environments/windows.json")
LEGACY_STORAGE = Path("/var/lib/apx/native-environments/windows-storage-v1.json")
INSTALLER_MARKER = Path("/var/lib/apx/native-environments/windows-installer-prepared-v2.json")
LEGACY_INSTALLER_MARKER = Path("/var/lib/apx/native-environments/windows-installer-prepared-v1.json")
FAILURES = Path("/var/lib/apx/native-environments/windows-failures")
STATUS = Path("/boot/EFI/APX/recovery/windows-lifecycle-v1.status")
EFI_INSTALL_STATUS = Path("/boot/EFI/APX/native-windows/install-status-v2.ini")
STATE = Path("/run/apx/environment-management-v1.json")
PREPARE = "/usr/lib/apx/prepare-native-windows-installer-v2.sh"
UKI = Path("/boot/EFI/APX/apx-native-windows-lifecycle-v1.efi")
ENTRY = Path("/boot/loader/entries/apx-native-windows-lifecycle-v1.conf")
GENERATION = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}")
TERMINAL_STAGES = {"failed", "recovery-required"}
EXPECTED_RETURN_HASHES = {
    "ProgramData/APX/ReturnToHub/APX-ReturnToHub.ps1": "fbd55f62c4abe4d0456832b7e5d0397989da0876e0f5952adf36c2092bb708a4",
    "ProgramData/APX/ReturnToHub/README.txt": "0434aa1e310d7a4e20400300f0d8b6062caf8f4ac023ae4a8560a5c203926349",
    "ProgramData/Microsoft/Windows/Start Menu/Programs/Startup/APX-ReturnToHub.vbs": "504a32302dbfc5590e6059dde1ec563e6e04371bfac6c8e352b20b10f044757f",
}


def run(arguments: tuple[str, ...]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(arguments, text=True, capture_output=True, check=False,
                          env={"PATH": "/usr/bin", "LC_ALL": "C"}, cwd=Path("/"))


def checked(arguments: tuple[str, ...]) -> str:
    result = run(arguments)
    if result.returncode:
        raise RuntimeError((result.stderr.strip() or result.stdout.strip() or "operação recusada")[-1000:])
    return result.stdout.strip()


def trusted_json(path: Path, profile: str) -> dict[str, object]:
    info = path.lstat(); raw = path.read_bytes(); value = json.loads(raw)
    if path.is_symlink() or not path.is_file() or info.st_uid != 0 or info.st_gid != 0 \
            or stat.S_IMODE(info.st_mode) != 0o400 or not raw or len(raw) > 4096 \
            or type(value) is not dict or value.get("profile") != profile:
        raise RuntimeError(f"os metadados {path.name} não são confiáveis")
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


def block_value(path: str, field: str) -> str:
    return checked(("/usr/bin/blkid", "-s", field, "-o", "value", path)).upper()


def firmware() -> tuple[str, dict[str, str], list[str]]:
    output = checked(("/usr/bin/efibootmgr", "-v"))
    order_match = re.search(r"^BootOrder:\s*([0-9A-F,]+)$", output, re.MULTILINE)
    if order_match is None:
        raise RuntimeError("a ordem UEFI não pôde ser lida")
    entries = {}
    for line in output.splitlines():
        match = re.match(r"^Boot([0-9A-F]{4})\*?\s+(.+)$", line)
        if match:
            entries[match.group(1)] = match.group(2)
    return output, entries, order_match.group(1).split(",")


def linux_entry(entries: dict[str, str]) -> str:
    matches = [number for number, text in entries.items()
               if text.startswith("Linux Boot Manager\t") and
               "9625f250-9acc-453a-ae63-0c863ade440f" in text.lower() and
               "\\efi\\systemd\\systemd-bootx64.efi" in text.lower()]
    if len(matches) != 1:
        raise RuntimeError("a entrada Linux UEFI é ambígua")
    return matches[0]


def set_linux_first(windows: str | None = None) -> None:
    _output, entries, order = firmware()
    linux = linux_entry(entries)
    selected = [linux]
    if windows is not None:
        selected.append(windows)
    for number in order:
        if number in entries and number not in selected and not entries[number].startswith("APX Windows Setup\t"):
            selected.append(number)
    checked(("/usr/bin/efibootmgr", "-o", ",".join(selected)))
    if not checked(("/usr/bin/efibootmgr",)).startswith(f"BootCurrent: {linux}\n"):
        raise RuntimeError("o Linux atual mudou durante a finalização")


def ensure_linux_safe() -> None:
    """Clear one-shot firmware state and keep the authenticated Linux entry first."""
    clear = run(("/usr/bin/efibootmgr", "-N"))
    output, entries, order = firmware()
    if clear.returncode and "BootNext:" in output:
        raise RuntimeError("BootNext não pôde ser limpo")
    linux = linux_entry(entries)
    if not order or order[0] != linux:
        set_linux_first()
        output, entries, order = firmware()
        linux = linux_entry(entries)
    if "BootNext:" in output or not order or order[0] != linux:
        raise RuntimeError("o caminho seguro Linux não ficou confirmado")


def archive_failure(pending: dict[str, object], status: dict[str, str] | None,
                    reason: str) -> None:
    """Persist every terminal diagnosis without deleting earlier evidence."""
    generation = str(pending["generation"])
    FAILURES.mkdir(mode=0o700, parents=True, exist_ok=True)
    root = FAILURES / generation
    root.mkdir(mode=0o700, exist_ok=True)
    recorded_at = int(time.time())
    raw_attempt = pending.get("explicit_attempts", 0)
    attempt = raw_attempt if type(raw_attempt) is int and 0 <= raw_attempt <= 2 else 0
    record = {
        "schema": 1,
        "profile": "apx-native-windows-failure-v1",
        "recorded_at": recorded_at,
        "reason": reason[:1000],
        "pending": pending.copy(),
        "winpe_status": status,
    }
    first = root / "failure.json"
    if not first.exists():
        write_json(first, record, 0o400)
    digest = hashlib.sha256(json.dumps(record, sort_keys=True,
                                       separators=(",", ":")).encode()).hexdigest()[:12]
    target = root / f"failure-{recorded_at}-attempt-{attempt}-{digest}.json"
    if not target.exists():
        write_json(target, record, 0o400)


def mark_terminal(pending: dict[str, object], stage: str, code: str,
                  step: str, reason: str, status: dict[str, str] | None = None) -> None:
    if stage not in TERMINAL_STAGES:
        raise ValueError("invalid terminal Windows stage")
    original = pending.copy()
    firmware_error = ""
    try:
        ensure_linux_safe()
    except Exception as error:
        firmware_error = f"; firmware safety check: {error}"
    archive_failure(original, status, reason + firmware_error)
    pending.update({
        "stage": stage,
        "failure_code": code[:80],
        "failure_step": step[:120],
        "failure_reason": (reason + firmware_error)[:1000],
        "failed_at": int(time.time()),
    })
    write_json(PENDING, pending, 0o400)
    write_state(str(pending.get("action", "create")), stage, 100,
                f"{code}: {reason}"[:300])


def remove_setup_entries() -> None:
    _output, entries, _order = firmware()
    for number, text in entries.items():
        if text.startswith("APX Windows Setup\t"):
            checked(("/usr/bin/efibootmgr", "-b", number, "-B"))


def cleanup_maintenance() -> None:
    _output, entries, _order = firmware()
    for number, text in entries.items():
        if not text.startswith("APX Windows Maintenance\t"):
            continue
        lowered = text.lower()
        if "9625f250-9acc-453a-ae63-0c863ade440f" not in lowered \
                or "\\efi\\apx\\apx-native-windows-lifecycle-v1.efi" not in lowered:
            raise RuntimeError("a entrada temporária de manutenção difere")
        checked(("/usr/bin/efibootmgr", "-b", number, "-B"))
    UKI.unlink(missing_ok=True); ENTRY.unlink(missing_ok=True)


def cleanup_windows_efi() -> None:
    if checked(("/usr/bin/findmnt", "-rn", "-o", "SOURCE", "/boot")) != "/dev/nvme0n1p1" \
            or block_value("/dev/nvme0n1p1", "PARTUUID") != "9625F250-9ACC-453A-AE63-0C863ADE440F" \
            or not Path("/boot/EFI/systemd/systemd-bootx64.efi").is_file() \
            or not Path("/boot/EFI/APX").is_dir():
        raise RuntimeError("a APX_EFI não é confiável para remover os ficheiros Windows")
    microsoft = Path("/boot/EFI/Microsoft")
    if microsoft.is_symlink():
        raise RuntimeError("a árvore EFI Microsoft não é confiável")
    if microsoft.exists():
        shutil.rmtree(microsoft)
    native = Path("/boot/EFI/APX/native-windows")
    if native.is_symlink():
        raise RuntimeError("o contrato EFI Windows não é confiável")
    if native.exists():
        shutil.rmtree(native)


def finalize_delete(pending: dict[str, object]) -> None:
    size = int(pending["requested_size_gib"]); generation = str(pending["generation"])
    expected_reserved = (1000215183 - ((1000215183 - size * 2097152) // 2048 * 2048)) * 512
    stage = str(pending.get("stage", ""))
    if stage == "maintenance":
        cleanup_maintenance()
        if STATUS.read_text().strip() != f"success:delete:{size}:{generation}:{expected_reserved}":
            raise RuntimeError("o resultado offline de eliminação difere")
        pending["stage"] = "finalizing"; write_json(PENDING, pending, 0o400)
    elif stage != "finalizing":
        raise RuntimeError("a fase de eliminação Windows difere")
    if int(checked(("/usr/bin/blockdev", "--getsize64", "/dev/nvme0n1p2"))) != 511035383296 \
            or any(Path(f"/dev/nvme0n1p{number}").exists() for number in range(3, 7)):
        raise RuntimeError("o disco não regressou à disposição APX completa")
    if int(checked(("/usr/bin/blockdev", "--getsize64", "/dev/mapper/cryptroot"))) != 511018606080:
        raise RuntimeError("o volume cifrado não reabriu com o tamanho completo")
    checked(("/usr/bin/btrfs", "filesystem", "resize", "1:max", "/"))
    remove_setup_entries()
    _output, entries, _order = firmware()
    for number, text in list(entries.items()):
        if text.startswith("Windows Boot Manager\t"):
            checked(("/usr/bin/efibootmgr", "-b", number, "-B"))
    set_linux_first()
    cleanup_windows_efi()
    METADATA.unlink(missing_ok=True); LEGACY_STORAGE.unlink(missing_ok=True)
    INSTALLER_MARKER.unlink(missing_ok=True); LEGACY_INSTALLER_MARKER.unlink(missing_ok=True)
    STATUS.unlink(missing_ok=True)
    cleanup_maintenance()
    write_state("delete", "complete", 100, "Windows apagado; todo o espaço regressou ao APX.")
    PENDING.unlink(missing_ok=True)
    run(("/usr/bin/systemctl", "restart", "apx-environment-switch-v1.service"))


def windows_complete() -> tuple[str, str, int] | None:
    if not Path("/dev/nvme0n1p3").is_block_device() or not Path("/dev/nvme0n1p4").is_block_device():
        return None
    if block_value("/dev/nvme0n1p3", "PARTUUID") != "099C31D8-313A-4ABA-B0E0-2B59502C9674" \
            or block_value("/dev/nvme0n1p3", "TYPE") != "NTFS" \
            or block_value("/dev/nvme0n1p1", "PARTUUID") != "9625F250-9ACC-453A-AE63-0C863ADE440F":
        return None
    root = Path(tempfile.mkdtemp(prefix="apx-windows-complete-", dir="/run"))
    try:
        checked(("/usr/bin/mount", "-t", "ntfs3", "-o", "ro,nosuid,nodev,noexec", "/dev/nvme0n1p3", str(root)))
        users = root / "Users"
        if not users.is_dir() or users.is_symlink():
            return None
        profiles = {child.name.lower() for child in users.iterdir()
                    if child.is_dir() and not child.is_symlink()}
        if not (root / "Windows/System32/winload.efi").is_file() \
                or not profiles.difference({"default", "default user", "public", "defaultuser0", "all users"}):
            return None
        for relative, expected in EXPECTED_RETURN_HASHES.items():
            path = root / relative
            if path.is_symlink() or not path.is_file() or path.stat().st_size > 32768 \
                    or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                return None
        desktop_fallback = root / "Users/Public/Desktop/REGRESSAR AO APX.cmd"
        if desktop_fallback.exists() or desktop_fallback.is_symlink():
            return None
        repositories = [path for path in
                        (root / "Windows/System32/DriverStore/FileRepository").glob(
                            "netrtwlane6.inf_*"
                        ) if path.is_dir() and not path.is_symlink()]
        matching = []
        for repository in repositories:
            for inf in repository.glob("netrtwlane6.inf"):
                if inf.is_symlink() or not inf.is_file() or inf.stat().st_size > 2 * 1024 * 1024:
                    continue
                raw = inf.read_bytes()
                try:
                    text = raw.decode("utf-16" if raw.startswith((b"\xff\xfe", b"\xfe\xff")) else "utf-8")
                except UnicodeError:
                    continue
                if "pci\\ven_10ec&dev_8852&subsys_485217aa" in text.lower():
                    matching.append(inf)
        if not matching:
            return None
    finally:
        run(("/usr/bin/umount", str(root))); root.rmdir()
    manager = Path("/boot/EFI/Microsoft/Boot/bootmgfw.efi")
    bcd = Path("/boot/EFI/Microsoft/Boot/BCD")
    if manager.is_symlink() or not manager.is_file() or not 64 * 1024 <= manager.stat().st_size <= 8 * 1024 * 1024 \
            or bcd.is_symlink() or not bcd.is_file() or not 16 * 1024 <= bcd.stat().st_size <= 1024 * 1024:
        return None
    signature = run(("/usr/bin/sbverify", "--list", str(manager)))
    if signature.returncode or "Microsoft" not in signature.stdout:
        return None
    output, entries, _order = firmware()
    matches = [number for number, text in entries.items()
               if text.startswith("Windows Boot Manager\t") and
               "9625f250-9acc-453a-ae63-0c863ade440f" in text.lower() and
               "\\efi\\microsoft\\boot\\bootmgfw.efi" in text.lower()]
    if len(matches) != 1:
        return None
    return matches[0], block_value("/dev/nvme0n1p3", "PARTUUID"), int(checked(("/usr/bin/blockdev", "--getsize64", "/dev/nvme0n1p3")))


def parse_installer_status(path: Path, generation: str) -> tuple[dict[str, str], bytes] | None:
    if not path.is_file() or path.is_symlink() or path.stat().st_size > 4096:
        return None
    raw = path.read_bytes()
    try:
        lines = raw.decode("ascii").splitlines()
    except UnicodeError:
        return None
    values: dict[str, str] = {}
    for line in lines:
        key, separator, value = line.partition("=")
        if not separator or key in values:
            return None
        values[key] = value
    if values.get("profile") != "apx-native-windows-install-status-v2" \
            or values.get("generation") != generation \
            or values.get("status") not in {"boot-prepared", "failed"}:
        return None
    return values, raw


def installer_status(generation: str) -> dict[str, str] | None:
    if not Path("/dev/nvme0n1p4").is_block_device() \
            or block_value("/dev/nvme0n1p4", "PARTUUID") != "309BEBB6-5C32-4E21-9C92-6D758E51389D" \
            or block_value("/dev/nvme0n1p4", "TYPE") != "VFAT":
        return None
    root = Path(tempfile.mkdtemp(prefix="apx-windows-status-", dir="/run"))
    try:
        checked(("/usr/bin/mount", "-t", "vfat", "-o", "ro,nosuid,nodev,noexec", "/dev/nvme0n1p4", str(root)))
        parsed = parse_installer_status(root / "APX/install-status-v2.ini", generation)
        if parsed is None:
            return None
        values, raw = parsed
        # A failure marker can only move the machine to a safer terminal state,
        # so the authenticated setup identity and generation are sufficient.
        if values["status"] == "failed":
            return values
        # Success can authorize a later Windows boot, so require the identical
        # marker independently mirrored on the APX ESP.
        mirrored = parse_installer_status(EFI_INSTALL_STATUS, generation)
        if mirrored is None or mirrored[1] != raw:
            return None
        return values
    finally:
        run(("/usr/bin/umount", str(root))); root.rmdir()


def windows_resume_entry(status: dict[str, str] | None) -> str | None:
    """Return only an exact installed Windows or still-valid setup boot entry."""
    _output, entries, _order = firmware()
    windows = [number for number, text in entries.items()
               if text.startswith("Windows Boot Manager\t") and
               "9625f250-9acc-453a-ae63-0c863ade440f" in text.lower() and
               "\\efi\\microsoft\\boot\\bootmgfw.efi" in text.lower()]
    if status is not None and status.get("status") == "boot-prepared" and len(windows) == 1 \
            and Path("/dev/nvme0n1p3").is_block_device() \
            and block_value("/dev/nvme0n1p3", "PARTUUID") == "099C31D8-313A-4ABA-B0E0-2B59502C9674" \
            and Path("/boot/EFI/Microsoft/Boot/bootmgfw.efi").is_file() \
            and Path("/boot/EFI/Microsoft/Boot/BCD").is_file():
        return windows[0]
    setup = [number for number, text in entries.items()
             if text.startswith("APX Windows Setup\t") and
               "309bebb6-5c32-4e21-9c92-6d758e51389d" in text.lower() and
               "\\efi\\boot\\bootx64.efi" in text.lower()]
    if status is None and len(setup) == 1 and Path("/dev/nvme0n1p4").is_block_device() \
            and block_value("/dev/nvme0n1p4", "PARTUUID") == "309BEBB6-5C32-4E21-9C92-6D758E51389D":
        return setup[0]
    return None


def finalize_create(pending: dict[str, object]) -> None:
    size = int(pending["requested_size_gib"]); generation = str(pending["generation"])
    stage = str(pending["stage"])
    expected_reserved = (1000215183 - ((1000215183 - size * 2097152) // 2048 * 2048)) * 512
    if stage in TERMINAL_STAGES:
        ensure_linux_safe()
        write_state("create", stage, 100,
                    str(pending.get("failure_reason", "A instalação Windows requer recuperação."))[:300])
        return
    if stage == "maintenance":
        cleanup_maintenance()
        if STATUS.read_text().strip() != f"success:create:{size}:{generation}:{expected_reserved}":
            mark_terminal(pending, "recovery-required", "APX-MAINTENANCE-RESULT",
                          "offline-result", "o resultado offline de criação difere")
            return
        pending["stage"] = "preparing-installer"; write_json(PENDING, pending, 0o400)
        stage = "preparing-installer"
    if stage == "preparing-installer":
        write_state("create", "applying", 58, "A preparar o instalador Windows interno…")
        try:
            checked((PREPARE, str(size), generation))
        except Exception as error:
            mark_terminal(pending, "recovery-required", "APX-PREPARE-FAILED",
                          "preparing-installer", str(error))
            return
        ensure_linux_safe()
        pending["stage"] = "prepared"; pending["explicit_attempts"] = 0
        write_json(PENDING, pending, 0o400)
        write_state("create", "prepared", 72,
                    "Instalador pronto; o arranque Windows requer confirmação explícita.")
        return
    if stage == "prepared":
        ensure_linux_safe()
        write_state("create", "prepared", 72,
                    "Instalador pronto; o arranque Windows requer confirmação explícita.")
        return
    if stage == "boot-prepared":
        completed = windows_complete()
        if completed is None:
            ensure_linux_safe()
            write_state("create", "prepared", 90,
                        "Windows aplicado; o primeiro arranque requer confirmação explícita.")
            return
        pending["stage"] = "finalizing"; write_json(PENDING, pending, 0o400)
        stage = "finalizing"
    elif stage == "installing":
        completed = windows_complete()
        if completed is None:
            status = installer_status(generation)
            if status is not None and status.get("status") == "failed":
                code = status.get("error", "APX-WINPE-FAILED")
                step = status.get("step", "unknown")
                detail = status.get("detail", "unknown")
                command = status.get("command", "unknown")
                exit_code = status.get("exit_code", "unknown")
                diagnostic = status.get("diagnostic", "none")
                mark_terminal(pending, "failed", code, step,
                              f"o WinPE parou em segurança: {code} ({step}/{detail}); "
                              f"comando={command}; exit={exit_code}; diagnóstico={diagnostic}", status)
                return
            if status is not None and status.get("status") == "boot-prepared":
                pending["stage"] = "boot-prepared"; write_json(PENDING, pending, 0o400)
                ensure_linux_safe()
                write_state("create", "prepared", 90,
                            "Windows aplicado; o primeiro arranque requer confirmação explícita.")
                return
            mark_terminal(pending, "recovery-required", "APX-WINPE-NO-STATUS",
                          "installing", "o WinPE regressou sem um resultado terminal autenticado")
            return
        pending["stage"] = "finalizing"; write_json(PENDING, pending, 0o400)
        stage = "finalizing"
    elif stage != "finalizing":
        raise RuntimeError("a fase de criação Windows difere")
    completed = windows_complete()
    if completed is None:
        mark_terminal(pending, "recovery-required", "APX-FINALIZE-INCOMPLETE",
                      "finalizing", "a instalação deixou de cumprir o contrato de conclusão")
        return
    windows_entry, windows_partuuid, windows_bytes = completed
    set_linux_first(windows_entry); remove_setup_entries()
    _output, entries, _order = firmware(); linux = linux_entry(entries)
    record = {
        "schema": 2, "profile": "apx-native-environment-v2", "name": "windows",
        "display_name": "Windows", "description": f"Windows 11 em partição física · {size} GiB · desempenho nativo",
        "category": "system", "environment_kind": "native-boot", "system_kind": "windows-native",
        "system_label": "NATIVO", "release": "windows-11-native-v1", "state": "ready",
        "generation": generation, "requested_size_gib": size, "reserved_bytes": expected_reserved,
        "disk_id": "AC9FC0BD-2162-43A9-AAE6-3F654FF6F275", "disk_serial": "S4DYNX0R253702",
        "linux_boot_entry": linux, "windows_boot_entry": windows_entry, "boot_entry": "firmware-windows",
        "windows_partuuid": windows_partuuid, "windows_bytes": windows_bytes,
        "windows_esp_partuuid": "9625F250-9ACC-453A-AE63-0C863ADE440F",
    }
    write_json(METADATA, record, 0o400)
    STATUS.unlink(missing_ok=True); INSTALLER_MARKER.unlink(missing_ok=True)
    LEGACY_INSTALLER_MARKER.unlink(missing_ok=True)
    for marker in (Path("/boot/EFI/APX/native-windows/install-contract-v2.ini"), EFI_INSTALL_STATUS):
        marker.unlink(missing_ok=True)
    cleanup_maintenance()
    write_state("create", "complete", 100, "Windows nativo criado e pronto.")
    PENDING.unlink(missing_ok=True)
    checked(("/usr/bin/systemctl", "restart", "apx-environment-switch-v1.service"))


def main() -> int:
    if os.geteuid() != 0 or Path("/etc/hostname").read_text().strip() != "apx-host":
        raise RuntimeError("a identidade do Host difere")
    pending = trusted_json(PENDING, "apx-native-windows-pending-v1")
    if pending.get("schema") != 1 or pending.get("action") not in {"create", "delete"} \
            or pending.get("requested_size_gib") not in {80, 120, 160} \
            or GENERATION.fullmatch(str(pending.get("generation", ""))) is None:
        raise RuntimeError("a operação Windows pendente difere")
    allowed = ({"maintenance", "preparing-installer", "prepared", "installing",
                "boot-prepared", "failed", "recovery-required", "finalizing"}
               if pending["action"] == "create" else {"maintenance", "finalizing"})
    if pending.get("stage") not in allowed:
        raise RuntimeError("a fase da operação Windows pendente difere")
    if pending["action"] == "delete": finalize_delete(pending)
    else: finalize_create(pending)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as error:
        try:
            pending = trusted_json(PENDING, "apx-native-windows-pending-v1")
            if pending.get("action") == "create" and pending.get("stage") not in TERMINAL_STAGES:
                mark_terminal(pending, "recovery-required", "APX-FINALIZER-ERROR",
                              str(pending.get("stage", "unknown")), str(error))
            else:
                ensure_linux_safe()
                write_state(str(pending.get("action", "create")), "failed", 100, str(error)[:300])
        except Exception:
            pass
        print(f"APX native Windows finalization failed: {error}", file=__import__("sys").stderr)
        raise SystemExit(2)
