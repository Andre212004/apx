#!/usr/bin/env bash
set -Eeuo pipefail

# Install only the active Hyprland configuration and its legacy fallback so a
# temporary QuickShell restart reveals plain black instead of Hyprland artwork.

readonly repository=/root/apx-host-development-mode-v1/apx
readonly source_lua=$repository/config/environment-shell-v1/hypr/hyprland.lua
readonly source_legacy=$repository/config/environment-shell-v1/hyprland/hyprland.conf
readonly hub_home=/var/lib/apx/environments/hub/home/apx
readonly live_lua=$hub_home/.config/hypr/hyprland.lua
readonly live_legacy=$hub_home/.config/hyprland/hyprland.conf
readonly source_lua_sha256=be195a30f0e9e4b3657fce3c2a2a375ac07e6d9d07258cfa180cf55b7867dcf8
readonly source_legacy_sha256=eac1bcb38d499c524221550bcb0018a34011cd319b2e9f11351095cfada460f8
readonly previous_lua_sha256=5990556173a4958a6e2d7a8d3a321ea92442174098c21ee0076678c0ae29a5ca
readonly previous_legacy_sha256=7c571ef6e748635d65545f68c01a7253d94db21c355bdaeca8e9284a509877ae
readonly backup="/var/lib/apx/backups/$(date -u +%Y%m%dT%H%M%SZ)-hyprland-black-fallback-v1"

fail() { echo "APX Hyprland black fallback deployment refused: $*" >&2; exit 2; }

[[ $EUID -eq 0 && $PWD == "$repository" ]] || fail 'root or repository differs'
[[ $(</etc/hostname) == apx-host && $(</sys/class/dmi/id/sys_vendor) == LENOVO \
   && $(</sys/class/dmi/id/product_name) == 82JU ]] || fail 'Host identity differs'
[[ $(machinectl show apx-hub -p State --value) == running ]] || fail 'Hub is not running'
for path in "$source_lua" "$source_legacy" "$live_lua" "$live_legacy"; do
    [[ -f $path && ! -L $path ]] || fail "configuration differs: $path"
done
[[ $(sha256sum "$source_lua" | awk '{print $1}') == "$source_lua_sha256" \
   && $(sha256sum "$source_legacy" | awk '{print $1}') == "$source_legacy_sha256" ]] \
    || fail 'source digest differs'
[[ $(sha256sum "$live_lua" | awk '{print $1}') == "$previous_lua_sha256" \
   && $(sha256sum "$live_legacy" | awk '{print $1}') == "$previous_legacy_sha256" ]] \
    || fail 'installed predecessor differs'
[[ ! -e $backup ]] || fail 'backup already exists'

session_environment=$(
    systemd-run -M apx-hub --uid=apx --pipe --wait --quiet /usr/bin/bash -lc '
        pid=$(pgrep -x quickshell | head -n1)
        test -n "$pid"
        tr "\0" "\n" < "/proc/$pid/environ" |
            sed -n "/^XDG_RUNTIME_DIR=/p;/^HYPRLAND_INSTANCE_SIGNATURE=/p"
    '
)
runtime_dir=$(sed -n 's/^XDG_RUNTIME_DIR=//p' <<<"$session_environment")
signature=$(sed -n 's/^HYPRLAND_INSTANCE_SIGNATURE=//p' <<<"$session_environment")
[[ $runtime_dir == /run/apx/session-1000 && $signature =~ ^[A-Za-z0-9_.-]+$ ]] \
    || fail 'graphical session environment differs'

python3 -m unittest tests.test_apx_work_defaults tests.test_apx_environment_switch_v1 >/dev/null
install -d -o root -g root -m 0700 "$backup"
cp --archive -- "$live_lua" "$backup/hyprland.lua.previous"
cp --archive -- "$live_legacy" "$backup/hyprland.conf.previous"

reload_hyprland() {
    systemd-run -M apx-hub --uid=apx --pipe --wait --quiet \
        --setenv="XDG_RUNTIME_DIR=$runtime_dir" \
        --setenv="HYPRLAND_INSTANCE_SIGNATURE=$signature" \
        /usr/bin/hyprctl reload >/dev/null
}

rollback() {
    local status=$?
    trap - ERR
    set +e
    cp --archive -- "$backup/hyprland.lua.previous" "$live_lua"
    cp --archive -- "$backup/hyprland.conf.previous" "$live_legacy"
    reload_hyprland
    echo "APX Hyprland black fallback rolled back; backup: $backup" >&2
    exit "$status"
}
trap rollback ERR

install -o 1000 -g 1000 -m 0600 "$source_lua" "$live_lua"
install -o 1000 -g 1000 -m 0600 "$source_legacy" "$live_legacy"
reload_hyprland
/usr/bin/sleep 0.3

options=$(
    systemd-run -M apx-hub --uid=apx --pipe --wait --quiet \
        --setenv="XDG_RUNTIME_DIR=$runtime_dir" \
        --setenv="HYPRLAND_INSTANCE_SIGNATURE=$signature" \
        /usr/bin/bash -lc '
            hyprctl getoption misc:force_default_wallpaper -j
            hyprctl getoption misc:disable_hyprland_logo -j
            hyprctl getoption misc:disable_splash_rendering -j
        '
)
python3 -c '
import json, sys
values = [json.loads(line) for line in sys.stdin if line.strip()]
assert values[0].get("int") == 0
assert values[1].get("bool") is True
assert values[2].get("bool") is True
' <<<"$options"

cmp -- "$source_lua" "$live_lua"
cmp -- "$source_legacy" "$live_legacy"
chown -R root:root "$backup"
find "$backup" -type f -exec chmod 0600 {} +
trap - ERR
echo "APX Hyprland fallback is plain black; backup: $backup"
