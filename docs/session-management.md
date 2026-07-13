# Session Management

This document records the intended APX session experience and the decisions
still required. No functional APX session-management implementation exists.

The complete v1 proposal for human identity, unlock, switching, unsaved-work
handling, locking, and recovery is maintained in
`human-identity-and-session-handoff-v1.md`. This overview remains the concise
statement of direction and current reality.

## Current System

SDDM currently manages graphical sessions. `greetd` has not been adopted or
implemented. Current manually created users have ordinary homes under the
existing `@home` subvolume. The normal system still exposes Linux account and
display-manager behavior; the intended APX abstraction is not implemented.

## Human-Facing Identity

The intended owner experience has one human identity and named Environments.
APX may retain one internal Linux account per Environment for ownership and
session separation, but normal boot and switching must not show an ordinary
Linux user chooser or ask the owner to select internal accounts.

Automatic entry into the Hub does not imply an unauthenticated computer. The
secure login, unlock, credential lifetime, and recovery mechanism remain to be
designed. A future multi-person model may group Environments beneath separate
human identities, but must not be inferred from the current internal account
mapping.

## Intended Flow

Only one normal graphical workload Environment should be active at a time:

```text
Boot -> secure Hub entry -> selected Environment -> Hub
```

The proposed handoff uses a minimal host-owned transition and recovery surface.
The Hub does not remain graphically active behind a workload Environment. This
surface is trusted lifecycle machinery, not another Environment or general
desktop.

For the preferred clean-install sequence, the initial Hub and Development
sessions are non-graphical. A physical host-owned text console provides
bootstrap/recovery before the Hub exists; afterward the bounded `apx` CLI in the
headless Hub drives lifecycle operations. This CLI-first stage is not permission
to expose internal accounts or a general host administration shell in the final
product.

### Hub

The Hub is the default minimal Environment and management surface. It can list,
create from templates, configure, launch, stop, snapshot, archive, restore, and
delete Environments. It may provide system summaries, visual customization, and
tightly scoped widgets. It is not a general-purpose browser, editor, gaming, or
development Environment.

The Hub selects declarative templates, software sets, and policies through a
future bounded APX protocol. It must not expose an arbitrary privileged package
installer or shell into other Environments.

### Hub to Environment

Launching an Environment must establish its internal identity, local
application/runtime view, storage, devices, services, desktop session, and
isolation policy. The Hub's graphical session should not remain as an
independent general desktop. The precise handoff mechanism is under evaluation.

### Environment to Hub

Returning must account for unsaved work, graphical clients, user services,
containers or namespaces, mounted storage, devices, and local assistants. APX
must distinguish clean stop, refusal because work is active, failure, forced
termination, and recoverable incomplete handoff.

## Desktop and Compositor Independence

An Environment may use Hyprland, KDE Plasma, GNOME, or another supported
desktop/compositor. Applications and dependencies are Environment-local in the
intended product. The boundary between minimal host graphical facilities and
per-Environment desktop packages remains an architecture question.

The Hub and workload sessions may share a versioned APX baseline, but no
workload session inherits the live Hub's management capabilities or mutable
state. Host-provided hardware and network facilities must be distinguished from
credentials or secrets copied into an Environment.

APX lifecycle must rely on stable system/session primitives and an explicit
adapter contract where necessary. It must not encode Plasma, GNOME, Hyprland,
KDE autostart, or another desktop API as the universal lifecycle mechanism.

## Process and Service Lifecycle

Normal Environment services are intended to exist only while the Environment
is active. `Linger=no` remains the current default direction. Services that
start subordinate runtimes must stop them explicitly and APX must verify that
no Environment-owned processes or mounts survive shutdown unless a future
reviewed policy permits them.

Linux ownership is useful but does not provide VM-equivalent containment.
Namespace, cgroup, capability, seccomp, IPC, network, GPU, device, and high-
security-profile behavior require a threat model and experiments.

## Local Assistant Lifecycle

An Odysseus instance may be enabled for a selected Environment and is active
only while that Environment is active. Initially it accesses only its own
Environment. Any Hub control over access is a policy-management action, not
implicit cross-Environment visibility. Communication or shared memory between
assistants is deferred.

Codex may later be provisioned in selected development Environments for coding
and debugging. Its tools and data access must remain separate from Odysseus
personal-assistant memory and permissions.

## Display Manager Direction

The display-manager and handoff mechanism remain under evaluation. SDDM is the
last confirmed current manager. `greetd` is only a candidate. The chosen design
must hide internal accounts, support secure Hub entry, recover from failed
launches, and remain desktop-independent.

The primary clean-install path initially has no display manager. Its first
graphical gate is H0, which activates one Hyprland Environment from a verified
no-graphical-owner baseline and must return to the headless recovery/Hub path.
SDDM/KDE G2 remains the separate in-place migration path.

The separate G2 exclusive-session design in
`hyprland-g2-exclusive-session-design-v1.md` records the physical handoff safety
boundary and the current blockers for any executable preview. It does not
authorize a broker, device grant, or host/session change yet.

For that experiment only, `hyprland-g2-broker-recovery-boundary-v1.md` selects
a host-owned text recovery VT, a separate Hyprland experiment VT, temporary
SDDM quiescence, and revocable exact device leases as the candidate boundary.
This narrows G2 without selecting the final APX broker or authorizing execution.

`hyprland-g2-kde-release-proof-v1.md` separately defines the required release
proof across login session, processes, services, graphical IPC, GPU, input, VT,
mounts, and namespaces. A blank display or successful logout response never
counts by itself.

The 2026-07-13 read-only observation found that current SDDM behavior retains
both an active Development KDE session and an inactive but live Hub KDE session
on the same seat. This is current-system evidence, not intended APX behavior;
both session generations must end before an exclusive G2 handoff.

The closed G2 observer schema discovers all graphical sessions from the seat,
classifies user-manager records separately, and permits only `released`,
`blocked`, or `unknown`. A reboot invalidates every prior runtime identity and
requires a fresh baseline.

G2 observation is further split into an unprivileged collector, one exact
session-local KDE adapter, a narrow privileged read-only source, and the
separate effect executor. No observer component receives a general root shell,
device open, or arbitrary UI path.

The Hub's privileged requests are separately bounded by the proposed
`privileged-executor-protocol-v1.md`. That proposal does not solve login or
session handoff: it depends on this document eventually defining how APX proves
that the human-facing Hub session is genuinely unlocked.

## Open Questions

- Which host authentication and recovery-credential method implements the
  proposed single owner identity?
- How are internal Environment accounts hidden without weakening security?
- Which display-manager and broker implementation best provides the proposed
  fixed transition flow?
- How does each supported desktop report unsaved-work refusal and secure lock?
- Which Hub settings survive reconstruction without preserving unsafe live Hub
  state?
- Which graphical/runtime components live on the host versus in an Environment?
- How do normal and high-security profiles affect devices and session features?
- How are future human identities and their Environment groups represented?
- What bounded permission lets the Hub request lifecycle operations?
