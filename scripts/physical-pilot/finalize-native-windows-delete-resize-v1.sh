#!/usr/bin/env bash
set -Eeuo pipefail

readonly repository=/root/apx-host-development-mode-v1/apx
readonly generation=32bd4ffb-a7f1-465f-9761-edcd292d417c
readonly source_file="$repository/scripts/physical-pilot/apx-native-windows-lifecycle-finalize-v1.py"
readonly target_file=/usr/lib/apx/apx-native-windows-lifecycle-finalize-v1.py
readonly pending=/var/lib/apx/native-environments/windows-pending.json
readonly metadata=/var/lib/apx/native-environments/windows.json
readonly legacy=/var/lib/apx/native-environments/windows-storage-v1.json
readonly status=/boot/EFI/APX/recovery/windows-lifecycle-v1.status
readonly uki=/boot/EFI/APX/apx-native-windows-lifecycle-v1.efi
readonly entry=/boot/loader/entries/apx-native-windows-lifecycle-v1.conf
readonly state=/run/apx/environment-management-v1.json
readonly backup_dir="/var/lib/apx/backups/$(date -u +%Y%m%dT%H%M%SZ)-native-windows-delete-finalize-v1"

fail() { echo "APX native Windows delete finalization refused: $*" >&2; exit 1; }

[[ $EUID -eq 0 && $PWD == "$repository" ]] || fail "root or repository differs"
[[ $(</etc/hostname) == apx-host ]] || fail "Host identity differs"
[[ -f $source_file && ! -L $source_file && -f $target_file && ! -L $target_file ]] || fail "finalizer differs"
[[ $(/usr/bin/blockdev --getsize64 /dev/nvme0n1p2) == 511035383296 ]] || fail "APX partition is not full-sized"
[[ $(/usr/bin/blockdev --getsize64 /dev/mapper/cryptroot) == 511018606080 ]] || fail "dm-crypt is not full-sized"
for number in 3 4 5 6; do [[ ! -e /dev/nvme0n1p$number ]] || fail "Windows partition p$number still exists"; done
[[ $(<"$status") == "success:delete:120:$generation:128849354240" ]] || fail "offline success marker differs"
[[ -f $pending && ! -L $pending && -f $metadata && ! -L $metadata && -f $legacy && ! -L $legacy ]] || fail "lifecycle metadata differs"
[[ -f $uki && ! -L $uki && -f $entry && ! -L $entry ]] || fail "maintenance artifacts differ"
readonly btrfs_size_before=$(/usr/bin/btrfs filesystem usage -b / | /usr/bin/awk '$1 == "Device" && $2 == "size:" {print $3; exit}')
readonly btrfs_slack_before=$(/usr/bin/btrfs filesystem usage -b / | /usr/bin/awk '$1 == "Device" && $2 == "slack:" {print $3; exit}')
[[ $btrfs_size_before:$btrfs_slack_before == 382169251840:128849354240 \
        || $btrfs_size_before:$btrfs_slack_before == 511018602496:3584 ]] \
    || fail "Btrfs pre-finalize geometry differs"
! /usr/bin/efibootmgr | /usr/bin/grep -q '^BootNext:' || fail "BootNext is armed"

/usr/bin/python3 - "$pending" "$metadata" "$generation" <<'PY'
import json
from pathlib import Path
import sys

pending = json.loads(Path(sys.argv[1]).read_bytes())
metadata = json.loads(Path(sys.argv[2]).read_bytes())
generation = sys.argv[3]
if (pending.get("action"), pending.get("generation"), pending.get("requested_size_gib"), pending.get("stage")) != (
        "delete", generation, 120, "maintenance"):
    raise SystemExit("pending operation differs")
if (metadata.get("profile"), metadata.get("generation"), metadata.get("requested_size_gib"), metadata.get("state")) != (
        "apx-native-environment-v2", generation, 120, "ready"):
    raise SystemExit("Windows metadata differs")
