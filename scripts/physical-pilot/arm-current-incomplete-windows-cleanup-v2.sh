#!/usr/bin/env bash
set -Eeuo pipefail

readonly repository=/root/apx-host-development-mode-v1/apx
readonly disk=/dev/nvme0n1
readonly windows=/dev/nvme0n1p3
readonly setup=/dev/nvme0n1p4
readonly pending=/var/lib/apx/native-environments/windows-pending.json
readonly original_windows_uuid=EAA7CDAF-EDF0-46BE-A6E3-D817D027BE64
readonly generation=9a73467f-3f59-47a2-8d47-57518c187b60
readonly initrd_asset=/usr/share/apx/native-windows-lifecycle-v1/apx-native-windows-lifecycle-initrd-v1.sh
readonly entry=apx-native-windows-lifecycle-v1.conf
readonly uki=/boot/EFI/APX/apx-native-windows-lifecycle-v1.efi
readonly entry_file=/boot/loader/entries/apx-native-windows-lifecycle-v1.conf
readonly backup="/var/lib/apx/backups/$(date -u +%Y%m%dT%H%M%SZ)-incomplete-windows-cleanup-v2"
readonly audit_mount=/run/apx-incomplete-windows-cleanup-v2
changed_pending=0
built=0
removed_old_maintenance=0
changed_initrd_asset=0

fail() { echo "APX incomplete Windows cleanup refused: $*" >&2; exit 1; }
[[ $EUID -eq 0 && $PWD == "$repository" ]] || fail "root or repository differs"
[[ $(</etc/hostname) == apx-host && $(</sys/class/dmi/id/product_name) == 82JU ]] || fail "Host identity differs"
[[ $(</sys/class/power_supply/ADP0/online) == 1 && $(</sys/class/power_supply/BAT0/capacity) -ge 40 ]] || fail "power differs"
[[ $(/usr/bin/xargs </sys/block/nvme0n1/device/serial) == S4DYNX0R253702 ]] || fail "disk serial differs"
[[ $(/usr/bin/blockdev --getsize64 "$disk") == 512110190592 \
        && $(/usr/bin/sfdisk --disk-id "$disk") == AC9FC0BD-2162-43A9-AAE6-3F654FF6F275 ]] || fail "disk identity differs"
[[ $(/usr/bin/efibootmgr | /usr/bin/awk '/^BootCurrent:/ {print $2}') == 0005 \
        && -z $(/usr/bin/efibootmgr | /usr/bin/awk '/^BootNext:/ {print}') ]] || fail "firmware state differs"
[[ ! -e /run/apx/environment-management-v1.lock && -f $uki && ! -L $uki \
        && -f $entry_file && ! -L $entry_file ]] || fail "the expected failed maintenance artifact is absent"
[[ -f $initrd_asset && ! -L $initrd_asset \
        && $(/usr/bin/sha256sum "$initrd_asset" | /usr/bin/awk '{print $1}') \
        == $(/usr/bin/sha256sum "$repository/scripts/physical-pilot/apx-native-windows-lifecycle-initrd-v1.sh" | /usr/bin/awk '{print $1}') ]] \
    || fail "the installed strict lifecycle executor differs"
old_cmdline=$(/usr/bin/objcopy -O binary --only-section=.cmdline "$uki" /dev/stdout | /usr/bin/tr -d '\0')
[[ $old_cmdline == *"apx.native_windows_action=create"* \
        && $old_cmdline == *"apx.native_windows_size_gib=120"* \
        && $old_cmdline == *"apx.native_windows_generation=$generation"* \
        && $(<"$entry_file") == $'title APX Windows Lifecycle Maintenance\nefi /EFI/APX/apx-native-windows-lifecycle-v1.efi' ]] \
    || fail "the failed maintenance artifact identity differs"
/usr/bin/sbverify --list "$uki" | /usr/bin/grep -F 'SecureBoot signing key on host apx-host' >/dev/null \
    || fail "the failed maintenance artifact signature differs"
