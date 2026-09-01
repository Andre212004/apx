# APX Project State

This is the canonical description of APX's current objective, architecture and
safety boundaries. Read it together with `CURRENT_HANDOFF.md` before changing
the repository or the physical pilot. Detailed chronological evidence through
2026-09-01 is preserved, unchanged, in
`docs/history/PROJECT_STATE-through-2026-09-01.md`.

## Product objective

APX makes one physical Arch Linux computer behave like a set of independent,
disposable computers without exposing ordinary Linux account management to the
owner. The intended flow is:

```text
Boot -> Hub -> selected Environment -> Hub
```

An Environment owns its applications, dependencies, documents, configuration,
processes and mutable state. Deleting it must remove that local state without
altering the Host, Hub or another Environment. APX is an orchestration platform,
not a separate kernel or operating system for every Environment.

The Hub is the minimal management Environment. It is not an unrestricted
administrator, a template for workloads or a place for general-purpose work.
Privileged lifecycle effects belong to typed, independently validating Host
executors. The CLI and graphical menus are clients of the same bounded
protocols.

## Confirmed architecture

- One Arch Linux Host and one Host kernel.
- Btrfs-backed, generation-bound Environment state and lifecycle plans.
- Separate internal identities and filesystems are the current ownership base.
- Only one normal graphical Environment is active at a time.
- The Host owns hardware integration and recovery; Environments receive only
  explicitly admitted devices and services.
- Environment package operations must never mutate the Host package database or
  another Environment.
- Shared defaults come from digest-pinned, versioned seeds, never from a live
  mutable Hub.
- Management requests are typed, authority-bound and fail closed on stale or
  uncertain state. There is no arbitrary privileged command channel.
- The current physical machine is an experimental pilot, not production.

The repository contains the lifecycle/runtime implementation, isolation and
threat-model documents, physical adapters, recovery contracts, graphical Hub
and Environment configuration, and the System VM v2 experiment. Dated physical
adapters are retained as exact deployment and rollback evidence; a dated script
must not be assumed reusable against a later source tree.

## Current graphical shell

The shared Environment shell uses Hyprland, QuickShell, Mako and local helper
scripts from `config/environment-shell-v1`. Its important current behavior is:

- the bar and menus use the same dark 85%-alpha surface (`#d90a1014`);
- the Calendar grid uses a more opaque card for legibility;
- every menu opening requests keyboard focus and supports keyboard navigation;
- an application-area dismissal layer closes a menu on the first outside click;
- popup and dismissal layer-shell surfaces remain mapped for the QuickShell
  lifetime, with zero-sized input regions while closed;
- bar actions activate on completed clicks, preserving a stationary pointer
  across open/close transitions;
- Wi-Fi, Bluetooth, audio, display, battery, power and Environment actions use
  bounded Host-service or APX intents rather than shell text supplied by UI;
- Hyprland supplies a plain black fallback behind QuickShell;
- terminal notifications are dismissed on terminal focus and have an 8-second
  fallback timeout.

The owner physically accepted the stationary same-button second-click fix on
2026-09-01. The accepted live Hub monolith has SHA-256
`2c6b39f50f2228d88320759ee770203c7913549fe32ec35f65616767b79b7f20`
and rollback directory
`/var/lib/apx/backups/20260901T012510Z-quickshell-popup-interaction-v1/`.
The repository subsequently extracted only three stateless visual primitives
from `shell.qml`; that maintenance-only seed candidate has not been installed
on the physical Hub.

## Current repository baseline

Commit `1dd0c59` on `agent/defer-local-model-phase10` is the published,
physically accepted pre-refactor baseline. At that checkpoint:

- source and live Hub `shell.qml` hashes matched;
- the same four QuickShell compositor surfaces survived popup open/close;
- the Hub was the sole running Environment;
- APX was healthy and the Host had zero failed units;
- all 1126 tests passed with 11 expected skips;
- shell syntax, Python compilation and diff whitespace checks passed.

The maintainability pass after that commit is repository-only. Its componentized
`shell.qml` is SHA-256
`77bab37b1dd1c853f1fa26998c50fa81f6883150178b9a7be76e10ad119e4bbc`.
All 1127 tests pass with 11 expected skips, along with tracked shell syntax,
Python compilation, seed digest and diff whitespace checks. The accepted live
Hub remains unchanged at the pre-refactor hash. This candidate must not be
described as physically accepted until separately installed and observed.

## System VM v2

System VM v2 remains experimental. One Environment runtime owns QEMU, swtpm and
optional Looking Glass under the supervised session cgroup. Direct QEMU VGA is
the deterministic recovery/default mode; a future native RTX/KVMFR mode is an
explicit next-entry choice, never an automatic transition. Guest storage is
generation-bound, destructive operations require exact approved plans, and
physical acceptance remains distinct from repository tests. The full design
and current acceptance ladder are in
`docs/system-vm-v2-architecture-2026-08-24.md` and the historical state record.

## Development method

1. Separate observations, accepted decisions, experiments and open questions.
2. Prefer small reversible changes with explicit preconditions, rollback and
   acceptance criteria.
3. Test deterministic contracts and failure behavior before Host experiments.
4. Treat sandbox-visible evidence as non-authoritative when Host confirmation
   is required.
5. Never change the physical Host from ordinary repository work. Physical work
   requires the identity-bound temporary Host guide and fresh owner authority
   for the exact effects.
6. Preserve failed and successful physical evidence. Never rewrite history to
   make a candidate appear accepted.
7. Update this document when the objective, architecture, current baseline or
   safety boundary changes; put detailed event chronology in `docs/history` or
   a dated evidence document.

## Hard stops

- Do not install, start, stop, mount, unmount, delete or clean physical state
  without current, explicit authorization for those effects.
- Do not change or destroy Hub, Development or a System Environment by inference.
- Do not weaken generation binding, digest admission, trusted authority checks,
  Host reserve protection, recovery gates or rollback evidence for convenience.
- Do not present user-account separation as VM-equivalent security.
- Local-model installation and external-model storage remain separately gated;
  neither is a prerequisite for repository maintenance.
- Do not commit or push unless the owner explicitly asks. That authority applies
  to the requested publication, not automatically to future work.

## Documentation map

- `CURRENT_HANDOFF.md`: current machine/repository checkpoint and next actions.
- `docs/codebase-maintainability-audit-2026-09-01.md`: current structure audit
  and conservative refactor boundary.
- `docs/history/PROJECT_STATE-through-2026-09-01.md`: complete former canonical
  state and technical chronology.
- `docs/history/CURRENT_HANDOFF-through-2026-09-01.md`: complete former handoff
  chronology.
- `docs/temporary-root-host-development-mode-v1.md`: identity-bound physical
  Host procedure; reading it is not authorization to execute it.
- `docs/physical-pilot-update-contract-v1.md`: update/rollback contract.
- `docs/isolation-architecture.md` and `docs/threat-model.md`: isolation limits
  and security model.
