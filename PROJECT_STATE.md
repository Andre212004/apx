# APX Project State

This is the canonical continuity document for APX. Future work must read it
before proposing or making changes. Any change to the product objective,
development method, confirmed architecture, or accepted deviation must update
this file in the same change.

## Human Objective

APX should make one physical Arch Linux computer feel like a collection of
independent, disposable computers without presenting ordinary Linux user
management to the person using it.

Examples include separate Environments for university, individual subjects,
work, games, individual games, and unsafe development experiments. Installing
Steam in one games Environment must not make Steam visible in another
Environment. Installing two separate Steam copies in two Environments, with
different games and data, must be possible. A document created for university
must not appear in a games Environment. Deleting an Environment must remove its
local applications, data, configuration, processes, and state without branching
into or damaging another Environment.

APX is a platform and orchestration layer, not a separate operating system per
Environment. The host retains one Arch Linux installation and one kernel. The
technical mechanism that provides per-Environment applications and stronger
containment is not yet selected.

## Intended User Experience

The owner sees one human identity and a set of named APX Environments. APX may
use separate Linux accounts internally, but the normal interface must not show
the display manager's user chooser or require the owner to reason about those
accounts.

The intended flow is:

```text
Boot -> Hub -> selected Environment -> Hub
```

The machine enters the Hub directly through a future secure login or unlock
flow. From there the owner creates, configures, launches, archives, restores,
and deletes Environments. A future multi-person model may group Environments by
human identity, for example `andre` and `pai`; its authentication and ownership
model is deliberately deferred.

## Environment Product Contract

Each Environment is intended to behave like a complete logical computer:

- local applications and dependencies;
- local documents and application data;
- local configuration and session state;
- local processes and services;
- a selectable desktop or compositor, such as Hyprland, KDE Plasma, or GNOME;
- lifecycle operations that do not alter other Environments;
- isolation by default, with sharing only through a future explicit policy;
- optional creation from a reviewed template;
- optional local assistants enabled by policy.

Software installation is always scoped to the active Environment. Commands such
as `sudo pacman -S steam`, `yay -S ...`, `apt install ...`, Flatpak operations,
language package managers, vendor installers, and installation scripts must use
only that Environment's files, databases, and services. They must never install
into, upgrade, remove, or otherwise modify the host, APX base, Hub, or another
Environment. Host package management is not exposed through normal Environment
`sudo`.

Environments may inherit a reviewed, versioned APX base at creation. This base
contains common compatibility and presentation defaults without making the
Environments share mutable application or user data. Hardware drivers and
machine-wide network capability normally remain host responsibilities;
Environment-visible integration, fonts, certificates, desktop defaults, and
other safe baseline content may be supplied through the base after their exact
boundary is validated.

APX must support ordinary trusted workloads with strong separation. It should
also support a future higher-security profile for Environments used to run
untrusted code. The profile mechanism and its guarantees require a threat model
before implementation. APX must never describe user accounts or filesystem
permissions alone as VM-equivalent security.

## Hub Product Contract

The Hub is the minimal default APX Environment and the management surface. It
may contain APX management UI, system status, visual customization, and tightly
scoped widgets needed for that role. General-purpose browsers, editors, games,
development tools, and ordinary workload applications do not belong there.

Software cannot be installed interactively into workload Environments from the
Hub as an arbitrary privileged action. The Hub may select reviewed templates,
policies, and declared software sets during creation or configuration through a
future bounded APX management protocol.

The Hub is not an unrestricted administrator. Privileged lifecycle work belongs
to a small, typed, independently validating executor. The Hub must remain
destroyable and reproducible from its definition; its default role does not
justify bypassing Environment lifecycle or isolation rules.

The live Hub is not the parent filesystem or template for other Environments.
The Hub and workload Environments are separate products derived from the same
versioned APX base plus different role profiles. Hub-only management UI,
credentials, permissions, metadata, widgets, and state must never propagate to
a workload Environment. Conversely, an accidental change inside the Hub must
not silently change future Environments.

## Local Assistants

Odysseus is intended to provide a local personal assistant inside selected
Environments. Each instance is active only while its Environment is active and
may access only the Environments explicitly allowed through future Hub policy.
The initial model is total separation between assistant instances. Cross-
Environment communication and shared memory are deferred.

