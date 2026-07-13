# APX Hyprland G2 Observer Source Adapters v1

Status: complete adapter and minimum-privilege proposal for repository review.
It defines read-only collection boundaries only. No collector, privileged
reader, policy, service, logout, SDDM action, DRM open, device lease, or host
change is implemented or authorized.

## Purpose

This document maps every required field in
`hyprland-g2-release-observer-schema-v1.md` to an authoritative host source and
states the least authority each adapter may receive.

The observer is not one privileged script. It has four separated trust levels:

| Level | Role | Host authority |
|---|---|---|
| U | Unprivileged collector | Read public package, login-manager, systemd, sysfs, cgroup, and own-runtime facts |
| S | Session-local KDE adapter | Connect only to the frozen outgoing user's session bus |
| P | Privileged read-only source | Read protected cross-UID `/proc` and exact resolved DRM kernel state |
| E | Privileged executor | Future effects such as SDDM quiescence, VT activation, and device grant; never used to make observation easier |

U assembles typed records. S may request graceful desktop behavior but cannot
prove release. P returns bounded typed facts and accepts no arbitrary path. E is
outside this observer and is never invoked by `read-only-preview`.

## Fixed Source Matrix

| Schema area | Adapter | Trust | Required source |
|---|---|---|---|
| Boot/time | Boot adapter | U | Kernel boot ID and monotonic clock |
| Version/provenance | Package adapter | U | Pacman local database plus executable metadata/digest |
| Seat/sessions | Login adapter | U | `org.freedesktop.login1` D-Bus properties/signals |
| SDDM/system units | System-unit adapter | U | `org.freedesktop.systemd1` read-only properties |
| KDE interface/work state | KDE adapter | S | Frozen user's D-Bus plus adapter contract |
| Cgroups/processes | Process adapter | U+P | cgroup v2 plus `/proc` identity and descriptor data |
| Wayland/desktop IPC | IPC adapter | U+P | Runtime object metadata plus owner reconciliation |
| AMD/input identity | Device adapter | U | sysfs ancestry, uevent, class, capabilities, major/minor |
| DRM users/master/leases | DRM adapter | P | Protected `/proc`, matching DRM kernel client state, login1 |
| Input users | Input adapter | U+P | sysfs identity plus protected descriptor reconciliation |
| Mounts/namespaces | Runtime adapter | U+P | cgroup membership, `/proc/<pid>/mountinfo`, namespace links |
| Recovery liveness | Recovery adapter | U | Fixed controller protocol and executor journal digest |
| Final result | Pair evaluator | U | Immutable typed records only; no host access |

No adapter may substitute a lower-authority source for a missing required
source. Missing P output produces `unknown`; U cannot infer privileged absence.

## Boot Adapter

The boot adapter reads the current kernel boot identity and monotonic time. It
does not use wall time for ordering.

It emits:

- boot identity;
- current monotonic nanoseconds;
- wall time for display only;
- current operation generation and plan digest supplied by the executor's
  already-open journal, never by the Hub;
- deadline comparison.

A boot identity change between any records invalidates the entire pair. Failure
to read the monotonic clock or journal binding is `unknown`.

## Package and Executable Provenance Adapter

The package adapter reads the local pacman database for the exact installed
package name, release, architecture, file ownership, and package metadata. It
then reads metadata and a content digest for only the frozen executables used by
the adapter plan.

It does not execute `plasmashell`, `sddm`, KWin, or another graphical binary to
discover a version. It does not query network repositories or accept a version
string from the process being inspected.

For the first fixture family it expects Plasma/KWin 6.7.2, SDDM 0.21.0, and
systemd 261.1. An exact release or executable digest outside the admitted
fixture set produces `unknown`, not automatic adaptation.

## Login and Seat Adapter

The login adapter uses read-only properties and lifecycle signals from
`org.freedesktop.login1`:

- seat `Id`, `ActiveSession`, `Sessions`, `CanTTY`, and `CanGraphical`;
- session `Id`, `User`, `Name`, `Seat`, `VTNr`/TTY, `Type`, `Class`, `State`,
  `Active`, `Remote`, `Leader`, `Scope`, `Service`, and `Desktop`;
- user `UID`, `Name`, `State`, `Linger`, `Sessions`, `Display`, `RuntimePath`,
  and `Service`;
- session/seat property changes plus session creation/removal signals during
  the observation window.

