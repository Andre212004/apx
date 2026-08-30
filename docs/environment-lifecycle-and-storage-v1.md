# Environment Lifecycle and Storage v1

Status: architecture proposal complete for review; no storage layout or
lifecycle mutation is implemented or authorized.

## Purpose and Boundary

This document defines the backend-neutral storage objects, lifecycle states,
operation protocol, recovery rules, and data-loss boundaries that a future APX
executor must preserve.

It does not select `systemd-nspawn`, Podman, a virtual machine, final physical
paths, or a Btrfs qgroup hierarchy. A backend may add private objects but may
not weaken these contracts or make the Hub a lifecycle exception.

Confirmed product requirements remain:

- applications, dependencies, data, configuration, and runtime state are local
  to one Environment;
- every Environment, including the Hub, follows the same lifecycle rules;
- common defaults come from a reviewed versioned base, never the live Hub;
- Environment package administration cannot mutate host package state;
- destructive actions require explicit data-loss scope and fresh identity
  evidence;
- only one normal graphical workload Environment is active at a time.

The object model and state machine below are proposals pending architecture
acceptance. Their repository-level threat-model review and physical Btrfs
proposal are recorded in `lifecycle-threat-model-review-v1.md` and
`btrfs-storage-layout-v1.md`. Backend validation, authorization transport,
session handoff, template format, encryption, and export policy remain open.

## Object Model

- **Base:** immutable verified common operating-system content.
- **Role template:** immutable declaration layered on a base, such as Hub,
  development, gaming, or university.
- **Definition:** desired identity, role, template, policy, and resource limits.
- **Root:** Environment-local operating-system and package state.
- **Home:** Environment-local documents, configuration, and application data.
- **Runtime:** ephemeral process, namespace, mount, network, device, and session
  state.
- **Registration:** atomically published ownership of one Environment
  generation and its resources.
- **Operation record:** write-ahead record for one requested mutation.
- **Generation:** monotonically increasing registration revision that rejects
  stale plans.
- **Snapshot set:** immutable, mutually bound capture of root, home, definition,
  generation, and provenance.
- **Archive:** portable verified representation of a snapshot set, not an
  active Environment.

| Object | Mutability | Required identity | Lifetime |
|---|---|---|---|
| definition | typed updates only | canonical digest and generation | Environment |
| registration | atomic replacement | Environment ID and generation | Environment |
| root | writable | backend and storage identity | Environment |
| home | writable | storage identity | Environment |
| runtime | ephemeral | activation ID | one activation |
| snapshot set | immutable after publication | snapshot-set digest | independent |
| archive | immutable after publication | archive digest | independent |

An Environment references but never owns or mutates one base and one template.
Deleting it cannot delete shared artifacts. Garbage collection is a separate
operation. Root and home remain separate objects even on one Btrfs filesystem,
allowing separate quotas, data-loss scope, and verification.

## Logical Namespace

The contract uses this logical namespace; it does not select physical paths:

```text
state/
  bases/<base-id>/
  templates/<template-id>/
  environments/<environment-id>/{registration,definition,root,home-reference}
  operations/<operation-id>/
  snapshots/<snapshot-set-id>/
  archives/<archive-id>/
  runtime/<activation-id>/
```

Home may live under a separately mounted Btrfs parent. Ownership is never
inferred from a pathname, label, Linux owner, or Environment name. For Btrfs,
authoritative evidence may include filesystem UUID, subvolume ID and UUID,
received and parent UUIDs, qgroup association, and mount identity. Mandatory
fields depend on the still-unselected physical topology.

## Invariants

1. An Environment ID identifies at most one published registration.
2. Every mutable root and home belongs to exactly one Environment generation.
3. No writable object is shared between workload Environments.
4. Bases, templates, snapshots, and archives are immutable after publication.
5. The Hub may share a base but is never the source of a workload.
6. A runtime references one generation and cannot outlive verified stop.
7. Registration is published only after independently observed postconditions.
8. Every mutation publishes an operation record before its first effect.
9. Names, paths, ownership, and intended records never prove deletion authority.
10. Uncertainty preserves data unless rollback is freshly proven lossless.
11. Plans bind generation, object identities, policy, and protocol version.
12. Operations cannot mutate a base, template, host, Hub, or another Environment.

