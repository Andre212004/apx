#!/usr/bin/bash
set -euo pipefail

# Hardware-bound, one-shot handoff to the installed Windows OOBE. The
# permanent firmware order must keep APX Linux first.
readonly repository=/root/apx-host-development-mode-v1/apx
readonly disk=/dev/nvme0n1
readonly windows_partition=/dev/nvme0n1p4
readonly windows_partuuid=099C31D8-313A-4ABA-B0E0-2B59502C9674
readonly windows_esp=/dev/nvme0n1p6
readonly windows_esp_partuuid=309BEBB6-5C32-4E21-9C92-6D758E51389D
readonly windows_loader='\EFI\Microsoft\Boot\bootmgfw.efi'
readonly expected_order=0005,0006,0000,2001,2002,2003
readonly expected_manager=d15b56f8800fa95efeeb63fb7b0891176fd40e447c10e44c3619e079487cd599
readonly backup=/var/lib/apx/backups/20260825-native-windows-oobe-v1
mount_dir=''
armed=0

fail() { /usr/bin/printf 'APX Windows OOBE boot refused: %s\n' "$1" >&2; exit 2; }
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
[[ $(/usr/bin/blkid -s PARTUUID -o value "$windows_partition" | /usr/bin/tr '[:lower:]' '[:upper:]') == "$windows_partuuid" ]] \
    || fail 'Windows partition identity differs'
[[ $(/usr/bin/blockdev --getsize64 "$windows_partition") == 118339141632 ]] \
    || fail 'Windows partition size differs'
[[ $(/usr/bin/blkid -s PARTUUID -o value "$windows_esp" | /usr/bin/tr '[:lower:]' '[:upper:]') == "$windows_esp_partuuid" ]] \
    || fail 'Windows ESP identity differs'
[[ $(/usr/bin/blockdev --getsize64 "$windows_esp") == 9663676416 ]] \
    || fail 'Windows ESP size differs'
[[ $(/usr/bin/bootctl status 2>/dev/null | /usr/bin/awk -F': ' '/Secure Boot:/ {print $2; exit}') == enabled* ]] \
    || fail 'Secure Boot is not enabled'
[[ $(/usr/bin/efibootmgr | /usr/bin/awk -F': ' '/^BootCurrent:/ {print $2}') == 0005 ]] \
    || fail 'the current boot is not APX Linux'
[[ $(/usr/bin/efibootmgr | /usr/bin/awk -F': ' '/^BootOrder:/ {print $2}') == "$expected_order" ]] \
    || fail 'Linux is not the permanent first boot target'
! /usr/bin/efibootmgr | /usr/bin/grep -q '^BootNext:' || fail 'another one-shot boot is already armed'

entry_line=$(/usr/bin/efibootmgr -v | /usr/bin/grep -F 'Windows Boot Manager' || true)
[[ $(/usr/bin/printf '%s\n' "$entry_line" | /usr/bin/grep -c '^Boot[0-9A-Fa-f]\{4\}\* Windows Boot Manager') == 1 ]] \
    || fail 'Windows firmware entry is missing or ambiguous'
[[ $entry_line == *"HD(6,GPT,${windows_esp_partuuid,,}"* && $entry_line == *"$windows_loader"* ]] \
    || fail 'Windows firmware path differs'
boot_number=${entry_line:4:4}
[[ $boot_number == 0006 ]] || fail 'Windows firmware number differs'

mount_dir=$(/usr/bin/mktemp -d /run/apx-windows-oobe-verify.XXXXXX)
/usr/bin/mount -o ro,nosuid,nodev,noexec "$windows_esp" "$mount_dir"
[[ $(/usr/bin/sha256sum "$mount_dir/EFI/Microsoft/Boot/bootmgfw.efi" | /usr/bin/awk '{print $1}') == "$expected_manager" ]] \
    || fail 'Windows Boot Manager digest differs'