[[ -f $pending && ! -L $pending && $(/usr/bin/stat -c '%U:%G:%a' "$pending") == root:root:400 ]] || fail "pending metadata differs"
/usr/bin/python3 - "$pending" "$generation" <<'PY' || fail "pending create identity differs"
import json
import sys
value = json.load(open(sys.argv[1], encoding="utf-8"))
if value.get("profile") != "apx-native-windows-pending-v1" or value.get("schema") != 1 \
        or value.get("action") != "create" or value.get("stage") != "installing" \
        or value.get("generation") != sys.argv[2] or value.get("requested_size_gib") != 120:
    raise SystemExit(1)
PY
[[ $(/usr/bin/blockdev --getsize64 /dev/nvme0n1p2) == 382186029056 ]] || fail "APX reserved size differs"
[[ $(/usr/bin/cat /sys/class/block/nvme0n1p3/start) == 748556288 \
        && $(/usr/bin/blockdev --getsz "$windows") == 232783872 \
        && $(/usr/bin/blkid -p -s PART_ENTRY_TYPE -o value "$windows") == ebd0a0a2-b9e5-4433-87c0-68b6b72699c7 \
        && $(/usr/bin/blkid -p -s PART_ENTRY_UUID -o value "$windows") == ${original_windows_uuid,,} \
        && $(/usr/bin/blkid -s TYPE -o value "$windows") == ntfs \
        && $(/usr/bin/blkid -s LABEL -o value "$windows") == windows ]] || fail "incomplete Windows partition differs"
[[ $(/usr/bin/cat /sys/class/block/nvme0n1p4/start) == 981340160 \
        && $(/usr/bin/blockdev --getsz "$setup") == 18874368 \
        && $(/usr/bin/blkid -p -s PART_ENTRY_TYPE -o value "$setup") == c12a7328-f81f-11d2-ba4b-00a0c93ec93b \
        && $(/usr/bin/blkid -p -s PART_ENTRY_UUID -o value "$setup") == 309bebb6-5c32-4e21-9c92-6d758e51389d \
        && $(/usr/bin/blkid -s TYPE -o value "$setup") == vfat \
        && $(/usr/bin/blkid -s LABEL -o value "$setup") == APXWINSETUP ]] || fail "installer partition differs"
[[ ! -b /dev/nvme0n1p5 && ! -b /dev/nvme0n1p6 ]] || fail "unexpected tail partitions exist"
[[ $(/usr/bin/blkid -s PARTUUID -o value /dev/nvme0n1p1) == 9625f250-9acc-453a-ae63-0c863ade440f \
        && -f /boot/EFI/systemd/systemd-bootx64.efi \
        && -f /boot/EFI/Microsoft/Boot/bootmgfw.efi \
        && -f /boot/EFI/Microsoft/Boot/BCD ]] || fail "shared APX EFI differs"

/usr/bin/mkdir -p "$audit_mount"
/usr/bin/mount -t ntfs3 -o ro,nosuid,nodev,noexec "$windows" "$audit_mount"
[[ -f $audit_mount/Windows/System32/winload.efi \
        && -d $audit_mount/Users/defaultuser0 \
        && ! -e $audit_mount/ProgramData/APX/ReturnToHub/APX-ReturnToHub.ps1 ]] || {
    /usr/bin/umount "$audit_mount"; /usr/bin/rmdir "$audit_mount"; fail "incomplete OOBE evidence differs";
}
/usr/bin/umount "$audit_mount"
/usr/bin/rmdir "$audit_mount"

/usr/bin/install -d -o root -g root -m 0700 "$backup"
/usr/bin/sfdisk --dump "$disk" >"$backup/gpt-before.sfdisk"
/usr/bin/efibootmgr -v >"$backup/efibootmgr-before.txt"
/usr/bin/cp --archive -- "$pending" "$backup/windows-pending.before.json"
/usr/bin/cp --archive -- "$uki" "$backup/create-maintenance.before.efi"
/usr/bin/cp --archive -- "$entry_file" "$backup/create-maintenance.before.conf"
/usr/bin/cp --archive -- "$initrd_asset" "$backup/strict-initrd.before.sh"
/usr/bin/sha256sum /boot/EFI/Microsoft/Boot/bootmgfw.efi /boot/EFI/Microsoft/Boot/BCD >"$backup/windows-efi-before.sha256"

