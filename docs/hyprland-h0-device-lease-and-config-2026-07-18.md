# APX Hyprland H0 Device Lease and Configuration — 2026-07-18

Status: exact pure lease plan and compositor configuration verified; no device
was granted and no graphical process was started.

## Practical result

The first physical H0 run is now bound to the existing stopped Environment
generation `c4fc5c49-4106-4a56-b1f0-13bffa41a0c1`. The plan permits only:

- AMD KMS `/dev/dri/card2`, character identity 226:2;
- AMD render `/dev/dri/renderD129`, character identity 226:129;
- built-in i8042 keyboard through its stable by-path identity;
- built-in ELAN touchpad through its stable by-path identity;
- experiment console `/dev/tty2`, character identity 4:2.

Keyboard and touchpad are resolved from stable Host identities immediately
before a run and appear under fixed internal names `/dev/input/event0` and
`/dev/input/event1`. Current Host numbers `event3` and `event11` are observations,
not persistent policy.

The plan explicitly excludes NVIDIA card1/renderD128, tty1, every other observed
input event, audio, camera, broad Host filesystem access, network, executor
access, and automatic graphical restart.

## Recovery and timeout

The Host must arm a 120-second deadline before the first device grant. Deadline
recovery is generation-bound and must:

1. terminate only the H0 unit;
2. revoke all five grants;
3. return the active console to tty1;
4. prove no machine, process, Wayland socket, or lease remains;
5. never restart Hyprland automatically.

The independent recovery console remains tty1 and is never present inside the
Environment. A 15-second stop ceiling bounds graceful teardown before the Host
watchdog continues recovery.

## Current exact preview

Read-only observation confirmed the AMD PCI/driver and connected internal
`card2-eDP-2`, active tty1, inactive tty2, absent display manager and graphical
owner, stopped Hub and Development, the exact Environment generation, and zero
APX uncertainty.

- observation digest:
  `a4f7fe2af15c74e0b878f01816a55a337f149b4ccb0449ab7e088af07df35162`;
- device-lease plan digest:
  `3ef21d19a2518d4fcea9d51513cc1eee63f6ff593d4470bcc10955b06e3059cb`.

`src/apx_hyprland_h0_device_lease.py` is pure: it accepts supplied evidence and
cannot open a device, start a process, change a VT, write a file, or control a
service.

## Hyprland configuration

`config/hyprland-h0.conf` selects only eDP-2, Portuguese keyboard layout,
built-in touchpad defaults, minimal decoration, no animation, no launched
program, no portal, no audio, and no Host integration. `SUPER+SHIFT+E` is a
manual compositor exit; the Host watchdog remains authoritative.

The installed Hyprland 0.55.4 parsed this exact file inside the stopped
Environment as the ordinary `apx` user and returned `config ok`. That validation
used no network, GPU, input, tty, graphical session, or persistent runtime
directory.

## Remaining effect boundary

The next code may translate only this plan into a fixed transient nspawn unit,
an independently armed Host watchdog, a bounded readiness observer, and an
unconditional teardown observer. Physical execution remains blocked until the
adapter proves that every failure path returns to tty1 without owner input.

The pure non-extendable watchdog state machine and internal session runner are
now implemented. The watchdog refuses stale generation/plan identities,
out-of-order or late grants, deadline extension, and completion with any
process, mount, socket, lease, or tty1 residue. On expiry it always selects
generation-bound termination, five-device revocation, tty1 activation,
zero-residue observation, and no restart.

The fixed runner revalidates all five internal character identities, starts
only transient `seatd`, then runs Hyprland as UID/GID 1000 with only tty, video,
render, and input supplementary groups and an empty controlled environment.
All inherited/ambient/bounding capabilities are removed from Hyprland. A shell
trap terminates and waits for seatd after normal exit, failure, or signal. The
runner contains no NVIDIA, other input, audio, camera, package, network, or tty1
path. It has not been physically executed.

The Host expiry adapter is now implemented and rehearsed without a graphical
unit or device grant. It accepts only `--expire`, revalidates the exact
Environment generation/role/release, stops only the fixed H0 unit, activates
tty1, and observes the exact nspawn machine argument, Environment mounts, and
unit state. It contains no start, restart, broad kill, deletion, Hub, or
Development action.

The first zero-effect rehearsal correctly refused a false success because the
outer test command itself contained the machine name. Review narrowed process
observation to an exact nspawn `--machine=...` argument rather than weakening
the residue gate. The repeated rehearsal then returned
`h0-watchdog: tty1-restored zero-residue`; APX remained healthy and stopped.
