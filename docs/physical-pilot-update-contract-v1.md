# APX Physical Pilot Update Contract v1

Status: pure candidate, closed artifact reader, readiness preview, ordered
journal, recovery model, and fixed import/effect-plan contract implemented. No
physical importer, installer, service adapter, restart, rollback executor, or
cleanup command is implemented or authorized.

## Why This Exists

The installed physical pilot will need bug fixes and later APX improvements.
Development and GitHub may produce those improvements, but Development must not
edit the Host or Hub directly. A Git commit, passing test suite, or ChatGPT
recommendation is not enough authority to change the running machine.

This contract creates a safe logical route:

```text
Development/GitHub candidate
  -> untrusted bounded staging
  -> independent verification
  -> separate activation decision
  -> stopped Hub and Development
  -> exact component replacement
  -> independent verification
  -> previous version retained for rollback
```

The current implementation models and tests this route only. It cannot perform
any arrow in the diagram on the physical computer.

## Update Scope

The first closed candidate may contain only these named APX components:

- `host-runtime`;
- `host-executor`;
- `hub-client`.

The component list must be unique, sorted, and non-empty. The candidate cannot
carry a shell command, package hook, credential, private key, arbitrary package
list, host path, mount option, service command, or cleanup instruction.

This contract does not update the Linux kernel, Arch packages, bootloader,
firmware, encryption, users, networking, systemd configuration, trust roots,
external SSD, Ollama model, or Environment data. Those require other reviewed
operation families.

## Candidate Identity

`PhysicalUpdateCandidate` in `src/apx_physical_update.py` binds:

- one update identity;
- exact source and expected installed parent revisions;
- artifact digest, byte limit, member count, and member-manifest digest;
- exact component set;
- test-result digest and counts;
- compatibility, rollback, and documentation evidence digests;
- explicit absence of credentials, private keys, commands, and package hooks;
- explicit classification as untrusted.

The candidate remains untrusted even when all fields are valid. Validation
means only that it is structurally eligible for separate review.

## Closed Artifact Reader

`src/apx_physical_update_artifact.py` now implements the first non-extracting
artifact boundary. It accepts only one canonical uncompressed tar whose first
regular member is mode-0600 `manifest.json`, followed by exactly one mode-0755
regular member for each sorted candidate component. The only component member
names are `components/host-runtime`, `components/host-executor`, and
`components/hub-client`.

The reader requires root UID/GID metadata, zero mtime, empty owner names, no PAX
extensions, no links, no directories, no special files, no path traversal, no
extra members, an 8 MiB component ceiling, and canonical duplicate-safe JSON.
It binds artifact bytes/hash/count, source and parent revisions, component set,
manifest digest, member sizes/modes/hashes, and actual reopened content. It
reads bounded bytes in memory for validation and never extracts, executes,
installs, changes permissions, or selects a host destination.

## Fixed staging and component mapping

`src/apx_physical_update_effects.py` closes the next planning boundary without
performing it. A staging plan is derived only from the candidate and ready
preview. Its logical Host root is fixed at `/var/lib/apx/updates/staging`, its
operation directory is exactly the update ID, and its only artifact name is
`candidate.tar`. The plan binds the artifact bytes and digest, candidate,
installed-evidence and preview-plan digests, and the separately supplied import
approval digest. It accepts no caller path, filename, command, or destination.

The first physical candidate is deliberately narrower than the generic
three-component artifact format. Only the singleton `host-runtime` set has a
reviewed target mapping:

- replace one regular mode-0755 file at
  `/usr/lib/apx/apx-lab-runtime.py`;
- require `/usr/bin/apx` to remain a symlink to that exact file, never replace
  or follow the alias as an independent target;
- bind the installed-before digest, candidate-after digest and rollback digest
  to the plan before any future effect.

`host-executor` and `hub-client` remain valid logical artifact component names
but have no physical destination mapping yet. Planning a physical effect for
either fails closed. This avoids guessing how to coordinate the executor
service or the immutable Hub release/current Hub root. A later architecture
decision and separate tests must define those effects.

