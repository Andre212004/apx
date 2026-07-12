# APX Stage 2 Approval Dossier

Status: review package complete at the repository-model level; acquisition,
creation, execution, and cleanup are not authorized.

## Decision Requested Later

Stage 2 is limited to producing a verified minimal Arch base and disposable
root/home storage for `isolation-trial`. It does not boot the container, start a
session, activate namespaces, expose devices, or validate graphical behavior.
Those effects belong to later separately approved stages.

The canonical machine-readable review identity is rendered by:

```text
apx host stage2-dossier
```

The command has no arguments and performs no observation or mutation. Its
digest changes if any intended resource, effect, gate, risk, rollback rule,
destructive scope, or blocker changes.

## Prerequisite Acquisition

The fixed acquisition candidate is `apx-base-2026.07.11-v1`, derived only from
the dated Arch Linux Archive URI. `apx host snapshot-plan` renders the exact
candidate, repositories, seeds, staging/evidence paths, phases, limits,
blockers, and digest without network access.

The candidate is not verified. The trust mechanism uses an explicitly observed
and frozen trusted-host `archlinux-keyring` to authenticate a matching isolated
archive; pacman performs fixed-path resolution/download-only, `pacman-key`
performs primary detached verification, and GnuPG performs the reopened-file
second pass. Host versions and keyring hashes are frozen in the plan. Matching
keyring archive authentication, future executor attestation, the real resolved
manifest, package signatures, capacity evidence, and network approval remain
blockers.

## Intended Resources

Stage 2 proposes exactly five typed resources:

| Type | Identity | Intended path | Publication boundary |
|---|---|---|---|
| immutable base | `apx-base-2026.07.11-v1` | `/var/lib/apx/bases/apx-base-2026.07.11-v1/root` | unpublished shared base until verified immutable |
| Environment root | `isolation-trial-root` | `/var/lib/apx/environments/isolation-trial/root` | unpublished experiment state |
| Environment home | `isolation-trial-home` | `/home/apx-isolation-trial` | unpublished experiment state |
| incomplete operation | `isolation-trial-operation` | `/var/lib/apx/operations/isolation-trial.json` | published before first mutation |
| registration | `isolation-trial-registration` | `/var/lib/apx/environments/isolation-trial.json` | published only after all creation postconditions |

Root has an 8 GiB budget and home has a 2 GiB budget. A pathname, expected
owner, or record never proves identity. Base/root/home require fresh Btrfs UUID,
subvolume ID, parent UUID, quota, and operation-provenance evidence as
applicable. Marker and registration require regular-file identity, canonical
content, ownership/mode, and digest/storage bindings.

## Downloads

The separately approved acquisition would download only:

- dated `core` and `extra` repository databases;
- the closed resolved set, bounded to at most 512 package archives;
- one detached signature per resolved package;
- one `archlinux-keyring` archive authenticated by the explicitly frozen
  trusted-host anchor.

Limits are 64 MiB per database, 1 GiB per package, 4 GiB aggregate, 15 seconds
to connect, 300 seconds per transfer, and two retries. Exceeding a limit aborts;
the operation cannot relax limits at runtime.

## Host Effects

Acquisition would perform bounded network reads and fixed staging/evidence
writes. Stage 2 would later create one base, one root, one home, one incomplete
marker, one internal account, and one final registration, then apply UID/GID,
quota, ownership, and minimal root-filesystem configuration.

Stage 2 performs no boot, graphical session, namespace activation, GPU/audio/
input exposure, Hub copying, Odysseus installation, or Codex installation.

## Gates Before Mutation

- snapshot evidence is `verified` and matches the approved acquisition digest;
- every intended identity and path is authoritatively absent;
- parents are correct and no symlink traversal exists;
- Btrfs quotas and capacity are authoritatively available;
- subordinate UID/GID ranges are valid and non-overlapping;
- the approval binds the exact current dossier digest and is neither expired
  nor replayed.

## Required Postconditions

- base/root/home have fresh, mutually distinct identities;
- base is immutable through the Environment;
- root/home quotas are enforced rather than merely declared;
- account and ownership match the recorded mapping;
- host package database, lock, package list, keyring, cache, and files are
  unchanged;
- no Hub, Development, host-home, secret, or device surface is visible;
- registration is atomically published after all earlier checks;
- final verification includes the published registration;
- the incomplete marker is removed only after final success.

## Failures and Rollback

Failures are `no-effect`, `owned-empty`, `owned-modified`,
`published-incomplete`, or `ownership-uncertain`. Automatic rollback is allowed
only for freshly proven operation-created, unpublished, unused, unmodified
resources. Package population, first use, external modification, uncertain
evidence, or publication ends automatic deletion eligibility.

Matching names, paths, owners, registration, or intended state are never enough
to delete. Uncertain and published resources are preserved as incomplete.

Cleanup is a separate destructive stage and approval. It must render exact data
loss, reconfirm stopped state and absence of processes/mounts/namespaces/network
state, revalidate every identity, and verify absence afterwards. Stage 2
creation approval cannot authorize cleanup.

## Principal Risks

- contaminating host package or trust state while building the base;
- symlink/path substitution or collision mutating unrelated resources;
- incorrect UID/GID mapping exposing host or cross-Environment data;
- unenforced quota exhausting host storage;
- partial publication creating ambiguous ownership;
- system containers later proving insufficient for the intended threat model.

## Remaining Blockers

- future executor attestation and replay-resistant binding for the recorded
  trusted-host keyring/tool evidence;
- real resolved package manifest and all package signatures;
- authoritative staging capacity and parent identities;
- bounded network-acquisition approval;
- approval authentication, lifetime, replay prevention, and executor protocol;
- exact Btrfs qgroup hierarchy and enforcement check;
- separate Stage 2 creation and Stage 7 cleanup approvals.

No blocker is converted into an implementation assumption by this dossier.

`src/apx_stage2_gate.py` implements the pure final conjunction of these gates.
It binds the dossier, acquisition plan, snapshot assessment, trust seal,
capacity evidence, absence and identity evidence, quota hierarchy, host
invariants, network approval, human approval freshness/replay state,
authoritative journal, and separate cleanup scope. Complete evidence produces
only `ready-for-separate-stage2-execution-approval`; the module performs no
effect and cannot authorize graphics, KDE removal, or cleanup.

The fixed `apx host snapshot-readiness` observer collected and the plan froze
the human-authorized host keyring/tool evidence. The prototype deliberately
cannot self-assert privileged authority, so executor attestation remains a
blocker. The observation cannot itself approve acquisition.

The matching keyring archive was subsequently acquired under a separate
bounded approval, verified by pacman-key and a signer-export/gpgv second pass,
and bound to the plan by package/signature/signer-key hashes and `.PKGINFO`
metadata. This closes only the keyring archive blocker; the complete base
remains unacquired.
