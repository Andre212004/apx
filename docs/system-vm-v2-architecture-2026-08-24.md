# APX system VM v2 — simple near-native candidate

## Status

This is an experimental physical candidate, not production. At the owner's
explicit instruction, v2 is installed on the identity-matched disposable
physical pilot. The two prior VM Environments were completely destroyed and
recreated from the admitted Windows 11 ISO. Faculdade has reached QEMU but not
firmware or Windows; physical display, boot, input, audio and performance
acceptance remain open.

The target-bound adapter is
`scripts/physical-pilot/deploy-system-vm-v2.sh`. It must not be run during
ordinary repository work. It becomes eligible only if the owner explicitly
invokes `docs/temporary-root-host-development-mode-v1.md` as `root@apx-host`
on the identity-matched disposable pilot.

The first v16 deployment exposed one fail-closed template omission during the
first Faculdade provisioning attempt: `vfio-pci-v1.json` had not been copied
into the new template. The create wrapper immediately applied its complete
rollback and removed both unpublished subvolumes. v17 adds the exact admitted
VFIO manifest, accepts the valid zero-system-Environment migration state and
was superseded by v18's profile-access repair and v19's QEMU startup repair.
The complete suite passes 1065 tests with
11 expected skips.

Old generations `ba865d3f-e592-4281-8e76-6bba8402ff2a` (`faculdade`) and
`bd9caf9d-aa17-411e-a0e3-4c9ca21cbe2e` (`trabalho`) were removed through the
APX destroy contract, including home/root, snapshots, archives, APX-managed
backups, metadata and plans. The new stopped Windows 11 generations are:

- `faculdade`: `3a2de127-176a-457a-97b4-a3010a4ca4d2`;
- `trabalho`: `c03e65b5-3310-4ff2-8a37-165769da1205`.

Both contain the admitted Portuguese ISO with SHA-256
`c74c96aa06e2548f14c76b5fd6600514c0d4f6eb05a731e4272ab005e8f48ce3`,
the source-matched runtime/profile/Hyprland/VFIO files and a NOCOW VM
directory. Both deliberately have no raw/qcow2 guest disk, NVRAM or TPM state;
the first owner-started direct entry creates those from empty state. Historical
deployment backups bearing old names contain no qcow2/raw/ISO/NVRAM/TPM guest
content. v16/v17 backups contain only bounded code/config rollback files.
The machine-readable reset checkpoint is
`docs/system-vm-v2-physical-reset-result-2026-08-24.json`.

The first owner entry then exposed a home-provisioning permission defect before
QEMU ran. Although `system-vm-v2.json` itself was uid 1000/mode 0600, its newly
created `.config/apx` parent was root/mode 0700 because the physical
provisioner ran with a restrictive umask. v18 makes Environment-home directory
creation explicit, repairs the exact ancestor directories for both stopped
guests and records their prior metadata for rollback. A uid-1000 probe rooted
at the future `/home` bind now reads both profiles. No guest disk, NVRAM or TPM
was created by the rejected attempt; display/boot acceptance remains open.

The subsequent direct entry reached QEMU but stopped before OVMF because the
command forced `-overcommit mem-lock=on`; QEMU's whole-process `mlockall`
request was refused. v19 removes that unnecessary request while retaining the
outer 24-GiB memlock allowance required for bounded VFIO mappings. The runtime
now includes the final QEMU diagnostic in its visible failure message. The
blank raw/NVRAM/TPM/lock artefacts from that pre-firmware attempt were
validated and removed, leaving the ISO and diagnostic log intact.

The v19 retry then reached OVMF and the Windows ISO prompt, but the direct GTK
surface had `grab-on-hover=off`; the owner's key was not delivered during the
installer's short confirmation window. v20 enables hover keyboard capture for
the full-screen direct surface. This keeps boot input inside the single QEMU
window and avoids reintroducing QMP, synthetic key injection or readiness
timers. The disk was still empty and its bounded initialization artefacts were
reset once more; ISO and logs remain unchanged.