It enumerates from the seat's `Sessions` array and follows each object path. It
never starts from historical session IDs. It records the active session but
also includes inactive, online, greeter, and autologin graphical sessions.

The observer does not call `Terminate`, `Kill`, `Activate`, `SwitchTo`,
`TakeControl`, `TakeDevice`, `ReleaseDevice`, or another mutating login1 method.
Those APIs belong to separately reviewed E/device-mediator work.

The official login1 contract states that seat `Sessions` lists every current
seat session and `ActiveSession` identifies the foreground session. It also
states that device descriptors obtained by a session controller are paused when
the session becomes inactive. APX still verifies descriptors independently;
session inactivity alone is not release proof.

## System-Unit and SDDM Adapter

The system-unit adapter uses read-only `org.freedesktop.systemd1` properties for
the resolved display-manager unit, both graphical session scopes, both user
manager units, and every frozen APX control unit.

It records:

- canonical unit ID and aliases;
- load, active, and sub states;
- fragment/executable provenance;
- main PID, control group, task count, and start-time identity;
- unit relationships needed to associate SDDM helpers with session scopes;
- property-change events during both release passes.

It never calls Start, Stop, Restart, Kill, ResetFailed, SetProperty, Enable, or
another mutation. Reading `ActiveState=inactive` is insufficient when a session
scope, helper, autologin path, device owner, or user manager still exists.

Exact SDDM quiescence/restoration remains E work and is not hidden in this
adapter.

## KDE Session Adapter

S runs as the exact frozen outgoing Environment identity and connects only to
that Environment's session bus. It has no host system-bus mutation authority and
no access to another Environment bus.

For Plasma 6.7.2, read-only introspection previously found:

- `org.kde.Shutdown` at `/Shutdown`, method `logout()`;
- `org.kde.LogoutPrompt` at `/LogoutPrompt`, method `promptLogout()`.

In observation modes S records only service/object/interface presence, owner
identity, and the version-bound adapter capability. It does not call either
method.

In a future separately approved stop sequence, the exact graceful-stop method
must be frozen in the plan. A successful D-Bus return means only that the
request transport completed. S may report `ready`, `refused`, or `unknown` work
safety, but cannot report resource release.

If the outgoing bus disappears, S ends. P/U continue independent release
observation; they do not reconnect to a newly created bus under the old
generation.

## Process and Cgroup Adapter

The process adapter uses the unified cgroup hierarchy as the primary membership
boundary. It reads every frozen session scope, user manager, SDDM cgroup, APX
control cgroup, and descendant membership.

For each member it reconciles:

- PID plus process start time;
- parent PID and start time;
- UID;
- cgroup path;
- executable identity;
- mount, PID, user, IPC, UTS, cgroup, and network namespace identity digests;
- only descriptors that reference a protected DRM/input/IPC/runtime object.

U may read its own visible process/cgroup facts. P supplies the protected
cross-UID process, namespace, and descriptor facts. Process command lines,
environment, cwd, document paths, and unrelated descriptors are never returned.

The adapter repeats complete cgroup membership after enumeration. A changed
membership generation, process start-time mismatch, permission denial, vanished
process that cannot be reconciled, or list overflow produces `unknown`.

The kernel warns that the per-task children list can race and omit children.
Therefore APX does not use `/proc/<pid>/task/<tid>/children` as its sole lineage
source; cgroup membership plus process identity and protected-resource scans are
required.

## IPC Adapter

The IPC adapter accepts no path from the Hub or UI. It derives the frozen
runtime root from the authoritative UID/session record and the exact Wayland/
desktop endpoint names from the baseline.

For each reviewed endpoint it records object type, device/inode identity,
owner/mode, live owner process identity, and whether the same object remains.
It does not connect as a client during release observation, read protocol
content, enumerate window titles, or delete stale objects.

A missing baseline endpoint, replacement inode, unexpected new graphical
endpoint, owner mismatch, or incomplete owner scan produces `unknown`. A
baseline endpoint with a proven live outgoing owner produces `blocked`.

## Device Identity Adapter

The device adapter resolves from stable ancestry, never a `cardN`, `renderDN`,
connector pathname, or `eventN` supplied by another component.

For AMD it records:

- PCI function and immutable parent ancestry;
- bound driver and driver-module identity;
- resolved primary/render major/minor and sysfs links;
- connector ancestry, type, kernel object identity, and connected state;
- NVIDIA resolution solely to prove exclusion.

