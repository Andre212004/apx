# Exact Hub direct Host console v1 — 2026-08-03

The live official Hub has one `TERMINAL DO HOST` button. One click immediately
opens a Kitty window connected to the Host; there is no second phrase, token or
confirmation screen. Only one Host console may be attached at a time.

The broker exposes no command field. On the authenticated button launch it creates one fixed
PTY and executes `/usr/bin/bash --noprofile --norc -i` as Host root in `/root`.
That distinction is important: this is not Environment-local sudo. Commands in
the window can modify the complete physical Host, services, packages and every
Environment. The title and prompt identify `APX HOST ROOT` visibly.

The socket is `root:root 0600` while inactive. Only the exact official Hub
launcher mounts and leases it to the dynamically translated Hub user as 0660;
the general workload launcher explicitly disables both mount and lease. Peer
authorization additionally validates the exact Hub generation, registration,
outer unit and Hyprland process. The service admits only a client descended
from the official Quickshell. No network listener exists.

This feature intentionally weakens the former Host/Hub operational separation:
an opened console has unrestricted Host authority, and a compromised
Hub/Quickshell could attempt to abuse that route. Exact lineage, the
one-console lock and audit reduce cross-Environment access, but cannot make a root Host shell
harmless. It should be used only for deliberate administration and ended with
`exit` or Ctrl-D when no longer needed.

The initially implemented `VOLTAR AO HOST`/tty switch was removed completely at
the owner's request, including its protocol operation; only the confirmed Host
terminal remains. The first real use exposed a PTY sizing defect: full-screen
applications such as Codex received an invalid terminal size and rendered a
black window. The client now passes Kitty's rows/columns before Bash starts;
the broker applies `TIOCSWINSZ` and `SIGWINCH`. A local `stty size` proof
observed the requested `31 100`, the bridge closed cleanly, and process/audit
inspection found no orphaned Host Bash, Kitty, console client or Codex.

A subsequent live owner session confirmed the complete path with Codex itself:
the active PTY reported `33 × 70`, Bash and Codex were Host UID/GID 0 with the
physical root, Codex owned the PTY foreground process group, all APX services
and the Hub Hyprland unit were active, and systemd reported `running`. Audit
accounting showed exactly one more open than close while that console was in
use, matching the single live Bash/Codex pair. `hostname` and the Host `kitty`
package are absent from the deliberately minimal Host package set; Kitty
correctly remains inside Hub and neither absence affects the bridge.

## Persistent attachment correction — 2026-08-12

Physical use exposed a lifecycle defect that the original close-on-disconnect
design could not solve. A Hub failure or an intentional Hub-to-Environment
handoff destroys the graphical client while a long-running Host-root Codex may
still own its conversation writer. A new `codex resume` then correctly refuses
the same conversation, but the owner has no graphical route back to its PTY.

The broker now owns one persistent in-memory PTY independently of the Kitty
connection. Losing or closing the window detaches the client and keeps the
same Bash, foreground process group and Codex alive. The broker continuously
drains output into a bounded 1 MiB memory buffer so a detached producer cannot
block on a full PTY. Reopening `TERMINAL DO HOST` from a newly authenticated
official Hub rechecks the normal peer, cgroup and Quickshell ancestry, applies
the new window size, signals the foreground process group and reattaches to the
same PTY. It never makes the console available to a workload Environment.

`exit` or Ctrl-D inside the shell remains the normal terminal operation and
ends the persistent PTY. A restart or stop of `apx-host-console-v1.service`
is the administrative recovery path and systemd's service cgroup terminates
the PTY descendants. No transcript, command, terminal output, token or secret
is written to disk; only the existing event audit is persistent. If detached
output exceeds 1 MiB, the oldest display bytes are discarded, while process
and conversation state remain live.

This deliberately changes the risk profile: after an explicit owner opening,
an unrestricted Host-root shell may remain alive without a visible window
until the owner exits it or the broker is restarted. The socket remains local,
single-attachment admission remains enforced, and every later attachment must
again prove the exact active official Hub lineage. The gain is continuity
across graphical failure and Environment handoff; it is not generic process
checkpointing and does not make Codex part of APX.
