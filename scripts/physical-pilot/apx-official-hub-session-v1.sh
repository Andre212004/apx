#!/usr/bin/env bash
set -euo pipefail

# The exact Hub keeps the Lua owner configuration.  The general graphical
# launcher supplies the independent copied Hyprland configuration instead.
readonly CONFIG=${APX_HYPRLAND_CONFIG:-/home/apx/.config/hypr/hyprland.lua}
readonly SESSION_MODE=${APX_SESSION_MODE:-desktop}
# This desktop is Host-supervised rather than a logind login. Keep its IPC
# outside /run/user/1000 so a short PAM session cannot remove Hyprland and
# QuickShell sockets while the graphical session is still running.
readonly RUNTIME=/run/apx/session-1000
readonly SEATD_SOCKET=/run/seatd.sock
readonly KEYBOARD_I8042=${APX_KEYBOARD_I8042_DEVICE:?}
readonly KEYBOARD_ITE=${APX_KEYBOARD_ITE_DEVICE:?}
readonly ELAN_MOUSE=${APX_ELAN_MOUSE_DEVICE:?}
readonly ELAN_TOUCHPAD=${APX_ELAN_TOUCHPAD_DEVICE:?}
readonly AUDIO_CONTROL=${APX_AUDIO_CONTROL_DEVICE:?}
readonly AUDIO_PLAYBACK=${APX_AUDIO_PLAYBACK_DEVICE:?}
readonly AUDIO_CAPTURE=${APX_AUDIO_CAPTURE_DEVICE:?}
readonly AUDIO_TIMER=${APX_AUDIO_TIMER_DEVICE:?}
readonly GPU_POLICY=${APX_GPU_POLICY:?}
readonly DISPLAY_CARD=${APX_DISPLAY_CARD:?}
readonly DISPLAY_RENDER=${APX_DISPLAY_RENDER:?}
readonly NVIDIA_CARD=${APX_NVIDIA_CARD_DEVICE:-}
readonly NVIDIA_RENDER=${APX_NVIDIA_RENDER_DEVICE:-}
dbus_pid=
pipewire_pid=
wireplumber_pid=
pulse_pid=
audio_state_pid=
hyprland_pid=

cleanup() {
  for process in "$audio_state_pid" "$pulse_pid" "$wireplumber_pid" "$pipewire_pid"; do
    if [[ -n $process ]] && kill -0 "$process" 2>/dev/null; then
      kill -TERM "$process" 2>/dev/null || true
      wait "$process" 2>/dev/null || true
    fi
  done
  if [[ -n $dbus_pid ]] && kill -0 "$dbus_pid" 2>/dev/null; then
    kill -TERM "$dbus_pid" 2>/dev/null || true
    wait "$dbus_pid" 2>/dev/null || true
  fi
  rm -f -- "$RUNTIME/bus"
}
trap cleanup EXIT HUP INT TERM

[[ $(id -u) == 0 ]]
[[ $SESSION_MODE == desktop || $SESSION_MODE == virtual-machine ]]
[[ $GPU_POLICY =~ ^(amd|hybrid|nvidia|vfio-guest)$ ]]
if [[ $GPU_POLICY == vfio-guest ]]; then
  [[ $SESSION_MODE == virtual-machine ]]
fi
[[ $DISPLAY_CARD =~ ^/dev/dri/card[0-9]+$ && -c $DISPLAY_CARD ]]
[[ $DISPLAY_RENDER =~ ^/dev/dri/renderD[0-9]+$ && -c $DISPLAY_RENDER ]]
[[ $(stat -Lc '%t' "$DISPLAY_CARD") == e2 ]]
[[ $(stat -Lc '%t' "$DISPLAY_RENDER") == e2 ]]
if [[ $GPU_POLICY == hybrid ]]; then
  [[ $NVIDIA_CARD =~ ^/dev/dri/card[0-9]+$ && -c $NVIDIA_CARD ]]
  [[ $NVIDIA_RENDER =~ ^/dev/dri/renderD[0-9]+$ && -c $NVIDIA_RENDER ]]
  [[ $(stat -Lc '%t' "$NVIDIA_CARD") == e2 ]]
  [[ $(stat -Lc '%t' "$NVIDIA_RENDER") == e2 ]]
  [[ $NVIDIA_CARD != "$DISPLAY_CARD" && $NVIDIA_RENDER != "$DISPLAY_RENDER" ]]
  drm_devices="$DISPLAY_CARD:$NVIDIA_CARD"