bcd="$mount_dir/EFI/Microsoft/Boot/BCD"
[[ -f $bcd && ! -L $bcd ]] || fail 'Windows BCD identity differs'
bcd_size=$(/usr/bin/stat -c %s "$bcd")
[[ $bcd_size -ge 16384 && $bcd_size -le 1048576 ]] || fail 'Windows BCD size differs'
bcd_hash=$(/usr/bin/sha256sum "$bcd" | /usr/bin/awk '{print $1}')
signature=$(/usr/bin/sbverify --list "$mount_dir/EFI/Microsoft/Boot/bootmgfw.efi" 2>&1) \
    || fail 'Windows Boot Manager signature cannot be read'
[[ $signature == *'Windows UEFI CA 2023'* ]] || fail 'Windows Boot Manager signer differs'
/usr/bin/umount "$mount_dir"

/usr/bin/mount -t ntfs3 -o ro,nosuid,nodev,noexec "$windows_partition" "$mount_dir"
[[ -f $mount_dir/Windows/System32/config/SYSTEM && ! -L $mount_dir/Windows/System32/config/SYSTEM ]] \
    || fail 'offline Windows identity differs'
declare -A driver_hashes=(
    [netrtwlane6.inf]=7742764146994bcf3660d8da874b941918b6e08db6cc3cd7c574afd3a6a9b901
    [netrtwlane6.cat]=3ed544c4860ff73d5a7e044a1bcc665a8527f8deb9fd6503cb356d91bd73c475
    [rtwlane6.sys]=be77de858665bd78680f67f96748337ac747704eb551fd552f14fbacb629abc1
    [rtldata60.txt]=32fe5fe472398feae62013b0b0f9c35f5ae273780c2a280e44634d75fbf20e64
)
for name in netrtwlane6.inf netrtwlane6.cat rtwlane6.sys rtldata60.txt; do
    path="$mount_dir/APX/Drivers/Realtek8852AE/$name"
    [[ -f $path && ! -L $path ]] || fail "staged Wi-Fi driver is missing: $name"
    [[ $(/usr/bin/sha256sum "$path" | /usr/bin/awk '{print $1}') == "${driver_hashes[$name]}" ]] \
        || fail "staged Wi-Fi driver digest differs: $name"
done
/usr/bin/umount "$mount_dir"
/usr/bin/rmdir "$mount_dir"
mount_dir=''

if [[ $action == --validate-only ]]; then
    /usr/bin/printf 'APX Windows OOBE target and offline Wi-Fi driver validated; no boot was armed.\n'
    exit 0
fi

if [[ ! -e $backup ]]; then
    /usr/bin/install -d -m 0700 "$backup"
else
    backup_stat=$(/usr/bin/stat -c '%U:%G:%a' "$backup")
    [[ -d $backup && ! -L $backup && $backup_stat == root:root:700 ]] \
        || fail 'OOBE evidence directory differs'
fi
evidence_prefix=''
for index in $(/usr/bin/seq -w 1 32); do
    candidate="$backup/handoff-$index"
    if (set -o noclobber; /usr/bin/efibootmgr -v >"$candidate-efibootmgr-before.txt") 2>/dev/null; then
        evidence_prefix=$candidate
        break
    fi
done
[[ -n $evidence_prefix ]] || fail 'OOBE evidence slots are exhausted'
/usr/bin/sfdisk --dump "$disk" >"$evidence_prefix-gpt.sfdisk"
/usr/bin/printf '%s  BCD\n' "$bcd_hash" >"$evidence_prefix-bcd.sha256"
/usr/bin/efibootmgr -n "$boot_number"
armed=1
[[ $(/usr/bin/efibootmgr | /usr/bin/awk -F': ' '/^BootNext:/ {print $2}') == "$boot_number" ]] \
    || fail 'one-shot Windows boot could not be verified'
[[ $(/usr/bin/efibootmgr | /usr/bin/awk -F': ' '/^BootOrder:/ {print $2}') == "$expected_order" ]] \
    || fail 'permanent Linux-first BootOrder changed unexpectedly'
/usr/bin/efibootmgr -v >"$evidence_prefix-efibootmgr-after.txt"
/usr/bin/sync
/usr/bin/systemctl reboot