Selected development Environments may also include Codex as a coding and
debugging tool. Codex must be treated separately from personal-assistant data
and permissions. The Codex used to build APX today remains temporary development
tooling and is not evidence that this future integration has been designed.

## Confirmed Platform Boundaries

- one physical Arch Linux host;
- one host kernel;
- APX is the orchestration layer;
- separate internal Linux accounts remain the current identity and ownership
  foundation;
- one intended dedicated Btrfs home subvolume per Environment;
- local applications, data, configuration, and runtime state per Environment;
- only one normal graphical workload Environment active at a time;
- compositor- and desktop-independent lifecycle behavior;
- no visible ordinary Linux account chooser in the intended experience;
- templates are the intended reproducible starting point;
- a versioned common APX base may supply reviewed defaults to every role;
- no implicit cross-Environment data access;
- no Environment package-manager path to the host package database;
- no lifecycle exception that makes the Hub irreplaceable.

## Decisions Still Required

The following are product requirements but not yet technical decisions:

- per-Environment application mechanism: container/root filesystem, image,
  package overlay, or another design;
- which minimal packages remain in the host package database and which
  graphical/runtime components belong in each Environment's package database;
- isolation boundaries and threat model for normal and high-security profiles;
- namespace, cgroup, capability, seccomp, device, IPC, network, and GPU policy;
- exact Btrfs layout for homes, application layers, templates, snapshots,
  archives, and restoration;
- desktop/compositor packaging and launch model;
- secure automatic entry to the Hub without exposing internal accounts;
- session handoff and failure recovery;
- Hub-to-executor authorization protocol;
- template format, provenance, updates, and reproducibility;
- exact host/base/role-template boundary for drivers, firmware, networking,
  fonts, certificates, graphical integration, and defaults;
- multi-person identity, grouping, authentication, and ownership;
- Odysseus permission, memory, model, and lifecycle boundaries;
- Codex provisioning and separation from personal-assistant data.
- the exact Environment administrator policy: which local administrative
  operations are allowed and how local `sudo` is confined without creating a
  path to host administration.

## Provisional Isolation Direction

The first backend to validate is one bootable Arch system container per
Environment using `systemd-nspawn`, a versioned base, Btrfs-backed writable
state, user and network namespaces, reduced capabilities, explicit syscall and
device policy, cgroup limits, and verified teardown. This is a validation
direction, not an accepted implementation.

Podman/OCI remains a serious alternative or complementary runtime. Its rootless
model, image ecosystem, Quadlet integration, seccomp support, and standardized
CDI device injection are valuable, particularly for NVIDIA. A hardware VM may
be required for a future profile whose threat model includes hostile kernel
exploitation. The comparison, gates, and initial threat model are recorded in
`docs/isolation-architecture.md` and `docs/threat-model.md`.

## Provisional Lifecycle and Storage Direction

The repository now has a complete logical v1 proposal in
`docs/environment-lifecycle-and-storage-v1.md`. It separates immutable base and
role-template references from mutable root and home, ephemeral runtime,
immutable snapshot sets, and portable archives. It proposes generation-bound
registration and one write-ahead protocol for create, activate, stop, snapshot,
archive, restore, recovery, and destroy.

This is a review proposal, not confirmed or implemented architecture. Physical
Btrfs behavior is now mapped by a separate flat-subvolume and hierarchical-
qgroup proposal, and the lifecycle contract has passed repository-level review
against the normal and high-security threat objectives. Host topology,
disposable-fixture validation, backend identities, template artifact format,
executor authorization, and session handoff remain acceptance gates. These
proposals deliberately do not make the provisional `systemd-nspawn` backend a
hidden decision.

## Provisional Base and Role-Template Direction

The repository now proposes the safe starting-model system in
`docs/base-and-role-template-model-v1.md`. A minimal common base is separate
from readable role definitions, immutable built releases, and the independent
Environment created from them. Proposed families include Hub, Minimal,
University, Development, Games, and High Security, but no final package list or
release is approved by those names alone.

Templates never come from cloning a live Environment. They exclude personal
data, credentials, machine identity, assistant memory, operation records, and
Hub authority. A new release never silently changes an existing Environment.
V1 permits new creation from an admitted release; migration of an existing
Environment requires a later offline, reversible protocol.

