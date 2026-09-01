#!/usr/bin/env bash
set -Eeuo pipefail

readonly repository=/root/apx-host-development-mode-v1/apx
readonly asset_root=/usr/share/apx/native-windows-lifecycle-v1
readonly backup_dir="/var/lib/apx/backups/$(date -u +%Y%m%dT%H%M%SZ)-native-windows-explicit-winpe-v2"
readonly finalizer_unit=/etc/systemd/system/apx-native-windows-lifecycle-finalize-v1.service

fail() { echo "APX explicit WinPE v2 deployment refused: $*" >&2; exit 1; }
[[ $EUID -eq 0 && $PWD == "$repository" ]] || fail "root or repository differs"
[[ $(</etc/hostname) == apx-host && $(</sys/class/dmi/id/product_name) == 82JU ]] || fail "Host identity differs"
[[ $(</sys/class/power_supply/ADP0/online) == 1 ]] || fail "AC adapter is required"
[[ $(</sys/class/power_supply/BAT0/capacity) -ge 40 ]] || fail "battery is below 40%"
[[ $(/usr/bin/xargs </sys/block/nvme0n1/device/serial) == S4DYNX0R253702 ]] || fail "disk serial differs"
[[ $(/usr/bin/sfdisk --disk-id /dev/nvme0n1) == AC9FC0BD-2162-43A9-AAE6-3F654FF6F275 ]] || fail "GPT identity differs"
[[ -z $(/usr/bin/efibootmgr | /usr/bin/awk '/^BootNext:/ {print}') ]] || fail "a BootNext is armed"
[[ ! -e $backup_dir ]] || fail "backup already exists"

declare -A sources=(
    [builder]="$repository/scripts/physical-pilot/build-native-windows-lifecycle-uki-v1.sh"
    [installer]="$repository/scripts/physical-pilot/prepare-native-windows-installer-v2.sh"
    [runner]="$repository/scripts/physical-pilot/apx-native-windows-lifecycle-v1.py"
    [finalizer]="$repository/scripts/physical-pilot/apx-native-windows-lifecycle-finalize-v1.py"
    [boot]="$repository/scripts/physical-pilot/apx-native-boot-runner-v1.py"
    [switch]="$repository/scripts/physical-pilot/apx-environment-switch-v1.py"
    [unit]="$repository/config/systemd/apx-native-windows-lifecycle-finalize-v1.service"
    [hook]="$repository/config/initcpio/install/apx_native_windows_lifecycle"
    [mkinitcpio]="$repository/config/mkinitcpio/apx-native-windows-lifecycle-v1.conf"
    [entry]="$repository/config/systemd-boot/apx-native-windows-lifecycle-v1.conf"
    [initrd]="$repository/scripts/physical-pilot/apx-native-windows-lifecycle-initrd-v1.sh"
    [initrd_unit]="$repository/config/systemd/initrd/apx-native-windows-lifecycle-v1.service"
    [winpe_cmd]="$repository/config/system-images-v1/windows-internal-winpe/apx-media.cmd"
    [winpe_shell]="$repository/config/system-images-v1/windows-internal-winpe/winpeshl.ini"
)
for source in "${sources[@]}"; do [[ -f $source && ! -L $source ]] || fail "source differs: $source"; done
for source in APX-ReturnToHub.ps1 APX-ReturnToHub.vbs APX-ProvisionHardware.cmd README.txt; do
    [[ -f $repository/config/native-windows-return-v1/$source && ! -L $repository/config/native-windows-return-v1/$source ]] \
        || fail "return source differs: $source"
done
for target in /usr/lib/apx/build-native-windows-lifecycle-uki-v1.sh \
        /usr/lib/apx/prepare-native-windows-installer-v2.sh \
        /usr/lib/apx/apx-native-windows-lifecycle-v1.py \
        /usr/lib/apx/apx-native-windows-lifecycle-finalize-v1.py \
        /usr/lib/apx/apx-native-boot-runner-v1.py \
        /usr/lib/apx/apx-environment-switch-v1.py "$finalizer_unit"; do
    [[ -f $target && ! -L $target ]] || fail "installed target differs: $target"
done

/usr/bin/bash -n "${sources[installer]}" "${sources[builder]}" "${sources[hook]}"
/usr/bin/sh -n "${sources[initrd]}"
/usr/bin/python3 -m py_compile "${sources[runner]}" "${sources[finalizer]}" "${sources[boot]}" "${sources[switch]}"
/usr/bin/python3 -m unittest discover -s tests >/dev/null

/usr/bin/install -d -o root -g root -m 0700 "$backup_dir"
/usr/bin/cp --archive -- "$asset_root" "$backup_dir/assets.previous"
for name in builder installer runner finalizer boot switch unit; do
    case $name in
        builder) target=/usr/lib/apx/build-native-windows-lifecycle-uki-v1.sh ;;
        installer) target=/usr/lib/apx/prepare-native-windows-installer-v2.sh ;;
        runner) target=/usr/lib/apx/apx-native-windows-lifecycle-v1.py ;;
        finalizer) target=/usr/lib/apx/apx-native-windows-lifecycle-finalize-v1.py ;;
        boot) target=/usr/lib/apx/apx-native-boot-runner-v1.py ;;
        switch) target=/usr/lib/apx/apx-environment-switch-v1.py ;;
        unit) target=$finalizer_unit ;;
    esac
    /usr/bin/cp --archive -- "$target" "$backup_dir/$name.previous"
done

