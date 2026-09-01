#!/usr/bin/bash
set -euo pipefail

readonly repository=/root/apx-host-development-mode-v1/apx
readonly disk=/dev/nvme0n1
readonly partition=/dev/nvme0n1p3
readonly mount_dir=/run/apx-windows-winpe-repair
readonly staging_dir=/var/lib/apx/package-artifacts/system-images-v1/apx-winpe-repair-v1
readonly backup=/var/lib/apx/backups/20260825-native-windows-winpe-media-v1
readonly boot_wim_hash=8fa24fc17e887ea975289b9ecd86f02848270000c655ae2be2989f989da30356
readonly winpeshl="$repository/config/system-images-v1/windows-internal-winpe/winpeshl.ini"
readonly media_script="$repository/config/system-images-v1/windows-internal-winpe/apx-media.cmd"
stage=0

fail() { /usr/bin/printf 'APX WinPE media repair refused: %s\n' "$1" >&2; exit 2; }
cleanup() {
    status=$?
    trap - EXIT INT TERM
    if /usr/bin/mountpoint -q "$mount_dir"; then
        if (( status != 0 && stage >= 2 && stage < 4 )) \
                && [[ -f $mount_dir/sources/boot.wim.apx-original ]]; then
            /usr/bin/mv -f -- "$mount_dir/sources/boot.wim.apx-original" "$mount_dir/sources/boot.wim" || true
        fi
        /usr/bin/umount "$mount_dir" || true
    fi
    /usr/bin/rmdir "$mount_dir" 2>/dev/null || true
    exit "$status"
}
trap cleanup EXIT INT TERM

[[ $(/usr/bin/id -u) == 0 ]] || fail 'root is required'
[[ $PWD == "$repository" ]] || fail 'repository differs'
[[ $(< /etc/hostname) == apx-host ]] || fail 'hostname differs'
[[ $(< /sys/class/dmi/id/product_name) == 82JU ]] || fail 'Lenovo identity differs'
/usr/bin/grep -Fxq 'profile=apx-physical-headless-pilot-v1' /etc/apx-physical-pilot \
    || fail 'physical-pilot marker differs'
[[ $(< /sys/class/power_supply/ADP0/online) == 1 ]] || fail 'AC adapter is required'
[[ $(/usr/bin/xargs < /sys/block/nvme0n1/device/serial) == S4DYNX0R253702 ]] \
    || fail 'disk serial differs'
[[ $(/usr/bin/sfdisk --disk-id "$disk") == AC9FC0BD-2162-43A9-AAE6-3F654FF6F275 ]] \
    || fail 'GPT identity differs'
[[ $(/usr/bin/blkid -s PARTUUID -o value "$partition" | /usr/bin/tr '[:lower:]' '[:upper:]') == 309BEBB6-5C32-4E21-9C92-6D758E51389D ]] \
    || fail 'installer partition identity differs'
[[ -f $winpeshl && ! -L $winpeshl && -f $media_script && ! -L $media_script ]] \
    || fail 'WinPE source differs'
[[ ! -e $backup && ! -e $staging_dir && ! -e $mount_dir ]] \
    || fail 'staging or backup already exists'
! /usr/bin/findmnt "$partition" >/dev/null || fail 'installer partition is already mounted'

/usr/bin/install -d -m 0700 "$backup" "$staging_dir"
/usr/bin/efibootmgr -v >"$backup/efibootmgr-before.txt"
/usr/bin/sfdisk --dump "$disk" >"$backup/gpt-before.sfdisk"
/usr/bin/install -m 0644 -- "$winpeshl" "$backup/winpeshl.ini"
/usr/bin/install -m 0644 -- "$media_script" "$backup/apx-media.cmd"

/usr/bin/mkdir "$mount_dir"
/usr/bin/mount -o ro "$partition" "$mount_dir"
[[ $(/usr/bin/sha256sum "$mount_dir/sources/boot.wim" | /usr/bin/awk '{print $1}') == "$boot_wim_hash" ]] \
    || fail 'original boot WIM digest differs'
/usr/bin/install -m 0600 -- "$mount_dir/sources/boot.wim" "$staging_dir/boot.wim"
/usr/bin/umount "$mount_dir"
stage=1

{
    /usr/bin/printf 'add "%s" /Windows/System32/winpeshl.ini\n' "$winpeshl"
    /usr/bin/printf 'add "%s" /Windows/System32/apx-media.cmd\n' "$media_script"
} >"$staging_dir/update-commands.txt"
/usr/bin/wimlib-imagex update "$staging_dir/boot.wim" 2 --check --rebuild \
    <"$staging_dir/update-commands.txt"
/usr/bin/wimlib-imagex verify "$staging_dir/boot.wim"
/usr/bin/wimlib-imagex extract "$staging_dir/boot.wim" 2 \
    Windows/System32/winpeshl.ini Windows/System32/apx-media.cmd \
    --dest-dir="$staging_dir/extracted" --no-acls >/dev/null
/usr/bin/cmp -s "$winpeshl" "$staging_dir/extracted/winpeshl.ini"
/usr/bin/cmp -s "$media_script" "$staging_dir/extracted/apx-media.cmd"
/usr/bin/sha256sum "$staging_dir/boot.wim" >"$backup/boot-wim-after.sha256"

/usr/bin/mount -o rw "$partition" "$mount_dir"
[[ $(/usr/bin/df --output=avail -B1 "$mount_dir" | /usr/bin/tail -n1 | /usr/bin/xargs) -gt 700000000 ]] \
    || fail 'installer partition lacks atomic replacement space'
/usr/bin/install -m 0644 -- "$staging_dir/boot.wim" "$mount_dir/sources/boot.wim.apx-new"
/usr/bin/sync
[[ $(/usr/bin/sha256sum "$mount_dir/sources/boot.wim.apx-new" | /usr/bin/awk '{print $1}') == $(/usr/bin/awk '{print $1}' "$backup/boot-wim-after.sha256") ]]
/usr/bin/mv -- "$mount_dir/sources/boot.wim" "$mount_dir/sources/boot.wim.apx-original"
stage=2
/usr/bin/mv -- "$mount_dir/sources/boot.wim.apx-new" "$mount_dir/sources/boot.wim"
stage=3
/usr/bin/sync
[[ $(/usr/bin/sha256sum "$mount_dir/sources/boot.wim" | /usr/bin/awk '{print $1}') == $(/usr/bin/awk '{print $1}' "$backup/boot-wim-after.sha256") ]]
/usr/bin/unlink "$mount_dir/sources/boot.wim.apx-original"
/usr/bin/sync
/usr/bin/umount "$mount_dir"
stage=4
/usr/bin/rmdir "$mount_dir"
/usr/bin/mv -- "$staging_dir/update-commands.txt" "$backup/update-commands.txt"
/usr/bin/sha256sum "$staging_dir/boot.wim" >"$backup/staged-boot-wim.sha256"
/usr/bin/find "$staging_dir" -depth -type f -delete
/usr/bin/find "$staging_dir" -depth -type d -empty -delete
trap - EXIT INT TERM
/usr/bin/printf 'APX WinPE media source repair installed.\n'
