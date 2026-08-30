#!/usr/bin/bash
set -euo pipefail

readonly repository=/root/apx-host-development-mode-v1/apx
readonly disk=/dev/nvme0n1
readonly windows_partition=/dev/nvme0n1p4
readonly windows_partuuid=099C31D8-313A-4ABA-B0E0-2B59502C9674
readonly windows_size=118339141632
readonly mount_dir=/run/apx-windows-wifi-stage-v1
readonly artifact_dir=/var/lib/apx/package-artifacts/system-images-v1/windows-82ju-drivers-v1
readonly package="$artifact_dir/2gy50jafs8k061c0.exe"
readonly source_dir="$artifact_dir/extracted/code\$GetExtractPath\$/Source/WLAN_Realtek8852AE"
readonly manifest="$repository/config/system-images-v1/windows-82ju-wifi-driver-v1.json"
readonly backup=/var/lib/apx/backups/20260825-native-windows-wifi-driver-v1
readonly target_relative=APX/Drivers/Realtek8852AE
target_created=0

fail() { /usr/bin/printf 'APX Windows Wi-Fi staging refused: %s\n' "$1" >&2; exit 2; }
cleanup() {
    status=$?
    trap - EXIT INT TERM
    if /usr/bin/mountpoint -q "$mount_dir"; then
        if (( status != 0 && target_created == 1 )); then
            /usr/bin/find "$mount_dir/$target_relative.apx-new" -depth -type f -delete 2>/dev/null || true
            /usr/bin/find "$mount_dir/$target_relative.apx-new" -depth -type d -empty -delete 2>/dev/null || true
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
[[ $(/usr/bin/blkid -s PARTUUID -o value "$windows_partition" | /usr/bin/tr '[:lower:]' '[:upper:]') == "$windows_partuuid" ]] \
    || fail 'Windows partition identity differs'
[[ $(/usr/bin/blockdev --getsize64 "$windows_partition") == "$windows_size" ]] \
    || fail 'Windows partition size differs'
[[ ! -e $backup && ! -e $mount_dir ]] || fail 'backup or mount staging already exists'
! /usr/bin/findmnt "$windows_partition" >/dev/null || fail 'Windows partition is already mounted'
[[ -f $manifest && ! -L $manifest && -f $package && ! -L $package ]] \
    || fail 'driver manifest or package differs'
[[ $(/usr/bin/sha256sum "$package" | /usr/bin/awk '{print $1}') == 1defff5645c18427c5f1af5af07a0ebae1dde25c70c3624869d485cef06f0c04 ]] \
    || fail 'official Lenovo package digest differs'
/usr/bin/python3 - "$manifest" <<'PY' || fail 'driver manifest differs'
import json, sys
value = json.load(open(sys.argv[1], encoding="utf-8"))
assert value["profile"] == "apx-windows-82ju-wifi-driver-v1"
assert value["hardware_id"] == r"PCI\VEN_10EC&DEV_8852&SUBSYS_485217AA"
assert value["lenovo_doc_id"] == "DS551503"
assert value["driver_version"] == "6001.0.10.340"
PY

declare -A hashes=(
    [netrtwlane6.inf]=7742764146994bcf3660d8da874b941918b6e08db6cc3cd7c574afd3a6a9b901
    [netrtwlane6.cat]=3ed544c4860ff73d5a7e044a1bcc665a8527f8deb9fd6503cb356d91bd73c475
    [rtwlane6.sys]=be77de858665bd78680f67f96748337ac747704eb551fd552f14fbacb629abc1
    [rtldata60.txt]=32fe5fe472398feae62013b0b0f9c35f5ae273780c2a280e44634d75fbf20e64
)
for name in netrtwlane6.inf netrtwlane6.cat rtwlane6.sys rtldata60.txt; do
    [[ -f $source_dir/$name && ! -L $source_dir/$name ]] || fail "driver source is missing: $name"
    [[ $(/usr/bin/sha256sum "$source_dir/$name" | /usr/bin/awk '{print $1}') == "${hashes[$name]}" ]] \
        || fail "driver source digest differs: $name"
done
/usr/bin/iconv -f UTF-16LE -t UTF-8 "$source_dir/netrtwlane6.inf" \
    | /usr/bin/grep -F 'PCI\VEN_10EC&DEV_8852&SUBSYS_485217AA' >/dev/null \
    || fail 'driver does not match the exact Lenovo Wi-Fi identity'
/usr/bin/iconv -f UTF-16LE -t UTF-8 "$source_dir/netrtwlane6.inf" \
    | /usr/bin/grep -F 'CatalogFile = netrtwlane6.cat' >/dev/null \
    || fail 'driver catalogue declaration differs'
certificates=$(/usr/bin/openssl pkcs7 -inform DER -in "$source_dir/netrtwlane6.cat" -print_certs -noout) \
    || fail 'driver catalogue signature cannot be read'
[[ $certificates == *'CN=Microsoft Windows Hardware Compatibility Publisher'* ]] \
    || fail 'driver catalogue signer differs'

/usr/bin/install -d -m 0700 "$backup"
/usr/bin/sfdisk --dump "$disk" >"$backup/gpt-before.sfdisk"
/usr/bin/efibootmgr -v >"$backup/efibootmgr-before.txt"
/usr/bin/install -m 0600 -- "$manifest" "$backup/manifest.json"
/usr/bin/sha256sum "$package" "$source_dir"/* >"$backup/source-files.sha256"

/usr/bin/mkdir "$mount_dir"
/usr/bin/mount -t ntfs3 -o rw,nosuid,nodev,noexec "$windows_partition" "$mount_dir"
[[ -f $mount_dir/Windows/System32/config/SYSTEM && ! -L $mount_dir/Windows/System32/config/SYSTEM ]] \
    || fail 'offline Windows identity differs'
[[ ! -e $mount_dir/$target_relative && ! -e $mount_dir/$target_relative.apx-new ]] \
    || fail 'Windows APX driver target already exists'
/usr/bin/install -d -m 0755 "$mount_dir/APX" "$mount_dir/APX/Drivers" \
    "$mount_dir/$target_relative.apx-new"
target_created=1
for name in netrtwlane6.inf netrtwlane6.cat rtwlane6.sys rtldata60.txt; do
    /usr/bin/install -m 0644 -- "$source_dir/$name" "$mount_dir/$target_relative.apx-new/$name"
    [[ $(/usr/bin/sha256sum "$mount_dir/$target_relative.apx-new/$name" | /usr/bin/awk '{print $1}') == "${hashes[$name]}" ]]
done
/usr/bin/sync
/usr/bin/mv -- "$mount_dir/$target_relative.apx-new" "$mount_dir/$target_relative"
target_created=0
/usr/bin/sync
/usr/bin/umount "$mount_dir"

/usr/bin/mount -t ntfs3 -o ro,nosuid,nodev,noexec "$windows_partition" "$mount_dir"
for name in netrtwlane6.inf netrtwlane6.cat rtwlane6.sys rtldata60.txt; do
    [[ $(/usr/bin/sha256sum "$mount_dir/$target_relative/$name" | /usr/bin/awk '{print $1}') == "${hashes[$name]}" ]]
done
/usr/bin/umount "$mount_dir"
/usr/bin/rmdir "$mount_dir"
trap - EXIT INT TERM
/usr/bin/printf 'Official Lenovo RTL8852AE Windows driver staged at C:\\APX\\Drivers\\Realtek8852AE.\n'
