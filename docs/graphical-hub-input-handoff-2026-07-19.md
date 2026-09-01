# Graphical Hub input handoff — 2026-07-19

## Purpose

This is the exact continuation record for the next development chat. The first
persistent graphical Hub reaches Hyprland and displays the UI, but the owner
cannot interact with it using the built-in keyboard or trackpad. Do not call
the round trip successful and do not ask for another manual attempt until an
automated input proof passes.

## Safe physical state at handoff

- tty1 is active.
- Hub registration is `stopped`.
- `test` registration is `stopped`.
- The exact Hub recovery adapter was run after the final owner report.
- No owner-facing graphical session is intentionally active.
- The retained headless Hub rollback remains at
  `/var/lib/apx/quarantine/retained-hub-headless-v3-d68ee7a2`.

## What works

- `entrar_no_HUB` performs exact recovery, starts the local executor, issues a
  fresh descriptor and approval, arms an independent watchdog, and starts the
  graphical Hub.
- Hyprland, Waybar, the Wayland socket, AMD `eDP-2`, and tty2 have repeatedly
  appeared.
- The watchdog has repeatedly restored tty1 without requiring an automatic
  reboot.
- The Host executor is a local Unix service; there is no network server.
- The switcher is configured with `exec-once = /usr/bin/apx-hub --switcher` so
  the owner should not need a keyboard shortcut merely to display it.
- An automated `hyprctl -j devices` observation after the latest device-name
  and cgroup changes listed:
  - main keyboard `at-translated-set-2-keyboard`, Portuguese layout;
  - ELAN pointer `elan06fa:00-04f3:31dd-mouse`.

That last observation proves enumeration only. It does not prove delivery of
real key, button, or motion events.

## Owner-visible failure

The owner reports the same result after the latest automated enumeration:

- graphical Hub opens;
- pointer does not move;
- Super shortcuts do nothing;
- no control inside the Environment is usable.

## Root cause found after handoff

A fresh Host observation proved that kernel-assigned `eventN` numbers changed
across boots. The broker still admitted `/dev/input/event10`, but it is now the
PC speaker (13:74), not ELAN input. The ELAN mouse is currently event8 (13:72)
and its touchpad node is event9 (13:73); the keyboard remains event3. Historical
`seatd` logs also contain two `Operation not permitted` device opens. Fixed
event numbers are therefore not physical identities and must not be restored.

Repository launch adapters now resolve three closed identities from udev at
each launch: the i8042 keyboard and both the mouse and touchpad capabilities on
the exact internal AMDI0010 ELAN path. Absence, overlap, or ambiguity fails
before effects. Only the resolved nodes receive cgroup and bind admission, and
their actual names are passed into the session runner. The repository suite
passes 834 tests with 11 skips. Installed Host assets have not yet been updated,
so another graphical launch remains blocked pending reviewed publication and
an automated event-delivery proof.

The owner previously rebooted to escape. The current watchdog is 180 seconds;
future instructions must explicitly say to wait for recovery instead of
rebooting, but the manual test must remain paused until automated proof exists.

## Bugs already found and fixed

1. The session readiness loop used `read -t ... </dev/null`, which did not wait.
   It now uses a real 50 ms sleep.
2. Old D-Bus and seatd sockets could survive in the Environment root. They are
   removed before startup and during cleanup.
3. D-Bus inherited `HOME=/root`. It now starts with the Environment user's
   HOME/XDG paths.
4. The watchdog initially could not update registrations under
   `ProtectSystem=strict`. Exact Hub, test, and `/run/apx` write paths are now
   admitted.
5. `/dev/input/event11` was incorrectly treated as the touchpad. It is the
   IdeaPad extra-buttons device. The real ELAN touchpad is Host `event10`.
6. Binding individual udev records containing `:` was invalid nspawn syntax.
   `/run/udev/data` is now exposed read-only; device-node access remains closed.
