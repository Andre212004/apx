# APX Hyprland G2 Exclusive Session Design v1

Status: design and acceptance contract only; no G2 preview, broker, physical
session, device grant, or host change exists or is authorized.

## Purpose

G1 proved that the disposable Hyprland role can render inside one KDE window
and can be removed without observed process or mount residue. G2 asks a
different question: can one APX Environment temporarily own the physical
display and intended input devices after the current graphical Environment has
stopped, then return control through a trusted recovery path?

G2 is not permission to expose more devices to the existing G1 container. It is
the first test of the proposed APX session-handoff boundary. A successful G2
would be evidence for one machine and one fixed hardware/software identity, not
adoption of a display manager, a production broker, or a general device policy.

## Current Reality and Proven Inputs

- SDDM and the ordinary KDE session remain the current graphical system.
- No APX broker, unlock surface, transition surface, or recovery UI exists.
- Read-only observation on 2026-07-13 found the active Development KDE session
  on `tty4` plus a live inactive Hub KDE session retained by SDDM autologin on
  `tty1`; both belong to the physical seat and must be released before G2.
- G1 passed nested Hyprland rendering and complete observed teardown.
- G0 established that the physical AMD render node alone cannot be selected as
  a compositor device by the tested Aquamarine 0.12.1 stack.
- The tested graphical root contains 332 packages and is bound to build report
  `79aec029862f03c169afde83c97a1eb3fc67918b5826823f6c5b3e1f64831f56`.
- The current machine has an AMD GPU at PCI `0000:05:00.0` and an NVIDIA GPU at
  PCI `0000:01:00.0`; transient `cardN`, render-node, connector, and input-event
  numbers are not stable identities.

None of those facts proves that the current KDE session can be safely stopped,
that the display can be recovered after a failed launch, or that raw input can
be granted without exposing unintended devices.

## Fixed Safety Boundary

The first G2 experiment, if it is later designed and separately approved, must
remain within all of these boundaries:

- one disposable runtime copy of the proven Hyprland root;
- one fixed physical seat and one selected AMD PCI device;
- no NVIDIA device;
- no network, audio, camera, microphone, removable-storage, host home, host
  D-Bus, host PipeWire, host portal, secret-service, or KDE Wayland socket;
- no persistent APX Environment, account, service, display-manager change,
  autologin change, PAM change, package change, or Btrfs operation;
- no wildcard grant of `/dev/dri`, `/dev/input`, or a whole device class;
- no adoption of a device, session, process, mount, or runtime identified only
  by a mutable pathname or process name;
- no automatic force-stop, reboot, or shutdown;
- no cleanup of uncertain state and no claim of success from disappearance of
  the graphical window alone.

The existing Development Environment and its KDE session are not disposable
test fixtures. A later execution may affect them only through an independently
reviewed stop-and-return procedure with an external recovery route.

## Required Trusted Roles

G2 requires three responsibilities that must not collapse into the disposable
Environment:

| Role | Required responsibility | Forbidden authority |
|---|---|---|
| Session broker | Own the transition/recovery display, observe the physical seat, and reveal a session only after verification | General shell, arbitrary command selection, Environment data access |
| Privileged executor | Apply the exact approved device/session plan, journal effects, verify teardown, and report authoritative state | UI-supplied paths, commands, device numbers, or self-declared success |
| Environment adapter | Start and stop the fixed Hyprland session and report bounded readiness or refusal | Declaring host seat ownership or complete teardown |

The broker must remain usable when the disposable Environment fails. Keeping a
terminal inside KDE, SSH, or the tested Environment as the only recovery route
does not satisfy this requirement.

## State and Handoff Contract

The experiment must use the session states already proposed in
`human-identity-and-session-handoff-v1.md`:

```text
environment-active (Development/KDE)
  -> stopping
  -> transition
  -> environment-active (disposable Hyprland)
  -> stopping
  -> transition
  -> environment-active (Development/KDE) or recovery
```

The broker owns `transition` and `recovery`. There is no stable or successful
state in which KDE and the disposable Hyprland session both own the physical
seat. If KDE teardown is incomplete or uncertain, G2 stops before granting KMS
or input. If Hyprland activation fails after a grant, the broker revokes the
proven G2 runtime resources, verifies their absence, and enters recovery; it
does not automatically expose a shell or retry indefinitely.

## Preconditions Before Any Executable Preview

An executable G2 preview is blocked until all of the following are fixed in the
repository:

1. Implementable evidence for the candidate broker/display-manager/login-
   session boundary selected in `hyprland-g2-broker-recovery-boundary-v1.md`,
   including exact SDDM quiescence/restoration and VT creation behavior.
2. The selected host-owned recovery-VT method tested from the physical machine
   without stopping KDE or depending on the disposable root, networking, or
   another user account.
3. Implementable evidence for the graceful-stop and authoritative release
   conjunction selected in `hyprland-g2-kde-release-proof-v1.md`, including the
   installed KDE/Plasma adapter and host-version observation mechanisms.
4. Stable resolution of the AMD PCI function to its intended KMS and render
   device identities, with connector identity and driver binding captured at
   preview time and rechecked immediately before grant.
5. A mediated seat/input design that selects only the intended physical
   keyboard and pointer. The design must account for hotplug, composite HID
   devices, virtual input devices, power buttons, and removal during the test.
6. The exact mechanism that grants and revokes KMS, render, seat, and input
   access without a writable host-device bind or an open-ended device rule.
7. A bounded readiness contract for the physical Hyprland session: expected
   compositor identity, output/connector, resolution, session ownership, and
   successful rendering, without screenshots or activity logs escaping the
   disposable evidence boundary.
8. A watchdog, timeout, journal, and recovery state machine that still works if
   the executor, adapter, compositor, container, GPU driver, or input path
   fails at each transition.
