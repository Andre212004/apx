#!/usr/bin/bash
set -euo pipefail

readonly repository=/root/apx-host-development-mode-v1/apx
readonly disk=/dev/nvme0n1
readonly linux_esp=/dev/nvme0n1p1
readonly windows_partition=/dev/nvme0n1p3
readonly linux_esp_partuuid=9625F250-9ACC-453A-AE63-0C863ADE440F
readonly windows_partuuid=099C31D8-313A-4ABA-B0E0-2B59502C9674
readonly windows_size=162135015424
readonly source_dir="$repository/config/native-windows-return-v1"
mount_dir=
backup=
program_target=
startup_target=
desktop_target=
stage=0

fail() { /usr/bin/printf 'APX Windows return staging refused: %s\n' "$1" >&2; exit 2; }
[[ $(/usr/bin/id -u) == 0 ]] || fail "root is required"
[[ $PWD == "$repository" ]] || fail "repository differs"
[[ $(< /etc/hostname) == apx-host ]] || fail "hostname differs"
[[ $(< /sys/class/dmi/id/product_name) == 82JU ]] || fail "Lenovo identity differs"
/usr/bin/grep -Fxq 'profile=apx-physical-headless-pilot-v1' /etc/apx-physical-pilot || fail "pilot marker differs"
[[ $(/usr/bin/xargs < /sys/block/nvme0n1/device/serial) == S4DYNX0R253702 ]] || fail "disk serial differs"
[[ $(/usr/bin/sfdisk --disk-id "$disk") == AC9FC0BD-2162-43A9-AAE6-3F654FF6F275 ]] || fail "GPT identity differs"
[[ $(/usr/bin/blkid -s PARTUUID -o value "$linux_esp" | /usr/bin/tr '[:lower:]' '[:upper:]') == "$linux_esp_partuuid" ]] || fail "Linux ESP PARTUUID differs"
[[ $(/usr/bin/blkid -s LABEL -o value "$linux_esp") == APX_EFI ]] || fail "Linux ESP label differs"
[[ $(/usr/bin/blkid -s TYPE -o value "$linux_esp") == vfat ]] || fail "Linux ESP filesystem differs"
[[ $(/usr/bin/blkid -s PARTUUID -o value "$windows_partition" | /usr/bin/tr '[:lower:]' '[:upper:]') == "$windows_partuuid" ]] || fail "Windows PARTUUID differs"
[[ $(/usr/bin/blockdev --getsize64 "$windows_partition") == "$windows_size" ]] || fail "Windows partition size differs"
[[ $(/usr/bin/blkid -s LABEL -o value "$windows_partition") == APXWINTARGET ]] || fail "Windows filesystem label differs"
[[ $(/usr/bin/blkid -s TYPE -o value "$windows_partition") == ntfs ]] || fail "Windows filesystem differs"
[[ $(/usr/bin/lsblk -ndo PARTLABEL "$windows_partition") == APX_WINDOWS_TARGET ]] || fail "Windows GPT label differs"
! /usr/bin/findmnt "$windows_partition" >/dev/null || fail "Windows partition is already mounted"
/usr/bin/python3 - /var/lib/apx/native-environments/windows.json <<'PY' || fail "Windows metadata differs"
import json, sys
with open(sys.argv[1], encoding="utf-8") as stream:
    value = json.load(stream)
assert value == {
    "boot_entry": "firmware-windows", "category": "system",
    "description": "Windows 11 · 160 GiB",
    "disk_id": "AC9FC0BD-2162-43A9-AAE6-3F654FF6F275",
    "disk_serial": "S4DYNX0R253702", "display_name": "Windows",
    "environment_kind": "native-boot",
    "generation": "1c5b5631-fb0e-4384-bf6f-b23eb1798f70",
    "linux_boot_entry": "0005", "name": "windows",
    "profile": "apx-native-environment-v2", "release": "windows-11-native-v1",
    "requested_size_gib": 160, "reserved_bytes": 171799027200, "schema": 2,
    "state": "ready", "system_kind": "windows-native", "system_label": "NATIVO",
    "windows_boot_entry": "0006", "windows_bytes": 162135015424,
    "windows_esp_partuuid": "9625F250-9ACC-453A-AE63-0C863ADE440F",
    "windows_partuuid": "099C31D8-313A-4ABA-B0E0-2B59502C9674",
}
PY
firmware=$(/usr/bin/efibootmgr)
[[ $firmware == *$'BootCurrent: 0005\n'* && $firmware == *$'BootOrder: 0005,'* \
        && $firmware != *'BootNext:'* ]] || fail "firmware state differs"
/usr/bin/ntfsfix -n "$windows_partition" >/dev/null || fail "Windows NTFS is not clean"
ntfs_report=$(/usr/bin/ntfsinfo -m "$windows_partition" 2>&1) \
    || fail "Windows NTFS is dirty or scheduled for check"
[[ $ntfs_report != *'unclean file system'* && $ntfs_report != *'Restart state: DIRTY'* ]] \
    || fail "Windows NTFS journal is dirty"
/usr/lib/apx/apx-native-boot-runner-v1.py --target windows --validate-only >/dev/null \
    || fail "native boot validation differs"
for source in APX-ReturnToHub.ps1 APX-ReturnToHub.vbs APX-ProvisionHardware.cmd README.txt; do
    [[ -f $source_dir/$source && ! -L $source_dir/$source ]] || fail "source differs: $source"
    [[ $(/usr/bin/stat -c %s "$source_dir/$source") -le 32768 ]] || fail "source is oversized: $source"
done
/usr/bin/python3 -m unittest discover -s tests >/dev/null || fail "repository tests failed"
/usr/bin/bash -n "$0" || fail "staging script does not parse"

