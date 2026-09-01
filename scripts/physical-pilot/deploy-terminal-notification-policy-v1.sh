#!/usr/bin/env bash
set -Eeuo pipefail

# Install only the terminal-notification policy, focus watcher and the launcher
# line that preserves it on later Environment sessions. No seed, runtime,
# package, Host service or other dirty-checkout file is installed.

readonly repository=/root/apx-host-development-mode-v1/apx
readonly source_config=$repository/config/environment-shell-v1/mako/config
readonly source_watcher=$repository/config/environment-shell-v1/local/bin/apx-notification-focus-v1
readonly source_launcher=$repository/config/environment-shell-v1/local/bin/apx-shell-v1
readonly hub_home=/var/lib/apx/environments/hub/home/apx
readonly live_config=$hub_home/.config/mako/config
readonly live_watcher=$hub_home/.local/bin/apx-notification-focus-v1
readonly live_launcher=$hub_home/.local/bin/apx-shell-v1
readonly container_watcher=/home/apx/.local/bin/apx-notification-focus-v1
readonly config_sha256=53cda37280ea02455e62879186619aae296b08e8f10bd8cc1c09fd25239cf122
readonly watcher_sha256=835cc0302f10f01c2417077884fca7f9b9a6b95b2328ac8d32dccc4e93ca7cc0
readonly launcher_sha256=19a04a0700f8f9ed512f5b6433a4ea9c0b114222810894095654b36bfc55423e
readonly previous_launcher_sha256=f5f8e6aeb729ea92c1561c6fe90c00e4692d17272e469f06ed7f7fbbccf5aca4
readonly backup="/var/lib/apx/backups/$(date -u +%Y%m%dT%H%M%SZ)-terminal-notification-policy-v1"
readonly service_token=$(date -u +%s%N)
readonly mako_unit="apx-mako-live-$service_token.service"
readonly watcher_unit="apx-notification-focus-$service_token.service"
readonly rollback_mako_unit="apx-mako-rollback-$service_token.service"

fail() { echo "APX terminal notification deployment refused: $*" >&2; exit 2; }

[[ $EUID -eq 0 && $PWD == "$repository" ]] || fail 'root or repository differs'
[[ $(</etc/hostname) == apx-host && $(</sys/class/dmi/id/sys_vendor) == LENOVO \
   && $(</sys/class/dmi/id/product_name) == 82JU ]] || fail 'Host identity differs'
[[ $(/usr/bin/machinectl show apx-hub -p State --value) == running ]] \
    || fail 'Hub is not running'
[[ -f $source_config && -f $source_watcher && -f $source_launcher ]] \
    || fail 'source files differ'
[[ -f $live_launcher && ! -L $live_launcher && ! -e $live_config && ! -e $live_watcher ]] \
    || fail 'installed predecessor differs'
[[ $(sha256sum "$source_config" | awk '{print $1}') == "$config_sha256" \
   && $(sha256sum "$source_watcher" | awk '{print $1}') == "$watcher_sha256" \
   && $(sha256sum "$source_launcher" | awk '{print $1}') == "$launcher_sha256" ]] \
    || fail 'source digest differs'
[[ $(sha256sum "$live_launcher" | awk '{print $1}') == "$previous_launcher_sha256" ]] \
    || fail 'installed launcher is not the admitted predecessor'
[[ ! -e $backup ]] || fail 'backup already exists'

session_environment=$(
    /usr/bin/systemd-run -M apx-hub --uid=apx --pipe --wait --quiet \
        /usr/bin/bash -lc '
            pid=$(pgrep -x quickshell | head -n1)
            test -n "$pid"
            for key in WAYLAND_DISPLAY HYPRLAND_INSTANCE_SIGNATURE; do
                value=$(tr "\0" "\n" < "/proc/$pid/environ" | sed -n "s/^$key=//p")
                printf "%s=%s\n" "$key" "$value"
            done
        '
)
wayland_display=$(sed -n 's/^WAYLAND_DISPLAY=//p' <<<"$session_environment")
hyprland_signature=$(sed -n 's/^HYPRLAND_INSTANCE_SIGNATURE=//p' <<<"$session_environment")
[[ $wayland_display =~ ^wayland-[0-9]+$ && $hyprland_signature =~ ^[A-Za-z0-9_.-]+$ ]] \
    || fail 'graphical session environment differs'

/usr/bin/python3 -m py_compile "$source_watcher"
/usr/bin/bash -n "$source_launcher"
/usr/bin/python3 -m unittest tests.test_apx_work_defaults >/dev/null

