#!/usr/bin/bash
set -Eeuo pipefail

# Rebuild only the WinPE boot image of one authenticated, incomplete native
# Windows creation. The incomplete Windows target and all split SWM files are
# preserved. A later, separately authenticated finalizer selects setup once.

readonly assets=/usr/share/apx/native-windows-lifecycle-v1
readonly fc_exe_sha256=f4d29fd93794e50a6740b9692da5dcad119d0f5a68a812357497c69ed6496ce3
readonly size_gib="${1:-}"
readonly generation="${2:-}"
readonly disk=/dev/nvme0n1
readonly target=/dev/nvme0n1p3
readonly setup=/dev/nvme0n1p4
readonly pending=/var/lib/apx/native-environments/windows-pending.json
readonly marker=/var/lib/apx/native-environments/windows-installer-prepared-v2.json
readonly target_mount=/run/apx-windows-retry-target-v2
readonly setup_mount=/run/apx-windows-retry-setup-v2
readonly backup="/var/lib/apx/backups/native-windows-retry-$generation-$(/usr/bin/date -u +%Y%m%dT%H%M%SZ)-$$"
readonly staging="$backup/staging"
readonly winpe_source="$assets/winpe"
stage=preflight
published=0

fail() { /usr/bin/printf 'APX Windows installer refresh refused at %s: %s\n' "$stage" "$1" >&2; exit 2; }
cleanup() {
    status=$?
    trap - EXIT INT TERM
    if /usr/bin/mountpoint -q "$setup_mount"; then
        if [[ $published == 0 && -f $setup_mount/sources/boot.wim.apx-original ]]; then
            /usr/bin/rm -f "$setup_mount/sources/boot.wim.apx-new"
            /usr/bin/mv -f "$setup_mount/sources/boot.wim.apx-original" "$setup_mount/sources/boot.wim" || true
            /usr/bin/sync || true
        fi
        /usr/bin/umount "$setup_mount" || true
    fi
    /usr/bin/mountpoint -q "$target_mount" && /usr/bin/umount "$target_mount" || true
    /usr/bin/rmdir "$target_mount" "$setup_mount" 2>/dev/null || true
    exit "$status"
}
trap cleanup EXIT INT TERM

[[ $size_gib == 80 || $size_gib == 120 || $size_gib == 160 ]] || fail 'size differs'
[[ $generation =~ ^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$ ]] || fail 'generation differs'
[[ $(/usr/bin/id -u) == 0 ]] || fail 'root is required'
[[ $(< /etc/hostname) == apx-host && $(< /sys/class/dmi/id/product_name) == 82JU ]] || fail 'computer identity differs'
[[ $(< /sys/class/power_supply/ADP0/online) == 1 ]] || fail 'AC adapter is required'
[[ $(/usr/bin/xargs < /sys/block/nvme0n1/device/serial) == S4DYNX0R253702 ]] || fail 'disk serial differs'
[[ $(/usr/bin/blockdev --getsize64 "$disk") == 512110190592 ]] || fail 'disk size differs'
[[ $(/usr/bin/sfdisk --disk-id "$disk") == AC9FC0BD-2162-43A9-AAE6-3F654FF6F275 ]] || fail 'GPT identity differs'
[[ -z $(/usr/bin/efibootmgr | /usr/bin/awk '/^BootNext:/ {print}') ]] || fail 'a BootNext is already armed'
[[ ! -e $backup && ! -e $target_mount && ! -e $setup_mount ]] || fail 'staging already exists'
for source in "$winpe_source/apx-media.cmd" "$winpe_source/winpeshl.ini"; do
    [[ -f $source && ! -L $source && $(/usr/bin/stat -c '%U:%G:%a' "$source") == root:root:644 ]] \
        || fail 'WinPE source differs'
done
! /usr/bin/grep -Fiq findstr "$winpe_source/apx-media.cmd" || fail 'WinPE source still depends on findstr'
/usr/bin/grep -Fq 'X:\Windows\System32\find.exe' "$winpe_source/apx-media.cmd" \
    || fail 'WinPE source does not use the required search primitive'

tail_start=$(( (1000215183 - size_gib * 2097152) / 2048 * 2048 ))
p2_sectors=$(( tail_start - 2099200 ))
windows_sectors=$(( 981340160 - tail_start ))
/usr/bin/python3 - "$pending" "$marker" "$generation" "$size_gib" <<'PY' || fail 'pending identity differs'
import json
from pathlib import Path
import stat
import sys

