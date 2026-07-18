# APX Hyprland H0 Release Promotion Contract v1

Status: design and non-executing plan only. No copy into `/var/lib/apx`, Btrfs
creation, account configuration, release publication, Environment creation,
GPU/input grant, or Hyprland launch is implemented or authorized here.

## Practical meaning

The project now has a verified temporary filesystem containing Hyprland and its
dependencies. That filesystem is not yet an APX release. Promotion is the
controlled step that would copy it into one new immutable APX template from
which a disposable graphical Environment can later be created.

Promotion does not start Hyprland and does not put it on the Host. The Host
continues to have no graphical packages. The packages remain inside the future
Environment template.

## Exact v1 release

- release ID: `hyprland-h0-v1`;
- source: fixed finalized temporary root
  `/tmp/apx-hyprland-build-v1/rootfs`;
- target directory: `/var/lib/apx/releases/hyprland-h0-v1`;
- target root: `/var/lib/apx/releases/hyprland-h0-v1/root`;
- package count: 332;
- source tree digest:
  `83c58deaa56c83c23eee57dc02ecd3a67ccaede0d75918932f7f3b9557ab3401`;
- finalization report digest:
  `fb8a06d588b3dbf0f48b8626a1effc0df95e4c6dd12bfa995f167fe0376c530a`.

The release is identity-neutral: machine ID empty, root locked, no random seed,
no private pacman trust, no build log, no Development-owned entry, and no
special file. It defines one internal account named `apx`, UID/GID 1000, home
`/home/apx`, shell `/usr/bin/bash`. This account belongs to the future
Environment root; it does not create or change a Host account.

## Closed promotion plan

`src/apx_hyprland_release_promotion.py` consumes supplied evidence only. It
requires the exact source/report identity, healthy Btrfs/APX state, sufficient
capacity, absent destination, and explicit confirmation that the source is
identity-neutral and contains no secrets or runtime residue.

If complete, it emits only `ready-for-separate-promotion-approval` with these
fixed future effects:

1. reverify the finalized source and report;
2. reserve exactly the new release directory without adopting an existing path;
3. create exactly one Btrfs release-root subvolume;
4. copy the normalized tree without changing the source;
5. configure only the fixed Environment-local account and empty identity;
6. write one canonical role manifest;
7. set the release root read-only;
8. independently remeasure and publish the release identity.

No caller path, command, package, user name, UID, shell, service, device, mount,
or configuration payload is accepted. Any existing destination, changed digest,
secret/runtime entry, unhealthy APX/quota state, or insufficient capacity
blocks before an effect.

## Boundaries after promotion

Even a successful promotion would not authorize:

- creation of a graphical Environment;
- stopping Hub or Development;
- changing tty1 or tty2;
- opening AMD DRM or input devices;
- installing anything on the Host;
- launching Hyprland;
- deleting the temporary source;
- retiring or replacing another release.

Those remain later, separately reviewed steps. Promotion rollback preserves an
uncertain or partial new release for inspection; it never deletes it
automatically and never modifies an existing release.

## Current preview — 2026-07-18

The finalized tree was independently remeasured with the expected digest. The
target release is absent, `/var/lib/apx` remains healthy Btrfs with healthy full
qgroup accounting, more than 470 GiB is available, APX has zero uncertain
operations, Hub and Development generations match, and the disposable hold is
unchanged.

The closed supplied evidence is stored in
`docs/hyprland-h0-release-promotion-preview-2026-07-18.json` and produces:

- classification: `ready-for-separate-promotion-approval`;
- blockers: none;
- evidence digest:
  `3686a1b9836e59ffb0438dbcfd6d3fa532f8faf1a59617b20ae57018444948ce`;
- consequence digest:
  `a4a316833dd873f55b6a14564c0da44c44ff8482c340d89d3a72fb16a284b6af`;
- plan digest:
  `dc15038fa6147f6f2ba098e90f880898ff4523586117bc0a338f9ea6e067146d`.

This result requests a separate promotion decision only. It is not standing
permission to execute promotion and grants no later Environment or graphical
authority.
