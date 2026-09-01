# APX Cleanup Completion v1

Status: complete-purge policy, evidence assessment, Hub progress state and the
bounded physical Environment executor are implemented.

## User Choice

Deletion has one scope: `complete-purge`. It deletes all APX-owned Environment
resources, including live data, snapshots, archives, explicitly named legacy
maintenance backups, capabilities, metadata and stored plans, after strong
data-loss confirmation. There is no preserve-copies option.

The plan enumerates every resource and immutable identity digest. A pathname,
name, owner, or matching type is never deletion authority. Anything not proven
APX-owned remains outside the scope. The append-only global audit journal keeps
only the fact and outcome of deletion, not recoverable Environment content.

## Completion Definition

Path disappearance is progress, not completion. The Hub keeps the Environment
visible as `A limpar` until authoritative evidence proves:

- every selected subvolume, runtime, network object, account, registration,
  qgroup, snapshot, and archive is absent;
- no selected subvolume remains `DELETED` and no selected qgroup remains
  `<under deletion>` or `<stale>`;
- no process, open handle, mount, or network state remains;
- quota accounting is consistent and protected neighbors are unchanged;
- fresh free-space evidence has been recorded.

Only then is the Environment identity reusable. Observed free-space increase
is reported factually. APX does not promise that it equals logical data size,
because Btrfs extents may have been shared with retained snapshots or other
approved artifacts.

## Pending and Failure Behaviour

`deletion-requested`, `under-deletion`, and `stale` remain `freeing-space`.
Unavailable or changed identity becomes `preserved-uncertain`; safety-gate
failure becomes `failed`. Neither state triggers broader or forced cleanup.
Recovery needs fresh evidence and separate approval. Restart resumes
observation from the journal and must not replay an already completed effect.

The Hub may continue managing unrelated healthy Environments while a cleanup
card remains visible. It cannot reuse the pending Environment name, identity,
quota allocation, or registration.

## Implemented Contract

`src/apx_cleanup.py` implements the fixed complete-purge scope, canonical resource plans, plan
digests, exact observation-set validation, cleanup assessment, observed reclaim
reporting, and plain-language output. `src/apx_hub.py` implements the visible
`cleaning` state with read-only progress and detail actions. The installed
`apx-lab-runtime.py` owns the bounded physical effect.
