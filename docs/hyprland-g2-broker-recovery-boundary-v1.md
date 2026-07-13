# APX Hyprland G2 Broker and Recovery Boundary v1

Status: selected candidate boundary for the G2 experiment only. It is not
implemented, does not select the production APX display manager, and does not
authorize a host, session, device, service, PAM, account, or package effect.

## Decision Summary

The first physical-session experiment will use two fixed virtual terminals
(VTs), selected and verified during a future preview:

- a host-owned recovery VT containing only a bounded text controller and its
  watchdog;
- a separate experiment VT used by the disposable Hyprland session.

The recovery VT is prepared and proven usable before KDE receives a stop
request. It does not use the AMD DRM device, the disposable root, KDE, SDDM's
greeter, networking, or another Linux account. It remains available while the
experiment VT owns the selected AMD display.

This is deliberately an experiment boundary, not the final APX experience. A
text recovery controller cannot count as the future graphical broker described
in `human-identity-and-session-handoff-v1.md`, but it can keep this destructive
hardware handoff recoverable while the product broker remains unimplemented.

## Current and Candidate Boundaries

The current machine still uses SDDM to start the Development KDE session. The
G2 candidate does not adopt SDDM as the APX broker and does not adopt `greetd`.

For a future G2 run, the boundary is:

| Component | G2 responsibility | Source of truth |
|---|---|---|
| SDDM | Current-session origin and later return target only | Observed current runtime state |
| Recovery controller | Fixed text status, bounded rollback choices, recovery VT ownership | Run-bound state and executor journal |
| Host login manager | Login-session, seat, active-VT, and device-pause observations | Host login-manager state |
| Privileged executor | Exact ordered effects, journal, device lease, revocation, teardown proof | Independently collected host state |
| KDE adapter | Graceful stop request and refusal/timeout report | KDE-specific session response |
| Hyprland adapter | Fixed launch, readiness, clean-stop request, and bounded status | Disposable runtime state |

SDDM must not respawn a greeter or another graphical session onto the physical
seat between KDE release and the verified return. Therefore a future preview
must name one version-specific, reversible way to quiesce only the current SDDM
runtime and later restore its exact prior state. That is a separately approved
temporary host effect. Persistent SDDM configuration, autologin, session files,
or package changes remain forbidden.

If no exact temporary SDDM quiescence and restoration mechanism can be proven,
G2 does not run. Starting Hyprland while an SDDM greeter owns the seat is not an
acceptable shortcut.

## Recovery VT Contract

The recovery controller is a fixed host-owned program, not a shell, login
prompt, terminal emulator, desktop, or Environment. Its interface contains only:

- current effect group and elapsed time;
- whether KDE, Hyprland, device revocation, and return are proven, failed, or
  unknown;
- cancel before the first irreversible transition, when cancellation is safe;
- request exact G2 stop and device revocation;
- retry read-only verification;
- request the reviewed SDDM/Development return sequence;
- remain locked in recovery.

It cannot accept commands, paths, device numbers, Environment names, session
commands, or policy changes from the user. It cannot force-stop, reboot,
shutdown, delete evidence, widen a device grant, or start a different session.

The controller uses its assigned kernel text VT and normal TTY input. It does
not open DRM render/KMS nodes or `/dev/input/event*`. This keeps the recovery
surface independent from the exact AMD and mediated input lease transferred to
the experiment VT.

Before KDE stop, the future executor must prove all of these in one generation:

1. the recovery and experiment VTs are distinct and neither identity changed;
2. the recovery controller is foreground on the recovery VT;
3. its watchdog and journal heartbeat are advancing;
4. the physical keyboard can invoke one bounded recovery action there;
5. the controller can request a read-only executor observation and receive the
   matching generation;
6. switching to the recovery VT does not require KDE, the disposable root,
   networking, or another account;
7. no recovery component holds the AMD KMS/render lease intended for Hyprland.

Failure of any check leaves KDE active and ends the attempt without a device
grant.

## Watchdog and Failure Ownership

The recovery controller and privileged executor have separate liveness roles.
The controller presents state and requests one of the fixed operations. The
executor owns the effect journal, deadlines, exact resource lease, revocation,
and authoritative verification.

The watchdog is armed before KDE stop. It binds the boot identity, operation
generation, recovery VT, experiment VT, outgoing session, disposable runtime,
and expected device identities. It must not discover or adopt substitutes.

On missed heartbeat, compositor exit, adapter loss, readiness timeout, or
unexpected VT/session ownership, the automatic response is limited to:

1. stop advancing the operation;
2. pause or revoke the exact G2 device lease;
3. activate the already verified recovery VT;
4. classify all unproven cleanup or ownership as uncertain;
5. expose only the bounded recovery choices.