This is a proposal, not an implemented catalogue or builder. Canonical schemas,
the isolated builder, artifact format, exact package manifests, reproducibility
evidence, sanitization fixtures, and per-release review remain required.

## Provisional Privileged Executor Direction

The repository now proposes a bounded Hub-to-executor protocol in
`docs/privileged-executor-protocol-v1.md`. In ordinary terms, the Hub may ask
for predefined APX actions but never receives a general administrator command
channel. The executor independently checks the current state, exact approved
plan, human approval strength, expiry, one-use nonce, operation journal, and
final result.

Routine launch and clean stop may use an unlocked APX session. Creation,
snapshots, archives, and restore require an explicit preview and confirmation.
Destroy, forced stop, and destructive recovery require fresh strong
confirmation and a plain-language explanation of possible data loss. A durable
write-ahead journal supports crash inspection; uncertain state preserves data.

This is a proposal, not an implemented privileged service. Human
authentication, secure Hub entry, final local transport, approval format,
minimal host privilege mapping, and failure-injection evidence remain required.

## Provisional Human Identity and Session Direction

The repository now proposes the complete visible single-owner flow in
`docs/human-identity-and-session-handoff-v1.md`. The person unlocks APX without
seeing internal Linux accounts, enters the Hub, selects an Environment, and can
return to a freshly activated Hub.

The Hub does not remain graphically active in the background. A minimal
host-owned broker provides only lock, transition, progress, and recovery while
APX stops one Environment, verifies teardown, and activates the next. If stop
cannot be proven, the next Environment does not open. If launch fails, the
broker offers bounded recovery without exposing a shell or turning a workload
into a temporary Hub.

APX cannot universally prove that every application saved its work. The
proposal therefore distinguishes ready, known blocker, and unknown safety;
unknown defaults to cancelling the switch. Force-stop requires fresh strong
confirmation. This is a proposal only: SDDM remains current, `greetd` remains a
candidate, and no broker, unlock, handoff, lock, or recovery flow exists.

## Provisional Environment-Local Administration Direction

The repository now proposes the local administration contract in
`docs/environment-local-administration-v1.md`. The owner may install software
and make system-level changes inside one Environment without receiving host
administrator authority. Local `sudo`, pacman, Flatpak, language managers, AUR
builds, vendor installers, hooks, services, and updates remain inside that
Environment's root, home, runtime, devices, network, and limits.

Local root is treated as a potentially hostile attacker, not a trusted safety
boundary. It must be unable to change the host, Hub, base, template, another
Environment, APX metadata, storage management, or outer resource policy. A bad
installer can still damage or expose its own Environment; APX offers honest
warnings and optional stopped-state restore points rather than claiming the
software is safe.

The owner-facing local-administrator confirmation must not copy a host password
or reusable approval into the Environment. Its exact mechanism, backend
enforcement, hostile-root denial tests, and package-manager experiments remain
unimplemented and required.

## Implemented Today

The repository contains documentation and a non-mutating Python prototype. It
implements read-only candidate, account, home, filesystem, Btrfs, registration,
session, process, removal-blocker, host-readiness, and Brave-isolation
inspection. It also implements deterministic dry-run creation and removal
planning, formal registration parsing, consistency classification, rollback
classification, a read-only Stage 0 system-container readiness observer, and
extensive tests. The repository now also contains a pure typed contract for an
immutable Arch Linux Archive base snapshot. It deterministically distinguishes
rejected structure, incomplete signature evidence, and fully verified fixture
evidence without downloading or installing packages. Its schema-v1 JSON
boundary rejects duplicate and unknown fields, wrong types, unsafe extensions,
oversized evidence, and excessive package counts, and supports deterministic
canonical round trips. The prototype also renders a fixed, non-executing
snapshot-acquisition plan and a review-only Stage 2 dossier with typed intended
resources, exact candidate paths and limits, gates, effects, failure states,
risks, rollback rules, destructive-operation separation, blockers, and stable
digests. A fixed `apx host snapshot-readiness` observer models read-only capture
of pacman/GnuPG versions, installed package identities, and regular-file
identity/hash evidence for the three fixed Arch keyring inputs; it accepts no
caller paths or packages and performs no trust mutation.

