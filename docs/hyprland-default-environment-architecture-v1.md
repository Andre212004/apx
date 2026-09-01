# Hyprland default Environment architecture v1

## 2026-07-30 official Hub bootstrap amendment

The first owner-development Hub is intentionally `hub-headless-v4`, not a
preconfigured graphical template. It contains only the normal Arch/APX base,
Environment-local administration, and Host-mediated networking. It does not
preinstall Hyprland, a terminal, Waybar, a launcher, a theme, or an owner
configuration. The owner will install Hyprland and the terminal recommended by
the official Hyprland tutorial inside that Environment.

The current graphical Hub is retained without deletion as the disposable
`hub-testes`. After the owner has built and reviewed the desired desktop in the
official Hub, selected configuration may become the source of a later
digest-bound graphical release. APX must never derive that release by blindly
copying the mutable live root.

This staged bootstrap supersedes the initial-template choice below for the
first official Hub only. It does not change the long-term compositor-independent
lifecycle, isolation, release, or recovery boundaries.

## Decision

Hyprland is the default visual base for normal APX Environments, including the
Hub. It is not built into the universal APX lifecycle protocol: recovery,
creation, stop, snapshot, archive, restore, and deletion remain compositor-
independent.

Every new graphical Environment receives an independent root, home, package
database, services, runtime state, and one-time copy of the versioned minimal
Hyprland configuration. Later template changes do not rewrite existing ricing.
The laboratory creator copies only the three digest-bound seed files and fails
closed on missing, extra, changed, linked, special, or oversized entries.

## Initial templates

`hyprland-base-v1` supplies a minimal functional desktop with Hyprland,
Waybar, Foot, Fuzzel, Mako, Portuguese keyboard defaults, portals, AMD graphics
userspace, PipeWire/WirePlumber, fonts, polkit, and Environment-local
administration.

`hub-hyprland-v1` uses the same release and adds the APX Hub role, native
GTK/libadwaita management application, and complete Waybar management entry.
That application is a required future Hub overlay, not part of the currently
admissible base release.
Gaming and university templates are later overlays, not separate base systems.

## Hub authority and the APX button

Every graphical Environment may show the APX button. In the active Hub it opens
the complete control centre: switch, create, snapshot, archive, restore, and
delete. In a workload it offers only return-to-Hub and read-only status/details.

This is not merely a hidden-button rule. The executor accepts Environment
management and switching only when trusted session evidence identifies the
authenticated, active, authoritative Hub. A workload may request a graceful
stop only for its own active generation, which is the controlled return-to-Hub
path. It cannot manage another Environment by forging a request or UI role.

The GTK demonstration now requires an explicit display role and refuses its
management mode for workload roles. This is a prototype-level safeguard only:
the future trusted session launcher must supply the observed role, and the
executor authorization remains the decisive boundary.

The demo source and its changing hash are explicitly excluded from the
immutable Hyprland base manifest. A production Hub client must later receive a
separate closed manifest and pass fake-executor and typed-executor gates before
Hub replacement can become eligible.

A pure pre-freeze candidate gate now records that promotion boundary. Even a
fully reproducible client with source review, no effect adapter, trusted role
derivation, workload refusal, fake/typed executor tests, and accessibility
evidence reaches only `ready-for-separate-manifest-freeze`; it is not admitted
until a later reviewed overlay freezes its exact artifact digest.

The pure launcher contract now binds active authenticated graphical-session
evidence to the exact verified Environment registration and generation. It
constructs only a fixed local UI command, rejects arbitrary modes, and refuses
workload management before the interface opens. Its observation and execution
adapter is not implemented yet.

The exclusive handoff state machine and internal test executor are implemented with
no system effects. They rehearse Hub stop, broker-owned transition, hidden
workload start/readiness, workload return, hidden Hub start/readiness, and the
final Hub state. Recovery and watchdog must be verified before the first stop;
release and readiness evidence is single-transition and cannot be replayed.
Failure injection before each of the eight stages ends in terminal broker-owned
recovery. This test path is not exposed by the GTK product prototype.

