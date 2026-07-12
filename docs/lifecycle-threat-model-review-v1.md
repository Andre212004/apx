# Lifecycle Threat-Model Review v1

Status: review complete at repository level; validation evidence pending.

## Scope

This review checks `environment-lifecycle-and-storage-v1.md` against the
authoritative APX product threat model. It does not replace or modify that
model, select the isolation backend, report code vulnerabilities, or authorize
host mutation.

## Review Result

The lifecycle contract is directionally compatible with both APX profiles and
introduces no known contradiction with the mandatory security invariants.
Acceptance gate 1 is satisfied at design-review level, but not at experimental
validation level.

The strongest parts are generation-bound plans, write-ahead operation records,
fresh identity verification, preservation under uncertainty, immutable
artifacts, restore-to-new-identity, and the refusal to treat paths or Linux
ownership as deletion authority.

The contract remains intentionally incomplete where enforcement belongs to the
backend, executor, session model, or storage topology. Those gaps are blockers,
not implied guarantees.

## Assets and Boundaries

| Threat-model asset or boundary | Lifecycle control | Remaining proof |
|---|---|---|
| Environment applications and data | distinct root/home identity and ownership | backend visibility and escape tests |
| Host integrity | no arbitrary effects; host state is forbidden output | independently observed host invariants |
| Hub authority | Hub is never a template; permissions do not restore | template sanitization and executor policy |
| Bases and templates | immutable content-bound references | provenance, signature, and reproducibility |
| Snapshots and archives | immutable publication after verification | encryption/export policy and corruption tests |
| Human credentials | excluded from records and artifacts by default | secret broker and consent model |
| Devices and runtime services | activation-scoped, policy-bound runtime | per-profile denial and teardown tests |
| Hub to executor | typed plan, digest, generation, nonce, expiry | authentication, attestation, replay store |
| Executor to host | ordered typed effects and revalidation | minimal privilege and syscall/API surface |
| Environment to kernel | backend isolation policy | shared-kernel escape testing and honest claims |

## Attacker Stories

### Stale or replayed operation

An attacker or failed Hub replays an older destroy or restore request after an
Environment has changed. Generation, object identities, nonce, expiry, policy,
and executor binding must reject it. The replay store and approval authority
remain to be designed.

### Path or identity substitution

A path is replaced by a symlink, mount, recreated subvolume, or reused Linux
account between plan and execution. File-descriptor-relative traversal,
authoritative filesystem identity, immediate revalidation, and neighbor
verification are required. A matching name or owner never permits mutation.

### Malicious template or restored archive

An artifact carries Hub credentials, host hooks, machine identity, privileged
policy, or another person's data. Immutability proves only that bytes did not
change; admission also requires provenance, schema validation, sanitization,
policy normalization, and regeneration of machine-local identity.

### Local root attempts host administration

Root inside an Environment runs a package hook or installer that targets host
mounts, sockets, devices, or package state. The runtime must expose none of
those authority surfaces. Before/after host evidence and malicious fixture
tests are required for both profiles.

### Resource exhaustion through snapshots

An Environment or management failure creates data or snapshots until the host
is unavailable. Root, home, retained snapshots, staging, and global reserve
must have enforced quota domains. Inconsistent quota accounting blocks new
mutation and destructive size claims.

### Interrupted lifecycle mutation

Power loss or executor failure leaves partially created, mounted, published, or
modified resources. The write-ahead record supports classification; only
freshly proven operation-owned empty resources qualify for automatic rollback.
All uncertain data is preserved for a newly approved recovery action.

### Runtime survives stop

A process, namespace, mount, veth, device client, user manager, or assistant
survives graphical logout. Stop succeeds only after independent teardown
observation. Logout alone is never sufficient evidence.

## Profile Review

| Control family | Normal profile | High-security profile | Lifecycle implication |
|---|---|---|---|
| host filesystem | fixed integration only | no host binds by default | binds belong to activation policy, never registration input |
| network | mediated outbound and declared inbound | denied by default | runtime objects must be enumerated and removed |
| devices | explicit usability grants | denied by default | device leases are activation-scoped |
| GPU and raw input | profile-specific grants | denied unless separately reviewed | no snapshot or restore inheritance |
| secrets and portals | scoped services | excluded by default | references, not secret bytes, in metadata |
| capabilities/syscalls | reviewed minimum | stricter allow/deny policy | backend version is plan-bound |
| compute/storage | enforced limits | tighter limits and duration | quota/cgroup inconsistency blocks activation |
| assistants | Environment-local when enabled | excluded by default | stop proves assistant absence |
| kernel escape | shared-kernel limitation disclosed | still shared-kernel unless VM profile | lifecycle state cannot imply VM security |

## Severity Calibration

Critical failures include an Environment or Hub request obtaining arbitrary
host execution, cross-Environment root/home mutation, deletion of an unrelated
resource, or propagation of Hub management credentials into a workload.

High-impact failures include bypassing package isolation, persistent runtime
survival after verified stop, approval replay that performs a privileged typed
operation, high-security network/device access contrary to policy, or restore
that imports privileged identity.

Medium-impact failures include quota bypass that degrades host availability,
metadata leakage without content access, incomplete teardown correctly
detected but operationally hard to recover, or an archive compatibility error
that preserves the source.

Low-impact failures include sanitized diagnostic inaccuracies, deterministic
rendering differences that cannot affect authorization, or availability issues
limited to an already stopped disposable fixture with no data loss.

Severity depends on reachable authority and real deployment. Documentation and
pure deterministic prototype code do not currently exercise a privileged
executor, so many stories become actionable only when a mutating runtime is
introduced.

## Required Security Gates

Before a mutating prototype:

1. Define executor authentication, minimal privileges, attestation, nonce
   durability, expiry, and replay rejection.
2. Define descriptor-relative path resolution and authoritative Btrfs identity
   collection at plan, execution, and verification time.
3. Bind every physical root, home, snapshot, archive, qgroup, and runtime object
   to an operation and generation.
4. Specify template/archive admission and secret sanitization.
5. Specify normal and high-security policy vocabularies with no caller-chosen
   host paths, devices, capabilities, or commands.
6. Test failure at every effect boundary and verify conservative recovery.
7. Preserve the shared-kernel warning and require a stronger backend when the
   threat model includes hostile kernel exploitation.

## Conclusion

The logical lifecycle proposal passes repository-level threat-model review.
Its security claims remain conditional on the physical storage proposal,
executor protocol, selected backend, session handoff, and experimental denial
tests. It must not be relabeled as implemented or security-validated.
