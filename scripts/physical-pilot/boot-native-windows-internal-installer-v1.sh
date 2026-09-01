#!/usr/bin/bash
set -euo pipefail

# Hardware-bound, one-shot handoff to the already prepared internal Windows
# installer. Nothing is added to the permanent BootOrder.
readonly repository=/root/apx-host-development-mode-v1/apx
readonly disk=/dev/nvme0n1
readonly installer_partition=/dev/nvme0n1p3
readonly installer_partuuid=309BEBB6-5C32-4E21-9C92-6D758E51389D
readonly installer_label='APX Windows Setup'
readonly installer_loader='\EFI\BOOT\BOOTX64.EFI'
readonly expected_boot_order=2001,0005,0000,2002,2003
readonly backup=/var/lib/apx/backups/20260825-native-windows-internal-installer-v5
readonly expected_bootx64=32b233afb2a8b4c517003796d435358dcad78e421a3ed386b8ee275a6957dbd0
readonly expected_boot_wim=b4041a17b34aca0db72e32eb1bcd7d675354f600d4b79efb2ab4a8af8dcb5df2
mount_dir=''
armed=0

fail() { /usr/bin/printf 'APX Windows installer boot refused: %s\n' "$1" >&2; exit 2; }
cleanup() {
    status=$?
    trap - EXIT INT TERM
    if [[ -n $mount_dir ]] && /usr/bin/mountpoint -q "$mount_dir"; then
        /usr/bin/umount "$mount_dir" || true
    fi
    [[ -z $mount_dir ]] || /usr/bin/rmdir "$mount_dir" 2>/dev/null || true
    if (( status != 0 && armed == 1 )); then
        /usr/bin/efibootmgr -N >/dev/null 2>&1 || true
    fi
    exit "$status"
}
trap cleanup EXIT INT TERM

[[ $# == 1 && ( $1 == --validate-only || $1 == --reboot ) ]] \
    || fail 'invoke with --validate-only or the exact --reboot confirmation'
readonly action=$1
[[ $(/usr/bin/id -u) == 0 ]] || fail 'root is required'
[[ $PWD == "$repository" ]] || fail 'repository differs'
[[ $(< /etc/hostname) == apx-host ]] || fail 'hostname differs'
[[ $(< /sys/class/dmi/id/product_name) == 82JU ]] || fail 'Lenovo identity differs'
/usr/bin/grep -Fxq 'profile=apx-physical-headless-pilot-v1' /etc/apx-physical-pilot \
    || fail 'physical-pilot marker differs'
[[ $(< /sys/class/power_supply/ADP0/online) == 1 ]] || fail 'AC adapter is required'
[[ $(< /sys/class/power_supply/BAT0/capacity) -ge 40 ]] || fail 'battery charge is below 40%'
[[ $(/usr/bin/xargs < /sys/block/nvme0n1/device/serial) == S4DYNX0R253702 ]] \
    || fail 'disk serial differs'
[[ $(/usr/bin/sfdisk --disk-id "$disk") == AC9FC0BD-2162-43A9-AAE6-3F654FF6F275 ]] \
    || fail 'GPT identity differs'
[[ $(/usr/bin/blockdev --getsize64 "$installer_partition") == 9663676416 ]] \
    || fail 'installer partition size differs'
[[ $(/usr/bin/blkid -s PARTUUID -o value "$installer_partition" | /usr/bin/tr '[:lower:]' '[:upper:]') == "$installer_partuuid" ]] \
    || fail 'installer partition identity differs'
[[ $(/usr/bin/blkid -s LABEL -o value "$installer_partition") == APXWINSETUP ]] \
    || fail 'installer filesystem label differs'
[[ $(/usr/bin/bootctl is-installed) == yes ]] || fail 'APX boot manager is not installed'
[[ $(/usr/bin/bootctl status 2>/dev/null | /usr/bin/awk -F': ' '/Secure Boot:/ {print $2; exit}') == enabled* ]] \
    || fail 'Secure Boot is not enabled'
[[ $(/usr/bin/efibootmgr | /usr/bin/awk -F': ' '/^BootCurrent:/ {print $2}') == 0005 ]] \
    || fail 'the current boot is not the APX Linux Boot Manager'
[[ $(/usr/bin/efibootmgr | /usr/bin/awk -F': ' '/^BootOrder:/ {print $2}') == "$expected_boot_order" ]] \
    || fail 'permanent BootOrder differs'
! /usr/bin/efibootmgr | /usr/bin/grep -q '^BootNext:' || fail 'another one-shot boot is already armed'

entry_line=$(/usr/bin/efibootmgr -v | /usr/bin/grep -F "$installer_label" || true)
[[ $(/usr/bin/printf '%s\n' "$entry_line" | /usr/bin/grep -c '^Boot[0-9A-Fa-f]\{4\}\* APX Windows Setup') == 1 ]] \
    || fail 'installer UEFI entry is missing or ambiguous'
[[ $entry_line == *"HD(3,GPT,${installer_partuuid,,}"* && $entry_line == *"$installer_loader"* ]] \
    || fail 'installer UEFI path differs'
boot_number=${entry_line:4:4}

mount_dir=$(/usr/bin/mktemp -d /run/apx-windows-boot-verify.XXXXXX)
/usr/bin/mount -o ro "$installer_partition" "$mount_dir"
[[ $(/usr/bin/sha256sum "$mount_dir/efi/boot/bootx64.efi" | /usr/bin/awk '{print $1}') == "$expected_bootx64" ]] \
    || fail 'Windows EFI loader digest differs'
[[ $(/usr/bin/sha256sum "$mount_dir/sources/boot.wim" | /usr/bin/awk '{print $1}') == "$expected_boot_wim" ]] \
    || fail 'Windows PE image digest differs'
signature=$(/usr/bin/sbverify --list "$mount_dir/efi/boot/bootx64.efi" 2>&1) \
    || fail 'Windows EFI signature could not be read'
[[ $signature == *'Microsoft Windows Production PCA 2011'* ]] \
    || fail 'Windows EFI signature differs'
for part in install.swm install2.swm install3.swm; do
    [[ -f $mount_dir/sources/$part && ! -L $mount_dir/sources/$part ]] \
        || fail "split Windows image is missing: $part"
done
/usr/bin/umount "$mount_dir"
/usr/bin/rmdir "$mount_dir"
mount_dir=''

if [[ $action == --validate-only ]]; then
    /usr/bin/printf 'APX internal Windows installer validated; no boot was armed.\n'
    exit 0
fi

/usr/bin/efibootmgr -n "$boot_number"
armed=1
[[ $(/usr/bin/efibootmgr | /usr/bin/awk -F': ' '/^BootNext:/ {print $2}') == "$boot_number" ]] \
    || fail 'one-shot installer boot could not be verified'
[[ $(/usr/bin/efibootmgr | /usr/bin/awk -F': ' '/^BootOrder:/ {print $2}') == "$expected_boot_order" ]] \
    || fail 'permanent BootOrder changed unexpectedly'
/usr/bin/efibootmgr -v >"$backup/efibootmgr-before-installer-reboot.txt"
/usr/bin/sync
/usr/bin/systemctl reboot
