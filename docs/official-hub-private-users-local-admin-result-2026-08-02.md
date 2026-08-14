# Official Hub private-users and local-admin result — 2026-08-02

## Result

The exact-generation official Hub graphical launcher now runs with a private
65,536-ID user namespace and preserves Environment-local `sudo`. A graphical
terminal may elevate user `apx` to root inside the Hub; that root is mapped to
a high Host UID/GID and is not Host root.

The final physical certification returned:

- `classification=verified`;
- `private_users=true` and `local_admin=true`;
- Hyprland on `eDP-2`, two keyboards, ELAN pointer devices and Kitty ready;
- Quickshell, local playback audio and the Host service menus ready;
- AMD display rendering and NVIDIA NVK render offload ready;
- recovery to `tty1`, no machine residue and no failed unit.

The complete repository suite passes 902 tests with 11 skips.

## Cause and correction

The earlier graphical launcher disabled user namespacing and applied
`NoNewPrivileges` plus an empty capability bounding set to the final session.
That made the Hub usable graphically but prevented the set-user-ID `sudo`
binary from acquiring root authority inside the Environment.

The launcher now uses `systemd-nspawn --private-users=pick`, an idmapped Home
bind and an exact one-line 65,536-ID UID/GID map. Host-service peer checks
translate `SO_PEERCRED` Host IDs through that map and still admit only
container UID/GID 1000. Container root remains refused by the user-only Host
service.

Removing the final-session privilege block exposed a second boundary: direct
GPU and audio device access through user namespacing. Host `seatd` now brokers
only the admitted AMD primary DRM node, tty and internal input identities.
Other exact device nodes are represented by temporary private character nodes,
owned by the shifted Environment IDs and bound individually into the Hub. The
outer transient unit uses `DevicePolicy=closed` and an exact `DeviceAllow`
catalogue.

The first proxy location under `/run` failed because that filesystem is
mounted `nodev`; permissions and cgroup rules cannot override that mount flag.
Moving the temporary nodes to
`/dev/apx-official-hub-device-leases-v1` fixed AMD render access without
granting the whole `/dev/dri`, `/dev/input` or `/dev/snd` trees. The directory,
nodes, seatd socket and state are removed during every recovery.

An owner interactive entry then exposed that an auxiliary AMD-open preflight
was not authoritative. It ran in a separate transient inner service, whose
device-policy timing/context can differ from the actual compositor service,
and could refuse a launch even after repeated full certifications passed. The
synthetic preflight was removed. The fail-closed proof is now the actual
Hyprland readiness path: the compositor must initialize its renderer, publish
its socket, expose `eDP-2` and enumerate keyboards within the bounded deadline,
or the launcher performs full recovery.

The corrected installed launcher passed the complete `--test` certification
and then the real `--interactive` startup path reached the Hyprland socket
without the auxiliary AMD refusal. The controlled Host recovery returned it to
tty1 without residue. Installed/source launcher SHA-256 is
`7cb78f591254980248ffc48ef1d35caacbe849b860bab2d4186d4c319ce1ef7f`.

## Local-admin proof

Certification checks that the Hyprland process has the shifted UID 1000,
`NoNewPrivs: 0` and a non-empty capability bounding set. It temporarily adds a
single exact no-password rule for `/usr/bin/id -u`, proves that `sudo` returns
container root UID 0, proves that this root cannot call the user-only Host
service, confirms the Hub hostname, and removes the temporary rule in a
`finally` path. The real `%wheel` password-required policy and the owner's Hub
password are unchanged.

Normal use therefore remains:

```text
sudo pacman -S <package>
```

The password prompt uses the password enrolled for user `apx` inside the Hub.
Package changes affect the Hub root only.

## Host changes and final state

Signed `seatd` 0.9.3-1 remains installed on the Host as the narrowly scoped
graphical device broker. `strace` and `libunwind`, installed only for diagnosis,
were removed after the proof. Bluetooth was found powered on and certification
now restores the initial power state instead of imposing an off baseline.

Final observed state: `tty1`, official Hub stopped, Bluetooth still powered on,
no running machine, no failed systemd unit, no device-lease directory, no
seatd socket and no temporary sudoers proof.

This remains an exact-generation physical-pilot bridge, not yet the general
graphical Environment launcher or a production mechanism.