/usr/bin/install -d -o root -g root -m 0700 "$backup"
/usr/bin/cp --archive -- "$live_launcher" "$backup/apx-shell-v1.previous"

stop_live_services() {
    /usr/bin/systemctl -M apx-hub stop "$watcher_unit" "$mako_unit" \
        >/dev/null 2>&1 || true
    /usr/bin/systemd-run -M apx-hub --uid=apx --pipe --wait --quiet \
        /usr/bin/pkill -x mako >/dev/null 2>&1 || true
}

start_live_service() {
    local unit=$1
    shift
    /usr/bin/systemd-run -M apx-hub --uid=apx --unit="$unit" --collect --quiet \
        --setenv=XDG_RUNTIME_DIR=/run/apx/session-1000 \
        --setenv=DBUS_SESSION_BUS_ADDRESS=unix:path=/run/apx/session-1000/bus \
        --setenv="WAYLAND_DISPLAY=$wayland_display" \
        --setenv="HYPRLAND_INSTANCE_SIGNATURE=$hyprland_signature" \
        "$@"
}

rollback() {
    local status=$?
    trap - ERR
    set +e
    stop_live_services
    /usr/bin/cp --archive -- "$backup/apx-shell-v1.previous" "$live_launcher"
    [[ ! -e $live_config ]] || /usr/bin/unlink -- "$live_config"
    [[ ! -e $live_watcher ]] || /usr/bin/unlink -- "$live_watcher"
    start_live_service "$rollback_mako_unit" /usr/bin/mako
    echo "APX terminal notification deployment rolled back; backup: $backup" >&2
    exit "$status"
}
trap rollback ERR

/usr/bin/install -d -o 1000 -g 1000 -m 0700 "$hub_home/.config/mako"
/usr/bin/install -o 1000 -g 1000 -m 0600 "$source_config" "$live_config"
/usr/bin/install -o 1000 -g 1000 -m 0700 "$source_watcher" "$live_watcher"
/usr/bin/install -o 1000 -g 1000 -m 0600 "$source_launcher" "$live_launcher"

stop_live_services
start_live_service "$mako_unit" /usr/bin/mako

for _ in {1..30}; do
    /usr/bin/systemctl -M apx-hub is-active --quiet "$mako_unit" && break
    /usr/bin/sleep 0.1
done
/usr/bin/systemctl -M apx-hub is-active --quiet "$mako_unit"

# Prove focus dismissal by creating a terminal notification while a terminal
# is focused, then starting the watcher: its initial focus check must remove it.
/usr/bin/systemd-run -M apx-hub --uid=apx --pipe --wait --quiet \
    --setenv=XDG_RUNTIME_DIR=/run/apx/session-1000 \
    --setenv=DBUS_SESSION_BUS_ADDRESS=unix:path=/run/apx/session-1000/bus \
    /usr/bin/notify-send -a kitty 'APX notification policy test' >/dev/null
start_live_service "$watcher_unit" "$container_watcher"
for _ in {1..30}; do
    /usr/bin/systemctl -M apx-hub is-active --quiet "$watcher_unit" && break
    /usr/bin/sleep 0.1
done
/usr/bin/systemctl -M apx-hub is-active --quiet "$watcher_unit"
/usr/bin/sleep 0.3

remaining=$(
    /usr/bin/systemd-run -M apx-hub --uid=apx --pipe --wait --quiet \
        --setenv=XDG_RUNTIME_DIR=/run/apx/session-1000 \
        --setenv=DBUS_SESSION_BUS_ADDRESS=unix:path=/run/apx/session-1000/bus \
        /usr/bin/makoctl list -j
)
/usr/bin/python3 -c '
import json, sys
assert not any(str(item.get("app_name", "")).casefold() in {"kitty", "alacritty"}
               for item in json.load(sys.stdin))
' <<<"$remaining"

/usr/bin/cmp -- "$source_config" "$live_config"
/usr/bin/cmp -- "$source_watcher" "$live_watcher"
/usr/bin/cmp -- "$source_launcher" "$live_launcher"
/usr/bin/systemctl -M apx-hub is-active --quiet "$watcher_unit"
/usr/bin/chown -R root:root "$backup"
/usr/bin/find "$backup" -type f -exec chmod 0600 {} +
trap - ERR
echo "APX terminal notifications now clear on focus and expire after 8 seconds; backup: $backup"
