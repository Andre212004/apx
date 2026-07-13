# APX Hyprland G2 Release Observer Schema v1

Status: complete logical schema and evaluator contract for repository review.
No observer, privileged reader, fixture, logout, SDDM action, device grant, or
host effect is implemented or authorized.

## Purpose

This schema converts the G2 KDE/SDDM release contract into one closed record
that can be evaluated without trusting a desktop response, mutable pathname,
process name, or user-supplied value.

The public result has exactly three values:

- `released`: every required absence proof passed twice in one generation;
- `blocked`: complete observations prove that a known owner or residue remains;
- `unknown`: the record is missing, contradictory, stale, changed, unsupported,
  or cannot be authoritatively collected.

Only `released` may permit the next effect group. `blocked` and `unknown` both
deny runtime creation and device grant. Neither authorizes cleanup or force.

## Reboot Rule

Every record belongs to exactly one boot. A reboot invalidates all earlier
session IDs, PIDs, VTs, device pathnames, socket identities, cgroups, deadlines,
and operation capabilities.

Historical reports remain documentation evidence only. After a reboot the
observer must create a new baseline from current host state. It must never
compare a new release pass with a baseline from an earlier boot or adopt a
matching numeric identifier as continuity.

## Closed Envelope

Every observation record contains these required top-level fields:

| Field | Contract |
|---|---|
| `schema` | Exact value `apx.g2.release-observation.v1` |
| `mode` | One of the five fixed observation modes |
| `boot_id` | Fresh host boot identity obtained by the executor |
| `operation_generation` | Fresh opaque G2 generation, never supplied by UI |
| `plan_digest` | Digest of the exact reviewed effect plan |
| `observer_digest` | Digest of the exact observer schema/build identity |
| `captured_wall_time` | Display/audit time only; never ordering authority |
| `captured_monotonic_ns` | Boot-relative ordering and deadline evidence |
| `deadline_monotonic_ns` | Fixed operation deadline |
| `source_status` | Per-source success/unknown records |
| `topology` | Seat, session, SDDM, device, and runtime observations |
| `observation_state` | Per-record `complete`, `blocked`, or `unknown` |
| `record_digest` | Digest over the canonical record without this field |

Unknown fields are rejected. Missing required fields produce `unknown`. Text
values have fixed length limits and must be valid UTF-8. Lists have explicit
maximum counts. Duplicate logical identities are invalid rather than merged.

## Observation Modes

| Mode | Purpose | May contribute to `released` |
|---|---|---|
| `read-only-preview` | Prove current sources and topology are observable without effects | No |
| `pre-stop-baseline` | Freeze every outgoing owner before the approved stop sequence | No |
| `release-pass-1` | First complete absence conjunction after graceful stop | Not alone |
| `release-pass-2` | Repeat the conjunction after the bounded stability interval | Yes, through pair evaluator |
| `return-pass` | Verify fresh Development/KDE return and zero G2 residue | No; emits return-specific status |

A record cannot change mode. Pass 1 and pass 2 are separate immutable records
joined by the evaluator through boot, generation, plan, observer, baseline, and
topology digests.

`complete` means one observation contains every required field; it does not
mean resources are released. `blocked` means this observation completely proves
a known owner/residue. `unknown` means completeness or identity cannot be
proven.

## Source Status

Each required source emits one status entry:

```text
source_id
source_kind
source_version
authority = executor | host-login-manager | kernel | user-manager
state = complete | unknown
reason_code
observation_digest
```

Allowed `source_kind` values are closed for v1:

- `package-database`;
- `login1-dbus`;
- `systemd-system-dbus`;
- `systemd-user-dbus`;
- `procfs-cgroup`;
- `procfs-descriptor`;
- `sysfs-device`;
- `kernel-drm-client`;
- `wayland-socket`;
- `mountinfo`;
- `namespace-inventory`;
- `kde-dbus-introspection`;
- `recovery-controller`.

Command output, stderr, arbitrary paths, environment variables, and unbounded
logs are not embedded. A source failure is represented by a fixed reason code
and bounded technical detail. If a required source is unavailable, the complete
result is `unknown`.

## Version Binding

The observer records package and executable provenance for the installed stack.
The first supported fixture target is the observed family:

- Plasma Workspace and KWin 6.7.2;
- SDDM 0.21.0;
- systemd/logind 261.1.

The exact installed package release and executable digest are re-read for every
preview. A newer or older version is not silently accepted. It produces
`unknown` until its source adapters and fixtures are reviewed.

Version discovery must not execute `plasmashell` or `sddm`. The 2026-07-13
observation showed their `--version` invocations are not safe in the current
graphical context. Package ownership, package version, executable metadata, and
content digest are the selected provenance inputs.

## Topology Record

The `topology` object contains exactly:

```text
seat
graphical_sessions[]
user_managers[]
display_manager
drm
input
graphical_ipc
processes_and_cgroups
mounts_and_namespaces
recovery
```

