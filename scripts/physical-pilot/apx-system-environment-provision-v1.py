#!/usr/bin/env python3
"""Provision one APX graphical Environment as a self-contained system guest."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import zipfile


ENVIRONMENTS = Path("/var/lib/apx/environments")
TEMPLATE = Path("/usr/lib/apx/system-environment-template-v2")
ARTIFACTS = Path("/var/lib/apx/package-artifacts/system-images-v1")
LOOKING_GLASS = Path("/var/lib/apx/package-artifacts/looking-glass-b7-799")
NAME = re.compile(r"[a-z](?:[a-z0-9]|-(?=[a-z0-9])){0,26}")


def run(arguments: tuple[str, ...]) -> None:
    result = subprocess.run(arguments, text=True, capture_output=True, check=False,
                            env={"PATH": "/usr/bin:/usr/local/bin", "LC_ALL": "C"})
    if result.returncode:
        raise RuntimeError((result.stderr.strip() or result.stdout.strip() or "comando falhou")[-1200:])


def install(source: Path, destination: Path, mode: int) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.{os.getpid()}.tmp")
    shutil.copyfile(source, temporary)
    os.chmod(temporary, mode)
    os.chown(temporary, 1000, 1000)
    os.replace(temporary, destination)


def root_marker(path: Path, value: bytes) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o400)
    try:
        os.write(descriptor, value)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def user_directory(path: Path, mode: int = 0o700) -> None:
    """Create an Environment-home directory that uid 1000 can traverse.

    The physical provisioner runs as root with a restrictive umask.  Relying
    on ``mkdir(parents=True)`` therefore created new intermediate directories
    such as ``.config/apx`` as root:root 0700 even though the final profile was
    owned by the Environment user.
    """
    path.mkdir(parents=True, exist_ok=True)
    os.chown(path, 1000, 1000)
    os.chmod(path, mode)


def provision(name: str, system_kind: str) -> None:
    environment = ENVIRONMENTS / name
    root, home = environment / "root", environment / "home/apx"
    registration = json.loads((environment / "registration.json").read_text())
    if (registration.get("name"), registration.get("role"), registration.get("state")) != (
            name, "graphical-base", "stopped"):
        raise RuntimeError("o Environment publicado não corresponde ao provisionamento")
    if system_kind not in {"windows11", "ubuntu"}:
        raise RuntimeError("sistema APX não suportado")

    # The guest engine belongs to this Environment. Packages are installed in
    # its immutable-looking root, never on the Host desktop or in the HUB.
    # Upgrade the private snapshot as one transaction before adding QEMU. This
    # avoids unsupported partial upgrades when the admitted base predates the
    # current repository, while keeping all packages inside the Environment.
    run(("/usr/bin/pacman", "--root", str(root), "--dbpath", str(root / "var/lib/pacman"),
         "--cachedir", "/var/cache/pacman/pkg", "--disable-sandbox",
         "-Syu", "--needed", "--noconfirm",
         "qemu-desktop", "edk2-ovmf", "swtpm", "rofi"))

    for directory in (home / ".config", home / ".config/apx", home / ".config/hypr",
                      home / ".local", home / ".local/bin"):
        user_directory(directory)
    install(TEMPLATE / "hypr/hyprland.lua", home / ".config/hypr/hyprland.lua", 0o600)
    install(TEMPLATE / "local/bin/apx-vm-runtime-v2",
            home / ".local/bin/apx-system-vm", 0o755)
    install(TEMPLATE / f"profiles/{system_kind}.json",
            home / ".config/apx/system-vm-v2.json", 0o600)
    # There is one implementation and one compositor entrypoint. The runtime
    # owns QEMU/Looking Glass directly; no autostart file, QMP helper, Host
    # readiness marker or guest-specific launcher is installed.
    if system_kind == "windows11":
        install(LOOKING_GLASS / "looking-glass-client", home / ".local/bin/looking-glass-client", 0o755)
        tools = home / "APXTools"; user_directory(tools, 0o755)
        for archive_name, executable in (("idd.zip", "looking-glass-idd-setup.exe"),
                                         ("host.zip", "looking-glass-host-setup.exe")):
            with zipfile.ZipFile(LOOKING_GLASS / archive_name) as archive:
                payload = archive.read(executable)
            target = tools / executable
            target.write_bytes(payload); os.chown(target, 1000, 1000); os.chmod(target, 0o500)
        install(TEMPLATE / "APXTools/LEIA-ME.txt", tools / "LEIA-ME.txt", 0o444)
        install(TEMPLATE / "APXTools/ATIVAR-ACELERACAO.cmd",
                tools / "ATIVAR-ACELERACAO.cmd", 0o444)
        install(TEMPLATE / "APXTools/APX-CONFIGURAR-120HZ.ps1",
                tools / "APX-CONFIGURAR-120HZ.ps1", 0o444)

    image_name = "Windows11.iso" if system_kind == "windows11" else "Ubuntu.iso"
    source_image = ARTIFACTS / ("windows11.iso" if system_kind == "windows11" else "ubuntu.iso")
    if not source_image.is_file() or source_image.is_symlink():
        raise RuntimeError(f"a imagem verificada de {system_kind} não está disponível")
    manifest = json.loads((ARTIFACTS / "manifest.json").read_text())
    expected = manifest["images"][source_image.name]["sha256"]
    with source_image.open("rb") as stream:
        observed = hashlib.file_digest(stream, "sha256").hexdigest()
    if observed != expected:
        raise RuntimeError(f"a imagem verificada de {system_kind} foi alterada")
    vm_dir = home / ("VMs/Windows11" if system_kind == "windows11" else "VMs/Ubuntu")
    user_directory(vm_dir.parent)
    user_directory(vm_dir)
    run(("/usr/bin/cp", "--reflink=auto", "--sparse=always", str(source_image), str(vm_dir / image_name)))
    os.chown(vm_dir / image_name, 1000, 1000); os.chmod(vm_dir / image_name, 0o400)
    # The verified ISO is reflinked first. Future raw guest-disk files inherit
    # NOCOW from this directory, avoiding qcow2-on-Btrfs double copy-on-write
    # without weakening the rest of the Environment home or its purge scope.
    run(("/usr/bin/chattr", "+C", str(vm_dir)))

    root_marker(environment / "kvm-v1", b"apx-kvm-v1\n")
    root_marker(environment / "virtual-machine-v1", b"apx-virtual-machine-v1\n")
    vfio = (TEMPLATE / "vfio-pci-v1.json").read_bytes()
    root_marker(environment / "vfio-pci-v1.json", vfio)
    metadata = json.dumps({"schema": 1, "profile": "apx-system-environment-v1",
                           "system_kind": system_kind}, sort_keys=True,
                          separators=(",", ":")).encode() + b"\n"
    root_marker(environment / "system-environment-v1.json", metadata)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--environment", required=True)
    parser.add_argument("--system", required=True, choices=("windows11", "ubuntu"))
    arguments = parser.parse_args()
    if NAME.fullmatch(arguments.environment) is None or arguments.environment == "hub":
        parser.error("invalid Environment")
    provision(arguments.environment, arguments.system)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
