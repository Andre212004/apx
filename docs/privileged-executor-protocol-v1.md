# Privileged Executor Protocol v1

Status: architecture proposal complete for review; no privileged service,
socket, authentication mechanism, or mutating operation is implemented.

The repository now contains a pure implementation of the closed operation plan,
request parser, approval binding, expiry, active-session, generation, and replay
precondition contract in `src/apx_executor_contract.py`. It performs no
authentication or host operation; those remain future trusted inputs.

`src/apx_executor_journal.py` now implements the non-privileged journal state
machine and a disposable fixture store. It enforces prepare-before-effect,
ordered completion, final verification, chained records, conservative recovery,
atomic fixture writes, and stale-writer and symbolic-link rejection. It does
not select an authoritative host location, authenticate callers, reserve real
nonces, or perform any host effect.

## Plain-Language Summary

Some APX actions eventually need permission to change important parts of the
computer. Creating storage, starting an Environment, or deleting its data are
examples. The Hub must be able to request these actions without becoming an
all-powerful administrator.

The proposed solution is a small protected executor. The Hub can select only
predefined APX actions. It cannot send shell commands, paths, users, device
names, package-manager arguments, or custom scripts. The executor independently
checks the request, the current machine state, the user's approval, and the
result.

Practical consequences:

- compromising the Hub should not automatically provide unrestricted host
  control;
- an old approval cannot be silently reused after the Environment changes;
- dangerous actions show their real effect and require fresh confirmation;
- a crash leaves a durable record so APX can inspect what happened;
- uncertainty stops the operation and preserves data.

This reduces risk but does not eliminate it. A flaw in the executor, kernel,
authentication system, or selected container backend could still be serious.

## Responsibilities

The design separates five responsibilities:

| Component | Responsibility | Explicitly cannot do |
|---|---|---|
| Hub client (CLI or UI) | show choices, effects, progress, and recovery | invent privileged effects |
| planner | observe state and create a deterministic plan | mutate the host |
| approval authority | prove the human approved one exact plan | change the plan |
| executor | revalidate and perform typed effects | accept arbitrary commands |
| verifier | independently observe postconditions | declare intent as evidence |

These may initially share repository code, but their trust roles remain
separate. The Hub client and planner are not trusted merely because APX supplied
them. The executor treats every incoming value as untrusted.

## Host Placement

The executor is a host-owned component, outside every Environment root and
home. Its executable, policy, socket endpoint, journal, replay records, and
verification code are not writable by the Hub or a workload Environment.

The preferred v1 transport candidate is a fixed local Unix socket exposed only
through a narrowly configured Hub management channel. The host checks the
connecting process identity through the socket and session context. Merely
possessing access to the socket is not approval for an operation.

The socket is never exposed to workload Environments. The Hub receives no host
shell, D-Bus administration surface, systemd control socket, package-manager
socket, filesystem-management socket, or general-purpose privileged API.

The final transport and host paths remain unimplemented and require validation
with the session-handoff design.

## Request Model

The Hub submits a small request containing references, not instructions:

```text
protocol version
operation kind
operation ID
plan digest
subject Environment ID and expected generation
requested policy choice from an internal allowlist
approval reference
nonce and expiry
```

The request contains no command line, executable, shell text, host path,
arbitrary UID/GID, device node, mount option, capability, package list, script,
environment variable, or caller-selected output location.

The executor obtains all concrete effects from its own versioned policy after
matching the plan digest. A Hub-selected Environment label is resolved to a
registered internal ID before planning and never becomes a host path.

Unknown, duplicate, missing, oversized, wrongly typed, or unsupported fields
are rejected. Schema parsing and policy validation occur before any effect.

The production client transport now has a separate closed implementation for
`/run/apx/executor-v1.sock`: fixed Unix-socket path, five-second timeout,
canonical request serialization, 64 KiB response limit, one-line framing, and
an exact response schema bound to protocol and operation ID. It accepts no
caller-selected endpoint, timeout, command, or path.

The endpoint core loads the reviewed plan and approval through injected trusted
authorities, observes current generation/session/state, performs the complete
contract assessment, and atomically reserves the nonce before invoking a typed
effect adapter. Contract rejection never reserves a nonce or reaches effects.
Failure or contradictory evidence after reservation returns `incomplete`
rather than retrying or reporting success. The Unix server wrapper, durable
authorities, and physical effect adapter are not installed yet.

## Operation Catalogue

V1 defines only these operation families:

