#!/usr/bin/env bash
set -Eeuo pipefail

# Stage the repaired Host daemon/unit, activate the Fn bridge in the current
# QuickShell session, and make Bluetooth usable now. The daemon is deliberately
# not restarted: its Unix socket is inode-bound into the active Hub, so full
# activation belongs to a coordinated Hub relaunch or the next normal boot.

readonly repository=/root/apx-host-development-mode-v1/apx
readonly daemon=/usr/lib/apx/apx-host-services-v3.py
readonly unit=/etc/systemd/system/apx-host-services-v3.service
readonly keyboard=/usr/lib/apx/apx-legion-brightness-keys-v1.py
readonly runtime=/usr/lib/apx/apx-lab-runtime.py
readonly hypr_seed=/usr/share/apx/config-seeds/environment-shell-v1/hypr/hyprland.lua
readonly hypr_live=/var/lib/apx/environments/hub/home/apx/.config/hypr/hyprland.lua
readonly backup="/var/lib/apx/backups/$(date -u +%Y%m%dT%H%M%SZ)-host-connectivity-input-v1"

fail() { echo "APX connectivity/input deployment refused: $*" >&2; exit 2; }
[[ $EUID -eq 0 && $PWD == "$repository" ]] || fail 'root or repository differs'
[[ $(</etc/hostname) == apx-host && $(</sys/class/dmi/id/product_name) == 82JU ]] \
    || fail 'Host identity differs'
[[ $(/usr/bin/machinectl show apx-hub -p State --value) == running ]] || fail 'Hub is not running'
[[ ! -e $backup ]] || fail 'backup already exists'

declare -A sources=(
    [daemon]="$repository/scripts/physical-pilot/apx-host-services-v3.py"
    [unit]="$repository/config/systemd/apx-host-services-v3.service"
    [keyboard]="$repository/scripts/physical-pilot/apx-legion-brightness-keys-v1.py"
    [runtime]="$repository/scripts/virtual-lab/apx-lab-runtime.py"
    [hypr_seed]="$repository/config/environment-shell-v1/hypr/hyprland.lua"
    [hypr_live]="$repository/config/environment-shell-v1/hypr/hyprland.lua"
)
declare -A targets=(
    [daemon]="$daemon" [unit]="$unit" [keyboard]="$keyboard" [runtime]="$runtime"
    [hypr_seed]="$hypr_seed" [hypr_live]="$hypr_live"
)
for name in daemon unit keyboard runtime hypr_seed hypr_live; do
    [[ -f ${sources[$name]} && ! -L ${sources[$name]} ]] || fail "source differs: $name"
    [[ -f ${targets[$name]} && ! -L ${targets[$name]} ]] || fail "target differs: $name"
done

/usr/bin/python3 -m py_compile "${sources[daemon]}" "${sources[keyboard]}" "${sources[runtime]}"
/usr/bin/systemd-analyze verify "${sources[unit]}"
/usr/bin/python3 -m unittest tests.test_apx_host_services_v3_physical \
    tests.test_apx_legion_hardware_profiles tests.test_apx_work_defaults >/dev/null
/usr/bin/python3 -m unittest tests.test_apx_lab_runtime_desktop_seed >/dev/null

if /usr/bin/bluetoothctl show | /usr/bin/grep -q $'^\tPowered: yes$'; then
    bluetooth_was_powered=yes
else
    bluetooth_was_powered=no
fi
readonly bluetooth_was_powered

/usr/bin/install -d -o root -g root -m 0700 "$backup"
for name in daemon unit keyboard runtime hypr_seed hypr_live; do
    /usr/bin/cp --archive -- "${targets[$name]}" "$backup/$name.previous"
done

