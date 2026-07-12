# APX

APX is a personal operating environment platform built on top of Arch Linux.

APX does not replace Linux. The host remains a single Arch Linux installation
with one kernel. APX adds an orchestration layer that makes the computer behave
like a collection of isolated, disposable personal Environments.

## What APX Is

APX is an architecture for managing multiple isolated personal Environments on one Arch Linux host.

Each Environment is intended to provide a separate personal workspace with its own Linux identity, home data, configuration, graphical session, processes, and APX metadata.

In the intended product, applications, dependencies, data, configuration, and
runtime state belong to an Environment. Installing an application in one
Environment must not expose it in another. The mechanism that provides this
while retaining one host kernel is still under architectural evaluation.

Isolation does not require duplicating every safe default. The Hub and workload
Environments may be built from a reviewed, versioned APX base that supplies
common integration and presentation defaults. The live Hub is never cloned:
Hub-only authority and mutable state must not enter other Environments.

Package installation follows the same boundary. Running, for example,
`sudo pacman -S steam` inside a games Environment installs Steam only there.
The command must not change the host, Hub, base, or another Environment.

## What APX Is Not

APX is not:

- a Linux distribution
- a replacement operating system
- necessarily a virtual-machine platform with a separate kernel per Environment
- a virtual machine manager
- a second package manager
- a replacement desktop shell
- a development workspace inside the Hub

These boundaries keep APX focused on orchestration rather than duplicating operating system responsibilities.

## Single-Arch Architecture

An APX system has:

- one Arch Linux installation
- one kernel
- the minimal host facilities required to start and manage Environments
- Environment-local workload applications and dependencies

APX does not create a separate kernel per Environment. The host remains the
authority for kernel updates, hardware integration, and global services. The
boundary for packages, compositors, and desktop components is under evaluation.

## Environments

An APX Environment is represented by:

- one Linux user
- one intended Btrfs home subvolume
- one independent graphical login session
- independent configuration
- user-owned processes separated by Linux user ownership
- independent metadata

Separate Linux users remain an internal identity and ownership boundary. The
person using APX sees one human identity and named Environments rather than an
ordinary Linux user chooser. Users and filesystem permissions alone are not a
VM-equivalent security boundary; stronger containment remains to be designed.

Current manually created users still have ordinary homes under the existing `@home` subvolume. Dedicated Btrfs home subvolumes are the intended APX architecture, not the current implemented state.

## Hub

The Hub is the default APX Environment and the management entry point.

The Hub's planned responsibility is to provide APX operations such as listing, creating, archiving, restoring, snapshotting, templating, and launching Environments.

The Hub is not a general-purpose desktop or a development workspace. It may
contain APX management UI, system summaries, visual customization, and tightly
scoped widgets. Browsers, ordinary editors, games, source repositories, IDEs,
build tools, and workload applications belong in dedicated Environments.

The Hub must be destroyable and recreatable like every other Environment. No APX implementation decision may require a unique lifecycle exception for the Hub.

## Btrfs

Btrfs is the intended storage foundation for Environment homes.

The target model is one dedicated home subvolume per Environment. This should support snapshots, archival, restoration, and templates.

The logical storage objects and lifecycle state machine now have a complete v1
proposal. The physical subvolume layout, mount topology, and qgroup hierarchy
are not selected or implemented and must be validated before implementation.

## Graphical Environment

APX is intended to support Hyprland, KDE Plasma, GNOME, and other viable desktop
or compositor choices. No one graphical environment may define APX lifecycle
semantics.

Environment separation must cover applications, dependencies, home data,
configuration, processes, services, and login sessions. APX lifecycle behavior
must remain independent of desktop-specific autostart or APIs.

Only one graphical Environment should run at a time in the intended session model.

## Current Development Status

APX is in the documentation and architecture foundation phase.

This repository contains architecture documentation and a read-only inspection and creation-planning prototype. No privileged creation or mutating APX runtime exists. Development currently takes place in the Development Environment named `apx-development`. Codex is a temporary development tool and is not part of APX.

`apx host check` performs a read-only readiness inspection for the proposed first experimental Environment, `trial`. It reports identity, storage, graphical-session, and account-policy evidence independently, marks sandbox-visible evidence as requiring authoritative host confirmation, and emits a deterministic non-executing manual plan. It does not create or modify host resources.

`apx host doctor` gives a short plain-language safety result for the newer
headless isolation experiment. It says stop, wait, or ready for review; it does
not execute the experiment. It uses the fresh `apx-isolation-trial` identity
and explicitly refuses to reuse, change, or delete the older manually created
`apx-trial` candidate.

`apx host validate` performs the read-only Milestone 3A practical inspection. It summarizes the three fixed APX accounts, removal-blocker evidence, Brave installation and per-user data state, and factual session-switching prerequisites. It does not remove or change host resources and does not claim deletion safety.

`apx environment removal-plan <name>` produces a read-only, non-executing plan with explicit blockers, unknown evidence, data-loss scope, privilege boundaries, irreversibility, and post-removal validation. The Hub returns a protected result and no removal plan.

`apx host brave-isolation` reports current Brave installation and visibility, per-user data evidence, available isolation approaches, and a non-executing first-experiment recommendation with backup, rollback, and approval requirements.