| Operation | Normal result | Approval class |
|---|---|---|
| `create` | new inactive Environment | explicit confirmation |
| `activate` | one active Environment runtime | unlocked-session approval |
| `stop` | clean inactive Environment | unlocked-session approval |
| `force-stop` | processes terminated; possible lost work | fresh strong confirmation |
| `snapshot` | immutable local snapshot set | explicit confirmation |
| `archive` | verified archive from snapshot | explicit confirmation |
| `configure-capabilities` | generation-bound optional-device policy for next activation | explicit confirmation |
| `restore` | new inactive Environment identity | explicit confirmation |
| `destroy` | Environment removed; retained artifacts listed | fresh strong confirmation |
| `recover-complete` | interrupted approved operation completed | new confirmation unless original remains valid |
| `recover-cleanup` | proven operation-owned resources deleted | fresh strong confirmation |

Read-only list, inspect, status, and plan operations do not use privileged
mutation authority. Shared-base garbage collection, policy migration,
replace-in-place restore, host update, and arbitrary package installation from
the Hub are outside v1.

Candidate import, release verification/admission, replacement-Hub creation,
Hub-generation selection, and old-Hub retirement are also outside this v1
catalogue. Their logical separation is proposed in
`development-to-hub-release-promotion-v1.md`. They require new closed operation
families and cannot be disguised as `create`, `restore`, a host update, or an
arbitrary package action under the current protocol.

All mutation families and `activate` are restricted to trusted evidence for
the authenticated, authoritative active Environment whose logical name is
`hub` and whose role is `hub` or `hub-graphical`. A workload may use only
`stop`, and only against its own active generation. Role and name must agree;
either value alone never grants Hub authority.

`configure-capabilities` cannot carry arbitrary devices in the executor
request. Its reviewed plan is separately generation-bound and limited to the
closed optional set: mediated camera, microphone, controller, and removable
storage. The target must be stopped and the essential capability baseline is
retained.

## Approval Classes

### Unlocked-session approval

Suitable for routine reversible actions such as launching or cleanly stopping
an Environment. It proves that the current human-facing APX session is unlocked
and permitted to control that Environment. It does not authorize data loss.

### Explicit confirmation

The Hub displays the selected Environment, operation, storage effect, network
or download effect, expected duration, reversibility, and plan identity. The
human confirms that exact preview. A materially changed plan requires another
confirmation.

### Strong confirmation

Required for destruction, force-stop, destructive cleanup, or another action
with likely data loss. It requires fresh human authentication or an equivalent
future secure re-verification, not merely an unlocked Hub button. The preview
lists measured data loss, retained snapshots/archives, unsaved-work risk,
irreversibility, and recovery limits.

The exact authentication technology is deferred to the human-identity design.
Automatic Hub entry must not turn strong confirmation into a meaningless
click.

## Approval Object

An approval is a short-lived signed or otherwise authenticated statement that
binds:

- protocol and approval schema versions;
- human identity and current Hub session identity;
- operation ID, kind, subject ID, and expected generation;
- complete plan digest and policy version;
- approval class and displayed consequence digest;
- one unpredictable nonce;
- issue time, not-before time, and expiry;
- approval-authority identity and authentication strength.

It contains no reusable password, recovery secret, private key, biometric data,
or session credential.

The executor checks approval authenticity, current session, required strength,
time window, nonce uniqueness, plan equality, policy compatibility, and current
generation. Failure of any check has no effect.

## Replay Protection

Every mutating operation has a unique unpredictable nonce. Before the first
effect, the executor durably records the nonce with the operation ID and plan
digest. A nonce already reserved, completed, expired, or associated with
different content is rejected.

The replay record survives executor and machine restarts. It is retired only
according to a retention policy long enough to prevent restoration of old Hub
state or metadata backups from replaying approvals.

Restoring an Environment, snapshot, or Hub does not restore executor nonce
state. Clock rollback, unavailable trustworthy time, or journal disagreement
blocks new approvals rather than extending their validity.

## Plan Binding

The planner renders all intended resources, effects, forbidden effects,
preconditions, limits, data loss, rollback boundary, and required
postconditions. The digest covers the complete security-relevant plan but
excludes cosmetic text, timestamps used only for display, and sanitized
diagnostics.

Immediately before execution, the executor rebuilds or independently validates
the plan from authoritative current state. It refuses when:

- the digest changed;
- the Environment generation changed;
- a resource appeared, disappeared, or changed identity;
- policy or executor version is incompatible;
- quota, capacity, session, runtime, or storage evidence is unavailable;
- the approval expired or its required strength increased;
- the requested operation is no longer allowed from the current lifecycle
  state.

The executor never asks the Hub whether a mismatch is safe.

## Durable Journal

Before the first external effect, the executor writes and durably publishes a
write-ahead journal entry. It records:

- operation, plan, approval, policy, and executor identities;
- initial authoritative observations;
- exact ordered effect types;
- current phase and completed effect numbers;
- identities of created or changed resources;
- verification results and recovery classification;
- final completion or incomplete state.