else
  [[ -z $NVIDIA_CARD && -z $NVIDIA_RENDER ]]
  drm_devices="$DISPLAY_CARD"
fi
for input_device in "$KEYBOARD_I8042" "$KEYBOARD_ITE" "$ELAN_MOUSE" "$ELAN_TOUCHPAD"; do
  [[ $input_device =~ ^/dev/input/event[0-9]+$ ]]
  [[ -c $input_device && $(stat -Lc '%t' "$input_device") == d ]]
done
[[ $(printf '%s\n' "$KEYBOARD_I8042" "$KEYBOARD_ITE" "$ELAN_MOUSE" "$ELAN_TOUCHPAD" | sort -u | wc -l) == 4 ]]
[[ -c /dev/tty2 && $(stat -Lc '%t:%T' /dev/tty2) == 4:2 ]]
[[ $AUDIO_CONTROL =~ ^/dev/snd/controlC[0-9]+$ && -c $AUDIO_CONTROL ]]
[[ $AUDIO_PLAYBACK =~ ^/dev/snd/pcmC[0-9]+D0p$ && -c $AUDIO_PLAYBACK ]]
[[ $AUDIO_CAPTURE =~ ^/dev/snd/pcmC[0-9]+D0c$ && -c $AUDIO_CAPTURE ]]
[[ $AUDIO_TIMER == /dev/snd/timer && -c $AUDIO_TIMER ]]
[[ $(stat -Lc '%t' "$AUDIO_CONTROL") == 74 ]]
[[ $(stat -Lc '%t' "$AUDIO_PLAYBACK") == 74 ]]
[[ $(stat -Lc '%t' "$AUDIO_CAPTURE") == 74 ]]
[[ $(stat -Lc '%t' "$AUDIO_TIMER") == 74 ]]
[[ -f $CONFIG && ! -L $CONFIG ]]
[[ -x /usr/bin/start-hyprland ]]
[[ -x /usr/bin/pipewire && -x /usr/bin/wireplumber ]]
if [[ $SESSION_MODE == desktop ]]; then
  [[ -x /usr/bin/pipewire-pulse ]]
fi

