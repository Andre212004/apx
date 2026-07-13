# APX Hyprland G2 Read-Only Host Observation — 2026-07-13

Status: completed non-disruptive observation of the current machine. No logout,
session stop, service action, device grant, package change, configuration
change, or persistent APX effect was requested. This is evidence for preview
design, not authorization to execute G2.

## Purpose

This observation checks whether the current Arch/KDE/SDDM host exposes the facts
required by `hyprland-g2-kde-release-proof-v1.md` without stopping a session.
It also freezes the installed component versions and identifies gaps that must
be solved before a physical-session preview.

The observations are time-bound to 2026-07-13 and must not be reused as device,
session, process, or approval identities in a later run.

## Installed Versions

The Arch package database reported:

- `plasma-workspace 6.7.2-1`;
- `kwin 6.7.2-1`;
- `sddm 0.21.0-7`;
- `systemd 261.1-1`.

`kwin_wayland --version` independently reported `kwin 6.7.2`.
`plasmashell --version` and `sddm --version` aborted in the current graphical
context, so they are not safe observer commands. The preview must use package
identity plus executable/package provenance instead of launching those binaries
for version discovery.

## Observed Login Sessions

The machine did not have only one KDE runtime.

### Development session

- session ID `4`;
- internal account `apx-development`, UID `1002`;
- active Wayland KDE session on `seat0`, `tty4`;
- service `sddm`, scope `session-4.scope`;
- session leader PID `1289` at observation time;
- `Linger=no` for UID `1002`;
- user manager `user@1002.service` remained active as expected while the
  session was active.

### Hub session

- session ID `1`;
- internal account `apx-hub`, UID `1001`;
- online but inactive Wayland KDE session on `seat0`, `tty1`;
- service `sddm-autologin`, scope `session-1.scope`;
- session leader PID `606` at observation time;
- the session scope was still active;
- its user manager still ran KWin, Xwayland, Plasma Shell, KSMServer, portals,
  PipeWire, secret storage, screen locking, and related desktop services.

The seat summary reported sessions `4` and `1`, with `4` active. Session `1` is
not a harmless historical record: it is a live inactive graphical runtime.

### User-manager record

Login-manager output also exposed ID `5` for UID `1002` with class `manager`,
type `unspecified`, service `systemd-user`, and no seat, VT, desktop, or session
scope. `session-5.scope` did not exist. The observer must classify this as the
user manager, not as a second graphical login session and not as proof of
residue by itself.

## SDDM State

SDDM was active and running as `sddm.service`/`display-manager.service`:

- main PID `562` at observation time;
- control group `/system.slice/sddm.service`;
- unit file `/usr/lib/systemd/system/sddm.service`;
- enabled state;
- 29 tasks reported during the first observation;
- separate helpers led the Hub and Development sessions.

This topology means a G2 plan cannot prove release by stopping only the
Development KDE adapter. It must safely close and independently verify both
graphical session generations, then prove SDDM cannot respawn a greeter or
autologin session before AMD KMS is granted.

No SDDM stop, quiescence, restart, or configuration operation was attempted.

## KDE Logout Interface

Read-only user-bus introspection on Plasma 6.7.2 exposed:

- service `org.kde.Shutdown`, object `/Shutdown`, method `logout()`;
- service `org.kde.LogoutPrompt`, object `/LogoutPrompt`, method
  `promptLogout()`.

Neither method was called. The future adapter must freeze which interface it
uses, its caller identity, timeout, cancellation behavior, and how it separates
transport acceptance from actual session release. Method presence is not proof
that logout is safe or complete.

## Wayland Runtime

The Development socket was `/run/user/1002/wayland-0` with:

- UID/GID `1002:1002`;
- filesystem device `70` and inode `83` at observation time;
- socket type;
- owner process PID `1441` reported at observation time.

These values confirm that socket identity is observable. They are transient and
cannot be embedded as future approval inputs.

## AMD Display Identity

The connected internal panel was observed at:

- AMD PCI function `0000:05:00.0`;
- DRM card observed as `card2`;
- connected connector observed as `card2-eDP-2`;
- render node previously established as `renderD129`.

The NVIDIA PCI function `0000:01:00.0` appeared as `card1`; its enumerated
connectors were disconnected. Mutable card and connector pathnames remain
observations only. G2 approval must bind the PCI and connector ancestry and
re-resolve their current pathnames.

## Observed AMD Device Users

Read-only descriptor inspection found current Development-session users of the
AMD nodes, including:

