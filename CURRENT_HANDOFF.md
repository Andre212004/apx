# APX Current Handoff

This file is intentionally short. It describes the latest actionable checkpoint,
not the complete history. The prior 3,000-line handoff is preserved unchanged at
`docs/history/CURRENT_HANDOFF-through-2026-09-01.md`; canonical product and
safety decisions are in `PROJECT_STATE.md`.

## Owner-reported physical state

The owner physically accepted the QuickShell stationary-pointer correction on
2026-09-01: after opening a menu, a second click on the same bar button closes
it without moving the mouse, and the hand cursor remains usable.

At the accepted checkpoint:

- the Lenovo physical pilot identity and APX marker matched;
- Hub was the only running Environment; other registered Environments were
  stopped;
- APX reported healthy and the Host had zero failed units;
- one supervised QuickShell process exposed four stable layer-shell surfaces;
- the menu was left closed;
- repository and live Hub `shell.qml` both matched SHA-256
  `2c6b39f50f2228d88320759ee770203c7913549fe32ec35f65616767b79b7f20`;
- rollback is available at
  `/var/lib/apx/backups/20260901T012510Z-quickshell-popup-interaction-v1/`.

This evidence covers the physically installed monolithic shell only. The later
repository maintainability refactor is not deployed and has no physical
acceptance claim.

## Repository checkpoint

The complete accepted state was committed and pushed as `1dd0c59` on branch
`agent/defer-local-model-phase10`. It includes APX runtime/configuration,
QuickShell menus, Wi-Fi/Bluetooth handling, terminal and notification policy,
Hyprland fallback, recovery helpers, tests and continuity updates.

The post-checkpoint maintainability pass:

- archives the oversized continuity history without deleting it;
- replaces the root continuity files with current operational summaries;
- extracts only stateless visual QuickShell primitives from `shell.qml`;
- keeps stateful Wi-Fi, Bluetooth, calendar, Environment and power logic in the
  existing root component until stronger QML integration coverage exists;
- records larger Python/QML candidates for later bounded refactors.

## Next owner action

No physical action is required for the accepted mouse fix. Review the repository
maintainability commit after its full test run. Installing the componentized
QuickShell seed on Hub or any stopped Environment is a separate physical change
and needs an exact adapter, backup and fresh approval.

System VM v2 remains an independent experimental track. Follow its dated
architecture/acceptance document before any owner-driven VM entry; do not infer
VM authorization from the shell work.

## Active safety blocks

- The physical pilot is experimental, not production.
- Repository tests do not replace physical pointer, compositor, GPU, VM or
  recovery evidence.
- Do not reuse the dated popup deployment adapter for the componentized seed;
  it is digest-pinned evidence for the accepted monolithic installation and
  must refuse later source bytes.
- Do not alter Hub, Development, System Environments, packages, mounts, devices,
  services or backups without fresh explicit owner authority.
- Do not clean historical deployment scripts or rollback records merely because
  they are dated.
- Do not begin local-model/external-SSD work as part of this refactor.
- Do not commit or push future changes unless the owner explicitly requests it.

## Refactor validation result

The repository candidate passes all 1127 tests with 11 expected skips, Python
compilation, `bash -n` for every tracked shell script, digest-manifest tests and
Git whitespace review. The accepted live Hub file still has its exact
pre-refactor SHA-256, confirming that this repository cleanup did not modify the
running interface.