## States and Transitions

Stable usable states are `inactive` and `active`. Transitional states are
`provisioning`, `activating`, `stopping`, `snapshotting`, `archiving`,
`restoring`, and `destroying`. `incomplete` means the intended state cannot be
proven after interruption or failure.

`archived` is not an Environment state: an archive is independent. Absence is
also not a state; after registration and resources are proven absent the
Environment no longer exists.

```text
absent -> provisioning -> inactive
inactive -> activating -> active
active -> stopping -> inactive
inactive -> snapshotting -> inactive
inactive -> archiving -> inactive
absent -> restoring -> inactive
inactive -> destroying -> absent
any transitional state -> incomplete
incomplete -> recovered prior stable state
incomplete -> separately approved cleanup -> absent
```

Restore creates a new Environment ID by default. Replace-in-place restore is
outside v1. The Hub uses this same state machine. A recovery policy may block
destruction of the currently needed Hub until another verified recovery path
exists, but that is a precondition, not a special lifecycle.

## Common Operation Protocol

Every mutation follows the same protocol:

1. **Observe:** collect fresh, bounded, read-only evidence.
2. **Plan:** render typed inputs, effects, gates, data loss, and stable digest.
3. **Authorize:** bind approval to digest, kind, subject, generation, expiry,
   nonce, and executor.
4. **Record:** atomically publish the write-ahead operation record.
5. **Revalidate:** repeat identity and safety gates before effects.
6. **Execute:** perform only the approved typed effects in order.
7. **Verify:** independently observe postconditions.
8. **Publish:** atomically publish registration or immutable artifact.
9. **Finalize:** complete and retire the active operation marker.

An operation record contains no arbitrary command channel. It binds schema and
protocol versions, operation identity and kind, expected generation, input and
output objects, base/template/policy/backend versions, evidence and plan
digests, ordered effects and forbidden effects, approval, executor, current
phase, observed result identities, and final evidence.

Secrets are referenced through separate policy and are not embedded in plans,
registrations, logs, snapshots, or archives by default.

## Create

Creation starts only from verified absence and an immutable base/template pair.
It creates fresh root and home identities, never writable clones of the Hub or
another Environment.

Preconditions include canonical unused identities, verified provenance,
authoritative parents/quota/capacity, supported policy/backend, destinations
free of symlink or mount substitution, and approval bound to the current plan.

Postconditions include distinct and uniquely registered root/home identities,
enforced quotas, intended visibility only, unchanged host/Hub package and trust
state, matching definition, and registration publication after every check.

## Activate and Stop

Activation begins from freshly verified `inactive`, creates a new activation
ID, and does not change resource ownership. `active` is published only after
cgroup, namespaces, mounts, network, devices, session, limits, and isolation
policy match observation.

Stop prevents new entry, requests graceful termination, and then yields clean
stop, protected-work refusal, timeout requiring explicit force approval, or
`incomplete`. Success proves absence of Environment processes, sessions,
mounts, namespaces, network objects, device leases, runtime records, and local
assistant instances. Suspend requires a future model and is not stop in v1.

## Snapshot Sets

V1 snapshots are allowed only from `inactive`; independent root/home snapshots
during live writes are not falsely described as atomic. A future live protocol
must define quiescing and cross-object consistency.

A published set binds source ID/generation, definition, base, template,
backend/policy, read-only root/home snapshot identities, operation/evidence
digests, lineage, trusted creation time, and retention metadata.

A snapshot is not a template. Promotion requires separate sanitization proving
absence of personal data, machine identity, credentials, Hub authority,
runtime residue, and inappropriate mutable trust or package state.

## Archive and Restore

Archive consumes an immutable snapshot set, never live root/home. Publication
requires reopening, hashing, schema validation, and manifest matching. A
partial archive remains unpublished staging and never justifies source deletion.
Compression is not integrity; encryption is not provenance.

Restore reconstructs from a verified archive or snapshot set. It never revives
runtime objects, activation IDs, machine identity, transient networking, device
leases, or approvals. It verifies integrity, provenance, compatibility, fresh
target identities, reconstructed content, quotas, policy, regenerated local
identity, and absence of unrelated storage access. The result records lineage
but receives a new Environment ID and generation. Source Hub permissions,
credentials, assistant access, and device policy do not transfer implicitly.