- Xwayland on KMS `card2` and `renderD129`;
- Plasma Shell on `renderD129`;
- Brave processes on `renderD129`;
- a KDE logout-greeter process on `renderD129` during the observation.

KWin did not appear as an ordinary `/dev/dri/*` pathname in the descriptor
scan, while the login-manager seat view still marked the AMD card and connector
as managed seat devices. Therefore `fuser` or `/proc/*/fd` absence alone cannot
prove that DRM master, a logind device reference, lease, or connector ownership
has ended. The future observer needs a second version-bound kernel/login-manager
mechanism for those facts.

A follow-up read-only check found:

- `/sys/kernel/debug` is root-only (`0700`) and the Development identity cannot
  inspect its DRM client state;
- the login-manager seat API exposes the active session plus both seat sessions,
  but not the complete DRM master/lease tree;
- `modetest` is installed but was not run because opening the primary DRM node
  is outside a strictly observational availability check.

The selected direction is therefore a narrow executor-owned observation, not a
new user permission. The future executor must enumerate every open descriptor
for the resolved primary/render device, read only the matching kernel DRM client
state when available, and cross-check the login-manager seat/session ownership.
It returns a typed summary; it never exposes debugfs or a DRM descriptor to the
Hub, adapter, or disposable Environment.

The kernel DRM model makes the distinction important: display leases form a
tree beneath a DRM master, while render-node clients are independent of DRM
master. G2 must prove zero unexpected primary/master/lease state and separately
prove zero outgoing render clients. See the upstream
[DRM user-space interface](https://docs.kernel.org/gpu/drm-uapi.html) and
[DRM client usage](https://docs.kernel.org/gpu/drm-usage-stats.html)
documentation.

## Input Identity

The current host exposes many seat input devices, including power controls,
lid switch, radio controls, camera-related USB ancestry, internal keyboard and
touchpad, and a composite Logitech receiver. A whole-seat or wildcard input
grant would therefore exceed G2.

Stable ancestry was observable for these possible minimal devices:

- built-in keyboard, observed as `event3`, under platform/i8042/serio0;
- built-in touchpad, observed as `event11`, under
  `AMDI0010:01/i2c-ELAN06FA:00/0018:04F3:31DD.0006`;
- companion ELAN mouse interface, observed as `event9`, under the same device;
- Logitech G305, observed as `event6`, beneath a composite USB receiver.

The safest initial G2 candidate is the built-in keyboard plus built-in touchpad.
It excludes the composite receiver, radio controls, power buttons, lid switch,
camera, audio input devices, and hotplug. This is a candidate allowlist, not a
device grant or final selection.

## Availability Result

| Required observation | Current result |
|---|---|
| Installed component identity | Available through package database/provenance |
| Login sessions, seat, VT, class, service, leader | Available through host login manager |
| Session and user cgroups | Available through systemd and `/proc` |
| SDDM service/cgroup/helpers | Available, but exact quiescence is untested |
| KDE logout interfaces | Present through read-only D-Bus introspection |
| Wayland socket identity/owner | Available |
| AMD PCI/card/connector ancestry | Available through sysfs/login manager |
| Ordinary DRM pathname descriptors | Partially available through `/proc`/`fuser` |
| DRM master, logind reference, lease absence | Sources identified; narrow privileged reader and exact schema not yet proven |
| Input device ancestry | Available through sysfs/login manager |
| Exact mediated input lease and revocation | Not implemented or proven |
| Mount and namespace inventory | Host tools available; schema not yet frozen |
| Recovery VT/controller | Not implemented or rehearsed |

The read-only availability gate is therefore partial, not passed.

## New Blocking Conditions

An executable G2 preview remains blocked because:

1. the inactive Hub KDE session on `tty1` is still live and must be included in
   safe work handling, graceful stop, release proof, and verified return;
2. SDDM autologin currently creates/retains that Hub session, so quiescence must
   prevent both greeter respawn and Hub autologin without persistent changes;
3. ordinary descriptor scanning does not prove complete DRM master, logind
   device, lease, and connector release; the selected privileged cross-check is
   not yet implemented or fixture-tested;
4. the exact Plasma 6.7.2 logout choice and result classification are not
   fixture-tested;
5. the recovery VT/controller and device mediator do not exist;
6. no logout, SDDM action, device grant, or physical recovery rehearsal is
   authorized by this observation.

The version-bound logical observer schema is now recorded in
`hyprland-g2-release-observer-schema-v1.md`. Its implementation, fixtures,
minimal source privileges, and a fresh post-reboot read-only preview remain
required. DRM release remains `unknown` until its privileged cross-check is
implemented and tested.
