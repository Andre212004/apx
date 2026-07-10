# APX

APX is a personal operating environment platform built on top of Arch Linux.

APX does not replace Linux. The host remains a single Arch Linux installation with one kernel, one package database, and one KDE Plasma installation. APX adds an orchestration layer for managing isolated personal environments on that system.

## Status

APX is in the foundation phase.

The current repository contains project documentation only. Implementation should begin after the architecture, boundaries, and operational model are documented clearly enough to guide long-term development.

## Core Model

An APX Environment is represented by:

- one Linux user
- one Btrfs subvolume
- one independent KDE session
- independent configuration
- independent processes
- independent metadata

Applications are installed globally through the host Arch Linux system. User data and configuration are isolated per Environment.

## Repository Structure

```text
.
├── docs/
│   ├── README.md
│   ├── architecture.md
│   ├── development-environment.md
│   ├── environments.md
│   ├── hub.md
│   └── repository.md
├── .gitignore
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