Automatic recovery does not force KDE or Hyprland to exit and does not claim
that resources are free. If revocation cannot be proven, SDDM/KDE is not
restarted. The controller remains in recovery and preserves the journal and
runtime evidence for a separately approved decision.

If the controller itself exits, its fixed supervisor may restart only that
same controller on the same recovery VT and in recovery state. It may not
resume the interrupted effect group. A generation mismatch or unreadable
journal permits only device revocation attempts and locked recovery.

## Session and VT State Machine

```text
Development/KDE active on current VT
  -> prepare recovery controller on recovery VT
  -> verify watchdog, journal, TTY input, and bounded rollback
  -> request KDE stop
  -> prove KDE and SDDM graphical ownership absent
  -> activate experiment VT and grant exact leases
  -> start hidden disposable Hyprland
  -> reveal only after physical readiness proof
  -> request Hyprland stop
  -> revoke leases and prove zero G2 ownership
  -> restore exact SDDM runtime state
  -> freshly start and verify Development/KDE
```

Any failure after KDE stop branches to the recovery VT. No branch launches a
second graphical session while the previous owner's absence is uncertain.

The recovery controller may remain alive when Development/KDE returns only
long enough to record the final result and relinquish its run-bound capability.
It does not become a permanent background management session.

## Device Lease Boundary

The executor resolves the selected AMD PCI function, its KMS and render nodes,
the intended connector, and the selected keyboard/pointer ancestry immediately
before grant. Mutable `cardN`, `renderDN`, and `eventN` names are observations,
not approval identities.

The selected direction is a host-owned, per-run seat/device mediator that:

- has a closed allowlist derived from the approved stable identities;
- opens only the resolved devices after KDE and SDDM release are proven;
- gives the disposable session revocable file-descriptor access rather than a
  writable host `/dev` bind, ACL change, mode change, or wildcard device rule;
- denies later hotplug and every request outside the frozen allowlist;
- reports open, pause, resume, close, and client-loss events to the executor;
- is destroyed after exact revocation and zero-client verification.

The mediator is not yet selected or implemented. `seatd`, logind device APIs,
or a narrower adapter may be tested behind this contract, but compatibility
with the packaged Hyprland/libseat stack must be proven in disposable fixtures.
The candidate name alone is not evidence that the allowlist or revocation
properties exist.

The disposable Environment does not receive `/dev/input`, `/dev/dri`, udev
control, seat management, VT switching authority, or the mediator's policy
interface. It receives only the fixed session-side endpoint and the exact
revocable resources needed by the compositor.

## Authentication and Approval

G2 starts only from the currently unlocked Development session after a fresh
plain-language approval for the exact run. The recovery controller receives a
one-use, run-bound capability for safe stop, revocation, read-only inspection,
and exact return. It receives no password or reusable owner credential.

Loss of trustworthy unlock or approval state prevents retry and any new
activation. It does not prevent the watchdog from revoking the exact G2 lease
or presenting locked recovery. Production owner reauthentication remains part
of the wider session architecture and is not solved by this experiment.

## Evidence Required Before an Executable Preview

This document resolves the conceptual broker/display-manager/recovery split for
G2, but an executable preview remains blocked until the repository contains:

1. the fixed recovery-controller command and closed input/output schema;
2. a non-privileged state-machine fixture covering every transition and
   restart from every journal boundary;
3. the exact current-version SDDM quiesce, absence proof, restoration, and
   failure behavior;
4. the installed-version KDE adapter and authoritative release observations
   required by `hyprland-g2-kde-release-proof-v1.md`;
5. the exact login-session and VT creation mechanism with stable identifiers;
6. the mediator choice and disposable compatibility proof for the packaged
   Hyprland, Aquamarine, libseat, and input stack;
7. implementation evidence for the observer privilege split selected in
   `hyprland-g2-observer-source-adapters-v1.md`, plus the separate future effect
   privileges for VT activation, device lease/revocation, and SDDM control;
8. a physical recovery rehearsal that does not stop KDE or grant GPU/input and
   proves the controller remains usable after broker/adapter failure;
9. bounded logs, retention, timeout, protected-neighbour, and zero-residue
   checks;
10. an exact preview digest and fresh explicit approval for its temporary host
   effects.

No item permits implementation or host execution merely because its design is
now written down.

## Production Questions Left Open

This G2 choice does not select the production APX graphical broker, greeter,
authentication method, display manager, or recovery credential. It does not
prove that a kernel text VT is an acceptable final user experience. It narrows
one hardware experiment so the physical display cannot be handed to a
disposable compositor without an independent route back.
