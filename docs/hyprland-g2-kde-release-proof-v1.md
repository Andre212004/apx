# APX Hyprland G2 KDE and SDDM Release Proof v1

Status: selected observation and acceptance contract for the G2 experiment
only. It is not implemented and authorizes no logout, process termination,
SDDM action, device inspection, device grant, or host effect.

## Purpose

G2 may give the disposable Hyprland session physical AMD KMS and mediated
input only after the outgoing Development/KDE session and the SDDM greeter are
proven unable to own those resources. A closed window, blank display, missing
Plasma shell, adapter success response, or elapsed timeout is not that proof.

This document defines the complete release decision. Every required observation
must refer to the same boot, operation generation, outgoing session, seat, VT,
account, SDDM runtime, AMD PCI function, connector, and selected input ancestry.
One missing, changed, contradictory, or uninspectable fact produces `unknown`
and blocks the G2 device grant.

The 2026-07-13 read-only observation found both the active Development KDE
session and a live inactive Hub KDE session retained by SDDM autologin. For the
current topology, “outgoing session” therefore includes every graphical session
on the selected seat that could retain or reacquire display/input ownership.
Both must satisfy this contract before G2 can report `released`.

## Relationship to Unsaved Work

Resource release and work safety are different decisions.

Before requesting logout, the KDE adapter must report one of:

- `ready`: no known application or lifecycle blocker;
- `refused`: a known application or operation refused to close;
- `unknown`: the adapter cannot determine whether closing is safe.

`refused` and `unknown` cancel the normal G2 attempt while KDE remains active.
The release proof begins only after `ready`, the user's explicit switch
confirmation, and a verified recovery VT. Even a complete release proof cannot
claim that every application saved its content.

Force-stop is outside G2. It is not an automatic response to refusal, timeout,
adapter failure, or incomplete release.

## Frozen Outgoing Identity

Immediately before the graceful stop request, the future executor must capture
and bind at least:

- boot identity and operation generation;
- outgoing login-session ID, type, class, state, leader PID, UID, seat, and VT;
- the exact session scope/cgroup and its initial process membership;
- the Development user-manager identity, unit, cgroup, and linger state;
- the SDDM service identity, main PID, cgroup, current greeter/session children,
  and exact pre-G2 runtime state;
- KDE/Plasma adapter and version identity used for the stop request;
- the outgoing Wayland display path plus filesystem object identity;
- the AMD PCI identity, bound driver, resolved KMS/render nodes, connector, and
  current DRM users visible to the executor;
- the selected keyboard/pointer ancestry, resolved event devices, and current
  users visible to the executor;
- Environment-owned runtime directories, mounts, namespaces, helpers, and
  assistants expected to end with the session.

Mutable PID, `cardN`, `renderDN`, `eventN`, VT, and session numbers are recorded
observations. They cannot replace their stable ancestry and generation binding.

If the current session cannot be uniquely associated with the expected
Development identity, physical seat, graphical VT, SDDM lineage, and AMD
device users, the stop request is not sent.

## Graceful KDE Stop Contract

The KDE adapter supplies one fixed, version-bound graceful logout operation.
Its command, destination, arguments, timeout, expected responses, refusal
signals, and authenticated caller must be frozen in the future preview. The Hub
or recovery UI cannot supply or modify any of them.

The normal adapter path may request logout and observe its result. It may not:

- send process signals directly;
- terminate the login session through the host login manager;
- stop the user manager or SDDM itself;
- suppress application save/refusal dialogs;
- convert timeout or transport failure into success;
- retry after the outgoing identity or approval generation changes.

The stop request is sent only after the recovery controller, watchdog, journal,
and temporary SDDM quiescence are verified. Quiescing SDDM prevents a greeter
from replacing KDE on the seat; it is not evidence that KDE stopped.

Adapter outcomes are limited to `accepted`, `refused`, `timeout`, and `error`.
Only `accepted` permits the executor to begin independent release observation.
It does not itself satisfy any release gate.

## Authoritative Release Conjunction

