#!/usr/bin/bash
set -Eeuo pipefail

readonly assets=/usr/share/apx/native-windows-lifecycle-v1
readonly size_gib="${1:-}"
readonly generation="${2:-}"
readonly disk=/dev/nvme0n1
readonly windows_partition=/dev/nvme0n1p3
readonly installer_partition=/dev/nvme0n1p4
readonly iso=/var/lib/apx/package-artifacts/system-images-v1/windows11.iso
readonly iso_sha256=c74c96aa06e2548f14c76b5fd6600514c0d4f6eb05a731e4272ab005e8f48ce3
readonly windows_uuid=099C31D8-313A-4ABA-B0E0-2B59502C9674
readonly windows_type=EBD0A0A2-B9E5-4433-87C0-68B6B72699C7
readonly installer_start=981340160
readonly installer_size=18874368
readonly installer_uuid=309BEBB6-5C32-4E21-9C92-6D758E51389D
readonly installer_type=C12A7328-F81F-11D2-BA4B-00A0C93EC93B
readonly windows_mount=/run/apx-windows-target-v2
readonly iso_mount=/run/apx-windows-iso-v2
readonly installer_mount=/run/apx-windows-installer-v2
readonly return_source="$assets/return"
readonly winpe_source="$assets/winpe"
readonly driver_source='/var/lib/apx/package-artifacts/system-images-v1/windows-82ju-drivers-v1/extracted/code$GetExtractPath$/Source/WLAN_Realtek8852AE'
readonly prepared_marker=/var/lib/apx/native-environments/windows-installer-prepared-v2.json
readonly backup="/var/lib/apx/backups/native-windows-installer-v2-$generation-$(/usr/bin/date -u +%Y%m%dT%H%M%SZ)-$$"
readonly staging="$backup/staging"
stage=preflight

fail() { /usr/bin/printf 'APX internal Windows installer v2 refused at %s: %s\n' "$stage" "$1" >&2; exit 2; }
[[ $size_gib == 80 || $size_gib == 120 || $size_gib == 160 ]] || fail "size differs"
[[ $generation =~ ^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$ ]] || fail "generation differs"
[[ $(/usr/bin/id -u) == 0 ]] || fail "root is required"
[[ $(< /etc/hostname) == apx-host && $(< /sys/class/dmi/id/product_name) == 82JU ]] || fail "computer identity differs"
[[ $(/usr/bin/xargs < /sys/block/nvme0n1/device/serial) == S4DYNX0R253702 ]] || fail "disk serial differs"
[[ $(/usr/bin/blockdev --getsize64 "$disk") == 512110190592 ]] || fail "disk size differs"
[[ $(/usr/bin/sfdisk --disk-id "$disk") == AC9FC0BD-2162-43A9-AAE6-3F654FF6F275 ]] || fail "GPT identity differs"
tail_start=$(( (1000215183 - size_gib * 2097152) / 2048 * 2048 ))
p2_sectors=$(( tail_start - 2099200 ))
windows_size=$(( installer_start - tail_start ))
[[ $(/usr/bin/blockdev --getsz /dev/nvme0n1p2) == "$p2_sectors" ]] || fail "APX partition size differs"
for number in 3 4 5 6; do [[ ! -b /dev/nvme0n1p$number ]] || fail "reserved Windows range is not empty"; done
[[ $(/usr/bin/blkid -s PARTUUID -o value /dev/nvme0n1p1) == 9625f250-9acc-453a-ae63-0c863ade440f ]] || fail "APX EFI identity differs"
[[ $(/usr/bin/blkid -s TYPE -o value /dev/nvme0n1p1) == vfat ]] || fail "APX EFI filesystem differs"
[[ $(/usr/bin/blkid -s LABEL -o value /dev/nvme0n1p1) == APX_EFI ]] || fail "APX EFI label differs"
[[ $(/usr/bin/cat /sys/class/block/nvme0n1p1/start) == 2048 && $(/usr/bin/blockdev --getsz /dev/nvme0n1p1) == 2097152 ]] || fail "APX EFI geometry differs"
[[ -f /boot/EFI/systemd/systemd-bootx64.efi && -d /boot/EFI/APX && ! -e /boot/EFI/Microsoft ]] || fail "APX EFI contents are not clean for a new Windows"
[[ -f $iso && ! -L $iso && $(/usr/bin/stat -c %s "$iso") == 8382230528 ]] || fail "installer ISO identity differs"
[[ $(/usr/bin/sha256sum "$iso" | /usr/bin/awk '{print $1}') == "$iso_sha256" ]] || fail "installer ISO digest differs"
[[ -d $driver_source && ! -L $driver_source ]] || fail "Wi-Fi driver source differs"
for source in APX-ReturnToHub.ps1 APX-ReturnToHub.vbs APX-ProvisionHardware.cmd README.txt; do
    [[ -f $return_source/$source && ! -L $return_source/$source \
            && $(/usr/bin/stat -c '%U:%G:%a' "$return_source/$source") == root:root:644 ]] \
        || fail "return source differs"
