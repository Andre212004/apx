# Btrfs Storage Layout v1

Status: physical-layout proposal for review; no subvolume, mount, quota, or
host path is implemented or authorized.

## Purpose

This proposal maps the logical lifecycle objects to Btrfs while preserving
separate Environment roots and homes, immutable shared artifacts, bounded
storage, snapshot lineage, conservative deletion, and backend independence.

It defines path classes and topology, not proof that those paths currently
exist. Existing manually created homes remain ordinary directories under the
current `@home` subvolume.

## Decisions Proposed

1. Use a flat subvolume layout under each Btrfs filesystem's top level.
2. Keep control metadata as small atomic regular files, outside Environment-
   writable roots and homes.
3. Mount root and home into a runtime by exact subvolume identity, not by
   walking an Environment-controlled path.
4. Use traditional hierarchical qgroups for v1, not simple quotas.
5. Charge live state and retained snapshots to explicit artifact domains.
6. Snapshot root and home separately while inactive, then bind them with one
   immutable snapshot-set manifest.
7. Treat a local snapshot as rollback material, not a backup.
8. Use full, verified archive streams before considering incremental archives.

## Why a Flat Layout

Btrfs snapshots are not recursive: nested subvolumes become barriers rather
than included content. A visually nested tree would therefore create misleading
snapshot and deletion semantics. APX instead proposes flat physical subvolumes
with relationships recorded in trusted metadata.

Human-readable names aid inspection but never prove identity. Every operation
uses filesystem UUID, subvolume ID, subvolume UUID, parent/received UUID when
applicable, generation, read-only flag, and qgroup membership as required.

## Host Path Classes

The existing `/var/lib/apx` direction is retained as the proposed control and
root-state prefix. Dedicated homes remain mounted at `/home/<internal-account>`.

```text
/var/lib/apx/
  metadata/
    environments/<environment-id>.json
    definitions/<environment-id>.json
    operations/<operation-id>.json
    snapshots/<snapshot-set-id>.json
    archives/<archive-id>.json
  mounts/
    roots/<environment-id>/
    artifacts/<artifact-id>/
  archives/<archive-id>/

/home/<internal-account>/
```

`metadata` is executor-owned and not visible writable inside any Environment.
`mounts` contains executor-established mountpoints, not ownership-bearing
directories. Archive files are regular immutable publications with separate
manifest and digest evidence; they are not Btrfs snapshots.

The executor also needs a private top-level management mount for every approved
Btrfs filesystem so it can address flat subvolumes without exposing the
top-level tree to an Environment. Its final runtime path is deliberately not
fixed until executor and mount-namespace design; it must be inaccessible to
Hub and workload sessions.

## Flat Physical Subvolumes

Within the applicable Btrfs top level, names use opaque IDs rather than user
labels:

```text
apx-base-<base-id>
apx-template-<template-id>
apx-root-<environment-id>
apx-home-<environment-id>
apx-snap-root-<snapshot-object-id>
apx-snap-home-<snapshot-object-id>
apx-stage-<operation-id>
```

Root and home may be on different Btrfs filesystems. If `/var/lib/apx` or
`/home` is not backed by a suitable Btrfs filesystem with working quotas, the
operation is blocked; APX does not create an implicit loopback filesystem or
fall back to an ordinary directory.

Base/template layout remains provisional because the selected backend may use
read-only snapshots, image files, or another verified representation. Whatever
the representation, the Environment cannot receive a writable reference to
shared base/template state.

## Mount Topology

For an inactive Environment, root and home are not exposed through a running
namespace. Executor inspection uses its private management namespace.

During activation:

```text
verified root subvolume -> backend machine root
verified home subvolume -> /home/<container-user> inside that machine
declared integration    -> individually policy-bound read-only or mediated surfaces
```

The host-facing `/home/<internal-account>` mount is the dedicated home
subvolume for compatibility with the internal Linux identity. The backend must
not also expose the host `/home` parent. No Environment receives the Btrfs
top-level mount, another APX mountpoint, `/var/lib/apx/metadata`, or archive
storage.

