#!/usr/bin/env bash
set -Eeuo pipefail

# Install only the reviewed QuickShell source in the running Hub. The official
# seed stays paired with its currently installed digest-pinned runtime; no Host
# service, runtime, Hyprland config, workload, package, or lifecycle state is
# changed. There is currently no registered Development Environment.

readonly repository=/root/apx-host-development-mode-v1/apx
readonly source_ui=$repository/config/environment-shell-v1/quickshell/apx/shell.qml
readonly hub_ui=/var/lib/apx/environments/hub/home/apx/.config/quickshell/apx/shell.qml
readonly hub_registration=/var/lib/apx/environments/hub/registration.json
readonly source_sha256=72fd55eb9703c7e5ba12d95c3df003b892803433324ac1c7c744dc49afadcaa7
readonly previous_sha256=aca096307a6258ce401f0e74ceb2ea9b3ff3ec17fbf8059d1154000a9d8c4166
readonly backup="/var/lib/apx/backups/$(date -u +%Y%m%dT%H%M%SZ)-quickshell-popup-interaction-v1"

fail() { echo "APX QuickShell popup deployment refused: $*" >&2; exit 2; }

[[ $EUID -eq 0 && $PWD == "$repository" ]] || fail 'root or repository differs'
[[ $(</etc/hostname) == apx-host && $(</sys/class/dmi/id/sys_vendor) == LENOVO \
   && $(</sys/class/dmi/id/product_name) == 82JU ]] || fail 'Host identity differs'
[[ $(/usr/bin/machinectl show apx-hub -p State --value) == running ]] \
    || fail 'Hub is not running'
[[ -f $source_ui && ! -L $source_ui && -f $hub_ui && ! -L $hub_ui ]] \
    || fail 'source or installed UI differs'
[[ -f $hub_registration && ! -L $hub_registration ]] || fail 'Hub registration differs'
[[ ! -e $backup ]] || fail 'backup already exists'
[[ $(/usr/bin/sha256sum "$source_ui" | /usr/bin/awk '{print $1}') == "$source_sha256" ]] \
    || fail 'source UI digest differs'
[[ $(/usr/bin/sha256sum "$hub_ui" | /usr/bin/awk '{print $1}') == "$previous_sha256" ]] \
    || fail 'installed Hub UI is not the admitted predecessor'

/usr/bin/python3 - "$hub_registration" <<'PY'
import json
import sys

value = json.load(open(sys.argv[1], encoding="utf-8"))
assert value.get("name") == "hub" and value.get("role") == "hub"
PY

/usr/bin/python3 -m unittest tests.test_apx_control_center_scale \
    tests.test_apx_environment_switch_v1 tests.test_apx_work_defaults >/dev/null

/usr/bin/install -d -o root -g root -m 0700 "$backup"
/usr/bin/cp --archive -- "$hub_ui" "$backup/hub-shell.qml.previous"

restart_shell() {
    /usr/bin/systemd-run -M apx-hub --uid=apx --pipe --wait --quiet \
        /usr/bin/pkill -x quickshell >/dev/null 2>&1 || true
}

rollback() {
    local status=$?
    trap - ERR
    set +e
    /usr/bin/cp --archive -- "$backup/hub-shell.qml.previous" "$hub_ui"
    restart_shell
    echo "APX QuickShell popup deployment rolled back to $previous_sha256" >&2
    exit "$status"
}
trap rollback ERR

# Preserve the live file inode because the Hub home is already visible to the
# running session. The supervised launcher recreates QuickShell afterward.
/usr/bin/cp -- "$source_ui" "$hub_ui"
/usr/bin/chown 1000:1000 "$hub_ui"
/usr/bin/chmod 0600 "$hub_ui"

restart_shell

ready=no
for _ in {1..100}; do
    if /usr/bin/systemd-run -M apx-hub --uid=apx --pipe --wait --quiet \
            /usr/bin/bash -lc 'test "$(pgrep -x quickshell | wc -l)" -eq 1' \
            >/dev/null 2>&1; then
        ready=yes
        break
    fi
    /usr/bin/sleep 0.1
done
if [[ $ready != yes ]]; then
    echo 'APX QuickShell popup deployment failed: exactly one supervised QuickShell did not return' >&2
    false
fi

/usr/bin/cmp -- "$source_ui" "$hub_ui"

popup_status=$(
    /usr/bin/systemd-run -M apx-hub --uid=apx --pipe --wait --quiet \
        /usr/bin/bash -lc '
            export XDG_RUNTIME_DIR=/run/apx/session-1000
            pid=$(pgrep -x quickshell | head -n1)
            /usr/bin/qs ipc --pid "$pid" call host openEnvironments >/dev/null
            /usr/bin/qs ipc --pid "$pid" call host popupStatus
        '
)
if [[ $popup_status != *'"kind":"environments"'* || $popup_status != *'"visible":true'* ]]; then
    echo "APX QuickShell popup deployment failed: Environment popup did not become visible: $popup_status" >&2
    false
fi

layers=$(
    /usr/bin/systemd-run -M apx-hub --uid=apx --pipe --wait --quiet \
        /usr/bin/bash -lc '
            export XDG_RUNTIME_DIR=/run/apx/session-1000
            for socket in "$XDG_RUNTIME_DIR"/hypr/*/.socket.sock; do
                test -S "$socket" || continue
                export HYPRLAND_INSTANCE_SIGNATURE=$(basename "$(dirname "$socket")")
                exec /usr/bin/hyprctl layers -j
            done
            exit 1
        '
)
/usr/bin/python3 -c '
import json, sys
value = json.load(sys.stdin)
assert any(layer.get("namespace") == "quickshell" and layer.get("w") == 430
           for monitor in value.values()
           for layer in monitor.get("levels", {}).get("3", []))
assert any(layer.get("namespace") == "quickshell"
           and layer.get("w", 0) > 1000 and layer.get("h", 0) > 500
           for monitor in value.values()
           for layer in monitor.get("levels", {}).get("2", []))
' <<<"$layers"

# The transparent Top-layer input surface is physically below the Overlay menu
# and covers the application area. The targeted tests prove its MouseArea calls
# closePopup; toggle the same button here to prove the live close path as well.
dismiss_status=$(
    /usr/bin/systemd-run -M apx-hub --uid=apx --pipe --wait --quiet \
        /usr/bin/bash -lc '
            export XDG_RUNTIME_DIR=/run/apx/session-1000
            pid=$(pgrep -x quickshell | head -n1)
            /usr/bin/qs ipc --pid "$pid" call host openEnvironments >/dev/null
            /usr/bin/qs ipc --pid "$pid" call host popupStatus
        '
)
if [[ $dismiss_status != *'"visible":false'* ]]; then
    echo "APX QuickShell popup deployment failed: live close path left popup visible: $dismiss_status" >&2
    false
fi

/usr/bin/chown -R root:root "$backup"
/usr/bin/find "$backup" -type f -exec chmod 0600 {} +
trap - ERR
echo "APX QuickShell popup interaction active; backup: $backup"
