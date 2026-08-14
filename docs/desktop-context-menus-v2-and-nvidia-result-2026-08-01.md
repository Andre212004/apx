# Desktop context menus v2 and NVIDIA physical result — 2026-08-01

## Result

The official Hub now uses ASCII context menus when the owner clicks Wi-Fi,
Bluetooth, audio, or battery in Waybar. The common `waybar-ascii-v1` seed has
the same click bindings for future Hub and normal graphical Environment config
copies. This changes presentation defaults without cloning mutable Hub state.

`apx-host-services-v2` is installed, enabled, and active beside v1 as a
rollback boundary. It authenticates the exact active official Hub with the
existing peer/cgroup/compositor proof. It accepts only typed operations:

- status, Wi-Fi scan, disconnect, and connection to a network already known by
  Host iwd;
- Bluetooth power, and connect/disconnect for an address already paired in
  Host BlueZ.

There is no arbitrary command, path, password, PIN, or shell field. Visible but
unknown Wi-Fi networks are informational. New Wi-Fi credentials and new
Bluetooth pairing need a later secret/PIN agent and are deliberately not
implemented by this protocol.

Audio remains owned by each Environment. Its menu supports mute, five-percent
volume changes, default PipeWire output selection, and optional pavucontrol.
Battery is read-only and shows charge/state because no reviewed Host power-mode
backend is installed.

## NVIDIA boundary and proof

The physical laptop contains an AMD Cezanne display GPU and NVIDIA GA106M RTX
3060. AMD continues to own the internal display. Host kernel ownership remains
with the already loaded `nouveau` driver. The launcher resolves the NVIDIA
render node from exact PCI identity `0000:01:00.0` and leases only that render
node to the Hub; it does not lease the NVIDIA card node or HDMI audio control.

The mutable official Hub has signed `vulkan-nouveau` 26.1.6-1 and diagnostic
`vulkan-tools` 1.4.350.1-1 installed locally. A bounded physical run executed
`DRI_PRIME=1! vulkaninfo --summary` inside the Hub and identified:

`NVIDIA GeForce RTX 3060 Laptop GPU (NVK GA106)`

The same run verified Hyprland, Waybar, local playback audio, authenticated v1
and v2 Host service state, the existing Bluetooth on/off recovery round trip,
Kitty, internal input, tty1 restoration, and zero machine residue.
The final repetition also proved a v2 Wi-Fi scan without changing the active
network and a v2 Bluetooth power on/off round trip with final power off.

The complete repository suite passes 897 tests with 11 skips.

Applications in the Hub can request NVIDIA render offload with `DRI_PRIME=1`;
Vulkan callers may use `DRI_PRIME=1!` to expose only the selected GPU.

## Exact current limitation

The presentation seed is ready for all newly copied graphical configurations,
but Host control and NVIDIA render access are physically active only in the
official Hub launcher. The normal graphical role still has no admitted general
device/recovery launcher; the ordinary runtime explicitly refuses graphical
activation and therefore cannot yet mount the v2 socket/menu bundle or lease a
GPU. Also, immutable `hyprland-base-v1` cannot be mutated to add NVK.

Completing all normal Environments requires two separate admitted artifacts:

1. a general exact-generation graphical launcher that publishes authenticated
   active state, mounts the v2 menu bundle, and revokes its leases on recovery;
2. a reproduced immutable successor to `hyprland-base-v1` containing the
   matching Environment-local NVIDIA userspace driver.

Until those exist, APX must not describe the menus or NVIDIA capability as
functional in arbitrary workload Environments.

## Interactive-launch correction — 2026-08-01

The first menu/NVIDIA launcher revision incorrectly ran the destructive
certification routines during every ordinary interactive Hub launch. It
therefore required Bluetooth to begin powered off, toggled it during startup,
and could refuse the desktop with `Bluetooth Host baseline differs before
toggle proof`.

The installed launcher now runs Wi-Fi scan, Bluetooth on/off cycles, and the
Vulkan proof only under explicit `--test`. `--interactive` publishes the
authenticated active session and lets Waybar observe/control the services
without imposing certification baseline state. A physical interactive run
remained active for 1 minute 54 seconds and recovered normally to tty1. The
final controller state was restored to powered off, no Environment remained,
and no systemd unit failed.
