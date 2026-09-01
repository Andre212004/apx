#!/usr/bin/env bash
set -euo pipefail

readonly CONFIG=/run/apx-h0/hyprland.conf
readonly RUNTIME=/run/user/1000
readonly SEATD_SOCKET=/run/seatd.sock
seatd_pid=

cleanup() {
  if [[ -n $seatd_pid ]] && kill -0 "$seatd_pid" 2>/dev/null; then
    kill -TERM "$seatd_pid" 2>/dev/null || true
    wait "$seatd_pid" 2>/dev/null || true
  fi
}
trap cleanup EXIT HUP INT TERM

[[ $(id -u) == 0 ]]
[[ -c /dev/dri/card2 && -c /dev/dri/renderD129 ]]
[[ -c /dev/input/event0 && -c /dev/input/event1 && -c /dev/tty2 ]]
[[ -f $CONFIG && ! -L $CONFIG ]]
[[ $(stat -Lc '%t:%T' /dev/dri/card2) == e2:2 ]]
[[ $(stat -Lc '%t:%T' /dev/dri/renderD129) == e2:81 ]]
[[ $(stat -Lc '%t:%T' /dev/input/event0) == d:43 ]]
[[ $(stat -Lc '%t:%T' /dev/input/event1) == d:4b ]]
[[ $(stat -Lc '%t:%T' /dev/tty2) == 4:2 ]]

install -d -m 0700 -o 1000 -g 1000 "$RUNTIME"
rm -f -- "$SEATD_SOCKET"
SEATD_VTBOUND=0 /usr/bin/seatd -u apx -l info &
seatd_pid=$!

for _ in {1..100}; do
  [[ -S $SEATD_SOCKET ]] && break
  kill -0 "$seatd_pid"
  read -r -t 0.05 _ </dev/null || true
done
[[ -S $SEATD_SOCKET ]]

/usr/bin/setpriv \
  --reuid=1000 --regid=1000 --groups=5,983,987,992 \
  --no-new-privs --inh-caps=-all --ambient-caps=-all --bounding-set=-all -- \
  /usr/bin/env -i \
  HOME=/home/apx USER=apx LOGNAME=apx SHELL=/usr/bin/bash \
  PATH=/usr/bin XDG_RUNTIME_DIR="$RUNTIME" XDG_SESSION_TYPE=wayland \
  XDG_CURRENT_DESKTOP=Hyprland LIBSEAT_BACKEND=seatd SEATD_SOCK="$SEATD_SOCKET" \
  AQ_DRM_DEVICES=/dev/dri/card2 \
  /usr/bin/Hyprland --config "$CONFIG"