The documented lifecycle and storage proposal defines logical objects, stable
and transitional states, snapshot consistency, archive publication,
restore-to-new-identity, explicit destruction scope, and conservative
incomplete-operation recovery. None of that proposal is a mutating
implementation.

The repository also implements a pure, non-mutating Environment isolation-
policy contract in `src/apx_policy.py`. It provides exactly two fixed reviewed
profiles: `normal-desktop` and `high-security-headless`. It deterministically
rejects writable host binds, privileged mode, mapping Environment root to host
root, direct devices, lingering, missing required namespaces, incomplete
teardown requirements, policy drift, and false VM-equivalent claims. This is a
testable specification, not runtime enforcement or proof of containment.

The repository now also implements the pure Hub-to-executor contract in
`src/apx_executor_contract.py`. It exposes only the fixed create, activate,
stop, force-stop, snapshot, archive, restore, destroy, and recovery operation
families. Strict bounded parsing rejects unknown or duplicate fields, commands,
paths, malformed identities, and wrong types. Assessment binds the exact fixed
plan, consequences, Environment generation, active Hub session, approval
strength, five-minute maximum lifetime, one-use nonce state, and authoritative
current-state confirmation. It performs no authentication, nonce reservation,
host observation, or mutation.

The repository now implements the executor journal state machine in
`src/apx_executor_journal.py`. Before an effect may be reported as complete,
the journal must identify that exact next effect; completion requires fresh
final evidence. Every transition binds the preceding record, and strict
parsing rejects corruption, extensions, reordering, and malformed state.
Recovery permits automatic rollback only for clearly APX-owned, empty,
unpublished, and unused resources. Published, used, modified, foreign,
identity-uncertain, and effect-outcome-uncertain resources are preserved for
review. A repository-only fixture store exercises atomic replacement, stale-
writer rejection, restrictive file modes, and refusal to follow symbolic
links. This is durable test-fixture behaviour, not the future authoritative
host journal, authentication, replay reservation, or a mutating executor.

The staged route to user testing is documented in `docs/testing-strategy-v1.md`.
Repository contracts and fake evidence are tested first; one headless disposable
Environment, two-Environment attack tests, graphical features, and destructive
recovery each require later separate readiness evidence and explicit approval.

The read-only CLI now provides `apx host doctor`, a plain-language front door
to the fixed `isolation-trial` Stage 0 checks. It reports stop, wait, or ready
for review without executing any plan. Positive evidence observed without an
authoritative host channel remains unconfirmed, while any visible identity,
path, registration, or mandatory-tool conflict blocks progress immediately.
The command explicitly excludes the existing manually created `apx-trial`
candidate from reuse, modification, or deletion.

The repository now implements a pure trust-evidence seal in
`src/apx_trust_evidence.py`. It binds one bounded set of readiness checks to
the exact snapshot-acquisition plan, observation time, observer class, and any
preceding seal. Raw diagnostic output is not retained; each observation is
represented by a SHA-256 digest. Only complete evidence from the future
authoritative executor can become `verified`; restricted observations remain
pending and any failed requirement remains blocked. Strict canonical parsing
rejects unknown, duplicate, missing, wrongly typed, reordered-identity, or
tampered evidence. This does not create or persist a real host seal, download a
base, or provide executor attestation.

The fixed Stage 0 isolation observer now checks Btrfs quota accounting with the
read-only `btrfs quota status /home` operation. It requires traditional full
accounting, consistent state, and normal limit enforcement. The user separately
authorized and performed quota enablement and a complete rescan on 2026-07-12
for `/dev/nvme0n1p2`, which contains `/`, `/home`, `/var`, and `/.snapshots`.
The reported state is enabled, full qgroup accounting, not inconsistent, no
limit override, eight automatic level-0 qgroups, and no configured limits. APX
did not perform this host mutation. Custom hierarchy, limit assignment, bounded
enforcement testing, and quota recovery remain unimplemented.