audio_card=${AUDIO_CONTROL##*C}
[[ $audio_card =~ ^[0-9]+$ ]]
install -d -m 0700 -o 1000 -g 1000 "$RUNTIME/config/pipewire/pipewire.conf.d"
audio_fragment="$RUNTIME/config/pipewire/pipewire.conf.d/99-apx-exact-analog.conf"
printf '%s\n' \
  'context.objects = [' \
  "  { factory = adapter args = { factory.name = api.alsa.pcm.sink node.name = apx_internal_output node.description = \"APX Internal Output\" media.class = \"Audio/Sink\" api.alsa.path = \"hw:${audio_card},0\" audio.channels = 2 audio.position = [ FL FR ] } }" \
  "  { factory = adapter args = { factory.name = api.alsa.pcm.source node.name = apx_internal_microphone node.description = \"APX Internal Microphone\" media.class = \"Audio/Source\" api.alsa.path = \"hw:${audio_card},0\" audio.channels = 2 audio.position = [ FL FR ] } }" \
  ']' > "$audio_fragment"
chown 1000:1000 "$audio_fragment"
chmod 0600 "$audio_fragment"

install -d -m 0700 -o 1000 -g 1000 "$RUNTIME"
rm -f -- "$RUNTIME/bus"
[[ -S $SEATD_SOCKET ]]

/usr/bin/setpriv --reuid=1000 --regid=1000 --clear-groups --no-new-privs -- \
  /usr/bin/env -i HOME=/home/apx USER=apx LOGNAME=apx SHELL=/usr/bin/bash \
  PATH=/usr/bin LANG=C.UTF-8 XDG_RUNTIME_DIR="$RUNTIME" \
  XDG_CONFIG_HOME=/home/apx/.config XDG_CACHE_HOME=/home/apx/.cache \
  XDG_DATA_HOME=/home/apx/.local/share \
  /usr/bin/dbus-daemon --session --address=unix:path="$RUNTIME/bus" \
  --nofork --nopidfile --nosyslog &
dbus_pid=$!
for _ in {1..100}; do
  [[ -S $RUNTIME/bus ]] && break
  kill -0 "$dbus_pid"
  /usr/bin/sleep 0.05
done
[[ -S $RUNTIME/bus ]]

# Give every independently created Home the familiar user folders expected on
# a normal desktop.  The command writes only this Environment's /home/apx and
# is idempotent on later launches.
if [[ $SESSION_MODE == desktop && -x /usr/bin/xdg-user-dirs-update ]]; then
  install -d -m 0700 -o 1000 -g 1000 /home/apx/.config
  /usr/bin/setpriv --reuid=1000 --regid=1000 --clear-groups --no-new-privs -- \
    /usr/bin/env -i HOME=/home/apx USER=apx LOGNAME=apx PATH=/usr/bin \
    LANG=en_US.UTF-8 XDG_CONFIG_HOME=/home/apx/.config \
    /usr/bin/xdg-user-dirs-update
fi

/usr/bin/setpriv --reuid=1000 --regid=1000 --groups=995 --no-new-privs -- \
  /usr/bin/env -i HOME=/home/apx USER=apx LOGNAME=apx SHELL=/usr/bin/bash \
  PATH=/usr/bin LANG=C.UTF-8 XDG_RUNTIME_DIR="$RUNTIME" \
  XDG_CONFIG_HOME="$RUNTIME/config" DBUS_SESSION_BUS_ADDRESS=unix:path="$RUNTIME/bus" /usr/bin/pipewire &
pipewire_pid=$!
/usr/bin/setpriv --reuid=1000 --regid=1000 --groups=995 --no-new-privs -- \
  /usr/bin/env -i HOME=/home/apx USER=apx LOGNAME=apx SHELL=/usr/bin/bash \
  PATH=/usr/bin LANG=C.UTF-8 XDG_RUNTIME_DIR="$RUNTIME" \
  XDG_CONFIG_HOME="$RUNTIME/config" DBUS_SESSION_BUS_ADDRESS=unix:path="$RUNTIME/bus" /usr/bin/wireplumber &
wireplumber_pid=$!
if [[ $SESSION_MODE == desktop ]]; then
  /usr/bin/setpriv --reuid=1000 --regid=1000 --groups=995 --no-new-privs -- \
    /usr/bin/env -i HOME=/home/apx USER=apx LOGNAME=apx SHELL=/usr/bin/bash \
    PATH=/usr/bin LANG=C.UTF-8 XDG_RUNTIME_DIR="$RUNTIME" \
    XDG_CONFIG_HOME="$RUNTIME/config" DBUS_SESSION_BUS_ADDRESS=unix:path="$RUNTIME/bus" /usr/bin/pipewire-pulse &
  pulse_pid=$!
fi
for _ in {1..200}; do
  if [[ -S $RUNTIME/pipewire-0 ]] \
      && { [[ $SESSION_MODE == virtual-machine ]] || [[ -S $RUNTIME/pulse/native ]]; }; then
    break
  fi
  kill -0 "$pipewire_pid"; kill -0 "$wireplumber_pid"
  if [[ $SESSION_MODE == desktop ]]; then
    kill -0 "$pulse_pid"
  fi
  /usr/bin/sleep 0.05
done
[[ -S $RUNTIME/pipewire-0 ]]
if [[ $SESSION_MODE == desktop ]]; then
  [[ -S $RUNTIME/pulse/native ]]
fi

if [[ $SESSION_MODE == desktop ]]; then
  /usr/bin/setpriv --reuid=1000 --regid=1000 --groups=995 --no-new-privs -- \
    /usr/bin/env -i HOME=/home/apx USER=apx LOGNAME=apx PATH=/usr/bin LANG=C.UTF-8 \
    XDG_RUNTIME_DIR="$RUNTIME" DBUS_SESSION_BUS_ADDRESS=unix:path="$RUNTIME/bus" \
    /run/apx/audio-state-client-v1.py watch &
  audio_state_pid=$!
fi

# Graphical applications inherit the compositor's working directory. Start the
# desktop from the Environment user's home so terminals and file dialogs do not
# default to the root-owned `/` directory.
cd -- /home/apx

/usr/bin/setpriv \
  --reuid=1000 --regid=1000 --groups=5,983,987,992,995,998 \
  --inh-caps=-all --ambient-caps=-all -- \
  /usr/bin/env -i HOME=/home/apx USER=apx LOGNAME=apx SHELL=/usr/bin/bash \
  PATH=/usr/bin LANG=C.UTF-8 XDG_RUNTIME_DIR="$RUNTIME" XDG_SESSION_TYPE=wayland \
  XDG_CURRENT_DESKTOP=Hyprland XDG_SESSION_DESKTOP=Hyprland \
  XDG_CONFIG_HOME=/home/apx/.config XDG_CACHE_HOME=/home/apx/.cache \
  XDG_DATA_HOME=/home/apx/.local/share LIBSEAT_BACKEND=seatd SEATD_SOCK="$SEATD_SOCKET" \
  DBUS_SESSION_BUS_ADDRESS=unix:path="$RUNTIME/bus" AQ_DRM_DEVICES="$drm_devices" \
  /usr/bin/start-hyprland -- --config "$CONFIG" &
hyprland_pid=$!

# Hyprland's Lua start event can be emitted before a late-loaded callback is
# active on a busy physical launch. Dispatch the owner shell once through the
# compositor IPC as a deterministic fallback. The shell's Quickshell command
# already refuses a duplicate instance when the Lua event won the race.
if [[ $SESSION_MODE == virtual-machine ]]; then
  workload_command=/home/apx/.local/bin/apx-system-vm
  workload_process=/home/apx/.local/bin/apx-system-vm
  [[ -x $workload_command ]]
else
  workload_command=/home/apx/.local/bin/apx-shell-v1
  workload_process=/home/apx/.local/bin/apx-shell-v1
fi
for _ in {1..400}; do
  kill -0 "$hyprland_pid"
  for socket in "$RUNTIME"/hypr/*/.socket.sock; do
    [[ -S $socket ]] || continue
    # The Lua callback is the normal path and may already have won the race.
    # Accept that live owner workload before trying the IPC fallback.  In
    # particular, do not make a healthy Hub depend on the return status of a
    # redundant `hyprctl dispatch exec` call.
    if /usr/bin/pgrep -u 1000 -f "$workload_process" >/dev/null; then
      break 2
    fi
    signature=${socket%/.socket.sock}
    signature=${signature##*/}
    if /usr/bin/setpriv \
      --reuid=1000 --regid=1000 --groups=5,983,987,992,995,998 \
      --inh-caps=-all --ambient-caps=-all -- \
      /usr/bin/env -i HOME=/home/apx USER=apx LOGNAME=apx SHELL=/usr/bin/bash \
      PATH=/usr/bin LANG=C.UTF-8 XDG_RUNTIME_DIR="$RUNTIME" \
      HYPRLAND_INSTANCE_SIGNATURE="$signature" \
      /usr/bin/hyprctl dispatch exec "$workload_command" \
      >/dev/null 2>&1; then
      /usr/bin/sleep 0.25
      if /usr/bin/pgrep -u 1000 -f "$workload_process" >/dev/null; then
        break 2
      fi
    fi
  done
  /usr/bin/sleep 0.05
done
# The outer Host launcher owns the authoritative compositor and owner-workload
# readiness proofs.  A best-effort duplicate-safe fallback must never tear down
# an otherwise healthy compositor merely because its IPC dispatch raced or
# returned an error; the outer proof will recover the session if neither path
# actually produced the required workload.
wait "$hyprland_pid"