For input it records the built-in keyboard and ELAN touchpad ancestry,
capability digest, resolved major/minor, and hotplug generation. Every other
input device is recorded only as an excluded identity digest, not granted or
opened.

U reads sysfs metadata. Neither U nor P opens DRM/input device nodes for
identity discovery. Changed ancestry, driver, capabilities, connector, or
major/minor between baseline and a release pass is `unknown`.

## DRM Privileged Read Adapter

P is required because the current debugfs root is `0700` and cross-UID process
descriptors are protected. P is a fixed executor-owned read operation, not a
general root shell, setuid utility, group membership, ACL, debugfs chmod, or new
debugfs mount.

P receives only:

- boot and operation generation;
- stable AMD PCI/connector identity from the signed plan;
- the already resolved expected major/minor identities;
- baseline digest;
- mode and deadline.

It independently re-resolves every identity before reading. It then:

1. enumerates all host process descriptors matching the resolved primary and
   render device identities;
2. associates each descriptor with process start time, UID, cgroup, session,
   and fixed owner class;
3. reads only the matching existing kernel DRM client state;
4. identifies userspace primary clients, render clients, master indication,
   and lease evidence supported by the installed kernel;
5. cross-checks login1 seat sessions, active session, and device relationship;
6. returns only the closed DRM subrecord and reason codes.

P must not:

- run `modetest`, open a primary/render node, become DRM master, create/revoke a
  lease, switch VT, pause/resume a session, or request a logind device;
- read unrelated debugfs entries;
- accept a path, PID, UID, command, or device number from the UI;
- expose raw debugfs/proc output;
- classify an unsupported kernel field as absent.

The recovery VT may have an existing kernel console/fbdev client. P admits it
only when the baseline and installed-version fixture identify the same fixed
host kernel client and no userspace outgoing or unexpected client exists. A
changed/unclassified kernel client is `unknown`.

Lease absence is reported only when the installed-version kernel client source
explicitly proves it or when the reviewed kernel model plus a complete client
enumeration proves no lessee-capable userspace primary client exists. Otherwise
it remains `unknown`. Render-client absence is always a separate field because
render nodes are independent of DRM master.

## Input Privileged Read Adapter

The input adapter uses U for sysfs identity and P only to reconcile protected
descriptor owners for the two selected devices. P does not open an event node,
read an input event, key, pointer movement, or capability outside the selected
sysfs metadata.

It returns selected-device owner classes, login-session/cgroup relationships,
mediator lease state when that future source exists, and hotplug/identity
agreement. It never returns input contents.

An owner outside the frozen outgoing sessions is `unknown`. A complete known
outgoing owner is `blocked`. No owner plus stable identity is one required
absence field; it does not grant the device.

## Mount and Namespace Adapter

For the frozen process/cgroup set, U/P read:

- `/proc/<pid>/mountinfo` identifiers and propagation relationships;
- namespace object identities from `/proc/<pid>/ns/*`;
- Environment runtime mount roots and registration identities from the signed
  plan;
- cgroup membership before and after enumeration.

It returns only identity digests, APX lifecycle classification, and presence.
It does not expose unrelated host mount paths or Environment-private filenames.

Mount IDs may be reused. They are valid only with boot, process start time,
namespace identity, filesystem/device identity, and baseline digest. Missing
cross-UID access or a race that prevents reconciliation produces `unknown`.

## Recovery Adapter

The recovery adapter reads a fixed, authenticated, local controller endpoint
declared by the signed plan. It accepts no command through the observer path.

It returns controller build/process identity, recovery VT, watchdog generation,
heartbeat monotonic time, journal generation/effect group, bounded TTY test
result, and proof that the recovery components hold no userspace AMD/input
descriptor or lease.

The adapter does not consider the expected kernel console/fbdev client a
controller-opened DRM resource. P classifies that client separately.

Missing authentication, wrong generation/VT, stale heartbeat, journal mismatch,
or controller restart produces `unknown`.

## Pair Evaluator

The pair evaluator is a pure unprivileged component. It has no D-Bus, `/proc`,
sysfs, debugfs, device, runtime-bus, network, or filesystem discovery access. It
receives the immutable baseline and two pass records, verifies their canonical
digests, and applies only the ordered rules in the schema.

