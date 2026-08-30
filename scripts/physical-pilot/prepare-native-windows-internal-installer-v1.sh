#!/usr/bin/bash
set -euo pipefail

readonly repository=/root/apx-host-development-mode-v1/apx
readonly disk=/dev/nvme0n1
readonly installer_partition=/dev/nvme0n1p3
readonly iso=/var/lib/apx/package-artifacts/system-images-v1/windows11.iso
readonly iso_sha256=c74c96aa06e2548f14c76b5fd6600514c0d4f6eb05a731e4272ab005e8f48ce3
readonly installer_start=981340160
readonly installer_size=18874368
readonly installer_uuid=309BEBB6-5C32-4E21-9C92-6D758E51389D
readonly installer_type=C12A7328-F81F-11D2-BA4B-00A0C93EC93B
readonly iso_mount=/run/apx-windows-iso
readonly installer_mount=/run/apx-windows-internal-installer
readonly backup=/var/lib/apx/backups/20260825-native-windows-internal-installer-v5
readonly maintenance_uki=/boot/EFI/APX/apx-native-windows-maintenance-v1.efi
readonly maintenance_entry=/boot/loader/entries/apx-native-windows-maintenance-v1.conf
stage=0

fail() { /usr/bin/printf 'APX internal Windows installer refused: %s\n' "$1" >&2; exit 2; }
[[ $(/usr/bin/id -u) == 0 ]] || fail "root is required"
[[ $PWD == "$repository" ]] || fail "repository differs"
[[ $(< /etc/hostname) == apx-host ]] || fail "hostname differs"
[[ $(< /sys/class/dmi/id/product_name) == 82JU ]] || fail "Lenovo identity differs"
/usr/bin/grep -Fxq 'profile=apx-physical-headless-pilot-v1' /etc/apx-physical-pilot || fail "pilot marker differs"
[[ $(< /sys/class/power_supply/ADP0/online) == 1 ]] || fail "AC adapter is required"
[[ $(< /sys/class/power_supply/BAT0/capacity) -ge 40 ]] || fail "battery charge is below 40%"
[[ $(/usr/bin/xargs < /sys/block/nvme0n1/device/serial) == S4DYNX0R253702 ]] || fail "disk serial differs"
[[ $(/usr/bin/sfdisk --disk-id "$disk") == AC9FC0BD-2162-43A9-AAE6-3F654FF6F275 ]] || fail "GPT identity differs"
[[ $(< /boot/EFI/APX/recovery/windows-storage-maintenance-v1.status) == success:128849354240 ]] || fail "storage success marker differs"
[[ $(/usr/bin/blockdev --getsize64 /dev/nvme0n1p2) == 382186029056 ]] || fail "APX partition size differs"
[[ $(/usr/bin/cryptsetup status cryptroot | /usr/bin/awk '$1 == "size:" {print $2}') == 746424320 ]] || fail "dm-crypt size differs"
[[ -f $iso && ! -L $iso && $(/usr/bin/stat -c %s "$iso") == 8382230528 ]] || fail "installer ISO identity differs"
[[ $(/usr/bin/sha256sum "$iso" | /usr/bin/awk '{print $1}') == "$iso_sha256" ]] || fail "installer ISO digest differs"
for binary in /usr/bin/bsdtar /usr/bin/efibootmgr /usr/bin/mkfs.fat /usr/bin/partx /usr/bin/sbverify /usr/bin/wimlib-imagex; do
    [[ -x $binary && ! -L $binary ]] || fail "required tool differs: $binary"
done
[[ ! -e $backup && ! -e $installer_partition ]] || fail "installer preparation already exists"
[[ ! -e $iso_mount && ! -e $installer_mount ]] || fail "mount staging path already exists"
[[ -f $maintenance_uki && ! -L $maintenance_uki && -f $maintenance_entry && ! -L $maintenance_entry ]] \
    || fail "completed maintenance artifacts differ"
/usr/bin/python3 - "$disk" <<'PY' || fail "reserved GPT tail differs"
import json
import subprocess
import sys

table = json.loads(subprocess.run(
    ("/usr/bin/sfdisk", "--json", sys.argv[1]), check=True, text=True, capture_output=True,
).stdout)["partitiontable"]
parts = table["partitions"]
assert table["id"] == "AC9FC0BD-2162-43A9-AAE6-3F654FF6F275"
assert len(parts) == 2
assert (parts[1]["start"], parts[1]["size"], parts[1]["uuid"]) == (
    2099200, 746457088, "8835C8F0-F02F-4FC2-9035-5DBBC191DF9E",
)
assert parts[1]["start"] + parts[1]["size"] == 748556288
assert table["lastlba"] == 1000215182
PY
/usr/bin/sfdisk --no-act --append --wipe never "$disk" <<EOF >/dev/null
start=$installer_start, size=$installer_size, type=$installer_type, uuid=$installer_uuid, name="APX_WINSETUP"
EOF