backup=$(/usr/bin/mktemp -d /var/lib/apx/backups/20260831-native-windows-return-v2.XXXXXX)
/usr/bin/sha256sum "$source_dir"/* >"$backup/source.sha256"
mount_dir=$(/usr/bin/mktemp -d /run/apx-native-windows-return-v2.XXXXXX)
program_target="$mount_dir/ProgramData/APX/ReturnToHub"
startup_target="$mount_dir/ProgramData/Microsoft/Windows/Start Menu/Programs/Startup/APX-ReturnToHub.vbs"
desktop_target="$mount_dir/Users/Public/Desktop/REGRESSAR AO APX.cmd"
cleanup() {
    if [[ -n $mount_dir ]] && /usr/bin/mountpoint -q "$mount_dir"; then
        /usr/bin/umount "$mount_dir" || true
    fi
    [[ -z $mount_dir ]] || /usr/bin/rmdir "$mount_dir" 2>/dev/null || true
}
rollback() {
    trap - ERR
    if (( stage >= 2 )); then
        if ! /usr/bin/mountpoint -q "$mount_dir"; then
            /usr/bin/mount -t ntfs3 -o rw,nosuid,nodev,noexec "$windows_partition" "$mount_dir" || true
        elif /usr/bin/findmnt -no OPTIONS "$mount_dir" | /usr/bin/grep -qw ro; then
            /usr/bin/mount -o remount,rw "$mount_dir" || true
        fi
        /usr/bin/install -m 0644 -- "$backup/APX-ReturnToHub.ps1" "$program_target/APX-ReturnToHub.ps1" || true
        /usr/bin/install -m 0644 -- "$backup/README.txt" "$program_target/README.txt" || true
        /usr/bin/install -m 0644 -- "$backup/APX-ReturnToHub.vbs" "$startup_target" || true
        /usr/bin/install -m 0644 -- "$backup/REGRESSAR AO APX.cmd" "$desktop_target" || true
        if [[ -f $backup/APX-ProvisionHardware.cmd ]]; then
            /usr/bin/install -m 0644 -- "$backup/APX-ProvisionHardware.cmd" "$program_target/APX-ProvisionHardware.cmd" || true
        else
            /usr/bin/rm -f -- "$program_target/APX-ProvisionHardware.cmd" || true
        fi
        /usr/bin/sync || true
    fi
    cleanup
    fail "installation failed; original helper restored from $backup"
}
trap cleanup EXIT
trap rollback ERR

/usr/bin/mount -t ntfs3 -o rw,nosuid,nodev,noexec "$windows_partition" "$mount_dir"
stage=1
[[ -f $mount_dir/Windows/System32/winload.efi && -d $mount_dir/Users/andre ]] || fail "completed Windows installation differs"
for target in "$program_target/APX-ReturnToHub.ps1" "$program_target/README.txt" "$startup_target" "$desktop_target"; do
    [[ -f $target && ! -L $target ]] || fail "the existing APX return target differs"
done
/usr/bin/cp -a -- "$program_target/APX-ReturnToHub.ps1" "$backup/APX-ReturnToHub.ps1"
/usr/bin/cp -a -- "$program_target/README.txt" "$backup/README.txt"
/usr/bin/cp -a -- "$startup_target" "$backup/APX-ReturnToHub.vbs"
/usr/bin/cp -a -- "$desktop_target" "$backup/REGRESSAR AO APX.cmd"
[[ ! -e $program_target/APX-ProvisionHardware.cmd ]] \
    || /usr/bin/cp -a -- "$program_target/APX-ProvisionHardware.cmd" "$backup/APX-ProvisionHardware.cmd"
stage=2
/usr/bin/install -m 0644 -- "$source_dir/APX-ReturnToHub.ps1" "$program_target/APX-ReturnToHub.ps1"
/usr/bin/install -m 0644 -- "$source_dir/README.txt" "$program_target/README.txt"
/usr/bin/install -m 0644 -- "$source_dir/APX-ReturnToHub.vbs" "$startup_target"
/usr/bin/install -m 0644 -- "$source_dir/APX-ProvisionHardware.cmd" "$program_target/APX-ProvisionHardware.cmd"
/usr/bin/rm -f -- "$desktop_target"
/usr/bin/sync
/usr/bin/umount "$mount_dir"
/usr/bin/mount -t ntfs3 -o ro,nosuid,nodev,noexec "$windows_partition" "$mount_dir"
/usr/bin/cmp -s -- "$source_dir/APX-ReturnToHub.ps1" "$program_target/APX-ReturnToHub.ps1"
/usr/bin/cmp -s -- "$source_dir/README.txt" "$program_target/README.txt"
/usr/bin/cmp -s -- "$source_dir/APX-ReturnToHub.vbs" "$startup_target"
/usr/bin/cmp -s -- "$source_dir/APX-ProvisionHardware.cmd" "$program_target/APX-ProvisionHardware.cmd"
[[ ! -e $desktop_target && ! -L $desktop_target ]]
/usr/bin/sha256sum "$program_target/APX-ReturnToHub.ps1" "$program_target/README.txt" \
    "$program_target/APX-ProvisionHardware.cmd" "$startup_target" >"$backup/installed.sha256"
/usr/bin/umount "$mount_dir"
/usr/bin/chmod 0600 "$backup"/*
/usr/lib/apx/apx-native-boot-runner-v1.py --target windows --validate-only >/dev/null
[[ $(/usr/bin/efibootmgr) != *'BootNext:'* ]]
stage=3
trap - ERR
/usr/bin/rmdir "$mount_dir"
mount_dir=
/usr/bin/printf 'APX Windows return updated and verified. Backup: %s\n' "$backup"
