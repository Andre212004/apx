# APX Bluetooth control and cross-Environment handoff v1 — 2026-08-03

## Objective and current result

Bluetooth identity, discovery and pairing are machine-owned because there is
one physical controller and one Host BlueZ daemon.  The authenticated active
graphical Environment may operate that daemon only through the closed APX Host
services socket.  Pairing records and trust therefore survive an Environment
switch without copying files or exposing the Host D-Bus.

The repository implementation now extends shared-services v3 with typed power,
scan, status, connect, disconnect, remove and interactive pairing operations.
v1 and v2 remain unchanged rollback endpoints.  Installation and a real-device
physical result must be recorded below before this document may call pairing
physically certified.

## Pairing protocol

Only one pairing session may exist at a time.  `bluetooth.pair.begin` accepts a
validated uppercase Bluetooth address already present in the Host scan and
starts the fixed BlueZ `KeyboardDisplay` agent through a private pseudo-terminal.
The daemon returns only a random session identifier and sanitized phase:

- `needs-response/confirm` with the six-digit comparison value;
- `needs-response/pin` for a PIN supplied through the Unix-socket body;
- `waiting-device/display-passkey` when the value must be typed on the remote
  keyboard;
- `working`, `completed` or `failed`.

The passkey/PIN is never a command argument, environment variable, temporary
file or audit payload.  Terminal echo is disabled.  A session expires after
120 seconds, a rejected challenge is sent as `no`, and successful pairing is
followed by a fixed BlueZ trust operation.  Arbitrary BlueZ commands remain
impossible.

The common Waybar menu and Hub Quickshell invoke the same mounted v3 client and
desktop menu.  The Host still authenticates the exact active graphical peer;
an inactive Environment, Environment root, Host caller or stale generation is
refused independently of socket permissions.

## Device delivery boundary

This milestone manages the controller and durable device relationship.  It
does not pretend that every Bluetooth profile has already crossed the APX
device boundary:

- an already admitted device can be discovered, paired, trusted, connected,
  disconnected and forgotten from any active graphical Environment;
- Bluetooth HID devices create dynamic `/dev/input/event*` nodes on the Host,
  while the current launcher leases only the four exact internal input nodes at
  session start.  A later hotplug-aware, revocable input broker is required
  before Bluetooth keyboards, mice and gamepads are certified inside every
  running Environment;
- each Environment owns an independent PipeWire graph and currently receives
  exact analog ALSA nodes.  Bluetooth headset playback, microphone and profile
  switching require a separate stream/device handoff that preserves exclusive
  active-Environment authority and microphone privacy;
- file-transfer, phone integration and arbitrary BLE application APIs are not
  included and must not inherit desktop-control authority implicitly.

These are separate data-plane mechanisms, not reasons to expose the Host BlueZ
D-Bus or controller device directly to an Environment.

## Recovery and rollback

Discovery is bounded to eight seconds and is explicitly stopped afterwards.
Mutations share the existing v3 single-operation lock.  Service restart cancels
any in-memory pairing session; BlueZ remains the durable owner of completed
pairings.  Rollback restores the backed-up v3 daemon, contract, client, UI
adapter and desktop menu, restarts only `apx-host-services-v3`, and retains v2
power/connect behavior.  Existing BlueZ pairings are not deleted by rollback.

## Evidence status

Repository Python compilation and the focused contract, daemon, client,
desktop-menu and Quickshell tests pass.  Pending physical evidence is:

1. installed/source hash equality and healthy v1/v2/v3 coexistence;
2. authenticated status and an eight-second scan from the active Hub;
3. one owner-selected disposable peripheral pairing, confirmation/PIN path as
   applicable, trust, disconnect/reconnect and optional removal;
4. a Hub-to-workload-to-Hub proof showing the pairing remains Host-owned and
   the inactive socket is revoked;
5. profile-specific HID and/or audio handoff work before claiming those device
   classes work inside all Environments.
