#!/usr/bin/env bash
set -Eeuo pipefail

readonly repository=/root/apx-host-development-mode-v1/apx
readonly asset_root=/usr/share/apx/native-windows-lifecycle-v1
readonly return_target="$asset_root/return"
readonly builder=/usr/lib/apx/build-native-windows-lifecycle-uki-v1.sh
readonly installer=/usr/lib/apx/prepare-native-windows-installer-v2.sh
readonly runner=/usr/lib/apx/apx-native-windows-lifecycle-v1.py
readonly finalizer=/usr/lib/apx/apx-native-windows-lifecycle-finalize-v1.py
readonly switch_service=/usr/lib/apx/apx-environment-switch-v1.py
readonly finalizer_unit=/etc/systemd/system/apx-native-windows-lifecycle-finalize-v1.service
readonly backup_dir="/var/lib/apx/backups/$(date -u +%Y%m%dT%H%M%SZ)-self-contained-native-windows-lifecycle-v1"

fail() { echo "APX self-contained native Windows deployment refused: $*" >&2; exit 1; }

[[ $EUID -eq 0 && $PWD == "$repository" ]] || fail "root or repository differs"
[[ $(</etc/hostname) == apx-host ]] || fail "Host identity differs"
[[ $(</sys/class/power_supply/ADP0/online) == 1 ]] || fail "AC adapter is required"
[[ $(</sys/class/power_supply/BAT0/capacity) -ge 40 ]] || fail "battery is below 40%"
[[ ! -e /var/lib/apx/native-environments/windows-pending.json ]] || fail "a Windows operation is pending"
[[ ! -e /run/apx/environment-management-v1.lock ]] || fail "an Environment operation is active"
[[ ! -e /boot/EFI/APX/apx-native-windows-lifecycle-v1.efi ]] || fail "a maintenance UKI exists"
[[ ! -e /boot/loader/entries/apx-native-windows-lifecycle-v1.conf ]] || fail "a maintenance entry exists"
[[ ! -e $asset_root && ! -L $asset_root ]] || fail "asset root already exists"
[[ ! -e $backup_dir ]] || fail "backup already exists"

declare -A sources=(
    [builder]="$repository/scripts/physical-pilot/build-native-windows-lifecycle-uki-v1.sh"
    [installer]="$repository/scripts/physical-pilot/prepare-native-windows-installer-v2.sh"
    [runner]="$repository/scripts/physical-pilot/apx-native-windows-lifecycle-v1.py"
    [finalizer]="$repository/scripts/physical-pilot/apx-native-windows-lifecycle-finalize-v1.py"
    [switch]="$repository/scripts/physical-pilot/apx-environment-switch-v1.py"
    [unit]="$repository/config/systemd/apx-native-windows-lifecycle-finalize-v1.service"
    [hook]="$repository/config/initcpio/install/apx_native_windows_lifecycle"
    [mkinitcpio]="$repository/config/mkinitcpio/apx-native-windows-lifecycle-v1.conf"
    [entry]="$repository/config/systemd-boot/apx-native-windows-lifecycle-v1.conf"
    [initrd]="$repository/scripts/physical-pilot/apx-native-windows-lifecycle-initrd-v1.sh"
    [initrd_unit]="$repository/config/systemd/initrd/apx-native-windows-lifecycle-v1.service"
)
for source in "${sources[@]}"; do [[ -f $source && ! -L $source ]] || fail "source differs: $source"; done
for source in APX-ReturnToHub.ps1 APX-ReturnToHub.vbs APX-ProvisionHardware.cmd README.txt; do
    [[ -f $repository/config/native-windows-return-v1/$source \
            && ! -L $repository/config/native-windows-return-v1/$source ]] \
        || fail "return source differs: $source"
done
for target in "$builder" "$installer" "$runner" "$finalizer" "$switch_service" "$finalizer_unit"; do
    [[ -f $target && ! -L $target ]] || fail "installed target differs: $target"
done

/usr/bin/bash -n "${sources[builder]}" "${sources[installer]}" "${sources[hook]}"
/usr/bin/sh -n "${sources[initrd]}"
/usr/bin/python3 -m py_compile "${sources[runner]}" "${sources[finalizer]}" "${sources[switch]}"
/usr/bin/python3 -m unittest discover -s tests >/dev/null

