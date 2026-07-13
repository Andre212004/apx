# Roadmap

This roadmap is documentation-first. `PROJECT_STATE.md` is the canonical source
for product intent, method, deviations, and the immediate milestone.

## Accepted Delivery Order

The primary first-install path is now CLI-first on a fresh minimal Arch host:

```text
headless bootstrap -> headless Hub CLI -> headless Development
  -> lifecycle/isolation/storage/recovery -> H0 Hyprland
  -> graphical controls -> optional graphical Hub
```

The full C0–C9 ladder is maintained in
`headless-bootstrap-and-cli-first-v1.md`. Git/Codex/source/build tools belong in
Development, never Hub. A Git checkout is not run as an unrestricted privileged
installer. Existing KDE/SDDM migration and G2 remain a secondary compatibility
campaign and no longer block the clean headless path.

Development-to-Hub delivery is a promotion pipeline, not cross-Environment
editing: an untrusted candidate crosses a bounded import into host-owned
quarantine, passes independent verification and separate catalogue admission,
then the executor reconstructs and verifies a replacement Hub while retaining
the previous generation for rollback. The logical contract is in
`development-to-hub-release-promotion-v1.md`; its physical mechanisms remain
open.

The first clean-install foundation now selects the bounded C1–C6 experiment:
x86_64 UEFI, one target disk, LUKS2/Btrfs, systemd-boot, a closed minimal Arch
package-name manifest, text-only broker session, password owner authentication,
a signed APX Arch package, and `systemd-nspawn` with mandatory private users and
no graphical/device grants. Exact target evidence and trust keys still block a
real installation.

The first pure contracts now parse a closed headless-Hub candidate, build a
non-mutating quarantine import plan, parse clean-install target/supply evidence,
and build a dossier that can reach only `ready-for-separate-approval`. The
future CLI vocabulary is fixed, but import, catalogue, installer, executor
effects, trust keys, and disposable installation remain absent.

The repository now also contains in-memory exact-transition stores for release
promotion and the full ten-stage clean-install journal. They prove approval
separation, ordered effects, stale-writer and forged-jump refusal, and
preserve-on-uncertainty recovery. They do not perform physical import,
catalogue publication, disk changes, or installation.

The internal Hub/base release tree now has a closed pure member-manifest and
reproducibility contract. It binds the candidate to exact canonical metadata,
content digests, and compressed artefact identity while rejecting unsafe or
mutable content. A raw archive reader, package build, signatures, and physical
admission remain absent.

The first unsigned package rehearsal is also closed at the definition/evidence
level as `apx-contracts-development`. It contains only three non-mutating
validators and four contract documents, exposes no APX command or service, and
can never become trusted merely by building successfully. Apache-2.0 is now the
project licence; actual package bytes wait for a clean frozen source revision.

The offline root/release-signer custody and ceremony boundary is documented,
including separated backups, proven restoration, independent verification,
rotation, revocation, and compromise handling. It deliberately does not choose
or generate production keys: the exact cryptographic/tool profile and a real
physical offline rehearsal remain gates.

The repository-side disposable C0–C6 rehearsal is now fixed: UEFI VM envelope,
no-host-share boundary, evidence/checkpoint rules, interruption injection,
Hub/Development/package-locality/lifecycle tests, and stop conditions. It is not
yet executable because the hypervisor/ISO, functional bootstrap, production
trust, effect adapters, and VM-bound dossier are absent.

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
- validate the headless backend first, then desktop operation with Hyprland,
  KDE Plasma, and GNOME;
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

The separate `hyprland-g2-exclusive-session-design-v1.md` records the physical
hand-off safety boundary and the current blockers for a G2 preview, but it does
not authorize a device, session, or host effect yet.

The companion `hyprland-g2-broker-recovery-boundary-v1.md` now selects a
two-VT, host-owned recovery direction and revocable exact device leases for G2
only. The controller, SDDM quiescence, device mediator, fixtures, and physical
rehearsal remain gates before any executable preview.

The separate `hyprland-g2-kde-release-proof-v1.md` now selects the independent
release conjunction and two-pass stability rule. Installed-version KDE/SDDM
operations, host observation mechanisms, evaluator fixtures, and a read-only
preview remain required.

The first read-only current-host observation found two live KDE session
generations on the physical seat and showed that ordinary DRM descriptor scans
cannot alone prove KMS release. The observer must therefore cover both sessions
and a second authoritative DRM ownership mechanism before G2 execution.

The logical G2 observer schema now closes the evidence record and pair-evaluator
contract. Exact source adapters, minimal privileges, evaluator fixtures, and a
fresh post-reboot read-only preview remain gates.

The source-adapter proposal now fixes the logical API/authority mapping and
first bounded limits. Implementation, installed-version fixtures, and the fresh
preview remain gates; observation failure never widens privilege.

For the primary clean-install path, H0 replaces G2 as the first graphical gate.
H0 begins with no display manager or graphical owner and retains the independent
text recovery surface. It reuses G2 device/readiness/teardown lessons without
requiring KDE logout or SDDM quiescence.

The proposed `environment-local-administration-v1.md` now defines how local
`sudo`, package managers, installers, services, updates, devices, limits, and
recovery remain confined to one Environment. Its confirmation mechanism and
backend enforcement still require design experiments.

## Phase 4: Minimal Mutating Prototype

Status: pure executor, journal, and isolation contracts started; no mutating
executor.

Goals:

- implement the smallest independently validating privileged executor;
- expose the smallest typed `apx` CLI before any graphical client;
- create one disposable headless Environment using the selected models;
- verify every postcondition using fresh authoritative evidence;
- exercise failure injection, incomplete-operation recovery, and bounded
  rollback;
- avoid an arbitrary command, path, package, or privilege interface.

The repository now models the fixed executor operation catalogue, deterministic
plans, strict bounded request parsing, consequence-bound approvals, expiry,
active-session binding, generation freshness, nonce state, and authoritative-
state requirement. It also models the durable journal sequence, strict journal
parsing, conservative recovery classification, and atomic disposable-fixture
writes. `testing-strategy-v1.md` defines the staged route from these safe
repository tests to a later explicitly approved host experiment.

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

Status: pure interface-state model, product flow, and browser-based visual demo
implemented; real Hyprland/graphical app not started.

Priority: after the headless Hub CLI, Development Environment, C0–C6 lifecycle
and recovery gates, and H0 first graphical Environment pass. The graphical Hub
is optional; it must remain a client of the CLI protocol rather than replacing
the independently usable command/recovery path.

Possible scope:

- Environment library and launcher;
- creation, template, archive, restore, and deletion workflows;
- global system summaries and tightly scoped widgets;
- visual customization;
- policy controls for local assistants;
- no general-purpose workload or development software.

The Hub remains reproducible and destroyable. Its role and constrained
permissions do not make it an architectural exception.

`src/apx_hub.py` now produces deterministic Environment/template cards,
plain-language state, warnings, fixed request kinds, and fail-closed button
availability without observing or changing the host. `hub-experience-v1.md`
defines creation, open, recovery-point, archive, restore, delete, progress,
failure, accessibility, and future graphical-prototype flows.

`prototypes/hub-demo` validates the selected light management screen plus the
clarified daily taskbar interaction: left-click APX expands five Environment
choices, right-click APX opens create/archive/full management, and right-click
an Environment opens state-bounded actions. It is demo-only and has no executor
or host connection.

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
- The accepted clean-install order is headless and CLI-first, but no clean APX
  bootstrap or mutating CLI exists.
- The user-local Brave experiment is evidence, not the selected application
  architecture.
