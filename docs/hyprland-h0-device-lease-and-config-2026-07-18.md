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

The first pure two-unit Host launch plan was closed with digest
`b5836e03a8c59f62018b58a4b9410a1dab1a7ee11c24fd03e64f1dab2b37d6ea`.
It binds three fixed assets by SHA-256 and mode, creates an independent
120-second expiry timer, requires that timer to be observed active, and only
then permits creation of the generation-bound graphical transient unit. The
graphical command has closed device policy, fixed CPU/memory/task limits,
private networking, no new privileges, no caller path or command, fixed home,
config, runner, and five device binds. Its final ordered gate always invokes
the expiry/recovery path after normal exit too, proves tty1/zero residue, and
only then permits timer cancellation. This remains a pure plan, not execution.

## Physical asset staging result

The exact staging adapter was published, tested, and then executed. It created
only `/var/lib/apx/h0/h0-3ef21d19a2518d4fcea9d51513cc1eee` and copied the
three reviewed assets as root-owned regular files:

- `hyprland.conf`: mode 0400, SHA-256
  `cf7aae5f7ebbee9d9128d0bd1dc8b762a77cf44202498e940e6cc9a42fccc54c`;
- `session`: mode 0500, SHA-256
  `8612d2b6370371679a595421186114e19591b9accdefae0ef03054ffc8137235`;
- `watchdog`: mode 0500, SHA-256
  `5c7d63bb2dd505f7f1c916fa1d3dd3083c4f8e591e11d2514424e2e2af7402e9`.

The mode-0400 staging result binds the experiment and Environment generation
and explicitly records `graphical_activation=false`. Final rehash passed. APX
remained healthy and stopped, systemd had zero failed units, and tty1 remained
active. No timer, unit, device, session, or compositor was started.

Final launch review found that the Host, not internal seatd, must own the
tty1/tty2 transition. The reviewed runner v2 therefore fixes
`SEATD_VTBOUND=0`; it does not broaden any device or privilege. Its SHA-256 is
`db099965ab22ba322f2d113365af6e561c612c92bd660a3205d6023072ed743c`.
The v1 staging directory remains immutable historical evidence. The new v2
experiment directory is distinct, and the current launch-plan digest is
`9c5342a5859a93a09dcafefe8b6d53d370a2028e712d3321ee61d15d93cf9305`.
The exact final executor is implemented with a 45-second bounded observation
inside the independent 120-second watchdog window; it has not yet run.

Physical v2 then armed the timer and returned safely to tty1, but nspawn refused
before registering a machine because the stable touchpad by-path contains a
colon that conflicts with bind-option syntax. No container, Hyprland process,
or device consumer started. V3 preserves that result and keeps stable paths as
the authority while binding only their revalidated current targets, keyboard
`event3` and touchpad `event11`, to fixed internal `event0`/`event1`. Its plan
digest is `83750219fbf0f0ac0569ba8965849c3f42b98235fa81ca6149f730b912f05eed`.

Physical v3 passed the bounded technical H0 gate. The independent timer was
active before the graphical unit, the nspawn machine and unprivileged Hyprland
process were both observed, and the process remained active for the complete
45-second observation window. Transient seatd accepted the UID 1000 client.
The final watchdog returned tty1, removed the machine and mounts, and left the
graphical/timer units inactive with APX healthy and zero failed units. The
sanitized result is `docs/hyprland-h0-physical-result-2026-07-18.json`.

Two non-fatal gaps remain. Aquamarine attempted to enumerate absent card1 but
could not open it; only the admitted AMD nodes existed inside the container.
The separate home subvolume lacks `/home/apx`, so shader-cache creation was
disabled. Neither prevented the 45-second Hyprland process pass, but both must
be resolved before calling the Environment daily-usable. Visual output and
input behavior still require the physically present owner's report.

The current Environment-local home gap is now resolved: `/home/apx` and its
cache directory exist inside only the separate home subvolume as mode 0700,
UID/GID 1000, under the retained 8 GiB quota. The repository runtime now creates
that fixed internal home automatically for every future `graphical-h0`
Environment. This source correction is not yet installed into the Host runtime;
the current Environment was corrected directly and reverified stopped/healthy.