rollback() {
    set +e
    /usr/bin/bootctl set-oneshot apx-secure-boot-v1.conf
    (( built )) && { /usr/bin/unlink "$uki"; /usr/bin/unlink "$entry_file"; }
    (( removed_old_maintenance )) && {
        /usr/bin/cp --archive -- "$backup/create-maintenance.before.efi" "$uki"
        /usr/bin/cp --archive -- "$backup/create-maintenance.before.conf" "$entry_file"
    }
    (( changed_pending )) && /usr/bin/cp --archive -- "$backup/windows-pending.before.json" "$pending"
    (( changed_initrd_asset )) && /usr/bin/cp --archive -- "$backup/strict-initrd.before.sh" "$initrd_asset"
}
trap rollback ERR

/usr/bin/unlink "$uki"
/usr/bin/unlink "$entry_file"
removed_old_maintenance=1

/usr/bin/python3 - "$pending" "$generation" <<'PY'
import json
import os
from pathlib import Path
import sys
path = Path(sys.argv[1]); old = json.loads(path.read_bytes())
value = {
    "schema": 1, "profile": "apx-native-windows-pending-v1", "action": "delete",
    "stage": "maintenance", "name": "windows", "generation": sys.argv[2],
    "requested_size_gib": 120, "created_at": old["created_at"],
}
temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o400)
try:
    os.write(descriptor, (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode())
    os.fsync(descriptor)
finally:
    os.close(descriptor)
os.replace(temporary, path)
PY
changed_pending=1

/usr/bin/sed \
    -e 's/099c31d8-313a-4aba-b0e0-2b59502c9674/eaa7cdaf-edf0-46be-a6e3-d817d027be64/' \
    -e 's/)" = APXWINTARGET || fail windows-label/)" = windows || fail windows-label/' \
    "$backup/strict-initrd.before.sh" >"$backup/exact-incomplete-initrd.sh"
[[ $(/usr/bin/grep -Fc 'eaa7cdaf-edf0-46be-a6e3-d817d027be64' "$backup/exact-incomplete-initrd.sh") == 1 \
        && $(/usr/bin/grep -Fc ')" = windows || fail windows-label' "$backup/exact-incomplete-initrd.sh") == 1 \
        && $(/usr/bin/grep -Fc '099c31d8-313a-4aba-b0e0-2b59502c9674' "$backup/exact-incomplete-initrd.sh") == 0 \
        && $(/usr/bin/grep -Fc ')" = APXWINTARGET || fail windows-label' "$backup/exact-incomplete-initrd.sh") == 0 ]] \
    || fail "the exact one-time initrd transformation differs"
/usr/bin/install -o root -g root -m 0755 "$backup/exact-incomplete-initrd.sh" "$initrd_asset"
changed_initrd_asset=1
/usr/lib/apx/build-native-windows-lifecycle-uki-v1.sh delete 120 "$generation"
built=1
/usr/bin/cp --archive -- "$backup/strict-initrd.before.sh" "$initrd_asset"
changed_initrd_asset=0
/usr/bin/objcopy -O binary --only-section=.initrd "$uki" "$backup/delete-initrd.img"
/usr/bin/mkdir "$backup/extracted-initrd"
(cd "$backup/extracted-initrd" && /usr/bin/lsinitcpio -x --cpio "$backup/delete-initrd.img")
/usr/bin/cmp -- "$backup/exact-incomplete-initrd.sh" "$backup/extracted-initrd/usr/bin/apx-native-windows-lifecycle-initrd-v1"
/usr/bin/sbverify --list "$uki" | /usr/bin/grep -F 'SecureBoot signing key on host apx-host' >/dev/null
/usr/bin/bootctl set-oneshot "$entry"
/usr/bin/bootctl status --no-pager | /usr/bin/grep -F "$entry" >/dev/null
/usr/bin/sfdisk --dump "$disk" >"$backup/gpt-armed.sfdisk"
/usr/bin/cp --archive -- "$pending" "$backup/windows-pending.armed.json"
/usr/bin/chown -R root:root "$backup"
/usr/bin/find "$backup" -type f -exec chmod 0600 {} +
trap - ERR
echo "APX exact cleanup is armed; backup: $backup"
