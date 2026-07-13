# APX Headless Bootstrap and CLI-First Delivery v1

Status: accepted development and clean-install direction. This document changes
the preferred delivery order, not the current machine. It does not authorize
disk formatting, Arch installation, package changes, users, services, Btrfs,
APX installation, or any effect outside this repository.

## Decision

The preferred first real APX installation starts from a newly installed,
minimal Arch Linux host with no KDE, Hyprland, SDDM, graphical greeter, desktop,
or APX graphical session.

APX is delivered and proven in command-line form first:

```text
minimal Arch console
  -> verified APX bootstrap
  -> headless Hub with APX CLI
  -> headless Development Environment
  -> lifecycle/isolation/storage/recovery validation
  -> first Hyprland Environment
  -> graphical APX controls
  -> optional graphical Hub
```

Graphical interface work is the last priority. The APX CLI is not a temporary
throwaway: it remains the scriptable, recovery-friendly interface beneath any
later button or graphical workflow.

## Why This Is Preferred

Starting without a desktop removes several unrelated variables from the first
implementation gate:

- no outgoing KDE session to close;
- no inactive Hub KDE session retained by SDDM;
- no SDDM autologin or greeter respawn;
- no existing compositor holding KMS, render, input, VT, or Wayland resources;
- no need to preserve a working graphical desktop during early lifecycle tests;
- recovery remains a physical text console until graphical handoff is proven.

This does not remove the need for device mediation, recovery, teardown proof,
or graphical-session isolation. It changes their starting condition from
“replace a live desktop” to “activate the first graphical owner from a verified
headless state.”

## Fresh Installation Versus Current-Machine Migration

APX now has two separate delivery paths:

| Path | Purpose | Priority |
|---|---|---|
| Clean headless bootstrap | Preferred first functional APX installation on a fresh minimal Arch host | Primary |
| In-place graphical migration | Preserve and transition an existing KDE/SDDM machine | Secondary compatibility path |

The G2 KDE/SDDM release work remains valid for the second path and for proving
that APX can coexist with legacy desktops. It no longer blocks the primary clean
bootstrap path.

No document authorizes erasing or reinstalling the current machine. A future
clean installation requires its own backup, recovery-media, disk-layout,
bootstrap, and cutover approval.

## Bootstrap Trust Boundary

A Git clone is source acquisition, not a privileged installation protocol.
Running an arbitrary mutable checkout as root would let repository content
become an unrestricted host installer and would bypass the APX executor model.

The accepted bootstrap direction is:

1. obtain a pinned APX source revision or release;
2. verify its repository/release identity and expected digest;
3. review the exact host prerequisites and effects;
4. build or select a versioned APX artifact in a bounded build context;
5. preview the exact installation plan;
6. approve and apply only the typed bootstrap effects;
7. verify installed files, authority, journal, and rollback/recovery state.

During development, `git clone` belongs in the Development Environment. The Hub
never contains the APX source repository, Git workflow, Codex, compiler, build
cache, or experimental scripts.

The initial pre-Environment bootstrap console may temporarily hold a reviewed
source/artifact staging area because no Environment exists yet. This is an
explicit bootstrap exception, not the future steady state. It must be bounded,
excluded from templates, and removed or archived after Development is created
and the installed artifact is independently verified.

## Minimal Host Contract

The clean Arch host contains only what the eventual accepted host boundary
requires:

- bootloader, kernel, firmware, storage, networking, time, trust, and recovery
  facilities;
- hardware drivers and physical-device ownership;
- the minimal APX registry, broker, executor, and runtime dependencies selected
  by later implementation decisions;
- no general desktop, display manager, browser, editor, IDE, Codex, development
  repository, or workload package set.

The first experimental package-name manifest, disk/boot profile, headless
backend, authentication method, and bootstrap representation are fixed in
`clean-install-foundation-v1.md`. Exact versions and target hardware remain
dossier inputs. “Minimal” never means removing recovery, trust verification,
networking needed for bootstrap, or hardware support merely to reduce package
count.

