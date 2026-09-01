#!/usr/bin/bash
set -Eeuo pipefail

# Exact, non-rebooting recovery for the 2026-08-26 create/160 generation that
# returned from WinPE before formatting because findstr.exe was unavailable.
# It patches only the already authenticated p4 boot.wim and installs the
# matching fixed executors. It never starts the finalizer or arms BootNext.

readonly repository=/root/apx-host-development-mode-v1/apx
readonly disk=/dev/nvme0n1
readonly target=/dev/nvme0n1p3
readonly setup=/dev/nvme0n1p4
readonly generation=890c5a4c-3b84-41ea-af57-2fb0043243b5
readonly contract_hash=9ccf99cded857bae46bc799ddda1627ce02f64592bf93506da05f3e315ddbc24
readonly original_boot_wim_hash=a0ad1e94ed5b0d92634747e998cdc6eb928278a07ad31d713dcb1afdb0dae4bf
readonly embedded_broken_cmd_hash=ed09f01b8309875ac9cf151e66302061e403a4dc4f3005ce458143415b686af7
readonly setup_mount=/run/apx-winpe-findstr-v3-setup
readonly target_mount=/run/apx-winpe-findstr-v3-target
readonly staging=/var/lib/apx/package-artifacts/system-images-v1/apx-winpe-findstr-v3
readonly backup="/var/lib/apx/backups/$(/usr/bin/date -u +%Y%m%dT%H%M%SZ)-native-windows-winpe-findstr-v3"
readonly media_source="$repository/config/system-images-v1/windows-internal-winpe/apx-media.cmd"
readonly finalizer_source="$repository/scripts/physical-pilot/apx-native-windows-lifecycle-finalize-v1.py"
readonly switch_source="$repository/scripts/physical-pilot/apx-environment-switch-v1.py"
readonly asset_media=/usr/share/apx/native-windows-lifecycle-v1/winpe/apx-media.cmd
readonly installed_finalizer=/usr/lib/apx/apx-native-windows-lifecycle-finalize-v1.py
readonly installed_switch=/usr/lib/apx/apx-environment-switch-v1.py
stage=preflight

fail() { /usr/bin/printf 'APX WinPE findstr recovery refused at %s: %s\n' "$stage" "$1" >&2; exit 2; }
cleanup() {
    status=$?
    trap - EXIT INT TERM
    if /usr/bin/mountpoint -q "$setup_mount" \
            && [[ -f $setup_mount/sources/boot.wim.apx-original ]]; then
        /usr/bin/mv -f "$setup_mount/sources/boot.wim.apx-original" \
            "$setup_mount/sources/boot.wim" || true
        /usr/bin/sync || true
    fi
    /usr/bin/mountpoint -q "$target_mount" && /usr/bin/umount "$target_mount" || true
    /usr/bin/mountpoint -q "$setup_mount" && /usr/bin/umount "$setup_mount" || true
    /usr/bin/rmdir "$target_mount" "$setup_mount" 2>/dev/null || true
    exit "$status"
}
trap cleanup EXIT INT TERM

