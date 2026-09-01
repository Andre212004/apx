# Faculdade Windows 11 KVM v1 — 2026-08-22

## Clean reset — 2026-08-24

At the owner's request, the entire original Faculdade generation was
destroyed through the APX complete-purge contract. No prior qcow2, NVRAM, TPM,
snapshot or archive remains. A new generation
`ba865d3f-e592-4281-8e76-6bba8402ff2a` was provisioned with the same admitted
Portuguese Windows 11 ISO; its disk, NVRAM and TPM will be created from empty
state on first launch. Installation initially uses the direct QEMU GTK/VGA
display with Looking Glass disabled and no Host timer.

## Owner outcome

Entering the existing `faculdade` Environment opens its persistent Windows 11
virtual machine automatically and full-screen. The ordinary APX shell remains
absent: Hyprland is only the invisible physical-device/lifecycle boundary and
QEMU is the sole visible workload. `SUPER+E` opens a minimal Environment menu
and `SUPER+M` is the explicit supervised route back to the Hub. The latest
physical report says Windows did not load reliably, so the virtual-display
pilot is not considered accepted or production-ready.

## Implemented boundary

- QEMU/KVM, OVMF and `swtpm` are installed only in the `faculdade` root.
- A root-owned, mode-0400 `kvm-v1` capability marker permits only the exact
  `/dev/kvm` character device to enter that Environment.
- The guest has 12 vCPU matching the Host's 6-core/12-thread topology, 8 GiB
  RAM, a sparse 120 GiB qcow2 NVMe disk, persistent
  Secure-Boot-capable UEFI variables and a persistent TPM 2.0 state.
- Networking is unprivileged QEMU user-mode NAT; no Host bridge, inbound port,
  Host directory share, USB passthrough or Host secret is exposed.
- Graphics use the safe virtual adapter. The NVIDIA GPU is not passed through.
- The VM-only Hyprland boundary owns `SUPER+E`/`SUPER+M` and prevents the guest
  window from inhibiting them; it still starts no QuickShell.
- The physical panel is 1920x1080 at 120 Hz. The boundary selects its
  highest-refresh native mode at scale 1 and standard VGA advertises the exact
  1920x1080/120 Hz mode with 64 MiB framebuffer, avoiding blurry enlargement
  of a firmware-sized guest surface.
- AMD `topoext` exposes the 6-core/12-thread topology correctly. The qcow2 disk
  uses threaded writeback AIO after native AIO produced I/O errors on the
  Btrfs-backed Environment.
- A per-VM lock prevents duplicate starts. TPM socket and pid endpoints are
  cleaned on normal exit and before a later restart.
- The official Windows 11 Portuguese (Portugal), x64 multi-edition ISO is kept
  under `~/VMs/Windows11/Windows11.iso`. Its full downloaded SHA-256 was
  confirmed as
  `C74C96AA06E2548F14C76B5FD6600514C0D4F6EB05A731E4272AB005E8F48CE3`.

Microsoft sources:

- <https://www.microsoft.com/software-download/windows11>
- <https://learn.microsoft.com/windows/whats-new/windows-11-requirements>

Activation and any Microsoft account are owner-managed. APX does not store or
invent a product key.

The persistent VM reached the official installer, selected Windows 11 Pro and
passed the installer's hardware-requirements gate without bypasses. Its fresh
disk launcher answers the DVD's short prompt through QMP; once setup has written
substantial data, later process launches prefer the persistent NVMe disk.

## Source and live state

The versioned guest-specific launcher is
`config/environment-vm-v1/local/bin/apx-windows11-vm`; provisioning also
installs it at the stable generic entry point `~/.local/bin/apx-system-vm`.
The adjacent desktop entry is retained only as metadata and is no longer copied
to desktop autostart. A minimal VM-only Hyprland profile has no QuickShell,
bar, lock, idle daemon, portal, PulseAudio compatibility server or ordinary
desktop shortcuts; the supervised session invokes the generic launcher once,
verifies exactly one QEMU process and rejects those forbidden background
services. Native PipeWire/WirePlumber remain for guest audio, and Hyprland
remains solely as the physical display/input and `SUPER+E`/`SUPER+M` boundary.

The graphical Environment launcher recognises narrowly validated `kvm-v1` and
`virtual-machine-v1` markers. Environments without the KVM marker continue to
receive no KVM device, and ordinary graphical Environments retain QuickShell.

Deleting `faculdade` uses APX complete-purge semantics. It removes the Windows
disk, ISO, UEFI variables, TPM state, QEMU installation, KVM/VM markers, all home
data, every snapshot/archive generation, explicitly named APX maintenance
backup and stored plan for that Environment. No recoverable VM copy is retained.
Only the global audit journal keeps the non-content fact that deletion occurred.

`SUPER+E` deliberately does not reproduce the Hub's full Environment catalog.
Its APX-styled dark/cyan overlay identifies the current Environment and exposes
only `REGRESSAR AO HUB`, preserving the owner's requested one-way boundary.

## General Environment shape

The runtime and provisioning boundary is now generic for every exact
`virtual-machine-v1` Environment. Guest-specific launchers still declare:

- guest identifier and OS installer/media;
- CPU, memory and bounded sparse-disk allocation;
- firmware, Secure Boot and TPM requirements;
- network, graphics and device-sharing policy;
- whether the guest opens automatically and full-screen;
- guest shutdown, snapshot, backup and upgrade lifecycle.

The same KVM-backed shape is suitable for Ubuntu and other operating systems.
Native multiboot is not the target: it removes the live APX supervisor needed
for switching, isolation, recovery and storage ownership. The selected next
phase is the narrower native-feel VFIO/Looking Glass design in
`faculdade-native-feel-vfio-v1-2026-08-23.md`; it remains gated on a controlled
IOMMU boot, live group audit and owner-approved reboot.

## Keyboard acceptance paired with this recovery

FnLock is off. Plain F1--F12 must reach applications as ordinary function keys;
multimedia actions must occur only with Fn+F1--F12. The Lenovo ITE event stream
is observed by exact device identity for Fn actions, while the ordinary AT
keyboard remains untouched. An earlier exclusive `EVIOCGRAB` experiment was
removed because this hardware also carried ordinary keyboard input through the
grabbed interface and made the keyboard appear non-responsive. Physical owner
confirmation remains required for both the ordinary and Fn variants.
