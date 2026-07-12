# AGENTS.md

This repository contains the APX project foundation.

These instructions are durable guidance for future Codex sessions working in this repository.

## User Communication

Communicate with the user in clear, non-technical language by default. Explain
what changed, why it matters, the practical consequences, the main risks or
limitations, and what remains to be done. When a technical term is necessary,
explain it briefly in ordinary language. Do not assume the user understands
implementation details merely because the project documentation is technical.

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
- applications, dependencies, data, configuration, and runtime state local to
  each Environment
- desktop- and compositor-independent APX lifecycle behavior
- separate internal Linux accounts hidden behind one human-facing APX identity
- the Hub is an Environment, not a special desktop

The exact application-isolation mechanism and the division between minimal
host packages and per-Environment packages are under evaluation. Do not restore
the earlier global-application assumption without an explicit, documented
architecture decision.

Common defaults may come from a reviewed, versioned APX base. Never treat the
live Hub as the filesystem parent or template for other Environments. Hub-only
management software, permissions, credentials, metadata, widgets, and mutable
state must not propagate to workload Environments.

Package managers and installers executed inside an Environment must affect only
that Environment. This includes `pacman`, `yay`, `apt`, Flatpak, language
package managers, vendor installers, and installation scripts. They must never
reach the host, Hub, base artifact, or another Environment. Do not design a
shared writable package root or expose host package administration to normal
Environment users.

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
- per-Environment application installation is intended but not implemented

## Hub Rules

The Hub is the default APX Environment and the APX management entry point.

The Hub must remain clean. It may contain APX management UI, system summaries,
visual customization, and tightly scoped management widgets. Do not place
general-purpose browsers or editors, development work, source repositories,
IDEs, build tools, development browser profiles, implementation artifacts, or
experimental development scripts in the Hub.

No implementation decision may require a unique lifecycle exception for the Hub. The Hub must be destroyable and recreatable like every other Environment.

## Development Environment

The current environment is the APX Development Environment named `apx-development`.

Development tools such as Git, GitHub CLI, Codex, ChatGPT, Brave, IDEs, compilers, build tools, and test tools belong here, not in the Hub.

Codex is a temporary development tool and is not part of APX.

## Canonical Project State

Read `PROJECT_STATE.md` before planning or editing. Update it in the same change
whenever the product objective, development method, confirmed architecture, or
an accepted deviation changes.

## Git Rules

Do not commit or push unless the user explicitly asks for it.

Before editing, inspect repository state. After editing, report changed files and relevant diffs when requested.

Preserve useful technical information when restructuring documentation. Do not delete existing documentation until its relevant content has been mapped into the new structure.
