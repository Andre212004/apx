# Faculdade native-feel VFIO v1 — 2026-08-23

## Decision

The target architecture remains an APX-supervised KVM guest, but replaces the
ordinary virtual display with direct NVIDIA RTX 3060 GPU assignment through
VFIO and a full-screen Looking Glass presentation on the AMD integrated GPU.
This is the closest available design to native Windows while retaining the APX
Environment boundary, instant supervised return and complete-purge lifecycle.

A hidden native dual boot is not the target. Once Windows owns the physical
machine there is no live Host supervisor able to enforce `SUPER+E`, return to
the Hub, verify isolation, or make Environment deletion an atomic APX action.
It would also introduce a reboot at every transition. A Windows-side agent
could imitate some controls, but the guest OS would then be enforcing its own
boundary and could not provide the same trust model.

## Hardware finding

The physical machine has two suitable graphics devices:

- AMD integrated graphics remains assigned to the APX Host and drives the
  physical Linux/Hyprland session;
- NVIDIA RTX 3060 Mobile graphics plus its HDMI audio function become an
  indivisible VFIO lease for `faculdade` while that Environment is active.

The CPU exposes 6 cores / 12 threads and KVM nested virtualization. IOMMU is
now enabled through the signed APX UKI with `iommu=pt`. The post-boot audit
proved that the NVIDIA graphics and audio functions are the only members of
group 11; the NVMe and AMD display remain in separate groups. No ACS override
is used.

## User experience contract

- Entering `faculdade` starts Windows as the only visible workload.
- There is no APX QuickShell, Linux bar, desktop or lock screen in that
  Environment.
- `SUPER+E` immediately requests the supervised return to the Hub.
- `SUPER+M` is a redundant direct return shortcut.
- `SUPER+SHIFT+E` opens the minimal Host-backed Environment chooser.
- The QEMU window cannot inhibit those APX shortcuts.
- Selecting another Environment performs a supervised workload-to-workload
  handoff; a failure restores the Hub instead of exposing a Host prompt.
- Deleting `faculdade` still purges the Windows disk, firmware/TPM state,
  installer media, configuration, snapshots, archives and APX metadata.

## Performance direction

The guest receives the NVIDIA GPU directly rather than rendering through a
virtual adapter. Looking Glass carries completed frames to the Host-owned AMD
display without a second physical monitor; KVMFR/DMABUF is the preferred
low-copy path. CPU pinning, huge pages and topology-aware memory allocation are
phase-two measurements, not assumptions: enable them only if benchmarks show
an improvement and the Host retains enough capacity for APX supervision.

The Windows guest requires the NVIDIA driver, Looking Glass Host, and a valid
guest display target (physical/dummy output or an indirect display driver).
The Linux side requires the Looking Glass client and a narrowly leased KVMFR
device. No Host files, USB device, secrets or inbound network are added by this
graphics change.

## Gated implementation phases

1. Enable AMD IOMMU in a reversible boot entry and reboot with owner approval.
2. Audit the live IOMMU groups and confirm that both NVIDIA functions can be
   isolated without detaching an unrelated Host device.
3. Bind the complete NVIDIA group to VFIO only for the dedicated guest path;
   preserve AMD graphics as the Host console and recovery display.
4. Install/configure Looking Glass and verify full-screen video, keyboard,
   pointer, audio, `SUPER+E`, `SUPER+M`, guest shutdown and Hub recovery.
5. Measure latency, frame pacing and CPU/memory pressure before enabling any
   optional pinning or huge-page tuning.
6. Run the complete-destroy test against a disposable VM Environment and prove
   no guest content or device lease remains.

Each phase must fail closed. In particular, an unsafe IOMMU group or failure to
recover the AMD Host display blocks GPU passthrough rather than widening the
device boundary.

## Implemented checkpoint