## Bootstrap Console

Before the Hub exists, the person uses one physical text console as a temporary
bootstrap/recovery surface. It is host-owned and outside the normal APX
Environment experience.

The bootstrap console may:

- inspect prerequisites and current state;
- verify source/release/artifact identity;
- render APX plans;
- request the bounded bootstrap operation;
- show journal, verification, and recovery results;
- create the first Hub only through the accepted executor protocol.

It is not the future Hub, does not become an unrestricted permanent APX admin
shell, and cannot be counted as a normal Environment. Once the Hub and recovery
path are verified, normal Environment management moves to the APX CLI in the
Hub.

## Headless Hub Contract

The first Hub is a headless APX Environment. “Headless” means it has no desktop
or compositor; it does not mean the Hub stops being an Environment.

Its user-facing management surface is the `apx` CLI. The initial command groups
must eventually cover:

- status and readiness;
- list and inspect Environments;
- render create/activate/stop plans;
- create from reviewed base/role releases;
- activate and return through non-graphical sessions;
- snapshot, archive, restore, and destroy previews;
- show blockers, progress, journal, and recovery choices;
- install no arbitrary software into another Environment.

The CLI is a bounded client of the same future protocol used by a graphical Hub.
It does not become a root shell, accept arbitrary executor commands, or bypass
approval rules.

The Hub may expose a terminal-like APX management view, but it remains
management-only. General shell work, browsing, editing, building, Git, Codex,
and source development belong in Development.

## First Development Environment

After the headless Hub passes creation and recovery checks, it creates a
headless Development Environment from the reviewed base plus Development role.

Development contains:

- Git and the APX source checkout;
- Codex and other temporary development assistants when explicitly selected;
- compiler, tests, build tools, documentation tools, and development browser;
- build outputs and experiment artifacts;
- no Hub authority beyond the same bounded APX client available to an ordinary
  authorized Environment integration.

APX development continues there, not in the Hub and not in the host bootstrap
console. The repository may build new versioned APX artifacts, but installation
still goes through preview, approval, executor, journal, verification, and
rollback.

The closed logical promotion path is specified in
`development-to-hub-release-promotion-v1.md`. Development and Codex produce an
untrusted immutable candidate; a host-owned import boundary copies it into
quarantine, independent verification and a separate decision admit a release,
and the executor creates a replacement Hub. Development never edits or mounts
the live Hub.

## Codex Lifecycle

Codex is development tooling, not part of APX and never a Hub dependency.

Before removing Codex from Development:

1. preserve the APX source and documentation in a verified repository history;
2. verify a separately reachable copy or remote;
3. retain reproducible build/test instructions without Codex;
4. verify the CLI and graphical controls do not call Codex;
5. remove Codex only from the Development Environment through its local package
   boundary or destroy/recreate that Environment from a Codex-free role.

Removing Codex must not alter the Hub, host, base, executor, another Environment,
or APX recovery. Destroying Development later remains an ordinary Environment
lifecycle operation.

## CLI-First Acceptance Ladder

No later gate inherits authority from an earlier one.

### C0 — Recovery and provenance

- independently reachable repository history;
- restore-tested personal backup;
- boot-tested Arch recovery media;
- pinned source/release identity and bootstrap artifact provenance;
- exact disk and host prerequisite plan reviewed but not applied implicitly.

### C1 — Minimal host bootstrap

- no graphical stack or display manager;
- exact APX host files/dependencies admitted by manifest;
- bounded executor/registry/broker authority;
- journal and rollback/recovery verified;
- reboot returns to a usable text recovery surface.

### C2 — Headless Hub

- Hub created as an ordinary Environment from a reviewed release;
- `apx` CLI provides only typed management operations;
- no source, Git, Codex, browser, editor, compiler, or development artifact;
- Hub destroy/recreate passes without losing host control or recovery.

### C3 — Headless Development