reload_hyprland() {
    /usr/bin/machinectl shell apx@apx-hub /usr/bin/bash -lc '
        export XDG_RUNTIME_DIR=/run/apx/session-1000
        for socket in "$XDG_RUNTIME_DIR"/hypr/*/.socket.sock; do
            test -S "$socket" || continue
            export HYPRLAND_INSTANCE_SIGNATURE=$(basename "$(dirname "$socket")")
            exec /usr/bin/hyprctl reload
        done
        exit 1
    ' >/dev/null 2>&1
}

stop_fn_bridge() {
    /usr/bin/machinectl shell apx@apx-hub /usr/bin/bash -lc \
        "/usr/bin/pkill -f '^python3 /usr/lib/apx/apx-legion-brightness-keys-v1.py$' || true" \
        >/dev/null 2>&1
}

rollback() {
    local status=$?
    trap - ERR
    set +e
    local name
    for name in daemon unit keyboard runtime hypr_seed hypr_live; do
        /usr/bin/cp --archive -- "$backup/$name.previous" "${targets[$name]}"
    done
    /usr/bin/systemctl daemon-reload
    reload_hyprland
    if [[ $bluetooth_was_powered == no ]]; then /usr/bin/bluetoothctl power off >/dev/null 2>&1; fi
    stop_fn_bridge
    /usr/bin/machinectl shell apx@apx-hub /usr/bin/pkill -x quickshell >/dev/null 2>&1
    echo 'APX connectivity/input deployment rolled back' >&2
    exit "$status"
}
trap rollback ERR

# Preserve the existing inodes: the runtime files are already bind-mounted
# into the Hub. An in-place copy lets the supervised QuickShell restart see the
# repaired bridge without relaunching Hyprland or the container.
/usr/bin/cp -- "${sources[daemon]}" "$daemon"
/usr/bin/install -o root -g root -m 0644 "${sources[unit]}" "$unit"
/usr/bin/cp -- "${sources[keyboard]}" "$keyboard"
/usr/bin/cp -- "${sources[runtime]}" "$runtime"
/usr/bin/cp -- "${sources[hypr_seed]}" "$hypr_seed"
/usr/bin/cp -- "${sources[hypr_live]}" "$hypr_live"
/usr/bin/chown root:root "$daemon" "$keyboard" "$runtime"
/usr/bin/chmod 0755 "$daemon" "$keyboard" "$runtime"
/usr/bin/systemctl daemon-reload
reload_hyprland

/usr/bin/rfkill unblock bluetooth
bluetooth_unblocked=no
for _ in {1..50}; do
    if ! /usr/bin/bluetoothctl show | /usr/bin/grep -q 'PowerState: off-blocked'; then
        bluetooth_unblocked=yes
        break
    fi
    /usr/bin/sleep 0.1
done
if [[ $bluetooth_unblocked != yes ]]; then
    echo 'APX connectivity/input deployment failed: Bluetooth did not finish unblocking' >&2
    false
fi
/usr/bin/bluetoothctl power on >/dev/null
stop_fn_bridge
/usr/bin/machinectl shell apx@apx-hub /usr/bin/pkill -x quickshell >/dev/null

bridge_ready=no
for _ in {1..80}; do
    if /usr/bin/machinectl shell apx@apx-hub /usr/bin/bash -lc \
            'test "$(pgrep -f "^python3 /usr/lib/apx/apx-legion-brightness-keys-v1.py$" | wc -l)" -eq 1' \
            >/dev/null 2>&1; then
        bridge_ready=yes
        break
    fi
    /usr/bin/sleep 0.1
done
if [[ $bridge_ready != yes ]]; then
    echo 'APX connectivity/input deployment failed: exactly one Fn bridge did not remain running' >&2
    false
fi
bluetooth_ready=no
for _ in {1..50}; do
    if /usr/bin/bluetoothctl show | /usr/bin/grep -q $'^\tPowered: yes$'; then
        bluetooth_ready=yes
        break
    fi
    /usr/bin/sleep 0.1
done
if [[ $bluetooth_ready != yes ]]; then
    echo 'APX connectivity/input deployment failed: Bluetooth did not power on' >&2
    false
fi
/usr/bin/systemctl is-active --quiet apx-host-services-v3.service

for name in daemon unit keyboard runtime hypr_seed hypr_live; do
    /usr/bin/cmp -- "${sources[$name]}" "${targets[$name]}"
done
/usr/bin/chown -R root:root "$backup"
/usr/bin/find "$backup" -type f -exec chmod 0600 {} +
trap - ERR
echo "APX connectivity/input staged; Fn and Bluetooth active; daemon activation pending coordinated Hub relaunch; backup: $backup"