The v15 stabilization temporarily disables Looking Glass only for
`faculdade`, using an explicit reversible marker. Host evidence did not prove a
Windows or QEMU crash in the preceding trial; it showed an abrupt physical
reboot and retained LGMP source-loss history. Faculdade therefore uses the
direct full-screen QEMU GTK/VGA display with no SPICE-to-IDD/LGMP transition
and retains the no-Host-timer contract. Acceleration work is paused until this
baseline is physically accepted. Rollback is
`/var/lib/apx/backups/20260824-faculdade-stable-display-v15/`.

The v14 owner-directed behavior removes the VM Host deadline entirely. While
the owner session is alive, the Host waits for the launcher's QEMU/QMP and
presentation proofs without a timer; `SUPER+E` remains the explicit return.
The preceding black trial ended in a machine reboot about 27 seconds after the
request rather than a 60-second supervisor action. Looking Glass now shows its
waiting state during cold Windows/video-source startup instead of suppressing
it as a silent black screen. Rollback is
`/var/lib/apx/backups/20260824-vm-no-host-timer-v14/`.

The final v13 readiness contract removes the redundant outer Looking Glass
process lookup. The launcher owns and waits for the real client PID, publishes
presentation readiness only after QMP proves a connected SPICE channel, and
kills QEMU if the client exits. The outer Host requires QEMU plus the two exact
markers; it can no longer terminate a stable visible Windows session solely
because `/proc` identity differs across nspawn boundaries. A regression test
locks this ownership chain. Rollback is
`/var/lib/apx/backups/20260824-vm-launcher-owned-liveness-v13/`.

The inode refinement also proved unsuitable because the nspawn home uses an
idmapped mount: device/inode values are not a valid cross-namespace identity.
The installed v12 verifier instead hashes the immutable live
`/proc/<pid>/exe` content for same-sized processes in the exact outer cgroup
and compares it with the root-owned B7-799 artefact. It retains the live-client
requirement without depending on a name or mount-relative inode. Rollback is
`/var/lib/apx/backups/20260824-vm-looking-glass-content-v12/`; physical
acceptance remains owner initiated.

The next diagnostic trial isolated the remaining false recovery completely:
QEMU and both exact marker proofs were valid and no forbidden desktop service
was present, but the Host counted no Looking Glass process. The B7 executable
file is named `looking-glass-client` while Linux reports its truncated process
name as `looking-glass-c`. The Host now verifies the installed file byte-for-
byte against the root-owned APX artefact and proves the live process through
that file's exact device/inode inside the same cgroup. This is installed with
rollback at `/var/lib/apx/backups/20260824-vm-looking-glass-identity-v11/` and
awaits a >75-second owner trial.

The guest's contemporaneous "GPU not found" message did not cause this Host
recovery and occurred before the acceleration tool could run. It remains a
separate Windows driver/device check; retained earlier evidence already shows
the same guest producing B7 IDD 1920x1080 frames through DMA.

The first 2026-08-24 acceptance attempt reached a stable visible Windows
desktop and then recovered the Hub at the exact 60-second Host readiness
deadline as Space was pressed. The retained mode-0600 guest and presentation
markers prove that QMP and the connected SPICE presentation stage had already
succeeded. Space is not an APX return binding or a standard Looking Glass exit
binding, so no keyboard-trigger conclusion is made from that coincidence.

The Host had still been proving the two VM processes through Linux `comm`, a
15-byte truncated and application-renamable identity. It now requires the
exact QEMU and Looking Glass `/proc/<pid>/exe` basenames inside the same exact
Host-owned systemd cgroup. On any future timeout it also emits the observed
process counts and readiness states, removing the prior opaque rejection. The
correction is physically installed with exact rollback at
`/var/lib/apx/backups/20260824-vm-executable-readiness-v10/` and awaits an
owner-initiated retest.

The later repository candidate reserves two physical CPU cores for Host
presentation, raises Windows from 8 to 12 GiB, explicitly enables KVMFR DMA,
uses relative raw-mouse input and requires both QMP-running and an actual SPICE
presentation connection before the Host accepts the session. Its fresh-install
DVD input spans a bounded cold-OVMF window instead of relying on one exact
instant. A Windows first-login verifier applies IDD 1920x1080/120 Hz only when
advertised and records objective evidence. These changes pass the complete
repository suite and are installed in the Host template plus the existing
stopped `faculdade` and `trabalho` Environments. They are not yet physically
accepted and therefore do not supersede the last observed result below. Exact
rollback is `/var/lib/apx/backups/20260824-vm-readiness-performance-v9/`.

