#!/usr/bin/env bash
set -Eeuo pipefail

readonly repository=/root/apx-host-development-mode-v1/apx
readonly generation=32bd4ffb-a7f1-465f-9761-edcd292d417c
readonly pending=/var/lib/apx/native-environments/windows-pending.json
readonly metadata=/var/lib/apx/native-environments/windows.json
readonly status=/boot/EFI/APX/recovery/windows-lifecycle-v1.status
readonly uki=/boot/EFI/APX/apx-native-windows-lifecycle-v1.efi
readonly entry=/boot/loader/entries/apx-native-windows-lifecycle-v1.conf
readonly backup_dir="/var/lib/apx/backups/$(date -u +%Y%m%dT%H%M%SZ)-native-windows-msr-probe-refusal-v1"

fail() { echo "APX native Windows refusal recovery rejected: $*" >&2; exit 1; }

[[ $EUID -eq 0 && $PWD == "$repository" ]] || fail "root or repository differs"
[[ $(</etc/hostname) == apx-host ]] || fail "Host identity differs"
[[ $(</sys/class/power_supply/ADP0/online) == 1 ]] || fail "AC adapter is required"
[[ $(</sys/class/power_supply/BAT0/capacity) -ge 40 ]] || fail "battery is below 40%"
[[ $(/usr/bin/blockdev --getsize64 /dev/nvme0n1p2) == 382186029056 ]] || fail "APX partition differs"
[[ $(/usr/bin/sfdisk --disk-id /dev/nvme0n1) == AC9FC0BD-2162-43A9-AAE6-3F654FF6F275 ]] || fail "GPT identity differs"
[[ $(/usr/bin/xargs </sys/block/nvme0n1/device/serial) == S4DYNX0R253702 ]] || fail "disk identity differs"
[[ $(</sys/class/block/nvme0n1p3/start) == 748556288 ]] || fail "Windows start differs"
[[ $(</sys/class/block/nvme0n1p6/start) == 981340160 ]] || fail "Windows ESP start differs"
[[ $(/usr/bin/blockdev --getsz /dev/nvme0n1p6) == 18874368 ]] || fail "Windows ESP size differs"
[[ $(/usr/bin/blkid -p -s PART_ENTRY_TYPE -o value /dev/nvme0n1p3) == e3c9e316-0b5c-4db8-817d-f92df00215ae ]] || fail "MSR type differs"
[[ $(/usr/bin/blkid -p -s PART_ENTRY_TYPE -o value /dev/nvme0n1p4) == ebd0a0a2-b9e5-4433-87c0-68b6b72699c7 ]] || fail "Windows type differs"
[[ $(/usr/bin/blkid -p -s PART_ENTRY_TYPE -o value /dev/nvme0n1p5) == de94bba4-06d1-4d40-a16a-bfd50179d6ac ]] || fail "Recovery type differs"
[[ $(/usr/bin/blkid -p -s PART_ENTRY_TYPE -o value /dev/nvme0n1p6) == c12a7328-f81f-11d2-ba4b-00a0c93ec93b ]] || fail "Windows ESP type differs"
[[ $(/usr/bin/blkid -s TYPE -o value /dev/nvme0n1p4) == ntfs ]] || fail "Windows filesystem differs"
[[ $(/usr/bin/blkid -s TYPE -o value /dev/nvme0n1p5) == ntfs ]] || fail "Recovery filesystem differs"
[[ $(/usr/bin/blkid -s TYPE -o value /dev/nvme0n1p6) == vfat ]] || fail "Windows ESP filesystem differs"
[[ $(/usr/bin/blkid -s PARTUUID -o value /dev/nvme0n1p6) == 309bebb6-5c32-4e21-9c92-6d758e51389d ]] || fail "Windows ESP identity differs"
[[ $(<"$status") == "failed:delete:120:$generation:msr-type" ]] || fail "failure status differs"
[[ -f $uki && ! -L $uki && -f $entry && ! -L $entry ]] || fail "maintenance artifacts differ"
! /usr/bin/efibootmgr | /usr/bin/grep -q '^BootNext:' || fail "BootNext is armed"

/usr/bin/python3 - "$pending" "$metadata" "$generation" <<'PY'
import json
from pathlib import Path
import stat
import sys

pending_path, metadata_path, generation = map(Path, sys.argv[1:])
for path in (pending_path, metadata_path):
    info = path.lstat()
    if path.is_symlink() or not path.is_file() or info.st_uid or info.st_gid or stat.S_IMODE(info.st_mode) != 0o400:
        raise SystemExit("untrusted lifecycle metadata")
pending = json.loads(pending_path.read_bytes())
metadata = json.loads(metadata_path.read_bytes())
if pending != {
    "action": "delete", "created_at": pending.get("created_at"), "generation": str(generation),
    "name": "windows", "profile": "apx-native-windows-pending-v1",
    "requested_size_gib": 120, "schema": 1, "stage": "maintenance",
} or type(pending["created_at"]) is not int:
    raise SystemExit("pending operation differs")
if (metadata.get("schema"), metadata.get("profile"), metadata.get("name"),
        metadata.get("generation"), metadata.get("state"), metadata.get("requested_size_gib")) != (
        2, "apx-native-environment-v2", "windows", str(generation), "ready", 120):
    raise SystemExit("Windows metadata differs")
PY

[[ ! -e $backup_dir ]] || fail "backup already exists"
/usr/bin/install -d -o root -g root -m 0700 "$backup_dir"
/usr/bin/cp --archive -- "$pending" "$backup_dir/windows-pending.json"
/usr/bin/cp --archive -- "$status" "$backup_dir/windows-lifecycle.status"
/usr/bin/cp --archive -- "$entry" "$backup_dir/maintenance-entry.conf"
/usr/bin/sfdisk --dump /dev/nvme0n1 >"$backup_dir/gpt.sfdisk"
/usr/bin/efibootmgr -v >"$backup_dir/efibootmgr.txt"
/usr/bin/sha256sum "$uki" >"$backup_dir/maintenance-uki.sha256"

/usr/bin/unlink "$pending"
/usr/bin/unlink "$status"
/usr/bin/unlink "$uki"
/usr/bin/unlink "$entry"
/usr/bin/systemctl reset-failed apx-native-windows-lifecycle-finalize-v1.service
/usr/bin/sync

[[ ! -e $pending && ! -e $status && ! -e $uki && ! -e $entry ]] || fail "failed artifacts remain"
for number in 3 4 5 6; do [[ -b /dev/nvme0n1p$number ]] || fail "Windows partition disappeared"; done
/usr/bin/chown -R root:root "$backup_dir"
/usr/bin/find "$backup_dir" -type f -exec chmod 0600 {} +
echo "APX native Windows safe refusal recovered; backup: $backup_dir"
