# APX Architecture

APX is a personal operating environment platform built on top of Arch Linux.

The operating system remains Linux. APX is an orchestration layer that manages isolated personal environments on a single Arch Linux installation.

## Current System

No functional APX implementation currently exists. Existing manually created users do not yet represent the intended APX storage model. Their homes remain ordinary directories under the existing `@home` subvolume rather than dedicated Btrfs home subvolumes.

Development currently takes place in the Development Environment named `apx-development`. SDDM currently manages graphical sessions. Codex is a temporary development tool and is not part of APX.

## Non-Goals

APX is not:

- a Linux distribution
- a replacement operating system
- a container runtime
- a virtual machine manager
- a second package manager
- a replacement desktop shell
- a development environment inside the Hub

These boundaries matter because APX should stay simple, predictable, and maintainable.

## Host System

An APX system has exactly one host Arch Linux installation.

The host owns:

- one kernel
- one package database
- one KDE Plasma installation
- global system services
- globally installed applications

APX does not duplicate these resources per Environment.

## Shared Applications, Isolated Data

Applications are shared globally through the Arch package database.

The intended Environment isolation applies to:

- user home data
- configuration
- session state
- user-owned processes
- APX metadata

This avoids duplicating applications while preserving independent personal workspaces.

## Environments

An Environment is the primary APX unit.

The intended Environment model maps each Environment to:

- one Linux user
- one dedicated Btrfs home subvolume
- one independent KDE session
- independent configuration
- user-owned processes separated by Linux user ownership
- independent metadata

The Linux user boundary provides ownership and process separation. The Btrfs subvolume provides storage structure, snapshot support, and lifecycle management. The KDE session provides an independent interactive workspace.

### Linux User

The Linux user is the primary identity boundary.

It defines:

- file ownership
- process ownership
- user-level permissions
- home directory ownership
- session identity

APX should avoid creating hidden alternate identity systems when Linux users already provide the required primitive.

### Btrfs Home Subvolume

The intended architecture is one Btrfs home subvolume per Environment.

The subvolume provides a clear storage boundary and supports lifecycle operations such as snapshots, archival, restoration, and templates.

Current manually created users still have ordinary homes under the existing `@home` subvolume. The exact APX subvolume layout must be documented and validated before implementation.

### KDE Session

Each Environment is intended to have its own independent KDE Plasma session.

KDE Plasma is shared at the system level, but user configuration, session state, and user-level services are separate per Environment.

### Processes

Processes belong to the Environment user that launched them.

APX should treat process ownership as part of the Environment boundary. Lifecycle operations that stop, archive, restore, or switch Environments must account for running processes.

Process isolation through Linux namespaces is not implemented and is not a confirmed architectural requirement.

### Metadata

Each Environment needs APX-managed metadata.

Metadata may include:

- Environment identifier
- display name
- lifecycle state
- associated Linux user
- associated Btrfs subvolume
- creation time
- archival state
- template origin
- snapshot references

The metadata format should be simple, explicit, and documented before implementation.

## The Hub

The Hub is an Environment dedicated to APX management.

The Hub is not a general desktop and must not become a development workspace. It exists to manage Environments and APX lifecycle operations.

The Hub is subject to the same architectural model as every other Environment. There are no special exceptions for the Hub beyond its purpose and permissions.

The Hub must be destroyable and recreatable like every other Environment. No implementation decision may require a unique lifecycle exception for the Hub.

The Hub is the default Environment in the intended APX session flow.

## Development Environment

The APX Development Environment is separate from the Hub.

Development tools such as Git, GitHub CLI, Codex, ChatGPT, browsers, IDEs, and build tooling belong in the Development Environment. They do not belong in the Hub.

Development activity includes source code, documentation drafts, repository management, experiments, build outputs, issue work, and pull request work.

## Lifecycle Operations

The future APX implementation is intended to manage:

- listing Environments
- creating Environments
- archiving Environments
- restoring Environments
- snapshotting Environments
- creating and applying templates
- launching Environment sessions

These operations should be designed around the Environment model rather than around ad hoc host mutations.

Initial lifecycle concepts include:

- active
- archived
- restorable
- template

These states are provisional and should be refined when lifecycle workflows are specified in detail.

## Architectural Decisions

### APX Uses Existing Linux Boundaries

APX should use ordinary Linux primitives before inventing APX-specific abstractions.

Initial boundaries are Linux users, Btrfs subvolumes, KDE sessions, process ownership, filesystem permissions, and metadata files or records.

### Applications Are Global

The system has one package database.

APX should not create per-Environment package databases unless a future architecture document proves that the added complexity is necessary.

### The Hub Is Clean

The Hub must remain focused on APX management. Development tools, build artifacts, source repositories, and implementation work belong in the Development Environment.

### One Graphical Environment at a Time

The intended session-management model runs only one graphical Environment at a time.

The target flow is:

```text
Boot -> Hub -> Environment -> Hub
```

This is documented in more detail in [session-management.md](session-management.md).

### Documentation Comes First

Implementation should follow documented architecture. When a design question is unresolved, the repository should capture the decision before code encodes it.

## Confirmed Intended Architecture

- APX is an orchestration layer on top of Arch Linux, not a replacement operating system.
- The host architecture is single Arch installation, single kernel, single package database, and single system-level KDE Plasma installation.
- Applications are globally installed.
- Environment data, configuration, session state, processes, and metadata are separated by Environment.
- Each Environment corresponds to one dedicated Linux user and one intended dedicated Btrfs home subvolume.
- Each Environment has its own KDE session, with only one graphical Environment active at a time.
- The Hub is an Environment dedicated to APX management.
- The Hub is the default Environment in the intended session model.
- The intended lifecycle is `Boot -> Hub -> Environment -> Hub`.
- The Hub must not become a development workspace.
- No implementation decision may require a unique lifecycle exception for the Hub.
- Linux user boundaries are sufficient as the primary identity and ownership boundary.

## Ideas Under Evaluation

- `greetd` is the preferred candidate under evaluation for replacing SDDM in the future session handoff model.

## Open Questions

- What exact Btrfs subvolume layout should APX use for Environment homes, snapshots, archives, and templates?
- What metadata format should APX use?
- What permissions should the Hub have to manage other Environments without creating a unique lifecycle exception?
- How should APX safely stop or hand off user processes during Environment switching?
- What exact display-manager/session-manager integration should APX use?
