# APX Host services v1 architecture and physical result — 2026-08-01

## Decision

Hardware-global desktop services live once on the Host. Environments retain
their own applications, presentation, local playback graph, and preferences,
but do not run competing Wi-Fi, Bluetooth, or kernel-time owners.

The boundary is:

1. Host backends own physical state and credentials.
2. `apx-host-services-v1` observes or applies only closed typed operations.
3. A fixed unprivileged client is mounted into the active graphical
   Environment together with the Unix socket.
4. Waybar invokes only that client; it never receives Host D-Bus, `/sys`, iwd
   credentials, a Bluetooth controller, `systemctl`, or an arbitrary command.
5. The daemon independently authenticates the exact active graphical
   generation using root-owned active state, registration state, peer UID,
   peer cgroup, compositor PID/name/cgroup, and exact unit identity.

## Physical Host backends

- Wi-Fi remains on the already installed `iwd` 3.12-1 backend. `wlan0` is
  Host-owned and connected. NetworkManager was not installed.
- Host time is owned by systemd. `systemd-timesyncd.service` is enabled and the
  physical result reached `NTP=yes`, `NTPSynchronized=yes`, timezone
  `America/Sao_Paulo`.
- BlueZ 5.87-2 and bluez-utils 5.87-2 were installed from signed Arch packages
  resolved by the existing local repository databases. Their dependency
  transaction also installed alsa-lib 1.2.16.1-1,
  alsa-topology-conf 1.2.5.1-4, and alsa-ucm-conf 1.2.16.1-1.
  `bluetooth.service` is enabled on the Host. The final controller state is
  powered off, non-discoverable, and non-pairable.

No NetworkManager, BlueZ daemon, or NTP synchronizer was installed or enabled
inside the Hub or a workload Environment by this work.

## Implemented v1 protocol

The endpoint socket is `/run/apx/host-services-v1.sock`. It accepts only:

- `status`: return sanitized network, time, and Bluetooth state;
- `bluetooth-toggle`: invert controller power and return the new sanitized
  state.

Requests contain only schema, profile, and operation. Extra fields, SSIDs,
paths, device names, commands, pairing targets, credentials, or service names
are rejected. The socket is mode 0666 only because authorization is based on
the Unix peer and trusted active-session state rather than caller-controlled
group membership. Unauthenticated Host and pre-publication Waybar calls are
closed without a response.

The systemd service has a read-only Host filesystem, protected homes, no
capability bounding set, no network address family other than AF_UNIX, and may
write only beneath `/run/apx`. Bluetooth power is requested through the Host
BlueZ D-Bus API; the daemon does not receive raw controller access or
`CAP_NET_ADMIN`.

## Waybar integration

The common `waybar-ascii-v1` seed now uses three Host-backed status modules:

- `[ WIFI <name> ]` or `[ WIFI DOWN ]`;
- `[ BT ON ]` / `[ BT OFF ]`, with click bound only to `bluetooth-toggle`;
- `[ TIME SYNC ]` / `[ TIME UNSYNC ]`.

Volume remains Environment-local through PipeWire and `wpctl`. New graphical
Environments receive independent copies of this configuration. A graphical
launcher must explicitly mount the client, pure contract module, and socket;
having the config alone grants no access.

The current official-Hub launcher performs these mounts and fails closed when
the bundle is absent. The launcher publishes active identity atomically only
after compositor, audio, and Waybar readiness, then verifies the client from
inside the Hub. Recovery removes active state and the entire container, so a
later process cannot reuse the authority.

## Physical verification

The bounded physical proof returned:

- `classification=verified`;
- `host_services=true`;
- `network_backend=iwd`;
- `ntp_enabled=true`;
- `bluetooth_backend=bluez`;
- `bluetooth_toggle=true` after an on/off round trip;
- Waybar, Hyprland, kitty, audio playback, monitor, keyboard and pointer gates
  true;
- tty1 restored and no machine residue.

The Bluetooth proof began and ended powered off. No discovery, pairing, trust,
connection, audio routing, or device credential operation occurred.

The complete repository suite passes 892 tests with 11 skips. Python
compilation, unit-file verification, JSON parsing and `git diff --check` pass.

## Deliberately pending operations

Wi-Fi management is not yet a generic `iwctl` passthrough. The next protocol
revision must separately define:

1. sanitized scan results;
2. activation of an already known Host network without exposing its key;
3. an explicit protected credential-entry flow for a new network;
4. loss-of-connectivity warning, rollback deadline, and recovery;
5. exact active-Environment authorization for future workload launchers.

Bluetooth discovery, pairing, trust, device selection and routing also remain
pending typed operations. They must expose friendly device identity without
allowing arbitrary BlueZ commands and must define where pairing credentials
and trust records live. System time has no per-Environment mutation operation;
only Host administration controls NTP or the kernel clock.