The 2026-08-24 repair addresses the later cold-start rollback. QMP readiness
no longer relies on one two-second `readline()`: it buffers partial messages,
skips asynchronous events and retries within a closed 30-second window. The
Host waits up to 35 seconds only for VM sessions, leaving native desktop
readiness at ten seconds. This prevents a healthy cold QEMU start from being
terminated before Looking Glass can start, without allowing an unbounded black
screen.

New VM creation is also leaner and was physically accepted end to end as the
stopped Windows 11 Environment `trabalho`. Graphical snapshots no longer
reinstall the NVIDIA/lib32 stack already present in their admitted immutable
release, and the private QEMU package transaction is a consistent full upgrade
with the required alternate-root sandbox handling. The shared Environment
shell now uses installed Kitty for `SUPER+Q`; the dedicated VM surface remains
terminal-free and keeps only its supervised return bindings.

The later 18:49 physical trial showed that the VM and accelerated source were
healthy: SPICE reached 1920x1080 and B7 received the IDD BGRA DMA frame after
23 seconds. The remaining black/warning and escape failures were deployment
identity problems. The existing generic launcher was stale, and the
`looking-glass-client` app id did not match the compositor rule intended to
forbid shortcut inhibition. The generic launcher is now synchronized with the
canonical Windows launcher, publishes `apx-system-vm`, suppresses the B7
waiting messages and is matched full-screen by class. `SUPER+E`/`SUPER+M` use
the compositor's native exit dispatcher; Host restoration therefore does not
depend on the presentation stack or Environment-switch client.

The Host now has a Secure-Boot-signed KVMFR 0.0.12 module and a persistent
128 MiB framebuffer. The B7-799 Looking Glass client was compiled against the
Faculdade userspace; the matching Windows Host and IDD installers are exposed
on the read-only `APXTools` guest drive. Both NVIDIA PCI functions successfully
bind to `vfio-pci` and restore to `nvidia`/`snd_hda_intel` in the non-graphical
self-test.

The system-Environment creator accepts `arch`, `windows11`, and `ubuntu` in its
authenticated closed contract. Windows 11 and Ubuntu 26.04 LTS installer
images live in the Host-owned verified artifact cache; the Ubuntu SHA-256 is
the exact value published by Canonical. Provisioning installs the VM engine
inside the new Environment, reflinks its selected ISO, emits root-owned
system/VFIO/KVM markers, and destroys the entire Environment automatically if
any provisioning step fails. Catalogue rows expose `WINDOWS` or `UBUNTU`
tags. Ordinary Arch Environments retain their existing presets and modules.

Two physical launch attempts failed closed before QEMU ran. The first exposed
a missing KVMFR lease-name admission; the second proved the generic launcher
was shadowed by an old sibling graphical engine. Both are corrected. The
installed generic launcher now explicitly selects the canonical `/var/lib`
engine, and both installed copies are synchronised. Further visual validation
must be initiated by the owner from the Environment menu; automated Hub exits
are prohibited because they interrupt the active collaboration session.

A subsequent owner-initiated launch found two further shared-session defects.
The session validator rejected the launcher's `vfio-guest` policy before
Hyprland could start. Its recovery did start a healthy Hub and QuickShell, but
the recently added IPC fallback treated failure of a redundant dispatch as a
session failure and ended that Hub after about 25 seconds. The repository fix
accepts `vfio-guest` only in `virtual-machine` mode, detects the Lua-started
owner workload before fallback dispatch, and makes the existing Host-side
readiness proof—not the best-effort fallback—the authority that can reject the
launch. The common Host supervisor additionally retains and reads the inner
systemd result, so an exit status 1 can no longer be misreported as a normal
owner return.

