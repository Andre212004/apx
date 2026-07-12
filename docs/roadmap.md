# Roadmap

This roadmap is documentation-first. `PROJECT_STATE.md` is the canonical source
for product intent, method, deviations, and the immediate milestone.

## Phase 0: Repository and Contract Foundation

Status: substantially complete.

Delivered:

- architecture, session, and development-principle documents;
- Environment naming, identity, registration, creation, consistency, and
  rollback contracts;
- read-only account, home, filesystem, Btrfs, registration, session, process,
  and host observations;
- deterministic creation and removal plans that cannot apply changes;
- practical host and Brave-isolation reports;
- automated tests for the current non-mutating prototype.

Ongoing requirement: retain clear separation between implemented behavior and
intended design as the architecture evolves.

## Phase 1: Isolation Architecture Decision

Status: provisional direction documented; experimental validation pending.

Goals:

- create a threat model for normal and high-security Environments;
- compare per-Environment root filesystem, container, image, overlay, package,
  namespace, and related approaches;
- define host versus Environment package boundaries;
- define the host, common APX base, role-template, and mutable Environment
  boundaries;
- validate desktop operation with Hyprland, KDE Plasma, and GNOME;
- specify GPU, audio, input, portals, notifications, secrets, storage, devices,
  IPC, network, capabilities, seccomp, and cgroup policies;
- prove that duplicate independent application installations and clean deletion
  are possible;
- select a direction with explicit tradeoffs and rollback.

No mutating lifecycle executor should be implemented before this phase produces
an accepted architecture decision.

Current provisional candidate: bootable Arch system containers with
`systemd-nspawn`, Btrfs-backed state, user/network namespaces, explicit device
policy, and verified teardown. Podman/OCI remains an alternative or
complementary runtime. The staged experiment and approval boundaries are defined
in `system-container-experiment.md`. See also `isolation-architecture.md` and
`threat-model.md`.

Stage 0 read-only host readiness has been implemented and exercised. The fixed
headless plan, dated snapshot-acquisition candidate, typed Stage 2 resources,
and review dossier are implemented as non-mutating models. They remain blocked
pending authoritative trust/tool identity capture, real signed snapshot evidence,
authoritative capacity/quota evidence, executor authorization design, and
explicit approvals for acquisition, creation, and cleanup.

Two fixed pure policy contracts now make the normal-desktop and high-security-
headless boundaries testable without changing the host. They fail closed when
host access, broad privilege, direct devices, lingering, required namespaces,
teardown checks, or security claims differ from the reviewed contract. Runtime
enforcement and hostile-workload evidence remain pending.

## Phase 2: Storage, Template, and Lifecycle Model

Status: repository-level v1 proposal documented; review and backend validation
pending.

Goals:

- define Btrfs layout for homes, application layers, templates, snapshots, and
  archives;
- define template format, provenance, updates, and reproducibility;
- prove that base updates cannot propagate Hub-only authority or mutable state;
- define create, activate, stop, snapshot, archive, restore, and destroy state
  transitions;
- define incomplete-operation recovery and deletion provenance;
- revise registration metadata only after these identities are known;
- specify non-destructive validation, backup, and rollback scenarios.

The logical object model, state machine, operation protocol, snapshot/archive/
restore semantics, incomplete-operation recovery, and destruction boundary are
proposed in `environment-lifecycle-and-storage-v1.md`. A repository-level
threat-model review and a flat-subvolume, hierarchical-qgroup physical proposal
now exist. The role-template definition, immutable release, catalogue,
sanitization, reproducibility, and update model is also proposed. Host topology
confirmation, disposable-fixture validation, canonical schemas,
builder/artifact selection, reproducibility evidence, and the runtime backend
remain acceptance gates, so this phase is not complete and mutation remains
blocked.

## Phase 3: Human Identity, Sessions, and Privileges

Status: executor, single-owner identity, and session-handoff protocols proposed;
implementation choices and validation remain open.

Goals:

- enter or securely unlock the Hub without exposing a Linux user chooser;
- implement the conceptual `Boot -> Hub -> Environment -> Hub` flow;
- hide internal Linux accounts behind one human-facing identity;
- define session failure recovery and handling of unsaved work;
- define the minimal typed Hub-to-executor authorization protocol;
- validate compositor-independent behavior;
- design future multi-person Environment grouping without weakening isolation.

The proposed `privileged-executor-protocol-v1.md` defines the bounded Hub
request, approval strengths, replay protection, durable journal, crash
recovery, concurrency, minimal privilege, verification, and user-facing
consequence rules. It deliberately leaves the final authentication technology
and session transport to this phase, so Phase 3 remains incomplete.

The proposed `human-identity-and-session-handoff-v1.md` now defines the visible
owner identity, locked boot, host transition/recovery surface, one graphical
Environment at a time, Hub-to-workload and return flows, honest unsaved-work
handling, desktop adapters, locking, power actions, and Hub-failure recovery.
Authentication technology, broker/display-manager selection, and experiments
remain unresolved.

The proposed `environment-local-administration-v1.md` now defines how local
`sudo`, package managers, installers, services, updates, devices, limits, and
recovery remain confined to one Environment. Its confirmation mechanism and
backend enforcement still require design experiments.

## Phase 4: Minimal Mutating Prototype

Status: pure executor and isolation contracts started; no mutating executor.

Goals:

- implement the smallest independently validating privileged executor;
- create one disposable experimental Environment using the selected models;
- verify every postcondition using fresh authoritative evidence;
- exercise failure injection, incomplete-operation recovery, and bounded
  rollback;
- avoid an arbitrary command, path, package, or privilege interface.

The repository now models the fixed executor operation catalogue, deterministic
plans, strict bounded request parsing, consequence-bound approvals, expiry,
active-session binding, generation freshness, nonce state, and authoritative-
state requirement. `testing-strategy-v1.md` defines the staged route from these
safe repository tests to a later explicitly approved host experiment.

## Phase 5: Environment Lifecycle

Status: not started.

Possible scope:

- list and inspect;
- create from templates;
- launch and return to Hub;
- stop safely;
- snapshot;
- archive and restore;
- destroy with explicit data-loss scope;
- configure normal or high-security isolation policy.

## Phase 6: Hub Experience

Status: not started.

Possible scope:

- Environment library and launcher;
- creation, template, archive, restore, and deletion workflows;
- global system summaries and tightly scoped widgets;
- visual customization;
- policy controls for local assistants;
- no general-purpose workload or development software.

The Hub remains reproducible and destroyable. Its role and constrained
permissions do not make it an architectural exception.

## Phase 7: Local Assistants

Status: not started.

Goals:

- run Odysseus only while its selected Environment is active;
- confine its files, memory, model access, tools, and network according to
  explicit policy;
- keep assistant instances isolated initially;
- optionally provision Codex in selected development Environments;
- keep Codex coding access separate from personal-assistant data;
- defer cross-Environment assistant communication until a separate threat model
  and consent design exist.

## Current Factual State

- The repository has a functional read-only planning and inspection prototype,
  but no mutating APX runtime.
- Development takes place in `apx-development`.
- SDDM is the last confirmed display manager.
- Current manually created users have ordinary homes beneath the existing
  `@home` subvolume.
- Environment-local software, stronger process isolation, templates, session
  handoff, the Hub UI, Odysseus integration, and Codex provisioning are not
  implemented.
- The user-local Brave experiment is evidence, not the selected application
  architecture.
