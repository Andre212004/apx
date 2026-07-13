# Human Identity and Session Handoff v1

Status: product and architecture proposal complete for review; the current
machine still uses SDDM and none of this flow is implemented.

## Plain-Language Summary

The person using APX sees one owner identity and a collection of named
Environments. Internal Linux accounts remain hidden machinery.

The intended experience is:

```text
turn on -> unlock APX -> Hub -> chosen Environment -> Hub -> lock or power off
```

The Hub does not remain secretly open behind a workload Environment. APX closes
it, checks that it really stopped, and only then opens the selected Environment.
During the short changeover, a minimal protected APX transition screen shows
progress and recovery choices.

This means:

- only one ordinary graphical Environment uses the screen at a time;
- the Hub cannot watch or interfere with another Environment while hidden;
- a failed Environment does not trap the user at a broken desktop;
- APX can refuse to switch when work may be lost;
- internal Linux usernames never appear in the normal experience.

## Current Reality

SDDM is the last confirmed current display manager. It still presents normal
Linux session behavior. Current APX-related accounts are manually created and
their homes are ordinary directories beneath the existing `@home` subvolume.

No APX unlock screen, transition screen, session broker, automatic Hub entry,
Environment handoff, or recovery UI exists. `greetd` remains a candidate under
evaluation, not an adopted component.

A read-only observation on 2026-07-13 found the active Development KDE session
on `tty4` and an inactive but live Hub KDE session on `tty1` retained by SDDM
autologin. This is current-system behavior, not acceptance of simultaneous APX
graphical Environments. The G2 release contract must account for both.

## Visible Identity

V1 has one human-facing owner identity. It is not the Hub's Linux account and
not any workload account. It represents the person allowed to unlock this APX
installation and control their Environments.

The user sees:

- their chosen display name and optional avatar;
- named Environments such as Hub, University, Work, or Games;
- lock, switch, recovery, and power actions;
- clear explanations of work-loss and security consequences.

The user does not normally see:

- Linux usernames or numeric IDs;
- a list of system accounts;
- desktop-session command lines;
- container or storage identifiers;
- administrator prompts belonging to the host.

Future support for several people must add separate human identities and
ownership rules. It cannot reinterpret Environment accounts as people.

## Host Session Broker

APX requires a small host-owned session broker. It is part of the trusted APX
runtime, not an Environment and not a general desktop. Its responsibilities are
limited to:

- show unlock, transition, and recovery surfaces;
- authenticate the human through the selected host authentication method;
- start only an internally declared Environment session;
- observe session and seat state;
- coordinate stop, teardown verification, and next launch;
- return to a safe locked or recovery state after failure;
- pass bounded approval context to the privileged executor.

It cannot browse files, run arbitrary applications, provide a shell, install
software, edit Environment data, or act as the Hub management UI.

The broker's existence does not make the Hub special. The Hub remains an
ordinary recreatable Environment. The broker is comparable to the small trusted
machinery required to reach any Environment safely.

## Boot and Unlock

At boot, APX enters a locked broker-owned surface. It does not automatically
open an authenticated Hub merely because the machine has one owner.

The proposed sequence is:

1. host boot and required APX services become ready;
2. broker verifies that no stale graphical Environment remains active;
3. owner unlock surface appears without a Linux user list;
4. host authentication verifies the APX owner;
5. broker creates a short-lived host-only unlock session;
6. executor verifies the Hub registration and readiness;
7. Hub activation begins;
8. the Hub becomes visible only after activation checks succeed.

Authentication secrets never enter the Hub root/home, an Environment variable,
registration, operation journal, snapshot, or archive. The Hub receives only a
bounded statement that the owner session is currently unlocked.

The exact authentication method is open. Password, PIN, hardware token,
biometric, or recovery credentials may have different roles, but must use the
host authentication boundary and support fresh strong confirmation for
destructive actions.

## Unlock Lifetime

An unlock session belongs to one physical seat and one boot. It ends on owner
logout, explicit lock with credential disposal, broker restart that cannot
recover trustworthy state, or security-relevant identity disagreement.

Unlock does not mean unlimited approval. Opening and cleanly stopping an owned
Environment may use the unlocked session. Destruction, forced stop, and
destructive recovery still require fresh strong confirmation as defined by the
executor protocol.

Environment snapshots and restores never contain the unlock session. Restoring
the Hub cannot restore authentication or approval authority.

## Seat State Machine

The host-visible seat has these states:

