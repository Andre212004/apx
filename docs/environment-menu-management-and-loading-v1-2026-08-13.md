# Environment menu, lifecycle buttons and transition loading v1 — 2026-08-13

## Result

The physical Hub now uses one native QuickShell Environment panel. The old
explanation paragraph, `ESC FECHAR`, `TRANSIÇÃO GERIDA PELO HOST`, and the
second Rofi chooser are absent. The panel shows the current Hub, a directly
selectable Environment list, and three aligned actions: **Criar**,
**Selecionar**, and **Apagar**.

The previous menu was captured before implementation and the installed panel
was captured afterwards. The latter loaded successfully in the real Hub and
showed Work selected without an intermediate menu or clipped status text.

## Selection and opening

`catalog.get` still comes from the root-owned switch service and accepts only
trusted `graphical-base` registrations from `hyprland-base-v2`. Selecting a row
changes only local UI state. **Selecionar** sends the exact logical name through
`switch.to-workload`; the Host revalidates stopped state, identity, generation,
the active official Hub, QuickShell parentage, and the handoff lock.

Workloads retain one compact **Voltar ao Hub** action. They receive no create or
destroy capability.

## Creation

The creation form accepts one bounded logical name. It does not accept paths,
packages, commands, accounts, devices, or arbitrary template identifiers.
`environment.create` always means the fixed reviewed role
`graphical-base` from `hyprland-base-v2`, with coordinated Host updates.

The root management runner creates the ordinary APX `create-plan`, verifies its
digest, and applies it with the exact approval string. The existing runtime
then snapshots the immutable release and creates an independent home. It copies
the reviewed Hyprland/Rofi base plus the desktop-essential and Environment-shell
seeds, so a new Environment has the same minimal desktop facilities as Work
without cloning the live Hub or inheriting Hub-only authority.

## Deletion

The delete button is disabled until a stopped Environment is selected. Its
first activation opens a plain data-loss question; only **Confirmar** sends the
request. The request carries both logical name and the selected registration
generation. The Host rejects Hub, an active Environment, a changed generation,
an untrusted registration, or any concurrent lifecycle/handoff operation.

The management runner independently creates a fresh `destroy-plan`, compares
its generation with the UI-bound generation, and only then applies the exact
`DESTROY <name>` approval. This removes only that Environment's APX-owned root,
home, and registration through the existing journalled runtime.

## Progress and concurrency

Create/destroy is asynchronous. A root-only state record in `/run/apx` exposes
only action, target, phase, percentage, message, and update time through
`management.status`. A root-owned reservation file is created before the
transient runner starts, closing the start-up race between two button presses.
The runner removes only the same inode it opened. The panel polls while busy,
shows a progress bar, refreshes the catalogue on completion, and surfaces a
bounded refusal message on failure.

## Environment transition surface

Opening or returning first raises a full-screen dark APX overlay in the active
QuickShell with a smoothly advancing cyan bar. Before the current graphical
Environment is stopped, the Host supervisor pre-renders a second branded APX
progress surface on tty1. That tty surface remains behind the graphical VT and
covers the exclusive teardown/start interval, so tty1 never needs to reveal a
Host login or shell prompt during the normal handoff. The workload return
endpoint primes the same surface before requesting the workload stop.

The Host progress stages are tied to real boundaries: outgoing close,
zero-residue recovery, destination preparation, machine registration, and Hub
restoration. The bar is intentionally stage progress, not a fabricated time
estimate.

## Latency changes

The already removed four-second QuickShell sleep remains replaced by two
enabled-monitor observations at 50 ms. This change also replaces the launcher's
fixed two-second Hyprland stability window with two successful 50 ms
observations; all required PID, socket, internal-monitor, and keyboard evidence
is still mandatory. Handoff recovery and destination-registration polling now
use 50 ms instead of 200/100 ms intervals. Deadlines and fail-closed recovery
remain unchanged.

The installed QuickShell parsed and loaded the new configuration in about
0.53 seconds. A complete physical Hub/Work round trip was not forced during
this change because the current Host-console PTY owns the active Codex session;
the prior repeated round-trip proof remains the handoff safety baseline.