`apx host isolation-readiness` performs the read-only Stage 0 inspection for the
provisional system-container experiment. It checks the fixed experimental
identity, required and optional tooling, kernel/systemd context, cgroup and user
namespace evidence, machine collisions, and `/home` storage capacity. It never
creates an image or container and treats restricted-context positives as
requiring authoritative host confirmation. Disabled Btrfs quota accounting is
reported as a hard blocker rather than a positive that merely needs review.

`apx host isolation-plan` renders the fixed, non-executing first headless
system-container plan. It contains no commands or caller-selected paths and
remains blocked until a separately approved host experiment.

`apx host snapshot-plan` renders the fixed, non-executing dated-archive
acquisition candidate, trust gaps, resource limits, phases, blockers, and plan
digest. It performs no network or filesystem operation.

`apx host snapshot-readiness` performs a fixed read-only observation of the
pacman/GnuPG tools, installed package identities, and regular-file identities
and hashes of the Arch keyring inputs. It accepts no paths or package names and
does not download, refresh, import, sign, or mutate trust state.

`apx host stage2-dossier` renders the fixed review-only Stage 2 resource and
approval package, including downloads, host effects, gates, risks, failures,
rollback rules, destructive-operation separation, blockers, and dossier digest.

The first approved extracted-build experiment and its unresolved validation
results are recorded in
[docs/brave-user-local-experiment.md](docs/brave-user-local-experiment.md).

SDDM remains the last confirmed current display manager. The future compositor-independent session-management direction is documented in [docs/session-management.md](docs/session-management.md). No display-manager replacement has been adopted or implemented.

No package installation, system configuration, user creation, Btrfs changes, display-manager changes, or service changes should be performed from this repository at this stage.

## Repository Structure

```text
.
├── AGENTS.md
├── PROJECT_STATE.md
├── docs/
│   ├── architecture.md
│   ├── base-and-storage-v1.md
│   ├── base-and-role-template-model-v1.md
│   ├── base-snapshot-acquisition-v1.md
│   ├── btrfs-storage-layout-v1.md
│   ├── brave-user-local-experiment.md
│   ├── development-principles.md
│   ├── environment-lifecycle-and-storage-v1.md
│   ├── environment-local-administration-v1.md
│   ├── human-identity-and-session-handoff-v1.md
│   ├── hub-experience-v1.md
│   ├── installation-migration-v1.md
│   ├── isolation-architecture.md
│   ├── lifecycle-threat-model-review-v1.md
│   ├── privileged-executor-protocol-v1.md
│   ├── quota-enforcement-fixture-v1.md
│   ├── roadmap.md
│   ├── session-management.md
│   ├── stage2-approval-dossier.md
│   ├── system-container-experiment.md
│   ├── testing-strategy-v1.md
│   └── threat-model.md
├── src/
│   ├── apx_cli.py
│   ├── apx_acquisition.py
│   ├── apx_capacity.py
│   ├── apx_consistency.py
│   ├── apx_executor_contract.py
│   ├── apx_executor_journal.py
│   ├── apx_host.py
│   ├── apx_hub.py
│   ├── apx_installation.py
│   ├── apx_policy.py
│   ├── apx_stage2_gate.py
│   ├── apx_staging.py
│   ├── apx_trust_evidence.py
│   ├── apx_environment.py
│   └── apx_registration.py
├── tests/
├── prototypes/
│   └── hub-demo/
├── .gitignore
├── apx
└── README.md
```

## Design Principles

- simplicity over complexity
- architecture before implementation
- no unnecessary abstractions
- no exceptions for the Hub
- Environment-local applications, dependencies, data, and state
- one human-facing identity over hidden internal accounts
- professional documentation
- clean repository history
- long-term maintainability

## Documentation

Start with [docs/architecture.md](docs/architecture.md). The proposed storage
and lifecycle contract is in
[docs/environment-lifecycle-and-storage-v1.md](docs/environment-lifecycle-and-storage-v1.md).
Its security review and proposed physical mapping are in
[docs/lifecycle-threat-model-review-v1.md](docs/lifecycle-threat-model-review-v1.md)
and [docs/btrfs-storage-layout-v1.md](docs/btrfs-storage-layout-v1.md).
The proposed safety boundary between the Hub and future system-changing actions
is documented in
[docs/privileged-executor-protocol-v1.md](docs/privileged-executor-protocol-v1.md).
The proposed owner unlock, Environment switching, and recovery experience is in
[docs/human-identity-and-session-handoff-v1.md](docs/human-identity-and-session-handoff-v1.md).
The proposed safe starting models for Hub, Games, University, Development, and
other Environment roles are defined in
[docs/base-and-role-template-model-v1.md](docs/base-and-role-template-model-v1.md).
The proposed rules allowing software installation and administration inside one
Environment without administering the host are in
[docs/environment-local-administration-v1.md](docs/environment-local-administration-v1.md).
The staged path from safe repository tests to later user-visible experiments is
in [docs/testing-strategy-v1.md](docs/testing-strategy-v1.md).
The future Hub screens and the currently implemented pure button/card rules are
described in [docs/hub-experience-v1.md](docs/hub-experience-v1.md).
The dependency-free interactive visual demo is in
[prototypes/hub-demo](prototypes/hub-demo/README.md). It uses only temporary
in-memory data and cannot alter APX or the host.
