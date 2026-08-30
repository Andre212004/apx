#!/usr/bin/env bash
set -Eeuo pipefail

readonly repository=/root/apx-host-development-mode-v1/apx
readonly source_file="$repository/scripts/physical-pilot/apx-native-windows-lifecycle-v1.py"
readonly target_file=/usr/lib/apx/apx-native-windows-lifecycle-v1.py
readonly backup_dir="/var/lib/apx/backups/$(date -u +%Y%m%dT%H%M%SZ)-native-windows-lifecycle-cwd-fix-v1"

fail() { echo "APX native Windows lifecycle fix refused: $*" >&2; exit 1; }

[[ $EUID -eq 0 ]] || fail "run as root"
[[ $PWD == "$repository" ]] || fail "repository differs"
[[ $(</etc/hostname) == apx-host ]] || fail "Host identity differs"
[[ -f $source_file && ! -L $source_file ]] || fail "source differs"
[[ -f $target_file && ! -L $target_file ]] || fail "installed target differs"
[[ ! -e /var/lib/apx/native-environments/windows-pending.json ]] || fail "a Windows operation is pending"
[[ ! -e /run/apx/environment-management-v1.lock ]] || fail "an Environment operation is active"
[[ ! -e $backup_dir ]] || fail "backup already exists"

/usr/bin/python3 -m py_compile "$source_file"
/usr/bin/python3 -m unittest tests.test_apx_native_windows_storage_v1 >/dev/null
/usr/bin/install -d -o root -g root -m 0700 "$backup_dir"
/usr/bin/cp --archive -- "$target_file" "$backup_dir/lifecycle-runner.previous"

rollback() {
    set +e
    /usr/bin/cp --archive -- "$backup_dir/lifecycle-runner.previous" "$target_file"
}
trap rollback ERR

/usr/bin/install -o root -g root -m 0755 "$source_file" "$target_file"
/usr/bin/cmp -- "$source_file" "$target_file"
/usr/bin/python3 - "$target_file" <<'PY'
import importlib.util
from pathlib import Path
from unittest import mock
import sys

path = Path(sys.argv[1])
spec = importlib.util.spec_from_file_location("apx_native_windows_lifecycle", path)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)
with mock.patch.object(module.subprocess, "run") as invoked:
    module.run(("/usr/bin/true",))
    assert invoked.call_args.kwargs["cwd"] == module.REPOSITORY
PY

/usr/bin/chown -R root:root "$backup_dir"
/usr/bin/find "$backup_dir" -type f -exec chmod 0600 {} +
trap - ERR
echo "APX native Windows lifecycle working-directory fix deployed; backup: $backup_dir"
