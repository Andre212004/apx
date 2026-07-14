# Development Principles

The production APX system remains in the documentation, architecture, trust,
and hardening phase. A separately guarded disposable-VM implementation may be
used to validate architecture without changing the physical system.

Production implementation should not advance beyond what the repository has
documented for architecture, session, lifecycle, storage, and unresolved risk.
Laboratory results must be identified as experimental and cannot be described
as physical-machine readiness.

## Principles

- simplicity over complexity
- architecture before implementation
- no unnecessary abstractions
- no exceptions for the Hub
- Environment-local applications, dependencies, data, and state
- one human-facing identity over hidden internal Linux accounts
- explicit isolation guarantees rather than VM-like claims
- reviewed versioned baselines rather than cloning live Environments
- Environment-local package administration with no host package-manager path
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

For the preferred future clean installation, APX first creates a headless Hub
with only the bounded management CLI, then a separate headless Development
Environment. The Git clone, Codex, compilers, tests, build outputs, and ongoing
source work move into Development. A temporary pre-Environment bootstrap staging
area is allowed only as a documented, bounded exception and is removed or
archived after the installed artifact and Development are verified.

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

The Hub may include APX management components, system summaries, visual
customization, and tightly scoped widgets. This does not make it a general-
purpose application Environment. Software selection for workload Environments
must occur through reviewed templates or a future bounded management protocol,
not an arbitrary privileged installer exposed by the Hub.

The first Hub may be headless. Its `apx` CLI is the management UI and remains
subject to the same typed operations, previews, approvals, journal, and recovery
rules as a future graphical button. A terminal presentation does not authorize
general development or host administration in Hub.

The Hub must not be used as the live base image for other Environments. Common
drivers, integration, fonts, certificates, and defaults belong to a reviewed,
versioned APX base or to the host according to a documented boundary. Hub-only
software, permissions, credentials, and mutable state remain confined to the
Hub role.

## Continuity Discipline

`PROJECT_STATE.md` is the canonical project-continuity document. Every change to
the objective, method, confirmed architecture, or an accepted deviation must
update it in the same change. Architectural experiments must record both
successful and unresolved evidence.

## Implementation Readiness

Before implementation begins, APX should have documented decisions for:

- Btrfs subvolume layout
- Environment metadata format
- session handoff mechanism
- Hub permissions
- Environment lifecycle states
- snapshot, archive, restore, and template behavior
- failure and recovery behavior
- per-Environment application and dependency isolation
- normal and high-security isolation threat models
- local-assistant lifecycle and permissions

## Git Discipline

Do not commit or push unless explicitly requested.

Keep changes scoped and reviewable. Avoid unrelated refactors while the repository is still establishing its foundations.