## Destroy

Destroy starts only from verified `inactive` under separate approval. Its plan
enumerates registration, definition, root, home, runtime residue and affected
references. Deletion is always complete: snapshots, archives, APX-owned named
backups, capabilities and stored plans are included rather than retained.

Immediately before deletion, generation, storage identities, lineage, qgroups,
mounts, processes, runtime state, and registration digests are revalidated.
Any disagreement stops rather than widening deletion by path or owner.
Deletion is leaf-first and registration-last. Final verification proves target
absence and continued identity of protected neighbors.

The single `complete-purge` path requires strong confirmation. There is no
preserve-copies variant. Logical path disappearance moves the Environment to visible
`cleaning`; only complete resource, runtime, qgroup, account, registration, and
physical-cleanup evidence moves it to absent and permits identity reuse. The
detailed contract is `cleanup-completion-v1.md`.

## Incomplete Operations and Recovery

Recovery begins read-only and classifies every involved resource as
`not-created`, `owned-empty`, `owned-modified`, `published`,
`foreign-or-conflicting`, or `identity-uncertain`.

Automatic rollback is limited to freshly proven `owned-empty` resources made
by the current operation that remain unpublished, unused, unmodified,
unmounted, and outside every other registration. Everything else is preserved.
Continuation is permitted only when the original exact approval remains valid
and all gates can be re-established. Destructive cleanup, force-stop,
replacement, or new effects require new approval.

## Base and Template Updates

Updates publish new immutable identities. Existing Environments do not change
silently; migration is a separate planned operation.

Templates may declare packages, desktop integration, policy, defaults, and
bounded first-boot actions. They cannot contain live Hub state or credentials,
personal data, mutable machine/runtime identity, host package databases or
private trust material, administration sockets, or unbounded host-authority
scripts. Publication records base, inputs, tooling, sources, sanitization,
reproducibility, and review identity. Physical artifact format remains open.

The complete proposed distinction between readable definitions, immutable
releases, catalogue admission, sanitization, creation, and updates is maintained
in `base-and-role-template-model-v1.md`.

## Registration Evolution

The current schema-v1 prototype models account and home identity only. It must
not be extended piecemeal before backend and physical storage decisions.

A future schema binds Environment ID/name/role/generation; account mapping;
base/template/backend/policy; root/home identities and quotas; definition
digest and stable state; creation provenance; active activation; retained
artifact relationships; and migration history. Existing ordinary homes under
`@home` cannot become compliant merely by adding metadata.

## Acceptance Gates

Before this proposal becomes confirmed architecture:

1. Review it against normal and high-security threat models. Repository-level
   review is complete; experimental enforcement validation remains.
2. Review and validate the proposed Btrfs parents, mounts, qgroups, and
   authoritative identity checks in `btrfs-storage-layout-v1.md`.
3. Map the system-container experiment to every object and transition.
4. Validate snapshot consistency and teardown on disposable fixtures.
5. Define executor authorization, attestation, replay prevention, and record
   durability.
6. Define template provenance and sanitization.
7. Inject interruption at every effect boundary for all operations.

These gates do not authorize host mutation; every experiment remains separately
planned and approved.

## Visible metadata editing in the physical pilot — 2026-08-25

The current physical pilot permits the authoritative Hub to change only an
Environment's visible `display_name` and `description`. This is not an identity
rename: the logical name, generation, role, release, backend, partition and
storage identities remain unchanged.

The request is bound to the selected logical name and current generation. The
Host accepts it only from the active official Hub QuickShell, while no other
Environment operation is running, and only when an ordinary Environment is
stopped or native Windows is ready. Titles are 1–64 characters and descriptions
0–120 characters; leading/trailing whitespace and control characters are
rejected.

A fixed root-owned runner reopens and validates the protected registration,
changes exactly the two presentation fields and replaces the file atomically in
its original directory and mode. It runs in a transient service with no
capabilities and write access limited to the two Environment metadata parents.
Native-Windows boot validation admits bounded user-selected presentation text
but continues to enforce every physical, firmware and system identity.