/usr/bin/install -d -m 0700 "$backup"
/usr/bin/sfdisk --dump "$disk" >"$backup/gpt-before.sfdisk"
/usr/bin/sfdisk --backup-pt-sectors -O "$backup/gpt" "$disk" >/dev/null
/usr/bin/efibootmgr -v >"$backup/efibootmgr-before.txt"
/usr/bin/sha256sum "$iso" >"$backup/windows11.iso.sha256"
/usr/bin/install -m 0644 -- "$maintenance_uki" "$backup/apx-native-windows-maintenance-v1.efi"
/usr/bin/install -m 0644 -- "$maintenance_entry" "$backup/apx-native-windows-maintenance-v1.conf"
/usr/bin/sha256sum "$maintenance_uki" "$maintenance_entry" >"$backup/maintenance-before-removal.sha256"

rollback() {
    failed_line="$1"
    failed_command="$2"
    trap - ERR
    if /usr/bin/mountpoint -q "$installer_mount"; then /usr/bin/umount "$installer_mount" || true; fi
    if /usr/bin/mountpoint -q "$iso_mount"; then /usr/bin/umount "$iso_mount" || true; fi
    /usr/bin/rmdir "$installer_mount" "$iso_mount" 2>/dev/null || true
    /usr/bin/printf 'stage=%s line=%s command=%s\n' "$stage" "$failed_line" "$failed_command" \
        >"$backup/failure.txt" || true
    if (( stage >= 4 )); then
        fail "validation failed at line $failed_line; the completed media was preserved for inspection"
    fi
    if (( stage >= 2 )); then /usr/bin/partx --delete --nr 3 "$disk" || true; fi
    if (( stage >= 1 )); then
        /usr/bin/sfdisk --delete --no-reread --no-tell-kernel "$disk" 3 || true
        /usr/bin/sync || true
    fi
    fail "preparation failed; only the new installer partition was rolled back"
}
trap 'rollback "$LINENO" "$BASH_COMMAND"' ERR

/usr/bin/sfdisk --append --no-reread --no-tell-kernel --wipe never "$disk" <<EOF >/dev/null
start=$installer_start, size=$installer_size, type=$installer_type, uuid=$installer_uuid, name="APX_WINSETUP"
EOF
stage=1
/usr/bin/partx --add --nr 3 "$disk"
stage=2
[[ $(/usr/bin/blockdev --getsize64 "$installer_partition") == 9663676416 ]]
/usr/bin/mkfs.fat -F 32 -n APXWINSETUP -i A9F25E31 "$installer_partition"
stage=3

/usr/bin/mkdir -p "$iso_mount" "$installer_mount"
/usr/bin/mount -o loop,ro "$iso" "$iso_mount"
/usr/bin/mount -t vfat -o rw,fmask=0022,dmask=0022 "$installer_partition" "$installer_mount"
/usr/bin/bsdtar -cf - --exclude='./sources/install.wim' -C "$iso_mount" . \
    | /usr/bin/bsdtar -xf - --no-same-owner --no-same-permissions -C "$installer_mount"
[[ ! -e $installer_mount/sources/install.wim ]]
/usr/bin/wimlib-imagex split "$iso_mount/sources/install.wim" \
    "$installer_mount/sources/install.swm" 3800 --check
/usr/bin/sync
stage=4

[[ -f $installer_mount/efi/boot/bootx64.efi ]]
[[ -f $installer_mount/sources/boot.wim ]]
[[ -f $installer_mount/sources/install.swm ]]
[[ -f $installer_mount/sources/install2.swm ]]
[[ -f $installer_mount/sources/install3.swm ]]
[[ $(/usr/bin/find "$installer_mount" -type f -size +4294967295c -print -quit) == '' ]]
/usr/bin/sbverify --list "$installer_mount/efi/boot/bootx64.efi" \
    | /usr/bin/grep -F 'Microsoft Windows Production PCA 2011' >/dev/null
/usr/bin/wimlib-imagex info "$installer_mount/sources/install.swm" \
    | /usr/bin/grep -F 'Image Count:    11' >/dev/null
/usr/bin/sha256sum "$installer_mount/efi/boot/bootx64.efi" \
    "$installer_mount/sources/boot.wim" >"$backup/installer-key-files.sha256"
/usr/bin/df -B1 "$installer_mount" >"$backup/installer-usage.txt"
/usr/bin/umount "$installer_mount"
/usr/bin/umount "$iso_mount"
/usr/bin/rmdir "$installer_mount" "$iso_mount"
/usr/bin/sfdisk --dump "$disk" >"$backup/gpt-after.sfdisk"
/usr/bin/sync
trap - ERR
/usr/bin/unlink "$maintenance_uki"
/usr/bin/unlink "$maintenance_entry"
/usr/bin/sync
/usr/bin/printf 'APX internal Windows installer ready: 111 GiB target + 9 GiB APX_WINSETUP.\n'