Production Environment storage is confirmed to be elastic rather than
preallocated: an Environment using 10 GiB consumes approximately its actual
charged extents, while another may grow to 40 GiB without reserving that space
in advance. Safety still requires independently enforced per-Environment and
APX-pool ceilings plus a non-APX host reserve. Automatic growth is allowed only
while all capacity and quota-health gates remain satisfied. The Stage 2 trial's
8 GiB root and 2 GiB home limits are deliberately small experimental safety
bounds, not product defaults. Exact production reserve and fairness policy
remain to be measured and selected.

`src/apx_capacity.py` now implements the pure elastic-growth and Stage 2
capacity gates. Growth is not preallocated: a request is allowed only within
the independently supplied Environment headroom, APX-pool headroom, physical
free space after the host reserve, and healthy quota evidence. The disposable
Stage 2 experiment fixes a conservative 64 GiB host reserve, 16 GiB combined
operation headroom, and 2 GiB metadata margin. These are experimental safety
values, not production defaults. The current real host has sufficient reported
free space and healthy top-level quota mode, but the bounded enforcement
fixture and authoritative metadata-capacity evidence have not run, so the
capacity gate remains blocked.

The user then manually executed the separately authorized leaf quota fixture
documented in `docs/quota-enforcement-fixture-v1.md`. Qgroup `0/263` enforced a
64 MiB referenced limit: an attempted 80 MiB write stopped at 67,076,096 bytes
with `Disk quota exceeded` and a non-zero result. Quota accounting remained
full, consistent, and without limit override. The user separately approved and
completed cleanup. After a normal restart, subvolume ID `263` and qgroup
`0/263` disappeared, the automatic level-0 count returned from nine to eight,
and quotas remained healthy. This proves one leaf limit and eventual complete
cleanup, not the intended hierarchy, snapshots, concurrency, executor
recovery, or attestation; the complete capacity gate therefore remains blocked.

The repository now implements the pure parallel-installation contract in
`src/apx_installation.py` and documents it in
`docs/installation-migration-v1.md`. Installation beside the current KDE
session, APX cutover, and optional legacy cleanup are separate gates. Remote
project history, restore-tested personal backup, boot-tested recovery media,
headless and two-Environment isolation, graphical Hub/handoff, application
isolation, and destructive recovery are ordered evidence requirements. Even
complete evidence permits only a package-by-package cleanup review; it never
authorizes KDE removal. No installer or cleanup implementation exists.

`src/apx_stage2_gate.py` now implements the pure final conjunction gate for
the first bounded host experiment. It requires exact dossier and acquisition-
plan identity, verified snapshot and authoritative trust evidence, ready
capacity evidence, absent intended identities, verified parents and
subordinate IDs, verified quota hierarchy, captured host invariants, bounded
network approval, authenticated/unexpired/unused human approval, authoritative
journaling, and separate cleanup scope. No single positive can override a
missing gate. Complete evidence yields only eligibility for a separate Stage 2
execution approval and never includes graphical use, KDE removal, or cleanup.

`src/apx_acquisition.py` now implements the pure network/file boundary for the
fixed dated Arch base acquisition. It accepts only HTTPS at the exact Arch
Linux Archive origin and date, the reviewed repositories and architectures,
safe unique canonical filenames, and bounded file/aggregate sizes. Credentials,
ports, queries, fragments, redirects, traversal, unexpected repositories,
wrong ordering, duplicate files, incomplete transfers, symbolic links, and
hash/size/identity disagreement fail closed. It validates supplied manifests
and post-transfer evidence only; it performs no network or filesystem access.

`src/apx_staging.py` now implements a repository-only acquisition staging
fixture. It reserves one new operation directory in a caller-provided
disposable parent, binds it to the plan digest, uses restrictive modes and
no-follow opens, enforces file and aggregate bounds while streaming, verifies
exact size and SHA-256, and publishes without replacement only after durable
validation. Partial or mismatched bytes remain explicitly partial and are
never adopted. Existing state, symlinks, non-regular entries, changed modes or
plan binding, duplicate names, and unsafe filenames fail closed. It never
selects or writes a production host path and is not the authoritative store.

