#!/usr/bin/bash
set -Eeuo pipefail

# Owner-invoked continuation after repair-current-native-windows-winpe-findstr-v3.
# Validation is read-only until the final command starts the existing finalizer;
# that finalizer arms only the authenticated APX Windows Setup entry and reboots.

readonly repository=/root/apx-host-development-mode-v1/apx
readonly generation=890c5a4c-3b84-41ea-af57-2fb0043243b5
readonly target=/dev/nvme0n1p3
readonly setup=/dev/nvme0n1p4
readonly setup_mount=/run/apx-winpe-resume-v3-setup
readonly target_mount=/run/apx-winpe-resume-v3-target
readonly extracted=/run/apx-winpe-resume-v3-extracted
readonly source_media="$repository/config/system-images-v1/windows-internal-winpe/apx-media.cmd"
readonly installed_media=/usr/share/apx/native-windows-lifecycle-v1/winpe/apx-media.cmd
readonly source_finalizer="$repository/scripts/physical-pilot/apx-native-windows-lifecycle-finalize-v1.py"
readonly installed_finalizer=/usr/lib/apx/apx-native-windows-lifecycle-finalize-v1.py
readonly source_switch="$repository/scripts/physical-pilot/apx-environment-switch-v1.py"
readonly installed_switch=/usr/lib/apx/apx-environment-switch-v1.py
stage=preflight

fail() { /usr/bin/printf 'APX Windows continuation refused at %s: %s\n' "$stage" "$1" >&2; exit 2; }
cleanup() {
    status=$?
    trap - EXIT INT TERM
    /usr/bin/mountpoint -q "$target_mount" && /usr/bin/umount "$target_mount" || true
    /usr/bin/mountpoint -q "$setup_mount" && /usr/bin/umount "$setup_mount" || true
    [[ ! -d $extracted ]] || /usr/bin/find "$extracted" -depth -delete
    /usr/bin/rmdir "$target_mount" "$setup_mount" 2>/dev/null || true
    exit "$status"
}
trap cleanup EXIT INT TERM