Sensitive raw logs remain separate, bounded, and access-controlled. The journal
does not contain passwords, tokens, secret values, unrelated host data, or
arbitrary command output.

Each phase update is flushed before the next effect. An operation is never
reported complete until final verification and durable publication succeed.

## Crash and Restart Behaviour

On startup, the executor first searches for unfinished journal entries. It does
not begin a new mutation affecting the same Environment or resources until each
entry is inspected.

Restart recovery is read-only by default:

1. reopen the journal through a trusted fixed parent;
2. verify its identity, schema, integrity, ownership, and operation binding;
3. observe every referenced resource again;
4. classify the last proven effect and current lifecycle state;
5. render safe recovery choices.

Automatic continuation is allowed only when the original approval is still
valid for the exact next effect and every gate is freshly satisfied. Automatic
rollback remains limited to proven operation-created, empty, unpublished,
unused, and unmodified resources. Otherwise APX preserves state and asks for a
new explicit recovery decision.

Corrupt, missing, conflicting, or ambiguous journal evidence blocks mutation.
The executor never reconstructs deletion authority from paths or names.

## Concurrency

Only one mutating operation may hold the lock for an Environment generation.
A separate global lock protects shared objects and operations that affect which
graphical Environment is active.

Locks alone are not ownership evidence. Each effect rechecks generation and
resource identity. If the executor dies, a new process may recover a lock only
after confirming the recorded process and operation are no longer active.

Read-only observation may run concurrently but must clearly report when a
mutation prevents a stable conclusion.

## Minimal Privilege

The executor runs with only the host permissions needed for the current typed
effect. The design must prefer small internal modules or tightly scoped helper
processes over one permanently all-powerful process.

Proposed privilege domains are:

- storage identity, snapshot, quota, and mount operations;
- internal account and ownership setup;
- container/runtime creation and teardown;
- network and device policy attachment;
- atomic metadata publication and verification.

No domain accepts raw caller arguments. The executor drops unnecessary
capabilities, uses a fixed clean environment, fixed executable identities,
bounded input/output, timeouts, resource limits, and no shell. A failure in one
domain must not silently grant another domain.

Whether v1 uses one carefully constrained daemon or short-lived helpers remains
an implementation decision. The security boundary and typed protocol are the
same either way.

## Verification

Intent and successful tool exit are not proof. After each meaningful effect,
the verifier observes authoritative state using a separate code path where
practical.

Final verification includes:

- exact expected resource identities and absence of unexpected resources;
- lifecycle state and generation;
- storage, qgroup, mount, process, namespace, network, and device state;
- host, Hub, base, and neighboring Environment protection;
- metadata and journal publication;
- explicit teardown or data-loss postconditions.

Unavailable evidence produces `incomplete` or `requires-confirmation`, never
success.

## User-Facing Consequences

The Hub must present outcomes in ordinary language:

- what APX is about to do;
- which Environment is affected;
- whether files or unsaved work can be lost;
- what will remain afterwards;
- whether the action can be reversed;
- why APX refused or stopped;
- what safe recovery choices exist.

Internal IDs and digests may be available in a technical-details view, but are
not substitutes for a clear explanation.

## Audit and Privacy

APX keeps a bounded history of privileged operations sufficient to explain who
approved what, which policy was used, what changed, and whether verification
succeeded. It does not record user documents, filenames unrelated to the
operation, secret contents, browser activity, assistant memory, or arbitrary
Environment logs.

Audit records are host-owned and cannot be changed by the Hub or workload
Environments. Retention, export, redaction, and future multi-person visibility
require explicit policy.

## Failure Rules

- Parse, authentication, approval, policy, observation, or revalidation failure
  before effects produces `no-effect`.
- Failure after effects produces `incomplete` until authoritative recovery
  proves a stable state.
- The executor never expands scope to make an operation succeed.
- Data preservation wins over automatic cleanup when evidence is uncertain.
- A failed operation does not authorize force-stop, destroy, or cleanup.
- The Hub cannot mark an executor refusal as success.

## Acceptance Gates

Before implementation:

1. Select the human authentication and secure Hub-session model.
2. Fix the local transport and prove workload Environments cannot reach it.
3. Define canonical schemas, size limits, cryptographic approval format, nonce
   storage, clock policy, and journal durability.
4. Map each operation to exact fixed effects and minimum host privileges.
5. Define independent verification APIs for every effect.
6. Threat-model the executor implementation and approval authority.
7. Test malformed requests, forged approvals, replay, expiry, stale plans,
   concurrency, crashes, journal corruption, and failures at every boundary.
8. Demonstrate that Hub compromise cannot become arbitrary host command
   execution through this protocol.

No acceptance gate authorizes a host service or privileged implementation.
