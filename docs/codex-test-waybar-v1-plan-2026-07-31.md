# codex-test-waybar-v1 physical fixture plan — 2026-07-31

## Purpose

Create one disposable normal graphical Environment named
`codex-test-waybar-v1` from immutable release `hyprland-base-v1`, then replace
only its independent copied Waybar configuration with the reviewed
`config/waybar-ascii-v1/environment-config.json` and shared `style.css`.

The live Hub is not a template or filesystem source. The reviewed profile was
manually extracted and sanitized in the repository. Hub mutable state,
authority, credentials, package database, cache, history, and other owner
configuration are excluded.

## Expected effects

- one independent writable root snapshot and one independent home subvolume;
- one `graphical-base` registration with a fresh generation;
- the immutable `hyprland-base-v1` release remains unchanged;
- the Environment Waybar matches the Hub ASCII design except that
  `hyprland/workspaces` appears immediately to the right of the date;
- no activation occurs during creation or profile installation.

## Current capability truth

- private Host-mediated outbound networking is expected through `host0`;
- playback audio is proven only for the official-Hub launcher and is not yet
  claimed for this fixture;
- Bluetooth is visible in the presentation but remains unavailable until an
  exclusive, revocable controller mediator is designed and verified;
- the APX button remains unavailable until the typed client, descriptor,
  socket, broker, and exact-generation effect adapter are installed together.

## Future cleanup proof

If deletion is later approved, verify absence of the registration, machine,
units, processes, mounts, root/home subvolumes, qgroups, runtime descriptors,
plans, and operation residue. Do not remove the shared immutable release or any
Hub state as part of that cleanup.

## Applied result

The plan was applied on 2026-07-31 with digest
`d4b37f676c851c46e2e2d9fb0ff416f2bce5e891bf400912e8291e0e2278da83`.
The resulting stopped Environment is generation
`1df14250-c628-49d4-961e-44ad22fd67a4`. Its copied Waybar configuration and
stylesheet exactly match the reviewed Environment profile hashes. The original
release-provided files are retained only as local seed backups in that
disposable Environment.

Creation initially stopped before publication because the installed runtime
expected an obsolete Hyprland seed digest. The partial path was already absent,
so the bounded recovery was made idempotent: a matching uncertain unpublished
operation may now close only after the exact target is proven absent. Recovery
completed with no uncertain operation, then a fresh plan created the fixture.