It cannot request recollection, retry a source, reinterpret an error, widen a
list, or authorize an effect. Its `next_effect_group` is `grant-exact-resources`
only for `released`; otherwise it is `none`.

## Minimum Privilege Contract

The future implementation must prove the following boundary:

| Capability | U | S | P | E |
|---|---:|---:|---:|---:|
| Read public login1/systemd/sysfs/package state | yes | no | independently recheck only | yes |
| Connect to one outgoing user bus | no | exact bus only | no | no |
| Read protected cross-UID process/fd/ns state | no | no | exact typed operation | yes |
| Read matching DRM kernel client state | no | no | exact typed operation | yes |
| Open DRM/input nodes | no | no | no | future reviewed grant only |
| Stop/kill sessions or services | no | graceful KDE request only | no | future reviewed effects only |
| Switch VT or control seat | no | no | no | future reviewed effects only |
| Accept UI paths/commands/device numbers | no | no | no | no |
| Network access | no | no | no | no for G2 |

P runs only after validating schema version, caller identity, plan/observer
digest, boot/generation, deadline, and exact allowed operation. It writes only
the bounded result into the executor journal/evidence destination. Permission
failure never triggers runtime privilege widening; it returns `unknown`.

No design requires `sudo`, a reusable root session, new group membership,
world-readable debugfs/proc state, a general polkit rule, or host device-node
mode/ACL changes.

## Bounded Collection Values

The first fixture limits are:

- 5 seconds per source adapter;
- 10 seconds for one complete observation record;
- 2 seconds minimum between release passes;
- 30 seconds from first release pass to pair evaluation;
- 4 MiB maximum canonical observation record;
- 64 seat sessions;
- 16,384 classified processes;
- 4,096 protected descriptor matches;
- 8,192 relevant mounts;
- 4,096 namespace references;
- 64 reason codes and 256 UTF-8 bytes per bounded technical detail.

These are denial limits, not truncation targets. Overflow, timeout, duplicate,
or invalid encoding produces `unknown`. Fixtures may lower them after measured
current-host evidence; no runtime path may raise them automatically.

## Required Source-Adapter Fixtures

Before a fresh read-only preview, repository fixtures must prove:

- seat enumeration includes active Development and inactive Hub sessions;
- manager-class records cannot hide graphical resources;
- every login1/systemd property type and missing-property case is closed;
- package/executable mismatch is unknown without launching the executable;
- KDE bus disappearance ends S without being treated as release;
- cgroup membership change during enumeration is unknown;
- protected `/proc` denial is unknown and never widens privilege;
- SDDM helper/autologin relationships survive process-name changes;
- the DRM adapter never opens a device and keeps master/lease/render separate;
- expected host kernel console client is distinguished from outgoing/unexpected
  clients only through a frozen fixture;
- unsupported lease evidence remains unknown;
- input adapter never reads event contents or admits excluded devices;
- mount ID reuse and namespace change are unknown;
- reboot invalidates every cached adapter result;
- every limit and source timeout fails closed;
- evaluator has no host access and only `released` selects the grant group.

## Technical Basis

The source choices follow upstream contracts:

- [systemd login manager D-Bus interface](https://www.freedesktop.org/software/systemd/man/latest/org.freedesktop.login1.html);
- [systemd process/cgroup identity APIs](https://www.freedesktop.org/software/systemd/man/latest/sd_pid_get_session.html);
- [Linux proc filesystem](https://docs.kernel.org/filesystems/proc.html);
- [Linux DRM user-space interface](https://docs.kernel.org/gpu/drm-uapi.html);
- [Linux DRM client usage](https://docs.kernel.org/gpu/drm-usage-stats.html).

Installed-version behavior still requires local fixtures. Upstream capability
does not prove that this host exposes every required field safely.

## Remaining Gate

This document closes the logical source mapping, trust separation, minimum
privilege direction, and first bounded limits. It does not implement or validate
them.

Before a physical-session preview, APX still needs:

1. pure source/evaluator fixtures for the exact installed versions;
2. a fresh post-reboot read-only preview using a non-mutating collector;
3. proof that P can return complete DRM/process/input/runtime facts without
   opening a device or exposing raw privileged data;
4. exact Plasma graceful-stop and SDDM quiescence/restoration effects;
5. recovery-controller and device-mediator design evidence;
6. fresh explicit approval for any real session/device effect.