PY

/usr/bin/python3 -m py_compile "$source_file"
/usr/bin/python3 -m unittest tests.test_apx_native_windows_storage_v1 >/dev/null
[[ ! -e $backup_dir ]] || fail "backup already exists"
/usr/bin/install -d -o root -g root -m 0700 "$backup_dir"
/usr/bin/cp --archive -- "$target_file" "$backup_dir/finalizer.previous"
/usr/bin/cp --archive -- "$pending" "$backup_dir/windows-pending.json"
/usr/bin/cp --archive -- "$metadata" "$backup_dir/windows.json"
/usr/bin/cp --archive -- "$legacy" "$backup_dir/windows-storage-v1.json"
/usr/bin/cp --archive -- "$status" "$backup_dir/windows-lifecycle.status"
/usr/bin/cp --archive -- "$entry" "$backup_dir/maintenance-entry.conf"
/usr/bin/cp --archive -- "$state" "$backup_dir/management-state.json"
/usr/bin/sfdisk --dump /dev/nvme0n1 >"$backup_dir/gpt-before-finalize.sfdisk"
/usr/bin/btrfs filesystem usage -b / >"$backup_dir/btrfs-before-finalize.txt"
/usr/bin/efibootmgr -v >"$backup_dir/efibootmgr-before-finalize.txt"
/usr/bin/sha256sum "$uki" >"$backup_dir/maintenance-uki.sha256"

rollback_install() {
    set +e
    /usr/bin/cp --archive -- "$backup_dir/finalizer.previous" "$target_file"
}
trap rollback_install ERR
/usr/bin/install -o root -g root -m 0755 "$source_file" "$target_file"
/usr/bin/cmp -- "$source_file" "$target_file"
trap - ERR

/usr/bin/systemctl reset-failed apx-native-windows-lifecycle-finalize-v1.service
/usr/bin/systemctl start apx-native-windows-lifecycle-finalize-v1.service
[[ $(/usr/bin/systemctl show -P Result apx-native-windows-lifecycle-finalize-v1.service) == success ]] || fail "finalizer service did not succeed"
[[ $(/usr/bin/systemctl show -P ExecMainStatus apx-native-windows-lifecycle-finalize-v1.service) == 0 ]] || fail "finalizer exit status differs"

for path in "$pending" "$metadata" "$legacy" "$status" "$uki" "$entry"; do [[ ! -e $path ]] || fail "finalized artifact remains: $path"; done
[[ $(/usr/bin/btrfs filesystem usage -b / | /usr/bin/awk '$1 == "Device" && $2 == "size:" {print $3; exit}') == 511018602496 ]] || fail "Btrfs did not regain the aligned disk"
[[ $(/usr/bin/btrfs filesystem usage -b / | /usr/bin/awk '$1 == "Device" && $2 == "slack:" {print $3; exit}') == 3584 ]] || fail "Btrfs alignment slack differs"
for number in 3 4 5 6; do [[ ! -e /dev/nvme0n1p$number ]] || fail "Windows partition returned"; done
! /usr/bin/efibootmgr | /usr/bin/grep -Eq '^Boot[0-9A-F]{4}\*? (Windows Boot Manager|APX Windows Setup)' || fail "Windows firmware entry remains"
! /usr/bin/efibootmgr | /usr/bin/grep -q '^BootNext:' || fail "BootNext was armed"
/usr/bin/python3 - "$state" <<'PY'
import json
from pathlib import Path
import sys

state = json.loads(Path(sys.argv[1]).read_bytes())
if (state.get("action"), state.get("target"), state.get("phase"), state.get("progress")) != (
        "native-delete", "windows", "complete", 100):
    raise SystemExit("completion state differs")
PY

/usr/bin/chown -R root:root "$backup_dir"
/usr/bin/find "$backup_dir" -type f -exec chmod 0600 {} +
echo "APX native Windows deletion finalized; backup: $backup_dir"