## Live-Hub compatibility

The running Hub had the old read-only client inode bind-mounted. Restarting the
Hub merely to replace that inode would have closed the visible Host-console
window. A root-owned compatibility client and matching contract were therefore
placed in the existing Hub-only `.apx-host-bridge`; the new Hub panel uses that
path while the current Hub remains alive. Newly launched Hub sessions use the
normal updated `/run/apx` bind. Workloads continue to use only `/run/apx`.

This compatibility bridge does not broaden service authority: every mutation
must still be a direct child of the admitted QuickShell in the exact official
Hub cgroup.

## Validation and recovery

- New QML loaded in the physical Hub without parse/runtime startup failure.
- Physical `catalog.get` and `management.status` requests from QuickShell were
  accepted by the Host; the panel displayed Work directly.
- Python compilation and shell syntax checks passed.
- The complete repository suite passed **1020 tests with 11 expected skips**.
- No Environment was created or destroyed merely for testing.

Exact pre-change physical files are retained under
`/var/lib/apx/backups/20260813-environment-menu-management-v1/`. Recovery is to
stop only `apx-environment-switch-v1.service`, restore the backed-up service,
client, contract, runner, runtime, launcher and shell copies, restart that
switch service, remove the new management runner and the two compatibility
files from the Hub `.apx-host-bridge`, then reload QuickShell. Do not restart
`apx-host-console-v1.service` while its persistent PTY is needed.

## Fresh-Home startup correction

The first real menu-created Homes (`jogos` and `andre`) revealed that the seed
copier validated and owned final directories such as `~/.local/bin` but did
not include an implicit ancestor created by `mkdir(parents=True)`. That left
`~/.local` as `root:root 0755`. The unprivileged `apx-shell-v1` failed at its
first `install -d ~/.local/state`, before a QuickShell process or log existed.
The generic launcher consequently returned `the selected workload shell did
not remain active` after its ten-second bounded check.

The copier now includes every directory below the Environment Home in its
regular-file/symlink checks and applies user ownership plus mode 0700. The two
existing stopped Homes were repaired without replacing any content. A focused
test now checks intermediate directory ownership and mode.

The incident also exposed a recovery sequencing gap: a failed destination was
cleaned, but the exception bypassed the later Hub launch. The runner now holds
that exception, completes workload cleanup, launches the authenticated Hub,
and reports the original failure only after the Hub session ends. An injected
failure test proves the destination and Hub launch calls occur in that order.

The corrected installed runtime and runner match repository source. The full
suite passed 1021 tests with 11 expected skips at that checkpoint. Backups are in
`/var/lib/apx/backups/20260813-environment-shell-parent-ownership-v1/`. The
active Hub was preserved, so entry into `andre` or `jogos` during normal owner
use remains the final visual confirmation rather than a claimed forced proof.

## Two-minute lifetime and local password follow-up

The first repaired `andre` session proved QuickShell startup, then ended at
exactly two minutes. Journal evidence identifies the
`apx-environment-switch-failsafe-v1` timer firing; there was no QuickShell or
Hyprland crash. The 120-second recovery had been designed for incomplete
handoffs but was never disarmed after a successful interactive startup.

The runner now waits for the root-owned active workload descriptor and checks
it against the root-owned registration: exact name, graphical-base role,
`hyprland-base-v2`, running state, generation, generation-derived outer unit
and positive PID. Only that complete state cancels the startup failsafe. A
partial or stuck launch remains recoverable after 120 seconds. The installed
runner matches source and the complete suite passes 1022 tests with 11 skips.

The owner's sudo attempt was not a typing error. `andre`, `jogos` and the
original `work` still had locked `apx:!` shadow entries. Wheel membership and
the password-required sudoers policy were present, but no password can
authenticate a locked account. Credentials remain Environment-local and the
Hub hash is not copied. Until a native enrollment UI exists, the secure owner
procedure while the target is active is: change visually to tty1, authenticate
as Host root, run `apx environment enroll-local-admin <name>`, enter the new
local password twice, and return to tty2. Passwords must never be supplied in
chat, command arguments or logs.