This does not make physical button testing ready. A real session broker,
trusted observation/effect adapters, an admitted graphical release, a
production Hub client, and renewed recovery evidence are still required.

## Manual button-test gate

The UI controls now bind to the closed executor catalogue: Hub `open` becomes
generation-bound `activate`, capability management becomes
`configure-capabilities`, and workload `return-to-hub` becomes `stop` for only
its own generation. Disabled, renamed, approval-mismatched, untrusted, or
non-Hub management controls cannot create an intent.

The real typed transport client and endpoint core now exist independently of
the removed disposable UI. They use a fixed production socket, bounded exact
responses, trusted plan/approval/session authorities, atomic nonce reservation,
and a typed effect boundary. Durable authority stores, the server wrapper, and
the physical graphical effect adapter remain required before GTK controls can
be enabled.

An effect-free integration test now joins the typed button intents, executor
assessment, exclusive broker plan, and complete handoff rehearsal. It returns
to `hub-active` with the Hub as the sole owner.

The current physical readiness assessment remains `blocked`. The admitted
graphical base, production Hub client, installed graphical Hub and workload,
trusted launcher, exclusive broker, mediated device adapter, and independent
graphical watchdog are absent, and H0 physical execution remains code-locked.
The post-battery tty1 observation and active typed executor are positive gates,
but cannot substitute for the missing graphical components. When every gate
passes, the result is only `ready-for-separate-owner-approval`, never automatic
execution. The bounded owner procedure will be click Development, wait for the
verified workload surface, click return to Hub, and confirm the restored Hub,
with a 30-second maximum visible interval and independent recovery throughout.

ASCII animation and ASCII-inspired controls are a planned ricing direction,
especially for the Hub. They remain a replaceable presentation layer so visual
experiments cannot weaken lifecycle authorization or recovery access.

## Capabilities

The essential-private default admits mediated display/GPU, keyboard, touchpad,
audio, notifications, portals, and Host-mediated outbound networking. The Host
owns the physical Wi-Fi connection; Environments receive connectivity rather
than direct Wi-Fi administration hardware.

Camera, microphone, controller, and removable storage are optional and absent
by default. Only one normal graphical Environment may own the graphical seat at
a time.

Optional capabilities have a pure Hub-only change contract. It requires the
target generation to be stopped, trusted canonical Hub evidence, no uncertain
APX operation, and explicit confirmation. It never activates the target or
changes essential capabilities as part of the policy update.

## Packages and customization

The owner-selected common essential desktop profile is now
`desktop-essential-v1`, with presentation in `waybar-ascii-v1`. The installed
Host runtime validates and independently copies this profile during every new
`graphical-base` or `hub-graphical` creation. Audio controls are local to the
Environment. Network and system time remain Host-owned, while Bluetooth is
visibly locked until an exclusive mediator exists. Installing NetworkManager,
BlueZ, or a time synchronizer inside every Environment is not used as a
substitute for hardware mediation and could create competing ownership.

The internal user has `sudo pacman` for its own writable Environment root. No
package allowlist is imposed on the Hub or workloads. The security boundary is
that package hooks, databases, caches, services, and files cannot access the
Host, another Environment, or the immutable release.

The Hub starter remains minimal by policy, not by a technical package ban. If
the owner later wants a clean Hub, APX creates a new Hub generation from the
template and transfers only explicitly selected preferences. It does not clone
the mutable live Hub root.

## Current implementation status

Repository contracts now define the two templates, storage limits, essential
and optional capability sets, independent config-copy behavior, release
admission evidence, runtime role mappings, Hub view-model mappings, a minimal
Hyprland/Waybar seed, a closed typed-session GTK client, and guarded Hub replacement.
The installed Hyprland 0.55.4 parsed the exact minimal starter through an
unregistered, private-network, device-free nspawn invocation and returned
`config ok`; no compositor session or graphical device was opened.

The physical Host does not yet contain an admitted `hyprland-base-v1` release.
No real Hub replacement or new graphical Environment was created. Physical H0
remains code-locked after the recovery incident. Package acquisition, two
reproducible builds, disposable activation, audio/network/portal validation,
typed Hub executor integration, and exclusive handoff tests remain required.
