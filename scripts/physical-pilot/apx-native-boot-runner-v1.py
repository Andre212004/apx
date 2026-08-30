#!/usr/bin/env python3
"""Root-only, hardware-bound one-shot APX-to-native-Windows reboot."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import tempfile


METADATA = Path("/var/lib/apx/native-environments/windows.json")
DISK = Path("/dev/nvme0n1")
WINDOWS = Path("/dev/nvme0n1p3")
WINDOWS_ESP = Path("/dev/nvme0n1p1")
EXPECTED_DISK_SERIAL = "S4DYNX0R253702"
EXPECTED_DISK_ID = "AC9FC0BD-2162-43A9-AAE6-3F654FF6F275"
EXPECTED_ESP_BYTES = 1073741824
EXPECTED_RETURN_HASHES = {
    "ProgramData/APX/ReturnToHub/APX-ReturnToHub.ps1": "a63d776336ae7bbdd406a0bab924193e409cc0a03a38fc7b332a9ccee0c54f11",
    "ProgramData/APX/ReturnToHub/README.txt": "c03fbf0afa374c30c64adf5a22c2f876f80a3d0a288a2414b6091d3ad17206a8",
    "ProgramData/Microsoft/Windows/Start Menu/Programs/Startup/APX-ReturnToHub.vbs": "504a32302dbfc5590e6059dde1ec563e6e04371bfac6c8e352b20b10f044757f",
}


def run(arguments: tuple[str, ...]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(arguments, text=True, capture_output=True, check=False,
                          env={"PATH": "/usr/bin", "LC_ALL": "C"})


def checked(arguments: tuple[str, ...], message: str) -> str:
    result = run(arguments)
    if result.returncode:
        raise RuntimeError(message)
    return result.stdout.strip()


def metadata() -> dict[str, object]:
    info = METADATA.lstat()
    raw = METADATA.read_bytes()
    value = json.loads(raw)
    expected = {
        "profile": "apx-native-environment-v2",
        "schema": 2,
        "name": "windows",
        "environment_kind": "native-boot",
        "system_kind": "windows-native",
        "system_label": "NATIVO",
        "state": "ready",
        "disk_id": EXPECTED_DISK_ID,
        "disk_serial": EXPECTED_DISK_SERIAL,
        "windows_partuuid": "099C31D8-313A-4ABA-B0E0-2B59502C9674",
        "windows_esp_partuuid": "9625F250-9ACC-453A-AE63-0C863ADE440F",
    }
    if METADATA.is_symlink() or not METADATA.is_file() or info.st_uid != 0 or info.st_gid != 0 \
            or stat.S_IMODE(info.st_mode) != 0o400 or not raw or len(raw) > 4096 \
            or type(value) is not dict \
            or any(value.get(key) != wanted for key, wanted in expected.items()) \
            or type(value.get("display_name")) is not str \
            or not 1 <= len(value["display_name"]) <= 64 \
            or value["display_name"] != value["display_name"].strip() \
            or any(ord(character) < 32 for character in value["display_name"]) \
            or type(value.get("description")) is not str or len(value["description"]) > 120 \
            or value["description"] != value["description"].strip() \
            or any(ord(character) < 32 for character in value["description"]) \
            or value.get("requested_size_gib") not in {80, 120, 160} \
            or value.get("reserved_bytes") != (1000215183 - ((1000215183 - value["requested_size_gib"] * 2097152) // 2048 * 2048)) * 512 \
            or re.fullmatch(r"[0-9a-f]{8}-[0-9a-f-]{27}", str(value.get("generation", ""))) is None \
            or not re.fullmatch(r"[0-9A-F]{4}", str(value.get("linux_boot_entry", ""))) \
            or not re.fullmatch(r"[0-9A-F]{4}", str(value.get("windows_boot_entry", ""))) \
            or type(value.get("windows_bytes")) is not int or not 64 * 1024**3 <= value["windows_bytes"] <= 160 * 1024**3:
        raise RuntimeError("os metadados do Windows nativo diferem")
    return value


def block_value(device: Path, field: str) -> str:
    return checked(("/usr/bin/blkid", "-s", field, "-o", "value", str(device)),
                   f"a identidade de {device.name} não pôde ser lida").upper()


def block_size(device: Path) -> int:
    return int(checked(("/usr/bin/blockdev", "--getsize64", str(device)),
                       f"o tamanho de {device.name} não pôde ser lido"))


def firmware(value: dict[str, object]) -> tuple[str, str]:
    output = checked(("/usr/bin/efibootmgr", "-v"), "o catálogo UEFI não pôde ser validado")
    fields = {match.group(1): match.group(2) for match in
              re.finditer(r"^(BootCurrent|BootNext|BootOrder):\s*(\S.*)$", output, re.MULTILINE)}
    linux = str(value["linux_boot_entry"])
    windows = str(value["windows_boot_entry"])
    order = fields.get("BootOrder", "").split(",")
    if fields.get("BootCurrent") != linux or fields.get("BootNext") is not None \
            or not order or order[0] != linux or windows not in order:
        raise RuntimeError("o Linux não é o arranque principal ou já existe um arranque único")
    entry = next((line for line in output.splitlines()
                  if re.match(rf"^Boot{windows}\*?\s+Windows Boot Manager\s", line)), "")
    expected_partition = str(value["windows_esp_partuuid"]).lower()
    lowered = entry.lower()
    if f"hd(1,gpt,{expected_partition}," not in lowered \
            or "\\efi\\microsoft\\boot\\bootmgfw.efi" not in lowered:
        raise RuntimeError("a entrada UEFI do Windows difere")
    return linux, windows


def mounted_read_only(device: Path, filesystem: str):
    class Mount:
        def __enter__(self) -> Path:
            self.path = Path(tempfile.mkdtemp(prefix="apx-native-windows-", dir="/run"))
            result = run(("/usr/bin/mount", "-t", filesystem, "-o", "ro,nosuid,nodev,noexec",
                          str(device), str(self.path)))
            if result.returncode:
                self.path.rmdir()
                raise RuntimeError(f"{device.name} não pôde ser validada em modo de leitura")
            return self.path

        def __exit__(self, _type, _value, _traceback) -> None:
            result = run(("/usr/bin/umount", str(self.path)))
            if result.returncode:
                raise RuntimeError(f"{device.name} não pôde ser desmontada")
            self.path.rmdir()
    return Mount()


def validate_hardware_and_return(root: Path) -> None:
    for relative, expected in EXPECTED_RETURN_HASHES.items():
        path = root / relative
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 32768 \
                or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise RuntimeError("o helper de regresso ao APX difere")
    desktop_fallback = root / "Users/Public/Desktop/REGRESSAR AO APX.cmd"
    if desktop_fallback.exists() or desktop_fallback.is_symlink():
        raise RuntimeError("o Ambiente de Trabalho Windows ainda contém o atalho APX antigo")
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
        raise RuntimeError("o controlador Wi-Fi não corresponde ao Lenovo 82JU")


def validate_windows(value: dict[str, object]) -> None:
    serial = Path("/sys/block/nvme0n1/device/serial").read_text().strip()
    disk_id = checked(("/usr/bin/sfdisk", "--disk-id", str(DISK)),
                      "a identidade GPT não pôde ser lida")
    if serial != EXPECTED_DISK_SERIAL or disk_id != EXPECTED_DISK_ID:
        raise RuntimeError("o disco físico difere")
    if block_value(WINDOWS, "PARTUUID") != value["windows_partuuid"] \
            or block_size(WINDOWS) != value["windows_bytes"] or block_value(WINDOWS, "TYPE") != "NTFS":
        raise RuntimeError("a partição principal do Windows difere")
    if block_value(WINDOWS_ESP, "PARTUUID") != value["windows_esp_partuuid"] \
            or block_size(WINDOWS_ESP) != EXPECTED_ESP_BYTES or block_value(WINDOWS_ESP, "TYPE") != "VFAT":
        raise RuntimeError("a partição EFI do Windows difere")
    if checked(("/usr/bin/findmnt", "-rn", "-o", "SOURCE", "/boot"),
               "a APX_EFI montada não pôde ser validada") != str(WINDOWS_ESP):
        raise RuntimeError("a APX_EFI montada difere")
    root = Path("/boot")
    manager = root / "EFI/Microsoft/Boot/bootmgfw.efi"
    bcd = root / "EFI/Microsoft/Boot/BCD"
    linux_manager = root / "EFI/systemd/systemd-bootx64.efi"
    if manager.is_symlink() or not manager.is_file() or not 64 * 1024 <= manager.stat().st_size <= 8 * 1024 * 1024 \
            or bcd.is_symlink() or not bcd.is_file() or not 16 * 1024 <= bcd.stat().st_size <= 1024 * 1024 \
            or linux_manager.is_symlink() or not linux_manager.is_file():
        raise RuntimeError("o Windows Boot Manager ou o Linux Boot Manager não é confiável")
    signature = checked(("/usr/bin/sbverify", "--list", str(manager)),
                        "a assinatura do Windows Boot Manager não pôde ser validada")
    if "image signature certificates" not in signature or "Microsoft" not in signature:
        raise RuntimeError("o Windows Boot Manager não tem uma assinatura Microsoft válida")
    with mounted_read_only(WINDOWS, "ntfs3") as root:
        loader = root / "Windows/System32/winload.efi"
        users = root / "Users"
        profiles = {child.name.lower() for child in users.iterdir() if child.is_dir()} if users.is_dir() else set()
        if loader.is_symlink() or not loader.is_file() or not 64 * 1024 <= loader.stat().st_size <= 8 * 1024 * 1024 \
                or not profiles.difference({"default", "default user", "public", "defaultuser0", "all users"}):
            raise RuntimeError("a instalação ou o perfil Windows ainda não estão concluídos")
        validate_hardware_and_return(root)


def validate_target() -> tuple[str, str]:
    if Path("/etc/hostname").read_text().strip() != "apx-host" \
            or Path("/sys/class/dmi/id/product_name").read_text().strip() != "82JU":
        raise RuntimeError("a identidade do computador difere")
    if checked(("/usr/bin/bootctl", "status", "--no-pager"),
               "o estado Secure Boot não pôde ser lido").find("Secure Boot: enabled (user)") < 0:
        raise RuntimeError("Secure Boot não está ativo")
    value = metadata()
    entries = firmware(value)
    validate_windows(value)
    return entries


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", choices=("windows",), required=True)
    parser.add_argument("--validate-only", action="store_true")
    arguments = parser.parse_args()
    if os.geteuid() != 0:
        raise RuntimeError("o executor de arranque nativo exige root")
    _linux, windows = validate_target()
    if arguments.validate_only:
        print("APX native Windows boot validation passed")
        return 0
    selected = run(("/usr/bin/efibootmgr", "-n", windows))
    if selected.returncode:
        raise RuntimeError("o arranque único do Windows não pôde ser definido")
    armed = run(("/usr/bin/efibootmgr",))
    if armed.returncode or f"BootNext: {windows}" not in armed.stdout:
        run(("/usr/bin/efibootmgr", "-N"))
        raise RuntimeError("o arranque único do Windows não ficou confirmado")
    payload = ("\033[2J\033[H\033[?25l\n\n\n\n"
               "                  APX ENVIRONMENTS\n\n"
               "                  A ARRANCAR O WINDOWS NATIVO\n\n"
               "                  [######################--------]  74%\n").encode()
    try:
        descriptor = os.open("/dev/tty1", os.O_WRONLY | os.O_NOCTTY)
        try:
            os.write(descriptor, payload)
        finally:
            os.close(descriptor)
        reboot = run(("/usr/bin/systemctl", "--no-block", "reboot"))
    except Exception:
        run(("/usr/bin/efibootmgr", "-N"))
        raise
    if reboot.returncode:
        run(("/usr/bin/efibootmgr", "-N"))
        raise RuntimeError("o reinício para o Windows foi recusado")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as error:
        print(f"APX native boot failed: {error}", file=__import__("sys").stderr)
        raise SystemExit(2)
