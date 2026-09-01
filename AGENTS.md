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

The temporary root-host development mode in
`docs/temporary-root-host-development-mode-v1.md` is a second, narrower
exception. It changes scope only when the owner explicitly invokes that guide
as `root@apx-host` on the already installed, identity-matched disposable
physical pilot. While that mode is active, Codex may inspect and change the
Host, Hub, Development, and APX test Environments for repository development
and validation. It may create and destroy only clearly named disposable test
Environments itself. Destroying Hub or Development, changing disks, reinstalling
Arch, or broad cleanup still requires a fresh explicit owner instruction. This
exception is experimental, temporary, and never a production permission.

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

APX has passed the functional headless C0–C6 ladder in a disposable VM and has
an extensively exercised owner-controlled physical pilot. The physical system
now boots to the graphical Hyprland/QuickShell Hub and has validated bounded
Environment lifecycle, recovery and UI paths. It remains experimental, not
production. Current physical evidence and open acceptance boundaries are in
`CURRENT_HANDOFF.md`; the chronological record is under `docs/history`.

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

Do not describe planned architecture, repository candidates or old physical
observations as current implemented reality. In particular:

- distinguish the accepted live Hub artifact from later repository-only seeds;
- distinguish normal/system Environments and the VM v2 experiment;
- distinguish automated tests from owner-observed compositor, recovery and GPU
  behavior;
- treat dated SDDM/KDE, headless-pilot and early quota observations as history,
  not current state;
- keep current summaries concise and preserve detailed chronology in dated
  evidence documents or `docs/history`.

## Hub Rules

The Hub is the default APX Environment and the APX management entry point.

Only the authenticated, authoritative active Hub may switch, create, snapshot,
archive, restore, recover, force-stop, or delete Environments. A workload may
stop only its own active generation to return to the Hub; its other APX controls
must be read-only. The executor must enforce this independently of the UI.

The Hub template must remain minimal by default. It contains APX management UI,
system summaries, visual customization, and management widgets on the common
Hyprland base. The owner may use Environment-local `sudo pacman` in the Hub;
this is not technically restricted to an allowlist. Recommend workload and
development software in separate Environments, but enforce isolation rather
than silently blocking a locally requested Hub package. Hub package operations
must never reach the Host or another Environment.

No implementation decision may require a unique lifecycle exception for the Hub. The Hub must be destroyable and recreatable like every other Environment.

Hyprland is the default graphical template, not a universal lifecycle
dependency. New normal graphical Environments receive an independent,
digest-pinned Environment shell seed (Hyprland, QuickShell, Mako and helpers)
and may customize their copy without changing the Hub, template or siblings.
APX lifecycle and tty1 recovery must continue to work when Hyprland or all user
customization is broken.

## Development Environment

The current repository checkout is in the explicitly invoked temporary
root-Host development mode on the identity-matched disposable pilot. This is a
bounded exception documented in
`docs/temporary-root-host-development-mode-v1.md`, not the intended product
placement. Development tools such as Git, GitHub CLI, Codex, browsers, IDEs,
compilers and test tools normally belong in a Development Environment, never
in the Hub.

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
