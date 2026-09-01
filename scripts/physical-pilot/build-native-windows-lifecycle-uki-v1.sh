#!/usr/bin/bash
set -euo pipefail

readonly assets=/usr/share/apx/native-windows-lifecycle-v1
readonly action="${1:-}"
readonly size_gib="${2:-}"
readonly generation="${3:-}"
readonly hook_source="$assets/apx_native_windows_lifecycle"
readonly hook_target=/etc/initcpio/install/apx_native_windows_lifecycle
readonly config="$assets/apx-native-windows-lifecycle-v1.mkinitcpio.conf"
readonly entry_source="$assets/apx-native-windows-lifecycle-v1.entry.conf"
readonly entry_target=/boot/loader/entries/apx-native-windows-lifecycle-v1.conf
readonly uki_target=/boot/EFI/APX/apx-native-windows-lifecycle-v1.efi
readonly backup="/var/lib/apx/backups/native-windows-lifecycle-$generation-$(/usr/bin/date -u +%Y%m%dT%H%M%SZ)-$$"
readonly staging_dir=/var/lib/apx/tmp
readonly cmdline="$staging_dir/native-windows-lifecycle-$generation.cmdline"
readonly staged_uki="$staging_dir/native-windows-lifecycle-$generation.efi"
readonly esp_temporary="${uki_target}.tmp.$$"
replacement_started=0

fail() { /usr/bin/printf 'APX Windows lifecycle UKI build refused: %s\n' "$1" >&2; exit 2; }
[[ $(/usr/bin/id -u) == 0 ]] || fail "root is required"
[[ $action == create || $action == delete ]] || fail "action differs"
[[ $size_gib == 80 || $size_gib == 120 || $size_gib == 160 ]] || fail "size differs"
[[ $generation =~ ^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$ ]] || fail "generation differs"
[[ $(< /etc/hostname) == apx-host && $(< /sys/class/dmi/id/product_name) == 82JU ]] || fail "computer identity differs"
/usr/bin/grep -Fxq 'profile=apx-physical-headless-pilot-v1' /etc/apx-physical-pilot || fail "pilot marker differs"
[[ $(< /sys/class/power_supply/ADP0/online) == 1 ]] || fail "AC adapter is required"
[[ $(< /sys/class/power_supply/BAT0/capacity) -ge 40 ]] || fail "battery charge is below 40%"
[[ $(/usr/bin/xargs < /sys/block/nvme0n1/device/serial) == S4DYNX0R253702 ]] || fail "disk serial differs"
[[ $(/usr/bin/sfdisk --disk-id /dev/nvme0n1) == AC9FC0BD-2162-43A9-AAE6-3F654FF6F275 ]] || fail "GPT identity differs"
[[ $(/usr/bin/stat -c %a /etc/kernel/secure-boot-private-key.pem) == 600 ]] || fail "Secure Boot key mode differs"
[[ ! -e $backup && ! -e $cmdline && ! -e $staged_uki && ! -e $esp_temporary ]] || fail "staging already exists"
[[ ! -e $hook_target && ! -e $entry_target && ! -e $uki_target ]] || fail "another maintenance image exists"
for source in "$hook_source" "$config" "$entry_source" \
        "$assets/apx-native-windows-lifecycle-initrd-v1.sh" \
        "$assets/apx-native-windows-lifecycle-v1.service"; do
    [[ -f $source && ! -L $source \
            && $(/usr/bin/stat -c '%U:%G' "$source") == root:root ]] \
        || fail "source differs: $source"
done
[[ $(/usr/bin/df -B1 --output=avail /boot | /usr/bin/tail -n1) -ge 250000000 ]] || fail "ESP free space is too low"
/usr/bin/bash -n "$hook_source" || fail "build hook does not parse"
/usr/bin/sh -n "$assets/apx-native-windows-lifecycle-initrd-v1.sh" || fail "initrd executor does not parse"

/usr/bin/install -d -m 0700 "$backup" "$staging_dir"
/usr/bin/sfdisk --dump /dev/nvme0n1 >"$backup/gpt-before.sfdisk"
/usr/bin/efibootmgr -v >"$backup/efibootmgr-before.txt"
/usr/bin/sha256sum /boot/EFI/APX/apx-system-v1.efi /boot/loader/loader.conf >"$backup/boot-before.sha256"
/usr/bin/install -m 0600 /dev/null "$cmdline"
/usr/bin/printf '%s\n' \
    "rd.luks.name=3ad5fc06-c4eb-4bb2-936b-f75eff3bc1c4=cryptroot root=/dev/mapper/cryptroot rootflags=subvol=@ rw rd.plymouth=0 plymouth.enable=0 rd.systemd.show_status=1 systemd.show_status=1 systemd.journald.forward_to_console=1 apx.native_windows_lifecycle=1 apx.native_windows_action=$action apx.native_windows_size_gib=$size_gib apx.native_windows_generation=$generation" \
    >"$cmdline"

rollback() {
    trap - ERR
    /usr/bin/rm -f -- "$cmdline" "$staged_uki" "$esp_temporary" "$hook_target"
    if [[ $replacement_started == 1 ]]; then
        /usr/bin/rm -f -- "$uki_target" "$entry_target"
    fi
    fail "maintenance UKI build failed; temporary artifacts were removed"
}
trap rollback ERR
/usr/bin/install -d -m 0755 /etc/initcpio/install
/usr/bin/install -m 0644 -o root -g root -- "$hook_source" "$hook_target"
/usr/bin/mkinitcpio --nopost -n -c "$config" -k "$(/usr/bin/uname -r)" \
    -U "$staged_uki" --cmdline "$cmdline" --ukiconfig /etc/kernel/uki.conf
/usr/bin/chmod 0644 "$staged_uki"
/usr/bin/sbverify --list "$staged_uki" | /usr/bin/grep -Fq 'signature certificates' || fail "maintenance UKI is not signed"
/usr/bin/ukify inspect "$staged_uki" | /usr/bin/grep -Fq "apx.native_windows_action=$action" || fail "embedded action differs"
/usr/bin/ukify inspect "$staged_uki" | /usr/bin/grep -Fq "apx.native_windows_size_gib=$size_gib" || fail "embedded size differs"
/usr/bin/ukify inspect "$staged_uki" | /usr/bin/grep -Fq "apx.native_windows_generation=$generation" || fail "embedded generation differs"
replacement_started=1
/usr/bin/install -m 0644 -- "$staged_uki" "$esp_temporary"
/usr/bin/mv -Tf -- "$esp_temporary" "$uki_target"
/usr/bin/install -m 0644 -o root -g root -- "$entry_source" "$entry_target"
/usr/bin/rm -f -- "$hook_target" "$staged_uki" "$cmdline"
/usr/bin/bootctl list --no-pager --json=short | /usr/bin/grep -Fq 'apx-native-windows-lifecycle-v1.conf' || fail "maintenance boot entry is not published"
/usr/bin/sha256sum "$uki_target" "$entry_target" >"$backup/maintenance.sha256"
/usr/bin/chmod 0600 "$backup"/*.txt "$backup"/*.sha256 "$backup"/*.sfdisk
/usr/bin/sync
trap - ERR
/usr/bin/printf 'APX Windows lifecycle UKI ready: action=%s size=%s generation=%s\n' "$action" "$size_gib" "$generation"
