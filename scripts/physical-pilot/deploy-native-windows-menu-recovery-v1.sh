#!/usr/bin/env bash
set -Eeuo pipefail

# Non-rebooting rollout of the menu-owned native-Windows failure controls.
# This installs code and UI only. It never mounts or writes a Windows volume,
# arms BootNext, starts the finalizer, or changes GPT state.

readonly repository=/root/apx-host-development-mode-v1/apx
readonly live_ui=/var/lib/apx/environments/hub/home/apx/.config/quickshell/apx/shell.qml
readonly seed_ui=/usr/share/apx/config-seeds/environment-shell-v1/quickshell/apx/shell.qml
readonly service=/usr/lib/apx/apx-environment-switch-v1.py
readonly client=/usr/lib/apx/apx-environment-switch-client-v1.py
readonly contract=/usr/lib/apx/apx_environment_switch_contract.py
readonly finalizer=/usr/lib/apx/apx-native-windows-lifecycle-finalize-v1.py
readonly recovery=/usr/lib/apx/apx-native-windows-recovery-v1.py
readonly refresh=/usr/lib/apx/refresh-native-windows-installer-v2.sh
readonly winpe=/usr/share/apx/native-windows-lifecycle-v1/winpe/apx-media.cmd
readonly pending=/var/lib/apx/native-environments/windows-pending.json
readonly backup="/var/lib/apx/backups/$(date -u +%Y%m%dT%H%M%SZ)-native-windows-menu-recovery-v1"

fail() { echo "APX native Windows menu recovery deployment refused: $*" >&2; exit 2; }
[[ $EUID -eq 0 && $PWD == "$repository" ]] || fail 'root or repository differs'
[[ $(</etc/hostname) == apx-host && $(</sys/class/dmi/id/product_name) == 82JU ]] || fail 'Host identity differs'
[[ $(</sys/class/power_supply/ADP0/online) == 1 && $(</sys/class/power_supply/BAT0/capacity) -ge 40 ]] || fail 'power differs'
[[ $(/usr/bin/xargs </sys/block/nvme0n1/device/serial) == S4DYNX0R253702 \
        && $(/usr/bin/sfdisk --disk-id /dev/nvme0n1) == AC9FC0BD-2162-43A9-AAE6-3F654FF6F275 ]] || fail 'disk identity differs'
[[ -z $(/usr/bin/efibootmgr | /usr/bin/awk '/^BootNext:/ {print}') ]] || fail 'BootNext is already armed'
[[ ! -e $backup && ! -e /run/apx/environment-management-v1.lock ]] || fail 'deployment staging or management lock exists'

declare -A sources=(
    [ui]="$repository/config/environment-shell-v1/quickshell/apx/shell.qml"
    [service]="$repository/scripts/physical-pilot/apx-environment-switch-v1.py"
    [client]="$repository/scripts/physical-pilot/apx-environment-switch-client-v1.py"
    [contract]="$repository/src/apx_environment_switch_contract.py"
    [finalizer]="$repository/scripts/physical-pilot/apx-native-windows-lifecycle-finalize-v1.py"
    [recovery]="$repository/scripts/physical-pilot/apx-native-windows-recovery-v1.py"
    [refresh]="$repository/scripts/physical-pilot/refresh-native-windows-installer-v2.sh"
    [winpe]="$repository/config/system-images-v1/windows-internal-winpe/apx-media.cmd"
)
for source in "${sources[@]}"; do [[ -f $source && ! -L $source ]] || fail "source differs: $source"; done
for target in "$live_ui" "$seed_ui" "$service" "$client" "$contract" "$finalizer" "$winpe"; do
    [[ -f $target && ! -L $target ]] || fail "installed target differs: $target"
done
[[ ! -e $recovery && ! -L $recovery && ! -e $refresh && ! -L $refresh ]] || fail 'new recovery target already exists'
! /usr/bin/grep -Fiq findstr "${sources[winpe]}" || fail 'WinPE source still depends on findstr'
/usr/bin/python3 - "$pending" <<'PY' || fail 'pending creation is not menu-recoverable'
import json
from pathlib import Path
import re
import stat
import sys

