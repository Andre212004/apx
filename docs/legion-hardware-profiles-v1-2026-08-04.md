# Lenovo Legion hardware profiles v1 — 2026-08-04

## Scope and physical evidence

This is a target-bound physical-pilot mechanism for the Lenovo Legion 5
15ACH6H (`LENOVO 82JU`, AMD `0000:05:00.0`, NVIDIA `0000:01:00.0`).  It is not
a generic laptop control API.

The running kernel exposes the Lenovo platform-profile interface with
`low-power balanced performance custom`; `balanced` was active at discovery.
The firmware Gamezone WMI interface reports Hybrid Graphics support value `2`,
current Hybrid Mode `1`, and iGPU-only support value `0`.  The NVIDIA device was
already runtime-suspended in `D3cold` while the Hub used the AMD internal
display and retained NVIDIA render offload.

Therefore the product labels have these exact meanings:

- **Hybrid**: the AMD GPU owns the display and APX leases NVIDIA render offload
  on demand.
- **NVIDIA**: Lenovo Hybrid Graphics is disabled so the discrete GPU owns the
  internal display after reboot.
- **Quiet / Normal / Performance** map to the firmware values `low-power`,
  `balanced`, and `performance`.  They apply immediately and use the laptop's
  own embedded-controller fan and power limits.
- **Display brightness** uses the exact internal AMD panel backlight
  `amdgpu_bl2` with a UI floor of 5 percent. The control-centre slider sends
  continuously throttled updates while it moves without disabling the drag,
  and F5/F6 use the same mediated path. Because this Hyprland build did not
  deliver the Lenovo brightness bindings, a Quickshell-owned bridge reads only
  the two already-admitted internal keyboards. It accepts ITE brightness codes
  224/225 and the Legion fallback F5/F6 codes 63/64, then calls the same shell
  methods that update both the bar and the physical panel.
- **Keyboard light** remains under the native Lenovo Fn+Space control. The
  compact button immediately before the screen slider cycles the exact
  `platform::kbd_backlight` levels `0 → 1 → 2 → 0`. It replaces the old
  full-width status button and mirrors the Fn+Space behavior. Its dim, cyan,
  and cyan-filled/white-icon appearances expose off, intermediate, and maximum.

## Authority and protocol

The existing exact-Hub `apx-system-power-v1` service now also exposes a closed,
typed hardware-profile surface.  Read-only status requires the authenticated
official Hub peer.  A platform-profile write additionally requires a direct
Quickshell child.  GPU writes use a Host-enforced random, single-use 30-second
confirmation tied to the same peer UID and Quickshell process.  There is no
path, arbitrary byte, shell command, fan curve, voltage, clock, or arbitrary WMI method in
the protocol.

The target-bound kernel bridge exposes only Lenovo Gamezone methods 40–42 and
63–65 under `/sys/kernel/apx_legion_gpu_profile_v1`.  It refuses non-Lenovo or
non-`82JU` systems.  The build is signed with the APX Secure Boot signing key,
installed as an out-of-tree module, loaded by `systemd-modules-load`, and
rebuilt after `linux` or `linux-headers` transactions.  This adds Host build
dependencies (`linux-headers`, `gcc`, and `make`) and taints the kernel as an
out-of-tree module.  On this Arch kernel the enrolled UEFI key is not in the
kernel module trust keyring, so the kernel logs a signature-verification taint
even though the signed module is permitted to load.  This limitation must not
be hidden or described as fully kernel-enforced module trust.

## Lifecycle and recovery

GPU selection writes the firmware target and a root-owned APX policy record,
then reports `reboot_required`.  The UI asks once before staging the change and
offers `REINICIAR AGORA` or `MAIS TARDE`; reboot itself retains the independent
system-power confirmation and inhibitor checks.  The launcher uses the prior
profile if relaunched during the same boot, then resolves the display card and
render node from the fixed PCI identity after the reboot.  It accepts exactly
one enabled internal `eDP-*` monitor rather than assuming the AMD-only
`eDP-2` name.

If the selected GPU cannot drive the Hub, tty1 remains the recovery boundary.
From the Host console, restore Hybrid Mode by loading the bridge if necessary,
writing `1` to `/sys/kernel/apx_legion_gpu_profile_v1/hybrid_mode`, removing or
correcting `/var/lib/apx/system-power-v1/hardware-profile.json`, and rebooting.
The firmware setup's Hybrid Mode control remains the independent hardware
recovery route.

No GPU mode was changed and no reboot was performed during implementation.
Hybrid and platform-profile reads passed on the physical machine.  Source and
contract tests cover the two firmware policy mappings and dynamic DRM selection; an
owner-triggered reboot into each GPU policy remains the required physical
certification.
