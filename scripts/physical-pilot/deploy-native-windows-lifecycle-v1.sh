#!/usr/bin/bash
set -euo pipefail

readonly repository=/root/apx-host-development-mode-v1/apx
readonly backup=/var/lib/apx/backups/20260825-native-windows-lifecycle-v1
readonly installed_ui=/var/lib/apx/environments/hub/home/apx/.config/quickshell/apx/shell.qml
readonly installed_seed=/usr/share/apx/config-seeds/environment-shell-v1/quickshell/apx/shell.qml
readonly metadata_target=/var/lib/apx/native-environments/windows.json
readonly policy_target=/usr/share/apx/native-environments/windows-policy-v1.json
readonly unit_target=/etc/systemd/system/apx-native-windows-lifecycle-finalize-v1.service
readonly service_target=/usr/lib/apx/apx-environment-switch-v1.py
readonly client_target=/usr/lib/apx/apx-environment-switch-client-v1.py
readonly contract_target=/usr/lib/apx/apx_environment_switch_contract.py
readonly runtime_target=/usr/lib/apx/apx-lab-runtime.py
readonly boot_target=/usr/lib/apx/apx-native-boot-runner-v1.py
readonly lifecycle_target=/usr/lib/apx/apx-native-windows-lifecycle-v1.py
readonly finalizer_target=/usr/lib/apx/apx-native-windows-lifecycle-finalize-v1.py
readonly build_target=/usr/lib/apx/build-native-windows-lifecycle-uki-v1.sh
readonly installer_target=/usr/lib/apx/prepare-native-windows-installer-v2.sh

fail() { /usr/bin/printf 'APX native Windows lifecycle deployment refused: %s\n' "$1" >&2; exit 2; }
[[ $(/usr/bin/id -u) == 0 && $PWD == "$repository" ]] || fail "root or repository differs"
[[ $(< /etc/hostname) == apx-host && $(< /sys/class/dmi/id/product_name) == 82JU ]] || fail "computer identity differs"
/usr/bin/grep -Fxq 'profile=apx-physical-headless-pilot-v1' /etc/apx-physical-pilot || fail "pilot marker differs"
[[ $(/usr/bin/xargs < /sys/block/nvme0n1/device/serial) == S4DYNX0R253702 ]] || fail "disk serial differs"
[[ $(/usr/bin/sfdisk --disk-id /dev/nvme0n1) == AC9FC0BD-2162-43A9-AAE6-3F654FF6F275 ]] || fail "GPT identity differs"
[[ $(/usr/bin/efibootmgr | /usr/bin/awk '/^BootCurrent:/ {print $2}') == 0005 ]] || fail "Linux is not current"
[[ $(/usr/bin/efibootmgr | /usr/bin/awk '/^BootOrder:/ {print $2}') == 0005,0006,0000,2001,2002,2003 ]] || fail "Linux-first order differs"
! /usr/bin/efibootmgr | /usr/bin/grep -q '^BootNext:' || fail "a BootNext is already armed"
[[ ! -e $backup && ! -e /var/lib/apx/native-environments/windows-pending.json ]] || fail "backup or pending operation exists"
[[ ! -e /boot/EFI/APX/apx-native-windows-lifecycle-v1.efi && ! -e /boot/loader/entries/apx-native-windows-lifecycle-v1.conf ]] || fail "maintenance artifacts already exist"

declare -A sources=(
    [service]="$repository/scripts/physical-pilot/apx-environment-switch-v1.py"
    [client]="$repository/scripts/physical-pilot/apx-environment-switch-client-v1.py"
    [contract]="$repository/src/apx_environment_switch_contract.py"
    [runtime]="$repository/scripts/virtual-lab/apx-lab-runtime.py"
    [boot]="$repository/scripts/physical-pilot/apx-native-boot-runner-v1.py"
    [lifecycle]="$repository/scripts/physical-pilot/apx-native-windows-lifecycle-v1.py"
    [finalizer]="$repository/scripts/physical-pilot/apx-native-windows-lifecycle-finalize-v1.py"
    [build]="$repository/scripts/physical-pilot/build-native-windows-lifecycle-uki-v1.sh"
    [installer]="$repository/scripts/physical-pilot/prepare-native-windows-installer-v2.sh"
    [ui]="$repository/config/environment-shell-v1/quickshell/apx/shell.qml"
    [metadata]="$repository/config/native-environments/windows-v1.json"
    [policy]="$repository/config/native-environments/windows-policy-v1.json"
    [unit]="$repository/config/systemd/apx-native-windows-lifecycle-finalize-v1.service"
)
for source in "${sources[@]}"; do [[ -f $source && ! -L $source ]] || fail "source differs: $source"; done
for target in "$service_target" "$client_target" "$contract_target" "$runtime_target" "$boot_target" \
        "$installed_ui" "$installed_seed" "$metadata_target"; do
    [[ -f $target && ! -L $target ]] || fail "installed target differs: $target"
done
for target in "$policy_target" "$unit_target" "$lifecycle_target" "$finalizer_target" "$build_target" "$installer_target"; do
    [[ ! -e $target ]] || fail "new target already exists: $target"
done
/usr/bin/python3 -m unittest discover -s tests >/dev/null || fail "repository tests failed"
/usr/bin/python3 -m py_compile "${sources[service]}" "${sources[client]}" "${sources[contract]}" \
    "${sources[runtime]}" "${sources[boot]}" "${sources[lifecycle]}" "${sources[finalizer]}" || fail "Python compilation failed"