| State | What the person sees | What may run |
|---|---|---|
| `locked` | APX unlock screen | broker and host services only |
| `transition` | progress, cancel where safe, recovery | broker plus bounded lifecycle operation |
| `hub-active` | Hub | one verified Hub graphical runtime |
| `hub-active-headless` | APX CLI in Hub | one verified non-graphical Hub runtime |
| `environment-active` | chosen Environment | one verified workload graphical runtime |
| `environment-active-headless` | chosen Environment console | one verified non-graphical workload runtime |
| `stopping` | saving/closing progress | current runtime while graceful stop is attempted |
| `recovery` | plain-language safe choices | broker and read-only inspection |
| `power-transition` | shutdown/restart progress | bounded host power operation |

There is never a stable state with both Hub and workload graphical sessions
active. A hidden text console or unrelated administrative login is outside the
normal APX experience and cannot be counted as a successful APX handoff. An
authenticated, broker-owned headless Hub/Environment session may count in the
CLI-first profile because it is explicitly lifecycle-managed and does not expose
host administration or ask the person to choose an internal Linux account.

## Hub to Environment

The user selects an Environment in the Hub. Selection alone does not start it.

1. Hub requests a read-only launch plan.
2. APX checks registration, storage, policy, capacity, and current session.
3. Hub explains what will close and whether uncertain work remains.
4. User confirms the switch or cancels.
5. Broker enters the protected transition screen.
6. Hub receives a graceful close request.
7. APX verifies Hub processes, mounts, services, assistants, and devices stopped.
8. Executor creates the selected Environment runtime.
9. APX verifies identity, isolation, limits, devices, and graphical readiness.
10. Only then does the broker reveal the new session.

If Hub stop cannot be proven, the workload does not launch. If workload launch
fails, APX tears down only proven new runtime state and enters recovery instead
of pretending the Hub is still safely available.

## Environment to Hub

Every supported Environment includes a small APX return action supplied through
a reviewed integration component. It asks the broker to begin a switch; it does
not receive host control.

The normal sequence mirrors Hub launch:

1. user chooses “Return to Hub”;
2. APX checks for work and explains any uncertainty;
3. user confirms or cancels;
4. broker takes over the display with the transition surface;
5. Environment is asked to close gracefully;
6. teardown is independently verified;
7. Hub is recreated from its registered state and activated;
8. Hub appears only after verification.

The Hub is not assumed to be paused in the background. Returning means a fresh
activation of the same Hub generation.

## Unsaved Work

No desktop-independent system can perfectly know whether every application has
saved its work. APX must be honest about this limitation.

Before a normal switch, APX combines:

- a session adapter's standard logout or close response;
- known applications reporting that shutdown is blocked;
- remaining graphical clients and user services;
- active terminal, package-manager, copy, archive, or assistant work when
  observable without reading private content;
- policy-defined tasks that must finish or be cancelled.

The result shown to the user is:

- **Ready to switch:** no known blocker, while still warning that applications
  control their own save behavior;
- **Work needs attention:** a known application or operation refused to close;
- **Cannot confirm:** APX cannot reliably determine whether closing is safe.

The default for the latter two is cancel and return to the current Environment.
Force-stop is a separate destructive action with fresh strong confirmation and
a clear warning that unsaved work may be lost.

APX never claims “everything is saved” merely because no process blocker was
found.

## Desktop Independence

APX defines a small session-adapter contract rather than one universal desktop
command. Hyprland, KDE Plasma, GNOME, and future desktops may implement the
contract differently.

An adapter declares:

- how its session becomes ready;
- how APX requests a normal close;
- how it reports refusal or timeout;
- how screen locking is requested and confirmed;
- which process represents session lifetime;
- how graphical clients and desktop services are enumerated;
- which features it cannot report reliably.

The broker and executor own lifecycle truth. A desktop adapter cannot declare
itself fully stopped while processes, mounts, namespaces, or device clients
remain.

## Locking

Locking is different from returning to the Hub.

For a short lock, the current Environment may remain active but its display,
input, clipboard, secrets, and user interaction must be protected by a verified
lock implementation. APX shows the human-facing owner identity, not the
Environment account.

If the active desktop cannot prove a secure lock, APX must not offer that form
of locking. The safe fallback is to warn the user, stop the Environment through
the normal flow, and return to the broker's locked state.

A future policy may stop high-security Environments whenever the screen locks.
That is safer but can lose unsaved work, so it requires a clear user setting and
pre-lock warning.

## Crash and Launch Failure

The broker watches the expected graphical session and lifecycle operation. An
unexpected exit never automatically launches another workload.

After failure it enters the recovery screen and explains:

- which Environment failed;
- whether its persistent files remain intact;
- whether runtime cleanup was verified;
- whether the Hub can be safely started;
- which actions are safe now.

