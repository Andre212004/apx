# Environment handoff runtime/readiness fix — 2026-08-18

## Status

Resolved in the physical APX pilot.

A graphical Environment such as `faculdade` opened successfully but returned
to the Hub after roughly 25 seconds without an explicit owner return.

The behaviour initially resembled a timer/watchdog recovery, but that was
disproved.

## Root cause

`/usr/lib/apx/apx-graphical-environment-v1.py` preferentially loads:

`/usr/lib/apx/apx-official-hub-graphical-v1.py`

before falling back to:

`/var/lib/apx/official-hub-v1/apx-official-hub-graphical-v1.py`

The `/usr/lib/apx` copy was stale.

It still searched for Hyprland IPC below:

`/run/user/1000/hypr`

and invoked Hyprland tools with:

`XDG_RUNTIME_DIR=/run/user/1000`

The current APX graphical runtime contract is:

`SESSION_RUNTIME=/run/apx/session-1000`

with Hyprland IPC below:

`/run/apx/session-1000/hypr/<HYPRLAND_INSTANCE_SIGNATURE>/`

The stale verifier therefore found the correct Hyprland PID but searched for
its IPC socket in the wrong runtime tree. It eventually reported:

`socket=False internal_monitor=absent keyboards=0`

and normal startup recovery returned the owner to Hub.

## Evidence

Live observation of the affected `faculdade` session proved that:

- the Hyprland PID belonged to
  `apx-graphical-faculdade-98edbee0.service`;
- `.socket.sock` existed below `/run/apx/session-1000/hypr/...`;
- `hyprctl -j monitors` succeeded;
- `eDP-1` was active;
- `hyprctl -j devices` succeeded;
- two keyboards were visible.

Thus the compositor, display and input path were healthy.

## Fix

The current repository engine was installed over the stale `/usr/lib/apx`
copy.

After repair, these three files were byte-identical:

- `/usr/lib/apx/apx-official-hub-graphical-v1.py`
- `/var/lib/apx/official-hub-v1/apx-official-hub-graphical-v1.py`
- `scripts/physical-pilot/apx-official-hub-graphical-v1.py`

SHA256:

`3ea93c79492b9b3b6808f980e1c9dd11a9bef2c2b80fa917a77975b41a31f0d4`

A subsequent `faculdade` session remained active instead of automatically
returning to Hub.

## Explicitly ruled out

The following were investigated and are not the cause of this incident:

- the 120-second Environment-switch failsafe;
- Hypridle;
- explicit `return.to-hub`;
- Hub watchdog recovery;
- missing physical keyboard;
- missing internal display;
- wrong workload graphical cgroup.

The failing sessions ended around 25 seconds, well before the 120-second
failsafe could fire.

## Current graphical runtime contract

The current shared runtime is:

`/run/apx/session-1000`

Hyprland IPC consumers and producers must agree on this path.

Do not reintroduce `/run/user/1000` assumptions into the physical graphical
launcher.

## Handoff runner behaviour

A handoff runner may legitimately remain alive after a workload returns.

After workload recovery it can release the transition lock, open the Hub and
wait for that Hub graphical process to terminate before finally emitting a
stored workload failure.

This means a historical failure may appear in the journal several minutes
after the workload that originally produced it.

## Follow-up hardening

The immediate automatic-return incident is considered resolved.

Recommended later hardening:

1. prevent `/usr/lib/apx` and `/var/lib/apx` engine copies from silently
   diverging;
2. validate the digest of the engine actually selected by the workload wrapper;
3. test `SESSION_RUNTIME=/run/apx/session-1000` directly;
4. add a focused workload Hyprland readiness test;
5. improve handoff failure correlation with handoff ID, generation, unit and
   compositor PID;
6. separate registration and readiness deadlines in the handoff runner;
7. make readiness timeout failures explicit;
8. generation-bind future failsafe recovery.

These are hardening opportunities, not evidence that the timer problem
remains active.

## Operational status

Treat the automatic Environment return/timer investigation as closed unless a
new reproducible failure appears.

Current development focus returns to improving the Environments.