9. Exact cleanup and evidence destinations, storage and time limits, protected
   neighbours, and a separate rule for retention or deletion of evidence.
10. A plain-language preview and a fresh explicit approval for the exact host
    effect. Approval for G0, G1, package work, or documentation does not apply.

## Required Fresh Observations

The future executor must obtain these observations itself immediately around
the operation. Values copied from this document are not authoritative inputs:

- boot identity, seat identity, active login-session identities, and current
  graphical owner;
- AMD PCI identity, bound driver, DRM device numbers, connector identities,
  and device ancestry;
- intended input-device ancestry and capabilities;
- open GPU and input descriptors attributable to the outgoing and incoming
  sessions;
- cgroup, namespace, process-tree, mount, and user-service identities;
- source-root and runtime-copy identities;
- journal generation, approval freshness, and absence of another graphical
  lifecycle operation.

Any missing, conflicting, or changed observation blocks the next effect.

## Ordered Effect Groups

A future plan must journal and verify each group before advancing:

1. **Prepare recovery:** activate and verify the independent transition and
   recovery surface, watchdog, journal, and abort path.
2. **Request KDE stop:** use the reviewed desktop adapter and preserve the
   distinction between ready, known blocker, and unknown work safety.
3. **Prove release:** verify the outgoing graphical session, its device users,
   descendants, services, mounts, and seat ownership are absent. Do not infer
   release from a blank display.
4. **Create disposable runtime:** copy and verify the fixed graphical source
   within its limit, then prepare only fixed per-run configuration.
5. **Grant exact resources:** resolve and grant only the reviewed AMD and
   mediated-seat/input identities after repeating their identity checks.
6. **Start hidden:** start the Environment without revealing it as active until
   namespace, package, device, session, output, and rendering readiness pass.
7. **Reveal and bound:** reveal the physical session for the approved duration
   while the broker watches liveness and retains the recovery path.
8. **Stop and revoke:** request clean Hyprland stop, revoke the exact grants,
   and verify zero device users, processes, services, mounts, and runtime
   namespaces remain.
9. **Return or recover:** recreate and verify the Development/KDE session only
   after G2 teardown is proven. If return fails, remain in broker-owned recovery.
10. **Finalize evidence:** verify the source and protected neighbours, publish a
    bounded result, and remove the disposable runtime only when its exact
    identity and complete disuse are proven.

Effect groups are not one best-effort script. A failure after any effect creates
an incomplete journal requiring authoritative recovery classification.

## Input and Device Policy

Raw `/dev/input` exposure is forbidden. A mediated design must provide normal
keyboard and pointer use while excluding unrelated keyboards, touchscreens,
game controllers, sensors, cameras, power controls, and newly attached devices.
It must define what happens when a selected device is unplugged or a new device
appears.

KMS access is inherently broader than render-only access: it can control the
physical display associated with the selected DRM card. The G2 grant therefore
exists only while the outgoing session is proven absent and the broker owns
recovery. The Environment must not receive host device-management authority,
permission to create arbitrary device nodes, or authority to change the outer
device policy.

## Success Evidence

G2 passes only if one final, generation-bound report proves all of these:

- recovery surface and watchdog were verified before KDE stop;
- no simultaneous outgoing and incoming physical graphical session;
- outgoing KDE release was authoritative, not inferred;
- the disposable root retained the expected 332 packages and private runtime
  boundaries;
- only the resolved AMD KMS/render identities and mediated intended input were
  granted;
- NVIDIA and every forbidden path remained unavailable;
- the intended physical connector rendered the bounded Hyprland proof;
- clean stop and exact grant revocation completed;
- zero G2 process, service, namespace, mount, GPU/input descriptor, or runtime
  copy remained;
- the source graphical root and protected host neighbours remained unchanged;
- Development/KDE returned and was freshly verified, or the broker remained in
  a safe recovery state without falsely reporting success.

A safe recovery outcome is evidence that failure handling worked, but it is not
a passed graphical G2 result.

## Mandatory Failure Exercises

Before G2 can support product architecture, disposable rehearsals must cover at
least: KDE refusal, unknown work safety, timeout before release, changed GPU or
input identity, device hot-unplug, compositor failure before and after reveal,
executor failure after each effect group, broker restart, failed grant
revocation, incomplete teardown, failed KDE return, and lost unlock proof.

Uncertain device or session ownership always preserves state and enters
recovery. Force-stop, reboot, shutdown, cleanup, display-manager change, and
policy widening remain separate decisions with their normal approval strength.

## Decision Still Required

The companion `hyprland-g2-broker-recovery-boundary-v1.md` now selects a
two-VT, host-owned recovery direction and a revocable per-run device-mediator
contract for G2 only. It deliberately does not adopt SDDM, `greetd`, a
production broker, a login-session creation mechanism, a mediator
implementation, or a device-grant API. Those remaining selections and their
repository evidence are required before a faithful executable G2 preview can
be produced.

The companion `hyprland-g2-kde-release-proof-v1.md` selects the outgoing
release conjunction and two-pass stability rule. Its installed-version adapter,
observation mechanisms, evaluator fixtures, and read-only preview remain
required; the document authorizes no KDE or SDDM effect.

The companion `hyprland-g2-release-observer-schema-v1.md` closes the logical
record and evaluator shape with `released`, `blocked`, and `unknown` outcomes,
automatic discovery of every graphical seat session, separate DRM ownership
fields, and boot/generation invalidation. It is not implemented.

The companion `hyprland-g2-observer-source-adapters-v1.md` closes the logical
source and minimum-privilege mapping. Collection is split between an
unprivileged collector, exact KDE session adapter, narrow privileged read-only
source, and separately authorized effect executor. No adapter is implemented.