path = Path(sys.argv[1]); info = path.lstat(); raw = path.read_bytes(); value = json.loads(raw)
if path.is_symlink() or not path.is_file() or (info.st_uid, info.st_gid) != (0, 0) \
        or stat.S_IMODE(info.st_mode) != 0o400 or len(raw) > 4096 \
        or value.get("schema") != 1 or value.get("profile") != "apx-native-windows-pending-v1" \
        or value.get("action") != "create" or value.get("stage") != "installing" \
        or value.get("name") != "windows" or value.get("requested_size_gib") not in {80, 120, 160} \
        or re.fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
                        str(value.get("generation", ""))) is None:
    raise SystemExit(1)
PY

/usr/bin/bash -n "${sources[refresh]}"
/usr/bin/python3 -m py_compile "${sources[service]}" "${sources[client]}" "${sources[contract]}" \
    "${sources[finalizer]}" "${sources[recovery]}"
/usr/bin/python3 -m unittest tests.test_apx_environment_switch_v1 tests.test_apx_native_windows_storage_v1 >/dev/null

/usr/bin/install -d -o root -g root -m 0700 "$backup"
declare -A targets=(
    [ui]="$live_ui" [seed_ui]="$seed_ui" [service]="$service" [client]="$client"
    [contract]="$contract" [finalizer]="$finalizer" [winpe]="$winpe"
)
for name in "${!targets[@]}"; do /usr/bin/cp --archive -- "${targets[$name]}" "$backup/$name.previous"; done
rollback() {
    set +e
    for name in "${!targets[@]}"; do /usr/bin/cp --archive -- "$backup/$name.previous" "${targets[$name]}"; done
    /usr/bin/unlink "$recovery" 2>/dev/null || true
    /usr/bin/unlink "$refresh" 2>/dev/null || true
    /usr/bin/systemctl restart apx-environment-switch-v1.service
}
trap rollback ERR

/usr/bin/systemctl stop apx-native-windows-lifecycle-finalize-v1.service 2>/dev/null || true
/usr/bin/install -o 1000 -g 1000 -m 0600 "${sources[ui]}" "$live_ui"
/usr/bin/install -o root -g root -m 0644 "${sources[ui]}" "$seed_ui"
/usr/bin/install -o root -g root -m 0755 "${sources[service]}" "$service"
/usr/bin/install -o root -g root -m 0755 "${sources[client]}" "$client"
/usr/bin/install -o root -g root -m 0644 "${sources[contract]}" "$contract"
/usr/bin/install -o root -g root -m 0755 "${sources[finalizer]}" "$finalizer"
/usr/bin/install -o root -g root -m 0755 "${sources[recovery]}" "$recovery"
/usr/bin/install -o root -g root -m 0755 "${sources[refresh]}" "$refresh"
/usr/bin/install -o root -g root -m 0644 "${sources[winpe]}" "$winpe"
/usr/bin/systemctl restart apx-environment-switch-v1.service
/usr/bin/systemctl is-active --quiet apx-environment-switch-v1.service

/usr/bin/cmp "${sources[ui]}" "$live_ui"
/usr/bin/cmp "${sources[ui]}" "$seed_ui"
for name in service client contract finalizer recovery refresh winpe; do
    case $name in
        service) target=$service ;; client) target=$client ;; contract) target=$contract ;;
        finalizer) target=$finalizer ;; recovery) target=$recovery ;; refresh) target=$refresh ;; winpe) target=$winpe ;;
    esac
    /usr/bin/cmp "${sources[$name]}" "$target"
done
[[ -z $(/usr/bin/efibootmgr | /usr/bin/awk '/^BootNext:/ {print}') ]] || fail 'deployment unexpectedly armed BootNext'
/usr/bin/chown -R root:root "$backup"
/usr/bin/find "$backup" -type f -exec chmod 0600 {} +
trap - ERR
echo "APX native Windows menu recovery deployed without disk or reboot action; backup: $backup"