The repository now implements the pure complete-cleanup contract in
`src/apx_cleanup.py` and documents it in `docs/cleanup-completion-v1.md`.
Deletion offers `environment-only`, which preserves enumerated snapshots and
archives, or `complete-purge`, which includes every enumerated Environment
copy. Completion requires selected resources, account, registration, runtime,
mounts, open handles, network state, deleted-subvolume records, and qgroups to
be absent; quota state must remain consistent and protected neighbors
unchanged. `<under deletion>` and `<stale>` remain visible as `freeing-space`.
Identity reuse is forbidden until complete. Observed physical reclaim is
reported without claiming it must equal logical size. The Hub now supports a
read-only `cleaning` card and retains it until final evidence passes. No
destructive executor is implemented.

`src/apx_downloader.py` now implements a bounded streaming HTTPS transfer
contract with an injected non-redirecting opener and protected-byte sink. It
requires the exact archive host/date/path, a safe matching filename, status
200, unchanged final URI, one valid Content-Length, approved maximum and any
known exact size/hash. It closes and rejects redirects, early EOF, excess
bytes, malformed or non-byte responses, timeouts/open/read failures, digest
disagreement, and staging rejection. Tests use fake responses; the module does
not construct a network opener or perform a real download by itself.

`src/apx_http.py` now implements the fixed direct HTTPS opener for the Arch
Linux Archive. It disables environment proxies, cookies, and redirects; uses
the system CA trust with hostname verification and TLS 1.2 minimum; sends only
fixed non-secret GET headers; and rejects alternate schemes, hosts,
credentials, ports, query strings, fragments, changed final URI, invalid
timeouts, and sanitized connection/status failures. Tests inject responses;
no real acquisition has been performed.

The repository now composes bounded download and protected staging through
`src/apx_transfer.py`. `StreamingStagingWriter` writes chunks directly to one
exclusive partial regular file, enforces per-file and aggregate bounds during
the stream, and publishes without overwrite only after transfer and staging
size/hash evidence agree. Network or validation failure preserves the partial
identity and blocks blind retry. Integration tests use fake responses and
disposable directories; the composition does not select a production path.

`src/apx_database_acquisition.py` now implements the zero-argument fixed first
database acquisition: exactly dated `core.db` and `extra.db`, 64 MiB each and
128 MiB aggregate, into one new fixed `/tmp` root. The user separately
authorized and ran it on 2026-07-12. It transferred 8,818,209 bytes, published
exactly two mode-0600 regular files, and independent reopen/hash verification
matched both recorded SHA-256 values. Quotas stayed healthy; no installation,
extraction, execution, other download, or cleanup occurred. Exact evidence and
the preserved boundary are in `docs/database-acquisition-experiment-v1.md`.

`src/apx_repository_db.py` now strictly reopens staged Arch database archives
without extraction. It binds the regular-file SHA-256, bounds compressed and
expanded bytes and record counts, rejects traversal and unexpected archive
members, and validates unique safe package names/files, version, architecture,
sizes, SHA-256, base64 signature, and dependency fields. The two real staged
databases passed: 296 `core` and 14,842 `extra` package records. This validates
metadata structure only; it does not yet accept a resolved package closure.

The repository now implements a pure future-Hub view model in `src/apx_hub.py`.
It renders deterministic Environment and template cards, plain-language state,
warnings, and fixed request kinds from supplied evidence without reading or
changing the host. It enables normal actions only while one verified Hub is
active and the overall system is ready. Active, incomplete, unconfirmed,
duplicate, incompatible, or multi-active state fails closed. Delete requires
strong confirmation; unconfirmed state exposes only retry and read-only detail.
The complete visible flow is proposed in `docs/hub-experience-v1.md`; no
graphical application or functional lifecycle button exists.

The intended daily Hub interaction is now clarified: the owner uses a normal
Hyprland desktop with one APX taskbar control. Left-click expands about five
Environment choices directly upward; left-clicking one requests handoff.
Right-clicking a choice exposes its allowed management actions. Right-clicking
the APX control exposes create, archived Environments, and full management. The
full selected light management direction remains a secondary screen.

`prototypes/hub-demo` implements this interaction with in-memory demonstration
data, including create/delete confirmations and the full management screen. It
has browser-executed interaction tests and visual QA evidence, but no import of
APX host code, executor connection, Hyprland integration, persistence, or real
lifecycle effect.

