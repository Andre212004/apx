#!/usr/bin/bash
set -euo pipefail

readonly repository=/root/apx-host-development-mode-v1/apx
readonly windows_partition=/dev/nvme0n1p4
readonly windows_partuuid=099C31D8-313A-4ABA-B0E0-2B59502C9674
readonly windows_size=118261547008
readonly source_dir="$repository/config/native-windows-return-v1"
readonly mount_dir=/run/apx-native-windows-return-v1
readonly backup=/var/lib/apx/backups/20260825-native-windows-return-v2
readonly program_target="$mount_dir/ProgramData/APX/ReturnToHub"
readonly startup_target="$mount_dir/ProgramData/Microsoft/Windows/Start Menu/Programs/Startup/APX-ReturnToHub.vbs"
readonly desktop_target="$mount_dir/Users/Public/Desktop/REGRESSAR AO APX.cmd"
stage=0

fail() { /usr/bin/printf 'APX Windows return staging refused: %s\n' "$1" >&2; exit 2; }
[[ $(/usr/bin/id -u) == 0 ]] || fail "root is required"
[[ $PWD == "$repository" ]] || fail "repository differs"
[[ $(< /etc/hostname) == apx-host ]] || fail "hostname differs"
[[ $(< /sys/class/dmi/id/product_name) == 82JU ]] || fail "Lenovo identity differs"
/usr/bin/grep -Fxq 'profile=apx-physical-headless-pilot-v1' /etc/apx-physical-pilot || fail "pilot marker differs"
[[ $(/usr/bin/xargs < /sys/block/nvme0n1/device/serial) == S4DYNX0R253702 ]] || fail "disk serial differs"
[[ $(/usr/bin/sfdisk --disk-id /dev/nvme0n1) == AC9FC0BD-2162-43A9-AAE6-3F654FF6F275 ]] || fail "GPT identity differs"
[[ $(/usr/bin/blkid -s PARTUUID -o value "$windows_partition" | /usr/bin/tr '[:lower:]' '[:upper:]') == "$windows_partuuid" ]] || fail "Windows PARTUUID differs"
[[ $(/usr/bin/blockdev --getsize64 "$windows_partition") == "$windows_size" ]] || fail "Windows partition size differs"
[[ ! -e $mount_dir && ! -e $backup ]] || fail "staging or backup already exists"
! /usr/bin/findmnt "$windows_partition" >/dev/null || fail "Windows partition is already mounted"
for source in APX-ReturnToHub.ps1 APX-ReturnToHub.vbs APX-ProvisionHardware.cmd README.txt; do
    [[ -f $source_dir/$source && ! -L $source_dir/$source ]] || fail "source differs: $source"
    [[ $(/usr/bin/stat -c %s "$source_dir/$source") -le 32768 ]] || fail "source is oversized: $source"
done
/usr/bin/python3 -m unittest discover -s tests >/dev/null || fail "repository tests failed"
/usr/bin/bash -n "$0" || fail "staging script does not parse"

/usr/bin/install -d -m 0700 "$backup"
/usr/bin/sha256sum "$source_dir"/* >"$backup/source.sha256"
/usr/bin/mkdir -m 0700 "$mount_dir"
cleanup() {
    if /usr/bin/mountpoint -q "$mount_dir"; then /usr/bin/umount "$mount_dir" || true; fi
    /usr/bin/rmdir "$mount_dir" 2>/dev/null || true
}
rollback() {
    trap - ERR
    if (( stage >= 2 )); then
        /usr/bin/install -m 0644 -- "$backup/APX-ReturnToHub.ps1" "$program_target/APX-ReturnToHub.ps1" || true
        /usr/bin/install -m 0644 -- "$backup/README.txt" "$program_target/README.txt" || true
        /usr/bin/install -m 0644 -- "$backup/APX-ReturnToHub.vbs" "$startup_target" || true
        /usr/bin/install -m 0644 -- "$backup/REGRESSAR AO APX.cmd" "$desktop_target" || true
        /usr/bin/rm -f -- "$program_target/APX-ProvisionHardware.cmd" || true
    fi
    cleanup
    fail "installation failed; only the newly staged APX return files were removed"
}
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
/usr/bin/install -m 0644 -- "$source_dir/APX-ReturnToHub.ps1" "$program_target/APX-ReturnToHub.ps1"
/usr/bin/install -m 0644 -- "$source_dir/README.txt" "$program_target/README.txt"
/usr/bin/install -m 0644 -- "$source_dir/APX-ReturnToHub.vbs" "$startup_target"
/usr/bin/install -m 0644 -- "$source_dir/APX-ProvisionHardware.cmd" "$program_target/APX-ProvisionHardware.cmd"
/usr/bin/rm -f -- "$desktop_target"
stage=2
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
/usr/bin/rmdir "$mount_dir"
stage=3
trap - ERR
/usr/bin/chmod 0600 "$backup"/*
/usr/bin/printf 'APX Windows return updated. SUPER+E is supervised in the background; no desktop icon remains.\n'