Possible recovery choices are limited to:

- retry read-only checks;
- retry the same activation with a new plan and approval;
- return to a verified Hub;
- lock the computer;
- request normal shutdown or restart;
- show bounded technical details.

Force cleanup, data deletion, alternate host commands, or changing isolation
policy are not casual recovery buttons. They use the privileged executor and
their normal approval strength.

## Hub Failure and Recreation

The broker does not depend on a working live Hub. If Hub activation fails, it
can remain locked, show recovery, and offer reconstruction from the reviewed
Hub role template.

Recreation is not silent repair of unknown state. APX preserves the failed Hub
for inspection unless a separately approved operation proves replacement is
safe. Hub-only configuration that should survive recreation must be explicitly
defined and backed up; management credentials are regenerated or restored only
through their own secure policy.

No workload becomes the temporary Hub and no workload receives Hub authority.

## Power Actions

Shutdown and restart are host actions requested through the bounded executor,
not arbitrary commands supplied by a greeter or Environment.

If an Environment is active, APX first performs the same work check and graceful
stop used for returning to Hub. Known refusal or uncertainty is shown to the
user. Forced power action requires strong confirmation and explains possible
data loss.

The power result is not reported successful merely because the graphical
session disappeared.

## Display-Manager Direction

The preferred clean bootstrap initially needs no display manager. It uses the
host-owned bootstrap/recovery console, then lifecycle-managed headless Hub and
Environment sessions. H0 adds the first graphical owner only after this path is
proven.

The selected display/session manager must support host authentication, proper
login-session creation, seat ownership, a fixed APX broker command, hidden
internal accounts, and reliable session exit reporting.

`greetd` remains the preferred lightweight candidate to test because its model
can start a fixed session after authentication. This is not adoption. A normal
greeter that permits users, sessions, or commands to be selected would violate
the APX experience unless those choices are disabled and the APX broker retains
control.

SDDM remains the current factual system and must not be changed until a separate
repository-reviewed experiment and explicit host approval.

For the narrower G2 hardware experiment only,
`hyprland-g2-broker-recovery-boundary-v1.md` selects a host-owned text recovery
VT and a separate compositor VT as the candidate failure boundary. That test
surface is not the final graphical APX broker and does not resolve the product
display-manager or authentication decisions in this document.

For the same experiment, `hyprland-g2-kde-release-proof-v1.md` defines the
independent release conjunction. A desktop adapter may request graceful logout,
but only the executor's repeated session, process, service, IPC, device, VT,
mount, namespace, and SDDM observations can permit the next activation.

## Privacy

The broker records lifecycle facts, not user activity. It may record owner
identity reference, Environment ID, transition result, timing, refusal class,
and sanitized failure reason. It does not record document names, window titles,
typed credentials, clipboard content, screenshots, assistant conversations, or
general application logs.

## Failure Rules

- Authentication failure remains locked and starts no Environment.
- Hub failure enters recovery rather than exposing internal accounts.
- Incomplete stop blocks the next Environment.
- Incomplete activation never becomes visible as a trusted active session.
- Unknown session ownership is never adopted as APX state.
- Work-loss uncertainty defaults to cancellation, not force.
- Loss of the unlock proof requires authentication again.
- Broker failure falls back to a locked or non-graphical recovery path, not an
  automatic shell.

## Acceptance Gates

Before implementation:

1. Select the host authentication and recovery-credential method.
2. Define the broker, executor, display-manager, and login-session boundary.
3. Test a fixed broker session without exposing user/session/command selection.
4. Define and fixture-test the desktop adapter for one minimal Wayland session.
5. Prove Hub-to-workload and workload-to-Hub failure recovery.
6. Test refusal, timeout, crash, broker restart, lock failure, and force-stop.
7. Prove no simultaneous Hub/workload graphical runtime or surviving assistant.
8. Validate Hyprland, KDE Plasma, and GNOME adapters separately.
9. Design Hub reconstruction and recovery credentials without copying live Hub
   authority into templates.
10. Review the complete experience in plain language with explicit data-loss
    warnings.

No gate authorizes changing SDDM, PAM, system services, users, or the real host.

## Technical Basis

The design relies on the host login manager for authoritative session and seat
observation. Upstream systemd documents activation, locking, termination,
session properties, and the distinction between session-manager requests and
authoritative process/resource teardown:

- [systemd login session control](https://www.freedesktop.org/software/systemd/man/latest/loginctl.html)
- [systemd logind interface](https://www.freedesktop.org/software/systemd/man/latest/org.freedesktop.login1.html)

Candidate-specific behavior must be frozen to the versions used by a future
experiment.
