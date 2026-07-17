# APX Physical Pilot Update Contract v1

Status: pure candidate, readiness preview, ordered journal, and recovery model
implemented. No physical update artifact, importer, installer, service adapter,
restart, rollback executor, or cleanup command is implemented or authorized.

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

## Installed Machine Evidence

The preview also requires a fresh `InstalledPilotEvidence` record. It binds the
physical machine and marker identities, installed source and component digests,
Hub release and generation, Development generation, reconciled audit evidence,
recovery availability, GitHub source recovery, APX journal health, Hub
cleanliness, Development repository health, and free-space reserve.

The update is blocked when:

- its expected parent differs from the installed revision;
- tomorrow's physical audit has not been reconciled;
- the recovery console or GitHub source recovery is unavailable;
- any APX operation is uncertain;
- Hub is not clean;
- Development's repository is unhealthy;
- the Host has less than the fixed 16 GiB reserve;
- any required identity is malformed or changed.

The current audit has not run, so no physical update can presently reach ready
status. Owner-reported state is not substituted for the evidence record.

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

1. reconciled results from the physical state audit;
2. exact installed runtime, executor, and Hub-client identities;
3. a closed member manifest and raw artifact reader;
4. a bounded physical transport into Host-owned staging;
5. independent component verification and compatibility rules;
6. minimum-privilege staging, stop, install, verification, and rollback adapters;
7. recovery-console fixtures before and after every effect;
8. a target-bound update dossier with exact hashes and consequences;
9. a separately reviewed immutable release and explicit owner approvals.

Do not create a tag or write physical update instructions merely because the
pure tests pass.
