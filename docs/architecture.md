# APX Architecture

APX is a personal operating environment platform built on top of Arch Linux.

The operating system remains Linux. APX is an orchestration layer that manages isolated personal environments on a single Arch Linux installation.

## Non-Goals

APX is not:

- a Linux distribution
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

## Environments

An Environment is the primary APX unit.

Each Environment maps to:

- one Linux user
- one Btrfs subvolume
- one independent KDE session
- independent configuration
- independent processes
- independent metadata

The Linux user boundary provides ownership and process separation. The Btrfs subvolume provides storage structure, snapshot support, and lifecycle management. The KDE session provides an independent interactive workspace.

## Shared Applications, Isolated Data

Applications are shared globally through the Arch package database.

Environment isolation applies to:

- user home data
- configuration
- session state
- running processes
- APX metadata

This avoids duplicating applications while preserving independent personal workspaces.

## The Hub

The Hub is an Environment dedicated to APX management.

The Hub is not a general desktop and must not become a development workspace. It exists to manage Environments and APX lifecycle operations.

The Hub is subject to the same architectural model as every other Environment. There are no special exceptions for the Hub beyond its purpose and permissions.

## Development Environment

The APX Development Environment is separate from the Hub.

Development tools such as Git, GitHub CLI, Codex, ChatGPT, browsers, IDEs, and build tooling belong in the Development Environment. They do not belong in the Hub.

## Lifecycle Operations

APX is expected to manage:

- listing Environments
- creating Environments
- archiving Environments
- restoring Environments
- snapshotting Environments
- creating and applying templates
- launching Environment sessions

These operations should be designed around the Environment model rather than around ad hoc host mutations.

## Architectural Decisions

### APX Uses Existing Linux Boundaries

APX should use ordinary Linux primitives before inventing APX-specific abstractions.

Initial boundaries are Linux users, Btrfs subvolumes, KDE sessions, process ownership, filesystem permissions, and metadata files or records.

### Applications Are Global

The system has one package database.

APX should not create per-Environment package databases unless a future architecture document proves that the added complexity is necessary.

### The Hub Is Clean

The Hub must remain focused on APX management. Development tools, build artifacts, source repositories, and implementation work belong in the Development Environment.

### Documentation Comes First

Implementation should follow documented architecture. When a design question is unresolved, the repository should capture the decision before code encodes it.