Stage 0 has now been exercised on the real host without mutation. It confirmed
the fixed experimental identity is unused, `/home` is writable Btrfs with
capacity available, cgroup v2 and user namespaces are available, subordinate
IDs exist for `apx-development`, no systemd machine/image name collision was
found, and both AMD and NVIDIA hardware are present. The fixed Stage 2 headless
experiment plan is implemented but remains approval-blocked.

It does not create users or subvolumes, install isolated applications, launch or
switch Environments, write canonical registration, enforce isolation, manage
templates, run Odysseus, integrate Codex, or provide a Hub UI. Current manual
accounts have ordinary directories under the existing `@home` subvolume. SDDM
is the last confirmed display manager. The user-local Brave work is an
experiment, not an accepted application architecture.

## Development Method

1. Keep current observations, confirmed product intent, selected architecture,
   experiments, and open questions explicitly separate.
2. Translate the human objective into invariants and threat models before
   choosing mechanisms.
3. Prefer small reversible experiments with explicit backup, rollback, and
   acceptance criteria.
4. Treat restricted or sandbox-visible evidence as non-authoritative when host
   confirmation is required.
5. Specify typed operations, preconditions, postconditions, provenance, failure
   states, and recovery before adding privileged mutation.
6. Never expose an arbitrary privileged command channel through the Hub.
7. Test deterministic contracts and failure behavior before host experiments.
8. Do not modify the host from repository work without a separately reviewed
   milestone and explicit user approval.
9. Record conclusions from every experiment, including failed and inconclusive
   results.
10. Update this file whenever a goal, method, decision, or justified deviation
    changes.
11. Derive shared defaults from an explicit versioned base, never by cloning the
    live Hub or another mutable Environment.
12. Treat every package operation initiated inside an Environment as local to
    that Environment; host package changes require a separate host-level APX
    maintenance path and explicit authority.

## Deviation Policy

A deviation is acceptable when evidence shows that the current method cannot
meet the product contract safely, reliably, or maintainably. The same change
must record:

- the previous rule or assumption;
- the evidence that invalidated or limited it;
- the replacement decision;
- safety and compatibility consequences;
- migration or rollback implications;
- validation performed or still required.

The first recorded architectural correction is the application model. Earlier
documents assumed globally installed applications with only user data isolated.
The clarified product objective requires applications and their dependencies to
be local to each Environment. The technical replacement is intentionally open
until package, desktop, GPU, security, update, and storage experiments identify
a defensible mechanism.

The second clarification concerns common defaults. Total duplication is not a
product requirement: Environments may receive a shared baseline at creation.
For reliability and least privilege, the baseline is a declarative, versioned
artifact rather than the live Hub. This prevents Hub-only authority or mutable
state from leaking into workload Environments while still allowing consistent
hardware integration, fonts, networking support, and desktop defaults.

### Temporary Ollama Development Deviation

Until per-Environment application roots and services exist, the
`apx-development` account may temporarily use the already-present host Ollama
executable for Odysseus development. This is a development convenience, not an
accepted APX application-isolation mechanism or evidence that Ollama is local
to the Environment.

The previous rule remains the product requirement: the executable,
dependencies, service, configuration, models, and mutable state must eventually
belong to one Environment. Current evidence shows a host Ollama client at
`/usr/local/bin/ollama` and no implemented Environment package or service
boundary. A manual `apx-development` process successfully served the
user-selected model directory and Odysseus reached it through
`host.containers.internal:11434` only while Ollama listened on `0.0.0.0:11434`.
Closing the terminal stopped the process and produced an expected unavailable
response until it was restarted. This validates a lifecycle signal, not a
genuinely local installation or safe final network boundary.

The temporary replacement is deliberately narrow:

- do not install, update, or remove the host Ollama package or executable;
- do not create or enable a host system service;
- run Ollama manually as `apx-development` only when needed;
- select an explicit model directory owned by `apx-development` rather than a
  shared model directory;
- keep Odysseus configuration and mutable model state in the Development
  Environment account;
- do not describe Unix-account ownership as process, package, or GPU isolation.

This deviation shares the host executable, kernel, GPU devices, and any
executable-level vulnerability with the host. It does not prevent another
authorized host account from using the global executable, and its resource use
is not yet contained by an APX cgroup policy. Rollback is to stop the manually
started process and remove only the explicitly selected user-owned model state.
No host package rollback is part of this deviation because it authorizes no
host package change.

