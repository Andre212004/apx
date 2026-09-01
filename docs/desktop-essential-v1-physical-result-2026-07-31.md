# Desktop essential v1 physical result — 2026-07-31

## Owner decision

The Hub establishes the common essential desktop experience. New graphical
Environments receive the same reviewed defaults as independent copies and may
later customize their packages and configuration without changing the Hub,
the Host seed, the immutable release, or siblings. The mutable Hub filesystem
is not copied or used as a template.

## Versioned profile

`config/desktop-essential-v1/profile.json` defines the minimum local package
and control boundary. The exact root-owned installed copy is
`/usr/share/apx/profiles/desktop-essential-v1.json`.

The required package baseline is already present in the current Hub and
`hyprland-base-v1`: `iproute2`, `iputils`, PipeWire, PipeWire Audio,
PipeWire Pulse compatibility, WirePlumber, `tzdata`, and Waybar. `pavucontrol`
is installed in the current Hub and remains an optional Environment-local
advanced audio interface; basic volume and mute use `wpctl` and do not depend
on it.

The common configuration is the reviewed `waybar-ascii-v1` profile. Its Host
seed is fixed at `/usr/share/apx/config-seeds/desktop-essential-v1` and contains
only the exact Hub config, normal-Environment config, and shared stylesheet.
The runtime validates the complete entry set, regular-file type, size, and
SHA-256 digest before copying. A normal Environment gets workspaces; a future
graphical Hub gets the same design without the workspace selector.

## Control ownership

- Audio playback is Environment-local. The active graphical launcher leases
  only playback nodes, then starts local PipeWire, WirePlumber, and Pulse
  compatibility. Capture remains excluded by default.
- Network connectivity is Host-mediated and appears inside each Environment as
  private `host0`. The Environment may inspect its connection but does not run
  NetworkManager or control the physical Wi-Fi adapter directly.
- System time and NTP remain Host-owned because all Environments share one
  kernel clock. Each Environment may display time and use its own locale-facing
  applications, but it does not enable its own time synchronizer.
- Bluetooth remains `[ BT LOCKED ]`. BlueZ/Blueman alone would not create safe
  controller ownership. A future exclusive, revocable Host mediator is required
  before an Environment receives Bluetooth controls.

NetworkManager, `bluetooth.service`, and `systemd-timesyncd.service` are not
enabled as competing Environment hardware owners by this profile. Their unit
files may exist as package content; the restriction concerns activation and
ownership, not misleading claims that the files are absent.

## Automatic creation proof

The updated installed runtime has SHA-256
`1afac77654a1ee2935ee991527c396cd75024ec59984492d4eb0d1a271dc10f6`.
It applies the versioned desktop seed after the immutable release seed and
before registration publication.

Disposable `codex-test-essential-v1`, generation
`7ba06c0e-e7fe-4bb4-abcf-3d7ae5682c35`, was created normally from
`hyprland-base-v1` under plan
`ad104bc3cddff08c714b296a04c830f31a5f084ffc933c98d585b47cc69357f1`.
No manual post-creation configuration was applied. Its Waybar config and style
match the installed Host seed exactly, are mode 0600, owned by Environment UID
and GID 1000, and the registration is stopped. All required local packages are
present, the optional `pavucontrol` package is absent, and the APX recovery
journal has no uncertain operation.

The complete repository suite passed 881 tests with 11 skips at this dated
checkpoint. The newer Host-services checkpoint supersedes the current count.

## Remaining work

Superseded on 2026-08-01 for Host service ownership: the read-only Host status
endpoint, Host NTP, Host BlueZ, and the authenticated Bluetooth power toggle
are now implemented and physically verified. See
`docs/host-services-v1-architecture-and-result-2026-08-01.md`. Wi-Fi mutation
and Bluetooth pairing remain pending.

The profile makes the common current behavior automatic; it does not turn
unimplemented mediators into working controls. The next essential-control work
is a typed Host connectivity service for read-only network discovery and
owner-approved Wi-Fi changes, followed by an exclusive Bluetooth lease/proxy.
Both must authenticate the active Environment, accept no arbitrary commands or
paths, preserve credentials on the Host, and recover independently.
