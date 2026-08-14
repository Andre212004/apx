# APX Host shared services v3 architecture and physical result — 2026-08-02

## Result

The owner-authored Hub specification at
`~/.config/quickshell/apx/HOST_SHARED_SERVICES.md` was reconciled with the APX
repository and the physical Host. A new `apx-host-services-v3` endpoint is
installed, enabled and active beside v1 and v2. Neither rollback endpoint was
disabled or changed.

The implemented first slice provides:

- a strict version-3 envelope with request IDs, structured result/error fields,
  capabilities, size limits and request timeouts;
- an authenticated Host snapshot covering detailed Wi-Fi, Bluetooth controller,
  Host time/NTP and read-only battery state;
- Wi-Fi network objects with SSID, security, normalized signal, known and
  connected state;
- scan, disconnect, forget, known/open connect and protected-network connect;
- a bounded long-poll event contract with `host.service_restarted`,
  `network.changed` and `network.scan_completed`;
- one mutation at a time, a 16-client ceiling and audit records containing the
  operation, request ID, peer PID and outcome but no payload or credential;
- a v3 client, a compatibility adapter for the current mutable Quickshell and
  v3-first/v2-fallback behavior for the existing desktop menu.

The physical bounded Hub proof returned `classification=verified`,
`host_services_v3=true` and `wifi_network_objects=true`. It also re-proved the
existing Hyprland, Quickshell, Kitty, playback audio, v1/v2 Host services,
Bluetooth power recovery, AMD display, NVIDIA NVK render, private users,
Environment-local administration, input, tty1 recovery and zero machine
residue.

## Installed boundary

- socket: `/run/apx/host-services-v3.sock`;
- daemon: `/usr/lib/apx/apx-host-services-v3.py`;
- contract: `/usr/lib/apx/apx_host_services_v3_contract.py`;
- typed client: `/usr/lib/apx/apx-host-services-client-v3.py`;
- current-UI adapter: `/usr/lib/apx/apx-host-services-ui-v3.py`;
- unit: `/etc/systemd/system/apx-host-services-v3.service`;
- service backups: `/var/lib/apx/host-services-v3/backups-20260802`;
- mutable-Hub QML backup:
  `~/.config/quickshell/apx/shell.qml.apx-backup-before-host-services-v3-20260802`.

The official Hub launcher mounts the three v3 files and socket read-only where
appropriate. The live owner QML changed only its Host client path and the
availability of protected Wi-Fi rows. Calendar, styling and other owner state
were preserved. The UI adapter continues to obtain Bluetooth data/actions from
v2 while it obtains all Wi-Fi data/actions from v3.

The socket remains mode 0666 for compatibility with dynamic private-user IDs.
This does not grant authority: the daemon independently validates `SO_PEERCRED`,
the translated container UID/GID 1000, exact root-owned active state,
registration, generation, unit cgroup and authoritative Hyprland process. Host,
inactive, Environment-root and stale-generation callers remain refused.

## Secret handling

The Quickshell adapter requests a protected-network passphrase with a no-echo
Rofi field. It passes the value to the fixed client on stdin. The client places
it only inside the bounded Unix-socket request body. The daemon validates it and
feeds `iwctl` through a private no-echo pseudo-terminal. It is never a command
argument, environment variable, notification, temporary file or audit/log
field. iwd remains the only persistent credential owner and stores the resulting
Host profile under its existing protected backend.

Enterprise/802.1X Wi-Fi is explicitly `unsupported`; the implementation does
not pretend that a personal passphrase is sufficient.

## Corrections to the Hub proposal

The document's ownership rule is accepted, but not every listed domain should
be placed in one privileged daemon:

1. Wi-Fi, Bluetooth, hardware observation and Host time are Host-owned.
2. Audio currently remains Environment-local. The physical launcher leases
   exact playback-only ALSA nodes and each Environment owns its PipeWire graph.
   Moving volume/devices to a single Host PipeWire instance requires a separate
   capture/privacy, stream-routing and revocation architecture first.
3. Power mutations, suspend/reboot and updates need separate higher-risk
   services and authorization. They must not inherit ordinary Wi-Fi status
   authority. Battery observation is safe in the v3 snapshot; brightness and
   power profiles truthfully report pending/unavailable.
4. Kernel, firmware, driver and Host package updates remain Host-owned, but the
   existing signed APX release/update journal is the design starting point. A
   generic `pacman` or shell API is prohibited.
5. Calendar, clipboard and notifications remain separate user-data contracts;
   they must not be mixed with hardware credentials.

## What is and is not certified

Certified physically:

- v1, v2 and v3 coexist and recover across service/Hub restarts;
- an authenticated Hub receives capabilities, detailed Wi-Fi status, snapshot
  and an initial event;
- scanning preserves the current network;
- Quickshell stays active with the v3 compatibility adapter mounted;
- Bluetooth power is restored to its initial state;
- network name remained `NOS-94A0`; no credential was logged.

Not yet certified physically:

- a new protected network, because no owner-approved disposable SSID and
  credential were available; unit/static tests prove the no-argv/no-file path,
  but successful iwd enrollment needs a real disposable access point;
- A-to-B persistence between two distinct graphical Environments. The current
  admitted launcher and peer proof are exact to the official Hub. The general
  graphical launcher is still absent, so claiming a two-Environment proof
  would be false;
- Bluetooth discovery/pairing, Host-global audio, brightness/power mutations or
  updates. They remain separately scoped future contracts.

## Migration and rollback

v3 is additive. v1/v2 stay enabled. The current UI adapter uses v3 only for
Wi-Fi and v2 for Bluetooth, so rollback is limited to restoring the backed-up
QML and launcher/menu, then disabling v3. No v2 removal is authorized until a
general launcher exists, at least two graphical Environments pass persistence
and revocation tests, a disposable protected Wi-Fi enrollment passes the
secret-leak audit, and Bluetooth has an admitted v3 pairing flow.

The repository suite passes 913 tests with 11 skips after this slice. Python
compilation, focused unit tests, installed/source hashes and the bounded
physical proof pass.
