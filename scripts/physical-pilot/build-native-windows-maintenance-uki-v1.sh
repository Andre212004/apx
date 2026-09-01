#!/usr/bin/bash
set -euo pipefail

readonly repository=/root/apx-host-development-mode-v1/apx
readonly hook_source="$repository/config/initcpio/install/apx_native_windows_reserve"
readonly hook_target=/etc/initcpio/install/apx_native_windows_reserve
readonly config="$repository/config/mkinitcpio/apx-native-windows-maintenance-v1.conf"
readonly cmdline="$repository/config/kernel/apx-native-windows-maintenance-v1.cmdline"
readonly entry_source="$repository/config/systemd-boot/apx-native-windows-maintenance-v1.conf"
readonly entry_target=/boot/loader/entries/apx-native-windows-maintenance-v1.conf
readonly uki_target=/boot/EFI/APX/apx-native-windows-maintenance-v1.efi
readonly mode="${1:-initial}"
if [[ $mode == refresh ]]; then
    readonly backup="/var/lib/apx/backups/$(/usr/bin/date -u +%Y%m%dT%H%M%SZ)-native-windows-maintenance-uki-refresh"
else
    readonly backup=/var/lib/apx/backups/20260825-native-windows-maintenance-uki-v1
fi
readonly staging_dir=/var/lib/apx/tmp
staged_uki="$staging_dir/apx-native-windows-maintenance-v1.efi.tmp.$$"
esp_temporary="${uki_target}.tmp.$$"
replacement_started=0

fail() { /usr/bin/printf 'APX Windows maintenance UKI build refused: %s\n' "$1" >&2; exit 2; }
[[ $(/usr/bin/id -u) == 0 ]] || fail "root is required"
[[ $(< /etc/hostname) == apx-host ]] || fail "hostname differs"
[[ $(< /sys/class/dmi/id/product_name) == 82JU ]] || fail "Lenovo identity differs"
/usr/bin/grep -Fxq 'profile=apx-physical-headless-pilot-v1' /etc/apx-physical-pilot || fail "pilot marker differs"
[[ $PWD == "$repository" ]] || fail "repository differs"
[[ $(< /sys/class/power_supply/ADP0/online) == 1 ]] || fail "AC adapter is required"
[[ $(/usr/bin/xargs < /sys/block/nvme0n1/device/serial) == S4DYNX0R253702 ]] || fail "disk serial differs"
[[ $(/usr/bin/blockdev --getsize64 /dev/nvme0n1p2) == 511035383296 ]] || fail "partition is not at the original size"
[[ $(/usr/bin/cryptsetup status cryptroot | /usr/bin/awk '$1 == "size:" {print $2}') == 998083215 ]] || fail "dm-crypt size differs"
[[ $mode == initial || $mode == refresh ]] || fail "usage: $0 [refresh]"
[[ ! -e $backup && ! -e $hook_target ]] || fail "build staging artifacts already exist"
if [[ $mode == refresh ]]; then
    [[ -f $entry_target && ! -L $entry_target && -f $uki_target && ! -L $uki_target ]] \
        || fail "published maintenance artifacts are missing"
else
    [[ ! -e $entry_target && ! -e $uki_target ]] || fail "maintenance artifacts already exist; use refresh"
fi
[[ $(/usr/bin/stat -c %a /etc/kernel/secure-boot-private-key.pem) == 600 ]] || fail "Secure Boot key mode differs"
for source in "$hook_source" "$config" "$cmdline" "$entry_source" \
        "$repository/scripts/physical-pilot/apx-native-windows-probe-initrd-v1.sh" \
        "$repository/scripts/physical-pilot/apx-native-windows-maintenance-initrd-v1.sh" \
        "$repository/config/systemd/initrd/apx-native-windows-probe-v1.service" \
        "$repository/config/systemd/initrd/apx-native-windows-reserve-v1.service"; do
    [[ -f $source && ! -L $source ]] || fail "source differs: $source"