- Development created independently from the same base plus its own role;
- Git/Codex/build tools exist only there;
- Hub and Development roots, homes, packages, processes, services, IPC,
  network policy, mounts, and runtime identities remain separate;
- stopping Development leaves zero unapproved runtime residue.

### C4 — Environment-local installation

- install one package in Development through its own package database;
- prove the package is absent from Hub, host, base, and a second Environment;
- install the same package independently in a second fixture Environment;
- delete one fixture without changing the other installation.

### C5 — Lifecycle and storage

- create, activate, stop, snapshot, archive, restore, and destroy pass through
  generation-bound journal transitions;
- interrupted operations preserve data and enter typed recovery;
- quota/capacity, source/template preservation, and zero-residue checks pass;
- reboot recovery classifies every incomplete operation conservatively.

### C6 — Non-graphical daily workflow

- boot reaches the locked/bootstrap or headless Hub path without a graphical
  account chooser;
- CLI can move between Hub and headless Environments without exposing host
  administration;
- an Environment can perform real development work and return cleanly;
- recovery works without networking, Codex, or a graphical session.

### C7 — First graphical Environment

- physical recovery VT/controller is verified first;
- current seat has no graphical owner, display manager, or stale device lease;
- one disposable Hyprland role receives only the selected AMD display and
  mediated built-in keyboard/touchpad;
- failure returns to the text recovery surface;
- teardown revokes devices and restores a verified headless Hub path.

This is not the existing G2 KDE handoff. It is a new clean-host graphical gate,
tentatively named H0, whose baseline is “no graphical owner.” G2 remains the
legacy graphical-to-graphical migration gate.

### C8 — Graphical controls

- selected Environment receives an APX return/switch control backed by the CLI
  protocol;
- each button renders the same plan, consequences, approval, journal, and result
  as the corresponding command;
- no graphical action gains authority unavailable to the typed protocol;
- Hyprland failure leaves CLI/recovery usable.

### C9 — Optional graphical Hub

- graphical Hub is built from the same reproducible Hub role;
- CLI remains available for recovery and automation;
- no development tooling or workload application is added to Hub;
- graphical Hub destroy/recreate and failure recovery pass;
- the product may still choose a headless/text Hub profile.

## H0 Versus G2

H0 and G2 share device identity, mediation, readiness, teardown, watchdog, and
recovery evidence, but their release preconditions differ:

| Gate | Starting state | Required release proof |
|---|---|---|
| H0 | Minimal host with no graphical session/display manager | Prove no graphical owner exists and recovery VT is independent |
| G2 | Existing KDE/SDDM graphical sessions | Gracefully stop all sessions, quiesce SDDM, then prove release |

H0 is the primary clean-install path. G2 remains useful but is not allowed to
delay C0–C6 or the first H0 design.

## Implementation Order

The new priority order is:

1. finish the clean-bootstrap host/base/backend decision;
2. freeze the APX CLI command and response contract;
3. freeze candidate import, release admission, and Hub replacement contracts;
4. validate headless lifecycle/storage/isolation with disposable fixtures;
5. implement the smallest reviewed bootstrap/CLI path;
6. prove C0–C6 on a disposable or freshly approved test installation;
7. design and prove H0 from a verified no-graphical-owner baseline;
8. add Hyprland integration and graphical Environment controls;
9. add a graphical Hub only after the CLI path remains independently usable;
10. retain G2 as the in-place KDE/SDDM migration campaign.

## Remaining Decisions

This direction deliberately does not yet select:

- final graphical and high-security system-container/OCI/backend choices;
- production APX trust keys, custody, rotation, and revocation;
- exact Btrfs disk/subvolume creation for a fresh machine;
- the first mutating executor transport and installation privileges;
- secure console unlock and owner authentication;
- headless Hub/Environment session transport;
- H0 broker, device mediator, and Hyprland launch mechanism;
- whether the final default Hub is text, graphical, or offers both profiles.

Those choices must be closed before a real fresh installation is attempted.