/usr/bin/install -d -o root -g root -m 0700 "$backup_dir"
/usr/bin/cp --archive -- "$builder" "$backup_dir/builder.previous"
/usr/bin/cp --archive -- "$installer" "$backup_dir/installer.previous"
/usr/bin/cp --archive -- "$runner" "$backup_dir/runner.previous"
/usr/bin/cp --archive -- "$finalizer" "$backup_dir/finalizer.previous"
/usr/bin/cp --archive -- "$switch_service" "$backup_dir/switch.previous"
/usr/bin/cp --archive -- "$finalizer_unit" "$backup_dir/finalizer-unit.previous"

rollback() {
    set +e
    /usr/bin/cp --archive -- "$backup_dir/builder.previous" "$builder"
    /usr/bin/cp --archive -- "$backup_dir/installer.previous" "$installer"
    /usr/bin/cp --archive -- "$backup_dir/runner.previous" "$runner"
    /usr/bin/cp --archive -- "$backup_dir/finalizer.previous" "$finalizer"
    /usr/bin/cp --archive -- "$backup_dir/switch.previous" "$switch_service"
    /usr/bin/cp --archive -- "$backup_dir/finalizer-unit.previous" "$finalizer_unit"
    if [[ -d $asset_root && ! -L $asset_root ]]; then /usr/bin/find "$asset_root" -depth -delete; fi
    /usr/bin/systemctl daemon-reload
    /usr/bin/systemctl restart apx-environment-switch-v1.service
}
trap rollback ERR

/usr/bin/install -d -o root -g root -m 0755 "$asset_root" "$return_target"
/usr/bin/install -o root -g root -m 0644 "${sources[hook]}" "$asset_root/apx_native_windows_lifecycle"
/usr/bin/install -o root -g root -m 0644 "${sources[mkinitcpio]}" "$asset_root/apx-native-windows-lifecycle-v1.mkinitcpio.conf"
/usr/bin/install -o root -g root -m 0644 "${sources[entry]}" "$asset_root/apx-native-windows-lifecycle-v1.entry.conf"
/usr/bin/install -o root -g root -m 0755 "${sources[initrd]}" "$asset_root/apx-native-windows-lifecycle-initrd-v1.sh"
/usr/bin/install -o root -g root -m 0644 "${sources[initrd_unit]}" "$asset_root/apx-native-windows-lifecycle-v1.service"
for source in APX-ReturnToHub.ps1 APX-ReturnToHub.vbs APX-ProvisionHardware.cmd README.txt; do
    /usr/bin/install -o root -g root -m 0644 "$repository/config/native-windows-return-v1/$source" "$return_target/$source"
done

/usr/bin/install -o root -g root -m 0755 "${sources[builder]}" "$builder"
/usr/bin/install -o root -g root -m 0755 "${sources[installer]}" "$installer"
/usr/bin/install -o root -g root -m 0755 "${sources[runner]}" "$runner"
/usr/bin/install -o root -g root -m 0755 "${sources[finalizer]}" "$finalizer"
/usr/bin/install -o root -g root -m 0755 "${sources[switch]}" "$switch_service"
/usr/bin/install -o root -g root -m 0644 "${sources[unit]}" "$finalizer_unit"

/usr/bin/systemctl daemon-reload
/usr/bin/systemctl restart apx-environment-switch-v1.service
/usr/bin/systemctl is-active --quiet apx-environment-switch-v1.service

/usr/bin/cmp -- "${sources[builder]}" "$builder"
/usr/bin/cmp -- "${sources[installer]}" "$installer"
/usr/bin/cmp -- "${sources[runner]}" "$runner"
/usr/bin/cmp -- "${sources[finalizer]}" "$finalizer"
/usr/bin/cmp -- "${sources[switch]}" "$switch_service"
/usr/bin/cmp -- "${sources[unit]}" "$finalizer_unit"
! /usr/bin/grep -R -Fq '/root/apx-host-development-mode-v1/apx' "$asset_root" "$builder" "$installer" "$runner" "$finalizer"
/usr/bin/systemd-analyze verify "$finalizer_unit"

/usr/bin/chown -R root:root "$backup_dir"
/usr/bin/find "$backup_dir" -type f -exec chmod 0600 {} +
trap - ERR
echo "APX self-contained native Windows lifecycle deployed; backup: $backup_dir"
