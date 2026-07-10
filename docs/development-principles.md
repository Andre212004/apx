# Development Principles

APX is currently in the documentation and architecture foundation phase.

Implementation should not begin until the repository clearly documents the architecture, session model, lifecycle model, storage model, and unresolved risks.

## Principles

- simplicity over complexity
- architecture before implementation
- no unnecessary abstractions
- no exceptions for the Hub
- global applications, isolated user data
- professional documentation
- clean repository history
- long-term maintainability

## Repository Boundaries

Work in this repository must not modify the host operating system.

Do not modify:

- `/etc`
- `/apx`
- systemd
- greetd
- SDDM
- PAM
- Linux users
- Btrfs subvolumes
- package state
- anything outside this repository

Do not use `sudo` for repository work.

## Documentation First

When a design question is unresolved, document it before encoding it in code.

Documentation should clearly separate:

- current system
- confirmed intended architecture
- ideas under evaluation
- open questions

Planned architecture must not be described as implemented reality.

## Development Environment

Development activity currently takes place in the APX Development Environment named `apx-development`, not in the Hub.

Development activity includes:

- source code
- documentation drafts
- repository management
- experiments
- build outputs
- issue work
- pull request work

Development tools may include Git, GitHub CLI, Codex, ChatGPT, Brave, IDEs, compilers, build tools, and test tools.

Codex is a temporary development tool and is not part of APX.

## Hub Discipline

The Hub must remain focused on APX management.

The following do not belong in the Hub:

- source repositories
- IDEs
- build tools
- development browsers or profiles
- Git workflow tools
- implementation artifacts
- experimental development scripts

The Hub may receive APX management permissions, but it must not bypass the core APX Environment model without a documented architectural decision.

## Implementation Readiness

Before implementation begins, APX should have documented decisions for:

- Btrfs subvolume layout
- Environment metadata format
- session handoff mechanism
- Hub permissions
- Environment lifecycle states
- snapshot, archive, restore, and template behavior
- failure and recovery behavior

## Git Discipline

Do not commit or push unless explicitly requested.

Keep changes scoped and reviewable. Avoid unrelated refactors while the repository is still establishing its foundations.
