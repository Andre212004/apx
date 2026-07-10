# AGENTS.md

This repository contains the APX project foundation.

These instructions are durable guidance for future Codex sessions working in this repository.

## Scope

Work only inside this repository unless the user explicitly changes the scope.

Do not modify:

- the operating system
- `/etc`
- `/apx`
- systemd
- greetd
- SDDM
- PAM
- Linux users
- Btrfs subvolumes
- packages
- anything outside this repository

Do not use `sudo`.

## Current Phase

APX is in the documentation and architecture foundation phase.

Do not write implementation code until the architecture, session model, lifecycle model, and storage model are documented clearly enough to guide implementation.

## Project Boundaries

APX is an orchestration layer on top of one Arch Linux installation.

Confirmed architectural boundaries:

- one Arch Linux installation
- one kernel
- one package database
- one system-level KDE Plasma installation
- globally installed applications
- isolated user data per Environment
- the Hub is an Environment, not a special desktop

## Documentation Rules

Keep documentation factual.

Clearly separate:

- current system
- confirmed intended architecture
- ideas under evaluation
- open questions

Do not describe planned architecture as implemented reality. In particular:

- dedicated Btrfs home subvolumes are intended architecture, not current state
- current manually created users still have ordinary homes under the existing `@home` subvolume
- `greetd` is a preferred candidate under evaluation, not adopted or implemented
- SDDM currently manages graphical sessions
- process isolation through namespaces is not implemented

## Hub Rules

The Hub is the default APX Environment and the APX management entry point.

The Hub must remain clean. Do not place development work, source repositories, IDEs, build tools, development browser profiles, implementation artifacts, or experimental development scripts in the Hub.

No implementation decision may require a unique lifecycle exception for the Hub. The Hub must be destroyable and recreatable like every other Environment.

## Development Environment

The current environment is the APX Development Environment named `apx-development`.

Development tools such as Git, GitHub CLI, Codex, ChatGPT, Brave, IDEs, compilers, build tools, and test tools belong here, not in the Hub.

Codex is a temporary development tool and is not part of APX.

## Git Rules

Do not commit or push unless the user explicitly asks for it.

Before editing, inspect repository state. After editing, report changed files and relevant diffs when requested.

Preserve useful technical information when restructuring documentation. Do not delete existing documentation until its relevant content has been mapped into the new structure.
