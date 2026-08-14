#!/usr/bin/env python3
"""Target-bound Host adapter for the owner's external APX model store."""

from __future__ import annotations

import json
import os
from pathlib import Path
import pwd
import stat
import subprocess
import sys


DISK = Path("/dev/disk/by-id/ata-Samsung_SSD_870_QVO_1TB_S5SVNF0R241427A")
PARTITION = Path(f"{DISK}-part1")
EXPECTED_SERIAL = "S5SVNF0R241427A"
EXPECTED_MODEL = "Samsung_SSD_870_QVO_1TB"
EXPECTED_SIZE = 1_000_204_886_016
EXPECTED_PARTUUID = "c8806268-9695-4d52-9136-6f278b95c2e4"
EXPECTED_LUKS_UUID = "f0ca74a0-90d1-408c-8f01-0668ce554a17"
EXPECTED_FILESYSTEM_UUID = "b94ab3ad-f41f-4eae-b663-78789ce3ba52"
MAPPER_NAME = "apx-model-store"
MAPPER = Path(f"/dev/mapper/{MAPPER_NAME}")
MOUNTPOINT = Path("/var/lib/apx/model-store")
MODEL_DIRECTORY = MOUNTPOINT / "ollama"
IDENTITY_FILE = MOUNTPOINT / ".apx-model-store-v1.json"


class ModelStoreError(RuntimeError):
    pass


def run(*arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        arguments,
        check=check,
        capture_output=True,
        text=True,
        env={"PATH": "/usr/bin", "LC_ALL": "C"},
    )


def property_for(device: Path, name: str) -> str:
    output = run("/usr/bin/udevadm", "info", "--query=property", f"--name={device}").stdout
    prefix = f"{name}="
    for line in output.splitlines():
        if line.startswith(prefix):
            return line[len(prefix):]
    raise ModelStoreError(f"missing device property {name}")


def blkid_value(device: Path, tag: str) -> str:
    return run("/usr/bin/blkid", "-s", tag, "-o", "value", str(device)).stdout.strip()