The contract emits descriptions and digests only. It does not create staging,
read or write `/usr`, stop a service or Environment, change the symlink, retain
rollback bytes, or install the candidate.

## Installed Machine Evidence

The preview also requires a fresh `InstalledPilotEvidence` record. It binds the
physical machine and marker identities, installed source and component digests,
Hub release and generation, Development generation, reconciled audit evidence,
recovery availability, GitHub source recovery, APX journal health, Hub
cleanliness, reconciled Development state, current temporary root-host-mode
inventory, and free-space reserve. A Development repository is required only
when Development is the selected development location. During the explicitly
accepted temporary root-host mode, the evidence instead binds the intentional
simple Development generation and the complete root-host inventory/recovery
boundary; it may not falsely claim a Development checkout exists.

The update is blocked when:

- its expected parent differs from the installed revision;
- tomorrow's physical audit has not been reconciled;
- the recovery console or GitHub source recovery is unavailable;
- any APX operation is uncertain;
- Hub is not clean;
- Development's current generation/state is not reconciled;
- the temporary root-host inventory is stale or unavailable;
- the Host has less than the fixed 16 GiB reserve;
- any required identity is malformed or changed.

The 2026-07-17 audit and 2026-07-18 root-host reconciliation have now run. A
preview still cannot reach ready status until a fresh target-bound evidence
record binds the current simple Development generation, stopped disposable
test hold, exact installed components, root-host inventory, recovery, and host
capacity. Owner-reported state is not substituted for that evidence record.

## Preview and Approvals

Complete matching evidence produces only
`ready-for-separate-import-approval`. The preview lists ten ordered effects and
states these practical consequences:

- Hub and Development must stop during activation;
- Host-owned APX components will change;
- the current components remain a bounded rollback set;
- deleting the rollback set is a later separate decision;
- uncertain state blocks activation and preserves data.

Import approval authorizes bounded private staging and independent verification
only. It does not authorize activation. After the first four effects verify the
artifact and installed identity, a second activation approval is required.

Rollback retirement is never included in either approval. The previous version
remains until later evidence and a separate owner decision establish that it is
safe to retire.

## Ordered Journal

`src/apx_physical_update_journal.py` implements the pure journal:

1. reserve private update staging;
2. copy bounded untrusted bytes;
3. verify members and provenance;
4. reverify installed identity and recovery;
5. require separate activation approval;
6. stop Development and Hub cleanly;
7. retain the exact current rollback set;
8. install the exact reviewed components;
9. verify Host, Hub, Development, and separation;
10. publish the new installed identity while retaining rollback.

Every effect is first marked prepared and then completed with an evidence
digest. The journal is chained so that altered history, replay, stale writers,
and skipped steps are rejected.

## Failure and Recovery

The recovery assessment never automatically installs, rolls back, cleans, or
deletes. It distinguishes:

- no recorded effect;
- private staging that may be safely rechecked;
- verified bytes awaiting a new activation decision;
- a prepared effect whose outcome is unknown;
- partial activation with the rollback set retained;
- complete verified update with rollback retained;
- terminal preserve-and-inspect state.

After activation begins, any uncertainty requires identifying both the current
and previous component sets through the recovery console. APX cannot guess that
the old set is safer, because an interrupted automatic rollback could overwrite
the only working or inspectable state.

## Remaining Physical Gates

Before a real update may be proposed, the repository still needs:

1. the separately authorized physical recovery-console rehearsal;
2. immediate pre-import reobservation of the already reconciled physical state
   and exact installed component identities;
3. reproduction of the exact temporary target candidate after any change to
   its component source (the 2026-07-18 runtime-only candidate was built twice
   and parsed, but is neither an immutable release nor imported);
4. a bounded physical transport that executes the fixed Host-owned staging
   plan (the non-executing plan contract is implemented);
5. independent component verification and compatibility rules;
6. minimum-privilege staging, stop, install, verification, and rollback
   adapters (the host-runtime target mapping is planned but not executable);
7. recovery-console fixtures before and after every effect;
8. revalidation of the existing target-bound dossier after every later gate;
9. a separately reviewed immutable release and explicit owner approvals.

Do not create a tag or write physical update instructions merely because the
pure tests pass.