## Decision

The VM lifecycle is reduced to one ownership chain:

```text
APX handoff / systemd cgroup
  -> minimal Hyprland display and recovery boundary
    -> apx-vm-runtime-v2
      -> QEMU/KVM/VFIO
      -> Looking Glass only in explicit native mode
```

There is no second Host readiness state machine. v2 removes QMP polling,
guest-ready and presentation-ready marker files, Host-side QEMU/Looking Glass
process rediscovery, automatic source selection and nested readiness timers.
The runtime owns every child. Guest shutdown, QEMU failure or Looking Glass
exit stops the remaining children and exits the dedicated compositor; the
existing APX handoff then restores the Hub and rebinds the RTX.

This does not remove the proven APX recovery boundary. `SUPER+E` and `SUPER+M`
remain direct compositor exits and therefore do not depend on Windows, QEMU,
SPICE, Looking Glass, a menu or the broker socket.

## Presentation modes

v2 deliberately separates setup/recovery from accelerated use. It never
changes video source during one session.

### Direct

`direct` is the default for every migrated and newly provisioned guest. QEMU
owns one full-screen GTK/VGA window at 1920x1080/120 Hz. It is the predictable
path for Windows installation, driver repair and recovery. The RTX is still
assigned to the guest, but this display path is not claimed as near-native.

### Native

After Windows has the admitted NVIDIA driver, Looking Glass B7 Host and IDD,
the owner presses `SUPER+SHIFT+N`. APX records `native`, exits to the Hub, and
the next entry starts with no emulated VGA or GTK window. Windows owns the RTX;
QEMU exposes the 128 MiB KVMFR device; Looking Glass presents the KVMFR frames
full-screen on the Host AMD display. SPICE remains only as the local,
clipboard-disabled input transport. There is no SPICE VGA source from which to
switch.

`SUPER+SHIFT+R` records `direct` and exits to the Hub. It is compositor-owned,
so recovery remains available even if the guest and Looking Glass surface are
black or frozen. The next entry uses the direct surface.

The Windows `APXTools` instructions now describe this exact two-step process.
The acceleration installer does not silently choose Host presentation state.

## Resource policy

The old fixed 8-vCPU/12-GiB plan is removed. At every start the runtime reads
the CPUs and memory actually admitted by the outer cgroup.

- CPU topology is read from sysfs.
- One complete physical core, including its SMT sibling, remains outside
  QEMU for the AMD compositor, PipeWire and APX recovery.
- Every other admitted logical CPU is pinned to QEMU and represented with its
  real core/thread topology. On the target Ryzen 5 5600H the measured sibling
  pairs are `0/1`, `2/3`, `4/5`, `6/7`, `8/9`, `10/11`; QEMU gets 5 cores and
  10 threads (`0-9`), with `10/11` reserved for the Host.
- Guest RAM is the smaller of 75% of admitted memory and admitted memory minus
  5 GiB, rounded down and capped at 22 GiB. With the v2 26-GiB outer bound the
  observed target plan gives the guest 20 GiB, leaving about 7 GiB plus one physical core
  for presentation and recovery.
- QEMU uses `-cpu host`, KVM, AMD topology extensions and Windows Hyper-V
  timing enlightenments. The unit retains a 24-GiB VFIO memlock allowance,
  but QEMU does not force `mlockall` across its entire address space.

“All resources” therefore means all safe workload capacity, not starving the
Host that must display the guest and recover it. Giving the guest all 12 CPU
threads or all 27.3 GiB would make frame delivery and recovery less native,
not more.

The outer APX unit admits the target's full 1200% CPU budget, 24 GiB
`MemoryHigh`, 26 GiB `MemoryMax` and 24 GiB locked memory. The runtime applies
the narrower dynamic guest plan inside that ceiling.

## Storage and devices

New v2 guests use a sparse 160-GiB raw NVMe file. The provisioner reflinks the
verified installer ISO first, then marks the VM directory NOCOW so future raw
disk extents avoid qcow2-on-Btrfs double copy-on-write. QEMU uses native AIO,
direct caching, discard and zero detection. The rest of the Environment keeps
Btrfs checksums, snapshots, quotas and complete-purge ownership.

