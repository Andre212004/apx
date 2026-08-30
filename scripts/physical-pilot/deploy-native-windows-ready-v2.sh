#!/usr/bin/bash
set -euo pipefail

readonly repository=/root/apx-host-development-mode-v1/apx
readonly backup=/var/lib/apx/backups/20260825-native-windows-ready-v2
readonly source_service="$repository/scripts/physical-pilot/apx-environment-switch-v1.py"
readonly source_runner="$repository/scripts/physical-pilot/apx-native-boot-runner-v1.py"
readonly source_metadata="$repository/config/native-environments/windows-v1.json"
readonly target_service=/usr/lib/apx/apx-environment-switch-v1.py
readonly target_runner=/usr/lib/apx/apx-native-boot-runner-v1.py
readonly target_metadata=/var/lib/apx/native-environments/windows.json

fail() { /usr/bin/printf 'APX native Windows ready deployment refused: %s\n' "$1" >&2; exit 2; }
[[ $(/usr/bin/id -u) == 0 ]] || fail "root is required"
[[ $PWD == "$repository" ]] || fail "repository differs"
[[ $(< /etc/hostname) == apx-host ]] || fail "hostname differs"
[[ $(< /sys/class/dmi/id/product_name) == 82JU ]] || fail "Lenovo identity differs"
/usr/bin/grep -Fxq 'profile=apx-physical-headless-pilot-v1' /etc/apx-physical-pilot || fail "pilot marker differs"
[[ $(/usr/bin/xargs < /sys/block/nvme0n1/device/serial) == S4DYNX0R253702 ]] || fail "disk serial differs"
[[ $(/usr/bin/sfdisk --disk-id /dev/nvme0n1) == AC9FC0BD-2162-43A9-AAE6-3F654FF6F275 ]] || fail "GPT identity differs"
[[ $(/usr/bin/efibootmgr | /usr/bin/awk '/^BootCurrent:/ {print $2}') == 0005 ]] || fail "Linux is not the current loader"
[[ $(/usr/bin/efibootmgr | /usr/bin/awk '/^BootOrder:/ {print $2}') == 0005,0006,0000,2001,2002,2003 ]] || fail "Linux-first BootOrder differs"
! /usr/bin/efibootmgr | /usr/bin/grep -q '^BootNext:' || fail "an unrelated BootNext is armed"
[[ ! -e $backup ]] || fail "backup destination already exists"
for source in "$source_service" "$source_runner" "$source_metadata"; do
    [[ -f $source && ! -L $source ]] || fail "source differs: $source"
done
for target in "$target_service" "$target_runner" "$target_metadata"; do
    [[ -f $target && ! -L $target ]] || fail "installed target differs: $target"
done
/usr/bin/python3 -m unittest discover -s tests >/dev/null || fail "repository tests failed"
/usr/bin/python3 -m py_compile "$source_service" "$source_runner" || fail "Python source does not compile"
/usr/bin/python3 - "$source_metadata" <<'PY' || fail "native metadata differs"
import json, re, sys
value = json.load(open(sys.argv[1]))
assert value["profile"] == "apx-native-environment-v2"
assert value["schema"] == 2 and value["state"] == "ready"
assert value["name"] == "windows" and value["requested_size_gib"] == 120
assert re.fullmatch(r"[0-9a-f]{8}-[0-9a-f-]{27}", value["generation"])
PY

/usr/bin/install -d -m 0700 "$backup"
/usr/bin/cp --archive -- "$target_service" "$backup/apx-environment-switch-v1.py"
/usr/bin/cp --archive -- "$target_runner" "$backup/apx-native-boot-runner-v1.py"
/usr/bin/cp --archive -- "$target_metadata" "$backup/windows.json"
/usr/bin/sha256sum "$target_service" "$target_runner" "$target_metadata" >"$backup/before.sha256"
rollback() {
    trap - ERR
    /usr/bin/cp --archive -- "$backup/apx-environment-switch-v1.py" "$target_service"
    /usr/bin/cp --archive -- "$backup/apx-native-boot-runner-v1.py" "$target_runner"
    /usr/bin/cp --archive -- "$backup/windows.json" "$target_metadata"
    /usr/bin/systemctl restart apx-environment-switch-v1.service || true
    fail "installation failed; the exact previous integration was restored"
}
trap rollback ERR
/usr/bin/install -m 0755 -o root -g root -- "$source_service" "$target_service"
/usr/bin/install -m 0755 -o root -g root -- "$source_runner" "$target_runner"
/usr/bin/install -m 0400 -o root -g root -- "$source_metadata" "$target_metadata"
/usr/bin/systemctl restart apx-environment-switch-v1.service
/usr/bin/systemctl is-active --quiet apx-environment-switch-v1.service
"$target_runner" --target windows --validate-only
/usr/bin/cmp -s -- "$source_service" "$target_service"
/usr/bin/cmp -s -- "$source_runner" "$target_runner"
/usr/bin/cmp -s -- "$source_metadata" "$target_metadata"
trap - ERR
/usr/bin/sha256sum "$target_service" "$target_runner" "$target_metadata" >"$backup/after.sha256"
/usr/bin/chmod 0600 "$backup/before.sha256" "$backup/after.sha256"
/usr/bin/printf 'APX native Windows is ready in the HUB; rollback: %s\n' "$backup"