[[ ${1:-} == --prepare && $# == 1 ]] || fail 'invoke explicitly with --prepare'
[[ $(/usr/bin/id -u) == 0 && $PWD == "$repository" ]] || fail 'root or repository differs'
[[ $(< /etc/hostname) == apx-host && $(< /sys/class/dmi/id/product_name) == 82JU ]] || fail 'computer identity differs'
[[ $(< /sys/class/power_supply/ADP0/online) == 1 ]] || fail 'AC adapter is required'
[[ $(/usr/bin/xargs < /sys/block/nvme0n1/device/serial) == S4DYNX0R253702 ]] || fail 'disk serial differs'
[[ $(/usr/bin/blockdev --getsize64 "$disk") == 512110190592 ]] || fail 'disk size differs'
[[ $(/usr/bin/sfdisk --disk-id "$disk") == AC9FC0BD-2162-43A9-AAE6-3F654FF6F275 ]] || fail 'GPT identity differs'
[[ -z $(/usr/bin/efibootmgr | /usr/bin/awk '/^BootNext:/ {print}') ]] || fail 'a BootNext is already armed'
[[ ! -e $backup && ! -e $staging && ! -e $setup_mount && ! -e $target_mount ]] || fail 'recovery staging already exists'
for source in "$media_source" "$finalizer_source" "$switch_source"; do
    [[ -f $source && ! -L $source ]] || fail "source differs: $source"
done
for installed in "$asset_media" "$installed_finalizer" "$installed_switch"; do
    [[ -f $installed && ! -L $installed ]] || fail "installed target differs: $installed"
done
/usr/bin/python3 -m py_compile "$finalizer_source" "$switch_source"
! /usr/bin/grep -Fiq findstr "$media_source" || fail 'fixed WinPE source still depends on findstr'
/usr/bin/python3 - "$generation" <<'PY' || fail 'pending lifecycle marker differs'
import json
from pathlib import Path
import stat
import sys

path = Path("/var/lib/apx/native-environments/windows-pending.json")
info = path.lstat(); value = json.loads(path.read_bytes())
expected = {
    "action": "create", "created_at": 1787761299, "generation": sys.argv[1],
    "name": "windows", "profile": "apx-native-windows-pending-v1",
    "requested_size_gib": 160, "resume_attempts": 0, "schema": 1,
    "stage": "installing",
}
if path.is_symlink() or not path.is_file() or info.st_uid or info.st_gid \
        or stat.S_IMODE(info.st_mode) != 0o400 or value != expected:
    raise SystemExit(1)
PY

stage=exact-layout
[[ $(/usr/bin/cat /sys/class/block/nvme0n1p1/start):$(/usr/bin/blockdev --getsz /dev/nvme0n1p1) == 2048:2097152 \
        && $(/usr/bin/blkid -p -s PART_ENTRY_UUID -o value /dev/nvme0n1p1) == 9625f250-9acc-453a-ae63-0c863ade440f \
        && $(/usr/bin/blkid -s LABEL -o value /dev/nvme0n1p1) == APX_EFI ]] || fail 'APX EFI differs'
[[ $(/usr/bin/cat /sys/class/block/nvme0n1p2/start):$(/usr/bin/blockdev --getsz /dev/nvme0n1p2) == 2099200:662571008 \
        && $(/usr/bin/blkid -p -s PART_ENTRY_UUID -o value /dev/nvme0n1p2) == 8835c8f0-f02f-4fc2-9035-5dbbc191df9e \
        && $(/usr/bin/blkid -p -s PART_ENTRY_TYPE -o value /dev/nvme0n1p2) == ca7d7ccb-63ed-4c53-861c-1742536059cc ]] || fail 'APX Linux differs'
[[ $(/usr/bin/cat /sys/class/block/nvme0n1p3/start):$(/usr/bin/blockdev --getsz "$target") == 664670208:316669952 \
        && $(/usr/bin/blkid -p -s PART_ENTRY_UUID -o value "$target") == 099c31d8-313a-4aba-b0e0-2b59502c9674 \
        && $(/usr/bin/blkid -p -s PART_ENTRY_TYPE -o value "$target") == ebd0a0a2-b9e5-4433-87c0-68b6b72699c7 \
        && $(/usr/bin/blkid -s TYPE -o value "$target") == ntfs \
        && $(/usr/bin/blkid -s LABEL -o value "$target") == APXWINTARGET ]] || fail 'Windows target differs'
[[ $(/usr/bin/cat /sys/class/block/nvme0n1p4/start):$(/usr/bin/blockdev --getsz "$setup") == 981340160:18874368 \
        && $(/usr/bin/blkid -p -s PART_ENTRY_UUID -o value "$setup") == 309bebb6-5c32-4e21-9c92-6d758e51389d \
        && $(/usr/bin/blkid -p -s PART_ENTRY_TYPE -o value "$setup") == c12a7328-f81f-11d2-ba4b-00a0c93ec93b \
        && $(/usr/bin/blkid -s TYPE -o value "$setup") == vfat \
        && $(/usr/bin/blkid -s LABEL -o value "$setup") == APXWINSETUP ]] || fail 'Windows setup differs'
for number in 5 6 7 8; do [[ ! -e /dev/nvme0n1p$number ]] || fail 'unexpected partition exists'; done
! /usr/bin/findmnt "$target" >/dev/null && ! /usr/bin/findmnt "$setup" >/dev/null || fail 'Windows volume is already mounted'
[[ ! -e /boot/EFI/Microsoft && -f /boot/EFI/systemd/systemd-bootx64.efi ]] || fail 'shared APX EFI differs'

stage=media-validation
/usr/bin/mkdir "$target_mount" "$setup_mount"
/usr/bin/mount -t ntfs3 -o ro,nosuid,nodev,noexec "$target" "$target_mount"
/usr/bin/mount -t vfat -o ro,nosuid,nodev,noexec "$setup" "$setup_mount"
[[ $(/usr/bin/find "$target_mount" -mindepth 1 -maxdepth 1 -printf '%f\n') == APX ]] || fail 'Windows target was changed after the safe stop'
for contract in "$target_mount/APX/install-contract-v2.ini" "$setup_mount/APX/install-contract-v2.ini" /boot/EFI/APX/native-windows/install-contract-v2.ini; do
    [[ -f $contract && ! -L $contract && $(/usr/bin/sha256sum "$contract" | /usr/bin/awk '{print $1}') == "$contract_hash" ]] || fail 'install contract differs'
done
[[ $(/usr/bin/sha256sum "$setup_mount/sources/boot.wim" | /usr/bin/awk '{print $1}') == "$original_boot_wim_hash" ]] || fail 'current boot WIM differs'
[[ $(/usr/bin/sha256sum "$setup_mount/sources/install.swm" | /usr/bin/awk '{print $1}') == 91d933c801ad3d87b5616e00437bf9feca455658739343f0923823149c79f4c8 \
        && $(/usr/bin/sha256sum "$setup_mount/sources/install2.swm" | /usr/bin/awk '{print $1}') == 6e89a08d7dea3eea72125e418e191a5f3729b36cf226fa16f3c97b3a0bbeff2f \
        && $(/usr/bin/sha256sum "$setup_mount/sources/install3.swm" | /usr/bin/awk '{print $1}') == b747761a19757a39c8ddd60ed1b55d1036fda844245eeb46c96bc92f199f51fb ]] || fail 'split Windows image differs'
/usr/bin/install -d -m 0700 "$backup" "$staging" "$staging/extracted"
/usr/bin/sfdisk --dump "$disk" >"$backup/gpt-before.sfdisk"
/usr/bin/efibootmgr -v >"$backup/efibootmgr-before.txt"
/usr/bin/cp --archive "$asset_media" "$backup/apx-media.installed-before.cmd"
/usr/bin/cp --archive "$installed_finalizer" "$backup/finalizer.installed-before.py"
/usr/bin/cp --archive "$installed_switch" "$backup/switch.installed-before.py"
/usr/bin/install -m 0600 "$setup_mount/sources/boot.wim" "$staging/boot.wim"
/usr/bin/install -m 0600 "$staging/boot.wim" "$backup/boot.wim.before"
/usr/bin/wimlib-imagex extract "$staging/boot.wim" 2 Windows/System32/apx-media.cmd Windows/System32/apx-expected.ini \
    --dest-dir="$staging/extracted" --no-acls >/dev/null
[[ $(/usr/bin/sha256sum "$staging/extracted/apx-media.cmd" | /usr/bin/awk '{print $1}') == "$embedded_broken_cmd_hash" ]] || fail 'embedded failed command differs'
/usr/bin/cmp -s "$staging/extracted/apx-expected.ini" "$setup_mount/APX/install-contract-v2.ini" || fail 'embedded contract differs'
/usr/bin/umount "$target_mount"
/usr/bin/umount "$setup_mount"

stage=rebuild-winpe
/usr/bin/printf 'add "%s" /Windows/System32/apx-media.cmd\n' "$media_source" >"$staging/update-commands.txt"
/usr/bin/wimlib-imagex update "$staging/boot.wim" 2 --check --rebuild <"$staging/update-commands.txt"
/usr/bin/wimlib-imagex verify "$staging/boot.wim"
/usr/bin/find "$staging/extracted" -depth -delete
/usr/bin/mkdir "$staging/extracted"
/usr/bin/wimlib-imagex extract "$staging/boot.wim" 2 Windows/System32/apx-media.cmd Windows/System32/apx-expected.ini \
    --dest-dir="$staging/extracted" --no-acls >/dev/null
/usr/bin/cmp -s "$media_source" "$staging/extracted/apx-media.cmd" || fail 'rebuilt command differs'
[[ $(/usr/bin/sha256sum "$staging/extracted/apx-expected.ini" | /usr/bin/awk '{print $1}') == "$contract_hash" ]] || fail 'rebuilt embedded contract differs'
/usr/bin/sha256sum "$staging/boot.wim" >"$backup/boot-wim-after.sha256"

stage=atomic-media-replacement
/usr/bin/mount -t vfat -o rw "$setup" "$setup_mount"
[[ $(/usr/bin/df --output=avail -B1 "$setup_mount" | /usr/bin/tail -n1 | /usr/bin/xargs) -gt 700000000 ]] || fail 'setup lacks replacement space'
/usr/bin/install -m 0644 "$staging/boot.wim" "$setup_mount/sources/boot.wim.apx-new"
/usr/bin/sync
[[ $(/usr/bin/sha256sum "$setup_mount/sources/boot.wim.apx-new" | /usr/bin/awk '{print $1}') == $(/usr/bin/awk '{print $1}' "$backup/boot-wim-after.sha256") ]] || fail 'staged media write differs'
/usr/bin/mv "$setup_mount/sources/boot.wim" "$setup_mount/sources/boot.wim.apx-original"
/usr/bin/mv "$setup_mount/sources/boot.wim.apx-new" "$setup_mount/sources/boot.wim"
/usr/bin/sync
[[ $(/usr/bin/sha256sum "$setup_mount/sources/boot.wim" | /usr/bin/awk '{print $1}') == $(/usr/bin/awk '{print $1}' "$backup/boot-wim-after.sha256") ]] || fail 'published media differs'
/usr/bin/unlink "$setup_mount/sources/boot.wim.apx-original"
/usr/bin/sync
/usr/bin/umount "$setup_mount"

stage=install-fixed-runtime
/usr/bin/install -o root -g root -m 0644 "$media_source" "$asset_media"
/usr/bin/install -o root -g root -m 0755 "$finalizer_source" "$installed_finalizer"
/usr/bin/install -o root -g root -m 0755 "$switch_source" "$installed_switch"
/usr/bin/cmp "$media_source" "$asset_media"
/usr/bin/cmp "$finalizer_source" "$installed_finalizer"
/usr/bin/cmp "$switch_source" "$installed_switch"
/usr/bin/systemctl restart apx-environment-switch-v1.service
/usr/bin/systemctl is-active --quiet apx-environment-switch-v1.service
/usr/bin/python3 - <<'PY'
import json
import os
from pathlib import Path
import time

path = Path("/run/apx/environment-management-v1.json")
temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
value = {
    "schema": 1, "profile": "apx-environment-management-v1",
    "action": "native-create", "target": "windows", "phase": "failed",
    "progress": 100,
    "message": "WinPE corrigido e preservado; retoma explícita pronta.",
    "updated_at": int(time.time()),
}
descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
try:
    os.write(descriptor, (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode())
    os.fsync(descriptor)
finally:
    os.close(descriptor)
os.replace(temporary, path)
PY
/usr/bin/sfdisk --dump "$disk" >"$backup/gpt-after.sfdisk"
/usr/bin/cmp "$backup/gpt-before.sfdisk" "$backup/gpt-after.sfdisk"
/usr/bin/efibootmgr -v >"$backup/efibootmgr-after.txt"
[[ -z $(/usr/bin/efibootmgr | /usr/bin/awk '/^BootNext:/ {print}') ]] || fail 'repair unexpectedly armed BootNext'
/usr/bin/find "$staging" -depth -delete
/usr/bin/chown -R root:root "$backup"
/usr/bin/find "$backup" -type f -exec chmod 0600 {} +
/usr/bin/rmdir "$target_mount" "$setup_mount"
trap - EXIT INT TERM
/usr/bin/printf 'APX WinPE recovery prepared without reboot; backup: %s\n' "$backup"