done
for source in apx-media.cmd winpeshl.ini; do
    [[ -f $winpe_source/$source && ! -L $winpe_source/$source \
            && $(/usr/bin/stat -c '%U:%G:%a' "$winpe_source/$source") == root:root:644 ]] \
        || fail "WinPE source differs"
done
! /usr/bin/grep -Fiq findstr "$winpe_source/apx-media.cmd" || fail "WinPE command depends on an unavailable optional tool"
/usr/bin/grep -Fq 'X:\Windows\System32\find.exe' "$winpe_source/apx-media.cmd" \
    || fail "WinPE command does not use the required search primitive"

if [[ -e $prepared_marker || -L $prepared_marker ]]; then
    /usr/bin/python3 - "$prepared_marker" "$generation" "$size_gib" <<'PY' || fail "prepared installer marker differs"
import json
from pathlib import Path
import stat
import sys

path = Path(sys.argv[1]); info = path.lstat(); value = json.loads(path.read_bytes())
expected = {
    "generation": sys.argv[2], "profile": "apx-native-windows-installer-prepared-v2",
    "schema": 2, "setup_entry": value.get("setup_entry"), "size_gib": int(sys.argv[3]),
    "windows_partuuid": "099C31D8-313A-4ABA-B0E0-2B59502C9674",
    "windows_esp_partuuid": "9625F250-9ACC-453A-AE63-0C863ADE440F",
    "setup_partuuid": "309BEBB6-5C32-4E21-9C92-6D758E51389D",
}
if path.is_symlink() or not path.is_file() or info.st_uid or info.st_gid \
        or stat.S_IMODE(info.st_mode) != 0o400 or value != expected \
        or not isinstance(value["setup_entry"], str) or len(value["setup_entry"]) != 4:
    raise SystemExit(1)
PY
    setup_entry=$(/usr/bin/python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["setup_entry"])' "$prepared_marker")
    [[ -b $windows_partition && -b $installer_partition && ! -e /dev/nvme0n1p5 && ! -e /dev/nvme0n1p6 ]] || fail "prepared installer layout differs"
    [[ $(/usr/bin/blkid -s PARTUUID -o value "$windows_partition") == ${windows_uuid,,} \
            && $(/usr/bin/blkid -s TYPE -o value "$windows_partition") == ntfs \
            && $(/usr/bin/blkid -s LABEL -o value "$windows_partition") == APXWINTARGET ]] || fail "prepared Windows target differs"
    [[ $(/usr/bin/blkid -s PARTUUID -o value "$installer_partition") == ${installer_uuid,,} \
            && $(/usr/bin/blkid -s TYPE -o value "$installer_partition") == vfat \
            && $(/usr/bin/blkid -s LABEL -o value "$installer_partition") == APXWINSETUP ]] || fail "prepared setup partition differs"
    /usr/bin/efibootmgr -v | /usr/bin/grep -Fiq "Boot${setup_entry}* APX Windows Setup" || fail "prepared setup boot entry differs"
    [[ -z $(/usr/bin/efibootmgr | /usr/bin/awk '/^BootNext:/ {print}') ]] \
        || fail "prepared installer unexpectedly has BootNext armed"
    /usr/bin/printf 'APX Windows installer v2 already prepared without reboot: Boot%s\n' "$setup_entry"
    exit 0
