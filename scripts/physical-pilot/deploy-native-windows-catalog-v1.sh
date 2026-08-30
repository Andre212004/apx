#!/usr/bin/bash
set -euo pipefail

# Hardware-bound deployment of the native Windows catalogue/one-shot boot path.
# This does not resize or repartition the disk and cannot boot Windows until the
# independently validated Windows Boot Manager exists.
readonly repository=/root/apx-host-development-mode-v1/apx
readonly backup=/var/lib/apx/backups/20260825-native-windows-catalog-v1
readonly installed_ui=/var/lib/apx/environments/hub/home/apx/.config/quickshell/apx/shell.qml
readonly installed_seed=/usr/share/apx/config-seeds/environment-shell-v1/quickshell/apx/shell.qml
readonly metadata_dir=/var/lib/apx/native-environments
readonly metadata_target="$metadata_dir/windows.json"

fail() { /usr/bin/printf 'APX native Windows catalogue deployment refused: %s\n' "$1" >&2; exit 2; }

[[ $(/usr/bin/id -u) == 0 ]] || fail "root is required"
[[ $(< /etc/hostname) == apx-host ]] || fail "hostname differs"
[[ $(< /sys/class/dmi/id/product_name) == 82JU ]] || fail "Lenovo identity differs"
/usr/bin/grep -Fxq 'profile=apx-physical-headless-pilot-v1' /etc/apx-physical-pilot \
    || fail "physical-pilot marker differs"
[[ $PWD == "$repository" ]] || fail "run from the dedicated repository"
[[ ! -e $backup ]] || fail "backup destination already exists"
[[ $(/usr/bin/machinectl list --no-legend | /usr/bin/awk '{print $1}') == apx-hub ]] \
    || fail "the Hub is not the only active machine"
! /usr/bin/pgrep -f '^/usr/lib/apx/apx-environment-management-runner-v1.py ' >/dev/null \
    || fail "Environment management is active"

readonly source_service="$repository/scripts/physical-pilot/apx-environment-switch-v1.py"
readonly source_client="$repository/scripts/physical-pilot/apx-environment-switch-client-v1.py"
readonly source_contract="$repository/src/apx_environment_switch_contract.py"
readonly source_runner="$repository/scripts/physical-pilot/apx-native-boot-runner-v1.py"
readonly source_ui="$repository/config/environment-shell-v1/quickshell/apx/shell.qml"
readonly source_metadata="$repository/config/native-environments/windows-v1.json"
readonly source_runtime="$repository/scripts/virtual-lab/apx-lab-runtime.py"
readonly target_service=/usr/lib/apx/apx-environment-switch-v1.py
readonly target_client=/usr/lib/apx/apx-environment-switch-client-v1.py
readonly target_contract=/usr/lib/apx/apx_environment_switch_contract.py
readonly target_runner=/usr/lib/apx/apx-native-boot-runner-v1.py
readonly target_runtime=/usr/lib/apx/apx-lab-runtime.py

for source in "$source_service" "$source_client" "$source_contract" "$source_runner" "$source_ui" "$source_metadata" "$source_runtime"; do
    [[ -f $source && ! -L $source ]] || fail "source differs: $source"
done
for target in "$target_service" "$target_client" "$target_contract" "$target_runtime" "$installed_ui" "$installed_seed"; do
    [[ -f $target && ! -L $target ]] || fail "installed target differs: $target"
done

/usr/bin/python3 -m unittest discover -s tests >/dev/null || fail "repository tests failed"
/usr/bin/python3 -m py_compile "$source_service" "$source_client" "$source_contract" "$source_runner" "$source_runtime" \
    || fail "Python source does not compile"
/usr/bin/python3 -c 'import json,sys; value=json.load(open(sys.argv[1])); assert value["reserved_bytes"] == 120*1024**3 and value["name"] == "windows" and value["environment_kind"] == "native-boot"' "$source_metadata" \
    || fail "native metadata differs"

/usr/bin/install -d -m 0700 "$backup"
/usr/bin/cp --archive -- "$target_service" "$backup/apx-environment-switch-v1.py"
/usr/bin/cp --archive -- "$target_client" "$backup/apx-environment-switch-client-v1.py"
/usr/bin/cp --archive -- "$target_contract" "$backup/apx_environment_switch_contract.py"
/usr/bin/cp --archive -- "$target_runtime" "$backup/apx-lab-runtime.py"
/usr/bin/cp --archive -- "$installed_ui" "$backup/shell.qml"
/usr/bin/cp --archive -- "$installed_seed" "$backup/seed-shell.qml"
/usr/bin/sha256sum "$target_service" "$target_client" "$target_contract" "$target_runtime" "$installed_ui" "$installed_seed" >"$backup/before.sha256"

rollback() {
    trap - ERR
    /usr/bin/cp --archive -- "$backup/apx-environment-switch-v1.py" "$target_service"
    /usr/bin/cp --archive -- "$backup/apx-environment-switch-client-v1.py" "$target_client"
    /usr/bin/cp --archive -- "$backup/apx_environment_switch_contract.py" "$target_contract"
    /usr/bin/cp --archive -- "$backup/apx-lab-runtime.py" "$target_runtime"
    /usr/bin/cp --archive -- "$backup/shell.qml" "$installed_ui"
    /usr/bin/cp --archive -- "$backup/seed-shell.qml" "$installed_seed"
    /usr/bin/rm -f -- "$target_runner" "$metadata_target"
    /usr/bin/systemctl restart apx-environment-switch-v1.service || true
    fail "installation failed; the exact previous catalogue was restored"
}
trap rollback ERR

/usr/bin/install -m 0755 -o root -g root -- "$source_service" "$target_service"
/usr/bin/install -m 0755 -o root -g root -- "$source_client" "$target_client"
/usr/bin/install -m 0644 -o root -g root -- "$source_contract" "$target_contract"
/usr/bin/install -m 0755 -o root -g root -- "$source_runner" "$target_runner"
/usr/bin/install -m 0755 -o root -g root -- "$source_runtime" "$target_runtime"
/usr/bin/install -m 0600 -o 1000 -g 1000 -- "$source_ui" "$installed_ui"
/usr/bin/install -m 0644 -o root -g root -- "$source_ui" "$installed_seed"
/usr/bin/install -d -m 0700 -o root -g root -- "$metadata_dir"
/usr/bin/install -m 0400 -o root -g root -- "$source_metadata" "$metadata_target"
/usr/bin/systemctl restart apx-environment-switch-v1.service
/usr/bin/systemctl is-active --quiet apx-environment-switch-v1.service

/usr/bin/cmp -s -- "$source_service" "$target_service"
/usr/bin/cmp -s -- "$source_client" "$target_client"
/usr/bin/cmp -s -- "$source_contract" "$target_contract"
/usr/bin/cmp -s -- "$source_runner" "$target_runner"
/usr/bin/cmp -s -- "$source_runtime" "$target_runtime"
/usr/bin/cmp -s -- "$source_ui" "$installed_ui"
/usr/bin/cmp -s -- "$source_ui" "$installed_seed"
/usr/bin/cmp -s -- "$source_metadata" "$metadata_target"

trap - ERR
/usr/bin/sha256sum "$target_service" "$target_client" "$target_contract" "$target_runner" "$target_runtime" "$installed_ui" "$installed_seed" "$metadata_target" >"$backup/after.sha256"
/usr/bin/chmod 0600 "$backup/before.sha256" "$backup/after.sha256"
/usr/bin/printf 'APX native Windows catalogue installed; rollback: %s\n' "$backup"