Mount creation uses already-open trusted parent descriptors or an equivalent
non-traversing API, exact source identity, fixed flags, and a private mount
namespace. Symlinks, caller-controlled paths, mount propagation, unexpected
pre-existing mounts, and identity changes block activation.

Required mount properties include:

- root/home writable only for the owning Environment activation;
- base/template read-only through every reachable mount;
- `nosuid`, `nodev`, and `noexec` applied where compatible with the specific
  data surface, not falsely applied to an executable machine root;
- no shared mount propagation back to the host;
- no host package database, lock, keyring authority, runtime socket, or Hub
  metadata exposure;
- teardown verified by mount ID and namespace identity, not pathname alone.

## Qgroup Hierarchy

Traditional qgroups are proposed because APX needs shared-versus-exclusive
accounting across snapshots. Simple quotas account extents to the first
allocator and cannot provide the same deletion and sharing semantics.

Qgroups are filesystem-local. Each filesystem uses opaque numeric IDs recorded
in metadata; an Environment ID is never hashed or truncated into an
authorization-relevant qgroup ID.

```text
0/<subvolid>                  automatic leaf for each subvolume
1/<object-domain-id>          live root or live home plus its retained snapshots
2/<environment-domain-id>     all APX objects for one Environment on this filesystem
2/<artifact-reserve-id>       independently retained snapshot objects
3/<apx-pool-id>               all APX charged objects on this filesystem
```

Where root and home use separate filesystems, each has a separate hierarchy and
limit; no cross-filesystem total is claimed as kernel-enforced. APX may report
their sum, but capacity gates are evaluated independently on both filesystems.

Proposed limits:

- leaf maximum referenced size limits the writable live root or home;
- level-1 referenced limit charges the live object and snapshots that remain in
  its retention domain;
- level-2 referenced limit bounds one Environment's total on that filesystem;
- level-3 referenced limit preserves a host-wide APX pool reserve;
- exclusive values inform estimated reclaim but never alone authorize deletion.

Limits must be assigned as part of subvolume/snapshot creation when possible.
Late assignment can require rescan and creates a window where accounting is not
authoritative.

## Quota Health Gate

Quota enforcement is trusted only when:

- quota is enabled in the selected traditional mode;
- every expected leaf and parent assignment exists exactly once;
- configured limits match registration and policy;
- no rescan is running;
- accounting is not inconsistent;
- a bounded write fixture has demonstrated enforcement for the experimental
  topology;
- free-space reserve remains above the policy floor.

If any condition is unavailable or false, APX blocks creation, restore,
snapshot, archive staging, and any destructive operation that relies on size or
reclaim claims. Active Environments may require an orderly stop depending on
host capacity, but APX never presents an inconsistent qgroup as enforced.

## Snapshot Protocol

V1 snapshot sets require the Environment to be fully stopped and all root/home
writable mounts absent. The executor then:

1. revalidates source identities, generation, quota health, and absence of use;
2. creates a read-only root snapshot with qgroup inheritance;
3. revalidates that root remained unchanged and no runtime appeared;
4. creates a read-only home snapshot with qgroup inheritance;
5. revalidates both snapshot identities, flags, parent UUIDs, and source state;
6. publishes one manifest binding both snapshots and the source generation.

Btrfs does not provide a cross-subvolume transaction for this APX snapshot set.
Consistency comes from verified inactivity throughout the bounded sequence. Any
write, mount, runtime, identity, or quota change prevents publication and leaves
the snapshots as operation-owned incomplete resources.

Read-only is verified from subvolume flags, not inferred from a read-only mount.
Snapshots are immutable APX artifacts after publication even if privileged
Btrfs tooling could technically change their flags.

## Archive Protocol

A Btrfs send stream is generated only from a verified read-only snapshot.
Read-only mounting alone is insufficient because another writable mount could
exist. V1 uses full streams; incremental parent selection and retention create
additional dependency and deletion hazards and are deferred.

Root and home streams are bounded staged files. The archive manifest binds:

- snapshot-set, root snapshot, and home snapshot identities;
- stream format/tool/kernel compatibility evidence;
- byte length and cryptographic digest of each stream;
- definition, base, template, policy, and provenance;
- archive schema and explicit encryption status.