fi
[[ ! -e $backup && ! -e $iso_mount && ! -e $installer_mount && ! -e $windows_mount ]] || fail "staging already exists"

/usr/bin/install -d -m 0700 "$backup" "$staging"
/usr/bin/sfdisk --dump "$disk" >"$backup/gpt-before.sfdisk"
/usr/bin/efibootmgr -v >"$backup/efibootmgr-before.txt"
/usr/bin/sha256sum "$iso" "$return_source"/* "$driver_source"/* "$winpe_source"/* >"$backup/sources.sha256"
contract="$staging/install-contract-v2.ini"
/usr/bin/printf '%s\n' \
    'profile=apx-native-windows-install-contract-v2' \
    "generation=$generation" \
    "size_gib=$size_gib" \
    'disk_guid=AC9FC0BD-2162-43A9-AAE6-3F654FF6F275' \
    'disk_bytes=512110190592' \
    'efi_partition_guid=9625F250-9ACC-453A-AE63-0C863ADE440F' \
    'efi_start_sector=2048' \
    'efi_sector_count=2097152' \
    'linux_partition_guid=8835C8F0-F02F-4FC2-9035-5DBBC191DF9E' \
    'linux_start_sector=2099200' \
    "linux_sector_count=$p2_sectors" \
    "windows_partition_guid=$windows_uuid" \
    "windows_start_sector=$tail_start" \
    "windows_sector_count=$windows_size" \
    "setup_partition_guid=$installer_uuid" \
    "setup_start_sector=$installer_start" \
    "setup_sector_count=$installer_size" \
    'image_index=6' >"$contract"

cleanup_mounts() {
    (
    set +e
    /usr/bin/mountpoint -q "$installer_mount" && /usr/bin/umount "$installer_mount"
    /usr/bin/mountpoint -q "$windows_mount" && /usr/bin/umount "$windows_mount"
    /usr/bin/mountpoint -q "$iso_mount" && /usr/bin/umount "$iso_mount"
    /usr/bin/rmdir "$installer_mount" "$windows_mount" "$iso_mount" 2>/dev/null
    )
}
on_error() {
    trap - ERR
    cleanup_mounts
    /usr/bin/printf 'APX installer preparation stopped safely at %s. Created partitions, if any, were retained for explicit recovery.\n' "$stage" >&2
    exit 2
}
trap on_error ERR
trap cleanup_mounts EXIT

stage=patch-winpe
/usr/bin/mkdir -p "$iso_mount"
/usr/bin/mount -o loop,ro "$iso" "$iso_mount"
/usr/bin/wimlib-imagex info "$iso_mount/sources/install.wim" 6 \
    | /usr/bin/grep -Fx 'Name:                   Windows 11 Pro' >/dev/null \
    || fail "Windows 11 Pro is not image index 6"
/usr/bin/install -m 0600 "$iso_mount/sources/boot.wim" "$staging/boot.wim"
{
    /usr/bin/printf 'add "%s" /Windows/System32/winpeshl.ini\n' "$winpe_source/winpeshl.ini"
    /usr/bin/printf 'add "%s" /Windows/System32/apx-media.cmd\n' "$winpe_source/apx-media.cmd"
    /usr/bin/printf 'add "%s" /Windows/System32/apx-expected.ini\n' "$contract"
} >"$staging/wim-update-commands.txt"
/usr/bin/wimlib-imagex update "$staging/boot.wim" 2 --check --rebuild <"$staging/wim-update-commands.txt"
/usr/bin/wimlib-imagex verify "$staging/boot.wim"
for executable in bcdboot.exe bcdedit.exe cmd.exe diskpart.exe dism.exe fc.exe find.exe mountvol.exe wpeutil.exe xcopy.exe; do
    /usr/bin/wimlib-imagex dir "$staging/boot.wim" 2 --path="Windows/System32/$executable" >/dev/null \
        || fail "required WinPE executable is absent: $executable"
done
/usr/bin/mkdir -p "$staging/extracted"
/usr/bin/wimlib-imagex extract "$staging/boot.wim" 2 Windows/System32/winpeshl.ini Windows/System32/apx-media.cmd Windows/System32/apx-expected.ini \
    --dest-dir="$staging/extracted" --no-acls >/dev/null
/usr/bin/cmp -s "$winpe_source/winpeshl.ini" "$staging/extracted/winpeshl.ini"
/usr/bin/cmp -s "$winpe_source/apx-media.cmd" "$staging/extracted/apx-media.cmd"
/usr/bin/cmp -s "$contract" "$staging/extracted/apx-expected.ini"

stage=create-exact-gpt-targets
/usr/bin/sfdisk --append --no-reread --no-tell-kernel --wipe never "$disk" <<EOF >/dev/null
start=$tail_start, size=$windows_size, type=$windows_type, uuid=$windows_uuid, name="APX_WINDOWS_TARGET"
start=$installer_start, size=$installer_size, type=$installer_type, uuid=$installer_uuid, name="APX_WINSETUP"
EOF
/usr/bin/partx --add --nr 3:4 "$disk"
[[ $(/usr/bin/cat /sys/class/block/nvme0n1p3/start) == "$tail_start" \
        && $(/usr/bin/blockdev --getsz "$windows_partition") == "$windows_size" \
        && $(/usr/bin/blkid -p -s PART_ENTRY_UUID -o value "$windows_partition") == ${windows_uuid,,} \
        && $(/usr/bin/blkid -p -s PART_ENTRY_TYPE -o value "$windows_partition") == ${windows_type,,} ]] || fail "Windows target GPT contract differs"
[[ $(/usr/bin/cat /sys/class/block/nvme0n1p4/start) == "$installer_start" \
        && $(/usr/bin/blockdev --getsz "$installer_partition") == "$installer_size" \
        && $(/usr/bin/blkid -p -s PART_ENTRY_UUID -o value "$installer_partition") == ${installer_uuid,,} \
        && $(/usr/bin/blkid -p -s PART_ENTRY_TYPE -o value "$installer_partition") == ${installer_type,,} ]] || fail "setup GPT contract differs"

stage=format-exact-gpt-targets
/usr/bin/mkfs.ntfs -F -Q -L APXWINTARGET "$windows_partition" >/dev/null
/usr/bin/mkfs.fat -F 32 -n APXWINSETUP -i A9F25E31 "$installer_partition"
[[ $(/usr/bin/blkid -s TYPE -o value "$windows_partition") == ntfs \
        && $(/usr/bin/blkid -s LABEL -o value "$windows_partition") == APXWINTARGET ]] || fail "Windows target format differs"
[[ $(/usr/bin/blkid -s TYPE -o value "$installer_partition") == vfat \
        && $(/usr/bin/blkid -s LABEL -o value "$installer_partition") == APXWINSETUP ]] || fail "setup format differs"

stage=populate-targets
/usr/bin/mkdir -p "$windows_mount" "$installer_mount"
/usr/bin/mount -t ntfs3 -o rw "$windows_partition" "$windows_mount"
/usr/bin/mount -t vfat -o rw,fmask=0022,dmask=0022 "$installer_partition" "$installer_mount"
/usr/bin/bsdtar -cf - --exclude='./sources/install.wim' --exclude='./sources/boot.wim' -C "$iso_mount" . \
    | /usr/bin/bsdtar -xf - --no-same-owner --no-same-permissions -C "$installer_mount"
/usr/bin/install -m 0644 "$staging/boot.wim" "$installer_mount/sources/boot.wim"
/usr/bin/wimlib-imagex split "$iso_mount/sources/install.wim" "$installer_mount/sources/install.swm" 3800 --check

/usr/bin/install -d -m 0755 "$windows_mount/APX" "$installer_mount/APX/Payload/ReturnToHub" \
    "$installer_mount/APX/Drivers/Realtek8852AE" /boot/EFI/APX/native-windows
/usr/bin/install -m 0644 "$contract" "$windows_mount/APX/install-contract-v2.ini"
/usr/bin/install -m 0644 "$contract" "$installer_mount/APX/install-contract-v2.ini"
/usr/bin/install -m 0644 "$contract" /boot/EFI/APX/native-windows/install-contract-v2.ini
for source in APX-ReturnToHub.ps1 APX-ReturnToHub.vbs APX-ProvisionHardware.cmd README.txt; do
    /usr/bin/install -m 0644 "$return_source/$source" "$installer_mount/APX/Payload/ReturnToHub/$source"
done
for source in netrtwlane6.cat netrtwlane6.inf rtldata60.txt rtwlane6.sys; do
    /usr/bin/install -m 0644 "$driver_source/$source" "$installer_mount/APX/Drivers/Realtek8852AE/$source"
done
/usr/bin/sync
[[ -f $installer_mount/efi/boot/bootx64.efi \
        && -f $installer_mount/sources/install.swm \
        && -f $installer_mount/sources/install2.swm \
        && -f $installer_mount/sources/install3.swm ]] || fail "split installer contents differ"
/usr/bin/sbverify --list "$installer_mount/efi/boot/bootx64.efi" | /usr/bin/grep -F 'Microsoft' >/dev/null
/usr/bin/cmp -s "$contract" "$windows_mount/APX/install-contract-v2.ini"
/usr/bin/cmp -s "$contract" "$installer_mount/APX/install-contract-v2.ini"
/usr/bin/cmp -s "$contract" /boot/EFI/APX/native-windows/install-contract-v2.ini
/usr/bin/cmp -s "$return_source/APX-ReturnToHub.ps1" "$installer_mount/APX/Payload/ReturnToHub/APX-ReturnToHub.ps1"
/usr/bin/cmp -s "$driver_source/netrtwlane6.inf" "$installer_mount/APX/Drivers/Realtek8852AE/netrtwlane6.inf"
cleanup_mounts

stage=firmware-entry
/usr/bin/efibootmgr --create --disk "$disk" --part 4 --label 'APX Windows Setup' --loader '\EFI\BOOT\BOOTX64.EFI'
setup_entry=$(/usr/bin/efibootmgr | /usr/bin/awk '/APX Windows Setup/ {value=substr($1,5,4)} END {print value}')
[[ $setup_entry =~ ^[0-9A-F]{4}$ ]] || fail "setup firmware entry differs"
/usr/bin/efibootmgr -v | /usr/bin/grep -Fiq "Boot${setup_entry}* APX Windows Setup" || fail "setup firmware path differs"
[[ -z $(/usr/bin/efibootmgr | /usr/bin/awk '/^BootNext:/ {print}') ]] \
    || fail "installer preparation unexpectedly armed BootNext"

stage=prepared-marker
/usr/bin/python3 - "$prepared_marker" "$generation" "$size_gib" "$setup_entry" <<'PY'
import json
import os
from pathlib import Path
import sys

path = Path(sys.argv[1]); temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
value = {
    "schema": 2, "profile": "apx-native-windows-installer-prepared-v2",
    "generation": sys.argv[2], "size_gib": int(sys.argv[3]), "setup_entry": sys.argv[4],
    "windows_partuuid": "099C31D8-313A-4ABA-B0E0-2B59502C9674",
    "windows_esp_partuuid": "9625F250-9ACC-453A-AE63-0C863ADE440F",
    "setup_partuuid": "309BEBB6-5C32-4E21-9C92-6D758E51389D",
}
descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o400)
try:
    os.write(descriptor, (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode())
    os.fsync(descriptor)
finally:
    os.close(descriptor)
os.replace(temporary, path)
PY
/usr/bin/sfdisk --dump "$disk" >"$backup/gpt-after.sfdisk"
/usr/bin/efibootmgr -v >"$backup/efibootmgr-after.txt"
/usr/bin/cp -- "$contract" "$backup/install-contract-v2.ini"
/usr/bin/printf '%s\n' "$setup_entry" >"$backup/setup-entry.txt"
/usr/bin/find "$staging" -depth -delete
/usr/bin/chmod 0600 "$backup"/*
/usr/bin/sync
trap - ERR
trap - EXIT
/usr/bin/printf 'APX Windows installer v2 ready without reboot: Boot%s\n' "$setup_entry"