The outgoing graphical owner is `released` only when every gate below passes.
The executor evaluates them independently from the KDE adapter.

### Login session and seat

- the frozen outgoing login-session ID no longer exists as an active, closing,
  or online session;
- no replacement graphical or greeter session appeared on the frozen seat;
- every other frozen graphical session on the seat, including the observed
  inactive Hub session, independently satisfies this complete release contract;
- the frozen VT is not owned by an outgoing or replacement graphical session;
- the host login manager reports no conflicting session/seat transition;
- the verified recovery controller remains the only permitted recovery owner.

### Process and cgroup lineage

- the frozen session scope/cgroup is absent or contains zero processes;
- every process captured in the outgoing lineage has exited;
- no descendant escaped to another cgroup or namespace during stop;
- no process with an open outgoing graphical/GPU/input resource remains merely
  because its name or parent changed;
- no APX operation relies on process-name or UID-only matching as proof.

### User services and assistants

- every session-bound graphical service and assistant captured before stop is
  inactive with an empty cgroup;
- the Development user manager has stopped when it has no other admitted login
  session and `Linger=no` applies;
- no lingering user unit, D-Bus activation, portal, PipeWire service, agent,
  container, or assistant retains an outgoing session resource;
- any admitted exception must have existed in the frozen plan and must hold no
  graphical, GPU, input, runtime, Environment-data, or lifecycle authority.

G2 v1 admits no such exception.

### Graphical IPC and runtime

- the frozen KDE Wayland socket object is absent and cannot accept a client;
- no X11, Wayland, portal, PipeWire, notification, secret-service, or desktop
  runtime endpoint from the outgoing session is adopted by the disposable root;
- captured session runtime directories contain no live socket, PID file, or
  lock whose owner still exists;
- no cleanup deletes an object merely to make this gate pass.

### AMD DRM and connector ownership

- no outgoing, SDDM, greeter, helper, or unknown process has an open descriptor
  for the resolved AMD KMS or render device;
- no captured DRM client attributable to the outgoing session remains;
- no conflicting DRM master, lease, or connector owner is reported by the
  selected host inspection mechanism;
- the AMD PCI function, driver, device ancestry, and connector identity still
  match the frozen plan;
- no NVIDIA node or unrelated DRM device became part of the operation.

Absence of a visible image, a compositor process, or one `/proc` descriptor is
not enough. The future preview must freeze the exact kernel/login-manager
observations used to prove DRM master and lease absence on the installed
versions.

The current-host direction is a narrow privileged cross-check: enumerate all
open descriptors for the resolved AMD primary/render device, inspect only its
kernel DRM client state when available, and compare it with the login manager's
active/session seat state. The executor emits a typed result and never exposes
debugfs or an open DRM descriptor. Primary/master/lease absence and render-
client absence are separate required fields.

### Input and VT ownership

- no outgoing, SDDM, greeter, helper, or unknown process retains an open
  descriptor for the selected input ancestry;
- no G2 mediator client or Environment input lease exists before the grant
  effect group;
- hotplug, removal, ancestry change, or capability change produces `unknown`;
- the outgoing session has no VT-switching or seat-control authority left.

### Mounts, namespaces, and runtime helpers

- every captured outgoing Environment mount and namespace is absent;
- every captured adapter, wrapper, nested runtime, and helper has exited;
- no subordinate container or session runtime remains registered or active;
- the disposable Hyprland runtime has not started early;
- the recovery controller and executor are the only admitted G2 control
  processes and match their frozen identities.

## Stability Window

A single clean observation may race with delayed activation or teardown. The
executor therefore records two complete release observations separated by one
fixed, bounded stability interval selected in the preview.

Both observations must:

- pass every release gate;
- have the same boot, generation, seat, VT, device, connector, and recovery
  identities;
- show no new graphical session, process, service, mount, namespace, device
  user, mediator client, or SDDM child;
- occur before the plan deadline and device grant.

The interval is a race-detection measure, not a substitute for an event or
resource proof. A timeout never converts an unknown gate into success.

## Decision Result

The release evaluator emits exactly one result:

| Result | Meaning | Next permitted action |
|---|---|---|
| `released` | Every gate passed twice in the same generation | Create runtime, re-resolve identities, then consider exact grant |
| `refused` | KDE or known work blocked normal logout | Return to unchanged KDE |
| `timeout` | Graceful stop or release proof missed its deadline | Recovery; no device grant |
| `unknown` | Any required fact is missing, changed, or contradictory | Recovery; preserve state; no device grant |
| `failed` | Adapter, executor, SDDM quiescence, or observation failed | Recovery; preserve state; no device grant |

Only `released` allows the next effect group. No user-facing button can
override this result inside G2.

## SDDM Release and Restoration

SDDM is treated separately from KDE:

- its exact pre-G2 active/inactive state and process identity are frozen;
- its reviewed temporary quiescence occurs before the KDE stop request;
- quiescence must prevent greeter/session respawn without changing persistent
  configuration;
- absence proof covers its cgroup, descendants, greeter session, DRM/input
  descriptors, and seat ownership;
- restoration occurs only after Hyprland teardown and lease revocation pass;
- restoration recreates only the frozen pre-G2 runtime state;
- a changed unit, executable, configuration identity, or unexpected child
  blocks restoration and leaves the broker in recovery.

The exact current-version quiescence and restoration operation remains a future
preview artifact and separately approved temporary host effect. This contract
does not authorize stopping or starting SDDM.

## Verified Return

Return is not proven by SDDM or KDE becoming visible. After exact SDDM runtime
restoration and a fresh Development/KDE activation, the executor must verify:

- the expected new login-session generation, seat, and VT;
- the expected SDDM-to-session lineage;
- a fresh Wayland socket identity owned by the Development session;
- the intended AMD connector and compositor readiness;
- input readiness through the normal host session path;
- absence of every G2 mediator client, device lease, process, mount, namespace,
  runtime copy, and session endpoint;
- source-root and protected-neighbour preservation.

The returned session is a new activation. Reappearance of an old PID, socket,
lease, or operation generation is a failure, not continuity.

## Failure Exercises Required

Repository fixtures must cover at least:

- KDE refusal and unknown work safety;
- adapter accepted response while KDE processes remain;
- session disappearance while its cgroup or user service remains;
- escaped descendant and changed process name;
- delayed D-Bus or user-service activation during the stability window;
- Wayland socket remaining after compositor exit;
- AMD descriptor, DRM client, master, lease, or connector mismatch;
- SDDM greeter respawn or new graphical login session;
- input hotplug, removal, or capability change;
- user manager remaining with `Linger=no`;
- hidden mount, namespace, container, or assistant residue;
- observation failure between the first and second stability pass;
- SDDM restoration mismatch and failed KDE return.

Every fixture must prove that the device-grant effect was not reached for any
result other than `released`.

## Remaining Preview Evidence

Before an executable G2 preview, the repository still needs:

1. the installed KDE/Plasma-version adapter request and response contract;
2. the exact current SDDM quiescence and restoration contract;
3. implementation and fixtures for the host source/privilege adapters selected
   in `hyprland-g2-observer-source-adapters-v1.md`;
4. implementation and fixtures for the logical observer/evaluator schema in
   `hyprland-g2-release-observer-schema-v1.md`;
5. bounded deadlines, stability interval, evidence size, and retention;
6. a non-disruptive read-only preview proving every observation is available;
7. fresh explicit approval before any real logout or SDDM action.

The current-host evidence and its limitations are recorded in
`hyprland-g2-read-only-observation-2026-07-13.md`.

The closed record shape, three-state result, two-session discovery rules, DRM
fields, reboot invalidation, and pair evaluator are recorded in
`hyprland-g2-release-observer-schema-v1.md`.

The exact logical source mapping, four trust levels, narrow privileged reader,
non-opening DRM rule, and first collection limits are recorded in
`hyprland-g2-observer-source-adapters-v1.md`.

Until all seven exist and agree, G2 cannot stop KDE or grant the physical AMD
session to Hyprland.
