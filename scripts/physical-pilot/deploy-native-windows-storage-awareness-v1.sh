#!/usr/bin/bash
set -euo pipefail

readonly repository=/root/apx-host-development-mode-v1/apx
readonly source_service="$repository/scripts/physical-pilot/apx-environment-switch-v1.py"
readonly target_service=/usr/lib/apx/apx-environment-switch-v1.py
readonly backup=/var/lib/apx/backups/20260825-native-windows-storage-awareness-v2

fail() { /usr/bin/printf 'APX Windows storage-awareness deployment refused: %s\n' "$1" >&2; exit 2; }
[[ $(/usr/bin/id -u) == 0 ]] || fail "root is required"
[[ $(< /etc/hostname) == apx-host ]] || fail "hostname differs"
[[ $(< /sys/class/dmi/id/product_name) == 82JU ]] || fail "Lenovo identity differs"
/usr/bin/grep -Fxq 'profile=apx-physical-headless-pilot-v1' /etc/apx-physical-pilot || fail "pilot marker differs"
[[ $PWD == "$repository" && ! -e $backup ]] || fail "repository or backup identity differs"
[[ -f $source_service && ! -L $source_service && -f $target_service && ! -L $target_service ]] || fail "service identity differs"
/usr/bin/python3 -m unittest discover -s tests >/dev/null || fail "repository tests failed"
/usr/bin/python3 -m py_compile "$source_service" || fail "service does not compile"

/usr/bin/install -d -m 0700 "$backup"
/usr/bin/cp --archive -- "$target_service" "$backup/apx-environment-switch-v1.py"
rollback() {
    trap - ERR
    /usr/bin/cp --archive -- "$backup/apx-environment-switch-v1.py" "$target_service"
    /usr/bin/systemctl restart apx-environment-switch-v1.service || true
    fail "installation failed; the previous service was restored"
}
trap rollback ERR
/usr/bin/install -m 0755 -o root -g root -- "$source_service" "$target_service"
/usr/bin/systemctl restart apx-environment-switch-v1.service
/usr/bin/systemctl is-active --quiet apx-environment-switch-v1.service
/usr/bin/cmp -s -- "$source_service" "$target_service"
trap - ERR
/usr/bin/printf 'APX Windows storage awareness installed; rollback: %s\n' "$backup"