[[ ${1:-} == --reboot && $# == 1 ]] || fail 'invoke explicitly with --reboot'
[[ $(/usr/bin/id -u) == 0 && $PWD == "$repository" ]] || fail 'root or repository differs'
[[ $(< /etc/hostname) == apx-host && $(< /sys/class/dmi/id/product_name) == 82JU ]] || fail 'computer identity differs'
[[ $(< /sys/class/power_supply/ADP0/online) == 1 ]] || fail 'AC adapter is required'
[[ $(/usr/bin/xargs < /sys/block/nvme0n1/device/serial) == S4DYNX0R253702 ]] || fail 'disk serial differs'
[[ $(/usr/bin/sfdisk --disk-id /dev/nvme0n1) == AC9FC0BD-2162-43A9-AAE6-3F654FF6F275 ]] || fail 'GPT identity differs'
[[ -z $(/usr/bin/efibootmgr | /usr/bin/awk '/^BootNext:/ {print}') ]] || fail 'a BootNext is already armed'
[[ ! -e $setup_mount && ! -e $target_mount && ! -e $extracted ]] || fail 'validation staging already exists'
/usr/bin/cmp "$source_media" "$installed_media" || fail 'installed WinPE command differs'
/usr/bin/cmp "$source_finalizer" "$installed_finalizer" || fail 'installed finalizer differs'
/usr/bin/cmp "$source_switch" "$installed_switch" || fail 'installed menu service differs'
! /usr/bin/grep -Fiq findstr "$installed_media" || fail 'installed WinPE still depends on findstr'

/usr/bin/python3 - "$generation" <<'PY' || fail 'pending lifecycle state differs'
import json
from pathlib import Path
import stat
import sys

pending_path = Path("/var/lib/apx/native-environments/windows-pending.json")
pending_info = pending_path.lstat(); pending = json.loads(pending_path.read_bytes())
expected_pending = {
    "action": "create", "created_at": 1787761299, "generation": sys.argv[1],
    "name": "windows", "profile": "apx-native-windows-pending-v1",
    "requested_size_gib": 160, "resume_attempts": 0, "schema": 1,
    "stage": "installing",
}
marker_path = Path("/var/lib/apx/native-environments/windows-installer-prepared-v2.json")
marker_info = marker_path.lstat(); marker = json.loads(marker_path.read_bytes())
expected_marker = {
    "generation": sys.argv[1], "profile": "apx-native-windows-installer-prepared-v2",
    "schema": 2, "setup_entry": "0000", "size_gib": 160,
    "setup_partuuid": "309BEBB6-5C32-4E21-9C92-6D758E51389D",
    "windows_esp_partuuid": "9625F250-9ACC-453A-AE63-0C863ADE440F",
    "windows_partuuid": "099C31D8-313A-4ABA-B0E0-2B59502C9674",
}
for path, info in ((pending_path, pending_info), (marker_path, marker_info)):
    if path.is_symlink() or not path.is_file() or info.st_uid or info.st_gid \
            or stat.S_IMODE(info.st_mode) != 0o400:
        raise SystemExit(1)
if pending != expected_pending or marker != expected_marker:
    raise SystemExit(1)
PY

stage=layout-and-firmware
[[ $(/usr/bin/cat /sys/class/block/nvme0n1p3/start):$(/usr/bin/blockdev --getsz "$target") == 664670208:316669952 \
        && $(/usr/bin/blkid -p -s PART_ENTRY_UUID -o value "$target") == 099c31d8-313a-4aba-b0e0-2b59502c9674 \
        && $(/usr/bin/blkid -s TYPE -o value "$target") == ntfs \
        && $(/usr/bin/blkid -s LABEL -o value "$target") == APXWINTARGET ]] || fail 'Windows target differs'
[[ $(/usr/bin/cat /sys/class/block/nvme0n1p4/start):$(/usr/bin/blockdev --getsz "$setup") == 981340160:18874368 \
        && $(/usr/bin/blkid -p -s PART_ENTRY_UUID -o value "$setup") == 309bebb6-5c32-4e21-9c92-6d758e51389d \
        && $(/usr/bin/blkid -s TYPE -o value "$setup") == vfat \
        && $(/usr/bin/blkid -s LABEL -o value "$setup") == APXWINSETUP ]] || fail 'Windows setup differs'
[[ ! -e /boot/EFI/Microsoft && -f /boot/EFI/systemd/systemd-bootx64.efi ]] || fail 'APX EFI differs'
entry=$(/usr/bin/efibootmgr -v | /usr/bin/awk '/^Boot0000\* APX Windows Setup/ {print $0}')
[[ $entry == *'GPT,309bebb6-5c32-4e21-9c92-6d758e51389d'* \
        && ${entry,,} == *'\efi\boot\bootx64.efi'* ]] || fail 'APX Windows Setup entry differs'

stage=media-and-target
/usr/bin/mkdir "$target_mount" "$setup_mount" "$extracted"
/usr/bin/mount -t ntfs3 -o ro,nosuid,nodev,noexec "$target" "$target_mount"
/usr/bin/mount -t vfat -o ro,nosuid,nodev,noexec "$setup" "$setup_mount"
[[ $(/usr/bin/find "$target_mount" -mindepth 1 -maxdepth 1 -printf '%f\n') == APX ]] || fail 'Windows target is no longer pristine'
[[ $(/usr/bin/sha256sum "$target_mount/APX/install-contract-v2.ini" | /usr/bin/awk '{print $1}') == 9ccf99cded857bae46bc799ddda1627ce02f64592bf93506da05f3e315ddbc24 ]] || fail 'target contract differs'
[[ $(/usr/bin/sha256sum "$setup_mount/sources/boot.wim" | /usr/bin/awk '{print $1}') != a0ad1e94ed5b0d92634747e998cdc6eb928278a07ad31d713dcb1afdb0dae4bf ]] || fail 'boot WIM was not repaired'
/usr/bin/wimlib-imagex verify "$setup_mount/sources/boot.wim"
/usr/bin/wimlib-imagex extract "$setup_mount/sources/boot.wim" 2 Windows/System32/apx-media.cmd Windows/System32/apx-expected.ini \
    --dest-dir="$extracted" --no-acls >/dev/null
/usr/bin/cmp "$installed_media" "$extracted/apx-media.cmd" || fail 'embedded repaired command differs'
/usr/bin/cmp "$setup_mount/APX/install-contract-v2.ini" "$extracted/apx-expected.ini" || fail 'embedded contract differs'
/usr/bin/umount "$target_mount"
/usr/bin/umount "$setup_mount"
/usr/bin/find "$extracted" -depth -delete
/usr/bin/rmdir "$target_mount" "$setup_mount"

stage=explicit-continuation
trap - EXIT INT TERM
/usr/bin/systemctl reset-failed apx-native-windows-lifecycle-finalize-v1.service
/usr/bin/systemctl start apx-native-windows-lifecycle-finalize-v1.service
/usr/bin/printf 'APX Windows continuation accepted; the authenticated setup reboot is being performed.\n'