Every subrecord carries its own observation state, stable identity fields,
transient resolved fields, source references, and digest.

## Seat and Graphical-Session Discovery

The observer starts from the selected stable physical-seat identity. It asks the
host login manager for every session on that seat; it never starts from a fixed
session number.

A seat session is a `graphical_session` if any of these are true:

- type is `wayland` or `x11`;
- desktop or display-manager service identifies a graphical session;
- it owns a VT plus graphical IPC;
- it has a process, cgroup, DRM, or selected-input relationship captured by the
  observer.

An inactive or online graphical session is still included. The observed Hub
session on `tty1` is the motivating case.

Each graphical-session record requires:

- APX Environment role resolved from approved registration, or `unregistered`;
- internal account UID and immutable account/Environment mapping digest;
- login session ID, type, class, service, desktop, state, active flag, seat, VT,
  leader, and scope as transient observations;
- session cgroup identity and complete membership digest;
- user-manager identity and cgroup;
- graceful-stop adapter identity and work-safety state;
- graphical socket, DRM, selected-input, mount, namespace, helper, and assistant
  references;
- baseline presence and current release state.

An unregistered graphical session, greeter, changed account mapping, duplicate
seat owner, or graphical process outside every discovered session makes the
result `unknown`.

## User-Manager Classification

Login managers may expose a manager-class record that is not a graphical login
session. V1 recognizes it only when all of these hold:

- class is `manager` and service is `systemd-user`;
- it has no seat, VT, desktop, graphical type, or session scope;
- its leader matches the expected user manager;
- its processes are independently associated with discovered session-bound or
  admitted non-graphical units.

It is stored in `user_managers[]`, not `graphical_sessions[]`. A manager record
does not hide its processes: any surviving graphical, GPU, input, IPC, mount,
namespace, assistant, or lifecycle owner still blocks release.

## Display-Manager Record

The `display_manager` object freezes:

- unit identity, package/executable digest, load/active/sub states;
- main PID, control group, task count, and complete descendant digest;
- every SDDM helper and its associated account, session, seat, and VT;
- every greeter and autologin relationship;
- exact pre-G2 state and expected quiesced state;
- persistent configuration identity before and after the operation.

Release requires the reviewed quiesced state, zero graphical/greeter child,
zero automatic Hub activation path during the handoff, zero DRM/input owner,
and unchanged persistent configuration. An inactive service state alone is not
enough.

## Process and Cgroup Record

The baseline records stable cgroup paths plus membership identity, not process
names alone. Each process entry is bounded to:

- PID and parent PID as transient observations;
- start-time identity from the current boot;
- UID;
- cgroup and namespace identity digests;
- executable identity digest;
- fixed role classification;
- references to observed device/socket/mount ownership.

Command lines, environment, window titles, document names, and private file
paths are excluded.

Release requires zero process in every outgoing session scope, zero escaped
baseline descendant, and zero unknown process holding a protected resource.
PID disappearance without start-time and cgroup reconciliation is insufficient.

## DRM Record

The `drm` object binds the stable AMD PCI function, driver, connector ancestry,
and expected device class. Resolved `cardN`, `renderDN`, major/minor, connector
pathname, and debugfs minor are transient observations only.

It contains separate required fields:

```text
primary_descriptors = outgoing_absent | outgoing_present | unknown
render_descriptors = outgoing_absent | outgoing_present | unknown
kernel_primary_clients = expected_host_only | unexpected_present | absent | unknown
master_owner = expected_host_recovery | unexpected_present | absent | unknown
lease_tree = absent | present | unknown
login_manager_reference = absent | present | unknown
connector_identity = match | changed | unknown
nvidia_excluded = true | false | unknown
```

Every state includes bounded owner references and its authoritative sources.
The executor may read only the resolved device's kernel client state and returns
this typed summary. It must not expose debugfs, open a primary DRM node merely
to inspect it, or pass a DRM descriptor to another component during observation.

The recovery text VT may retain a version-bound kernel console/fbdev client even
though the recovery controller itself opens no DRM node. That exact host client
is frozen at baseline and may produce `expected_host_only` or
`expected_host_recovery`; it is not adopted from a changed observation.

`released` requires outgoing primary/render descriptors absent, no unexpected
kernel client or master, `lease_tree=absent`,
`login_manager_reference=absent`, connector `match`, and
`nvidia_excluded=true` in both passes. Render clients are evaluated separately
from DRM master and leases. Any unclassified kernel client is `unknown`.

## Input Record

V1 freezes a minimal allowlist by stable ancestry. The current candidate is:

- built-in keyboard beneath platform/i8042/serio0;
- built-in ELAN touchpad beneath its I2C/HID ancestry.

Observed `eventN` values are transient. The Logitech composite receiver, ELAN
mouse companion interface, power buttons, lid switch, radio controls, camera,
audio inputs, and every hotplugged device are excluded.

Each selected device records ancestry, capabilities digest, resolved node and
major/minor, current descriptor owners, login-manager reference, mediator lease
state, and hotplug generation. Any change between baseline and release passes
produces `unknown`.