Publication occurs only after both streams are complete, reopened, hashed, and
validated against the manifest. CRCs inside a send stream are transport checks,
not the archive's provenance or publication digest.

## Restore Protocol

Receive runs only in a fresh operation-owned staging parent on an approved
Btrfs filesystem. Received subvolumes are never mounted into an Environment
until content, read-only flag, received/parent lineage, manifest, quotas, and
fresh target identity have been verified.

Because received subvolume identifiers can differ from the source, restore
records the new authoritative identities and preserves source lineage
separately. Writable root/home objects are created as fresh snapshots or copies
according to the selected backend; published received snapshots remain
immutable artifacts. A receive destination is never caller-selected.

## Destroy and Reclaim

Destruction identifies exact leaf subvolumes and validates membership in the
approved Environment and qgroup domains. It refuses:

- unexpected child or nested subvolumes;
- missing, duplicate, stale, or inconsistent qgroups;
- mounts, open runtimes, changed UUIDs, or unrecorded snapshots;
- retained artifacts not explicitly listed for deletion;
- size or identity evidence that became unavailable.

Registration is removed last. Btrfs deletion may complete asynchronously, so
path disappearance alone is not final proof of reclaimed storage. Final
reporting distinguishes logical absence from completed filesystem cleanup and
observed quota/free-space recovery.

## Capacity and Reserve Policy

The Stage 2 experiment retains its proposed 8 GiB root and 2 GiB home budgets.
These are experimental values, not product defaults. Before each allocation,
APX evaluates logical quota headroom, physical unallocated/free space, metadata
pressure, active staging, retained artifacts, and a non-APX host reserve.

Quota limits prevent one charged domain from growing without bound but do not
guarantee physical space or protect against all metadata exhaustion. Capacity
and quota are separate gates.

## Threat-Model Consequences

- Flat subvolumes prevent nested snapshot omissions from being mistaken for a
  complete Environment capture.
- Private top-level access prevents Environment-local root from discovering or
  mounting sibling APX objects.
- Traditional hierarchical qgroups charge snapshots and support bounded
  domains, while inconsistency becomes a fail-closed condition.
- Separate control metadata prevents root/home compromise from rewriting APX
  ownership claims.
- Full archive streams avoid hidden incremental-parent retention in v1.
- Exact identity and neighbor verification constrain confused-deputy deletion.

This topology does not mitigate kernel, Btrfs, storage hardware, firmware, or
physical attacks and does not turn a system container into a VM boundary.

## Open Decisions and Validation Gates

1. Confirm whether root and `/home` reside on the same Btrfs filesystem and
   record both filesystem identities authoritatively.
2. Select the private top-level mount and executor namespace design.
3. Fix numeric qgroup allocation, metadata schema, and collision handling.
4. Measure traditional qgroup performance and consistency with expected
   snapshot counts; compare simple quotas only if required evidence can be
   preserved another way.
5. Validate quota inheritance, rescan failure, deletion latency, metadata
   exhaustion, and crash recovery on disposable fixtures.
6. Define archive encryption, key custody, external media, and import trust.
7. Map system-container root construction and base representation to this
   topology without writable shared state.
8. Resolve how the host-facing dedicated home mount interacts with session
   handoff and container UID mapping.

No gate authorizes creation or mutation on the real host.

## Technical Basis

This proposal relies on the documented Btrfs behavior that snapshots are
non-recursive, subvolumes have persistent numeric IDs and UUID/lineage fields,
qgroups track referenced and exclusive extents hierarchically, inconsistent
qgroups cannot safely enforce limits, and send operates on read-only
subvolumes:

- [Btrfs subvolumes and non-recursive snapshots](https://btrfs.readthedocs.io/en/latest/btrfs-subvolume.html)
- [Btrfs qgroup accounting and hierarchy](https://btrfs.readthedocs.io/en/latest/Qgroups.html)
- [Btrfs send and receive](https://btrfs.readthedocs.io/en/stable/Send-receive.html)

Validation must freeze the actual kernel and `btrfs-progs` versions used by an
experiment.
