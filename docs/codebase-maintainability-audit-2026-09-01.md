# APX Codebase Maintainability Audit — 2026-09-01

## Scope and method

This repository-only audit covers APX source, physical and virtual-lab scripts,
the Environment shell seed, QuickShell menus, Hyprland/Mako/terminal helpers,
tests and continuity documentation. It does not authorize or perform a physical
deployment, cleanup or lifecycle operation.

The audit used tracked-file inventory, line counts, responsibility counts,
cross-reference searches, digest-manifest inspection and the existing test
contracts. “Old” does not mean “unused”: dated physical scripts and evidence
are deliberately retained when they define an admitted artifact, rollback or
failed experiment.

## Findings

### Continuity documents mixed state with chronology

`PROJECT_STATE.md` had grown beyond 5,000 lines and `CURRENT_HANDOFF.md` beyond
3,000. Both repeated dated checkpoints before and after canonical architecture
sections. That made the actual current state difficult to find and made the
supposedly concise handoff slower to validate.

Resolution: preserve both former files byte-for-byte in `docs/history`, replace
their root paths with concise current documents, and link the current statements
to dated detailed evidence. Historical documentation tests now inspect the
archive for historical claims and the root documents for current safety rules.

The same audit found `docs/architecture.md`, `docs/session-management.md` and
`AGENTS.md` still presenting the July SDDM/KDE/headless preparation state as
current. The two foundation documents are also archived unchanged and replaced
with concise maps of the implemented pilot and remaining open design. Durable
agent instructions now point to the graphical Hyprland/QuickShell pilot and the
explicit temporary root-Host development exception.

### QuickShell root accumulated unrelated responsibilities

`config/environment-shell-v1/quickshell/apx/shell.qml` exceeded 5,300 lines and
contained theme/state, Wi-Fi and Bluetooth parsing, calendar behavior,
Environment lifecycle UI, audio/display/power controls, processes, timers,
layer-shell windows and reusable visual primitives. The file is large because
QuickShell root state genuinely coordinates several coupled surfaces, but its
small visual primitives did not need that ownership.

Resolution in this pass: extract `BarButton.qml`, `BounceMouseArea.qml` and
`ControlIcon.qml`. They own no APX state or process and receive palette values
explicitly. The second-click-critical `MouseArea` remains singular and its
completed-click contract has direct tests. All new files are digest-pinned in
the Environment shell manifest.

Deferred deliberately: Wi-Fi, Bluetooth, calendar, Environment and power
controllers remain in the root. Moving them changes QML context, signal and
process ownership, and cannot be accepted safely with text-contract tests alone.
The next split should first add a runnable QuickShell component/integration
harness, then extract one domain at a time with equivalent malformed-output,
busy-state, keyboard and lifecycle tests.

### Large Python modules need seams, not mechanical splitting

The largest implementation files include the physical Hub graphical adapter,
`src/apx_isolation.py`, the virtual-lab runtime and CLI. Their size reflects
multiple policy domains, but they also contain tightly coupled validation and
effect ordering. A mechanical file split would make imports prettier without
reducing risk and could obscure the fail-closed sequence.

Recommended later boundaries are:

- separate pure parsing/validation from effect adapters;
- centralize immutable release/seed manifests without weakening digest checks;
- give lifecycle planning, generation validation and filesystem effects their
  own typed interfaces;
- keep physical identity, precondition and rollback gates adjacent to effects;
- add characterization tests before moving any destructive-path function.

No such Python split is included in this conservative pass.

### Deployment adapters are intentionally historical

Physical adapters embed identity, predecessor and source digests. Once source
changes, an old adapter should refuse rather than silently deploy new bytes.
The accepted popup adapter therefore remains as historical evidence for commit
`1dd0c59`; it is not updated to install the componentized repository candidate.
A future physical rollout needs a new adapter that backs up and atomically
installs all four QML files, validates the new process/layers, and removes or
restores partial new files on rollback.

### Ignored local artifacts are not project content

Ignored `.apx-live-*`, `.apx-restored-*` captures and Python bytecode were found
in the checkout. They are local diagnostic/cache data, are not Git-tracked, and
were not included in the publication or deleted. Cleanup of evidence outside
Git is a separate explicit decision.

## Resulting structure

```text
PROJECT_STATE.md                         current canonical state
CURRENT_HANDOFF.md                       current actionable checkpoint
docs/history/                            preserved former continuity records
docs/codebase-maintainability-audit-*    decisions and deferred work
docs/architecture.md                     current architecture map
docs/session-management.md               current session/handoff contract
config/environment-shell-v1/
  quickshell/apx/
    shell.qml                            stateful orchestration and surfaces
    BarButton.qml                        bar interaction/visual primitive
    BounceMouseArea.qml                  reusable press animation
    ControlIcon.qml                      Qt icon rendering primitive
    calendar_store.py                    bounded calendar persistence helper
```

## Acceptance boundary

This refactor is acceptable when the complete suite, Python compilation, shell
syntax, asset digests and Git diff checks pass, and the live accepted Hub source
still has its pre-refactor digest. Those checks establish repository equivalence
for covered contracts; only a separately approved physical deployment can prove
runtime QML loading and compositor behavior for the componentized seed.

Result: all 1127 tests pass with 11 expected skips. Python compilation, every
tracked shell script's syntax, asset digest contracts and Git whitespace checks
pass. The live Hub source remains unchanged at its accepted SHA-256. No QML
runtime validator is installed in the repository Host context, so loading the
new implicit local component types remains part of the separately authorized
physical acceptance rather than an inferred claim.
