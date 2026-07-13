# First APX Environment Test Plan v1

Status: all first-console build, boot, observation, stop, and cleanup gates
passed by 2026-07-13; graphical Environment work remains separate.

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

The separately authorized corrected attempt passed option parsing but stopped
before systemd because the host's `/tmp` filesystem cannot provide ID-mapped
mounts. It again left zero matching processes and mounts and preserved the
source. Report digest:
`0de4390b36caeb65f35fcc527ce92420615e263457b90bd09b2637295295bda7`.
Removing private-user isolation is rejected. The v3 preview instead creates an
exact temporary runtime copy under `/tmp/apx-first-console-runtime-v3`, caps it
at 1 GiB, shifts ownership only in that copy, boots with the original limits,
and requires deletion of the copy after verified shutdown. The source remains
unchanged. V3 preview digest:
`6853311174a1cf4b3822f663a96fc9715e8871f4b36e00ab7dd38400c4bc07a6`.
It is not authorized to execute.

The authorized v9 run closed the console gate. Read-only systemctl queries
reported overall state `running`, both `multi-user.target` and
`systemd-user-sessions.service` active, zero failed units, and zero pending
jobs. Every v7 isolation/package proof repeated; clean stop returned code 0,
removed the copy, left zero residue, and preserved the source. V9 report digest:
`f129d383b0b6c4cc8a80882a46a7237c16becb76693a1af97b2f20ea11b44432`.
The evidence-only final assessment passed boot, isolation, own package boundary,
session readiness, clean lifecycle, and source preservation. Assessment digest:
`de0266fa91884d05c84887a4a91740e52db82c3067d5fc454337f3509c6998b6`.
The first console Environment lifecycle gate is complete.

The authorized v8 run repeated every v7 success but did not observe the
user-sessions readiness condition within 30 seconds. It stopped cleanly with
code 0, removed the copy, left zero residue, and preserved the source. Report
digest:
`e3a93175545bdeeeb56f1421eaee6bea98963f3c0bac33761c77a58185058b3d`.
V9 keeps all prior read-only observations and adds only fixed `systemctl`
queries inside the already isolated namespaces: overall system state, active
state for `multi-user.target` and `systemd-user-sessions.service`, failed units,
and pending jobs. These queries cannot start, stop, enable, or alter a unit.
V9 preview digest:
`1f3bbd7c8b9701dd523c8185379093e82a8b9966e177dec229c296acc39aafa6`.
It is not authorized to execute.

The authorized v7 run produced the first positive isolated-boot proof. The
observer identified systemd as namespace PID 1, distinct PID/mount/user/network
namespaces, the internal systemd runtime, exactly 138 package records, and an
absent host Development home. It then requested a clean stop; code 0, zero
process/mount residue, removed copy, and unchanged source all passed. Report
digest:
`310e12efec05eec8dcf7d52bc0192bf9289037c62d6b2ba83400e8c309be233e`.
The old multi-user marker was invalid because target units do not publish the
invocation file assumed by the observer. V8 instead requires the active
`systemd-user-sessions.service` invocation marker and absence of `/run/nologin`,
the concrete readiness boundary for user sessions in this root. All other
behavior is unchanged. V8 preview digest:
`d0fa74a7695412a7cbc7560e70f879a3248562417754a1ac3895dd263c40e2f9`.
It is not authorized to execute.

The authorized v6 run observed for 30 seconds, requested a clean stop, returned
code 0, removed the copy, left zero process/mount residue, and preserved the
source. The observer recorded no PID 1 because it required systemd's mutable
process title to retain the original `--unit` argument. Report digest:
`8d9cd684d9f670ba8ce08ac0bb751e490cbe73cae7d07610d18738c6f0816df1`.
V7 changes only process identification: the executable must end in `/systemd`
and Linux's read-only `NSpid` status must report namespace PID 1. All boot,
observation, isolation, timeout, and cleanup rules remain. V7 preview digest:
`0f59742d68e041b7bc2147dce7a2a901dd575ed0c99929875f1ac844dbcc883b`.
It is not authorized to execute.

The authorized v5 run again retained container PID 1 until the 120-second
timeout, removed its runtime copy, left zero processes and mounts, and preserved
the source. Explicit console flags still produced no systemd readiness marker,
so success remains unproven. Report digest:
`a68561a540c9cd2c8801df3e1696dded28581119fdd0577a2040938e2fa40156`.
V6 keeps the same boot boundary but adds a 30-second read-only observer through
`/proc`. It must identify the container PID 1 executable, distinct PID/mount/
user/network namespaces, the internal systemd runtime marker, exactly 138
package records, and absence of the host Development home. It may then stop the
test early. V6 preview digest:
`7585522ccf01168db8efa4b6d6382d23f475bbc4b64d0f68580e127e189617ad`.
It is not authorized to execute.

The authorized v4 run retained a container PID 1 for the full 120-second bound,
then timeout requested termination. It removed the runtime copy, left zero
processes and mounts, and preserved the source. However, the console exposed no
systemd readiness evidence, while reporting that the private-user boundary
could not apply `RLIMIT_CORE`. Therefore the run is not counted as a successful
boot. Report digest:
`6bd0d43a800b416201613932f93b8e2fe49c3f37dd834338cc5667c619a3c1f0`.
V5 requests explicit systemd console/status logging and replaces the
incompatible core limit with `Storage=none` and `ProcessSizeMax=0` in a fixed
coredump policy written only to the disposable copy. All prior boundaries and
cleanup requirements remain. V5 preview digest:
`93aa2e816680a6f570ea584352063ab4841e5a1eca11cfc4ca0df466c9840c0e`.
It is not authorized to execute.

The authorized v3 attempt created and byte-verified its bounded runtime copy,
but nspawn rejected combining ownership shifting with its implicit read-only
volatile overlay. It started no systemd, left zero processes and mounts,
removed the runtime copy, and preserved the source. Report digest:
`d13733fdf7ebf09a88b9072127a350f670997f40976cc517206a6afaedf428ae`.
V4 removes only the redundant overlay: the exact runtime copy is itself the
writable disposable layer and remains mandatory to delete. Private users,
network/device/resource limits, timeout, source immutability, and all other
prohibitions remain. V4 preview digest:
`0db2db8bdf726e4855244bb3201fb0290f2b5d15da1c6eaf7ee97494307c79c3`.
It is not authorized to execute.

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

This passed console result is evidence for the new clean-install sequence, but
it does not replace C0–C6. First prove the real bootstrap, headless Hub,
headless Development Environment, Environment-local packages, lifecycle,
storage, recovery, and daily CLI operation. Then build a separate versioned
Hyprland role from the admitted base, validate GPU/input/audio/portal access,
and run H0 with one disposable graphical Environment on a host with no active
graphical owner. Only after H0 works should APX connect graphical Hub controls
to the same lifecycle protocol already used by the CLI.

## Authorization boundary

This document does not authorize Phase C. The next request must bind the exact
preview digest and permit only the bounded console boot, observation, clean
stop, and removal of transient runtime state. No Btrfs, persistent user,
service, login-manager, desktop, package, or system configuration change is
included.