done
available=$(/usr/bin/df -B1 --output=avail /boot | /usr/bin/tail -n1)
if [[ $mode == refresh ]]; then
    available=$((available + $(/usr/bin/stat -c %s "$uki_target")))
fi
[[ $available -ge 250000000 ]] || fail "ESP free space is too low"
/usr/bin/python3 -m unittest discover -s tests >/dev/null || fail "repository tests failed"
/usr/bin/bash -n "$hook_source" || fail "build hook does not parse"
/usr/bin/sh -n "$repository/scripts/physical-pilot/apx-native-windows-probe-initrd-v1.sh" || fail "initrd probe does not parse"
/usr/bin/sh -n "$repository/scripts/physical-pilot/apx-native-windows-maintenance-initrd-v1.sh" || fail "initrd executor does not parse"

/usr/bin/install -d -m 0700 "$backup"
/usr/bin/install -d -m 0700 "$staging_dir"
/usr/bin/sfdisk --dump /dev/nvme0n1 >"$backup/gpt-before.sfdisk"
/usr/bin/sha256sum /boot/EFI/APX/apx-system-v1.efi /boot/loader/loader.conf >"$backup/boot-before.sha256"
if [[ $mode == refresh ]]; then
    /usr/bin/install -m 0644 -- "$uki_target" "$backup/apx-native-windows-maintenance-v1.efi"
    /usr/bin/install -m 0644 -- "$entry_target" "$backup/apx-native-windows-maintenance-v1.conf"
fi

rollback() {
    trap - ERR
    /usr/bin/rm -f -- "$staged_uki" "$esp_temporary" "$hook_target"
    if [[ $replacement_started == 1 ]]; then
        /usr/bin/rm -f -- "$uki_target"
        if [[ $mode == refresh ]]; then
            /usr/bin/install -m 0644 -- "$backup/apx-native-windows-maintenance-v1.efi" "$uki_target"
            /usr/bin/install -m 0644 -- "$backup/apx-native-windows-maintenance-v1.conf" "$entry_target"
        else
            /usr/bin/rm -f -- "$entry_target"
        fi
    fi
    fail "maintenance UKI build failed; temporary artifacts were removed"
}
trap rollback ERR
/usr/bin/install -d -m 0755 /etc/initcpio/install
/usr/bin/install -m 0644 -o root -g root -- "$hook_source" "$hook_target"
/usr/bin/mkinitcpio -n -c "$config" -k "$(/usr/bin/uname -r)" \
    -U "$staged_uki" --cmdline "$cmdline" --ukiconfig /etc/kernel/uki.conf
/usr/bin/chmod 0644 "$staged_uki"
/usr/bin/sbverify --list "$staged_uki" | /usr/bin/grep -Fq 'signature certificates' \
    || fail "maintenance UKI is not signed"
/usr/bin/ukify inspect "$staged_uki" | /usr/bin/grep -Fq 'apx.native_windows_reserve=1' \
    || fail "maintenance UKI cmdline differs"
replacement_started=1
/usr/bin/rm -f -- "$uki_target"
/usr/bin/install -m 0644 -- "$staged_uki" "$esp_temporary"
/usr/bin/sbverify --list "$esp_temporary" | /usr/bin/grep -Fq 'signature certificates' \
    || fail "copied maintenance UKI is not signed"
/usr/bin/mv -Tf -- "$esp_temporary" "$uki_target"
/usr/bin/install -m 0644 -o root -g root -- "$entry_source" "$entry_target"
/usr/bin/rm -f -- "$hook_target" "$staged_uki"
/usr/bin/bootctl list --no-pager --json=short | /usr/bin/grep -Fq 'apx-native-windows-maintenance-v1.conf' \
    || fail "maintenance boot entry is not published"
/usr/bin/sha256sum "$uki_target" "$entry_target" >"$backup/maintenance.sha256"
/usr/bin/sync
trap - ERR
/usr/bin/printf 'APX Windows maintenance UKI ready: %s\n' "$uki_target"