pending_path, marker_path = map(Path, sys.argv[1:3])
generation, size = sys.argv[3], int(sys.argv[4])
for path, profile, mode in (
    (pending_path, "apx-native-windows-pending-v1", 0o400),
    (marker_path, "apx-native-windows-installer-prepared-v2", 0o400),
):
    info = path.lstat(); raw = path.read_bytes(); value = json.loads(raw)
    if path.is_symlink() or not path.is_file() or (info.st_uid, info.st_gid) != (0, 0) \
            or stat.S_IMODE(info.st_mode) != mode or len(raw) > 4096 \
            or value.get("profile") != profile:
        raise SystemExit(1)
pending = json.loads(pending_path.read_bytes())
if pending.get("schema") != 1 or pending.get("action") != "create" \
        or pending.get("stage") != "installing" or pending.get("name") != "windows" \
        or pending.get("generation") != generation or pending.get("requested_size_gib") != size:
    raise SystemExit(1)
marker = json.loads(marker_path.read_bytes())
expected = {
    "generation": generation, "profile": "apx-native-windows-installer-prepared-v2",
    "schema": 2, "setup_entry": marker.get("setup_entry"), "size_gib": size,
    "windows_partuuid": "099C31D8-313A-4ABA-B0E0-2B59502C9674",
    "windows_esp_partuuid": "9625F250-9ACC-453A-AE63-0C863ADE440F",
    "setup_partuuid": "309BEBB6-5C32-4E21-9C92-6D758E51389D",
}
if marker != expected or not isinstance(marker["setup_entry"], str) \
        or __import__("re").fullmatch(r"[0-9A-F]{4}", marker["setup_entry"]) is None:
    raise SystemExit(1)
PY

stage=layout
[[ $(/usr/bin/blockdev --getsz /dev/nvme0n1p2) == "$p2_sectors" ]] || fail 'APX partition size differs'
[[ $(/usr/bin/cat /sys/class/block/nvme0n1p3/start) == "$tail_start" \
        && $(/usr/bin/blockdev --getsz "$target") == "$windows_sectors" \
        && $(/usr/bin/blkid -p -s PART_ENTRY_UUID -o value "$target") == 099c31d8-313a-4aba-b0e0-2b59502c9674 \
        && $(/usr/bin/blkid -p -s PART_ENTRY_TYPE -o value "$target") == ebd0a0a2-b9e5-4433-87c0-68b6b72699c7 \
        && $(/usr/bin/blkid -s TYPE -o value "$target") == ntfs \
        && $(/usr/bin/blkid -s LABEL -o value "$target") == APXWINTARGET ]] || fail 'Windows target differs'
[[ $(/usr/bin/cat /sys/class/block/nvme0n1p4/start) == 981340160 \
        && $(/usr/bin/blockdev --getsz "$setup") == 18874368 \
        && $(/usr/bin/blkid -p -s PART_ENTRY_UUID -o value "$setup") == 309bebb6-5c32-4e21-9c92-6d758e51389d \
        && $(/usr/bin/blkid -p -s PART_ENTRY_TYPE -o value "$setup") == c12a7328-f81f-11d2-ba4b-00a0c93ec93b \
        && $(/usr/bin/blkid -s TYPE -o value "$setup") == vfat \
        && $(/usr/bin/blkid -s LABEL -o value "$setup") == APXWINSETUP ]] || fail 'Windows setup differs'
for number in 5 6; do [[ ! -e /dev/nvme0n1p$number ]] || fail 'unexpected tail partition exists'; done
[[ $(/usr/bin/blkid -s PARTUUID -o value /dev/nvme0n1p1) == 9625f250-9acc-453a-ae63-0c863ade440f \
        && $(/usr/bin/blkid -s LABEL -o value /dev/nvme0n1p1) == APX_EFI \
        && -f /boot/EFI/systemd/systemd-bootx64.efi ]] || fail 'APX EFI differs'
! /usr/bin/findmnt -rn -S "$target" >/dev/null && ! /usr/bin/findmnt -rn -S "$setup" >/dev/null \
    || fail 'Windows volume is already mounted'

stage=media-validation
/usr/bin/mkdir "$target_mount" "$setup_mount"
/usr/bin/mount -t ntfs3 -o ro,nosuid,nodev,noexec "$target" "$target_mount"
/usr/bin/mount -t vfat -o ro,nosuid,nodev,noexec "$setup" "$setup_mount"
/usr/bin/python3 - "$target_mount/APX/install-contract-v2.ini" \
        "$setup_mount/APX/install-contract-v2.ini" \
        /boot/EFI/APX/native-windows/install-contract-v2.ini \
        "$generation" "$size_gib" "$tail_start" "$p2_sectors" "$windows_sectors" <<'PY' \
        || fail 'installation contract differs'