rollback() {
    set +e
    /usr/bin/cp --archive -- "$backup_dir/assets.previous/." "$asset_root/"
    /usr/bin/cp --archive -- "$backup_dir/builder.previous" /usr/lib/apx/build-native-windows-lifecycle-uki-v1.sh
    /usr/bin/cp --archive -- "$backup_dir/installer.previous" /usr/lib/apx/prepare-native-windows-installer-v2.sh
    /usr/bin/cp --archive -- "$backup_dir/runner.previous" /usr/lib/apx/apx-native-windows-lifecycle-v1.py
    /usr/bin/cp --archive -- "$backup_dir/finalizer.previous" /usr/lib/apx/apx-native-windows-lifecycle-finalize-v1.py
    /usr/bin/cp --archive -- "$backup_dir/boot.previous" /usr/lib/apx/apx-native-boot-runner-v1.py
    /usr/bin/cp --archive -- "$backup_dir/switch.previous" /usr/lib/apx/apx-environment-switch-v1.py
    /usr/bin/cp --archive -- "$backup_dir/unit.previous" "$finalizer_unit"
    /usr/bin/systemctl daemon-reload
    /usr/bin/systemctl restart apx-environment-switch-v1.service
}
trap rollback ERR

/usr/bin/systemctl stop apx-native-windows-lifecycle-finalize-v1.service 2>/dev/null || true
/usr/bin/install -d -o root -g root -m 0755 "$asset_root" "$asset_root/return" "$asset_root/winpe"
/usr/bin/install -o root -g root -m 0644 "${sources[hook]}" "$asset_root/apx_native_windows_lifecycle"
/usr/bin/install -o root -g root -m 0644 "${sources[mkinitcpio]}" "$asset_root/apx-native-windows-lifecycle-v1.mkinitcpio.conf"
/usr/bin/install -o root -g root -m 0644 "${sources[entry]}" "$asset_root/apx-native-windows-lifecycle-v1.entry.conf"
/usr/bin/install -o root -g root -m 0755 "${sources[initrd]}" "$asset_root/apx-native-windows-lifecycle-initrd-v1.sh"
/usr/bin/install -o root -g root -m 0644 "${sources[initrd_unit]}" "$asset_root/apx-native-windows-lifecycle-v1.service"
/usr/bin/install -o root -g root -m 0644 "${sources[winpe_cmd]}" "$asset_root/winpe/apx-media.cmd"
/usr/bin/install -o root -g root -m 0644 "${sources[winpe_shell]}" "$asset_root/winpe/winpeshl.ini"
for source in APX-ReturnToHub.ps1 APX-ReturnToHub.vbs APX-ProvisionHardware.cmd README.txt; do
    /usr/bin/install -o root -g root -m 0644 "$repository/config/native-windows-return-v1/$source" "$asset_root/return/$source"
done

/usr/bin/install -o root -g root -m 0755 "${sources[builder]}" /usr/lib/apx/build-native-windows-lifecycle-uki-v1.sh
/usr/bin/install -o root -g root -m 0755 "${sources[installer]}" /usr/lib/apx/prepare-native-windows-installer-v2.sh
/usr/bin/install -o root -g root -m 0755 "${sources[runner]}" /usr/lib/apx/apx-native-windows-lifecycle-v1.py
/usr/bin/install -o root -g root -m 0755 "${sources[finalizer]}" /usr/lib/apx/apx-native-windows-lifecycle-finalize-v1.py
/usr/bin/install -o root -g root -m 0755 "${sources[boot]}" /usr/lib/apx/apx-native-boot-runner-v1.py
/usr/bin/install -o root -g root -m 0755 "${sources[switch]}" /usr/lib/apx/apx-environment-switch-v1.py
/usr/bin/install -o root -g root -m 0644 "${sources[unit]}" "$finalizer_unit"

/usr/bin/systemctl daemon-reload
/usr/bin/systemctl reset-failed apx-native-windows-lifecycle-finalize-v1.service || true
/usr/bin/systemctl restart apx-environment-switch-v1.service
/usr/bin/systemctl is-active --quiet apx-environment-switch-v1.service
for name in builder installer runner finalizer boot switch unit; do
    case $name in
        builder) target=/usr/lib/apx/build-native-windows-lifecycle-uki-v1.sh ;;
        installer) target=/usr/lib/apx/prepare-native-windows-installer-v2.sh ;;
        runner) target=/usr/lib/apx/apx-native-windows-lifecycle-v1.py ;;
        finalizer) target=/usr/lib/apx/apx-native-windows-lifecycle-finalize-v1.py ;;
        boot) target=/usr/lib/apx/apx-native-boot-runner-v1.py ;;
        switch) target=/usr/lib/apx/apx-environment-switch-v1.py ;;
        unit) target=$finalizer_unit ;;
    esac
    /usr/bin/cmp -- "${sources[$name]}" "$target"
done
/usr/bin/cmp -- "${sources[winpe_cmd]}" "$asset_root/winpe/apx-media.cmd"
/usr/bin/cmp -- "${sources[winpe_shell]}" "$asset_root/winpe/winpeshl.ini"
! /usr/bin/grep -R -Fq '/root/apx-host-development-mode-v1/apx' "$asset_root" \
    /usr/lib/apx/build-native-windows-lifecycle-uki-v1.sh \
    /usr/lib/apx/prepare-native-windows-installer-v2.sh \
    /usr/lib/apx/apx-native-windows-lifecycle-v1.py \
    /usr/lib/apx/apx-native-windows-lifecycle-finalize-v1.py
/usr/bin/systemd-analyze verify "$finalizer_unit"
/usr/bin/chown -R root:root "$backup_dir"
/usr/bin/find "$backup_dir" -type f -exec chmod 0600 {} +
trap - ERR
echo "APX explicit WinPE v2 deployed; backup: $backup_dir"
