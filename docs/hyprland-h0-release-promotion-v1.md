# APX Hyprland H0 Release Promotion Contract v1

Status: promotion plan complete and exact fixed effect adapter under test. The
owner separately authorized creation of only `hyprland-h0-v1` on 2026-07-18.
Environment creation, GPU/input grant, VT change, and Hyprland launch remain
unimplemented and unauthorized.

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

The first authorized run copied the source and configured the fixed account,
then stopped because the normalized package root correctly had no existing
`/etc/hostname` to replace. The reviewed partial tree digest is
`b1bb42da33a9df56b39a28ec84bc11a0cbf14670e2c97efbb805dc294d997664`.
Hub, Development, the disposable hold, source tree, and APX journal remained
unchanged. The adapter now has one recovery continuation for only that exact
writable subvolume/account/home state: create the previously absent fixed
hostname, then finish measurement, manifest, read-only conversion, and final
verification. Any other partial state remains preserved and refused.

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

## Fixed effect adapter

`src/apx_hyprland_release_promote.py` implements only the approved promotion.
It has no arguments and revalidates the exact source tree/report, physical
identity, Btrfs parent, healthy quota accounting, free-space reserve, absent
destination, exact Hub/Development/disposable generations, and zero uncertain
APX operations before its first write.

It creates the new release directory and one Btrfs root, copies the normalized
source, adds only the fixed Environment-local `apx` account and home, writes the
fixed hostname and canonical manifest, remeasures the complete configured tree,
sets the root read-only, and verifies it again. Any partial or uncertain result
is preserved for inspection and blocks retry; the adapter contains no deletion
or automatic rollback path.

## Physical promotion result — 2026-07-18

The exact recovery continuation completed the owner-authorized promotion.
`hyprland-h0-v1` now exists as one read-only Btrfs release root. The result is
stored in `docs/hyprland-h0-release-promotion-result-2026-07-18.json`:

- configured tree digest:
  `4798a8f6a0396dfab94758a9bb2498364a72948c6b2587593eadc04faca15b92`;
- manifest digest:
  `dc1beaaaf6f073f8c3493d2e6b1d001e4b5f07f431f8a522f2125f242151ea40`;
- package count: 332;
- logical/allocated bytes: 1,596,400,518 / 1,736,675,328;
- root read-only and source preserved: true;
- Hub, Development, disposable hold, and zero-uncertainty state unchanged.

No Environment was created and no graphical, GPU, input, VT, service, Host
package, source cleanup, or rollback effect occurred.
