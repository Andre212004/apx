#!/usr/bin/env bash
set -Eeuo pipefail

readonly repository=/root/apx-host-development-mode-v1/apx
readonly runner_source="$repository/scripts/physical-pilot/apx-native-windows-lifecycle-v1.py"
readonly builder_source="$repository/scripts/physical-pilot/build-native-windows-lifecycle-uki-v1.sh"
readonly runner_target=/usr/lib/apx/apx-native-windows-lifecycle-v1.py
readonly builder_target=/usr/lib/apx/build-native-windows-lifecycle-uki-v1.sh
readonly backup_dir="/var/lib/apx/backups/$(date -u +%Y%m%dT%H%M%SZ)-native-windows-lifecycle-build-fix-v1"

fail() { echo "APX native Windows lifecycle build fix refused: $*" >&2; exit 1; }

[[ $EUID -eq 0 && $PWD == "$repository" ]] || fail "root or repository differs"
[[ $(</etc/hostname) == apx-host ]] || fail "Host identity differs"
for file in "$runner_source" "$builder_source" "$runner_target" "$builder_target"; do
    [[ -f $file && ! -L $file ]] || fail "file differs: $file"
done
[[ ! -e /var/lib/apx/native-environments/windows-pending.json ]] || fail "a Windows operation is pending"
[[ ! -e /run/apx/environment-management-v1.lock ]] || fail "an Environment operation is active"
[[ ! -e /boot/EFI/APX/apx-native-windows-lifecycle-v1.efi ]] || fail "a maintenance UKI exists"
[[ ! -e /boot/loader/entries/apx-native-windows-lifecycle-v1.conf ]] || fail "a maintenance entry exists"
[[ ! -e $backup_dir ]] || fail "backup already exists"

/usr/bin/python3 -m py_compile "$runner_source"
/usr/bin/bash -n "$builder_source"
/usr/bin/bash -n "$repository/config/initcpio/install/apx_native_windows_lifecycle"
/usr/bin/python3 -m unittest tests.test_apx_native_windows_storage_v1 >/dev/null

/usr/bin/install -d -o root -g root -m 0700 "$backup_dir"
/usr/bin/cp --archive -- "$runner_target" "$backup_dir/lifecycle-runner.previous"
/usr/bin/cp --archive -- "$builder_target" "$backup_dir/lifecycle-builder.previous"

rollback() {
    set +e
    /usr/bin/cp --archive -- "$backup_dir/lifecycle-runner.previous" "$runner_target"
    /usr/bin/cp --archive -- "$backup_dir/lifecycle-builder.previous" "$builder_target"
}
trap rollback ERR

/usr/bin/install -o root -g root -m 0755 "$runner_source" "$runner_target"
/usr/bin/install -o root -g root -m 0755 "$builder_source" "$builder_target"
/usr/bin/cmp -- "$runner_source" "$runner_target"
/usr/bin/cmp -- "$builder_source" "$builder_target"

/usr/bin/chown -R root:root "$backup_dir"
/usr/bin/find "$backup_dir" -type f -exec chmod 0600 {} +
trap - ERR
echo "APX native Windows lifecycle build fix deployed; backup: $backup_dir"