from pathlib import Path
import sys

paths = [Path(value) for value in sys.argv[1:4]]
generation, size, start, linux_count, windows_count = sys.argv[4:]
raw = [path.read_bytes() for path in paths]
if any(path.is_symlink() or not path.is_file() or len(data) > 4096 for path, data in zip(paths, raw)) \
        or len(set(raw)) != 1:
    raise SystemExit(1)
values = {}
for line in raw[0].decode("ascii").splitlines():
    key, separator, value = line.partition("=")
    if not separator or key in values:
        raise SystemExit(1)
    values[key] = value
expected = {
    "profile": "apx-native-windows-install-contract-v2", "generation": generation,
    "size_gib": size, "disk_guid": "AC9FC0BD-2162-43A9-AAE6-3F654FF6F275",
    "disk_bytes": "512110190592", "efi_partition_guid": "9625F250-9ACC-453A-AE63-0C863ADE440F",
    "efi_start_sector": "2048", "efi_sector_count": "2097152",
    "linux_partition_guid": "8835C8F0-F02F-4FC2-9035-5DBBC191DF9E",
    "linux_start_sector": "2099200", "linux_sector_count": linux_count,
    "windows_partition_guid": "099C31D8-313A-4ABA-B0E0-2B59502C9674",
    "windows_start_sector": start, "windows_sector_count": windows_count,
    "setup_partition_guid": "309BEBB6-5C32-4E21-9C92-6D758E51389D",
    "setup_start_sector": "981340160", "setup_sector_count": "18874368", "image_index": "6",
}
if values != expected:
    raise SystemExit(1)
PY
[[ -f $setup_mount/sources/boot.wim && ! -L $setup_mount/sources/boot.wim ]] || fail 'boot WIM differs'
swm_count=$(/usr/bin/find "$setup_mount/sources" -maxdepth 1 -type f -iname 'install*.swm' -printf '.\n' | /usr/bin/wc -l)
[[ $swm_count == 3 && -f $setup_mount/sources/install.swm \
        && -f $setup_mount/sources/install2.swm && -f $setup_mount/sources/install3.swm ]] || fail 'split image set differs'
/usr/bin/wimlib-imagex info "$setup_mount/sources/install.swm" 6 \
    | /usr/bin/grep -Fx 'Name:                   Windows 11 Pro' >/dev/null || fail 'Windows 11 Pro index differs'
setup_entry=$(/usr/bin/python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["setup_entry"])' "$marker")
setup_line=$(/usr/bin/efibootmgr -v | /usr/bin/awk -v prefix="Boot${setup_entry}" \
    'index($0,prefix)==1 && $0 ~ /APX Windows Setup/ {print}')
[[ ${setup_line,,} == *'hd(4,gpt,309bebb6-5c32-4e21-9c92-6d758e51389d,'* \
        && ${setup_line,,} == *'\efi\boot\bootx64.efi'* ]] || fail 'setup boot entry differs'

stage=rebuild-winpe
/usr/bin/install -d -m 0700 "$backup" "$staging" "$staging/extracted"
/usr/bin/sfdisk --dump "$disk" >"$backup/gpt-before.sfdisk"
/usr/bin/efibootmgr -v >"$backup/efibootmgr-before.txt"
/usr/bin/wimlib-imagex extract "$setup_mount/sources/install.swm" 6 Windows/System32/fc.exe \
    --ref="$setup_mount/sources/install*.swm" --to-stdout >"$staging/fc.exe"
[[ -f $staging/fc.exe && ! -L $staging/fc.exe && $(/usr/bin/stat -c %s "$staging/fc.exe") == 49152 \
        && $(/usr/bin/sha256sum "$staging/fc.exe" | /usr/bin/awk '{print $1}') == "$fc_exe_sha256" ]] \
    || fail 'Windows 11 Pro comparison executable differs'
