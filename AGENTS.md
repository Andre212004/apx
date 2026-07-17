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
The target-bound physical pilot in
`docs/physical-headless-development-handoff-v1.md` changes that scope only when
the owner explicitly invokes that guide from the Arch installation medium. It
is not standing authorization during ordinary repository work.

During ordinary repository work, do not modify:

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

APX has passed the functional headless C0–C6 ladder in a disposable VM. The
production system remains in architecture, trust, hardening, and physical-
readiness work. A separately documented owner-controlled physical pilot is
prepared but has not been executed.

Implementation may advance only within documented boundaries. VM laboratory
code and exact target-bound physical-pilot adapters are experimental and must
never be described as production. Any new production mechanism still requires
its architecture, session, lifecycle, storage, risks, and recovery behavior to
be documented first.

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
- namespace process isolation and per-Environment package installation passed
  in the disposable VM, but are not installed on the physical system

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

Also read `CURRENT_HANDOFF.md` before planning or editing. It is the concise
current-session bridge: it records the latest owner-reported physical state,
the next external evidence expected, active safety blocks, and the immediate
repository milestone. Update it whenever those facts change. It does not
override `PROJECT_STATE.md`; disagreement must be resolved explicitly rather
than guessed.

## Git Rules

Do not commit or push unless the user explicitly asks for it.

Before editing, inspect repository state. After editing, report changed files and relevant diffs when requested.

Preserve useful technical information when restructuring documentation. Do not delete existing documentation until its relevant content has been mapped into the new structure.