Existing qcow2 disks are not converted, renamed or deleted. v2 detects exactly
one legacy qcow2 and opens it with the proven threaded/writeback compatibility
settings. If raw and qcow2 both exist, startup refuses rather than guessing.
A later conversion requires a separate, owner-approved, free-space-checked
plan and benchmark.

The exact target-bound NVIDIA graphics/audio IOMMU group remains the only VFIO
lease. KVMFR is required only in native mode. Networking remains unprivileged
user-mode NAT: E1000E for Windows compatibility and VirtIO for Ubuntu. No Host
directory, general USB device, inbound port or Host secret is exposed.

Windows keeps Secure Boot OVMF and TPM 2.0. A new installer boot is no longer
tied to injected QMP keystrokes; the owner presses a key in the visible direct
window. Firmware, TPM, disk, ISO and runtime state remain inside that
Environment's existing complete-purge scope.

## Provisioning and migration

Future system Environments receive:

- one runtime at `~/.local/bin/apx-system-vm`;
- one small OS profile at `~/.config/apx/system-vm-v2.json`;
- one minimal Hyprland boundary;
- Windows-only Looking Glass and APXTools artifacts when applicable.

There are no guest-specific launcher copies, desktop autostart entry, VM
return menu or readiness files. The existing `system-environment-v1.json`
classification marker remains temporarily because it is the stable catalog
contract; it does not describe the internal runtime version.

The prepared physical adapter:

1. proves the exact disposable Host identity;
2. requires the Hub to be the sole active machine and every system Environment
   to be stopped;
3. refuses active QEMU, Looking Glass or VFIO state;
4. runs the repository test suite;
5. backs up every replaced/created file with before/after digests;
6. installs the v2 template, provisioner, Host launcher and stopped guest
   runtime/configuration;
7. initializes all migrated guests in `direct` mode;
8. does not start a VM or restart the Hub.

It preserves qcow2, raw disks, ISO, NVRAM, TPM, snapshots, archives and APX
metadata byte-for-byte.

## Failure and recovery behavior

- Missing KVM/VFIO/firmware/runtime dependencies fail before QEMU starts.
- Native mode additionally requires the admitted Looking Glass client and
  KVMFR device.
- A local VM lock makes duplicate launch requests harmless.
- Stale TPM/SPICE socket paths are removed only inside the selected VM
  directory; no process or endpoint is reused.
- Errors are appended to a 2-MiB-rotated local log, shown on an APX error
  surface, and then return to the Hub.
- Signals stop Looking Glass, QEMU and swtpm in that order, with a four-second
  TERM-to-KILL bound per child. The outer cgroup remains the final cleanup
  boundary.
- The RTX restore remains Host-owned and runs before the Environment is
  published stopped.

## Known limits and physical acceptance gate

Repository tests cannot prove firmware boot, Windows driver health, KVMFR
frames, input latency, physical 120 Hz, audio or clean RTX rebind. v2 must not
be promoted on source inspection alone.

Physical acceptance requires:

1. deploy v2 without starting a VM and verify hashes/services/VFIO-clear state;
2. perform five cold direct boots and five supervised returns;
3. complete the Windows NVIDIA/IDD/Host setup in direct mode;
4. enter native mode for five cold boots and retain objective Looking Glass
   DMA, 1920x1080/120-Hz, input and audio evidence;
5. exercise `SUPER+E`, `SUPER+M` and black-surface `SUPER+SHIFT+R` recovery;
6. shut down Windows normally and prove automatic Hub restoration;
7. measure CPU, memory, storage and frame pacing against the accepted native
   Host baseline;
8. complete-destroy a disposable v2 VM and prove no disk, firmware, TPM,
   presentation state, snapshot, archive or VFIO lease remains.

Until those checks pass, v2 is the intended replacement candidate, not the
current physical system.