for source in "${sources[build]}" "${sources[installer]}" \
        "$repository/scripts/physical-pilot/apx-native-windows-lifecycle-initrd-v1.sh"; do
    /usr/bin/bash -n "$source" || fail "shell source does not parse: $source"
done

/usr/bin/install -d -m 0700 "$backup"
/usr/bin/cp --archive -- "$service_target" "$backup/service.py"
/usr/bin/cp --archive -- "$client_target" "$backup/client.py"
/usr/bin/cp --archive -- "$contract_target" "$backup/contract.py"
/usr/bin/cp --archive -- "$runtime_target" "$backup/runtime.py"
/usr/bin/cp --archive -- "$boot_target" "$backup/boot.py"
/usr/bin/cp --archive -- "$installed_ui" "$backup/shell.qml"
/usr/bin/cp --archive -- "$installed_seed" "$backup/seed-shell.qml"
/usr/bin/cp --archive -- "$metadata_target" "$backup/windows.json"
/usr/bin/sha256sum "$service_target" "$client_target" "$contract_target" "$runtime_target" \
    "$boot_target" "$installed_ui" "$installed_seed" "$metadata_target" >"$backup/before.sha256"

rollback() {
    trap - ERR
    /usr/bin/systemctl disable apx-native-windows-lifecycle-finalize-v1.service >/dev/null 2>&1 || true
    /usr/bin/rm -f -- "$policy_target" "$unit_target" "$lifecycle_target" "$finalizer_target" "$build_target" "$installer_target"
    /usr/bin/cp --archive -- "$backup/service.py" "$service_target"
    /usr/bin/cp --archive -- "$backup/client.py" "$client_target"
    /usr/bin/cp --archive -- "$backup/contract.py" "$contract_target"
    /usr/bin/cp --archive -- "$backup/runtime.py" "$runtime_target"
    /usr/bin/cp --archive -- "$backup/boot.py" "$boot_target"
    /usr/bin/cp --archive -- "$backup/shell.qml" "$installed_ui"
    /usr/bin/cp --archive -- "$backup/seed-shell.qml" "$installed_seed"
    /usr/bin/cp --archive -- "$backup/windows.json" "$metadata_target"
    /usr/bin/systemctl daemon-reload || true
    /usr/bin/systemctl restart apx-environment-switch-v1.service || true
    fail "installation failed; the exact previous integration was restored"
}
trap rollback ERR

/usr/bin/install -m 0755 -o root -g root -- "${sources[service]}" "$service_target"
/usr/bin/install -m 0755 -o root -g root -- "${sources[client]}" "$client_target"
/usr/bin/install -m 0644 -o root -g root -- "${sources[contract]}" "$contract_target"
/usr/bin/install -m 0755 -o root -g root -- "${sources[runtime]}" "$runtime_target"
/usr/bin/install -m 0755 -o root -g root -- "${sources[boot]}" "$boot_target"
/usr/bin/install -m 0755 -o root -g root -- "${sources[lifecycle]}" "$lifecycle_target"
/usr/bin/install -m 0755 -o root -g root -- "${sources[finalizer]}" "$finalizer_target"
/usr/bin/install -m 0755 -o root -g root -- "${sources[build]}" "$build_target"
/usr/bin/install -m 0755 -o root -g root -- "${sources[installer]}" "$installer_target"
/usr/bin/install -m 0600 -o 1000 -g 1000 -- "${sources[ui]}" "$installed_ui"
/usr/bin/install -m 0644 -o root -g root -- "${sources[ui]}" "$installed_seed"
/usr/bin/install -m 0400 -o root -g root -- "${sources[metadata]}" "$metadata_target"
/usr/bin/install -d -m 0755 -o root -g root -- "$(/usr/bin/dirname "$policy_target")"
/usr/bin/install -m 0444 -o root -g root -- "${sources[policy]}" "$policy_target"
/usr/bin/install -m 0644 -o root -g root -- "${sources[unit]}" "$unit_target"
/usr/bin/systemctl daemon-reload
/usr/bin/systemctl enable apx-native-windows-lifecycle-finalize-v1.service >/dev/null
/usr/bin/systemctl restart apx-environment-switch-v1.service
/usr/bin/systemctl is-active --quiet apx-environment-switch-v1.service
"$boot_target" --target windows --validate-only
for key in service client contract runtime boot lifecycle finalizer build installer; do
    target_var="${key}_target"
    /usr/bin/cmp -s -- "${sources[$key]}" "${!target_var}"
done
/usr/bin/cmp -s -- "${sources[ui]}" "$installed_ui"
/usr/bin/cmp -s -- "${sources[ui]}" "$installed_seed"
/usr/bin/cmp -s -- "${sources[metadata]}" "$metadata_target"
/usr/bin/cmp -s -- "${sources[policy]}" "$policy_target"
/usr/bin/cmp -s -- "${sources[unit]}" "$unit_target"
trap - ERR
/usr/bin/sha256sum "$service_target" "$client_target" "$contract_target" "$runtime_target" \
    "$boot_target" "$lifecycle_target" "$finalizer_target" "$build_target" "$installer_target" \
    "$installed_ui" "$installed_seed" "$metadata_target" "$policy_target" "$unit_target" >"$backup/after.sha256"
/usr/bin/chmod 0600 "$backup/before.sha256" "$backup/after.sha256"
/usr/bin/printf 'APX repeatable native Windows lifecycle installed; rollback: %s\n' "$backup"