The selected model directory, manual start/stop behavior, listening-address
dependency, and a successful Odysseus request were exercised. Binding to
`0.0.0.0` may expose an unauthenticated API beyond the intended Environment and
is unacceptable as the final design. Disk/GPU resource behavior, private
Environment networking, readiness, authenticated management, crash recovery,
and teardown still require validation. The deviation must be retired when the
selected Environment backend can own Ollama and its service.

## Next Milestone

The package names, storage identities, resource limits, rollback boundary, and
snapshot evidence contract for Stage 2 are fixed in
`docs/base-and-storage-v1.md`. A dated 2026-07-11 acquisition candidate with
fixed derived source, staging/evidence paths, limits, phases, blockers, and
digest is ready for review. The trust mechanism is selected: explicitly freeze
the trusted host's installed `archlinux-keyring`, use it to authenticate a
matching isolated keyring archive, use pacman for fixed-path resolution and
download-only acquisition, `pacman-key` for primary detached verification, and
GnuPG for the reopened-file second pass. The next external-effect milestone is
to authenticate the matching keyring archive, approve bounded acquisition,
produce the real artifact, and verify every package signature and digest. Stage
2 creation remains a later separate approval. It must preserve these cases:

The acquisition phases, trust boundary, staging rules, independent validation,
publication semantics, failure classes, and remaining approval inputs are
specified in `docs/base-snapshot-acquisition-v1.md`. Exact intended Stage 2
resources, effects, gates, risks, rollback, destructive separation, and
blockers are summarized in `docs/stage2-approval-dossier.md`. Neither procedure
is authorized to run. Matching archive authentication, real signatures,
authoritative quota/capacity evidence, approval protocol, future executor
attestation, and separate human approvals remain unresolved.

The trust/tool identity observer was executed through an explicitly authorized
host context. It observed `archlinux-keyring 20260707.1-1`, pacman
`7.1.0.r9.g54d9411-2`, pacman-key `7.1.0`, GnuPG `2.4.9-1`, 17 keyring package
files with zero altered files, and the three fixed keyring hashes now frozen in
the acquisition plan. The CLI conservatively reported
`requires-host-confirmation` because the prototype has no privileged attestation
channel. The evidence closes the unknown version/file/hash inputs for planning,
but executor attestation and approval for the complete base acquisition remain
blockers.

A separately approved keyring-only acquisition then downloaded
`archlinux-keyring-20260707.1-1-any.pkg.tar.zst` and its detached signature into
operation-owned `/tmp` staging. The package SHA-256 is
`b47fc9c8066377e73d72bdb6a166bbbd829d5dcc745e424ef32436bd673cbc0d`;
pacman-key reported a full-trust good signature by fingerprint
`0429897DE5F3BDAC537A30696D42BDD116E0068F`. Direct use of the distributed
`archlinux.gpg` with gpg/gpgv failed due to its format. Exporting only the
trusted signer public key allowed a successful independent gpgv pass; the
exported key hash is
`0fcc071d58801d83e29a68f0ac0008c142f675cdfd8d8b7a27362ac1ec578470`.
Read-only metadata matched package name, version, architecture, and packager.
No package was installed. This closes the matching keyring archive blocker but
does not authorize or complete base acquisition.

The current Arch repositories have been resolved non-mutatingly to 138 packages
with recorded database and manifest digests. This is not yet an accepted
snapshot: every package and its signature must be downloaded and verified
before base creation. The implemented contract does not make this observed
resolution acceptable and authorizes no download or host mutation.

- two Environments independently installing the same application;
- deletion without residual application or user data;
- desktop operation under Hyprland, KDE Plasma, and GNOME;
- GPU, audio, input, portals, notifications, secrets, and removable devices;
- normal and high-security profiles;
- updates, rollback, templates, snapshots, backup, and recovery;
- reproducible common-base updates without mutable cross-Environment state;
- Odysseus limited to one active Environment;
- no ordinary Linux user chooser during boot or switching.

No container creation, package change, Btrfs mutation, or privileged operation
is authorized merely by the plan. The first host mutation requires a fresh
review of the exact base source, disk budget, created resources, backup,
rollback, and approval request.