7. Renaming Host event3/event10 to container event0/event1 disagreed with udev
   DEVNAME metadata. They now retain names event3 and event10 inside.
8. seatd opens input nodes read/write. Exact `DeviceAllow` entries for event3
   and event10 changed from `r` to `rw`; every other input remains denied.
9. Treating event numbers as durable identities was invalid. The touchpad moved
   from event10 to event9 and event10 became the PC speaker. Repository adapters
   now resolve exact udev path/capability identities at launch and admit both
   ELAN mouse and touchpad nodes.

## Exact physical identities

- built-in keyboard: `/dev/input/event3`, character 13:67, group `input` 992,
  udev `ID_INPUT_KEYBOARD=1`;
- ELAN mouse and touchpad: dynamically resolved from exact udev path
  `platform-AMDI0010:01` with `ID_INPUT_MOUSE=1` and
  `ID_INPUT_TOUCHPAD=1`; current observations are event8 (13:72) and event9
  (13:73), but these numbers are not identities;
- AMD KMS: `/dev/dri/card2`;
- AMD render: `/dev/dri/renderD129`;
- experiment console: `/dev/tty2`;
- recovery console: tty1.

The Environment graphical user is UID/GID 1000 and its fixed supplementary
groups include input GID 992.

## Current code and installed assets

Repository sources:

- `scripts/physical-pilot/entrar_no_HUB`
- `scripts/physical-pilot/apx-graphical-broker-v1.py`
- `scripts/physical-pilot/apx-graphical-session-v1.sh`
- `scripts/physical-pilot/apx-graphical-recovery-v1.py`
- `scripts/physical-pilot/apx-graphical-test-launch-v1.py`
- `src/apx_graphical_effect_adapter.py`
- `src/apx_executor_daemon.py`
- `config/systemd/apx-executor-v1.service`
- `config/hyprland-base/hyprland.conf`

Installed counterparts include:

- `/usr/local/bin/entrar_no_HUB`
- `/var/lib/apx/graphical-v1/apx-graphical-broker-v1.py`
- `/var/lib/apx/graphical-v1/apx-graphical-session-v1.sh`
- `/var/lib/apx/graphical-v1/apx-graphical-recovery-v1.py`
- `/usr/lib/apx/apx_executor_daemon.py`
- `/etc/systemd/system/apx-executor-v1.service`

The latest targeted suite passed 10 tests after the input path/name changes and
9 tests after changing exact input access to `rw`. The earlier whole suite
passed 831 tests with 11 skips. These tests do not simulate real evdev event
delivery.

## Required next investigation

Build a bounded, automated proof before another owner attempt:

1. Start Hub with the independent watchdog already active.
2. Observe exact unit/cgroup device policy and exact container device nodes.
3. Capture events from event3 and event10 inside the running mount/PID context,
   without exposing arbitrary input or logging owner secrets.
4. Prefer a harmless synthetic test device or a narrowly timed owner-generated
   test event; do not record normal typing.
5. Correlate an evdev event with Hyprland/libinput debug evidence or compositor
   state change.
6. Verify the automatically opened GTK process/window separately. Enumeration
   of the keyboard and ELAN pointer is insufficient.
7. Recover immediately, then prove tty1, stopped registrations, no machine,
   no graphical unit, and no failed watchdog unit.

Likely remaining areas include seat/session ownership, libinput event delivery,
VT focus, and whether the Host console still exclusively owns input despite
seatd enumeration. Do not broaden to all `/dev/input`, disable the closed
device policy, start a display manager, or remove the watchdog as a shortcut.

## Product direction confirmed by owner

This graphical Hub is disposable test infrastructure. After the switching
logic works, the owner intends to recreate the Hub from a clean Arch-like base
and personally build its Hyprland/Waybar/Eww/Rofi/Alacritty appearance. APX
logic will then be integrated into that finished design. New Environments may
receive an independently copied, reviewed visual base derived from the design;
they must never clone the mutable live Hub or its credentials/Hub-only state.