The VM path is now the generic APX system-VM runtime rather than a Faculdade
special case. It exposes only the Environment-switch broker and starts only
D-Bus, native PipeWire/WirePlumber, Hyprland, QEMU/Looking Glass and the
on-demand return menu. Looking Glass suppresses the unused GTK/VGA display;
that display exists only as the installer/recovery fallback. The next manual
visual trial remains owner-initiated to avoid interrupting maintenance. The
source and live hashes match and the complete suite passes 1056 tests with 11
expected skips.

That trial subsequently proved QEMU was still constrained by the transient
unit's inherited 8 MiB memlock limit. VFIO could not pin the 8 GiB guest RAM and
failed `vfio_container_dma_map` with `ENOMEM`, producing the reported black
surface. VFIO-only outer and inner units now carry a bounded 10 GiB memlock
ceiling. Both system launchers additionally require a QMP `running` response
before publishing readiness, so this class of early QEMU failure restores the
Hub instead of being accepted. That revision's complete suite passed 1057
tests with 11 expected skips.

The next trial made Windows visible but exposed the remaining presentation
gap: it was still the software VGA/GTK recovery window, so visible response was
not near-native even though VFIO owned the RTX. Host telemetry showed ample
idle CPU and memory, ruling out resource starvation. The installed B7 client
proves built-in SPICE recovery transport; the launcher now makes it the sole
window, uses SPICE video/input only until guest Host/IDD frames appear, and
then switches automatically to KVMFR/RTX without a manual Linux marker. GTK is
absent. QMP plus a live Looking Glass process are required before readiness.

The read-only APXTools guest drive includes `ATIVAR-ACELERACAO.cmd`, which asks
for Windows UAC, silently installs the matching verified IDD and Host packages
and schedules the required guest reboot. This guest-account confirmation is
deliberately not bypassed by the Host. The VM return surface is again top
anchored; its colours use Rofi's actual `#RRGGBBAA` ordering, and a normal
single click is explicitly accepted. The complete suite passes 1058 tests with
11 expected skips.

The 18:23 physical attempt then certified the rebuilt client boundary. With
`/dev/fuse` deliberately absent, Looking Glass stayed alive, initialized the
AMD Wayland/EGL renderer, KVMFR/LGMP, UNIX-SPICE input/video and JIT mode, and
created a 1920x1080 recovery surface. APX nevertheless recovered the guest
after ten seconds because its process verifier requested
`looking-glass-cl`; Linux exposes the executable `comm` as the 15-byte
`looking-glass-c`. The verifier now uses that exact kernel identity.

Hub recovery in the same attempt was disturbed by boot autostart's
`Restart=on-failure`: the expected external Hub stop was treated as malformed,
then autostart competed with the authenticated handoff runner. Autostart now
recognizes the trusted root-owned handoff lock before starting and after an
interrupted Hub result, returning success so only the supervisor performs the
restoration. Both fixes were deployed offline while tty1 remained active. The
complete suite now passes 1061 tests with 11 expected skips.

Owner acceptance then completed the guest-local setup. The matching B7 Host
and IDD appeared after 4m35s, published BGRA 1920x1080 frames with KVMFR DMA,
and changed input from SPICE to LGMP. During the installer-requested reboot the
source was absent for 23 seconds; SPICE recovery reconnected and accelerated
frames resumed. The Host was physically powered off at that same instant, so
the evidence contains no QEMU, Looking Glass, VFIO, or Host crash.

For a cleaner and safer repeat, B7's waiting/capture overlay is suppressed and
SPICE clipboard is explicitly disabled. `ATIVAR-ACELERACAO.cmd` now requires
an explicit Restart/Later choice and explains that a guest reboot may be black
for up to 90 seconds. `SUPER+E` and `SUPER+M` are direct compositor-owned Hub
returns throughout that interval; the blue menu is on `SUPER+SHIFT+E`.

## Primary references

- Linux kernel VFIO documentation: <https://docs.kernel.org/6.16/driver-api/vfio.html>
- Looking Glass B7 requirements: <https://looking-glass.io/docs/B7/requirements/>
- Looking Glass B7 usage: <https://looking-glass.io/docs/B7/usage/>
