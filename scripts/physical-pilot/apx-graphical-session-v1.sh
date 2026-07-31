#!/usr/bin/env bash
set -euo pipefail
[[ ${APX_SESSION_TRACE:-0} == 0 ]] || set -x

readonly CONFIG=/home/apx/.config/hyprland/hyprland.conf
readonly RUNTIME=/run/user/1000
readonly SEATD_SOCKET=/run/seatd.sock
readonly KEYBOARD_DEVICE=${APX_KEYBOARD_DEVICE:?}
readonly ELAN_MOUSE_DEVICE=${APX_ELAN_MOUSE_DEVICE:?}
readonly ELAN_TOUCHPAD_DEVICE=${APX_ELAN_TOUCHPAD_DEVICE:?}
seatd_pid=
dbus_pid=

cleanup() {
  if [[ -n $dbus_pid ]] && kill -0 "$dbus_pid" 2>/dev/null; then
    kill -TERM "$dbus_pid" 2>/dev/null || true
    wait "$dbus_pid" 2>/dev/null || true
  fi
  if [[ -n $seatd_pid ]] && kill -0 "$seatd_pid" 2>/dev/null; then
    kill -TERM "$seatd_pid" 2>/dev/null || true
    wait "$seatd_pid" 2>/dev/null || true
  fi
  rm -f -- "$RUNTIME/bus" "$SEATD_SOCKET"
}
trap cleanup EXIT HUP INT TERM

[[ $(id -u) == 0 ]]
[[ -c /dev/dri/card2 && $(stat -Lc '%t:%T' /dev/dri/card2) == e2:2 ]]
[[ -c /dev/dri/renderD129 && $(stat -Lc '%t:%T' /dev/dri/renderD129) == e2:81 ]]
for input_device in "$KEYBOARD_DEVICE" "$ELAN_MOUSE_DEVICE" "$ELAN_TOUCHPAD_DEVICE"; do
  [[ $input_device =~ ^/dev/input/event[0-9]+$ ]]
  [[ -c $input_device && $(stat -Lc '%t' "$input_device") == d ]]
done
[[ $KEYBOARD_DEVICE != "$ELAN_MOUSE_DEVICE" && $KEYBOARD_DEVICE != "$ELAN_TOUCHPAD_DEVICE" ]]
[[ $ELAN_MOUSE_DEVICE != "$ELAN_TOUCHPAD_DEVICE" ]]
[[ -c /dev/tty2 && $(stat -Lc '%t:%T' /dev/tty2) == 4:2 ]]
[[ -f $CONFIG && ! -L $CONFIG ]]

install -d -m 0700 -o 1000 -g 1000 "$RUNTIME"
rm -f -- "$RUNTIME/bus" "$SEATD_SOCKET"
SEATD_VTBOUND=0 /usr/bin/seatd -u apx -l info &
seatd_pid=$!
for _ in {1..100}; do
  [[ -S $SEATD_SOCKET ]] && break
  kill -0 "$seatd_pid"
  /usr/bin/sleep 0.05
done
[[ -S $SEATD_SOCKET ]]

/usr/bin/setpriv --reuid=1000 --regid=1000 --clear-groups --no-new-privs -- \
  /usr/bin/env -i HOME=/home/apx USER=apx LOGNAME=apx SHELL=/usr/bin/bash \
  PATH=/usr/bin XDG_RUNTIME_DIR="$RUNTIME" XDG_CONFIG_HOME=/home/apx/.config \
  XDG_CACHE_HOME=/home/apx/.cache XDG_DATA_HOME=/home/apx/.local/share \
  /usr/bin/dbus-daemon --session --address=unix:path="$RUNTIME/bus" \
  --nofork --nopidfile --nosyslog &
dbus_pid=$!
for _ in {1..100}; do
  [[ -S $RUNTIME/bus ]] && break
  kill -0 "$dbus_pid"
  /usr/bin/sleep 0.05
done
[[ -S $RUNTIME/bus ]]

/usr/bin/setpriv \
  --reuid=1000 --regid=1000 --groups=5,983,987,992 \
  --no-new-privs --inh-caps=-all --ambient-caps=-all --bounding-set=-all -- \
  /usr/bin/env -i HOME=/home/apx USER=apx LOGNAME=apx SHELL=/usr/bin/bash \
  PATH=/usr/bin XDG_RUNTIME_DIR="$RUNTIME" XDG_SESSION_TYPE=wayland \
  XDG_CURRENT_DESKTOP=Hyprland LIBSEAT_BACKEND=seatd SEATD_SOCK="$SEATD_SOCKET" \
  DBUS_SESSION_BUS_ADDRESS=unix:path="$RUNTIME/bus" \
  AQ_DRM_DEVICES=/dev/dri/card2 \
  /usr/bin/Hyprland --config "$CONFIG"