Release requires zero outgoing owner and zero mediator lease before the grant
effect group. The recovery controller's TTY input is a separate host path and
does not expand this allowlist.

## IPC, Mount, and Namespace Record

Graphical IPC records object identity and live owner for the exact outgoing
Wayland/X11 and reviewed desktop endpoints. It never records contents.

Mount and namespace records are limited to Environment/runtime-owned objects
plus any object referenced by a captured outgoing process. Each entry has stable
mount/namespace identity, owner classification, lifecycle expectation, source,
and current state.

Release requires every outgoing graphical IPC endpoint absent, every captured
Environment mount/namespace absent, no unexpected new entry, and no early
Hyprland runtime.

## Recovery Record

Every baseline and release pass includes:

- recovery VT stable plan identity and current resolved VT;
- controller executable/build digest and process start-time identity;
- watchdog generation, heartbeat, and deadline state;
- executor journal generation and last completed effect group;
- bounded TTY interaction proof;
- confirmation that recovery owns no AMD or selected-input lease.

Missing heartbeat, changed process, wrong VT, journal disagreement, expired
deadline, or recovery resource conflict produces `unknown` and blocks handoff.

## Pair Evaluator

The pair evaluator accepts one baseline, pass 1, and pass 2. Evaluation order is
fixed:

1. reject schema, digest, boot, generation, plan, observer, deadline, or topology
   disagreement as `unknown`;
2. reject any missing/unknown required source or field as `unknown`;
3. reject any new/unregistered graphical session or protected owner as
   `unknown`;
4. report `blocked` when complete evidence proves an expected outgoing session,
   process, service, IPC endpoint, device owner, mount, namespace, SDDM child,
   or mediator lease remains;
5. report `unknown` when pass 2 is not after the fixed minimum stability
   interval or either pass is outside the deadline;
6. report `released` only when every required absence/match field passes in both
   observations and the recovery record remains valid.

Reason codes are cumulative and bounded. The public result follows the order
above, so an incomplete record never becomes a reassuring `blocked` result even
when one known blocker is also visible.

The evaluator publishes a separate closed record with schema
`apx.g2.release-evaluation.v1`. It contains only the boot/generation/plan/
observer identities, the three immutable input-record digests, stability timing,
the public result, bounded reason codes, next permitted effect group, and its own
record digest. No single observation record can publish `released`.

## Closed Reason Codes

V1 reason families are:

- `schema.*`;
- `identity.*`;
- `source.*`;
- `session.*`;
- `sddm.*`;
- `process.*`;
- `service.*`;
- `ipc.*`;
- `drm.*`;
- `input.*`;
- `mount.*`;
- `namespace.*`;
- `recovery.*`;
- `deadline.*`.

Examples include `session.graphical_still_present`, `sddm.autologin_path_live`,
`drm.master_unknown`, `drm.render_client_present`,
`input.ancestry_changed`, and `recovery.heartbeat_missing`. Free-form reason
codes are forbidden.

## Privacy and Evidence Limits

The observer records lifecycle identity, not activity content. It excludes:

- screenshots and screen contents;
- window titles and application documents;
- command lines and environment variables;
- clipboard, typed input, credentials, and secrets;
- general browser, assistant, or application logs;
- arbitrary home-directory paths.

The future preview must freeze maximum record bytes, list counts, string sizes,
collection time, stability interval, retention, and deletion policy. Limit
overflow produces `unknown`; truncation cannot produce `released`.

## Required Fixture Matrix

Before implementation can be considered faithful, pure fixtures must prove:

- active Development plus inactive live Hub is not released;
- manager-class session is classified separately but its resources still count;
- accepted KDE logout with either graphical session remaining is blocked;
- missing session/cgroup/DRM/input source is unknown;
- stale boot, reused PID, changed VT, or changed device pathname is unknown;
- complete residue is blocked while incomplete residue evidence is unknown;
- SDDM greeter/autologin respawn is unknown;
- primary owner, render client, master, lease, and logind-reference failures are
  independently detected;
- pass 1 clean and pass 2 dirty is blocked or unknown, never released;
- two complete clean passes before the interval are unknown;
- two complete clean passes after deadline are unknown;
- recovery heartbeat or journal mismatch is unknown;
- only a complete, stable, same-generation pair reports released;
- no non-released fixture reaches runtime creation or device grant.

## Remaining Gate

This schema closes the logical observer shape. It does not close:

- implementation and fixtures for the source/privilege mapping selected in
  `hyprland-g2-observer-source-adapters-v1.md`;
- exact SDDM quiescence/restoration operation;
- exact Plasma 6.7.2 graceful-stop behavior;
- recovery-controller implementation and rehearsal;
- device mediator selection and compatibility;
- pure evaluator implementation and fixtures;
- bounded evidence values and a fresh post-reboot read-only preview;
- explicit approval for any real session or device effect.

Until those items pass, G2 remains non-executable.
