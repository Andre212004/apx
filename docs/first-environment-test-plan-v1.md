# First APX Environment Test Plan v1

Status: Phase A disposable offline-root build passed on 2026-07-12; boot phases
remain proposals and are not authorized.

## Plain-language objective

The first test proves that APX can create one small, disposable Arch computer,
start it without exposing the host, stop it cleanly, and remove every resource
it created. It is a console and lifecycle test, not yet the promised Hyprland
desktop demonstration. Passing it is the shortest safe route to that graphical
test because it validates the same base, package ownership, isolation, startup,
shutdown, and cleanup foundations first.

## Current candidate result

The downloaded packages are authentic and the temporary filesystem is complete
and free of personal machine identity. It is not launchable yet. Raw archive
opening deliberately did not create pacman's installed-package records and,
because it ran without administrator powers, its files have development-fixture
ownership rather than final internal root ownership. Launching it now would
produce misleading results and could make package management unreliable.

## Closed test identity

The test will use a new operation identifier and one generation-bound logical
name, `apx-first-console-v1`. It must never adopt an existing path, user,
container registration, network interface, cgroup, or Btrfs identity. Exact
digests for the verified package manifest, signatures, package metadata, and
source tree are mandatory inputs to the preview.

## Phase A: rebuild a correct disposable root

Create a new root owned by the future privileged executor, still separate from
the current extracted fixture. Use only the 138 already verified package files,
with networking disabled. Populate the filesystem and pacman database through
pacman's root-directed installation semantics, not by copying the raw fixture.
Package scripts and hooks must run inside the new root boundary or be rejected;
none may address host paths. Record final ownership, permissions, package
database identities, package file hashes, and absence of machine-local secrets.

This phase needs a separate exact approval because it invokes package
installation logic, even though its intended destination is disposable.

The separately authorized Phase A run created only
`/tmp/apx-first-console-build-v1`. Network isolation wrapped keyring setup and
pacman installation. Pacman recorded all 138 verified packages in the new
root's own database. The result uses 614,490,112 allocated bytes, has no files
owned by the Development Environment identity, and has no remaining runtime
sockets or special files. Its unique generated machine identity is recorded by
hash rather than exposed. Final report digest:
`741fe1c332c334f9f0667b295ae98e7de686c752c3f415e169e0e48912535b68`.
No candidate content was booted and no host package was installed.

## Phase B: read-only boot preview

Before starting anything, render the exact `systemd-nspawn` request and reject
host networking, host package paths, host home paths, device write access,
privileged capabilities beyond the reviewed minimum, and unbounded resources.
The candidate root is exposed read-only for the first boot observation. A
temporary writable runtime layer holds generated machine identity and logs so
the reviewed base remains unchanged.

The deterministic Phase B preview is now implemented and passed repository
tests. It fixes a 120-second timeout, 512 MiB memory ceiling, 256-task ceiling,
50% CPU quota, private network with no external route, closed device policy,
private user mapping, no host binds, no machine registration, no journal link,
and a volatile overlay over the unchanged source root. Preview digest:
`676d22c1d3b9f8d5f9005d20583addeafdc0abdf42986b38b9c67cda29b8fd28`.
Generating this preview did not execute `systemd-nspawn`.

The first authorized Phase C attempt stopped before starting systemd because
the installed nspawn parser requires comma-separated capability names. It
returned code 1, started no candidate content, left zero matching processes and
mounts, and preserved the source report. Failed-attempt report digest:
`daddc5109d728b2c9083114019da457568fa38488e5917409aa28c1f3fc5f413`.
The punctuation-only correction preserves the same dropped capabilities and
produces preview digest
`53c30a3c55c1a6b5b196d9f73694b3b6851e7cab84fdcd6f4bcace24bdb91944`.
It is deliberately blocked from execution until separately authorized.

## Phase C: bounded console boot

Start only `/usr/lib/systemd/systemd` with a fixed timeout, private process and
IPC views, private networking with no external route, bounded memory/CPU/tasks,
no GPU, no audio, no removable devices, and no host home. Prove that PID 1 is
inside the container, the Arch release identity is correct, the 138-package
database is visible, and host sentinel paths are absent. Do not log in, install
software, or run a graphical session in this first boot.

## Phase D: verified stop and complete cleanup

Request a clean shutdown, wait for every contained process to disappear, and
verify the absence of registrations, mounts, cgroups, runtime files, network
objects, open handles, and generation identity. Remove only the exact resources
listed in the approved operation record. If any identity disagrees or deletion
is still pending, report cleanup as incomplete rather than claiming success.

## Pass conditions

- correct root ownership and a complete pacman installed-package database;
- no personal identity, credentials, host home, or host package database;
- bounded offline boot reaches a healthy systemd state;
- container sees the intended Arch base and cannot see host sentinels;
- clean shutdown leaves no process or runtime attachment;
- exact disposable resources are removed and independently absent;
- the immutable verified package and base evidence remains unchanged.

## Route to the graphical demonstration

After this console test passes, build a separate versioned Hyprland role from
the admitted base, add the graphical packages through the same local package
boundary, validate GPU/input/audio/portal access, and start a disposable
graphical Environment. Only after that works should APX connect the Hub button,
Environment switching, right-click deletion, and archived-Environment views to
the real lifecycle executor.

## Authorization boundary

This document does not authorize Phase C. The next request must bind the exact
preview digest and permit only the bounded console boot, observation, clean
stop, and removal of transient runtime state. No Btrfs, persistent user,
service, login-manager, desktop, package, or system configuration change is
included.