def mounted_source() -> str | None:
    result = run(
        "/usr/bin/findmnt", "-rn", "-o", "SOURCE", "--mountpoint", str(MOUNTPOINT),
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def mount_options() -> set[str]:
    result = run(
        "/usr/bin/findmnt", "-rn", "-o", "OPTIONS", "--mountpoint", str(MOUNTPOINT),
        check=False,
    )
    return set(result.stdout.strip().split(",")) if result.returncode == 0 else set()


def verify_physical_identity() -> None:
    if os.geteuid() != 0:
        raise ModelStoreError("the model-store adapter requires Host root")
    if not DISK.exists() or not PARTITION.exists():
        raise ModelStoreError("the exact external model SSD is absent")
    resolved_disk = Path(os.path.realpath(DISK))
    resolved_partition = Path(os.path.realpath(PARTITION))
    if resolved_partition != Path(f"{resolved_disk}1"):
        raise ModelStoreError("the stable partition link does not belong to the exact SSD")
    observed = {
        "serial": property_for(resolved_disk, "ID_SERIAL_SHORT"),
        "model": property_for(resolved_disk, "ID_MODEL"),
        "size": int(run("/usr/bin/blockdev", "--getsize64", str(resolved_disk)).stdout),
        "partuuid": blkid_value(resolved_partition, "PARTUUID"),
        "luks_uuid": blkid_value(resolved_partition, "UUID"),
        "type": blkid_value(resolved_partition, "TYPE"),
    }
    expected = {
        "serial": EXPECTED_SERIAL,
        "model": EXPECTED_MODEL,
        "size": EXPECTED_SIZE,
        "partuuid": EXPECTED_PARTUUID,
        "luks_uuid": EXPECTED_LUKS_UUID,
        "type": "crypto_LUKS",
    }
    if observed != expected:
        raise ModelStoreError("external model SSD identity differs from the admitted device")


def verify_filesystem() -> None:
    if blkid_value(MAPPER, "UUID") != EXPECTED_FILESYSTEM_UUID:
        raise ModelStoreError("unlocked model-store filesystem identity differs")
    if blkid_value(MAPPER, "TYPE") != "btrfs":
        raise ModelStoreError("unlocked model store is not Btrfs")


def activate() -> None:
    verify_physical_identity()
    if not MAPPER.exists():
        run(
            "/usr/lib/systemd/systemd-cryptsetup", "attach", MAPPER_NAME,
            str(PARTITION), "none", "tpm2-device=auto,headless=yes",
        )
    verify_filesystem()
    MOUNTPOINT.mkdir(mode=0o000, parents=True, exist_ok=True)
    os.chown(MOUNTPOINT, 0, 0)
    os.chmod(MOUNTPOINT, 0o000)
    source = mounted_source()
    if source is None:
        run(
            "/usr/bin/mount", "-t", "btrfs",
            "-o", "ro,nosuid,nodev,noexec,noatime,compress=zstd:3,ssd,discard=async",
            str(MAPPER), str(MOUNTPOINT),
        )
    elif os.path.realpath(source) != os.path.realpath(MAPPER):
        raise ModelStoreError("the private model-store path is occupied by another filesystem")
    verify_filesystem()
    if "ro" not in mount_options():
        raise ModelStoreError("model store is not mounted read-only")
    ollama = pwd.getpwnam("ollama")
    try:
        model_metadata = MODEL_DIRECTORY.stat()
    except OSError as error:
        raise ModelStoreError("the admitted model directory is unavailable") from error
    if not stat.S_ISDIR(model_metadata.st_mode) or (model_metadata.st_uid, model_metadata.st_gid) \
            != (ollama.pw_uid, ollama.pw_gid) or stat.S_IMODE(model_metadata.st_mode) != 0o750:
        raise ModelStoreError("the admitted model directory ownership or mode differs")
    identity = {
        "contract": "apx-host-model-store-v1",
        "filesystem_uuid": EXPECTED_FILESYSTEM_UUID,
        "luks_uuid": EXPECTED_LUKS_UUID,
        "model_directory": str(MODEL_DIRECTORY),
        "physical_model": EXPECTED_MODEL,
        "physical_serial": EXPECTED_SERIAL,
    }
    if IDENTITY_FILE.exists():
        try:
            existing = json.loads(IDENTITY_FILE.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ModelStoreError("the model-store identity record is unreadable") from error
        if existing != identity:
            raise ModelStoreError("the model-store identity record differs")
    else:
        raise ModelStoreError("the immutable model-store identity record is absent")


def deactivate() -> None:
    if mounted_source() is not None:
        os.sync()
        result = run("/usr/bin/umount", str(MOUNTPOINT), check=False)
        if result.returncode != 0:
            raise ModelStoreError("model store remains busy; preserving the mapped volume")
    if MAPPER.exists():
        run("/usr/lib/systemd/systemd-cryptsetup", "detach", MAPPER_NAME)
    MOUNTPOINT.mkdir(mode=0o000, parents=True, exist_ok=True)
    os.chown(MOUNTPOINT, 0, 0)
    os.chmod(MOUNTPOINT, 0o000)


def status() -> None:
    state = {
        "device_present": DISK.exists() and PARTITION.exists(),
        "mapped": MAPPER.exists(),
        "mounted": mounted_source() is not None,
        "read_only": "ro" in mount_options(),
        "model_directory": MODEL_DIRECTORY.is_dir() if mounted_source() is not None else False,
    }
    print(json.dumps(state, sort_keys=True))


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in {"activate", "deactivate", "status"}:
        raise ModelStoreError("usage: apx-model-store-v1.py activate|deactivate|status")
    {"activate": activate, "deactivate": deactivate, "status": status}[sys.argv[1]]()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ModelStoreError, KeyError, OSError, subprocess.CalledProcessError) as error:
        print(f"APX model store refused: {error}", file=sys.stderr)
        raise SystemExit(2)
