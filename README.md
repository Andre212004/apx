# APX

APX is a personal operating environment platform built on top of Arch Linux.

APX does not replace Linux. The host remains a single Arch Linux installation with one kernel, one package database, and one KDE Plasma installation. APX adds an orchestration layer for managing isolated personal Environments on that system.

## What APX Is

APX is an architecture for managing multiple isolated personal Environments on one Arch Linux host.

Each Environment is intended to provide a separate personal workspace with its own Linux identity, home data, configuration, graphical session, processes, and APX metadata.

In the intended architecture, applications are shared globally through the host Arch Linux system while user data and session state are separated by Environment.

## What APX Is Not

APX is not:

- a Linux distribution
- a replacement operating system
- a container runtime
- a virtual machine manager
- a second package manager
- a replacement desktop shell
- a development workspace inside the Hub

These boundaries keep APX focused on orchestration rather than duplicating operating system responsibilities.

## Single-Arch Architecture

An APX system has:

- one Arch Linux installation
- one kernel
- one package database
- one KDE Plasma installation
- one shared set of globally installed applications

APX does not create a separate operating system per Environment. The host system remains the authority for packages, services, kernel updates, and the system-level KDE Plasma installation.

## Environments

An APX Environment is represented by:

- one Linux user
- one intended Btrfs home subvolume
- one independent KDE session
- independent configuration
- user-owned processes separated by Linux user ownership
- independent metadata

The Linux user is the primary identity boundary. It defines file ownership, process ownership, user-level permissions, home ownership, and session identity.

Current manually created users still have ordinary homes under the existing `@home` subvolume. Dedicated Btrfs home subvolumes are the intended APX architecture, not the current implemented state.

## Hub

The Hub is the default APX Environment and the management entry point.

The Hub's planned responsibility is to provide APX operations such as listing, creating, archiving, restoring, snapshotting, templating, and launching Environments.

The Hub is not a general-purpose desktop or a development workspace. Source repositories, IDEs, build tools, Git workflow tools, development browser profiles, and implementation artifacts belong in the APX Development Environment.

The Hub must be destroyable and recreatable like every other Environment. No APX implementation decision may require a unique lifecycle exception for the Hub.

## Btrfs

Btrfs is the intended storage foundation for Environment homes.

The target model is one dedicated home subvolume per Environment. This should support snapshots, archival, restoration, and templates.

The exact subvolume layout is not implemented yet and must be validated before implementation.

## KDE Plasma

KDE Plasma is shared at the system level.

Environment separation is expected to come from separate Linux users, separate user configuration, separate home data, and separate graphical sessions. APX does not intend to install a separate KDE Plasma copy per Environment.

Only one graphical Environment should run at a time in the intended session model.

## Current Development Status

APX is in the documentation and architecture foundation phase.

This repository contains architecture documentation and a read-only inspection and creation-planning prototype. No privileged creation or mutating APX runtime exists. Development currently takes place in the Development Environment named `apx-development`. Codex is a temporary development tool and is not part of APX.

`apx host check` performs a read-only readiness inspection for the proposed first experimental Environment, `trial`. It reports identity, storage, graphical-session, and account-policy evidence independently, marks sandbox-visible evidence as requiring authoritative host confirmation, and emits a deterministic non-executing manual plan. It does not create or modify host resources.

`apx host validate` performs the read-only Milestone 3A practical inspection. It summarizes the three fixed APX accounts, removal-blocker evidence, Brave installation and per-user data state, and factual session-switching prerequisites. It does not remove or change host resources and does not claim deletion safety.

SDDM currently manages graphical sessions. The future session-management direction is documented in [docs/session-management.md](docs/session-management.md). `greetd` remains only a preferred direction under evaluation; it has not been adopted or implemented.

No package installation, system configuration, user creation, Btrfs changes, display-manager changes, or service changes should be performed from this repository at this stage.

## Repository Structure

```text
.
├── AGENTS.md
├── docs/
│   ├── architecture.md
│   ├── development-principles.md
│   ├── roadmap.md
│   └── session-management.md
├── src/
│   ├── apx_cli.py
│   ├── apx_consistency.py
│   ├── apx_host.py
│   ├── apx_environment.py
│   └── apx_registration.py
├── tests/
├── .gitignore
├── apx
└── README.md
```

## Design Principles

- simplicity over complexity
- architecture before implementation
- no unnecessary abstractions
- no exceptions for the Hub
- global applications, isolated user data
- professional documentation
- clean repository history
- long-term maintainability

## Documentation

Start with [docs/architecture.md](docs/architecture.md).
