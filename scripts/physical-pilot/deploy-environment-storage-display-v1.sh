#!/usr/bin/env bash
set -Eeuo pipefail

readonly repository=/root/apx-host-development-mode-v1/apx
readonly backup_dir="/var/lib/apx/backups/$(date -u +%Y%m%dT%H%M%SZ)-environment-storage-display-v1"
readonly live_ui=/var/lib/apx/environments/hub/home/apx/.config/quickshell/apx/shell.qml
readonly seed_ui=/usr/share/apx/config-seeds/environment-shell-v1/quickshell/apx/shell.qml
readonly service=/usr/lib/apx/apx-environment-switch-v1.py
readonly client=/usr/lib/apx/apx-environment-switch-client-v1.py
readonly contract=/usr/lib/apx/apx_environment_switch_contract.py
readonly storage_runner=/usr/lib/apx/apx-environment-storage-runner-v1.py
readonly runtime=/usr/lib/apx/apx-lab-runtime.py

fail() { echo "APX storage-display deployment refused: $*" >&2; exit 1; }

[[ $EUID -eq 0 ]] || fail "run as root"
[[ $(</etc/hostname) == apx-host ]] || fail "Host identity differs"
[[ ! -e $backup_dir ]] || fail "backup already exists"

declare -A sources=(
    [service]="$repository/scripts/physical-pilot/apx-environment-switch-v1.py"
    [client]="$repository/scripts/physical-pilot/apx-environment-switch-client-v1.py"
    [contract]="$repository/src/apx_environment_switch_contract.py"
    [storage_runner]="$repository/scripts/physical-pilot/apx-environment-storage-runner-v1.py"
    [runtime]="$repository/scripts/virtual-lab/apx-lab-runtime.py"
    [ui]="$repository/config/environment-shell-v1/quickshell/apx/shell.qml"
)
for source in "${sources[@]}"; do
    [[ -f $source && ! -L $source ]] || fail "source differs: $source"
done

/usr/bin/install -d -o root -g root -m 0700 "$backup_dir"
declare -A backups=(
    ["$service"]="$backup_dir/service"
    ["$client"]="$backup_dir/client"
    ["$contract"]="$backup_dir/contract"
    ["$runtime"]="$backup_dir/runtime"
    ["$live_ui"]="$backup_dir/ui-live"
    ["$seed_ui"]="$backup_dir/ui-seed"
)
for target in "${!backups[@]}"; do
    [[ -f $target && ! -L $target ]] || fail "installed target differs: $target"
    /usr/bin/cp --archive -- "$target" "${backups[$target]}"
done
if [[ -e $storage_runner || -L $storage_runner ]]; then
    [[ -f $storage_runner && ! -L $storage_runner ]] || fail "storage runner target differs"
    /usr/bin/cp --archive -- "$storage_runner" "$backup_dir/storage-runner.previous"
fi

rollback() {
    set +e
    local target
    for target in "${!backups[@]}"; do
        [[ -f ${backups[$target]} ]] && /usr/bin/cp --archive -- "${backups[$target]}" "$target"
    done
    if [[ -f $backup_dir/storage-runner.previous ]]; then
        /usr/bin/cp --archive -- "$backup_dir/storage-runner.previous" "$storage_runner"
    elif [[ -e $storage_runner && ! -L $storage_runner ]]; then
        /usr/bin/unlink "$storage_runner"
    fi
    /usr/bin/systemctl restart apx-environment-switch-v1.service
    /usr/bin/systemctl restart apx-pilot-executor.service
}
trap rollback ERR

/usr/bin/install -o root -g root -m 0755 "${sources[service]}" "$service"
/usr/bin/install -o root -g root -m 0755 "${sources[client]}" "$client"
/usr/bin/install -o root -g root -m 0644 "${sources[contract]}" "$contract"
/usr/bin/install -o root -g root -m 0755 "${sources[storage_runner]}" "$storage_runner"
/usr/bin/install -o root -g root -m 0755 "${sources[runtime]}" "$runtime"
/usr/bin/install -o root -g root -m 0644 "${sources[ui]}" "$seed_ui"
/usr/bin/install -o 1000 -g 1000 -m 0600 "${sources[ui]}" "$live_ui"

/usr/bin/systemctl restart apx-environment-switch-v1.service
/usr/bin/systemctl restart apx-pilot-executor.service
/usr/bin/systemctl is-active --quiet apx-environment-switch-v1.service
/usr/bin/systemctl is-active --quiet apx-pilot-executor.service

/usr/bin/cmp -- "${sources[service]}" "$service"
/usr/bin/cmp -- "${sources[client]}" "$client"
/usr/bin/cmp -- "${sources[contract]}" "$contract"
/usr/bin/cmp -- "${sources[storage_runner]}" "$storage_runner"
/usr/bin/cmp -- "${sources[runtime]}" "$runtime"
/usr/bin/cmp -- "${sources[ui]}" "$seed_ui"
/usr/bin/cmp -- "${sources[ui]}" "$live_ui"

/usr/bin/chown -R root:root "$backup_dir"
/usr/bin/find "$backup_dir" -type f -exec chmod 0600 {} +
trap - ERR
echo "APX Environment storage display deployed; backup: $backup_dir"