/usr/bin/install -m 0600 "$setup_mount/sources/boot.wim" "$staging/boot.wim"
/usr/bin/install -m 0600 "$staging/boot.wim" "$backup/boot.wim.before"
/usr/bin/install -m 0600 "$setup_mount/APX/install-contract-v2.ini" "$staging/install-contract-v2.ini"
/usr/bin/umount "$target_mount"
/usr/bin/umount "$setup_mount"
{
    /usr/bin/printf 'add "%s" /Windows/System32/winpeshl.ini\n' "$winpe_source/winpeshl.ini"
    /usr/bin/printf 'add "%s" /Windows/System32/apx-media.cmd\n' "$winpe_source/apx-media.cmd"
    /usr/bin/printf 'add "%s" /Windows/System32/apx-expected.ini\n' "$staging/install-contract-v2.ini"
    /usr/bin/printf 'add "%s" /Windows/System32/fc.exe\n' "$staging/fc.exe"
} >"$staging/wim-update-commands.txt"
/usr/bin/wimlib-imagex update "$staging/boot.wim" 2 --check --rebuild <"$staging/wim-update-commands.txt"
/usr/bin/wimlib-imagex verify "$staging/boot.wim"
for executable in bcdboot.exe bcdedit.exe cmd.exe diskpart.exe Dism.exe fc.exe find.exe mountvol.exe wpeutil.exe xcopy.exe; do
    /usr/bin/wimlib-imagex dir "$staging/boot.wim" 2 --path="Windows/System32/$executable" >/dev/null \
        || fail "required WinPE executable is absent: $executable"
done
/usr/bin/wimlib-imagex extract "$staging/boot.wim" 2 Windows/System32/winpeshl.ini \
    Windows/System32/apx-media.cmd Windows/System32/apx-expected.ini \
    --dest-dir="$staging/extracted" --no-acls >/dev/null
/usr/bin/cmp -s "$winpe_source/winpeshl.ini" "$staging/extracted/winpeshl.ini"
/usr/bin/cmp -s "$winpe_source/apx-media.cmd" "$staging/extracted/apx-media.cmd"
/usr/bin/cmp -s "$staging/install-contract-v2.ini" "$staging/extracted/apx-expected.ini"
/usr/bin/sha256sum "$staging/boot.wim" >"$backup/boot-wim-after.sha256"

stage=atomic-replacement
/usr/bin/mount -t vfat -o rw "$setup" "$setup_mount"
[[ $(/usr/bin/df --output=avail -B1 "$setup_mount" | /usr/bin/tail -n1 | /usr/bin/xargs) -gt 700000000 ]] \
    || fail 'setup lacks replacement space'
/usr/bin/install -m 0644 "$staging/boot.wim" "$setup_mount/sources/boot.wim.apx-new"
/usr/bin/sync
[[ $(/usr/bin/sha256sum "$setup_mount/sources/boot.wim.apx-new" | /usr/bin/awk '{print $1}') \
        == $(/usr/bin/awk '{print $1}' "$backup/boot-wim-after.sha256") ]] || fail 'staged boot WIM differs'
/usr/bin/mv "$setup_mount/sources/boot.wim" "$setup_mount/sources/boot.wim.apx-original"
/usr/bin/mv "$setup_mount/sources/boot.wim.apx-new" "$setup_mount/sources/boot.wim"
/usr/bin/sync
[[ $(/usr/bin/sha256sum "$setup_mount/sources/boot.wim" | /usr/bin/awk '{print $1}') \
        == $(/usr/bin/awk '{print $1}' "$backup/boot-wim-after.sha256") ]] || fail 'published boot WIM differs'
/usr/bin/rm -f "$setup_mount/APX/install-status-v2.ini"
/usr/bin/sync
/usr/bin/unlink "$setup_mount/sources/boot.wim.apx-original"
published=1
/usr/bin/umount "$setup_mount"

stage=postflight
/usr/bin/sfdisk --dump "$disk" >"$backup/gpt-after.sfdisk"
/usr/bin/cmp "$backup/gpt-before.sfdisk" "$backup/gpt-after.sfdisk"
/usr/bin/efibootmgr -v >"$backup/efibootmgr-after.txt"
[[ -z $(/usr/bin/efibootmgr | /usr/bin/awk '/^BootNext:/ {print}') ]] || fail 'refresh unexpectedly armed BootNext'
/usr/bin/find "$staging" -depth -delete
/usr/bin/chown -R root:root "$backup"
/usr/bin/find "$backup" -type f -exec chmod 0600 {} +
/usr/bin/rmdir "$target_mount" "$setup_mount"
trap - EXIT INT TERM
/usr/bin/printf 'APX Windows installer refreshed without reboot; backup: %s\n' "$backup"
