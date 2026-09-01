# APX Project State

This is the canonical continuity document for APX. Future work must read it
before proposing or making changes. Any change to the product objective,
development method, confirmed architecture, or accepted deviation must update
this file in the same change.

`CURRENT_HANDOFF.md` is now the concise companion for cross-chat continuity.
It records the latest owner-reported physical checkpoint, next expected audit,
active safety blocks, and immediate repository milestone. `AGENTS.md` requires
future sessions to read both files. The handoff never overrides this canonical
state; disagreement must be resolved explicitly.

## QuickShell popup interaction candidate — 2026-09-01

The owner reported three coupled regressions in the shared QuickShell menus:
the menu surface appeared too transparent, clicking a bar button did not move
keyboard navigation away from the terminal, and clicking outside QuickShell
did not close the menu. The repository candidate moves Control Centre action
surfaces from saturated blue to the same neutral dark palette as the other
menus. After visual follow-up, the owner selected one consistent opacity for
both surfaces: the bar and menus use `#d90a1014` (85% alpha). The Calendar
month grid alone sits on the existing higher-opacity `root.card` surface with
a neutral border, improving date readability without making the whole popup
opaque.

Calendar keyboard focus is grouped by visible row. Left/right move only inside
the month-navigation pair, Day/Month/Year tabs, current calendar row, or
Today/New Event pair. Up/down move between those groups; within the month grid
they advance by seven days, entering the adjacent group at the first or last
week. A fresh opening resets the month view and focuses today's exact date.
The Environments focus list now begins with index `-1`, the active HUB card;
Down continues into the Environment catalogue and action row.

Bar buttons invoke their toggle on pointer press, before a popup focus change
can cancel a release-time tap; the TapHandler itself also keeps the pointing
hand cursor. The display-brightness card no longer carries a one-off blue-grey
surface and instead uses the shared neutral Control Centre palette.

Every mouse or IPC bar opening now requests exclusive layer-shell keyboard
focus for the menu lifetime. Outside-click dismissal no longer depends on an
application accepting focus while that exclusive claim is active: a
transparent, non-keyboard Top-layer surface covers only the application area,
sits below the Overlay popup and closes the popup on its first click. The bar
is excluded from that surface so its own buttons retain their established
toggle behavior. `HyprlandFocusGrab` remains a secondary compositor cleanup
boundary.

The owner explicitly authorized a shell-only physical exception from the
dirty-checkout refusal. The current Hub file and source match SHA-256
`5b4973d5db51207aed683dc0979b288ca54ace5b9b4556dcbdbdc2efa5112c36`;
rollback is `/var/lib/apx/backups/20260901T004406Z-quickshell-popup-interaction-v1/`.
The targeted 42-test group, exact live layer topology, one-process QuickShell
restart and Host health checks passed; the complete repository suite passes
1124 tests with 11 expected skips. No registered Development Environment
exists, and the seed, installed runtime, stopped Environments and every other
dirty-checkout change were intentionally not installed. A physical owner
click/keyboard check remains acceptance evidence rather than an automated
claim.

## System VM v2 repository candidate — 2026-08-24

After the owner rejected the accumulated VM launch path as unreliable and
requested a near-native restart from first principles, v2 is now installed as
an experimental physical candidate. It is not production; a direct entry has
reached QEMU but not firmware or Windows, and physical acceptance remains open.

v2 has one lifecycle owner: the minimal Hyprland session starts one
`apx-vm-runtime-v2`; that runtime owns QEMU, swtpm and optional Looking Glass;
the existing systemd cgroup owns the runtime. QMP polling, Host/guest readiness
and presentation markers, Host process rediscovery, automatic presentation
switching and nested timers are absent. Guest shutdown or a child failure ends
the dedicated compositor and lets the existing authenticated handoff restore
the Hub and RTX.

Presentation has two explicit session-stable modes. `direct` is the default
full-screen QEMU VGA installer/recovery surface. After guest NVIDIA, Looking
Glass Host and IDD setup, `SUPER+SHIFT+N` selects the next-entry `native` path:
no emulated VGA/GTK surface, direct RTX VFIO frames through KVMFR/Looking Glass
on the AMD display. `SUPER+SHIFT+R` always selects direct recovery and exits,
even from a black guest surface. `SUPER+E`/`SUPER+M` remain independent direct
returns. There is no automatic SPICE-video-to-IDD transition inside a session.

Resources are derived from the runtime's admitted CPU and RAM view. On the target, QEMU
gets five physical cores/ten SMT threads and 20 GiB RAM; one full physical core
and roughly 7–8 GiB remain for Host display, audio and recovery. The outer unit
admits 1200% CPU, 24 GiB high/26 GiB maximum RAM and 24 GiB memlock. New disks
are sparse 160-GiB raw NVMe with native AIO on a NOCOW VM directory. Existing
qcow2 disks are opened unchanged with their proven compatibility I/O settings;
raw+qcow2 ambiguity is refused and no automatic conversion or deletion exists.

Future provisioning installs one runtime plus one small OS profile. A
target-bound, backup-and-rollback deployment adapter installed v17 after the
owner explicitly invoked the temporary physical Host guide. It did not start a
VM or restart the Hub. Architecture, lifecycle, storage, recovery, migration
limits and the physical acceptance ladder are recorded in
`docs/system-vm-v2-architecture-2026-08-24.md`. The complete repository suite
passes 1065 tests with 11 expected skips; Python compilation, deployment-shell
syntax and diff whitespace validation also pass.

The owner explicitly requested complete deletion and from-empty recreation of
every existing VM Environment. APX destroyed old `faculdade` generation
`ba865d3f-e592-4281-8e76-6bba8402ff2a` and old `trabalho` generation
`bd9caf9d-aa17-411e-a0e3-4c9ca21cbe2e` through their exact complete-destroy
plans. New stopped Windows 11 v2 generations are `faculdade`
`3a2de127-176a-457a-97b4-a3010a4ca4d2` and `trabalho`
`c03e65b5-3310-4ff2-8a37-165769da1205`. Each has the admitted Portuguese ISO,
source-matched v2 runtime/profile/Hyprland/VFIO content and a NOCOW VM
directory, but no guest disk, NVRAM or TPM. No QEMU/Looking Glass/VFIO residue
or failed unit exists; Hub is sole and healthy. The next action is an
owner-driven first direct Faculdade entry and clean Windows installation.

That first entry failed before QEMU, disk, NVRAM or TPM creation. The v2
profile bytes and ownership were correct, but the root-run provisioner had
created intermediate `.config/apx` as `root:root 0700`; uid 1000 could execute
the runtime yet could not traverse to its profile. The APX error surface was
therefore the only visible window and the supervised session restored the Hub
and RTX normally. v18 adds an explicit user-directory primitive, installs all
home directory ancestors as `1000:1000`, and repairs both stopped system
Environments with metadata-backed rollback. A bind-root-relative uid-1000
probe now parses both profiles successfully. Source and Host provisioner hash
`754443848fe94177d5e59b11822b6f00efd612c33b1f53e7c3e62068474400a0`
matches; both guests remain empty and stopped. The next action remains one
owner-driven Faculdade direct entry.

The next owner entry reached QEMU but QEMU exited before OVMF with
`mlockall: Operation not permitted` / `locking memory failed`. The cause was
the v2 command's unnecessary `-overcommit mem-lock=on`, which asks QEMU to
lock its entire address space; the existing 24-GiB systemd memlock allowance
already supplies the bounded VFIO mapping capacity and the prior working path
did not force `mlockall`. v19 removes only that option, preserves KVM/VFIO and
the memlock allowance, reports the last QEMU diagnostic in the visible error
surface, and corrects the target topology fixture to the measured sibling
pairs `0/1` through `10/11` (guest `0-9`, Host `10-11`). The failed attempt's
4-KiB-allocated sparse raw file, pristine NVRAM copy, empty TPM directory and
empty lock file were validated and removed; the verified ISO and logs remain.
Both Environments are stopped and empty, so the next action is again an
owner-driven direct Faculdade entry.

That v19 entry reached the verified Windows ISO and displayed its
`Press any key to boot from CD or DVD` prompt, proving QEMU, OVMF, VGA and the
installer media path. No key reached the firmware before the short prompt
expired because direct GTK had explicitly disabled keyboard capture on hover.
The disk remained empty. v20 changes only direct presentation to
`grab-on-hover=on`, so moving the cursor over the full-screen VM captures the
keyboard without a menu, QMP injector or timing loop. The blank disk,
firmware/TPM initialization, lock and stale swtpm socket from this attempt were
validated and removed; the ISO and log remain. The v20 backup is
`/var/lib/apx/backups/20260824-system-vm-v2-v20/` and the full 1065-test suite
passes with 11 expected skips.

## VM boot, presentation readiness and balanced-performance candidate — 2026-08-24

The owner subsequently chose a total Faculdade reset. The complete-destroy
contract removed old generation `98edbee0-a816-4637-9473-9e824c8a6974`,
including home/root, Windows disk, firmware/TPM state, snapshots, archives,
metadata and plans. An independent filesystem audit found no old guest disk or
state. Historical deployment backups retained elsewhere contain only small
code/config rollback files, including shared `trabalho` targets, and no
recoverable Windows content.

Fresh generation `ba865d3f-e592-4281-8e76-6bba8402ff2a` is a stopped minimal
system VM provisioned for Windows 11. Its Portuguese ISO matches the admitted
SHA-256. The disk, NVRAM and TPM are intentionally absent until the first
launcher execution creates them new. Initial installation is forced through
the direct QEMU GTK/VGA stable-display path, with Looking Glass disabled and
no Host readiness timer. The next boundary is an owner-driven clean Windows
installation.

The next v14 trial showed Windows and then an apparent crash, but Host evidence
contains no QEMU/VFIO/OOM/guest-container failure or supervisor termination.
The physical Host was abruptly rebooted about six minutes after launch. The
retained Looking Glass history does contain LGMP source loss/restart events,
so the unstable boundary is classified as presentation switching rather than
a proven Windows crash.

`faculdade` is now deliberately forced to the stable full-screen QEMU GTK/VGA
display through a separate `looking-glass-disabled-v1` marker. Looking Glass
does not start and cannot switch from SPICE recovery to IDD/LGMP. The VM Host
timer remains absent. Shared launchers understand this reversible marker;
`trabalho` and the template are not marked disabled. The v15 physical state
passes 1065 tests with 11 skips and has exact rollback at
`/var/lib/apx/backups/20260824-faculdade-stable-display-v15/`. Near-native
presentation optimization is paused until this stable baseline is accepted.

At the owner's explicit request, the VM path now has no Host readiness timer.
It waits for QEMU/QMP and the presentation marker while the already-proven
Hyprland owner session remains alive; only native desktop readiness retains a
ten-second bound. The foreground VM launcher remains the liveness owner and
`SUPER+E` remains the explicit supervised exit.

The v13 black trial did not reach the former 60-second boundary: prior-boot
journal evidence shows the VM started and the physical machine was abruptly
rebooted roughly 27 seconds after the request, with no supervisor QEMU
termination logged. Looking Glass had been configured to suppress its waiting
message, making cold guest/source startup indistinguishable from a dead black
surface. v14 restores the visible waiting state. Host/template and both system
VM Environments are synchronized, 1065 tests pass with 11 skips, and rollback
is `/var/lib/apx/backups/20260824-vm-no-host-timer-v14/`.

Repeated physical evidence established that any second Host-side Looking Glass
process rediscovery is both namespace-sensitive and redundant. The actual VM
launcher owns the Looking Glass PID, creates presentation readiness only after
QMP `query-spice` exposes a connected channel, waits on that PID, and kills
QEMU when the client exits. The outer Host therefore now accepts the exact
QEMU process plus both exact readiness markers; it no longer kills a visible,
stable Windows desktop after 60 seconds because a duplicate `/proc` lookup
cannot represent the client across nspawn boundaries. Real client death still
terminates the supervised launcher/session.

The ownership chain has a dedicated regression test. The v13 correction is
physically installed, source/Host hashes match, and all 1065 tests pass with 11
skips. Exact rollback is
`/var/lib/apx/backups/20260824-vm-launcher-owned-liveness-v13/`; one
owner-initiated Faculdade acceptance entry remains.

The first inode-based refinement was itself rejected physically. An idmapped
nspawn bind does not provide a stable device/inode identity across the Host
and workload mount namespaces, even though the installed binary validation
succeeded. A prior failed handoff also retains the restored blocking Hub
command and emits its failure only when that Hub stops for the next request;
this made the following attempt look like an immediate return although its new
VM ran until the same bounded 60-second rejection.

The installed v12 proof opens the immutable live `/proc/<pid>/exe` image only
for same-sized processes in the exact outer cgroup and compares its SHA-256
with the root-owned B7-799 artefact. This removes both truncated-name and
namespace-relative-inode assumptions while continuing to require QEMU, both
markers and the live certified presentation client. Source/Host hashes match,
the complete suite passes 1064 tests with 11 skips, and exact rollback is
`/var/lib/apx/backups/20260824-vm-looking-glass-content-v12/`. One physical
owner-started entry remains the acceptance boundary.

The executable-basename diagnostic refinement then produced decisive physical
evidence: QEMU and both readiness markers were valid, presentation was
required, forbidden processes were absent, and only the Looking Glass count
was zero. The installed B7-799 client is byte-identical to its root-owned APX
package artefact, but Linux exposes its process as the truncated
`looking-glass-c` while the installed file is `looking-glass-client`.

The Host now validates the installed client content and metadata against the
root-owned artefact once, then recognizes the process by the exact installed
file device/inode inside the unchanged Host-owned cgroup. It therefore neither
depends on a mutable/truncated name nor accepts a readiness marker without a
live admitted client. This correction is physically installed with rollback
at `/var/lib/apx/backups/20260824-vm-looking-glass-identity-v11/`. The complete
suite passes 1064 tests with 11 skips; one owner-started >75-second trial is
pending. The contemporaneous guest "GPU not found" report remains a separate
driver/passthrough observation: the supervisor terminated the trial before the
acceleration tool ran, while earlier retained logs prove this guest previously
produced B7 IDD 1920x1080 DMA frames.

The first physical acceptance attempt subsequently proved that Windows and
the accelerated presentation reached a stable visible desktop, but the Host
recovered the Hub at the exact 60-second outer bound when the owner happened
to press Space. Both readiness marker proofs remained valid after recovery.
Space is neither an APX return binding nor a standard Looking Glass exit
binding; the correlation is retained as an observation, not claimed as the
cause.

The outer verifier's remaining process proof used `/proc/<pid>/comm`. That
field is limited to 15 bytes and applications may rename it, making it weaker
than the intended executable-identity check. The installed correction uses
the exact `/proc/<pid>/exe` basename for `qemu-system-x86_64` and
`looking-glass-client`, still constrained to the exact Host-owned systemd
cgroup. Timeout errors now include bounded JSON observations of both process
counts, readiness markers, presentation requirement and forbidden services.
The source/installed hashes match and the complete suite still passes 1064
tests with 11 skips. Exact rollback is
`/var/lib/apx/backups/20260824-vm-executable-readiness-v10/`; physical
acceptance remains pending one owner-initiated retest.

The owner retained the APX-supervised KVM/VFIO/Looking Glass architecture and
requested a complete correction of the reported Windows creation/boot,
Faculdade rollback and non-native response. The candidate is installed on the
physical pilot but not yet owner-accepted.

Windows now has two distinct bounded readiness phases. Buffered, event-aware
QMP must report `running` within 30 seconds, then the Looking Glass recovery
path must expose an actual connected SPICE channel within 20 seconds. Separate
mode-0600 exact-content markers represent guest and presentation readiness;
the Host requires both plus the live QEMU and, where certified, Looking Glass
processes. Its VM-only outer bound is 60 seconds. This prevents both premature
rollback and acceptance of a black process-only surface. A failure stops the
guest and presents one APX-styled error with the retained launcher-log path;
the owner can acknowledge it or use the compositor-owned emergency return.

A new Windows disk no longer depends on one key at an exact 7.2-second point.
Its already bounded QMP helper sends three short Enter events between 5.5 and
9.5 seconds, covering cold OVMF variance while remaining before the later
Windows PE interaction. The readiness regression test now checks the number of
30-second deadlines and explicitly excludes the former 12-second value, so the
installer helper cannot mask a stale main deadline again. Ubuntu emits the
same guest/presentation marker pair for its visible GTK path.

The target-specific performance profile reserves two of the Legion's six
physical cores for Host presentation and supervision. QEMU is pinned to SMT
pairs `0/6` through `3/9` and exposes four cores/eight threads, instead of
competing for all six cores/twelve threads. The guest receives 12 GiB RAM; its
outer resource bounds are 14 GiB high, 16 GiB maximum and 14 GiB locked-memory
capacity. Looking Glass explicitly admits DMA and polls frames/cursor at the
documented one-millisecond interval. A relative USB mouse matches its raw input
path; the resampled absolute tablet is absent.

The guest acceleration media now includes a bounded Windows verifier. After
the IDD/Host installation reboot it locates only a Looking Glass/indirect
display, requires that it advertise exact 1920x1080/120 Hz, applies that mode,
selects Windows High Performance and records display, GPU and Looking Glass
service evidence under `C:\ProgramData\APX`. Failure is explicit and does not
silently claim 120 Hz.

E1000E and the existing NVMe/qcow2/Btrfs path are preserved in this candidate.
Windows has no admitted verified VirtIO driver artifact, so switching network
or boot storage now could remove connectivity or make the installed guest
unbootable. Storage format changes likewise remain measurement-gated because
they interact with APX Btrfs snapshot and complete-purge semantics. Those are
deliberate open optimizations, not claimed fixes. All 1064 repository tests
pass with 11 expected skips.

The target-bound deployment installed the source-matched generic graphical
launcher, synchronized both Host graphical engines, and updated the system VM
template/provisioner plus the stopped `faculdade` and `trabalho` launchers and
APXTools. It did not restart the running Hub or start a VM. Post-install proof
found only the Hub machine, active switch/Hub services, no QEMU/Looking Glass/
VFIO residue, consistent Btrfs quotas and no failed unit. The exact prior files
and before/after digests are retained at
`/var/lib/apx/backups/20260824-vm-readiness-performance-v9/`. Physical
acceptance remains the separate owner-initiated five-boot/frame/input/return
trial.

## Cold-VM readiness, lean creation and terminal repair — 2026-08-24

The latest Faculdade rollback came from two nested deadlines: its launcher
connected to QMP but abandoned a single read after two seconds, while the Host
classified the VM as failed after ten seconds. VM launchers now use buffered,
event-aware QMP parsing with a bounded 30-second deadline. The Host's VM-only
readiness window is 35 seconds; the normal desktop window remains ten seconds.
This preserves fail-closed recovery without rejecting healthy cold firmware,
VFIO and TPM initialization.

The Windows creator is now proven end to end. Installed shell seeds are again
identical to their digest-pinned sources. Environment feature selection no
longer reinstalls GPU packages already owned by the immutable graphical
release, avoiding both wasted storage and partial-upgrade conflicts. The
system provisioner performs one private-root `pacman -Syu` transaction with
the required sandbox override before adding QEMU. Failed unpublished attempts
are removed only by journal-backed recovery. The physical `trabalho` Windows
11 Environment completed creation and remains stopped.

The shared `SUPER+Q` action now targets Kitty, the terminal actually included
in the graphical release, instead of absent Alacritty. The source and physical
seed, Hub and existing ordinary Environments are synchronized; the running Hub
reloaded successfully and exposes the binding. All 1063 tests pass with 11
expected skips; Host, Hub and switch services are healthy with no failed unit.

## Generic minimal VM runtime and launch-recovery repair — 2026-08-23

The 18:49 owner trial exposed three deployment gaps after the earlier repair.
The existing Faculdade still launched its generated `apx-system-vm` copy,
which had not received the current Looking Glass warning suppression. Looking
Glass also published its default `looking-glass-client` app id while the
compositor's shortcut-inhibition rule matched only a QEMU-style title. Finally,
the Hub creation UI used a persistent bridge client predating the `--system`
field, so Windows 11 creation failed locally before reaching the Host service.

The canonical Windows launcher is now installed as both the named and generic
Faculdade entry point and gives Looking Glass the deterministic
`apx-system-vm` app id. Hyprland matches that identity, forbids shortcut
inhibition and forces the presentation full-screen. `SUPER+E` and redundant
`SUPER+M` now execute Hyprland's native exit dispatcher; the foreground Host
supervisor restores Hub without any menu, Python client, socket, SPICE,
Looking Glass, or guest dependency. The Hub UI always uses the current
read-only `/run` client, and non-Arch creation emits the minimal system payload.
Source/template/live hashes match, QuickShell hot-reloaded successfully, and
the complete suite passes 1062 tests with 11 expected skips.

Physical acceptance of `ATIVAR-ACELERACAO.cmd` proved the matching B7 Windows
Host/IDD path: the client switched from SPICE to KVMFR DMA, accepted BGRA
1920x1080 frames and LGMP input, and visibly improved response. The scheduled
guest reboot later removed the source for 23 seconds; SPICE recovery connected
and KVMFR frames resumed normally. The user powered off at the same instant
the accelerated source returned, so the black interval was the expected guest
reboot rather than a QEMU, client, VFIO, or Host failure.

The client now hides B7's waiting/capture overlays, and the Windows setup tool
requires an explicit Restart/Later choice instead of scheduling a surprise
reboot. Its screen and readme warn that a reboot can be black for up to 90
seconds. `SUPER+E` and the redundant `SUPER+M` now request the supervised Hub
return directly from the Host-owned compositor; neither depends on Windows,
Looking Glass, SPICE, or a visible guest frame. The blue chooser remains on
`SUPER+SHIFT+E`. This keeps recovery available throughout guest reboot and
avoids unsafe physical power-off.

The owner-initiated 18:23 trial proved the rebuilt minimal B7 client itself is
healthy: without `/dev/fuse` it initialized Wayland/EGL, UNIX SPICE input and
video, KVMFR/LGMP, JIT rendering, and a 1920x1080 recovery surface. APX then
incorrectly killed that healthy VM because Linux exposes only 15 bytes of the
executable `comm`; readiness searched for impossible `looking-glass-cl`
instead of the actual `looking-glass-c`. The verifier now uses the exact
kernel identity.

That failure also exposed a Hub restoration race. The boot autostart process
interpreted the supervisor's deliberate Hub stop as a malformed session and
`Restart=on-failure` launched competing Hub instances during the active
handoff. Autostart now recognizes the trusted root-owned handoff lock both
before launch and after an interrupted Hub result, returns success, and leaves
restoration exclusively to the handoff supervisor. These corrections are
installed offline while the owner remains on tty1; no VM/VFIO state remains.
The complete suite passes 1061 tests with 11 expected skips.

The owner then confirmed Windows was visible but the recovery presentation was
far from native: Windows-button actions took visibly too long, and the return
surface rendered pale/transparent at the centre and did not accept a normal
single click. The Host had about 25 GiB RAM available and negligible CPU/I/O
pressure, excluding Host resource starvation. The launch had no
`looking-glass-ready-v1` marker, so it was still the software VGA/GTK recovery
path rather than RTX/KVMFR presentation.

The B7-799 client physically installed in Faculdade was queried inside its own
root and proves built-in SPICE recovery video/input plus automatic LGMP/KVMFR
transport. The Windows launcher now uses that client as the one presentation
window whenever the exact client and KVMFR device exist: QEMU has no GTK
window, the client initially shows the VGA recovery surface over its UNIX
SPICE socket, and automatically changes to KVMFR frames when the matching
Windows Looking Glass Host/IDD begins publishing. JIT rendering, raw mouse,
automatic capture and guest-resolution requests are enabled; SPICE audio and
both clipboard directions are disabled because audio already has its bounded
PipeWire path and the VM contract exposes no Host clipboard. Host readiness
also requires the Looking Glass client process, preventing another accepted
black presentation.

The guest read-only `APXTools` drive now includes
`ATIVAR-ACELERACAO.cmd`. It asks for Windows administrator confirmation,
silently installs the already verified matching IDD and Host packages and
schedules one Windows reboot. This remaining guest-local UAC action cannot be
performed by the Host without taking control of the owner's Windows account.

Rofi B7 uses `#RRGGBBAA`, while the earlier VM theme mistakenly supplied alpha
first; that produced the reported pale/white surface. The corrected panel is
again anchored at the top, uses the exact blue/cyan RGBA ordering, accepts a
single `MousePrimary` click instead of Rofi's default double-click and also
accepts Enter/Space. The fixed one-row action returns independently of its
display label.

The next physical Faculdade trial reached the VM boundary but showed a black
screen. Persistent evidence identified the exact cause: VFIO attempted to pin
the 8 GiB guest RAM while the transient service inherited an 8 MiB
`RLIMIT_MEMLOCK`, and QEMU exited with `vfio_container_dma_map ... -12
(Cannot allocate memory)`. The VFIO-only outer and inner units now receive a
bounded 10 GiB memlock ceiling; this grants capacity but does not allocate or
reserve 10 GiB. A physical transient-unit proof reports the expected
10,485,760 KiB limit.

VM readiness no longer means merely finding a short-lived QEMU PID. Every
system-VM launcher removes a stale marker, queries QMP, requires guest status
`running`, and only then publishes a root-supervised exact-content readiness
marker. An immediate VFIO/QEMU failure therefore keeps the handoff failsafe
armed and restores the Hub instead of accepting a black screen.

The one-action VM overlay no longer compares Rofi's returned Unicode label.
Any accepted selection requests `return.to-hub`; three broker failures invoke
a clean local `hyprctl dispatch exit`, which the foreground supervisor treats
as the owner exit and follows by restoring the Hub. Its lightweight Rofi theme
is now centred with a translucent blue surface, cyan border, blue information
card and selected action styling consistent with the APX menus. No persistent
desktop shell was added.

Every Environment carrying the exact `virtual-machine-v1` capability now uses
one generic `apx-system-vm` owner entry point and the same minimal session
contract, irrespective of whether its guest is Windows or Ubuntu. The boundary
contains only D-Bus, native PipeWire/WirePlumber, Hyprland, QEMU/Looking Glass
and the on-demand APX return menu. It starts no QuickShell, Waybar, hypridle,
hyprlock, PulseAudio compatibility server, portal or ordinary Linux desktop;
the Host-side readiness proof rejects a VM session if any of those processes
appears. Hyprland remains required as the narrow display/input/lifecycle owner
that reserves `SUPER+E` and `SUPER+M` and can always return to the Hub.

VM containers receive only the authenticated Environment-switch socket. Host
desktop summaries, model controls, desktop menus and shared audio-state
authority are no longer mounted. Looking Glass launches QEMU with no hidden GTK
or virtual-VGA display; the safe GTK/VGA path remains only as an explicit
installer/recovery fallback when Looking Glass is unavailable. Provisioning no
longer installs an autostart desktop file, and all future non-Arch system
Environments are forced to the `basic`/`system` package plan regardless of UI
state. Existing guest disks and installed guest software are not rewritten.

The common supervisor now preserves and reads the inner systemd unit result.
Only a clean owner exit is classified as a normal return; a policy error,
launcher crash or other non-zero inner result fails closed and triggers Hub
recovery. This closes the false-success path that previously reported a
restored Hub after the Faculdade session had actually failed.

## Host-console repair and native-feel Faculdade direction — 2026-08-23

The `SUPER+H` Host-console path no longer depends on a persistent PTY or a
detached Kitty process retaining QuickShell ancestry. The direct QuickShell
child first obtains a 10-second, uid-bound, single-use broker ticket while its
official-Hub ancestry is provable; the detached terminal consumes that ticket
to open a fresh root PTY. Closing the window terminates that shell. Reopening
focuses the stable Kitty class if it exists, otherwise creates a new console.
The non-interactive error window closes automatically and can no longer trap
the user behind an Enter/ESC prompt. Broker audit records rejection reasons.

The owner confirmed that the Host-console window itself now works, but the
physical `SUPER+H` binding did not: the shared Hyprland profile still mapped H
to its ordinary `terminal` variable. It now calls the capability-aware
QuickShell `openTerminal` IPC; in the official Hub that method launches the
ticketed Host console, while workloads acquire no Host-console capability.

The VM-only profile now has a minimal Rofi Environment chooser on `SUPER+E`
and a Host-supervised return on `SUPER+M`, without adding QuickShell. Guest
shortcut inhibition is disabled for these compositor-owned bindings. The Host
switch service accepts a generation-bound workload-to-workload request and its
runner restores the Hub on invalid/stale requests or launch failure.

The first post-VFIO manual launch exposed a shared-session contract mismatch:
the launcher selected `vfio-guest`, but the session validation still rejected
that policy. Recovery then exposed a second regression where the IPC fallback
could end a healthy Hub even after its Lua callback had started QuickShell.
The session now admits `vfio-guest` only for `virtual-machine`, accepts an
already-running owner workload before fallback dispatch, and leaves the final
readiness decision to the Host-side authoritative proof. The corrected session,
common engine, generic launcher, provisioning/management runners, system-VM
template and Faculdade instance are installed with matching source hashes. A
new owner-initiated visual trial remains pending.

The owner accepted the functional `SUPER+E` escape in `faculdade` but rejected
its generic multi-Environment list. The VM-only overlay now reads its
authenticated identity, presents the APX dark/cyan/monospace visual language,
labels the current Environment, and exposes exactly one action: `REGRESSAR AO
HUB`. It cannot open a sibling Environment.

The physical panel audit found the active native mode is 1920x1080 at 120 Hz.
The VM boundary now selects Hyprland `highrr` at scale 1 and QEMU advertises an
exact 1920x1080/120 Hz EDID-backed standard VGA mode with 64 MiB framebuffer,
instead of allowing a small framebuffer to be blurred by GTK zoom. AMD guest
topology exposes `topoext`; the qcow2 path uses threaded writeback AIO with
discard/zero detection after earlier native-AIO I/O errors on Btrfs. This is an
interim clarity/stability improvement, not virtual 3D acceleration; full GPU
performance still requires the gated VFIO phase.

For the requested near-native experience, the selected direction is NVIDIA
RTX 3060 VFIO passthrough with Looking Glass displayed through the Host-owned
AMD integrated GPU. This remains technically a KVM guest because true dual
boot cannot preserve a live APX supervisor, instant `SUPER+E`, or the same
Environment isolation/deletion contract. IOMMU is currently disabled and its
groups are therefore unknown; boot changes and a reboot remain explicitly
gated on owner approval. The decision and safe phases are recorded in
`docs/faculdade-native-feel-vfio-v1-2026-08-23.md`.

## Dedicated Faculdade VM session and Host-console takeover — 2026-08-22

`faculdade` is now a dedicated `virtual-machine-v1` graphical Environment.
The common supervised session starts QEMU directly and verifies exactly one
VM process; it does not start QuickShell, hyprlock, a bar, a terminal or an
ordinary Linux desktop. Hyprland remains as the invisible physical device and
lifecycle boundary. `SUPER+E` opens the minimal Environment chooser and
`SUPER+M` requests return to the Hub. The VM
is full-screen, KVM accelerated, UEFI Secure-Boot-capable, TPM 2.0 backed and
uses the persistent isolated Environment storage. The official installer has
passed Windows 11 requirements and is currently paused at the Windows 11 Pro
license terms for the owner to accept personally.

The Host-console paragraph here is superseded by the 2026-08-23 fresh-console
ticket design above.

## Environment deletion is always complete purge — 2026-08-22

The owner requires `Apagar Environment` to remove every APX-owned resource for
that logical Environment, with no preservation choice. The physical executor
now purges all generations of its snapshots and archives, explicitly named
legacy maintenance backups, live `home` and `root` subvolumes, capability and
other top-level metadata such as `kvm-v1`, registration, and every stored plan
whose authoritative `name` matches. The plan is generation-bound, declares
these effects, requires the exact `DESTROY <name>` approval and rejects the old
effect list. Exact UUID-shaped snapshot/archive names and exact logical-name
matching protect neighboring Environments with similar names. Only the global
append-only audit journal retains the fact that deletion happened; it contains
no VM disk, ISO, home data, snapshot or recoverable Environment content. The
`faculdade` VM is therefore deleted with `faculdade`, including its Windows
disk, installer ISO, UEFI/TPM state, KVM marker and every APX copy.

## Faculdade Windows 11 KVM pilot and keyboard recovery — 2026-08-22

The existing `faculdade` Environment now has an isolated Windows 11 VM pilot.
QEMU/KVM, OVMF and swtpm are installed only in that Environment; its exact
root-owned mode-0400 `kvm-v1` marker leases only `/dev/kvm`. The persistent VM
uses 12 vCPU (6 cores/12 threads), 8 GiB RAM, a sparse 120 GiB qcow2 NVMe disk, UEFI, TPM 2.0,
user-mode NAT, virtual graphics and no Host shares or passthrough devices. Its
launcher opens automatically and full-screen as the only workload,
while `SUPER+M` remains the route back to the Hub. The downloaded official
Portuguese (Portugal) x64 Windows 11 ISO is bootable and its full SHA-256
matched Microsoft's published value exactly. A disposable smoke boot also
proved the complete KVM, UEFI, TPM 2.0, NVMe and NAT device combination.
Interactive installation, activation and account choices remain owner actions.
The implementation and future generic VM-Environment
shape are recorded in
`docs/faculdade-windows11-kvm-v1-2026-08-22.md`.

The latest physical report supersedes the exclusive-grab statement below.
FnLock is off and the required contract is plain F1--F12 as application keys,
with multimedia actions exclusively on Fn+F1--F12. `EVIOCGRAB` was removed
because grabbing the Lenovo ITE interface made ordinary typing non-responsive
on this hardware. The current exact-identity observer maps only ITE Fn-row
events and leaves the AT keyboard untouched. Physical owner confirmation of
both halves remains pending.

## Lenovo keyboard hotkeys — 2026-08-21

Historical note: an exclusive ITE grab was tried to stop raw Fn events reaching
focused applications, but was reverted by the 2026-08-22 physical recovery
above because it also made ordinary typing non-responsive.

A second physical trial confirmed the OSD presentation and volume path but
showed that most remaining Fn actions were not reaching their commands. A live
capture established the target-specific route: Fn+F4--F12 are mirrored by the
internal ITE interface as raw Linux key codes `62--68,87,88`; normal F4--F12
come from the separate AT interface. The exact-keyboard bridge therefore owns
only the ITE copies, preserving normal function keys, and routes microphone,
brightness, display, radio feedback, application launcher, touchpad feedback,
window overview and calculator. The AT `KEY_SYSRQ/99` route owns Print Screen.
All destinations passed direct post-install proof, including microphone
mute/restore, brightness `65535 → 62258 → 65535`, and a timestamped screenshot.

The shared graphical Environment profile now implements the documented Lenovo
Legion 5 15ACH6H hotkey row. Volume, microphone and mediated display brightness
retain their existing paths. F7 cycles connected-display layouts; F8 remains
the Host kernel's Lenovo rfkill path; F9 opens the Environment app launcher;
F10 toggles the exact internal ELAN touchpad; F11 opens the Environment window
list; and F12 opens a calculator only when one is installed locally. Print
Screen now saves a timestamped PNG under the Environment's Pictures directory.
Insert, Delete, Home, End, Page Up and Page Down remain unbound compositor keys
and pass normally to applications. Standard XF86 symbols and this firmware
generation's F13--F16 fallbacks are covered without widening Host authority.
Details are in `docs/legion-keyboard-hotkeys-v1-2026-08-21.md`.

The first owner trial confirmed volume, mute and airplane mode but exposed no
brightness response and no visible state feedback. The Host brightness backend
was proved healthy by changing `amdgpu_bl1` raw brightness
`65535 → 62258 → 65535`. The exact internal keyboard bridge now accepts both
F5/F6 and brightness 224/225 codes from either identity-checked Lenovo internal
keyboard interface. A translucent, non-keyboard-focus QuickShell OSD reports
audio, microphone, brightness, airplane state, display layout, application and
window launchers, touchpad, calculator availability and screenshots. Airplane
feedback reads the kernel's rfkill soft blocks directly from read-only sysfs,
so it remains live across Host-service socket replacement; a typed read-only
`radio.status` Host view also exists for other consumers. Mutation remains owned
by the kernel rfkill handler. The active Hub loaded the OSD successfully, a
visual capture confirmed its translucent bottom-centred presentation, Hyprland
reported `natural_scroll = true`, and the full suite passed 1046 tests with 11
expected skips.

The shared touchpad profile also uses natural two-finger scrolling: dragging
upward moves down through page content.

## AC-powered native performance closure — 2026-08-21

The owner connected AC power (`ADP0=1`) and authorized final performance
closure. Three alternating direct-I/O passes with 256 MiB incompressible data
measured Host/APX writes of ~638/~655 MB/s and reads of ~3.07/~2.97 GB/s. The
earlier apparent 19% Steam storage deficit did not reproduce; the remaining
~3% spread is normal measurement variance. Weekly `fstrim.timer` is enabled.
Btrfs CoW, zstd compression, checksums, snapshots and full qgroup accounting
remain because there is no evidence that trading those guarantees away would
improve this workload.

GPU overhead was isolated without changing monitor, compositor or userspace.
The same `vkmark 2025.01` binary and NVIDIA ICD rendered through the same RTX
3060 UUID, Hyprland, Wayland socket and 1920×1080 NVIDIA-connected BenQ. One
process ran normally inside APX; the comparator entered only the Hub mount
namespace to reach that socket and remained a Host process outside APX's user
namespace and cgroup. Both scored 691 at 1080p. Three 3840×2160 pairs scored
APX 93/192/192 and Host 92/191/192, averages 159.0 and 158.3. The simultaneous
cold-to-boost ramp and ~0.4% final spread establish no measurable APX Vulkan
overhead. Benchmark-only `vkmark` and `assimp` were removed afterward.

CPU, direct storage and Vulkan/RTX structural performance are now accepted as
native-equivalent for this Arch/Hyprland hardware and software stack. No Steam
games or manifests exist, so per-title Proton FPS, 1% lows and frametime tails
cannot be measured yet; those are title acceptance, not an open APX performance
defect. Gamepad, paired Bluetooth and LAN `iperf3` likewise require external
fixtures that are not currently available.

## Host/HUB/Steam physical performance remediation — 2026-08-20

The physical Ryzen 5 5600H pilot initially measured 14.62–14.93 GB/s native
versus 7.15–7.64 GB/s in graphical Environments. The root cause was the outer
launcher's explicit `CPUQuota=600%`: the namespace showed 12 logical CPUs and
unlimited descendant cgroups, but its parent allowed only six CPUs of runtime.
Hub and generic workloads now use `CPUQuota=1200%`; the physical outer cgroup
reports `1200000 100000`. Post-fix Steam proofs measured 15.06 GB/s and
20.62 GB/s, so the structural 49% ceiling is removed.

NVIDIA admission now runs `nvidia-modprobe -u`, proves the unique dynamic UVM
major, and leases both `/dev/nvidia-uvm` and `nvidia-uvm-tools`. A second cause
was nspawn's filtered sysfs under `--private-network`: NVIDIA userspace could
open `nvidiactl` but could not see `/sys/module/nvidia/initstate`, then returned
`NVML_ERROR_OPERATING_SYSTEM`. The launcher now bind-mounts only that NVIDIA
module subtree read-only. Hub and Steam physically return RTX 3060 through
both NVML and Vulkan while network isolation and `DevicePolicy=closed` remain.

Steam's multilib repository is enabled and its current root has matching
`nvidia-utils 610.43.03-3` / `lib32-nvidia-utils 610.43.03-1`, plus
`lib32-mesa`, `lib32-vulkan-radeon`, `lib32-vulkan-icd-loader`, `egl-gbm` and
`vulkan-tools`. Runtime creation and the physical base builder install the
same stack for future roots. `pacman -Dk` is clean. Hyprland physically
enumerated the four admitted internal input identities. seatd's remaining
EPERM messages are failed discovery attempts for non-leased hardware; the
policy was deliberately not widened merely to silence them.

Exact Hub and Steam QuickShell files were restored, only Hub is active at its
normal login surface, and no credential was automated. The complete repository
suite passes 1043 tests with 11 expected skips. A real game FPS/frametime test,
LAN `iperf3`, paired Bluetooth peripheral and gamepad remain hardware acceptance
work rather than known performance blockers. Full evidence is in
`docs/apx-host-hub-steam-performance-assessment-2026-08-20.md`.

## NVIDIA control-node Hub boot repair — 2026-08-15

The physical Host booted NVIDIA 610.43.03 successfully and published its GPU,
KMS and UVM device nodes, but `nvidia-modprobe -c 0` returned success without
publishing `/dev/nvidiactl`. The exact Hub therefore failed closed before
starting, retried three times and reached the autostart start limit. With no
authenticated Hub, Environment creation was unavailable by design.

The exact Hub launcher now repairs only the missing NVIDIA control character
device after proving that the running kernel exposes one unambiguous
`195 nvidiactl` registration in `/proc/devices`. The result is still checked as
major 195, minor 255 before it is leased. Missing, wrong or duplicate kernel
registrations remain a refusal. The repaired launcher is installed with a
backup and physically progressed through NVIDIA admission into Hyprland and
the Hub login surface. The current session is intentionally waiting at that
login surface; authenticated QuickShell management proof remains pending the
owner's local unlock. The repository passes 1034 tests with 11 expected skips.
Details are in
`docs/nvidia-control-hub-boot-repair-v1-2026-08-15.md`.

## Interactive popup and shortcut-module repair — 2026-08-14

The first popup-focus repair kept IPC-launched menus visible, but the resulting
xdg popup did not provide reliable pointer/keyboard input on the physical
session. The shared shell now renders the menu as a focused `PanelWindow` with
`WlrKeyboardFocus.OnDemand`; the compositor `HyprlandFocusGrab` remains the
outside-click dismissal boundary. The menu recomputes its horizontal margin
from the opening bar button, clamps to the monitor edges, and starts directly
below the bar while remaining an input-capable QuickShell surface.

The Environment creation popup is intentionally capped at 620×540 so its
long feature list scrolls inside the form instead of taking over the screen.
Its content expands from the top edge with a short opacity/scale animation.

The duplicate `Atalhos APX` switch was removed from the crowded Control Centre.
The capability is now an explicit `shortcuts` Environment module with a clear
Portuguese title, description, and `SUPER+A/B/D/E` program detail. Intermediate
and Complete presets include it; Basic remains the minimal base. The feature
catalogue, dependency closure, size estimate, creation UI focus map, runtime
digest, seed, current Hub, and existing `faculdade` are synchronized.

## Keyboard popup and pre-identity return hotfix — 2026-08-14

The owner-visible `SUPER+A/B/D/E` failure was a Wayland popup focus defect.
Bindings and QuickShell IPC were healthy, but an IPC-triggered shortcut has no
pointer input serial. `PopupWindow.grabFocus: true` therefore opened and
immediately dismissed the menu; QuickShell recorded the missing eligible
parent/input event. The common shell now uses Quickshell 0.3's native
`HyprlandFocusGrab` over the bar and popup, with standard popup grab disabled.
A real outside click clears the grab and dismisses the menu. Physical direct
proofs kept Controls, Calendar, Battery and Environments visibly open.

Workload return also no longer becomes unavailable during the narrow interval
before Host-authorized identity publication. The Host-console socket is an
exact Hub-only local role proof and grants no new operation. In a workload with
identity not yet ready, both return controls invoke local compositor exit; the
already authenticated handoff supervisor then performs bounded cleanup and Hub
restoration. Normal Host-driven return remains preferred after identity is
ready. The repair is installed in current Hub, current `faculdade`, the future
Environment seed and the digest-bound creation runtime. Details are in
`docs/environment-shortcut-popup-and-return-hotfix-v1-2026-08-14.md`.

## Environment creation, persistent shortcuts, loading, Brave and HDMI — 2026-08-14

The common creation shell now presents explicit Base APX, Daily Use and Work
profile titles. Capability drawers and rows remain title-only until right
click, which reveals their description and exact program set. Accepted create
requests immediately dismiss the form, preventing the stale form/list layering
that appeared as background flashing. The workload Control Centre follows the
Hub's everyday layout but excludes Host-only terminal and APX Host authority.

Future Environments use Brave for browser bindings and MIME defaults. Brave is
installed from a SHA-256-pinned Host-owned `brave-bin 1:1.93.136-1` artifact;
Firefox is no longer part of the web/documents capability. Existing profiles
are not rewritten because the owner chose to recreate them.

`SUPER+A` and `SUPER+E` are seeded into every new graphical Environment and
have an enabled-by-default per-Environment Control Centre toggle. Their return
failure was caused by logind deleting `/run/user/1000` after a transient login,
not by missing bindings. Host-supervised sessions now keep Hyprland and
QuickShell IPC under `/run/apx/session-1000`. A real Hub-to-Hub transition
preserved those sockets; the watchdog remained healthy and post-return IPC
succeeded.

The Host loading page now owns tty1 without a terminal flash. The handoff
supervisor runtime-masks and stops `getty@tty1` for the supervised graphical
chain, transfers ownership across overlapping handoff runners, and unmasks the
recovery login only when no lock, machine or GUI remains and tty1 is active.
Physical validation showed the unit masked/inactive and no getty journal entry
during the transition.

Hybrid AMD/NVIDIA sessions now lease both KMS card/render pairs plus the
NVIDIA auxiliary devices and prefer AMD:NVIDIA in `AQ_DRM_DEVICES`. New roots
receive `egl-gbm` and exact Host-driver-matched `nvidia-utils 610.43.03-3` from
a digest-pinned local artifact. The active Hub sees the devices and matching
userspace. Final two-monitor proof is pending because HDMI-A-1 was physically
disconnected at the last check. The pre-change `faculdade` profile failed
closed during a launch and restored Hub; it was not migrated by design.

The complete repository suite passes 1032 tests with 11 expected skips. Source
and installed runner match SHA-256
`78af71882edafdc5faedffeef48799d075528eaf0db4c1ca97eecc85a04839fc`.
Details and rollback are in
`docs/environment-creation-shortcuts-loading-brave-hdmi-v1-2026-08-14.md`.

## Environment UI clarity and hybrid external displays — 2026-08-13

The Environment creation form now distinguishes clearly between the APX base
and packages genuinely added by a capability. Basic, Intermediate and Complete
are labelled as Base APX, Daily Use and Work starting points with concrete
software summaries. Capability drawers and rows remain compact; right-clicking
an individual row reveals its purpose and exact base/installed program list.
The common workload Control Centre has sufficient height and a readable 2×2
action grid, so Apps, Lock, Files and Return are no longer clipped. It otherwise
keeps the Hub's mediated everyday controls while excluding the persistent Host
terminal and APX exit-to-Host rows.

The owner also reported that HDMI never activated. Physical connector evidence
explains the defect: internal eDP-2 belongs to AMD card2, while HDMI-A-1 and both
DP connectors belong to NVIDIA card1. Hybrid APX sessions leased AMD KMS plus
NVIDIA render only, so external connectors were invisible. Hybrid launches now
lease both card/render pairs and start Hyprland with AMD first and NVIDIA
second in `AQ_DRM_DEVICES`; the same mechanism covers Hub and normal graphical
Environments. Installed files match source, but the active Hub was not restarted
solely for proof. The next normal launch plus a real attached HDMI monitor is
the remaining physical acceptance. Details and rollback are in
`docs/environment-ui-and-hybrid-external-monitors-v1-2026-08-13.md`.

## Fresh Environment shell ownership and failed-start recovery — 2026-08-13

The first menu-created Environments exposed a creation defect: nested seed
copying created the implicit `~/.local` ancestor as Host root with mode 0755,
then correctly placed user-owned executables below it. The unprivileged shell
launcher could not create `~/.local/state`, so it exited before opening
QuickShell or creating its own log. Hyprland remained alive until the generic
launcher correctly rejected the missing desktop shell after ten seconds.

The runtime now enumerates, validates, modes and owns every destination
directory between the Environment Home and each reviewed shell asset. Tests
assert the intermediate `.local`, `.local/bin` and `.config` ownership/mode,
not only the final files. The existing stopped `jogos` and `andre`
Environments were repaired in place by changing only `~/.local` to
`apx:apx 0700`.

The failure also showed that the handoff runner cleaned the rejected workload
but propagated its exception before reaching the Hub relaunch. It now retains
the destination or cleanup failure, always attempts authenticated Hub
restoration after bounded cleanup, and only reports the retained failure after
that restored Hub session ends. A regression test injects the exact workload
shell failure and proves that the Hub launcher is still called. Installed and
source runtime/runner hashes match, and the full suite passes 1021 tests with
11 skips. A forced graphical transition was not performed while the active
Hub carried the Host-console Codex; normal owner use remains the visual proof.

The next owner trial exposed a distinct lifetime defect: the 120-second
startup failsafe remained armed even after `andre` had published a healthy
QuickShell session, so systemd recovered it at exactly two minutes. The runner
now treats the failsafe as startup-only. It disarms only after a root-owned,
bounded active descriptor matches the trusted registration's logical name,
graphical-base role, v2 release, running state, generation, generation-derived
outer unit and positive compositor PID. If that evidence never appears, the
original 120-second recovery remains armed. Installed/source runner hashes
match and the full suite passes 1022 tests with 11 skips.

The sudo report from the same trial is also confirmed. Fresh v2 graphical
accounts have `apx:!` until the owner chooses a password local to that
Environment. Sudo policy and wheel membership were correct, but PAM cannot
accept any password while the account is locked. APX must never silently copy
the Hub credential. The existing secure Host-console enrollment command is
`apx environment enroll-local-admin <name>` while that graphical Environment
is running; a native first-run/password-management surface remains an explicit
product gap.

## Native Environment management panel and loading transition — 2026-08-13

The exact physical Hub now has one compact native QuickShell panel with a
direct selectable catalogue and aligned **Criar**, **Selecionar**, and
**Apagar** actions. The old explanatory text, ESC/Host footer, and secondary
Rofi chooser are removed. Creation is fixed to the reviewed
`graphical-base`/`hyprland-base-v2` path, which supplies independent storage,
Hyprland, Rofi, desktop essentials and the common QuickShell without cloning
the live Hub. Delete is stopped-state and generation bound, requires a second
explicit confirmation, and can never target Hub.

Create/destroy run asynchronously through a root-owned reservation, typed
plan/digest, existing journalled APX runtime and read-only progress endpoint.
Workloads receive only return-to-Hub. A full-screen QuickShell loading overlay
now hands off to a pre-rendered Host-owned tty1 APX progress page, preventing a
normal transition from exposing a Host prompt. Hyprland readiness changed from
a fixed two-second stability delay to two complete 50 ms evidence samples;
recovery/registration polling is also 50 ms while the original deadlines and
fail-closed gates remain.

The new QML loaded on the physical Hub in about 0.53 seconds; live catalogue
and progress reads were accepted and the final visual capture is clean. The
complete repository passes 1020 tests with 11 skips. No disposable Environment
was created or destroyed solely for proof, and the current Host-console PTY was
preserved. Backups are under
`/var/lib/apx/backups/20260813-environment-menu-management-v1/`; details and
rollback are in
`docs/environment-menu-management-and-loading-v1-2026-08-13.md`.

## Owner-selected emergency shortcut — 2026-08-12

The owner inverted the two bindings on 2026-08-13: `Super+E` now opens the
Environments menu and `Super+M` is the IPC-independent internal Hyprland exit.
The Hub Control Centre no longer contains “Choose Environment”; it contains a
Hub-only “Exit to Host” action using the same internal exit dispatcher. The
central bar button remains the graphical route to the Environments menu.

Environment shell startup no longer sleeps for four seconds unconditionally.
It waits for two consecutive enabled-monitor observations through Hyprland IPC
at 50 ms intervals, bounded to two seconds. QuickShell itself was measured at
about 0.5 seconds to load on the physical Hub; the normal ready path therefore
removes approximately 3.9 seconds of artificial latency while retaining a
readiness barrier for the historical portal/layer-shell race.

The owner clarified the complete contract on 2026-08-13. `Super+H` in the
exact Hub attaches to the one persistent Host-owned PTY; it must never launch
an Environment-local Codex or a second Host Codex. Closing the graphical
window only detaches, and reopening it reattaches the same Bash and foreground
program. Direct process evidence confirmed that the current Codex is the sole
foreground Codex under `apx-host-console-v1.service`.
The Hub opener focuses an existing `APX HOST ROOT` window; only when no such
window exists does it open a client that reattaches to that persistent PTY.

The paragraph above supersedes the earlier E/M assignment: `Super+M` is now
Hyprland's internal `hl.dsp.exit()` dispatcher and `Super+E` opens the menu.

During this investigation an ad-hoc `machinectl shell apx@apx-hub` diagnostic
login caused logind to remove the graphical session's `/run/user/1000` after
that transient login closed. This unlinked the Hyprland and QuickShell sockets.
Do not create user machinectl login sessions inside an active graphical
Environment; inspect through its existing PID namespace or root-only paths.

The owner rejected `Super+M` for Environment transitions and selected
`Super+E` as the memorable, service-independent emergency escape. The normal
graphical button remains the authenticated Work-to-Hub path, `Super+F` opens
files, and the later clarification above assigns `Super+M` only to opening the
menu. Exiting the Work compositor
lets the Host supervisor clean it and restore Hub; exiting Hub restores the
basic Host terminal on tty1. `Ctrl+Alt+F1` remains an immediate visual fallback.

The physical system currently has the exact Hub active with one Kitty attached
to the one persistent Host PTY/Codex. The Host-console broker, Environment
switch service and Hub graphical unit are active with no failed Host units.
See `CURRENT_HANDOFF.md` for the latest checkpoint.

## Host-driven repeated Environment return — 2026-08-12

The physical Work return defect is closed. The authenticated Host endpoint now
stops the exact active workload outer unit asynchronously; the workload client
does not invoke `hyprctl` and receives no generic stop authority. Peer
PID/UID/GID mapping, active root-published state, cgroup lineage, trusted
registration, generation and supervised-handoff lock remain mandatory.

The handoff supervisor releases its own inode-matched lock before waiting for
the restored Hub, allowing a new Hub-to-workload transition without an old
runner being able to unlink a newer lock. Boot reconciliation dynamically
repairs stale running state for all trusted `graphical-base` v2 registrations.
QuickShell reports refusal text, suppresses repeat requests after acceptance,
and Host journal entries identify accepted/rejected operations. The owner then
selected `Super+E` as the executor-independent recovery escape on Hub and
workloads. `Super+M` opens the menu but performs no direct transition; the file
manager moved to `Super+F`. The graphical button remains the normal typed
return path.

Repeated physical Hub → Work → Hub cycles passed, including three additional
complete cycles at 07:29, 07:30 and 07:31. One restored Hub stayed healthy for
more than 23 minutes with repeated healthy watchdog results; final cleanup left
both registrations stopped and no machine, active record or lock.
The repository passes 1019 tests with 11 expected skips. Installed artifacts
match source and exact pre-change backups are retained. Generic boot
reconciliation is installed and unit-tested but awaits the next normal reboot
for physical evidence. See
`docs/environment-switch-round-trip-hardening-v2-2026-08-12.md`.

The final owner-facing state after a clean 07:34 exit is Hub and Work stopped,
tty1 free, the switch service active, no handoff lock and no failed Host units.

The owner-selected `Super+E`/`Super+F` bindings are installed in Hub, Work,
both reviewed graphical seed formats and the creation runtime. A direct Hub
compositor exit restored tty1 at 10:10:50. Two attempted direct Work proofs
were pre-empted by the normal typed button return; physical `Super+E` in Work
therefore remains pending observation and is not claimed as proven.

## Persistent Host-console attachment staged — 2026-08-12

The owner confirmed that a Hub failure or Environment transition can remove
the graphical Host-console window while its Host-root Codex remains active and
retains the conversation writer. The Host-console broker now stages one
persistent in-memory PTY: client loss detaches rather than terminates it, and a
later exact authenticated Hub client reattaches to the same Bash/Codex. Output
is drained into a bounded 1 MiB memory buffer while detached; nothing new is
persisted to disk. `exit`/Ctrl-D ends the shell, and restarting the broker is
the recovery/forced-termination path. Single attachment, exact Hub lineage and
workload exclusion remain enforced.

This is implemented, covered by repository tests and installed byte-for-byte on
the Host, but cannot be activated by restarting the live broker from the Codex
session that currently depends on that broker. The graphical round trip is now
proven; a post-session service restart and proof that the same persistent PTY
reattaches after that round trip remain required. See
`docs/exact-hub-confirmed-host-console-v1-2026-08-03.md`.

## Work Environment v1 and contextual switch control — 2026-08-12

The first normal non-Hub graphical Environment now exists. `work` is registered
as **Work**, category `work`, role `graphical-base`, generation
`23408376-1cfc-4fe2-aeb9-c4f185c5c9c3`, from sealed release
`hyprland-base-v2`. Its independent Btrfs root/home are capped at 32/64 GiB.
The Work image has Firefox plus the base's Rofi, Thunar/GVFS, Flatpak/Flathub,
notifications, portals, Polkit and removable-media support. Its private home
contains the normal XDG directories and explicit default associations.

Work keeps the Hub's dark/cyan visual language but has Environment semantics:
its bar identifies `APX · WORK · VOLTAR AO HUB`, `Super+D` launches Rofi,
`Super+F` opens Thunar and `Super+B` opens Firefox. The button requests a typed
return to Hub; `Super+E` directly exits the compositor for recovery and
`Super+M` only opens the menu; it is not a direct transition shortcut. It does not expose Host console, Host power, coordinated update
or Environment-management controls. Host `/var/lib/apx` and `/root/.codex`
remain hidden from its namespace.

The Hub control now identifies `APX · HUB · ENVIRONMENTS` and its menu reports
catalogue state, session policy and update policy. The switch service serves a
stable live bridge beneath the root-owned Hub home bridge as well as the
per-launch socket; peer PID/UID/cgroup/active-identity admission remains
mandatory. A Hub-namespace proof sees Work in the catalogue. Work's Hyprland
configuration passes offline parsing. A physical supervised run then kept the
Work compositor and Waybar active for approximately 42 seconds, exited cleanly
and launched Hub, proving the Work → Hub round trip.

That physical run closed three incompatible assumptions: official-Hub process
discovery is now scoped to its systemd unit; the generic launcher supplies the
current full graphics policy to the shared session; and authenticated return
requests from a normal Environment no longer require an impossible QuickShell
parent when Waybar or a Hyprland binding launched the client. Work also exports
its Wayland variables to D-Bus activation before portal consumers start.

The complete repository regression now passes 1011 tests with 11 expected
hardware/external-condition skips. Installed runtime, switch service/client,
session launcher and switch unit match their source versions; Host failed-unit
count remains zero.

The new Work account is locked pending owner-selected local-password
enrollment. Password-required sudo policy and wheel membership are present;
no Hub credential, temporary credential or `NOPASSWD` authority was copied.
Desktop use does not depend on sudo, but the stopped/first-launch enrollment UX
is an explicit remaining product gap. Full details are in
`docs/work-environment-v1-2026-08-12.md`.

## Conversation lock and Environment handoff correction — 2026-08-11

An apparently blocked earlier Codex conversation was traced to a still-running
Host-root `codex resume` process on tty1. It was waiting at an approval prompt
after the owner had moved away from that console, so its per-thread writer lock
was working as designed. The process was terminated gracefully; the recorded
conversation remains resumable. This also confirms that temporary Host-root
Codex consoles share `/root/.codex` and are not Environment-local development
sessions. Normal APX use must place development tooling and its state inside a
dedicated Development Environment home.

The same inspection caught an incompatible same-day change to the direct-Hub
boot unit. `Restart=always` would relaunch the boot-owned Hub after the normal
clean exit used by the Hub-to-workload handoff, racing the handoff supervisor.
The unit is restored to `Restart=on-failure`: boot failures remain restartable,
while an intentional clean transition remains under the switch supervisor.

## Emergency boot recovery and normal graphical base v2 — 2026-08-11

The reboot regression is recovered without replacing or restarting the live
Hub again.  The internal AMD backlight changed from `amdgpu_bl2` to
`amdgpu_bl1`; the Host power authority now resolves the one backlight attached
to PCI `0000:05:00.0` on every boot instead of pinning the kernel's transient
number.  The graphical watchdog now accepts the exact single Hyprlock login
process before authentication, so it no longer tears down a healthy Hub merely
because the owner has not typed the password within twenty seconds.  A missing
optional power socket degrades only those controls rather than blocking the
desktop. Host Ollama no longer uses a one-shot `ExecCondition`: the service
creates the ephemeral NVIDIA device nodes before startup, probes the GPU
without making that instant a permanent gate, and retains Ollama's CPU fallback
plus bounded restart behavior. This closes the Hybrid-mode runtime-resume race
that left a healthy mounted SSD with the model permanently off. Host
failed-unit count is zero.

The current Hub is running at its deliberate login screen on tty2.  Normal
interactive boot opens no terminal.  Its outer service has CPU quota 600%, CPU
and I/O weight 200, memory high/max 10/12 GiB and 4096 tasks.  Btrfs qgroup
accounting is consistent; Hub root is capped at 16 GiB and home at 32 GiB,
while creation reserves 96 GiB for Host recovery.  The filesystem currently
has approximately 449 GiB available.

`hyprland-base-v2` is now a sealed read-only 540-package graphical release.
It contains a valid Arch signing keyring, generated `en_US.UTF-8` and
`pt_PT.UTF-8` locales, password-required Environment-local sudo, `base-devel`,
Git, `less`, Kitty, Hyprland/Hyprlock, Quickshell, Thunar/GVFS, notifications,
keyring, portals, UDisks/Udiskie, Flatpak and the normal desktop utilities.  It
enables networkd/resolved and the paccache timer and carries the system Flathub
remote.  A disposable boot proved PID 1, logind, D-Bus, a `systemd --user`
manager and user bus; another isolated run proved the network stack stays
without Internet until the Host-side APX egress policy is applied, as designed.
The creation contract, catalogue, generic launcher and switch service all now
agree on release/config seed v2.  Existing Hub state is not cloned into new
Environments.

The live control centre uses scale `1` at the desktop's native 150% output
scale after the 100% trial was found too small.  Its Adwaita symbolic SVGs go
directly through Qt `ToolButton.icon`; the texture plus `MultiEffect` resampling
path is absent.  Final perceived sharpness still needs owner inspection after
unlock.  BlueZ discovery is real and has observed nearby devices; pairing a
specific owner-selected device remains the required physical proof.

The complete repository regression passes 1004 tests with 11 hardware/external
condition skips.  Remaining normal-computer gaps are generic hot-plug and
owner-approved device routing, a real Bluetooth pair/audio proof, background
continuity/session restore, mediated cross-Environment file transfer, backup
UX, accessibility certification and the actual creation UI behind the
Environments button.  These are the next product milestones, not hidden
claims of the v2 base.

## Host/Hub daily usability correction — 2026-08-11

The physical pilot's direct Host console remains a fixed Host-root Bash PTY,
but it now advertises the Host-supported `xterm-256color` terminal profile.
The earlier `xterm-kitty` value had no matching Host terminfo entry and caused
ordinary terminal commands such as `clear` to fail. Kitty remains only the
graphical terminal emulator; this compatibility correction does not change the
console's authority.

Normal interactive Hub startup no longer opens Kitty automatically. The
automatic window is retained only by the bounded `--test` certification path,
where it proves terminal integration. Environment-local sudo remains present,
password-required and unrestricted inside the Hub; container root stays mapped
away from Host root. `brave` is not an Arch repository package, so that name
still cannot be installed directly with pacman even when sudo succeeds.

The owner then reproduced `apx is not in the sudoers file` in the already-open
Hub session. The account database was correct, but the graphical launcher used
an explicit supplementary-group list that omitted `wheel`. The session list
now includes the exact wheel GID, and the password-required policy also names
`apx` explicitly so the live session is repaired without a restart. This
remains Environment-local and does not add `NOPASSWD` or any Host authority.

The same running session exposed a separate desktop-origin defect: Hyprland was
started with working directory `/`, so ordinary Kitty windows inherited the
root-owned filesystem root instead of `/home/apx`. The shared graphical session
now changes to `/home/apx` before starting the compositor, covering the Hub and
future graphical Environments. The live Hub binding also launches Kitty with
`--directory /home/apx` and was reloaded without restarting owner work.

The live Bluetooth v3 scan was observed with BlueZ `Discovering=yes` and found
nearby devices. Pair/connect support is implemented, but a real peripheral
still needs an owner-selected physical pairing proof. The Hub control-centre
icons now request device-pixel-aligned SVG textures and use 16 logical pixels;
press feedback was shortened. A first owner-requested 100% physical trial was
too small and exposed pixelated icon corners. The accepted follow-up is 125%
physical (`5/6` inside the 150%-scaled desktop), while the bar and other windows
remain unchanged. Control icons now use Qt's native icon source/color pipeline;
the hidden texture plus `MultiEffect` post-processing path was removed. This
was live-reloaded and captured at 1920x1080. Full evidence is in
`docs/host-hub-usability-investigation-2026-08-11.md`.

The first owner-driven AUR build exposed interactive starvation and package
freshness gaps. The Hub had no memory or I/O pressure, but recent CPU pressure
reached 24% over 60 seconds while Go compiled and compressed `yay`; build work
and the compositor share the Environment's intentional 200% CPU quota. Regular
Kitty terminals now keep the emulator at normal priority but start their Bash
workload at nice 10 and idle I/O priority, protecting Hyprland/Quickshell. The
already-open shell was adjusted live. The failed Brave dependency transaction
used pacman databases last refreshed on August 1 and requested an `nspr`
signature no longer present beside the cached package; the safe recovery is a
full `pacman -Syu`, not disabling signatures or performing a partial refresh.
`less` is also absent from the current base and is a required next-base package.

The follow-up normal-Linux gap audit found two additional P0 consistency
blocks. The Hub root and home qgroups have no limits, Btrfs reports quota data
inconsistent/rescan-needed, and the Environment sees the Host's full 476 GB;
general Environment creation must not claim storage isolation until accounting
is healthy and enforced. Inside the running Hub, `systemd-logind` is failed and
`user@1000.service` is inactive, leaving no normal user service manager. The
next common base/session must close these gaps plus notifications, secret
service, portal round trips, locale generation and explicit update policy.
Details are in
`docs/environment-consistency-and-normal-linux-gap-audit-2026-08-11.md`.

## Host-local coder on target-bound external SSD — 2026-08-05

The owner explicitly replaced the previously deferred Development-only local
model plan for the current physical pilot: the exact connected Samsung 870 QVO
1 TB is now dedicated model storage, while Ollama and Qwen Code run on the Host
and become available only with that SSD. The old NTFS content was intentionally
destroyed after exact disk identity, non-use and healthy SMART evidence were
proved. The SSD is now one TPM2/PCR-7-bound LUKS2 volume containing Btrfs and a
private `/var/lib/apx/model-store` mount.

An exact-identity udev/systemd adapter validates the physical disk, partition,
LUKS and filesystem before mounting. It then starts a separate Host Ollama
service bound to the SSD lifecycle. The API is loopback-only, cloud-disabled
and configured for a 32K working context; Vulkan detects the 6 GB RTX 3060 via
NVK. The selected model is `qwen3-coder:30b` because its approximately 19 GB
artifact fits the 28 GiB system RAM, while the 48.4 GB minimum official
Qwen3-Coder-Next representation does not. Qwen Code and the guarded
`apx-local-code` launcher provide the Codex-like terminal workflow with normal
confirmation, never unrestricted mode.

This is an owner-accepted physical-pilot deviation from Environment-local
application ownership, not a new general APX architecture rule. The model API
is not exposed to Hub or workloads. There is deliberately no stored LUKS
recovery key because only replaceable public artifacts live on the disk; a TPM
policy loss requires recreating and redownloading the store. Do not hot-unplug
while the model is active. Exact implementation, remaining physical evidence
and rollback are in
`docs/host-local-coder-external-ssd-v1-2026-08-05.md`.

## Lenovo Legion GPU and thermal profiles staged — 2026-08-04

The exact Hub battery menu now has working Quiet, Normal and Performance
firmware profiles plus AMD-only, Hybrid and NVIDIA GPU policies.  Physical
discovery proved platform profiles `low-power/balanced/performance`, Hybrid
Graphics support, and no firmware iGPU-only support on this 82JU.  Accordingly,
AMD-only is an explicit APX device-exclusion policy while Hybrid and NVIDIA use
the Lenovo MUX.  GPU changes require a Host-enforced confirmation and reboot;
the boot launcher now resolves AMD/NVIDIA DRM nodes dynamically.  No GPU change
or reboot was executed during staging.  See
`docs/legion-hardware-profiles-v1-2026-08-04.md`.

## Secure Boot, measured UKI and TPM unlock staged — 2026-08-03

The owner selected verified boot plus TPM automatic LUKS unlock to remove the
remaining pre-boot password. UEFI/TPM2/SHA-256 support is confirmed, and the
first signed LUKS-only UKI boot passed physically with `Measured UKI: yes` and
`Measured OS: yes`. LUKS password slot 0 remains intact and no TPM token exists.
The normal signed image is now `/EFI/APX/apx-system-v1.efi`; the duplicate
auto-discovered image was archived off the ESP, the normal menu is hidden with
timeout zero, and the retained verbose entry is named `APX Legacy Recovery
(LUKS)`. The UKI uses `quiet splash`, while tty1 alone remains the automatic
recovery console so a tty2 getty cannot interfere with the graphical handoff.

The APX-signed systemd-boot vendor and fallback images verify correctly. The
owner cleared the firmware keys, enrolled the custom APX keys, corrected the
PXE-first firmware order and enabled enforcement. Physical Host evidence now
proves `Secure Boot: enabled (user)`, `Measured UKI: yes`, `Measured OS: yes`,
current entry `apx-secure-boot-v1.conf` and current stub
`/EFI/APX/apx-system-v1.efi`. LUKS still has only password slot 0. TPM PCR-7
unlock is now technically eligible but remains pending until the APX session
password is explicitly set and the new login gate is proven. See
`docs/secure-boot-measured-uki-tpm-unlock-v1-2026-08-03.md`.

## APX login, idle lock and clean transition staged — 2026-08-03

The owner selected the Windows-like split where TPM unlocks encrypted storage
and a normal APX password unlocks the graphical session. The Hub already has
`hyprlock`, `hypridle` and a password-bearing `apx` account. The owner privately
set that password, and the installed source-matched Hub runner now adds a
Hub-matched initial hyprlock, five-minute idle lock and ten-minute DPMS off; it
deliberately adds no automatic suspend, Host account or display manager. Static
and isolated parser checks pass. The existing `BLOQUEAR` control must now prove
the password before the first boot-time activation.

The ugly Host flash was proven to be exactly one tty1 recovery getty, not
accumulating terminals: one task, 544 KiB live memory and 15 ms CPU at the
inspection point. The installed boot launcher now clears tty1 before starting
the Hub without removing that recovery getty or adding a persistent process.
The next physical boot must prove the clean transition. See
`docs/apx-login-idle-and-clean-transition-v1-2026-08-03.md`.

## Bluetooth v3 and dynamic Environment identity awaiting relaunch proof — 2026-08-03

Host shared-services v3 now has a closed interactive Bluetooth pairing and
device-management protocol while v1/v2 remain rollback endpoints.  Pairing is
Host-global and active-Environment controlled; PIN/passkey material uses only a
no-echo PTY and socket body.  The service and current Hub UI are installed with
backups, but the already-running Hub retains the old bind-mounted socket inode
after service restart.  One clean Hub relaunch, authenticated scan and a real
owner-selected peripheral proof remain required.  HID hotplug and Bluetooth
audio data-plane handoff remain separate uncertified work.

The switch endpoint now derives a bounded catalog from trusted Host
registrations.  Only the authenticated Hub can list/select workloads; each
active workload receives only its own identity and can only end its compositor
so the Host supervisor returns to the Hub.  Display name/category have safe
defaults.  Installed/source hashes match, but the new mount awaits the same Hub
relaunch and Hub/workload round-trip proof.

Per-Environment application session restore is accepted intended architecture:
disabled by default, persistently toggled, prompt-per-exit, Environment-local
manifest and explicit browser/LibreOffice adapters.  It is not implemented or
certified, and generic process checkpointing is not adopted.  See
`docs/bluetooth-control-and-cross-environment-handoff-v1-2026-08-03.md` and
`docs/environment-catalog-identity-and-session-restore-v1-2026-08-03.md`.

## HUB fictício switch trial retired — 2026-08-03

The owner explicitly retired the stopped disposable `hub-ficticio` generation
`441ed74c-c89f-47ae-8102-1ce3e09e6b47`. The normal digest-bound APX destroy
flow unpublished it and deleted its independent root and Home subvolumes.
Postconditions showed only the official Hub in the catalogue and only
`apx-hub` running. A historical red-shell copy remains solely in the
root-owned environment-switch backup directory; it is not registered or
launchable. The trial history remains in
`docs/hub-ficticio-environment-switch-trial-2026-08-03.md`.

## Direct Hub boot confirmed; graphical LUKS transition active — 2026-08-03

The owner selected direct Hub entry after LUKS rather than a display manager.
The systemd-boot timeout is now zero while its fixed default and disabled editor
remain. The owner confirmed that the boot menu/root prompt disappeared and the
exact Hub launches after encrypted-root unlock. Plymouth `spinner` is installed
in the rebuilt initramfs so the still-required LUKS secret has a graphical UI.
Root tty1 remains recovery. No Host user, PAM rule, display manager, TPM token
or automatic LUKS unlock was added. The owner subsequently proved the signed
measured UKI; Secure Boot enforcement and TPM unlock remain staged separately.
The Plymouth screen itself still needs visual capture for aesthetic audit. See
`docs/direct-hub-boot-v1-architecture-and-pending-result-2026-08-03.md`.

## Exact-Hub direct Host console checkpoint — 2026-08-03

The live official Hub now has one `TERMINAL DO HOST` button backed by the
separate enabled `apx-host-console-v1` service. A click immediately opens one
fixed Host-root Bash PTY; the extra phrase/token confirmation was removed at
the owner's request. The Host still enforces exact official-Hub peer and
Quickshell ancestry plus a single-console lock. There is no command field or
network endpoint. The socket is inactive
`root:root 0600`, leased only by the exact Hub launcher, and explicitly omitted
from general workload launch.

This is intentionally full Host authority and weakens operational separation
after the deliberate button click; it cannot make an unrestricted root shell safe.
The initially proposed return-to-tty button and operation were removed at the
owner's request. The first Codex TUI appeared black because Kitty's terminal
dimensions were not forwarded. `TIOCSWINSZ` plus `SIGWINCH` now applies the
initial size; `stty size` observed `31 100`. Audit/process checks proved both
user-opened consoles closed and left no Bash/Kitty/client/Codex orphan. See
`docs/exact-hub-confirmed-host-console-v1-2026-08-03.md`.

## General graphical handoff and Host controls checkpoint — 2026-08-03

The shared graphical path is now implemented for admitted `graphical-base`
Environments while preserving independent homes, configurations and packages.
Physical bounded proofs passed for both the Quickshell/Kitty Hub and the
Waybar/Alacritty `test` Environment, including exact input, ALC287 audio,
Wi-Fi/Bluetooth, tty1 restoration and zero residue. Host-service/audio/update
sockets are `root:root 0600` while inactive and are leased only to the translated
active user; shared services/audio accept the active graphical identity, while
updates and physical power remain Hub-only.

The live Hub now provides unprivileged BLOQUEAR and Host-mediated SUSPENDER in
addition to reboot/poweroff. Suspend locks first, respects update/sleep blockers
and preserves the active Environment. Hibernation and all new recovery work are
deferred. Creation planning defaults to `follow-host` and supports explicit
exclusion, but the production graphical creation screen is still unfinished.
The coordinated preview is ready with no exclusions; no package mutation was
useful or executed. See
`docs/general-graphical-handoff-and-host-controls-2026-08-03.md`. The complete
suite passes 939 tests with 11 skips.

## Host system-power v1 checkpoint — 2026-08-03

The Hub-authored power-actions proposal was accepted and implemented as the
separate enabled `apx-system-power-v1` Host service. The live exact Hub now has
functional REINICIAR/DESLIGAR controls with Host-enforced prepare, a random
30-second single-use confirmation, cancel, blockers and status. There is no
shell or arbitrary argument surface. Mutations require the existing exact-Hub
peer proof plus a direct Quickshell parent; tokens travel over stdin/socket and
are absent from arguments and audit.

Because private user namespaces use dynamic translated IDs, the proposed fixed
Host group was replaced by a safer session lease: the socket is `root:root
0600` while inactive, `0660` for only the translated active user, then closed
again during recovery. Power and updates share a transition lock/reservation.
The runner rechecks inhibitors/update state, closes the Environment, proves no
machine remains and only then calls Host logind. The first owner-requested real
poweroff exposed concurrent recovery by the foreground launcher and power
runner: one deleted device-lease state while the other still expected it, so
the Environment closed but Host poweroff correctly failed closed. Recovery is
now serialized, and the runner first quiesces the one exact root interactive
Hub supervisor before invoking recovery. Source/installed hashes matched and
19 focused tests passed at that checkpoint. See
`docs/system-power-v1-architecture-and-result-2026-08-03.md`. The complete
suite passes 935 tests with 11 skips.

The subsequent real REINICIAR proof confirmed recovery but exposed that
`loginctl` on systemd 261 has no reboot/poweroff verbs. Those two terminal
actions now use target-confirmed `systemctl --no-block reboot/poweroff`;
suspend remains `loginctl suspend`. The daemon's runner launch is asynchronous
and a vanished Quickshell client no longer kills the authority. The owner then
proved a real reboot with a changed boot ID. Installed/source runner hashes
match, and the current focused secure-boot/power/launcher suite passes 24 tests.

## Coordinated updates and active audio physical checkpoint — 2026-08-03

The physical pilot now has enabled, authenticated Host services for coordinated
updates and machine-continuous audio state. The exact Hub exposes `[ UPDATE ]`,
requires a preview and confirmation, uses root-only operation staging, creates
independent Btrfs rollback snapshots, stops on first failure and never reboots
automatically. New Environments follow the Host by default; explicit exclusions
are persisted. Packages, applications, files and PipeWire graphs remain
separate per Environment.

The exact ALC287 playback and capture nodes are leased only to the translated
user of the active official Hub. Output/input volume and mute persist in a
root-owned bounded state, and the live Hub has a one-second microphone activity
indicator. A bounded physical proof passed authenticated update preview, real
sink/source publication and complete device revocation, then restored tty1
with no residue. No mass package mutation was executed, and cross-Environment
audio still awaits the general graphical launcher plus destructive two-target
certification. Details are in
`docs/coordinated-updates-and-audio-physical-result-2026-08-03.md`. The suite
passes 927 tests with 11 skips.

## Host shared services v3 checkpoint — 2026-08-02

The owner-authored Hub proposal for Host-owned shared services has been
reconciled and its first v3 slice is installed beside v1/v2. The v3 endpoint
provides a versioned typed contract, capabilities, structured errors, detailed
Wi-Fi objects, snapshot, bounded events and safe Wi-Fi operations including a
new protected-network credential path. The credential travels only through the
Unix-socket body and a no-echo PTY to iwd; it is absent from arguments, logs and
temporary files. Mutations are serialized and audit records omit payloads.

The current mutable Quickshell uses a compatibility adapter: Wi-Fi comes from
v3 and Bluetooth remains on v2. A bounded physical proof passed v3
authentication, capabilities, snapshot, events, detailed Wi-Fi state,
Quickshell and the complete existing graphical/recovery ladder. v1/v2 remain
active rollback boundaries. A real new protected AP and two distinct graphical
Environments were unavailable, so credential enrollment and A-to-B persistence
are not yet physically certified. The exact official-Hub peer proof remains the
authorization boundary until the pending general graphical launcher exists.

Battery, Bluetooth controller and time are exposed read-only in the snapshot.
Host-global audio is not adopted: the current playback-only Environment-local
PipeWire boundary remains until capture/privacy and routing are designed.
Power mutations and Host updates require separate higher-risk services rather
than inheriting the desktop-status authority. Details and rollback are in
`docs/host-shared-services-v3-architecture-and-result-2026-08-02.md`.

## Coordinated updates and active-audio decision — 2026-08-03

The owner selected coordinated updates as the default policy. An update
requested through the authoritative Hub includes the Host and every Environment
with `follow-host`; new Environments default to that policy and expose a checked
creation control, while explicit opt-out records `excluded`. Equal coordination
means one frozen signed repository view and one transaction, not identical
package sets. Each target resolves its own installed packages, receives an
independent snapshot and is applied offline. Any running/unsnapshottable target
or incomplete private staged package set blocks the whole operation; first failure stops the
transaction and retains rollback sets.

The owner also selected machine-continuous audio settings with exclusive active-
Environment device authority. Output/input volume, mute and selected devices
are handed from the outgoing session to the incoming session. Local PipeWire
graphs remain per-Environment; playback and capture leases must be revoked and
proven inaccessible before the next Environment receives them. The exact
physical Hub now admits capture; cross-Environment handoff still requires the
general graphical launcher and a separate two-Environment proof.

Policy/planning contracts, creation metadata, physical preview/executor services
and exact-Hub microphone state are installed. Real mass package mutation and
cross-Environment microphone handoff are not yet certified. See
`docs/coordinated-updates-and-active-audio-architecture-v1.md`.

## Cross-Environment data and notification boundary — 2026-08-03

The owner rejected a shared reusable package-download cache, shared folders and
a cross-Environment file portal. Environment files do not cross the boundary
through an APX convenience mechanism. Package update bytes may exist only in
root-owned, operation-private coordinator staging that is invisible to every
Environment and is not reused as a common Environment cache.

Application notifications remain Environment-local by default and are not
aggregated into a global notification history. An inactive Environment cannot
continue publishing visible notifications. Host-originated machine alerts such
as critical battery, thermal/storage failure, update result or required reboot
remain eligible for a separate Host alert channel because they describe the
computer rather than an Environment application. Any future exception for
application notifications requires a new explicit owner decision.

## Official Hub owner-bootstrap checkpoint — 2026-07-31

## Official Hub health watchdog and shell containment — 2026-08-02

The official Hub interactive path no longer has a fixed four-hour expiry.
Normal sessions arm an independent Host watchdog whose first check runs after
60 seconds and repeats every 30 seconds. It validates the exact registration,
active-session record, outer/machine/inner units, Hyprland process and socket,
`eDP-2`, and admitted keyboards. One or two consecutive unhealthy observations
are degraded; the third invokes exact recovery. Healthy observations clear the
failure counter, while an already stopped session is inactive. The bounded
certification path retains its independent 75-second expiry.

A physical interactive run produced seven consecutive healthy watchdog results
before normal owner exit, then restored tty1 with no machine or runtime
residue. The watchdog recovery sandbox now permits the exact seatd socket write
needed to unlink it while retaining `ProtectSystem=strict`.
The complete repository suite passes 905 tests with 11 skips.

Quickshell failures observed in older sessions were separate from the
four-hour session expiry and included Qt Wayland/Core crashes. The live mutable
Hub's runner now prevents duplicate instances, preserves rotating verbose logs
and exit status in the Hub Home, and falls back to Waybar. The owner's live QML
was not overwritten and Quickshell remains an unpromoted Hub-only trial. See
`docs/official-hub-health-watchdog-and-shell-stability-2026-08-02.md`.

## Official Hub private-users local-admin checkpoint — 2026-08-02

The exact-generation official Hub graphical bridge now combines a dynamic
65,536-ID private user namespace, idmapped Home and functional
password-required Environment-local sudo. Container root maps to a high Host
UID/GID and the authenticated Host services continue to accept only translated
container UID/GID 1000, rejecting Environment root.

Host `seatd` provides the admitted AMD primary DRM/input/tty descriptors. The
remaining exact GPU and playback-audio nodes use ephemeral private character
nodes under `/dev/apx-official-hub-device-leases-v1`, individual binds and an
outer `DevicePolicy=closed` catalogue. `/run` was rejected as a proxy location
because its `nodev` mount flag caused the observed Mesa permission failure.
All proxy state is removed during recovery.

A bounded physical certification passed Hyprland/eDP-2, both keyboards, ELAN
input, Quickshell, Kitty, local playback, authenticated Host menus, AMD display,
NVIDIA NVK offload, `private_users=true` and `local_admin=true`, then restored
tty1 with no machine or unit residue. The temporary exact sudoers proof was
removed. Bluetooth certification now preserves its initial power state; it was
on before and after the final proof. Diagnostic `strace` and `libunwind` were
removed while signed Host `seatd` remains. The complete repository suite passes
902 tests with 11 skips. Details are in
`docs/official-hub-private-users-local-admin-result-2026-08-02.md`.

This is still a target-bound, exact-generation physical-pilot adapter. It does
not yet establish the general graphical Environment launcher or production
device mediation.

A later owner entry proved that an auxiliary AMD-open preflight was not an
authoritative readiness check: it ran in a separate transient inner service
whose device context could be denied even when repeated real compositor proofs
passed. It is removed. The bounded Hyprland renderer/socket/eDP-2/input
readiness remains the fail-closed authority and still triggers full recovery
on failure; the device catalogue is unchanged.

The corrected launcher passed the full certification and the real interactive
path reached the Hyprland socket before controlled Host recovery. Its
installed/source SHA-256 is
`7cb78f591254980248ffc48ef1d35caacbe849b860bab2d4186d4c319ce1ef7f`.

## Quickshell ASCII trial and temporary Hub Codex — 2026-08-01

The live mutable Hub now starts the first `config/quickshell-ascii-v1` shell:
ASCII/monospace bar, cyan accents, slightly rounded compact popovers, outside-
click dismissal and scrollable Wi-Fi/Bluetooth/audio/battery content. The
existing typed Host service clients and Environment-local PipeWire controls
remain the authority; Quickshell does not bypass them. Waybar remains installed
as automatic fallback. This is intentionally a Hub-only visual trial and is
not yet the common graphical seed or an immutable release change.

At the owner's explicit request, Codex CLI 0.146.0 plus its Node/npm runtime is
temporarily installed under the Hub user `apx`; its PATH is local to that user.
No Host/root credentials were copied and the user must run `codex login` in the
Hub. This tooling is not in `desktop-essential-v1` or any Environment template.
The complete result and physical proof are in
`docs/quickshell-ascii-v1-and-hub-codex-result-2026-08-01.md`.

## Host-owned desktop services checkpoint — 2026-08-01

The later context-menu/NVIDIA checkpoint is documented in
`docs/desktop-context-menus-v2-and-nvidia-result-2026-08-01.md`.
`apx-host-services-v2` is installed beside v1 and the official Hub now opens
ASCII menus for Wi-Fi, Bluetooth, local audio and battery. Host mutations are
closed to known iwd networks, explicit Bluetooth power state, and already
paired BlueZ addresses. New secrets and pairing are not exposed. Audio output
selection remains Environment-local; battery power modes remain unavailable.

The Host's existing nouveau driver remains kernel owner of the RTX 3060. The
official Hub launcher now leases only its exact render node, while AMD still
owns the display. Signed Hub-local NVK userspace passed a physical
`DRI_PRIME=1!` Vulkan proof identifying the RTX 3060. The common Waybar seed
contains the menu bindings, but normal graphical Environments cannot yet use
Host controls or NVIDIA: their admitted general graphical launcher and a new
reproduced immutable base release remain pending. `hyprland-base-v1` was not
mutated.

The interactive launcher was subsequently corrected after an owner launch
exposed that it was incorrectly running the `--test` Bluetooth/Wi-Fi/NVIDIA
certification path during normal entry. Mutating proof routines are now
strictly test-only. A real interactive run remained active for 1 minute 54
seconds and recovered to tty1; final Bluetooth was off with no machine or
failed-unit residue. The failure message was a launcher-mode bug, not a BlueZ
service failure.

The owner confirmed that hardware-global essentials belong below Environments
on the Host. `apx-host-services-v1` is now implemented, installed, enabled and
physically verified. The complete architecture and evidence are in
`docs/host-services-v1-architecture-and-result-2026-08-01.md`.

The Host preserves its existing `iwd` Wi-Fi backend; NetworkManager was not
installed. Host `systemd-timesyncd` is enabled and synchronized. Signed BlueZ
5.87-2 and bluez-utils 5.87-2 are installed with `bluetooth.service` enabled;
the final controller state is powered off. No corresponding hardware-owner
daemon is enabled inside Environments.

The first socket protocol provides sanitized status and one fixed mutating
operation, `bluetooth-toggle`. It authenticates the exact active official Hub
by root-owned active state, registration, UID, cgroup and compositor identity.
The common Waybar seed now displays Host Wi-Fi, Bluetooth and NTP state through
the fixed client. A click on Bluetooth invokes only the typed toggle. The
bounded physical proof verified Host services, iwd, NTP, BlueZ, a Bluetooth
on/off round trip, Waybar, audio, graphics/input, tty1 recovery and zero machine
residue. Wi-Fi switching, new credentials, Bluetooth discovery/pairing and
future workload-launcher authorization remain separate pending protocols.

The owner has now selected `desktop-essential-v1` as the common minimum for the
Hub and all newly created graphical Environments. It is installed as a
root-owned, digest-bound Host profile and `waybar-ascii-v1` seed. The creation
runtime copies it independently after the immutable release seed and before
publishing registration; it does not clone the mutable Hub. Automatic physical
creation was proved with stopped `codex-test-essential-v1`, generation
`7ba06c0e-e7fe-4bb4-abcf-3d7ae5682c35`, whose Waybar files exactly match the
Host seed without a manual overlay. The detailed result is
`docs/desktop-essential-v1-physical-result-2026-07-31.md`.

The essential local package baseline is already present in the current Hub and
graphical base: IP inspection tools, complete local playback audio, timezone
data, and Waybar. `pavucontrol` remains an optional advanced local interface
and is present in the Hub. Physical Wi-Fi, kernel time/NTP, and Bluetooth remain
Host-owned. Network status works through private `host0`; Bluetooth now has
authenticated Host status/power mediation, while pairing remains pending. No competing
NetworkManager, BlueZ daemon, or time synchronizer is enabled in Environments
by the profile.

The complete repository suite now passes 897 tests with 11 skips.

The later Waybar/audio checkpoint is recorded in
`docs/waybar-ascii-v1-physical-result-2026-07-31.md`. The authoritative Hub
now has the owner-approved ASCII Waybar profile and Hyprland autostart. Its
exact-generation launcher physically verified Environment-local playback
audio and Waybar readiness while excluding capture. Network status truthfully
represents private `host0`, not ownership of Host Wi-Fi. Bluetooth was blocked
at that earlier checkpoint and is superseded by the 2026-08-01 Host service.

A reviewed `config/waybar-ascii-v1` source profile now defines the common Hub
and normal-Environment appearance; only the normal profile adds the workspace
selector immediately after the date. Disposable stopped Environment
`codex-test-waybar-v1`, generation
`1df14250-c628-49d4-961e-44ad22fd67a4`, was independently created from
immutable `hyprland-base-v1` and received its own copy. The profile is not yet
an admitted replacement release, and the APX visual button is not functional:
the installed graphical executor prototype is bound to superseded generations
and the official Hub lacks the matching typed client/session bundle. The
earlier Waybar-only checkpoint passed 872 tests with 11 skips; the newer
desktop-essential checkpoint above supersedes that count.

The current authoritative physical details and operator commands are recorded
in `docs/official-hub-owner-hyprland-checkpoint-2026-07-31.md`.

The owner-built official Hub has advanced beyond its clean textual delivery.
Canonical `hub`, generation `6f63f9a9-daea-40d1-969f-e25ff0752f4d`, still
derives from immutable `hub-headless-v4`, but its independent mutable root/home
now contain the owner's Hyprland 0.56.1-2 and kitty 0.48.1-1 installation and
configuration. This is allowed Environment-local ownership; it did not mutate
the Host, immutable release, `hub-testes`, `test`, or another Environment.
Local-admin enrollment is complete.

A dedicated temporary physical bridge is implemented and installed for this
exact official generation. Host command `entrar_no_HUB`, restricted to root on
safe `tty1`, dynamically resolves and grants only the fixed internal i8042 and
ITE keyboard identities, ELAN mouse/touchpad identities, AMD card2/renderD129,
and tty2. It starts Hyprland as UID/GID 1000 and automatically opens kitty. An
independent bounded proof returned `classification=verified`, Hyprland true,
kitty true, monitor `eDP-2`, keyboard count two, all four expected input
identities, tty1 restored, and no machine residue. The owner subsequently
confirmed two interactive sessions worked. Earlier ambiguous keyboard results
and the older official-Hub physical-launch block are superseded for this
bridge; they remain historical evidence for the abandoned prototype path.

The historical `Super+M` exit-to-Host binding, `Ctrl+Alt+F1` visual recovery, and
health-based watchdog are development safety mechanisms, not intended normal
product UX. The fixed four-hour expiry was removed on 2026-08-02. The owner
explicitly requires the final normal Hub desktop not to
offer a return-to-Host shortcut. That decision was superseded on 2026-08-12 by
the owner's explicit selection of `Super+E` as a retained recovery escape.
Protected Host recovery remains an architectural requirement.

The owner can now evolve Hyprland independently inside the Hub. APX work must
not overwrite the live owner configuration or turn that mutable Hub into an
Environment template. The remaining immediate product work is final boot into
the authoritative Hub, protected recovery outside normal UX, audio/brightness
mediation, owner-selected launcher/file manager, locale/portal cleanup, and
later resumption of the separately scoped Hub-to-Environment button/effect
integration.

At handoff, Host tty1 was active, the Hub was stopped, no machine or failed unit
remained, and the complete repository suite passed 858 tests with 11 skips.
The worktree remains intentionally uncommitted.

The owner has now accepted a temporary development-method deviation for the
disposable Lenovo physical pilot: Codex, Git, and GitHub CLI may run directly as
`root@apx-host` so repository changes and physical lifecycle tests can be
automated. This grants the temporary agent host-wide technical access, but not
standing authority to destroy Hub or Development, change disks, reinstall Arch,
or perform broad cleanup. It may create and destroy only clearly named test
Environments that it created itself. The target-bound entry, prompt, evidence,
and exit boundaries are documented in
`docs/temporary-root-host-development-mode-v1.md`; the preparation helper is
`scripts/physical-pilot/prepare-root-host-development-mode-v1.sh`. This is an
experimental development exception, not APX architecture or production state.
The mode is not active until the owner explicitly runs the guide on the exact
physical host, and its later removal requires a fresh inventory and exact
cleanup approval.

On 2026-07-18 the owner renamed the GitHub account from `Andre212004` to
`andrepereira2004`. The canonical repository URL for current operations is now
`https://github.com/andrepereira2004/apx.git`. Dated evidence may retain the old
URL when it truthfully records what was observed at that time.

The first pure already-installed physical-pilot update contract is now
implemented in `src/apx_physical_update.py` and documented in
`docs/physical-pilot-update-contract-v1.md`. It binds one untrusted bounded
candidate to the exact expected installed revision, component set, tests,
compatibility, rollback, documentation, reconciled audit, machine, Hub,
Development, recovery, journal-health, and capacity evidence. A valid result
reaches only `ready-for-separate-import-approval`; activation requires another
approval and rollback retirement remains a later decision.

`src/apx_physical_update_journal.py` now fixes the ordered staging,
verification, activation, replacement, final verification, publication, and
rollback-retention record. Prepared or partial effects preserve state and block
automatic rollback or cleanup. The implementation contains no artifact reader,
transport, installer, service control, physical rollback, or cleanup adapter.
The physical audit and target-bound release remain mandatory gates.

`src/apx_physical_update_artifact.py` now closes the generic raw-artifact
boundary for physical updates. It accepts only canonical uncompressed tar bytes
containing one canonical manifest and the exact sorted regular component files;
it rejects links, special files, directories, extra members, traversal,
non-root/variable metadata, nonzero timestamps, PAX extensions, oversized
content, duplicate JSON, and every candidate/manifest/content disagreement. It
does not extract, execute, install, select a destination, or change the host.
The update evidence schema now truthfully accepts the owner-approved temporary
root-host development mode by requiring reconciled Development state and a
current root-host inventory instead of falsely requiring a Development
repository. An exact target artifact, transport, effect adapter, interruption
fixtures, immutable release, and separate approvals remain pending.

An exact host-runtime-only candidate was then built twice outside Git from
source revision `909a7de7a257ed7320544bd5faa409b96afc543e`; both 30,720-byte
tar outputs were byte-identical and passed the closed reader. The target-bound
preview is documented in
`docs/physical-runtime-generation-fix-update-2026-07-18.md`. It remains
`blocked` solely because the physical recovery console has not been exercised;
boot-entry metadata is not substituted for that proof. No artifact was
imported, installed, or committed and no release tag was created.

`src/apx_recovery_console.py` now provides the pure, closed receipt and
assessment boundary for that remaining gate. Verification requires distinct
pre-reboot and recovery boot identities, exact boot-component and physical
identity digests, an owner physically using the built-in keyboard to unlock
encrypted root and reach the independent root console, and a post-boot APX
reconciliation proving unchanged Hub, Development, and disposable hold with no
uncertain operation. It also requires explicit evidence of no disk,
encryption, bootloader, package, or APX lifecycle effect. The module performs
no reboot or mutation, and metadata alone cannot satisfy it. The physical
rehearsal still requires the owner at the machine and fresh approval for the
availability-affecting reboot window.

`src/apx_physical_update_effects.py` now closes the non-executing staging and
target-mapping plan. For the first runtime-only candidate it fixes logical
staging at `/var/lib/apx/updates/staging/<update-id>/candidate.tar`, binds the
candidate, installed evidence, ready preview, import approval, artifact bytes,
and every before/after/rollback digest, and maps only `host-runtime` to the
regular mode-0755 `/usr/lib/apx/apx-lab-runtime.py`. `/usr/bin/apx` is a
required exact symlink invariant, not a second replacement target. Physical
mapping of `host-executor` and `hub-client` fails closed until their service and
immutable/current-Hub effects have separate designs. The plan has no
filesystem, service, lifecycle, install, rollback, or cleanup adapter; physical
staging and activation remain unimplemented and unauthorized.

The owner-authorized physical recovery-console rehearsal completed on
2026-07-18. A controlled reboot crossed to a distinct boot identity; the owner
used the built-in keyboard, unlocked encrypted root, reached the independent
root text console, and returned to the root-host session. Exact marker,
machine, boot-entry, kernel, initramfs, Hub, Development, disposable-hold,
disk/encryption, package, systemd, and APX reconciliation passed with zero
uncertain operations. The sanitized receipt in
`docs/physical-recovery-console-rehearsal-2026-07-18.json` is `verified` with
evidence digest
`db70438f786c3282755c44940bc27a5b18095bd31eeb4a904dbce62003634ad2`.
No physical update or lifecycle effect occurred. The earlier update preview is
now stale because it bound recovery evidence as false; a new complete preview
is required and still grants no import or activation authority.

The first post-reboot H0 observation confirms the physical pilot is the clean
headless path, not the historical KDE/SDDM G2 topology. No display manager or
Host graphical package is installed; tty1 is the tested recovery console and
tty2 is inactive; AMD `0000:05:00.0` resolves to card2/renderD129 and uniquely
owns connected internal eDP-2 at 1920×1080; NVIDIA remains separately resolved
and excluded. Stable built-in candidates are the i8042 keyboard and ELAN
touchpad, while the ITE special keys and external Logitech device are outside
H0. Exact facts are in
`docs/hyprland-h0-read-only-observation-2026-07-18.md`.

The dated graphical supply chain was also reconstructed into `/tmp`: all 138
base and 194 role packages repeated double signature and metadata verification,
and the 332-package offline root rebuilt without Host/APX effects. Review found
that package installation alone left locally generated pacman private trust,
machine identity, install timestamps, and a transaction log, so it was not
publishable. `src/apx_hyprland_release_finalize.py` now validates the closed
build, removes only temporary pacman trust, empties identity/log state,
normalizes the 332 install dates, rejects private keys/random seeds/special
files, and hashes the complete normalized tree. The real finalization produced
tree digest `83c58deaa56c83c23eee57dc02ecd3a67ccaede0d75918932f7f3b9557ab3401`
and report digest
`fb8a06d588b3dbf0f48b8626a1effc0df95e4c6dd12bfa995f167fe0376c530a`,
with all secret/runtime counters zero. It remains temporary evidence, not an
APX release; reproducibility, promotion, mediation, watchdog, and H0 approval
remain required.

The pure H0 release-promotion contract now fixes the next boundary: only
`hyprland-h0-v1`, sourced from the exact finalized tree, may target
`/var/lib/apx/releases/hyprland-h0-v1/root`; its internal account is fixed to
Environment-local `apx` UID/GID 1000 and no caller path, command, package,
service, device, or configuration is accepted. A real read-only evidence
capture reverified the tree, absent destination, healthy Btrfs quotas, more
than 470 GiB free, exact generations, disposable hold, and zero uncertainty.
The preview is `ready-for-separate-promotion-approval` with zero blockers and
plan digest
`dc15038fa6147f6f2ba098e90f880898ff4523586117bc0a338f9ea6e067146d`.
At preview time promotion remained unexecuted; the preview itself did not
create an Environment or authorize GPU/input/VT access or Hyprland activation.

The owner then authorized only that immutable release promotion. The first run
safely preserved an exact account-configured partial because the normalized
source had no hostname file to replace. A digest-bound continuation accepted
only that reviewed partial, created the fixed missing hostname, measured the
configured tree, wrote the canonical manifest, set the Btrfs root read-only,
and reverified all neighbours. `hyprland-h0-v1` is now a physical immutable APX
release containing 332 packages, configured-tree digest
`4798a8f6a0396dfab94758a9bb2498364a72948c6b2587593eadc04faca15b92`
and manifest digest
`dc1beaaaf6f073f8c3493d2e6b1d001e4b5f07f431f8a522f2125f242151ea40`.
The source, Hub, Development, disposable hold, and APX uncertainty state are
unchanged. No graphical Environment or session exists yet; device mediation,
watchdog, Environment creation, and physical H0 approval remain separate.

The repository lifecycle runtime now recognizes the closed `graphical-h0` role,
maps it only to the promoted `hyprland-h0-v1` release, and assigns bounded 16
GiB root and 8 GiB home quotas. Its generic headless start path deliberately
refuses this role before any runtime effect, so creation cannot accidentally
grant graphics or bypass the future AMD/input/VT/watchdog adapter. This source
change is not installed on the Host yet and no Environment was created. The
fixed first name and update-before-create sequence are documented in
`docs/hyprland-h0-environment-creation-v1.md`.

An exact Host-runtime-only candidate for that committed change was built twice
outside Git and both 30,720-byte USTAR artifacts were identical. Its artifact
digest is `a1b55982d14fb0bdf7afa8f1dd7991caf9d3a7ad5e24b321510763ad5b675a66`
and the closed reader accepted only candidate runtime digest
`0d7cc0c0c0631b65f68639f8b4994e3e3441a817604487256a30edd82f96da9f`.
Fresh observation then found a post-reboot mismatch: Hub and Development have
no running machine or current unit, but both registrations still claim
`running`. The shutdown journal shows a clean controlled stop during the
recovery reboot. Physical update preview/import remains blocked until those two
registrations are reconciled through a separately authorized exact action.

The owner authorized that exact reconciliation; Hub and Development now
truthfully remain stopped with unchanged generations. The fixed runtime update
adapter retained the previous runtime and installed the verified candidate.
APX then created the first real stopped graphical Environment,
`codex-test-hyprland-h0-v1`, generation
`c4fc5c49-4106-4a56-b1f0-13bffa41a0c1`, from `hyprland-h0-v1`, with 16 GiB
root and 8 GiB separate-home qgroup limits. An intentional generic-start test
refused before any machine or graphical effect. GPU/input/VT/watchdog mediation
and physical Hyprland activation remain unimplemented and separate.

The next pure H0 boundary is now closed. A generation-bound device-lease plan
admits only AMD card2/renderD129, the stable built-in keyboard and ELAN touchpad
identities, and tty2; it excludes NVIDIA, tty1, other input, audio, camera,
network, Host filesystem, and executor access. Its current plan digest is
`3ef21d19a2518d4fcea9d51513cc1eee63f6ff593d4470bcc10955b06e3059cb`.
The Host watchdog contract uses a 120-second deadline, 15-second stop ceiling,
generation-bound termination, full revocation, tty1 return, zero-residue proof,
and no automatic graphical restart. The minimal Portuguese-layout H0 config
was parsed by the installed Hyprland inside the Environment as `config ok`
without devices or a graphical start. No physical lease or session exists yet.

`src/apx_hyprland_h0_watchdog.py` now fixes a non-extendable, generation/plan-
bound watchdog state machine. It cannot complete with tty1 unrestored or any
process, mount, socket, or lease residue. The internal H0 session runner starts
only transient seatd, drops Hyprland to UID/GID 1000 with four exact auxiliary
groups and no capabilities, and traps mediator cleanup. Both remain unexecuted;
an independent Host launcher and hostile interruption tests are still required.

The Host expiry adapter now exists and was rehearsed with no graphical unit or
device grant. It revalidates the fixed generation, stops only the exact H0 unit,
activates tty1, and measures exact nspawn, mount, and unit residue. An initial
false-positive from the outer test command was corrected by matching only an
exact nspawn machine argument; the repeated rehearsal proved tty1 restored and
zero residue. It cannot start/restart graphics, broadly kill, delete, or affect
Hub/Development. The independent arming/launch adapter remains pending.

`src/apx_hyprland_h0_launch_plan.py` now closes the two-unit command plan. It
binds the three fixed asset identities/modes, arms and verifies an independent
120-second expiry timer before any device grant, then describes only the fixed
generation-bound nspawn unit with closed device policy and resource/network
limits. Its plan digest is
`9c5342a5859a93a09dcafefe8b6d53d370a2028e712d3321ee61d15d93cf9305`
after final review assigned VT switching exclusively to the Host and fixed
internal seatd to `SEATD_VTBOUND=0`.
The module is pure; asset staging, launch, readiness observation, interruption
execution, and physical display activation have not occurred.

The separately implemented exact asset-staging adapter then copied only the
three launch-plan assets into the fixed private Host experiment directory.
Their 0400/0500 modes and SHA-256 identities reverified, and the result records
`graphical_activation=false`. APX remained healthy/stopped with tty1 active and
zero failed units. Timer arming, device grants, nspawn launch, and Hyprland
execution still have not occurred.

Physical H0 v3 has now executed and passed the bounded technical process and
recovery gate. The expiry timer preceded graphics; the exact nspawn machine,
transient seatd UID-1000 client, and unprivileged Hyprland process were observed
through the full 45-second window. Recovery restored tty1, removed machine and
mount residue, and left graphical/timer units inactive with APX healthy. The
result is `docs/hyprland-h0-physical-result-2026-07-18.json`. This does not yet
claim visual/input acceptance: owner observation is pending. Aquamarine's
blocked absent-card1 enumeration and the missing separate-home `/home/apx`
directory are follow-up gaps before daily usability.

The current missing-home gap is resolved. The disposable graphical Environment
now has mode-0700 UID/GID-1000 `/home/apx` and `.cache` inside only its separate
8 GiB home subvolume. Repository runtime creation now performs the same fixed
home initialization for future `graphical-h0` Environments. That new runtime
source hash is not installed yet; the existing Environment is already corrected
and remains stopped/healthy.

The exact physical executor is now implemented and bounded to 45 seconds of
observation inside the independent 120-second expiry window. It rechecks the
real connector, amdgpu driver, tty1, display-manager absence, asset identities,
generation, devices, failed units, and zero old machine/unit state before
arming. Its unconditional finalizer invokes the staged watchdog and stops the
expiry timer only after that recovery attempt. It has not yet run.

The later physical H0 v9 run produced direct compositor evidence: Hyprland
published its Wayland socket and reported the internal `eDP-2` panel enabled,
focused, DPMS-on, and operating at 1920x1080/120.213 Hz on AMD. No application
client was observed, so this is a compositor/display pass rather than complete
visual acceptance. During the following v10 attempt the owner powered off after
about 25 seconds because no obvious exit was available. The 120-second Host
deadline had not expired; that deadline was nevertheless an unacceptable
recovery design for an interactive physical test. The incident is recorded in
`docs/hyprland-h0-recovery-incident-2026-07-18.md`.

Physical H0 is now code-locked. The repository-only recovery-v2 design reduces
normal observation to 10 seconds, the independent absolute Host deadline to 15
seconds, and the unit stop ceiling to 3 seconds. It retains the local
Super+Shift+E compositor exit and the independent Host-owned timer as separate
escape paths. Its device-plan digest is
`cfb0a57a8251203d7283dd88e22d500ad3f5d4d1a47495a53904ed2c38cdab96`
and launch-plan digest is
`c360cc97adce381b56368bde6db034cd685f6d05c688e33719ef4d57f62a9026`.
These are unactivated repository contracts, not permission to run graphics;
the code interlock remains false until pure and non-graphical recovery evidence
is reviewed.

Recovery v2 then passed all 714 repository tests (11 skipped) and a physical
non-graphical interruption rehearsal. The first dummy rehearsal exposed and
safely recovered from an expected `ProtectHome=yes` path error when attempting
to execute from `/root`; this fixes the requirement that recovery assets live
under private `/var/lib/apx/h0` state. The corrected digest-matched staged
watchdog stopped only an exact-unit `sleep` process at 15 seconds, restored
tty1, and reported zero residue with no failed units. Evidence is in
`docs/hyprland-h0-recovery-v2-rehearsal-2026-07-18.md`. GPU, input, tty2,
Hyprland, and Environment lifecycle were not touched. The physical interlock
remains disabled pending a fresh exact-plan review.

The owner has now selected Hyprland as the default graphical base for all
normal Environments, including the Hub. Each Environment receives an
independent copy-on-create configuration and Environment-local unrestricted
`sudo pacman`; the Hub starter remains minimal by choice rather than package
allowlisting. Essential defaults are mediated AMD display/GPU, keyboard,
touchpad, outbound network, and audio. Application notifications remain local
to the active Environment and no cross-Environment file portal exists. Camera,
microphone, controllers, and removable storage remain opt-in. Waybar with an
APX switch/return control is part of every starter.

Repository implementation now contains the fixed `hyprland-base-v1` and
`hub-hyprland-v1` template catalogue, independent storage/config creation plan,
future runtime role mappings, closed release-evidence contract, minimal
Hyprland/Waybar assets, demo-only GTK/libadwaita Hub shell, safe Hub template
summaries, and guarded headless-to-graphical Hub replacement plan. The existing
stopped `hub-headless-v3` has an empty home and is fixed as retained rollback.
No `hyprland-base-v1` release has been built or promoted, no real Hub was
replaced, and no graphical activation was unlocked. The architecture is
documented in `docs/hyprland-default-environment-architecture-v1.md`.

## Human Objective

APX should make one physical Arch Linux computer feel like a collection of
independent, disposable computers without presenting ordinary Linux user
management to the person using it.

Examples include separate Environments for university, individual subjects,
work, games, individual games, and unsafe development experiments. Installing
Steam in one games Environment must not make Steam visible in another
Environment. Installing two separate Steam copies in two Environments, with
different games and data, must be possible. A document created for university
must not appear in a games Environment. Deleting an Environment must remove its
local applications, data, configuration, processes, and state without branching
into or damaging another Environment.

APX is a platform and orchestration layer, not a separate operating system per
Environment. The host retains one Arch Linux installation and one kernel. The
technical mechanism that provides per-Environment applications and stronger
containment is not yet selected.

## Intended User Experience

The owner sees one human identity and a set of named APX Environments. APX may
use separate Linux accounts internally, but the normal interface must not show
the display manager's user chooser or require the owner to reason about those
accounts.

The intended flow is:

```text
Boot -> Hub -> selected Environment -> Hub
```

The delivery order is now CLI-first. The first functional clean installation
may present a headless Hub through the `apx` CLI and headless Environments
through physical console/session transitions. This is an implementation and
validation stage, not a change to the final one-human-identity product. A
graphical Hub and graphical buttons are later clients of the same bounded
protocol, not prerequisites for Environment lifecycle.

The machine enters the Hub directly through a future secure login or unlock
flow. From there the owner creates, configures, launches, archives, restores,
and deletes Environments. A future multi-person model may group Environments by
human identity, for example `andre` and `pai`; its authentication and ownership
model is deliberately deferred.

## Environment Product Contract

Each Environment is intended to behave like a complete logical computer:

- local applications and dependencies;
- local documents and application data;
- local configuration and session state;
- local processes and services;
- a selectable desktop or compositor, such as Hyprland, KDE Plasma, or GNOME;
- lifecycle operations that do not alter other Environments;
- isolation by default, with sharing only through a future explicit policy;
- optional creation from a reviewed template;
- optional local assistants enabled by policy.

Software installation is always scoped to the active Environment. Commands such
as `sudo pacman -S steam`, `yay -S ...`, `apt install ...`, Flatpak operations,
language package managers, vendor installers, and installation scripts must use
only that Environment's files, databases, and services. They must never install
into, upgrade, remove, or otherwise modify the host, APX base, Hub, or another
Environment. Host package management is not exposed through normal Environment
`sudo`.

Environments may inherit a reviewed, versioned APX base at creation. This base
contains common compatibility and presentation defaults without making the
Environments share mutable application or user data. Hardware drivers and
machine-wide network capability normally remain host responsibilities;
Environment-visible integration, fonts, certificates, desktop defaults, and
other safe baseline content may be supplied through the base after their exact
boundary is validated.

APX must support ordinary trusted workloads with strong separation. It should
also support a future higher-security profile for Environments used to run
untrusted code. The profile mechanism and its guarantees require a threat model
before implementation. APX must never describe user accounts or filesystem
permissions alone as VM-equivalent security.

## Hub Product Contract

The Hub is the minimal default APX Environment and the management surface. It
may contain APX management UI, system status, visual customization, and tightly
scoped widgets needed for that role. General-purpose browsers, editors, games,
development tools, and ordinary workload applications do not belong there.

Software cannot be installed interactively into workload Environments from the
Hub as an arbitrary privileged action. The Hub may select reviewed templates,
policies, and declared software sets during creation or configuration through a
future bounded APX management protocol.

The Hub is not an unrestricted administrator. Privileged lifecycle work belongs
to a small, typed, independently validating executor. The Hub must remain
destroyable and reproducible from its definition; its default role does not
justify bypassing Environment lifecycle or isolation rules.

The first Hub may be headless. Its `apx` CLI is a management surface, not a
general development shell. The Hub still excludes Git repositories, Codex,
compilers, editors, development browsers, build outputs, and experimental
scripts. A later graphical Hub must map its buttons to the same typed protocol
and cannot gain broader authority.

The live Hub is not the parent filesystem or template for other Environments.
The Hub and workload Environments are separate products derived from the same
versioned APX base plus different role profiles. Hub-only management UI,
credentials, permissions, metadata, widgets, and state must never propagate to
a workload Environment. Conversely, an accidental change inside the Hub must
not silently change future Environments.

## Local Assistants

Odysseus is intended to provide a local personal assistant inside selected
Environments. Each instance is active only while its Environment is active and
may access only the Environments explicitly allowed through future Hub policy.
The initial model is total separation between assistant instances. Cross-
Environment communication and shared memory are deferred.

Selected development Environments may also include Codex as a coding and
debugging tool. Codex must be treated separately from personal-assistant data
and permissions. The Codex used to build APX today remains temporary development
tooling and is not evidence that this future integration has been designed.

For the accepted owner-controlled physical pilot, Development will also receive
an optional local coding fallback after Codex is working. The initial selection
is Qwen2.5-Coder 7B Instruct through an Environment-local CPU-first Ollama
service and Qwen Code terminal agent. It complements Codex for bounded review,
diagnosis, documentation, and small confirmed changes; it does not approve or
promote its output. The service, model, configuration, indexes, conversations,
and tools belong only to Development, listen on Environment loopback, and stop
with that Environment. GPU acceleration and provisioning separate instances in
other Environments remain gated future work. The complete pilot boundary is in
`docs/local-development-agent-v1.md`.

## Confirmed Platform Boundaries

- one physical Arch Linux host;
- one host kernel;
- APX is the orchestration layer;
- separate internal Linux accounts remain the current identity and ownership
  foundation;
- one intended dedicated Btrfs home subvolume per Environment;
- local applications, data, configuration, and runtime state per Environment;
- only one normal graphical workload Environment active at a time;
- compositor- and desktop-independent lifecycle behavior;
- no visible ordinary Linux account chooser in the intended experience;
- templates are the intended reproducible starting point;
- a versioned common APX base may supply reviewed defaults to every role;
- no implicit cross-Environment data access;
- no Environment package-manager path to the host package database;
- no lifecycle exception that makes the Hub irreplaceable.
- the APX CLI is the first management interface and remains available beneath
  later graphical controls;
- a headless Hub is a valid initial Hub profile;
- graphical interface work follows successful headless lifecycle, isolation,
  storage, package-locality, and recovery validation.

## Decisions Still Required

The following are product requirements but not yet technical decisions:

- per-Environment application mechanism: container/root filesystem, image,
  package overlay, or another design;
- which minimal packages remain in the host package database and which
  graphical/runtime components belong in each Environment's package database;
- isolation boundaries and threat model for normal and high-security profiles;
- namespace, cgroup, capability, seccomp, device, IPC, network, and GPU policy;
- exact Btrfs layout for homes, application layers, templates, snapshots,
  archives, and restoration;
- desktop/compositor packaging and launch model;
- secure automatic entry to the Hub without exposing internal accounts;
- exact clean-bootstrap artifact, trust root, minimal host manifest, and typed
  installation protocol;
- exact non-graphical Hub and Environment session transport;
- session handoff and failure recovery;
- Hub-to-executor authorization protocol;
- template format, provenance, updates, and reproducibility;
- exact host/base/role-template boundary for drivers, firmware, networking,
  fonts, certificates, graphical integration, and defaults;
- multi-person identity, grouping, authentication, and ownership;
- Odysseus permission, memory, model, and lifecycle boundaries;
- Codex provisioning and separation from personal-assistant data.
- the exact Environment administrator policy: which local administrative
  operations are allowed and how local `sudo` is confined without creating a
  path to host administration.

## Provisional Isolation Direction

The first backend to validate is one bootable Arch system container per
Environment using `systemd-nspawn`, a versioned base, Btrfs-backed writable
state, user and network namespaces, reduced capabilities, explicit syscall and
device policy, cgroup limits, and verified teardown. This is a validation
direction, not an accepted implementation.

Podman/OCI remains a serious alternative or complementary runtime. Its rootless
model, image ecosystem, Quadlet integration, seccomp support, and standardized
CDI device injection are valuable, particularly for NVIDIA. A hardware VM may
be required for a future profile whose threat model includes hostile kernel
exploitation. The comparison, gates, and initial threat model are recorded in
`docs/isolation-architecture.md` and `docs/threat-model.md`.

## Provisional Lifecycle and Storage Direction

The repository now has a complete logical v1 proposal in
`docs/environment-lifecycle-and-storage-v1.md`. It separates immutable base and
role-template references from mutable root and home, ephemeral runtime,
immutable snapshot sets, and portable archives. It proposes generation-bound
registration and one write-ahead protocol for create, activate, stop, snapshot,
archive, restore, recovery, and destroy.

This is a review proposal, not confirmed or implemented architecture. Physical
Btrfs behavior is now mapped by a separate flat-subvolume and hierarchical-
qgroup proposal, and the lifecycle contract has passed repository-level review
against the normal and high-security threat objectives. Host topology,
disposable-fixture validation, backend identities, template artifact format,
executor authorization, and session handoff remain acceptance gates. These
proposals deliberately do not make the provisional `systemd-nspawn` backend a
hidden decision.

## Provisional Base and Role-Template Direction

The repository now proposes the safe starting-model system in
`docs/base-and-role-template-model-v1.md`. A minimal common base is separate
from readable role definitions, immutable built releases, and the independent
Environment created from them. Proposed families include Hub, Minimal,
University, Development, Games, and High Security, but no final package list or
release is approved by those names alone.

Templates never come from cloning a live Environment. They exclude personal
data, credentials, machine identity, assistant memory, operation records, and
Hub authority. A new release never silently changes an existing Environment.
V1 permits new creation from an admitted release; migration of an existing
Environment requires a later offline, reversible protocol.

This is a proposal, not an implemented catalogue or builder. Canonical schemas,
the isolated builder, artifact format, exact package manifests, reproducibility
evidence, sanitization fixtures, and per-release review remain required.

## Provisional Privileged Executor Direction

The repository now proposes a bounded Hub-to-executor protocol in
`docs/privileged-executor-protocol-v1.md`. In ordinary terms, the Hub may ask
for predefined APX actions but never receives a general administrator command
channel. The executor independently checks the current state, exact approved
plan, human approval strength, expiry, one-use nonce, operation journal, and
final result.

Routine launch and clean stop may use an unlocked APX session. Creation,
snapshots, archives, and restore require an explicit preview and confirmation.
Destroy, forced stop, and destructive recovery require fresh strong
confirmation and a plain-language explanation of possible data loss. A durable
write-ahead journal supports crash inspection; uncertain state preserves data.

This is a proposal, not an implemented privileged service. Human
authentication, secure Hub entry, final local transport, approval format,
minimal host privilege mapping, and failure-injection evidence remain required.

## Provisional Human Identity and Session Direction

The repository now proposes the complete visible single-owner flow in
`docs/human-identity-and-session-handoff-v1.md`. The person unlocks APX without
seeing internal Linux accounts, enters the Hub, selects an Environment, and can
return to a freshly activated Hub.

The Hub does not remain graphically active in the background. A minimal
host-owned broker provides only lock, transition, progress, and recovery while
APX stops one Environment, verifies teardown, and activates the next. If stop
cannot be proven, the next Environment does not open. If launch fails, the
broker offers bounded recovery without exposing a shell or turning a workload
into a temporary Hub.

APX cannot universally prove that every application saved its work. The
proposal therefore distinguishes ready, known blocker, and unknown safety;
unknown defaults to cancelling the switch. Force-stop requires fresh strong
confirmation. This is a proposal only: SDDM remains current, `greetd` remains a
candidate, and no broker, unlock, handoff, lock, or recovery flow exists.

## Provisional Environment-Local Administration Direction

The repository now proposes the local administration contract in
`docs/environment-local-administration-v1.md`. The owner may install software
and make system-level changes inside one Environment without receiving host
administrator authority. Local `sudo`, pacman, Flatpak, language managers, AUR
builds, vendor installers, hooks, services, and updates remain inside that
Environment's root, home, runtime, devices, network, and limits.

Local root is treated as a potentially hostile attacker, not a trusted safety
boundary. It must be unable to change the host, Hub, base, template, another
Environment, APX metadata, storage management, or outer resource policy. A bad
installer can still damage or expose its own Environment; APX offers honest
warnings and optional stopped-state restore points rather than claiming the
software is safe.

The owner-facing local-administrator confirmation must not copy a host password
or reusable approval into the Environment. Its exact mechanism, backend
enforcement, hostile-root denial tests, and package-manager experiments remain
unimplemented and required.

## Accepted Headless Bootstrap and CLI-First Direction

The preferred first functional APX installation is now a fresh minimal Arch
host with no KDE, Hyprland, SDDM, display manager, or graphical session. The
ordered development path is recorded in
`docs/headless-bootstrap-and-cli-first-v1.md`: verified bootstrap, headless Hub
CLI, headless Development, Environment-local installation and separation,
lifecycle/storage/recovery, first Hyprland Environment, graphical controls, and
only then an optional graphical Hub.

This is a development-method and clean-install decision, not authorization to
erase or reinstall the current machine. A future real installation requires a
separate target-bound dossier with verified repository history, restore-tested
personal backup, boot-tested recovery media, disk plan, minimal package
manifest, pinned APX artifact, exact effects, rollback, and explicit approval.

A Git clone is development source acquisition, not a privileged APX installer.
The steady-state source checkout, Git, Codex, compilers, tests, and build outputs
belong in the Development Environment. The Hub contains only the bounded APX
management client and role-appropriate state. Before any Environment exists, a
temporary host bootstrap staging area is an explicit bounded exception; it is
removed or archived after Development and the installed APX artifact are
independently verified.

Codex remains temporary Development tooling and never becomes a Hub, host,
executor, recovery, or product dependency. It may be removed from Development
only after source/history, remote or separately reachable copy, reproducible
build/test instructions, and Codex-independent CLI/graphical operation are
verified. Removing or destroying Development must not alter Hub or host state.

The physical headless pilot quota policy is now role-aware. Hub and Minimal
retain the experimental 4 GiB root and 2 GiB home limits; Development receives
a bounded 16 GiB root and 8 GiB home so its accepted roughly 4.7 GB local model,
Environment-local packages, Codex state, repository, credentials, and working
space can coexist. These are pilot limits, not production defaults. The first
physical Development was created under the earlier fixed 4/2 GiB policy, so
`scripts/physical-pilot/recover-development-quota-v1.sh` provides a guarded,
in-place migration. It requires the exact physical identity, stopped
Development registration, healthy traditional qgroups, expected subvolume
identities and old limits, then raises only those two limits and installs the
matching role-aware runtime. It preserves Development root/home content and
rolls limits back if final verification or runtime installation fails. Owner
execution and post-recovery physical validation remain required; repository
tests do not claim the recovery has run on the machine.

The first quota recovery release falsely rejected the installed `btrfs-progs`
status layout because its anchored shell expressions did not admit the leading
indentation used by `Enabled: yes`, `Mode: qgroup (full accounting)`, and
`Inconsistent: no`. The corrected parser normalizes only surrounding whitespace
and supports both known field-name/value formats. It still requires enabled
traditional qgroups and consistent accounting, rejects duplicate or malformed
safety fields, and continues to reject limit override or active rescan evidence.

The second quota recovery release reached the installed status parser but
queried qgroups through the `/var/lib/apx` `@apx` subvolume mount, which exposed
only qgroup `0/256` rather than the nested Development root/home qgroups on this
physical layout. The v3 recovery resolves the Btrfs filesystem UUID from the
fixed APX state path, creates a private temporary mount of that exact
filesystem's top-level subvolume ID 5, independently verifies filesystem UUID,
type, and root ID, and uses only that scope for quota status, discovery, limit,
verification, and rollback operations. The mount is removed on every exit.
This does not expose the top level to an Environment or make it persistent.

The same quota-status correction is now also present in both original bootstrap
sources: the VM laboratory bootstrap and its target-bound physical-pilot
counterpart. They accept the two observed `btrfs-progs` field layouts, enable
quotas only when explicitly reported disabled, reject ambiguous or unhealthy
accounting, and verify healthy traditional qgroups after enablement. This is a
repository correction only; it does not change the already frozen initial
physical-pilot tag or claim that either bootstrap was rerun.

The 2026-07-17 audit observed the Ollama package inside physical Development
with no downloaded model. Root-host reconciliation on 2026-07-18 later proved
that this audited Development generation no longer exists. The APX journal
records a complete stop and destroy of generation
`72b3777b-6dba-4175-8d3e-3fb24401bf50`, including completed `remove-home` and
`remove-root` effects, followed 13 seconds later by creation of generation
`b90155f6-ece2-44ae-91fc-42d91d6b35a5`. The replacement is running but has an
empty home, about 8 KiB of APX Environment state, and no GitHub CLI, Ollama,
Qwen Code, Codex, or repository. No registered APX snapshot, archive,
quarantine object, or catalogue object preserves the prior generation. The
journal does not identify who requested destruction. The owner subsequently
confirmed that this was their intentional lifecycle test, so it is not treated
as an unexplained security incident or executor malfunction.

The owner accepts the replacement as an intentionally simple Development
fixture and prefers not to reprovision its former toolchain now. The old
in-place quota-recovery route remains inapplicable to this generation. The
temporary root-host mode and checkout remain the explicitly bounded development
location while this work continues. This delays Phase 10 removal of root-host
development state but does not block repository development or physical tests
using newly created `codex-test-*` disposable Environments. Changing Hub or
Development still requires fresh exact approval.

The first root-host disposable lifecycle test created and cleanly started and
stopped `codex-test-lifecycle-v1`. It proved a running minimal system, 139
internal packages, a distinct PID namespace, link-local-only Environment
networking, no executor socket, no root-host checkout, no Development home, and
zero machine or mount residue after stop. Destruction was deliberately not
executed: the installed runtime generated a destroy plan with a random
generation instead of the registered generation and did not compare them before
destructive effects. A stale same-name plan could therefore target a later
generation.

The repository runtime now binds destroy plans to the current registered
generation and refuses a mismatch before journal, stop, unpublish, or removal.
Regression tests cover plan binding and pre-effect stale refusal. The physical
runtime is not changed by this repository correction. `codex-test-lifecycle-v1`
remains stopped and preserved until a separately reviewed physical runtime
update installs the fix; do not use the existing destroy plan or improvise
cleanup.

**Pinned owner decision — 2026-07-18:** local-model acquisition and execution
are deferred to a future milestone because the wanted model's storage cost is
not currently worthwhile. No Phase 9 or Phase 10 procedure may download a
smaller substitute merely to close the checklist. The current replacement has
neither Ollama nor a model; that minimal state is a valid deliberate outcome.
All Ollama/model lifecycle checks are `not-applicable` until this decision is
separately reopened. Host/Hub isolation, APX lifecycle, storage, quota,
recovery, and all non-model gates remain required. A future verified
package-only state would not by itself require keeping temporary Host bootstrap
material after every other applicable Phase 10 audit gate passes. The repository now proposes the external model
storage boundary in `docs/external-development-model-storage-v1.md`: one exact
encrypted device and attachment identity, visible only to one Development
generation, with bounded capacity, immutable model evidence, fail-closed
disconnect behavior, and no shared writable host or Hub path. This is a
proposal only. No disk, mount, runtime adapter, model relocation, or larger
model is implemented or authorized.

The first external-model-store repository contract is now implemented in
`src/apx_external_model_storage.py`. It parses one closed, duplicate-safe
evidence schema and fails closed on changed device, Development generation,
LUKS/filesystem identity, visibility, ownership, capacity reserve, partial
download, disconnect, recovery, or model-manifest facts. It produces only
`blocked` or `ready-for-separate-design-review` plus a no-effect plan digest.
It has no formatting, unlock, mount, attachment, download, or cleanup function;
the physical evidence, adapter design, failure fixtures, denial tests, and
target-bound destructive dossier remain required.

The same module now implements the closed `ModelArtifactManifest`. It binds a
served tag to its reviewed source, licence, Ollama version, measured size,
manifest digest, unique ordered blob digests, and explicit absence of partial
downloads, credentials, and conversation state. This closes only the pure
model-record contract; physical Ollama path observation and model acquisition
remain pending.

The external-store module also produces a deterministic attach preview only
from complete ready evidence. It fixes a private runtime path, the candidate
Development Ollama data path, ordered effect names, and a generation-bound
operation identity while carrying no command or execution function. The audit
must confirm the real installed Ollama path; physical detach evidence, the
runtime adapter, interruption experiments, and physical approval remain open.

The pure attach/detach journal is now implemented in
`src/apx_external_model_lifecycle.py`. It binds one preview to ordered attach
evidence, permits activation only from verified attached-stopped state,
requires separate detach approval, records ordered detach evidence, and treats
prepared, partial, disconnected, or otherwise uncertain state as preserve and
inspect. Its fixture store rejects replay, stale writers, and transition jumps.
It performs no disk, encryption, mount, service, Environment, or cleanup effect;
physical source adapters and interruption fixtures remain required.

The logical Development-to-Hub promotion boundary is now proposed in
`docs/development-to-hub-release-promotion-v1.md`. Codex and the Development
builder may produce only an untrusted immutable candidate. A closed host-owned
import copies one exact candidate into quarantine without executing it;
independent verification and a separately approved catalogue admission create
an immutable release identity. The executor then creates and verifies a new Hub
generation instead of allowing Development to mount, edit, enter, or
package-manage the live Hub. The old Hub remains a bounded rollback candidate
until separately approved retirement.

The first-Hub bootstrap uses the same logical verification and admission stages
from a temporary bounded pre-Environment staging area. Once the Hub creates
Development, normal Git/Codex/build work moves there. Candidate schema, artifact
format, physical import transport, trust roots, independent build method,
initial Hub manifest, safe preference schema, executor operations, and rollback
retention remain open and unimplemented.

The first graphical clean-host gate is H0. It starts from a verified state with
no graphical session or display manager, proves the independent recovery VT,
then grants only the selected AMD display and mediated built-in keyboard/
touchpad to one disposable Hyprland Environment. G2 remains the separate
secondary gate for migrating a live KDE/SDDM machine. G2 evidence is preserved,
but it no longer blocks the headless C0–C6 ladder or H0 design.

The first closed H0 repository contract is now implemented in
`src/apx_hyprland_h0.py` and documented in
`docs/hyprland-h0-clean-host-v1.md`. It binds reconciled audit, no-display-
manager/session/lease evidence, independent recovery VT, healthy APX state,
exact target AMD identities, explicit NVIDIA exclusion, exactly mediated
built-in keyboard/touchpad, forbidden audio/camera/microphone/broad-input/Host/
executor access, graphical release/config/control identities, watchdog,
timeout, and teardown observer into a no-effect preview. Complete evidence
reaches only `ready-for-separate-physical-approval`.

`src/apx_hyprland_h0_journal.py` now fixes ordered recovery-VT verification,
Hub/Development stop, lease reservation, AMD/input grants, Hyprland launch,
Wayland/control/watchdog verification, teardown, device revocation, zero
residue, and restored headless operation. Every partial or uncertain state
blocks automatic graphical restart and requires recovery-VT inspection. No
physical graphical adapter, package installation, VT switch, device grant,
compositor launch, or cleanup is implemented.

## Accepted First Clean-Install Foundation

`docs/clean-install-foundation-v1.md` fixes the first experimental C0–C6 target:
x86_64 UEFI, one explicitly identified disk, GPT, a 1 GiB EFI System Partition,
LUKS2 plus Btrfs, systemd-boot, text-only Arch, and `systemd-nspawn` with
mandatory private users and no graphical/device grants. This accepts nspawn
only for the headless implementation; H0 and future high-security profiles may
select a different or hybrid backend.

The initial source package-name manifest is `base`, `linux`,
`linux-firmware`, `btrfs-progs`, `cryptsetup`, `iwd`, `python`, and `gnupg`,
plus exactly one applicable CPU microcode package and proven hardware-specific
firmware. Exact versions, archives, hashes, signatures, databases, and signers
must come from one dated Arch snapshot in the target-bound dossier. Git, Codex,
build tools, desktops, display managers, browsers, and workload packages are
excluded from the steady-state host.

The first headless session is a broker-owned pseudoterminal, not a host shell or
machine selector. The first owner authentication method is a host-owned
password with fresh re-entry for strong confirmation, separate from the LUKS
recovery passphrase. The first APX host artifact is a signed, versioned Arch
`.pkg.tar.zst` with complete SHA-256 identity. Exact PAM/service code, real APX
trust keys/custody, schemas, privileged implementation, disposable-install
rehearsal, and target dossier remain unimplemented and required.

The first pure installation/promotion contracts are now implemented without
host effects. `src/apx_release_candidate.py` parses the exact headless-Hub
candidate schema, computes canonical identity, classifies every parsed candidate
as untrusted, and produces a reference-only quarantine import plan. It accepts
no command, path, destination, URL, signature shortcut, policy override, or
unknown field. `src/apx_clean_install_dossier.py` parses target and supply-chain
evidence and returns only `blocked` or `ready-for-separate-approval`; even the
latter still requires fresh strong disk approval and has no apply function.

The schemas and fixed future CLI vocabulary are recorded in
`docs/release-candidate-schema-v1.md`,
`docs/clean-install-dossier-schema-v1.md`, and
`docs/clean-install-cli-contract-v1.md`. The promotion and installation fixture
state machines are now implemented in `src/apx_release_promotion.py` and
`src/apx_clean_install_journal.py`. Promotion keeps import, verification,
admission, and immutable catalogue publication separate; its store accepts only
one exact allowed plan and compare-and-swap transition. The installation journal
expands all ten stages into ordered fixed effects, requires a separate approval
for each applicable current stage, and never automatically deletes uncertain
state. Its store accepts only one exact ready dossier and one-step transitions.

The release member and reproducibility contract is now closed in
`docs/release-artifact-manifest-v1.md` and implemented as a pure validator in
`src/apx_release_artifact.py`. It binds the candidate to a canonical ordered
tree and compressed-artefact digest; rejects special files, privileged modes,
path escapes, mutable identity/runtime state, personal homes, credentials, and
Development state; and requires exact independently rebuilt outputs. It does
not read or extract an archive and cannot admit a release.

The first packaging rehearsal is closed as an unsigned definition only in
`docs/bootstrap-development-package-v1.md` and
`src/apx_contracts_package.py`. `apx-contracts-development` contains exactly
three non-mutating validators, four package-owned contract documents, and the
repository licence declaration, with fixed source-to-target mappings, `python`
as its sole runtime dependency, no command/service/hook/installer, and exact
two-build evidence. It is deliberately not the production bootstrap package.
The project licence is now Apache-2.0. Commit
`c6f61ff7259fa71039c087023018731c6f3a774d` freezes the source used by the
first package rehearsal. `packaging/apx-contracts-development/PKGBUILD` binds
its Git-archive digest and exact eight payload files. An initial two-directory
build correctly failed reproducibility because Arch records absolute build
paths in `.BUILDINFO`. Two later clean builds at one canonical path produced
byte-identical 21,601-byte unsigned packages with SHA-256
`3895d89e34a95b38bc5559a49b87cd338725b3889a42122932fd2a0fe3fff76a`.
The retained sanitized evidence is in
`docs/bootstrap-development-package-build-2026-07-13.md`. This is same-
Development-environment evidence only; two separately created frozen builders
remain required, and the package was not installed, trusted, or published.

The independent follow-up is now positive. Two separate network-disabled Arch
containers from one pinned builder image produced byte-identical 16,109-byte
packages with SHA-256
`9d6e53007bc56e8a9105f4ff65c14097dbec13aa8b0b4c7ddb70912b01b012fd`.
A third disposable offline container installed the result; pacman reported zero
altered entries and all three modules imported. The full frozen identities are
appended to `docs/bootstrap-development-package-build-2026-07-13.md`. This
closes the development contracts-package build proof, not the functional APX
bootstrap or production trust.

The production trust operational boundary and mandatory physical rehearsal are
now defined in `docs/release-key-custody-and-ceremony-v1.md`. Root and release
signer roles are separate and offline; private material may never enter the
host, Hub, Development, Codex, Git, or a networked builder; two separated
encrypted backups and a proven restore are required; compromise, rotation,
revocation, signing, and sanitized evidence paths are explicit. This is a plan,
not a completed ceremony. Exact cryptographic profile/tool versions and an
explicitly approved offline disposable-machine rehearsal still block real-key
generation.

The disposable C0–C6 proof is now specified in
`docs/disposable-clean-install-rehearsal-v1.md`: one unmistakably disposable
x86_64 UEFI VM, one new 64 GiB virtual disk, no host shares or secrets, retained
text recovery, exact external evidence, checkpoints only for fault injection,
power loss before/after every destructive/publication boundary, and the full
Hub/Development/package-locality/lifecycle/offline-recovery ladder.

The experimental functional ladder passed on 2026-07-13 in a disposable QEMU/
KVM VM backed only by one new sparse 64 GiB qcow2 disk. A guarded installer
produced a minimal UEFI/systemd-boot/LUKS2/Btrfs Arch host without graphics.
An experimental headless runtime then demonstrated immutable role releases,
independent mutable roots and homes, private user and network namespaces,
Environment-local pacman and npm installation, quotas, stop with zero runtime
residue, snapshot, archive, restore to a new generation, destruction,
conservative recovery, and a real cold boot with QEMU `-nic none`.

The recreated `hub-headless-v3` contains only an unprivileged typed client. A
host-owned Unix-socket executor accepts fixed operation schemas and authorizes
the peer only when its host UID belongs to the active Hub's private 65,536-ID
map. The Hub used it to create, start, stop, and destroy a fixture. Host root
using the client was refused, and Development had neither the socket nor the
`apx` command. The full result, identities, failure corrections, checkpoints,
and limits are in `docs/virtual-headless-c0-c6-result-2026-07-13.md`.

This closes the functional virtual milestone, not the production-shaped formal
rehearsal. The signed functional bootstrap, production trust/custody,
untrusted-archive reader, broker/PAM authentication, minimum-privilege service
hardening, exhaustive before/after interruption matrix, hostile local-root
containment, physical recovery/backup dossier, hardware validation, and H0
remain required.

The owner has accepted a separate hands-on physical development pilot because
the current computer is dedicated to APX work and the GitHub repository is the
required source recovery copy. This does not waive disk-identity checks or turn
the pilot into a production release. The target is bound to Lenovo product
`82JU`, board `LNVNB161216`, and the 512,110,190,592-byte Samsung NVMe
`S4DYNX0R253702`. Any mismatch stops the run.

`docs/physical-headless-development-handoff-v1.md` is the autonomous ChatGPT
handoff from official Arch media to a headless Hub and separate Development.
The destructive installer and temporary host bootstrap are frozen through the
immutable `physical-headless-pilot-v1` Git tag; only the later Development
checkout follows `master` for ongoing work.
The two initial scripts under `scripts/physical-pilot/` are deliberately separate from
the VM installer: one erases only the exact reviewed NVMe after repeating its
model/serial/size checks and exact typed approval; the other admits only the
installed physical marker and exact Lenovo DMI identity before installing the
experimental runtime. On 2026-07-17 the owner reported that Phases 1 through 8
of the physical handoff had been completed on the target, including the initial
installation, Hub, Development, GitHub, and Codex setup. Phase 9 is partial:
Ollama is reported installed inside Development without a downloaded model;
quota recovery and the remaining package-only local-agent evidence are
pending. On 2026-07-18 the owner pinned model installation as a future-only
milestone and directed Phase 10 review to proceed without it. Phase 10 remains
subject to every non-model gate and separate cleanup approval. This is an owner
progress report, not independently captured repository evidence; the read-only
physical state and cleanup audit must reconcile the machine before cleanup or
a later host update.

This is an accepted development-method deviation, not a claim that the
production blockers are closed. The initial host Git checkout and Git package
are bounded bootstrap staging and must be removed only after Development has a
persistent checkout, working GitHub authentication, Codex, the accepted
local-agent checks, and the separately reviewed physical audit. Ongoing source,
build, GitHub, Codex, Ollama, model, and
Qwen Code work remains Development-only. The Hub still receives only the typed
client and no development tools or assistant endpoint.

Forty-eight focused tests cover canonical round trips, direct-object bypass,
duplicate/unknown/missing fields, commands and paths, wrong types, limits,
digests, fixed policies, every dossier gate, invalid dates/configuration,
deterministic plans, security-relevant digest changes, stale writers, forged
initial state, multi-step jumps, approval separation, every fake install effect,
interruption recovery, archive member policy, link containment, candidate/tree
binding, exact release rebuild comparison, closed package contents, and exact
package rebuild evidence. The complete suite now runs 635 tests: 631 pass and
four external-fixture checks are explicitly skipped because reboot removed
their bound `/tmp` evidence. There are no test failures or errors. No physical
candidate import, archive extraction, signature
verification, trusted catalogue, installer effect, disk operation, executor
effect, or production Hub creation is implemented. The separate guarded
VM-only runtime is experimental evidence and is not wired into the production
CLI.

The dated readiness audit is in
`docs/clean-install-readiness-2026-07-13.md`. A destructive installation remains
blocked by absent production trust keys/custody, bootstrap package, physical
quarantine/archive-verification/catalogue/Hub-replacement machinery, privileged
production executor/broker/authentication, reviewed physical effect adapters,
the remaining formal interruption matrix, and target-specific evidence. The VM
proves the functional architecture; it does not authorize running the
laboratory installer on the physical computer.

## Implemented Today

The owner selected a new immediate Hub-development sequence on 2026-07-30.
The current graphical Hub is disposable and will be preserved as the ordinary
non-authoritative `hub-testes` Environment. The new canonical Hub begins as a
clean Arch text Environment. The owner, not APX, will install Hyprland and the
officially recommended terminal and follow the upstream tutorial. The
repository contains pure admission contracts and guarded physical adapters
for an independently rebuilt `hub-headless-v4`, Environment-local password
enrollment and password-required sudo, public-Internet-only mediated egress,
explicit Host/Environment terminal boundary banners, physical input proof, and
a rollback-preserving Hub cutover.

The physical delivery completed on 2026-07-30. After retaining an initial
non-matching diagnostic pair, two fresh normalized `pacstrap` builds matched
exactly and published immutable `hub-headless-v4`, tree digest
`3c21ba4145314cd8e6c09b1178adb3f1a904e9e406af03695676b4c21310a0c5`.
The journaled cutover published official Hub generation
`6f63f9a9-daea-40d1-969f-e25ff0752f4d` and preserved the complete former
graphical Hub as non-authoritative `hub-testes`, generation
`2c3dbacc-106f-4053-8603-f649552f5513`.

A real bounded boot validated systemd running state, public HTTPS, Host-gateway
denial, absence of graphical packages and user configuration, and visible
Host/Environment entry and exit banners. It then stopped cleanly to tty1 with
no machine, failed unit, or network-rule residue. The local `apx` password
remains intentionally unknown and locked until the owner runs
`apx environment enroll-local-admin hub`; that command enables only
password-required Environment-local sudo.

The first real enrollment invocation then found a false `already enrolled`
result. `machinectl shell` was proven to return zero for both inner
`/usr/bin/false` and an absent-file test. Direct Hub inspection confirmed no
state mutation: the `apx` password remained locked, wheel and sudo policy were
absent, and no enrollment marker existed. The installed runtime now consumes a
fixed structured inner observation and verifies password status, wheel, exact
sudo policy, and marker both before and after enrollment. It cannot write the
marker after a cancelled or failed password change. The corrected full suite
passes 855 tests with 11 skips.

The first bounded input proof materially narrowed the existing graphical bug:
real ELAN pointer events reached the running graphical path and Hyprland's
cursor moved, while the selected i8042 keyboard produced no observed events and
the temporary shortcut did not execute. Automatic recovery returned tty1 and
left no graphical machine, unit, failed-unit, or registration residue. The
keyboard identity remains unresolved because subsequent Host-only attempts were
not explicitly synchronized with owner keypresses. On 2026-07-30 the owner
explicitly deferred the graphical input/button work and prioritized delivery
of the clean textual official Hub. Its cutover therefore does not depend on
graphical input evidence: it neither activates nor deletes the current
graphical generation, which remains stopped and fully preserved as
`hub-testes`. Input evidence remains mandatory before button work resumes.
The installed count-only adapter now observes the i8042 and internal USB ITE
keyboard candidates simultaneously, labels only their stable identities, and
discards key codes and values. Repository validation after this change passes
all 855 tests with 11 explicit skips, plus adapter compilation and
`git diff --check`.

The repository contains documentation, a non-mutating production-oriented
Python prototype, and a clearly separated guarded disposable-VM laboratory. The
main `src/` prototype implements read-only candidate, account, home, filesystem,
Btrfs, registration,
session, process, removal-blocker, host-readiness, and Brave-isolation
inspection. It also implements deterministic dry-run creation and removal
planning, formal registration parsing, consistency classification, rollback
classification, a read-only Stage 0 system-container readiness observer, and
extensive tests. The repository now also contains a pure typed contract for an
immutable Arch Linux Archive base snapshot. It deterministically distinguishes
rejected structure, incomplete signature evidence, and fully verified fixture
evidence without downloading or installing packages. Its schema-v1 JSON
boundary rejects duplicate and unknown fields, wrong types, unsafe extensions,
oversized evidence, and excessive package counts, and supports deterministic
canonical round trips. The prototype also renders a fixed, non-executing
snapshot-acquisition plan and a review-only Stage 2 dossier with typed intended
resources, exact candidate paths and limits, gates, effects, failure states,
risks, rollback rules, destructive-operation separation, blockers, and stable
digests. A fixed `apx host snapshot-readiness` observer models read-only capture
of pacman/GnuPG versions, installed package identities, and regular-file
identity/hash evidence for the three fixed Arch keyring inputs; it accepts no
caller paths or packages and performs no trust mutation.

The documented lifecycle and storage proposal defines logical objects, stable
and transitional states, snapshot consistency, archive publication,
restore-to-new-identity, explicit destruction scope, and conservative
incomplete-operation recovery. None of that proposal is a mutating
implementation.

The repository also implements a pure, non-mutating Environment isolation-
policy contract in `src/apx_policy.py`. It provides exactly two fixed reviewed
profiles: `normal-desktop` and `high-security-headless`. It deterministically
rejects writable host binds, privileged mode, mapping Environment root to host
root, direct devices, lingering, missing required namespaces, incomplete
teardown requirements, policy drift, and false VM-equivalent claims. This is a
testable specification, not runtime enforcement or proof of containment.

The repository now also implements the pure Hub-to-executor contract in
`src/apx_executor_contract.py`. It exposes only the fixed create, activate,
stop, force-stop, snapshot, archive, restore, destroy, and recovery operation
families. Strict bounded parsing rejects unknown or duplicate fields, commands,
paths, malformed identities, and wrong types. Assessment binds the exact fixed
plan, consequences, Environment generation, active Hub session, approval
strength, five-minute maximum lifetime, one-use nonce state, and authoritative
current-state confirmation. It performs no authentication, nonce reservation,
host observation, or mutation.

The repository now implements the executor journal state machine in
`src/apx_executor_journal.py`. Before an effect may be reported as complete,
the journal must identify that exact next effect; completion requires fresh
final evidence. Every transition binds the preceding record, and strict
parsing rejects corruption, extensions, reordering, and malformed state.
Recovery permits automatic rollback only for clearly APX-owned, empty,
unpublished, and unused resources. Published, used, modified, foreign,
identity-uncertain, and effect-outcome-uncertain resources are preserved for
review. A repository-only fixture store exercises atomic replacement, stale-
writer rejection, restrictive file modes, and refusal to follow symbolic
links. This is durable test-fixture behaviour, not the future authoritative
host journal, authentication, replay reservation, or a mutating executor.

The staged route to user testing is documented in `docs/testing-strategy-v1.md`.
Repository contracts and fake evidence are tested first; one headless disposable
Environment, two-Environment attack tests, graphical features, and destructive
recovery each require later separate readiness evidence and explicit approval.

The read-only CLI now provides `apx host doctor`, a plain-language front door
to the fixed `isolation-trial` Stage 0 checks. It reports stop, wait, or ready
for review without executing any plan. Positive evidence observed without an
authoritative host channel remains unconfirmed, while any visible identity,
path, registration, or mandatory-tool conflict blocks progress immediately.
The command explicitly excludes the existing manually created `apx-trial`
candidate from reuse, modification, or deletion.

The repository now implements a pure trust-evidence seal in
`src/apx_trust_evidence.py`. It binds one bounded set of readiness checks to
the exact snapshot-acquisition plan, observation time, observer class, and any
preceding seal. Raw diagnostic output is not retained; each observation is
represented by a SHA-256 digest. Only complete evidence from the future
authoritative executor can become `verified`; restricted observations remain
pending and any failed requirement remains blocked. Strict canonical parsing
rejects unknown, duplicate, missing, wrongly typed, reordered-identity, or
tampered evidence. This does not create or persist a real host seal, download a
base, or provide executor attestation.

The fixed Stage 0 isolation observer now checks Btrfs quota accounting with the
read-only `btrfs quota status /home` operation. It requires traditional full
accounting, consistent state, and normal limit enforcement. The user separately
authorized and performed quota enablement and a complete rescan on 2026-07-12
for `/dev/nvme0n1p2`, which contains `/`, `/home`, `/var`, and `/.snapshots`.
The reported state is enabled, full qgroup accounting, not inconsistent, no
limit override, eight automatic level-0 qgroups, and no configured limits. APX
did not perform this host mutation. Custom hierarchy, limit assignment, bounded
enforcement testing, and quota recovery remain unimplemented.

Production Environment storage is confirmed to be elastic rather than
preallocated: an Environment using 10 GiB consumes approximately its actual
charged extents, while another may grow to 40 GiB without reserving that space
in advance. Safety still requires independently enforced per-Environment and
APX-pool ceilings plus a non-APX host reserve. Automatic growth is allowed only
while all capacity and quota-health gates remain satisfied. The Stage 2 trial's
8 GiB root and 2 GiB home limits are deliberately small experimental safety
bounds, not product defaults. Exact production reserve and fairness policy
remain to be measured and selected.

`src/apx_capacity.py` now implements the pure elastic-growth and Stage 2
capacity gates. Growth is not preallocated: a request is allowed only within
the independently supplied Environment headroom, APX-pool headroom, physical
free space after the host reserve, and healthy quota evidence. The disposable
Stage 2 experiment fixes a conservative 64 GiB host reserve, 16 GiB combined
operation headroom, and 2 GiB metadata margin. These are experimental safety
values, not production defaults. The current real host has sufficient reported
free space and healthy top-level quota mode, but the bounded enforcement
fixture and authoritative metadata-capacity evidence have not run, so the
capacity gate remains blocked.

The user then manually executed the separately authorized leaf quota fixture
documented in `docs/quota-enforcement-fixture-v1.md`. Qgroup `0/263` enforced a
64 MiB referenced limit: an attempted 80 MiB write stopped at 67,076,096 bytes
with `Disk quota exceeded` and a non-zero result. Quota accounting remained
full, consistent, and without limit override. The user separately approved and
completed cleanup. After a normal restart, subvolume ID `263` and qgroup
`0/263` disappeared, the automatic level-0 count returned from nine to eight,
and quotas remained healthy. This proves one leaf limit and eventual complete
cleanup, not the intended hierarchy, snapshots, concurrency, executor
recovery, or attestation; the complete capacity gate therefore remains blocked.

The repository implements only the pure in-place migration assessment in
`src/apx_installation.py`; `docs/installation-migration-v1.md` now separates it
from the preferred clean headless path. Installation beside the current KDE
session, G2 cutover, and optional legacy cleanup remain secondary gates. The
new clean path requires remote project history, restore-tested backup,
boot-tested recovery media, typed bootstrap, headless Hub/Development,
two-Environment isolation, local package proof, lifecycle/storage/recovery,
H0, then graphical controls. Even complete in-place evidence permits only a
package-by-package cleanup review and never authorizes KDE removal. No clean or
in-place installer or cleanup implementation exists.

`src/apx_stage2_gate.py` now implements the pure final conjunction gate for
the first bounded host experiment. It requires exact dossier and acquisition-
plan identity, verified snapshot and authoritative trust evidence, ready
capacity evidence, absent intended identities, verified parents and
subordinate IDs, verified quota hierarchy, captured host invariants, bounded
network approval, authenticated/unexpired/unused human approval, authoritative
journaling, and separate cleanup scope. No single positive can override a
missing gate. Complete evidence yields only eligibility for a separate Stage 2
execution approval and never includes graphical use, KDE removal, or cleanup.

`src/apx_acquisition.py` now implements the pure network/file boundary for the
fixed dated Arch base acquisition. It accepts only HTTPS at the exact Arch
Linux Archive origin and date, the reviewed repositories and architectures,
safe unique canonical filenames, and bounded file/aggregate sizes. Credentials,
ports, queries, fragments, redirects, traversal, unexpected repositories,
wrong ordering, duplicate files, incomplete transfers, symbolic links, and
hash/size/identity disagreement fail closed. It validates supplied manifests
and post-transfer evidence only; it performs no network or filesystem access.

`src/apx_staging.py` now implements a repository-only acquisition staging
fixture. It reserves one new operation directory in a caller-provided
disposable parent, binds it to the plan digest, uses restrictive modes and
no-follow opens, enforces file and aggregate bounds while streaming, verifies
exact size and SHA-256, and publishes without replacement only after durable
validation. Partial or mismatched bytes remain explicitly partial and are
never adopted. Existing state, symlinks, non-regular entries, changed modes or
plan binding, duplicate names, and unsafe filenames fail closed. It never
selects or writes a production host path and is not the authoritative store.

The repository implements the pure complete-cleanup contract in
`src/apx_cleanup.py` and documents it in `docs/cleanup-completion-v1.md`.
The earlier optional `environment-only` scope was removed by the owner's
2026-08-22 policy: deletion always uses `complete-purge` and includes every
enumerated Environment copy. Completion requires selected resources, account, registration, runtime,
mounts, open handles, network state, deleted-subvolume records, and qgroups to
be absent; quota state must remain consistent and protected neighbors
unchanged. `<under deletion>` and `<stale>` remain visible as `freeing-space`.
Identity reuse is forbidden until complete. Observed physical reclaim is
reported without claiming it must equal logical size. The Hub now supports a
read-only `cleaning` card and retains it until final evidence passes. No
preserve-copies deletion path remains.

`src/apx_downloader.py` now implements a bounded streaming HTTPS transfer
contract with an injected non-redirecting opener and protected-byte sink. It
requires the exact archive host/date/path, a safe matching filename, status
200, unchanged final URI, one valid Content-Length, approved maximum and any
known exact size/hash. It closes and rejects redirects, early EOF, excess
bytes, malformed or non-byte responses, timeouts/open/read failures, digest
disagreement, and staging rejection. Tests use fake responses; the module does
not construct a network opener or perform a real download by itself.

`src/apx_http.py` now implements the fixed direct HTTPS opener for the Arch
Linux Archive. It disables environment proxies, cookies, and redirects; uses
the system CA trust with hostname verification and TLS 1.2 minimum; sends only
fixed non-secret GET headers; and rejects alternate schemes, hosts,
credentials, ports, query strings, fragments, changed final URI, invalid
timeouts, and sanitized connection/status failures. Tests inject responses;
no real acquisition has been performed.

The repository now composes bounded download and protected staging through
`src/apx_transfer.py`. `StreamingStagingWriter` writes chunks directly to one
exclusive partial regular file, enforces per-file and aggregate bounds during
the stream, and publishes without overwrite only after transfer and staging
size/hash evidence agree. Network or validation failure preserves the partial
identity and blocks blind retry. Integration tests use fake responses and
disposable directories; the composition does not select a production path.

`src/apx_database_acquisition.py` now implements the zero-argument fixed first
database acquisition: exactly dated `core.db` and `extra.db`, 64 MiB each and
128 MiB aggregate, into one new fixed `/tmp` root. The user separately
authorized and ran it on 2026-07-12. It transferred 8,818,209 bytes, published
exactly two mode-0600 regular files, and independent reopen/hash verification
matched both recorded SHA-256 values. Quotas stayed healthy; no installation,
extraction, execution, other download, or cleanup occurred. Exact evidence and
the preserved boundary are in `docs/database-acquisition-experiment-v1.md`.

`src/apx_repository_db.py` now strictly reopens staged Arch database archives
without extraction. It binds the regular-file SHA-256, bounds compressed and
expanded bytes and record counts, rejects traversal and unexpected archive
members, and validates unique safe package names/files, version, architecture,
sizes, SHA-256, base64 signature, and dependency fields. The two real staged
databases passed: 296 `core` and 14,842 `extra` package records. This validates
metadata structure only; it does not yet accept a resolved package closure.

`src/apx_resolution.py` now implements fixed offline resolution against only
the staged databases and an empty root/local package database. It runs pacman
print-only twice, requires identical output, cross-checks every selected field,
enforces seeds, uniqueness, 512-package and 4-GiB bounds, canonicalizes results,
and writes exclusive mode-0600 evidence. The real run selected 138 unique
packages totaling 128,264,129 bytes with manifest digest
`574f5d31e7c4ee46b1982fe2baf285d014ba0d712e91aea6d00413ba8fe5e3f9`.
No network, download, install, or extraction occurred. Exact evidence is in
`docs/package-resolution-experiment-v1.md`.

`src/apx_package_acquisition.py` now implements the zero-argument acquisition
bound to that exact manifest. The user separately authorized and ran it on
2026-07-12. Direct protected streaming published exactly 138 package and 138
detached-signature regular files totaling 128,294,816 bytes, below the
137,308,097-byte authorization. Independent reopen verified every package size
and SHA-256, signature non-empty/size/mode bounds, zero partials, and zero
unexpected entries. Quotas remained healthy; no install, extraction, execution,
other download, or cleanup occurred. Evidence is in
`docs/package-acquisition-experiment-v1.md`. Cryptographic signer verification
and independent second pass remain blocked.

The repository now implements a pure future-Hub view model in `src/apx_hub.py`.
It renders deterministic Environment and template cards, plain-language state,
warnings, and fixed request kinds from supplied evidence without reading or
changing the host. It enables normal actions only while one verified Hub is
active and the overall system is ready. Active, incomplete, unconfirmed,
duplicate, incompatible, or multi-active state fails closed. Delete requires
strong confirmation; unconfirmed state exposes only retry and read-only detail.
The complete visible flow is proposed in `docs/hub-experience-v1.md`; no
graphical application or functional lifecycle button exists.

The intended daily Hub interaction is now clarified: the owner uses a normal
Hyprland desktop with one APX taskbar control. Left-click expands about five
Environment choices directly upward; left-clicking one requests handoff.
Right-clicking a choice exposes its allowed management actions. Right-clicking
the APX control exposes create, archived Environments, and full management. The
full selected light management direction remains a secondary screen.

`prototypes/hub-demo` implements this interaction with in-memory demonstration
data, including create/delete confirmations and the full management screen. It
has browser-executed interaction tests and visual QA evidence, but no import of
APX host code, executor connection, Hyprland integration, persistence, or real
lifecycle effect.

Stage 0 has now been exercised on the real host without mutation. It confirmed
the fixed experimental identity is unused, `/home` is writable Btrfs with
capacity available, cgroup v2 and user namespaces are available, subordinate
IDs exist for `apx-development`, no systemd machine/image name collision was
found, and both AMD and NVIDIA hardware are present. The fixed Stage 2 headless
experiment plan is implemented but remains approval-blocked.

It does not create users or subvolumes, install isolated applications, launch or
switch Environments, write canonical registration, enforce isolation, manage
templates, run Odysseus, integrate Codex, or provide a Hub UI. Current manual
accounts have ordinary directories under the existing `@home` subvolume. SDDM
is the last confirmed display manager. The user-local Brave work is an
experiment, not an accepted application architecture.

## Development Method

1. Keep current observations, confirmed product intent, selected architecture,
   experiments, and open questions explicitly separate.
2. Translate the human objective into invariants and threat models before
   choosing mechanisms.
3. Prefer small reversible experiments with explicit backup, rollback, and
   acceptance criteria.
4. Treat restricted or sandbox-visible evidence as non-authoritative when host
   confirmation is required.
5. Specify typed operations, preconditions, postconditions, provenance, failure
   states, and recovery before adding privileged mutation.
6. Never expose an arbitrary privileged command channel through the Hub.
7. Test deterministic contracts and failure behavior before host experiments.
8. Do not modify the host from repository work without a separately reviewed
   milestone and explicit user approval.
9. Record conclusions from every experiment, including failed and inconclusive
   results.
10. Update this file whenever a goal, method, decision, or justified deviation
    changes.
11. Derive shared defaults from an explicit versioned base, never by cloning the
    live Hub or another mutable Environment.
12. Treat every package operation initiated inside an Environment as local to
    that Environment; host package changes require a separate host-level APX
    maintenance path and explicit authority.

## Deviation Policy

A deviation is acceptable when evidence shows that the current method cannot
meet the product contract safely, reliably, or maintainably. The same change
must record:

- the previous rule or assumption;
- the evidence that invalidated or limited it;
- the replacement decision;
- safety and compatibility consequences;
- migration or rollback implications;
- validation performed or still required.

The first recorded architectural correction is the application model. Earlier
documents assumed globally installed applications with only user data isolated.
The clarified product objective requires applications and their dependencies to
be local to each Environment. The technical replacement is intentionally open
until package, desktop, GPU, security, update, and storage experiments identify
a defensible mechanism.

The second clarification concerns common defaults. Total duplication is not a
product requirement: Environments may receive a shared baseline at creation.
For reliability and least privilege, the baseline is a declarative, versioned
artifact rather than the live Hub. This prevents Hub-only authority or mutable
state from leaking into workload Environments while still allowing consistent
hardware integration, fonts, networking support, and desktop defaults.

### Temporary Ollama Development Deviation

Until per-Environment application roots and services exist, the
`apx-development` account may temporarily use the already-present host Ollama
executable for Odysseus development. This is a development convenience, not an
accepted APX application-isolation mechanism or evidence that Ollama is local
to the Environment.

The previous rule remains the product requirement: the executable,
dependencies, service, configuration, models, and mutable state must eventually
belong to one Environment. Current evidence shows a host Ollama client at
`/usr/local/bin/ollama` and no implemented Environment package or service
boundary. A manual `apx-development` process successfully served the
user-selected model directory and Odysseus reached it through
`host.containers.internal:11434` only while Ollama listened on `0.0.0.0:11434`.
Closing the terminal stopped the process and produced an expected unavailable
response until it was restarted. This validates a lifecycle signal, not a
genuinely local installation or safe final network boundary.

The temporary replacement is deliberately narrow:

- do not install, update, or remove the host Ollama package or executable;
- do not create or enable a host system service;
- run Ollama manually as `apx-development` only when needed;
- select an explicit model directory owned by `apx-development` rather than a
  shared model directory;
- keep Odysseus configuration and mutable model state in the Development
  Environment account;
- do not describe Unix-account ownership as process, package, or GPU isolation.

This deviation shares the host executable, kernel, GPU devices, and any
executable-level vulnerability with the host. It does not prevent another
authorized host account from using the global executable, and its resource use
is not yet contained by an APX cgroup policy. Rollback is to stop the manually
started process and remove only the explicitly selected user-owned model state.
No host package rollback is part of this deviation because it authorizes no
host package change.

The selected model directory, manual start/stop behavior, listening-address
dependency, and a successful Odysseus request were exercised. Binding to
`0.0.0.0` may expose an unauthenticated API beyond the intended Environment and
is unacceptable as the final design. Disk/GPU resource behavior, private
Environment networking, readiness, authenticated management, crash recovery,
and teardown still require validation. The deviation must be retired when the
selected Environment backend can own Ollama and its service.

## Next Milestone

The package names, storage identities, resource limits, rollback boundary, and
snapshot evidence contract for Stage 2 are fixed in
`docs/base-and-storage-v1.md`. A dated 2026-07-11 acquisition candidate with
fixed derived source, staging/evidence paths, limits, phases, blockers, and
digest is ready for review. The trust mechanism is selected: explicitly freeze
the trusted host's installed `archlinux-keyring`, use it to authenticate a
matching isolated keyring archive, use pacman for fixed-path resolution and
download-only acquisition, `pacman-key` for primary detached verification, and
GnuPG for the reopened-file second pass. The next external-effect milestone is
to authenticate the matching keyring archive, approve bounded acquisition,
produce the real artifact, and verify every package signature and digest. Stage
2 creation remains a later separate approval. It must preserve these cases:

The acquisition phases, trust boundary, staging rules, independent validation,
publication semantics, failure classes, and remaining approval inputs are
specified in `docs/base-snapshot-acquisition-v1.md`. Exact intended Stage 2
resources, effects, gates, risks, rollback, destructive separation, and
blockers are summarized in `docs/stage2-approval-dossier.md`. Neither procedure
is authorized to run. Matching archive authentication, real signatures,
authoritative quota/capacity evidence, approval protocol, future executor
attestation, and separate human approvals remain unresolved.

The trust/tool identity observer was executed through an explicitly authorized
host context. It observed `archlinux-keyring 20260707.1-1`, pacman
`7.1.0.r9.g54d9411-2`, pacman-key `7.1.0`, GnuPG `2.4.9-1`, 17 keyring package
files with zero altered files, and the three fixed keyring hashes now frozen in
the acquisition plan. The CLI conservatively reported
`requires-host-confirmation` because the prototype has no privileged attestation
channel. The evidence closes the unknown version/file/hash inputs for planning,
but executor attestation and approval for the complete base acquisition remain
blockers.

A separately approved keyring-only acquisition then downloaded
`archlinux-keyring-20260707.1-1-any.pkg.tar.zst` and its detached signature into
operation-owned `/tmp` staging. The package SHA-256 is
`b47fc9c8066377e73d72bdb6a166bbbd829d5dcc745e424ef32436bd673cbc0d`;
pacman-key reported a full-trust good signature by fingerprint
`0429897DE5F3BDAC537A30696D42BDD116E0068F`. Direct use of the distributed
`archlinux.gpg` with gpg/gpgv failed due to its format. Exporting only the
trusted signer public key allowed a successful independent gpgv pass; the
exported key hash is
`0fcc071d58801d83e29a68f0ac0008c142f675cdfd8d8b7a27362ac1ec578470`.
Read-only metadata matched package name, version, architecture, and packager.
No package was installed. This closes the matching keyring archive blocker but
does not authorize or complete base acquisition.

The dated Arch repositories were resolved non-mutatingly to a closed set of 138
packages. A separately authorized download acquired exactly those packages and
their 138 detached signatures. Every package hash matches the closed manifest;
all signatures passed offline verification using current Arch master trust and
revocation inputs, followed by an independent `gpgv` pass that agreed on every
signer. The signature receipt digest is
`468116fb5277d91a099d0d4adbc5ca6579a5962965b062c0b6a1f09db9e4ea84`.
This completes acquisition and authenticity verification, not the base
snapshot. A bounded metadata-only pass has also matched the internal name,
version, and architecture of all 138 packages to the signed manifest. It
records 552,949,311 declared installed bytes and metadata digest
`0722db2c4a04f46d8617b7607e534dfd8429de6482bfbdaf57e3e69162a4f294`.
At that point a separately reviewed disposable extraction/build stage remained
required. No installation or host mutation was authorized by that evidence.

A separately authorized disposable extraction has now opened the complete
verified package set only under `/tmp`. The candidate contains 23,144 regular
files, 1,191 directories, 7,519 symbolic links and zero special files. It uses
606,330,880 allocated bytes under its 1 GiB ceiling. An independent tree walk
reproduced these results. Its tree digest is
`0f4e517a27ec474f63a3de74cec5df4f1a3adaee9a235a9c7e3c736a4e1622c1`.
This proves bounded assembly of a candidate filesystem; it does not admit a
base release, create an Environment, execute candidate content, or authorize a
host change. Candidate sanitization and structural validation are next.

Read-only candidate admission has now passed evidence integrity, core runtime
presence, and absence of machine-local identity. It truthfully reports four
blockers: raw extraction has development-fixture ownership, the local pacman
installed-package database is absent, isolated boot/stop has not passed, and no
generation-bound lifecycle record exists. The assessment digest is
`fcd1cc097f5ffb494225b73fe5bbbb627686a448b6542ae31587daa26900543a`.
`docs/first-environment-test-plan-v1.md` defines the closed route: rebuild a
correct offline disposable root, preview the isolated systemd-nspawn boundary,
perform one bounded networkless console boot, then verify complete stop and
cleanup. This remains a proposal and authorizes no package execution, boot, or
host mutation. A graphical Hyprland role follows a successful console gate.

The separately authorized first-console Phase A build has now created a correct
offline root only at `/tmp/apx-first-console-build-v1`. This is not a second
host Arch installation: it is the private filesystem intended for one future
Environment. Pacman installed the exact 138 verified local packages into that
root with networking disabled and recorded all 138 in its own local database.
The root uses 614,490,112 allocated bytes, has zero files owned by the
Development Environment identity, and retained zero special runtime entries
after bounded GPG finalization. Its final report digest is
`741fe1c332c334f9f0667b295ae98e7de686c752c3f415e169e0e48912535b68`.
No content has been booted. The next gate is an exact read-only boot preview;
actual systemd-nspawn execution requires separate approval.

The exact non-executing Phase B preview is now implemented. It preserves the
source through a volatile overlay, disables external networking and persistent
registration, shares no host path, applies private user mapping and a closed
device policy, and caps the test at 120 seconds, 512 MiB memory, 256 tasks, and
50% CPU. Its digest is
`676d22c1d3b9f8d5f9005d20583addeafdc0abdf42986b38b9c67cda29b8fd28`.
No container was started. Phase C boot and transient cleanup still require an
exact separate approval.

The first Phase C attempt was authorized against that digest but stopped before
systemd because nspawn requires comma-separated capability names. It returned
code 1, left zero matching processes and mounts, and preserved the source. The
failed-attempt report digest is
`daddc5109d728b2c9083114019da457568fa38488e5917409aa28c1f3fc5f413`.
The same protection list is now encoded with the required punctuation under
corrected preview digest
`53c30a3c55c1a6b5b196d9f73694b3b6851e7cab84fdcd6f4bcace24bdb91944`.
The executor intentionally refuses this corrected plan until separate approval.

The corrected plan was separately authorized and passed parsing, but the host's
`/tmp` filesystem cannot supply ID-mapped mounts. The attempt again stopped
before systemd with zero process/mount residue and an unchanged source. Its
report digest is
`0de4390b36caeb65f35fcc527ce92420615e263457b90bd09b2637295295bda7`.
Private-user isolation will not be removed. The new v3 preview creates a bounded
exact runtime copy below `/tmp/apx-first-console-runtime-v3`, permits ownership
shifting only in that disposable copy, retains all prior runtime limits, and
requires complete copy cleanup. Its digest is
`6853311174a1cf4b3822f663a96fc9715e8871f4b36e00ab7dd38400c4bc07a6`.
The executor refuses v3 until separate authorization.

V3 was separately authorized. It created and content-verified the bounded copy,
then stopped before systemd because nspawn forbids ownership shifting together
with its implicit read-only overlay. It left zero process/mount residue, removed
the copy, and preserved the source. Report digest:
`d13733fdf7ebf09a88b9072127a350f670997f40976cc517206a6afaedf428ae`.
The v4 preview removes only that redundant overlay: the disposable runtime copy
itself receives all writes and must still be removed. Every other boundary is
unchanged. V4 preview digest:
`0db2db8bdf726e4855244bb3201fb0290f2b5d15da1c6eaf7ee97494307c79c3`.
The executor refuses v4 until separate authorization.

V4 was separately authorized and retained a container PID 1 until the bounded
120-second timeout, after which it left zero process/mount residue, removed the
runtime copy, and preserved the source. It is not a passed boot because no
systemd readiness marker appeared and the private-user boundary rejected the
core rlimit. Report digest:
`6bd0d43a800b416201613932f93b8e2fe49c3f37dd834338cc5667c619a3c1f0`.
V5 enables explicit systemd console/status output and disables core-file
storage through a fixed policy only in the disposable copy. Every other limit
and cleanup rule remains. V5 preview digest:
`93aa2e816680a6f570ea584352063ab4841e5a1eca11cfc4ca0df466c9840c0e`.
The executor refuses v5 until separate authorization.

V5 was separately authorized and again retained container PID 1 to timeout,
then removed the copy with zero process/mount residue and an unchanged source.
Explicit console logging still produced no readiness marker, so it is not a
passed boot. Report digest:
`a68561a540c9cd2c8801df3e1696dded28581119fdd0577a2040938e2fa40156`.
V6 keeps the same isolation and adds at most 30 seconds of read-only `/proc`
observation to prove the PID 1 executable, four distinct namespaces, systemd
runtime marker, 138 internal package records, and hidden host Development home.
Its preview digest is
`7585522ccf01168db8efa4b6d6382d23f475bbc4b64d0f68580e127e189617ad`.
The executor refuses v6 until separate authorization.

V6 was separately authorized, observed for 30 seconds, returned code 0 after a
clean-stop request, removed the copy, left zero residue, and preserved the
source. Its observer missed PID 1 because it incorrectly required systemd's
mutable process title to retain an initial argument. Report digest:
`8d9cd684d9f670ba8ce08ac0bb751e490cbe73cae7d07610d18738c6f0816df1`.
V7 identifies the systemd executable and separately requires namespace PID 1
from the kernel's read-only `NSpid` field. No runtime boundary changes. V7
preview digest:
`0f59742d68e041b7bc2147dce7a2a901dd575ed0c99929875f1ac844dbcc883b`.
The executor refuses v7 until separate authorization.

V7 was separately authorized and produced the first positive isolated boot:
systemd was namespace PID 1, PID/mount/user/network namespaces differed, the
internal systemd runtime and 138 package records were visible, and the host
Development home was absent. Clean stop returned code 0, removed the copy, left
zero residue, and preserved the source. Report digest:
`310e12efec05eec8dcf7d52bc0192bf9289037c62d6b2ba83400e8c309be233e`.
The only false result came from expecting an invocation marker for a target
unit, which systemd does not publish. V8 uses the concrete user-session service
marker plus absence of `/run/nologin`; no isolation or execution behavior
changes. V8 preview digest:
`d0fa74a7695412a7cbc7560e70f879a3248562417754a1ac3895dd263c40e2f9`.
The executor refuses v8 until separate authorization.

V8 was separately authorized and repeated all positive isolation/lifecycle
evidence, but user-session readiness remained false after 30 seconds. It then
stopped cleanly with code 0, removed the copy, left zero residue, and preserved
the source. Report digest:
`e3a93175545bdeeeb56f1421eaee6bea98963f3c0bac33761c77a58185058b3d`.
V9 adds only fixed read-only `systemctl` queries inside the container for
overall state, multi-user/user-session state, failed units, and pending jobs.
It cannot change a unit. V9 preview digest:
`1f3bbd7c8b9701dd523c8185379093e82a8b9966e177dec229c296acc39aafa6`.
The executor refuses v9 until separate authorization.

V9 was separately authorized and completed the first console lifecycle gate.
Inside the isolated root, systemd reported `running`, multi-user and user-session
units were active, and no failed unit or pending job existed. All prior PID 1,
namespace, 138-package, hidden-host-home, clean-stop, zero-residue, copy-removal,
and source-preservation evidence repeated. V9 report digest:
`f129d383b0b6c4cc8a80882a46a7237c16becb76693a1af97b2f20ea11b44432`.
The final evidence-only assessment passed all six gates with digest
`de0266fa91884d05c84887a4a91740e52db82c3067d5fc454337f3509c6998b6`.
The next milestone is a separately versioned Hyprland graphical role: resolve
and authenticate its exact packages, define private display/GPU/input/audio/
portal/session boundaries, then perform a disposable graphical boot before
wiring the real Hub UI. The console result does not authorize those downloads
or device/session effects.

The first Hyprland graphical role is now resolved offline against the same
dated 2026-07-11 Arch databases. Fourteen explicit seeds produce 194 new
packages, 264,648,263 compressed bytes, and 1,022,339,199 declared installed
bytes; base plus role totals 332 packages. The manifest digest is
`e2f6adfc19e00dfe7cae21b4eab1650437edf24d817dc355a9af449d1cd9b25e`.
No network, download, installation, extraction, or graphical execution occurred.

The host has AMD PCI `0000:05:00.0` using `amdgpu` and NVIDIA PCI
`0000:01:00.0` using `nouveau`. `docs/hyprland-graphical-role-v1.md` selects
only AMD for G0 headless rendering, keeps KDE available for G1 nested display,
and defers physical KMS/input handoff to G2. NVIDIA, raw input, audio, and host
Wayland/PipeWire/D-Bus/portal sockets are not part of G0. Waybar is not the
final panel; the expanding APX taskbar control remains a dedicated component
with a desktop-independent lifecycle contract. Package acquisition and every
graphical/device/session effect require later approvals.

The graphical role packages were then separately authorized and acquired from
the dated Archive: exactly 194 packages plus 194 signatures totaling
264,707,836 bytes. Independent reopen matched all package sizes and hashes and
found zero missing, unexpected, or partial files. No package was installed,
extracted, or executed and no GPU/system effect occurred. Detached-signature
trust verification and the independent second cryptographic pass remain the
next gate before any role build.

All 194 graphical package signatures subsequently passed offline GnuPG trust
validation and an independent `gpgv` pass; both paths agreed on every signer
across 25 trusted primary identities. Evidence digest:
`15ee100d7be5bfef16278f476503c2b2d7e3546fb3027b5f3a541180dc302863`.
The first attempt safely exposed an overly broad interpretation of bare
`KEYEXPIRED` warnings from unrelated historical subkeys. The corrected policy
still blocks `EXPKEYSIG`, expired signatures, revoked/unknown/bad signatures,
and insufficient Arch master trust. No install, extraction, execution, GPU, or
system effect occurred. Bounded metadata inspection and a separately approved
disposable graphical-role build are next.

Bounded `.PKGINFO` inspection has now matched the internal identity of all 194
graphical packages to the signed manifest and reproduced 1,022,339,199 declared
installed bytes. Metadata digest:
`89ed0ab7623a93972bb403af33bbda4ee1ebb2717d285455fa4a240adea455df`.
No other package content was extracted or executed. A separately approved
offline build into a disposable copy is now the next gate; GPU and graphical
execution remain later and separate.

The separately authorized offline Hyprland role build has now copied the proven
console root to `/tmp/apx-hyprland-build-v1` and installed only those 194
verified packages into the copy with external networking disabled. Its internal
database contains 332 packages and the result uses 1,739,587,584 allocated
bytes under the 3 GiB ceiling. Full source content digests before and after
matched; zero Development-owned entries and zero special runtime files remain.
An independent read reproduced the report digest
`9331a5cf181fa550cc163a179a340aa17cc1f01aa6b2167585e8b909b087ce0e`,
package count, and Hyprland/UWSM/Foot presence. Nothing graphical was launched
and no GPU, display, input, audio, host session, Btrfs, persistent service, real
user, prior-area cleanup, or main-Arch package effect occurred. The next gate
is a separately bounded G0 headless launch using only the intended AMD render
device; it must preserve KDE and deny physical display and input access.

A 2026-07-13 reconstruction after `/tmp` cleanup reproduced the exact dated
database hashes, 138-package manifest, double signature evidence, and package
metadata digest. Its offline base build kept the same package count and storage
ceiling but legitimately differed by 40 logical bytes and generated a new
Environment machine identity. The finalizer previously required the historical
build-report digest and therefore blocked a valid reconstruction. The accepted
reconstruction rule now verifies the canonical report digest plus the closed
manifest, signature evidence, package counts, byte ceilings, ownership, and
identity invariants. It does not treat per-run GnuPG/log/identity bytes as a
reproducibility identity. A new final report remains bound to that exact rebuilt
root and does not replace the historical evidence digest.

The same reconstruction encountered repeated Wi-Fi interruption during the
194-package graphical acquisition. The staging correctly preserved completed
files and one `.partial` entry but intentionally refused implicit adoption. A
fixed recovery path now revalidates the plan, directory and file metadata,
expected names, package sizes, and package hashes, removes only recognized
partial files, and fetches only missing requests. Preserved signatures receive
no trust from resumption and must still pass the complete offline double
verification. This is a transport recovery rule, not package admission.

The recovered acquisition completed all 388 package/signature files with zero
partials. All 194 graphical packages then repeated the two independent
signature passes and exact metadata digest. The rebuilt graphical root contains
332 packages, uses 1,739,587,584 allocated bytes, preserves its reconstructed
base, and has zero Development-owned or special runtime entries. Its new
root-bound report digest is
`79aec029862f03c169afde83c97a1eb3fc67918b5826823f6c5b3e1f64831f56`;
G0 v13 is now bound to that digest rather than the removed historical `/tmp`
root.

G0 v13 completed with report digest
`abbb2428c5b288c9ffdc7cf624c607f908d2fab98e1e1a5da029af6334b03ef5`.
It passed container PID 1, private namespaces, 332 packages, transient seatd,
zero other DRM visibility, source preservation, zero process/mount residue,
and runtime removal. Hyprland still did not open AMD or publish `HEADLESS-0`.
The retained trace plus Aquamarine 0.12.1 source establish that the DRM backend
enumerates and selects canonical `cardN` devices. `AQ_NO_KMS_REQUIREMENT`
permits a card without outputs but does not turn the physical AMD render node
into a separately selectable compositor card. Exposing `/dev/dri/card2` would
add physical KMS authority and is forbidden in G0. This is an accepted negative
hardware/backend result, not permission to broaden the grant. G1 nested without
direct DRM is next; exclusive AMD KMS belongs only to a separately reviewed G2
after KDE teardown is proven.

A non-executing G1 v1 preview is now bound to the rebuilt 332-package root and
the current KDE socket `/run/user/1002/wayland-0`. It keeps the container network
private and the device policy closed, with no direct DRM, input, audio, D-Bus,
PipeWire, portal, or host-home path. Its one added surface is a read-only bind of
the exact Wayland socket to a fixed internal path. This is a provisional
functional test, not an accepted isolation boundary: direct Wayland protocol
exposure and host-session lifetime still require mediation. No G1 container or
window has been launched. The exact non-executing preview digest is
`42f2b4a128e95c6b9e12e0f9feb6f59147711e4a9920b7a62fa0dc2884f0dc03`.

The G1 campaign then completed the nested graphical gate. V1 confirmed that the
private-user mapping correctly prevented the internal UID from connecting to
the KDE socket as host UID 1002. V2 used a temporary ACL for only the exact
shifted UID and restored the original ACL byte-for-byte; it reached the Wayland
backend but lacked a renderer. V3 added only AMD `/dev/dri/renderD129`, never a
KMS `cardN`, and produced `WAYLAND-1`; v3/v4 exposed and safely recovered from
an outer-wrapper teardown defect. V5 signaled inner Hyprland directly and
passed: `WAYLAND-1` at 1280×720/60, a 4,319-byte internal screenshot, Hyprland
exit code 0, 332 packages, private namespaces, one render node, hidden host
Development home, exact ACL restoration, unchanged source, runtime removal,
and zero process/mount residue. Report digest:
`7e2328625de5fde3ba15b1f249f2108922fe14b1de475d88f4b42af32386bb82`.

This is a functional and cleanup proof, not acceptance of direct KDE Wayland
protocol exposure as final isolation. Production mediation remains required.
For the current KDE/SDDM machine, the next physical compatibility gate is G2:
prove KDE teardown, exclusive AMD KMS and mediated input ownership, bounded
failure recovery, and return without residue. For the preferred fresh headless
installation, H0 is the first physical gate and G2 is not a prerequisite.

That G2 design and acceptance contract is now recorded in
`docs/hyprland-g2-exclusive-session-design-v1.md`. It fixes a no-network,
AMD-only, disposable boundary; separates the broker, executor, and Environment
adapter; orders KDE stop, authoritative release proof, exact device grant,
hidden launch, reveal, revocation, teardown, and verified return; and defines
mandatory failure exercises. It explicitly forbids wildcard DRM/input grants
and treating a blank display as proof of release.

The companion `docs/hyprland-g2-broker-recovery-boundary-v1.md` now selects the
candidate boundary for this experiment only: one host-owned text recovery VT,
one separate Hyprland experiment VT, temporary exact SDDM quiescence, and a
host-owned per-run mediator that provides revocable descriptor access only to
the approved GPU and input identities. The recovery controller has a closed
interface and no shell, while the executor owns deadlines, journal, revocation,
and authoritative state. This does not adopt SDDM, `greetd`, a production
broker, or a mediator implementation. No executable G2 preview is safe yet:
the exact controller and SDDM mechanisms, installed-version adapter and host
observations, stable device resolution, mediator compatibility, fixtures,
physical recovery rehearsal, and fresh approval remain absent.

The companion `docs/hyprland-g2-kde-release-proof-v1.md` now selects the
authoritative outgoing-session release contract. KDE adapter acceptance is
only permission to observe; release requires two complete, generation-bound
passes across login session and seat, cgroups and descendants, user services
and assistants, graphical IPC, AMD DRM/connector ownership, selected input and
VT ownership, mounts, namespaces, helpers, and SDDM absence. Refusal, timeout,
missing facts, identity change, or contradiction blocks the device grant and
enters recovery. The installed KDE/Plasma request, exact SDDM runtime operation,
host-version observation APIs, pure evaluator fixtures, read-only preview, and
fresh approval remain required. This documentation authorizes no host effect.

The first non-disruptive G2 host observation is recorded in
`docs/hyprland-g2-read-only-observation-2026-07-13.md`. The installed stack is
Plasma/KWin 6.7.2, SDDM 0.21.0, and systemd 261.1. The host login manager showed
the active Development KDE session on `seat0`/`tty4` and a second live inactive
Hub KDE session on `seat0`/`tty1` retained by `sddm-autologin`; the latter still
had its own KWin, Xwayland, Plasma, portals, audio, secret, and lock processes.
Consequently G2 must gracefully release and independently prove both graphical
session generations absent, not only the foreground desktop. SDDM must also be
quiesced against greeter respawn and Hub autologin before any KMS grant.

The same observation proved that component versions, login/session/cgroup
identity, SDDM lineage, Wayland socket identity, AMD PCI/card/connector ancestry,
ordinary DRM pathname descriptors, and input ancestry are readable. It found
current AMD users including Xwayland, Plasma Shell, Brave, and a KDE logout
greeter. KWin was not represented as an ordinary `/dev/dri/*` pathname in that
scan while logind still marked the AMD devices as seat-managed, so `fuser` and
`/proc/*/fd` absence cannot be the sole DRM release proof. DRM master/logind
reference/lease inspection, a version-bound two-session observer schema, exact
Plasma logout behavior, SDDM quiescence, recovery VT, and device mediator remain
blocked. No logout, service action, or device effect occurred.

A follow-up read-only availability check found the DRM debugfs boundary is
root-only and the login-manager seat API exposes active/session ownership but
not the complete DRM master/lease tree. `modetest` exists but was deliberately
not run because opening the primary DRM node is outside the non-disruptive
availability gate. The selected release direction is a narrow executor-owned
cross-check of all resolved primary/render descriptors, matching kernel DRM
client state when available, and logind seat/session state. The executor exposes
only a typed result. This is still unimplemented and untested; no new user,
Hub, adapter, or Environment access to debugfs or DRM is proposed.

The logical G2 observer/evaluator schema is now recorded in
`docs/hyprland-g2-release-observer-schema-v1.md`. It discovers every graphical
session from the physical seat instead of trusting fixed session numbers,
classifies systemd user-manager records separately without ignoring their
resources, freezes SDDM/greeter/autologin topology, and records process/cgroup,
IPC, mount, namespace, recovery, selected input, and separate AMD primary,
render, master, lease, login-manager, connector, and NVIDIA-exclusion fields.
Its public outcome is only `released`, `blocked`, or `unknown`; only two complete
clean observations in the same boot/generation after the bounded stability
interval can report `released`. Any reboot invalidates the prior baseline and
all transient identifiers. Unknown sources, topology disagreement, or changed
identity fail closed. The schema is complete logical architecture, not an
implementation. Source-adapter/evaluator implementation and fixtures, SDDM and
Plasma operations, recovery controller, device mediator, bounded-evidence
validation, a fresh post-reboot preview, and approval remain required.

The logical source/privilege mapping is now recorded in
`docs/hyprland-g2-observer-source-adapters-v1.md`. It separates an unprivileged
collector, one exact outgoing-session KDE adapter, a narrow privileged read-only
source, and the independently approved effect executor. Every schema area is
mapped to package provenance, login1/systemd D-Bus, cgroup/proc, sysfs, Wayland
object metadata, matching kernel DRM client state, input ownership,
mount/namespace identity, or recovery-controller evidence. The privileged
reader accepts only signed-plan identities, re-resolves them, never opens a DRM
or input node, never runs `modetest`, and returns bounded typed facts rather
than raw debugfs/proc output. No general root shell, sudo path, group/ACL change,
world-readable debugfs, broad polkit rule, or runtime privilege widening is
proposed.

The DRM schema was corrected to admit only an exact baseline-bound host kernel
console/fbdev client for the recovery VT while still requiring zero outgoing or
unexpected primary/render clients, no lease, no outgoing logind device
reference, matching connector identity, and NVIDIA exclusion. An unclassified
kernel client remains `unknown`. First denial limits are 10 seconds and 4 MiB
per observation, a two-second minimum stability interval, a 30-second pair
deadline, and fixed count/string ceilings. The adapter design and limits are
not implemented or validated; installed-version fixtures, a fresh post-reboot
read-only preview, exact Plasma/SDDM effects, recovery controller, device
mediator, and explicit effect approval remain required.

The first separately authorized G0 attempt passed its system-container,
namespace, exact-device, source-preservation, and teardown boundaries. It
exposed only AMD `/dev/dri/renderD129`, with zero other DRM nodes, and left zero
processes or mounts before removing the runtime copy. Hyprland briefly started
but exited without publishing `HEADLESS-0`, opening the render device, or
creating a screenshot, so G0 has not passed. Report digest:
`40d8a76dbe8c7f1e602b90868b68a6b31f101cc7a08a3065ef3240fda0d995a3`.
The first runner did not retain its bounded output, preventing a proven cause.
A non-executing v2 correction uses an ordinary UID 1000 only inside the runtime
copy and preserves up to 1 MiB of diagnostic output in a separate evidence
directory. It retains every prior isolation and cleanup boundary and requires
fresh authorization before another GPU-visible execution.

G0 v2 was separately authorized and again passed container PID 1, private
namespaces, 332 internal packages, exact AMD-only visibility, unchanged source,
zero residue, and runtime-copy removal. Running as ordinary internal UID 1000
did not resolve rendering: retained diagnostics show Aquamarine failed at
`CBackend::create()` before Hyprland opened the render node or published
`HEADLESS-0`. Report digest:
`c2d19362a2cdab0787938da8caf634a1aeb08c8e8f729637d776bf7984233f72`.
Current official documentation confirms the render-only environment flags.
A prepared, non-executed v3 keeps the identical device boundary, creates the
missing internal cache path, and enables bounded Hyprland/Aquamarine tracing.

G0 v3 was separately authorized and again preserved the complete outer safety
boundary, but still did not open AMD or create `HEADLESS-0`. Its report digest
is `20f23e577319176e3dc1373649bcd7620f9705fffa15fdf3494894f8dbc695ea`.
The runtime copy was removed and the bounded trace was retained under the
protected v3 evidence root. A subsequent read was refused because the host
authentication window had expired. The next action is read-only diagnosis of
that existing trace, not another graphical execution or broader device access.

The user supplied the protected v3 trace. Hyprland loaded the intended config
and then failed at `CBackend::create()`; the later `lspci` and working-directory
messages are crash-report side effects. The test incorrectly forced unsupported
`LIBSEAT_BACKEND=noop`; current libseat offers seatd, logind, embedded seatd,
and automatic selection. A prepared, non-executed v4 removes only that invalid
override and captures any crash report before deleting the runtime copy. It
does not broaden device, session, namespace, time, or persistence authority.

G0 v4 was separately authorized and its preserved crash report proved that
Aquamarine found neither a seatd socket nor a logind primary session for the
disposable user. It therefore never opened AMD. Every outer isolation and
teardown check passed; report digest:
`5974fa90c3b66277dbcc1c32b1fb383d00c6c269cb72070d0cfadff7d4355518`.
A prepared, non-executed v5 runs the already-packaged seatd binary only in the
foreground inside the disposable container, with a private socket owned by the
disposable user. It creates/enables no service and retains exact AMD render-only
visibility, private namespaces, bounded time, source preservation, and cleanup.

G0 v5 was separately authorized. Its transient seatd process stopped before
creating the socket because the packaged Arch version rejects `-s`; Hyprland
therefore repeated the known no-seat failure. Isolation, unchanged source, zero
residue, and runtime removal passed. Report digest:
`8e178e66be24cde9907d87862dceb2ef7ee18cf6325d15a8345cbb3badae10d6`.
Arch seatd defaults to `/run/seatd.sock`; prepared, non-executed v6 removes only
the incompatible option and retains every safety boundary.

G0 v6 started the transient mediator but uncovered a teardown bug in the test
runner: it signaled the outer namespace wrapper rather than inner seatd and
raised before normal cleanup. APX immediately observed the exact v6 processes
and mount, stopped the container, verified mount disappearance, and deleted only
the authorized v6 runtime copy. No v6 evidence report was published, so the
render result is inconclusive. Prepared v7 targets the inner daemon PID and
registers emergency teardown for unexpected runner exceptions. The user's
standing authorization permits further G0 versions only within the unchanged
AMD-render-only, no-network/input/audio/KMS, 120-second, disposable boundaries.

G0 v7 passed transient-seat startup, direct inner-process teardown, and all
prior cleanup gates. Seatd nevertheless kept the client inactive because it
could not bind to an intentionally absent physical VT, so no device opened.
Report digest:
`43a7d155b5c9f8f39928416d5b6d718961bf4f945935e6983e34e8b9f108cb7b`.
Official Arch seatd documents `SEATD_VTBOUND=0` for a seat not bound to a VT.
Prepared v8 adds only that setting and does not add KMS, input, or another
device.

G0 v8 activated the official non-VT-bound seat, but seatd and Aquamarine proved
the nspawn-created render entry could not be canonicalized or opened. Cleanup
again passed; report digest:
`555e54af0d09c4937afe74b06464d6ea941e0bc06046b2a320647205b0d7e5c7`.
Prepared v9 replaces only that unusable bind with an ephemeral internal
`/dev/dri/apx-amd-render` character node carrying the exact authorized AMD
major/minor `226:129`. The closed outer device policy remains unchanged and no
KMS, input, or other device is added.

G0 v9 again cleaned up safely but did not publish the headless output. Report
digest: `7370f014e3f8b847c47f511a669b13d3483b6d2f82e20c5b9ffa45f6f3def78d`.
The root-owned evidence read was blocked after host authentication expired.
Prepared v10 repeats the same runtime and device boundary while assigning only
the new evidence directory/files to Development UID 1002, avoiding repeated
administrator reads without exposing runtime or source content.

G0 v10 made evidence directly readable and proved the current Aquamarine build
does not accept an arbitrary alias for the explicit DRM device. It continued to
seek the standard AMD render name. Cleanup passed; report digest:
`c3e20c7fa4b0d2e762aaadd1046d5f8588209ff56c4b27deb5bc968a34cbe6e2`.
Prepared v11 retains the ephemeral character node and exact major/minor
`226:129` but names it `/dev/dri/renderD129` as expected by the backend.

G0 v11 still failed to open the standard-named node, while cleanup passed;
report digest:
`9fe499eecc102200d01a4c81637ef14e83823b0d7eb3f650f8964a95129e2854`.
The node-creation umask could remove write permission. Prepared v12 explicitly
sets `0666` to match the authorized host render node and records the internal
user's bounded pre-launch stat evidence.

G0 v12 left zero observed process, mount, and runtime-copy residue, but its
outer authorization wrapper remained stuck after the Python child ended and no
final report was published. The render result is inconclusive. Prepared v13
writes a bounded Development-readable progress journal from the beginning so
the last completed stage survives any outer-wrapper failure. The prepared
evidence path and files remain executor-owned and only group-readable by the
Development identity; fixed ownership, permissions, and no-follow opening keep
read access from becoming control over a privileged evidence path.

- two Environments independently installing the same application;
- deletion without residual application or user data;
- desktop operation under Hyprland, KDE Plasma, and GNOME;
- GPU, audio, input, portals, notifications, secrets, and removable devices;
- normal and high-security profiles;
- updates, rollback, templates, snapshots, backup, and recovery;
- reproducible common-base updates without mutable cross-Environment state;
- Odysseus limited to one active Environment;
- no ordinary Linux user chooser during boot or switching.

The graphical architecture now also fixes Hub-only lifecycle authority. Every
Environment may show an APX button, but workloads receive only return-to-Hub
and read-only actions. The executor uses separately trusted active-session
context: only an authenticated, authoritative Hub may switch or manage
Environments, while a workload may gracefully stop only its own generation.
ASCII animation and ASCII-inspired controls are recorded as a future,
replaceable ricing layer rather than part of the security boundary.

The role-aware GTK prototype and pure trusted-launch decision now implement the
same split without real effects. The launcher derives the UI role only after
active authenticated graphical-session facts exactly match verified
registration name, role, and generation. The full repository suite passes 800
tests with 11 expected external-fixture or privilege-context skips.

The disposable runtime now independently enforces the canonical Hub identity:
`hub` accepts only admitted Hub roles, and no other logical name can acquire a
Hub role through creation, a forged registration, or restore. Graphical config
creation no longer copies an open-ended directory tree. It admits exactly the
three versioned regular files with matching SHA-256 digests and refuses missing,
extra, changed, linked, special, or oversized entries before publication.

The changing GTK demonstration is no longer represented as an immutable
production Hub asset. It is explicitly outside the base release; a future
production Hub overlay needs its own closed manifest and both fake- and
typed-executor validation gates.

Hub authority now additionally requires canonical name and role to agree at
the executor and UI-launch boundaries. The typed executor catalogue includes a
Hub-only `configure-capabilities` family. Its separate plan keeps optional
camera, microphone, controller, and removable-storage mediation absent by
default, requires a stopped target generation and explicit confirmation, and
never changes the essential baseline or activates the Environment.

The GTK prototype delays importing GTK until after CLI role/mode checks. Its
help and workload-management refusal therefore run successfully in the current
headless Development context without installing `python-gobject` or opening a
window. A separate pre-freeze contract defines the evidence a later production
Hub client needs, but intentionally cannot admit it or freeze its artifact.

After the 2026-07-18 battery-loss reboot, a fresh read-only system-scope check
observed zero failed systemd units, zero registered machines, and no graphical
session. Only the expected root tty1/manager sessions were listed, while
`apx-pilot-executor.service` was active. This confirms no observed Hyprland or
Environment runtime remained stuck after the power loss; it does not unlock H0
physical execution.

The graphical button path now has an effect-free exclusive handoff state
machine. It models Hub stop, broker transitions, hidden incoming start,
readiness-gated reveal, workload return, and Hub recovery with one seat owner at
every phase. Recovery and watchdog evidence is mandatory before Hub stop;
release/readiness evidence cannot be replayed between transitions. The internal
executor passes a complete Hub-to-workload-to-Hub cycle and failure injection
before all eight stages reaches terminal broker-owned recovery. This path is
test-only and is not exposed by the GTK product prototype.

Hub controls now convert into typed executor intents only when their action ID,
operation kind, enabled state, approval class, target generation, and trusted
canonical Hub context all agree. The workload return control produces only a
generation-bound `stop` for itself. An integrated effect-free rehearsal proves
both executor assessments, the broker boundary, the exclusive handoff, and the
final `hub-active`/Hub-owned state together.

The new manual physical round-trip assessment truthfully remains `blocked`.
Positive current evidence is limited to the repository integration, installed
typed pilot executor, post-battery tty1 recovery observation, and absence of
failed/uncertain observed runtime state. Missing gates are the admitted
graphical base release, admitted production Hub client, installed graphical Hub
and workload, installed trusted launcher and exclusive broker, verified
mediated device adapter, verified independent graphical watchdog, and an
unlocked physical H0. Completing the pure contracts does not satisfy those
physical gates or authorize a test.

At the owner's request, the disposable web/terminal handoff simulation, its
tests, its GTK fake-executor mode, generated bytecode, and documentation were
removed completely. Internal effect-free state-machine and integration tests
remain as non-product regression infrastructure.

Development has moved to the real executor-v1 boundary. The client fixes the
Unix endpoint, timeout, request format, response limit/framing/schema, protocol,
and operation binding. The endpoint core retrieves plan/approval/state only
through trusted authorities, assesses the full contract, atomically reserves
the nonce, and invokes only the typed plan adapter. Rejection cannot reach an
effect; post-reservation failure becomes `incomplete`. Durable stores, a socket
server wrapper, and physical session/device effects remain unimplemented and
uninstalled.

No container creation, package change, Btrfs mutation, or privileged operation
is authorized merely by the plan. The first host mutation requires a fresh
review of the exact base source, disk budget, created resources, backup,
rollback, and approval request.

On 2026-07-18 the owner authorized the first normal graphical Environment.
Two builds from immutable `hyprland-h0-v1` produced the same 402 packages and,
after identity/build-cache normalization, the same content digest
`a43e3336ace31b21d250abdce25ed5bdfe4b506a7148902d4f5f150c52dd4e85`.
The resulting `hyprland-base-v1` is read-only; the second build remains in
quarantine as reproduction evidence.

The first stopped workload was initially published with the invalid doubled
logical prefix `apx-test`. The validator correctly exposed that the logical
name must be `test`, which derives runtime machine name `apx-test`. The old
empty stopped tree was moved intact to quarantine. The corrected stopped
`test`, generation `69b56acc-fd4d-4499-8009-e1d0108466f4`, includes Hyprland,
Waybar, Rofi, Alacritty, Fastfetch, Chafa, audio,
network, notifications, portals and AMD graphical userspace. Seven
digest-bound config files were copied independently into its home. Its actual
Hyprland config returned `config ok` and Fastfetch ran in a device-free nspawn
validation. Eww is deferred as an optional later overlay because it is absent
from official Arch repositories.

No graphical process or device grant occurred. The visual round trip remains
blocked on the graphical Hub, production Hub client, installed broker/socket,
and recovery-bounded mediated activation. The physical H0 code lock remains.

The owner subsequently replaced per-Environment size caps with a flexible
shared storage policy. New contracts no longer ask the owner to predict root or
home size when creating an Environment. They require a shared APX pool and a
fixed 32 GiB Host/recovery reserve. Existing physical leaf limits remain in
place temporarily until a reviewed hierarchical Btrfs pool limit can replace
them; removing them first would expose the Host to complete disk exhaustion.

A separate graphical Hub candidate now exists in quarantine with an independent
root/home and config seed; the registered headless Hub is unchanged. The GTK
client no longer contains demonstration data or disabled fake buttons. It
loads a single fixed Host-issued session descriptor, derives its role from that
descriptor, and sends only complete typed executor requests. Hub descriptors
may contain activate actions; workload descriptors must contain exactly one
generation-bound stop for themselves. The client is installed in the Hub
candidate and `test`, but no descriptor issuer, executor-v1 socket server, or
physical graphical broker is installed yet, so every real button remains
fail-closed rather than simulating success.

The Host-side session issuer now creates the exact descriptor, plans,
approvals, and requests together. Hub sessions can receive only typed activate
actions; a workload receives exactly one stop action bound to its own logical
name and generation. All actions expire within 300 seconds and bind the trusted
active session identity. The physical Hub/test plan then binds the current
`test` generation, graphical release manifest, AMD card2/renderD129, built-in
keyboard/touchpad event3/event11, tty2, and a non-extendable 15-second recovery
deadline. A fresh read-only physical observation passed every clean-host gate;
plan digest is
`7603c8d17c787ed4122cff9520f49392c0865412967b5a53e9b595ff8dec43f3`.
This is still a non-executing plan: the Host effect adapter and graphical Hub
publication are the remaining boundaries before a visual run.

The Host recovery adapter subsequently passed a real harmless rehearsal: an
independent three-second timer was active before a constrained `sleep 60`,
terminated only that unit, restored tty1, and left no machine, failed unit, or
runtime residue. The same recovery path then bounded real `test` activations to
10 visible seconds inside a 15-second absolute deadline. After adding an
Environment-local D-Bus session, structured observation proved the nspawn
machine, Hyprland, Wayland socket, Waybar, and enabled 1920x1080 `eDP-2`; final
recovery again restored tty1 with zero residue. Waybar reported its 1920x30 bar
on `eDP-2`.

Replacement plan
`e6f99a38aecc88088949770c3213b2690aadcdefcad75c62c06de86b0776abee`
then published graphical Hub generation
`2c3dbacc-106f-4053-8603-f649552f5513`. The previous stopped headless Hub was
moved intact to
`/var/lib/apx/quarantine/retained-hub-headless-v3-d68ee7a2` and remains the
rollback; no Hub graphical activation occurred during publication.

Rebinding the exclusive runtime plan to the published Hub generation produced
current plan digest
`2def2bb58aeb6aa3b15cfd7764421c94e94cbd1c092fccddefcf7eeb3787c64f`.
The earlier `7603...` digest remains historical evidence for the successful
pre-publication `test` proof and must not be replayed for the Hub round trip.

Review before installing the executor-v1 socket exposed a real schema mismatch:
the pure executor contract currently models `expected_generation` as an
integer, while every physical registration uses a UUID string. All earlier
executor tests used synthetic integer generations, so they do not authorize a
physical request. The server must not hash, truncate, or silently map the UUID.
Either the protocol must evolve to canonical UUID generations or a durable
executor-owned serial-to-UUID binding must be added and verified by the effect
adapter. Until that binding is closed and hostile-tested, the new socket stays
uninstalled and no button can cause a physical effect.

The protocol has now evolved without a lossy mapping. Existing positive
integer generations remain accepted only for legacy laboratory fixtures;
physical requests preserve canonical lowercase UUIDv4 strings end to end in
plans, requests, approvals, requester context, current-state evidence, and
desktop descriptors. Truncated, uppercase, non-v4, malformed, boolean, stale,
and cross-bound values fail closed. The socket remains uninstalled until its
atomic plan/approval/nonce stores and peer-to-active-machine authentication are
implemented and tested.

The first durable executor-v1 store is now implemented and its empty physical
directories are installed at `/var/lib/apx/executor-v1` with root-only mode
0700. Plans are recomputed from fixed policy before write and after read;
approvals require verified authenticity; records are immutable create-once
0400 files; symlinks, wrong ownership/type/schema/digest, and malformed UUIDs
are rejected. Nonces use atomic exclusive creation, so replay returns false
without replacing the original request digest. No plan, approval, nonce,
socket, service, or effect is currently published.

The executor-v1 Unix transport and production authority composition are now
implemented but not installed as a service. The kernel peer PID/UID/GID must
map to UID 1000 inside the exact active generation-named graphical systemd
unit; root-owned active-session state must match the root-owned physical
registration name, role, UUID, running state, and expected unit. Wrong UID,
vanished PID, other cgroup, forged Hub role, stale UUID, changed unit, symlink,
or malformed state fails before plan/approval lookup. Transport accepts one
bounded newline frame, silently drops malformed/unauthenticated peers, and has
no network listener. The socket remains absent because starting it with a
no-op or permissive effect adapter would make an accepted response dishonest.

The published graphical Hub now also passed its own bounded physical visual
launch against current plan `2def...`: machine `apx-hub`, Hyprland, Wayland
socket, Waybar, and enabled internal `eDP-2` were observed, followed by tty1
restoration and zero machine/process/unit residue. A diagnostic attempt to
change D-Bus activation environment made startup unreliable and was reverted
to the previously proven runner; its portal/dconf HOME warnings are non-fatal
follow-up work, not hidden as complete. The executor socket remains blocked
only on the real activate/stop effect adapter and active-session publication.

On 2026-07-19 the first persistent graphical Hub prototype advanced beyond the
bounded visual proof but did not complete the owner-facing round trip. The
local executor-v1 service, fixed broker, Host-issued descriptors, 180-second
independent watchdog, global `entrar_no_HUB` bootstrap command, and automatic
GTK switcher launch are installed. Hyprland, Waybar, Wayland, AMD `eDP-2`, and
tty2 appear reliably. No Hub-to-`test` button transition has yet succeeded.

Physical input remains the active blocker. A fresh observation proved that
kernel `eventN` numbers changed: event10 is now the PC speaker, while the exact
internal ELAN mouse and touchpad are event8 and event9. Fixed event numbers are
not physical identities. Repository broker and bounded-test adapters now
resolve the exact i8042 keyboard and AMDI0010 ELAN mouse/touchpad udev
path/capability identities before effects, fail on absence or ambiguity, and
grant only the three resolved nodes. Their current names are passed to and
validated by the session runner. The full suite passes 834 tests with 11 skips.
Installed Host assets remain stale, so graphical launch is blocked pending
reviewed publication and an automated, recovery-bounded evdev-to-Hyprland
event-delivery proof. Another manual owner attempt is blocked until it passes.
See `docs/graphical-hub-input-handoff-2026-07-19.md`.

The owner also confirmed that this Hub is disposable test infrastructure. Once
the APX switching logic is proven, the current Hub may be replaced only under
a fresh exact instruction. The owner intends to construct a clean Arch-like
Hub and its Hyprland/Waybar/Eww/Rofi/Alacritty ricing personally, after which
APX controls will be integrated. A reviewed visual base may be extracted into
independent copies for workload Environments; the mutable live Hub must never
be used directly as their template.

The accepted shared-network boundary now includes captive-portal detection.
The Host remains the only Wi-Fi authority and classifies connectivity using
validated RFC 8910/8908 data announced through DHCPv4, DHCPv6 or IPv6 Router
Advertisements, plus a bounded HTTP fallback. It never contains or
launches a browser. Only the exact authenticated active Environment may request
the Host-selected portal URL. The current Hub implements that interaction with
a single-purpose ephemeral WebKit window: no general browser desktop entry,
profile, history or Host web stack is introduced. Portal form data and cookies
remain inside that temporary Environment process and are deleted when it
closes. This is an accepted Hub-local management dependency, not a shared
package or an exception to per-Environment package separation. Physical result
and remaining limitations are recorded in
`docs/host-wifi-captive-portal-v1-physical-result-2026-08-03.md`.

## Lenovo hardware profiles — 2026-08-04

The physical Legion 5 15ACH6H (`82JU`) exposes Lenovo Hybrid Graphics support
but no firmware iGPU-only mode. The Hub battery menu therefore exposes exactly
two GPU modes, `HÍBRIDO` and `NVIDIA`, plus immediate `SILENCIOSO`, `NORMAL`,
and `PERFORMANCE` platform profiles. The earlier APX-only AMD button was
removed. GPU changes remain Host-confirmed and require reboot.

The initial Host rejection was an activation mismatch: the live QML had the
new commands while `apx-system-power-v1` still ran its old process. The updated
daemon is now active. Because the running nspawn retained the dead file-bind
socket after service restart, the same authenticated authority also listens on
a root-owned idmapped live bridge for this Hub session; mutations still require
a direct Quickshell child and a single-use confirmation. Physical readback is
`balanced`, Hybrid Mode `1`, and iGPU-only support `0`. No GPU mode or reboot
was performed. The focused hardware, contract, launcher, and QML tests pass.

The initial profile UI was subsequently corrected to restore the complete
06:56 Quickshell baseline rather than the stale reduced source used on the
first attempt. The restored live shell retains calendar behavior, control-centre
microphone/volume controls, popup dismissal, and animations, while adding only
the Lenovo battery-menu integration and current authenticated power transport.

The complete control centre now also has target-bound brightness controls. The
screen slider writes only the exact internal `amdgpu_bl2` backlight at 5–100%
and applies continuously throttled changes without interrupting the drag; F5/F6
use the same operation. A compact keyboard-light icon before the slider cycles
the exact LED levels 0/1/2 like Fn+Space and replaces the removed full-width
status button. Its dim, cyan, and cyan-filled/white-icon appearances expose
off, intermediate, and maximum. Hardware status continues to observe both
values. Microphone mute is now confirmed from the Hub session's own PipeWire
source rather than being overwritten every second by an unavailable Host input
name. F1–F4 call Quickshell first for immediate visual feedback and then apply
the expected PipeWire controls. F10 toggles the exact ELAN
touchpad, PrintScreen saves a `grim` capture under `Pictures/Screenshots`, and
F8 remains available to the firmware/kernel RFKill mechanism. Focused tests
pass and Quickshell reloaded cleanly.
F5/F6 use a Quickshell-owned exact-input bridge because neither the brightness
keysym nor raw Hyprland bindings received this Legion's events. The bridge
opens only the already-admitted ITE and AT internal keyboards, accepts ITE
brightness codes 224/225 or the Legion F5/F6 fallback 63/64, and invokes the
same shell methods as the slider so the visible state and panel change together.

## External local-model SSD safe control — 2026-08-05

The exact Samsung model store now mounts read-only for inference, while its
unmounted Host path is root-owned mode `000`. An authenticated official-Hub
controller exposes only status, activate and confirmed safe-detach. Safe detach
was proved to stop Ollama, unmount Btrfs and close LUKS; activation restored the
same TPM-bound volume and model. The live QML has an `IA ON`/`SSD OK` button.
Its authenticated root-owned live bridge is operational in the current Hub,
while later launches use the normal leased `/run` socket binding. The popup
has independent model start/stop and SSD mount/safe-unmount buttons; manual
mount leaves the model stopped, while physical reinsertion preserves auto-start.

## Hub control-centre dismissal — 2026-08-13

Calendar, Control Centre, IA, Battery and Environments use anchored
`PopupWindow` surfaces below their invoking top-bar buttons. Clicking anywhere
outside dismisses the active menu; Escape and pressing the same top-bar button
also close it. This restores the established Hub interaction and is active in
the current Hub.

Menu keyboard access is `SUPER+A` for Control Centre, `SUPER+D` for Calendar,
`SUPER+I` for the Hub-only IA/model menu, and `SUPER+B` for Battery. Each key is
a toggle and uses the same QuickShell action as its top-bar button. The former
browser shortcut moved to `SUPER+SHIFT+B`; application launch remains
`SUPER+R`.

Host-console reattachment now has a bounded terminal-state replay in addition
to its persistent PTY. A new Kitty window is reset, receives the retained PTY
stream, and triggers a foreground resize/redraw, preventing the former mostly
black screen with only newly changed characters. Activation is deliberately
deferred until the current persistent console finishes so its Codex process is
not terminated mid-conversation.

## Environment creation interaction — 2026-08-13

The official Hub's Environment catalogue and creation form have explicit
keyboard navigation without an implicit initial focus. Opening either view
leaves every row/control unfocused; creation additionally collapses every
capability group. The first arrow key establishes focus and subsequent arrows,
Enter, Tab/Shift+Tab and Escape provide full traversal and activation. This
focus state is deliberately separate from creation values: Intermediate still
preselects the reviewed recommended capabilities by default.

Environment deletion accepts an exact duplicate destroy request only when the
recorded prior destroy for the same name and generation is complete and its
filesystem target is absent. This prevents a stale UI event from turning a
successful deletion into a visible failure without weakening generation or
registration checks for other requests.

Creation-form arrow navigation follows the visual grid: horizontal arrows
remain within the three-profile row or a two-column module row, while vertical
arrows move to the control above or below. A creation failure may leave partial
Btrfs root/home subvolumes deliberately preserved as uncertain. When a user
retries the exact name, the Host may automatically invoke the existing
journal-gated unpublished-recovery operation; it proceeds only if the target
has no registration, is not running and matches an uncertain create/restore
operation. Otherwise the existing-name refusal is retained.

Password inheritance supports both stopped UID-0 roots and a running Hub whose
on-disk ownership is shifted by `systemd-nspawn --private-users=pick`. Trust is
anchored at the Host-root-owned Environment container; the Environment root,
`etc`, and regular mode-0600 `shadow` must have one consistent root owner.
Bounded no-follow descriptors prevent path replacement while reading or
rewriting only the `apx` password field.

Physical alternate-root package installation uses pacman 7's explicit
`--disable-sandbox` downloader option because the Host `alpm` user cannot
traverse the private mode-0700 Environment directory. Package state and files
remain scoped by the Environment-specific `--root` and `--dbpath`; repository
signature verification remains enabled. This is a deliberate constrained
exception for creation-time installation, not permission for Environment
package operations to reach another root.

## Graphical Environment handoff runtime contract — 2026-08-18

The physical graphical Environment automatic-return investigation is closed.
The roughly 25-second return was not caused by Hypridle, the 120-second switch
failsafe, an explicit owner return, or Hub watchdog recovery.

The workload Hyprland itself was healthy: the expected graphical cgroup,
Hyprland IPC socket, `eDP-1` output and two keyboards were independently
observed.

The root cause was deployment drift between duplicate graphical-engine copies.
`/usr/lib/apx/apx-graphical-environment-v1.py` preferentially loads the
adjacent `/usr/lib/apx/apx-official-hub-graphical-v1.py`. That selected copy
was stale and still expected `/run/user/1000`.

The current APX graphical runtime contract is:

`SESSION_RUNTIME=/run/apx/session-1000`

The stale `/usr/lib/apx` engine was replaced with the current repository
engine. `/usr/lib`, `/var/lib` and the repository engine then matched SHA256
`3ea93c79492b9b3b6808f980e1c9dd11a9bef2c2b80fa917a77975b41a31f0d4`.

A subsequent `faculdade` graphical session remained active instead of
automatically returning to Hub.

The timer/watchdog investigation should not be reopened without new evidence.
Future hardening should prevent duplicate engine copies from silently
diverging and directly test the `/run/apx/session-1000` runtime contract.

Detailed record:
`docs/environment-handoff-runtime-readiness-fix-2026-08-18.md`.

## Host automatic timezone policy — 2026-08-18

APX now has a separate Host-only `apx-timezone-v1` service. It does not use
external geolocation, GeoClue, SSID/BSSID uploads or Environment authority.
A root-owned `0600` policy at `/var/lib/apx/timezone-v1/networks.json` maps
explicitly trusted Wi-Fi SSIDs to validated IANA timezone names.

The current physical policy maps `Casa` to `Europe/Lisbon`, verified against
the owner's current local time while preserving `NTP=yes` and
`NTPSynchronized=yes`. The earlier `America/Sao_Paulo` mapping was incorrect
for the current physical location and was replaced.

Unknown networks, absent or malformed policy, invalid timezone names and
unavailable Host evidence fail closed by retaining the current timezone.
The service owns only Host timezone selection; kernel time and NTP remain
systemd Host responsibilities. Graphical Environments inherit the Host
timezone on new launches through the separately installed
`systemd-nspawn --timezone=bind` contract.

## Graphical Environment timezone propagation — 2026-08-18

The Host remains the sole authority for kernel time, NTP and graphical-session
timezone. The production graphical nspawn command now uses
`--timezone=bind`, making `/etc/localtime` inside a running Hub or workload
follow the Host rather than relying on the Environment root's possibly stale
timezone symlink.

This does not grant workloads location, Wi-Fi or time-setting authority.
Host timezone selection is implemented through the local trusted-network
`apx-timezone-v1` policy; it does not perform geographic geolocation or send
location/network identifiers to an external service.

Repository source and both installed graphical-engine copies carry the
`--timezone=bind` contract. The already-running Hub could not have its
user-namespaced `/etc/localtime` mount rebound dynamically, so its stale link
was repaired in place and physically verified at `Europe/Lisbon`. Future
graphical sessions receive the Host timezone through `--timezone=bind`.


## Host-owned physical audio master initialization — 2026-08-18

Physical diagnosis of the shared internal analog audio path established that
Environment-local PipeWire was healthy and successfully opened the leased
ALC287 analog PCM, while the Host ALSA `Master Playback Switch` remained off.
The individual Speaker and Headphone controls reported enabled, but the HDA
speaker/headphone pins remained hardware-muted until the Host master control
was enabled.

The graphical lifecycle now establishes the physical playback prerequisite on
the Host after the exact internal audio identity is resolved and validated and
before any device lease is prepared. `ensure_audio_master_playback()` opens the
resolved Host ALSA control card through `libasound.so.2`, requires one exact
boolean `Master Playback Switch` at index 0, enables it when necessary, reads
the value back, and fails closed on missing, ambiguous, malformed, or
unverifiable state.

This does not transfer physical mixer authority to an Environment. Environments
continue to own only their local PipeWire output/input volume and mute state via
the existing audio-state handoff. No HDA verb, whole `/dev/snd` bind, package
installation, or persistent ALSA state file was introduced.

Physical diagnosis proved `pw-play` reached the leased PCM successfully and
that enabling the Host master changed the ALC287 speaker/headphone HDA amp state
from muted (`0x80`) to enabled (`0x00`).

## Trusted-network timezone correction — 2026-08-18

The current trusted `Casa` Wi-Fi mapping was corrected from
`America/Sao_Paulo` to `Europe/Lisbon` after physical observation showed that
the former mapping did not match the owner's current location. The Host remains
the sole timezone authority; the graphical Environment receives the Host
timezone through the existing `--timezone=bind` contract.

`apx-timezone-v1` still uses only the trusted local SSID mapping. No BSSID/IP
geolocation, GeoClue, external geolocation service, or Environment-side
location authority was introduced.

## Physical audio master-volume completion — 2026-08-18

The ALC287 diagnosis also exposed `Master Playback Volume` at its minimum while
Environment-local PipeWire output was at 100%. The Host-owned graphical audio
initialization now establishes both physical prerequisites before device lease:
`Master Playback Switch` enabled and `Master Playback Volume` at the hardware
maximum/neutral level. Logical user volume and mute remain Environment-local
PipeWire state.


## Live QuickShell output-volume interaction — 2026-08-18

The control-centre output-volume slider no longer waits for pointer release.
During a drag, QuickShell updates the displayed percentage immediately and
coalesces real `wpctl set-volume` writes through a dedicated serialized process
with a 45 ms debounce. Pointer release guarantees the exact final slider value
is eventually applied. This preserves Environment-local PipeWire authority and
avoids flooding the audio server with one subprocess per pointer pixel.

The owner physically confirmed working internal audio after the Host physical
Master switch/volume repair. Host and active Hub local time are also physically
aligned to `Europe/Lisbon`, and the QuickShell clock displays the correct time.

## Staged QuickShell calendar keyboard access and volume parity — 2026-08-20

The canonical Environment shell now exposes every calendar overview action to
the keyboard. Arrow keys and Tab/Shift+Tab traverse the period controls, view
selectors, dates or months, Today/New Event, and event edit/delete actions;
Enter or Space activates the focused action. Page Up/Page Down change the
displayed period and Home returns to today. The event editor starts in its title
field and includes its fields, category controls, sharing toggle, reminder
controls, Save and Cancel in the Tab focus chain. Escape leaves the editor
before a subsequent Escape closes the calendar.

The compact control-centre volume slider now uses the same immediate preview
and serialized `wpctl` path as the expanded audio slider. Both the displayed
percentage and Environment-local PipeWire volume therefore change during the
drag, while the existing newest-value coalescing prevents concurrent `wpctl`
processes. The source was installed into the active Hub on 2026-08-20 with an
exact pre-change backup under
`/var/lib/apx/backups/20260820-quickshell-calendar-volume-v1/`. QuickShell hot
reloaded it without restarting the graphical Environment, logged
`Configuration Loaded`, and its IPC then reported the calendar surface visible
at 480×390. The Hub-local PipeWire sink also remained readable after reload.

## System Environment platform checkpoint — 2026-08-23

APX now models Arch-native and Windows/Ubuntu system Environments in the Hub
creation flow. The choice is enforced end to end by the authenticated contract,
atomic management path, trusted root-owned metadata and catalogue tags. Shared
installer artifacts are verified; per-Environment disks/media/configuration
remain purgeable through the existing destroy lifecycle.

Faculdade is staged for near-native Windows presentation with group-11 RTX
VFIO, signed KVMFR, Looking Glass B7-799 and matching Windows IDD/Host tools.
The VFIO bind/restore self-test passes. The remaining proof is an owner-started
visual launch and one-time Windows tool installation. Automated graphical
handoffs are disallowed during active Codex collaboration because changing the
physical Environment interrupts the conversation.

## Native Windows catalogue and normal-create repair — 2026-08-25

The Arch partial-upgrade failure in normal Environment creation is resolved:
the added-module transaction now uses `pacman -Syu`, a disposable graphical
Environment completed and was destroyed, and the complete suite passes 1065
tests with 11 skips. Failed unpublished `faculdade` and `xasso` clones were
removed through the exact recovery contract.

The previous VM-system direction is superseded in the Hub creation flow.
Normal creation now exposes only APX Environments. A separate trusted catalogue
entry named `Windows`, tagged `NATIVO`, represents a future physical Windows
installation. It is non-deletable, reports `A PREPARAR`, and can become
openable only after a validated Windows Boot Manager exists. Its fixed executor
sets `auto-windows` only for the next boot; APX remains the permanent default.

The exact 120 GiB tail reservation is complete. A signed, one-shot maintenance
UKI shrank unmounted Btrfs, closed dm-crypt and then shortened GPT p2 while
preserving its start and UUID. The final marker is
`success:128849354240`; p2 is 382186029056 bytes, dm-crypt/Btrfs are
382169251840 bytes, Btrfs slack is zero, and the tail sectors
748556288..1000215182 were reserved. Current read/write/flush/generation error
counters are zero. The trusted storage marker is installed and the Hub
recognizes the reservation.

Because the owner has no removable USB drive, installation media is now
prepared internally without QEMU. The final 9 GiB of the reserved tail is the
FAT32 ESP `APX_WINSETUP`; the preceding exact 111 GiB remains unallocated for
Windows Setup. The Microsoft-signed Portuguese setup loader, `boot.wim`, and
three FAT32-compatible SWM parts were validated. Secure Boot retains the
original APX trust and additionally admits Microsoft's Windows/UEFI
authorities. A create-only firmware entry `APX Windows Setup` targets only p3;
it is absent from the unchanged permanent BootOrder and no BootNext is armed.
The fixed reboot script revalidates hardware, power, GPT, media digests,
signature and UEFI identity before setting that entry for one boot only.
Windows remains `A PREPARAR` until installation creates and APX validates the
real Windows Boot Manager. The complete repository suite passes 1076 tests
with 11 expected skips. See
`docs/native-windows-physical-120gib-v1-2026-08-25.md`.

The first installer boots reached Windows Setup but its hardware-selection
stage requested a driver. All exits preserved the exact GPT and filesystems.
The diagnostic WinPE boot then proved that DiskPart sees Disk 0 at 476 GB with
111 GB free. `drvload X:\Windows\INF\stornvme.inf` returned `0x80070103`
because the matching Microsoft NVMe driver was already active; the subsequent
multimedia-driver message was Setup's generic missing-source-media failure.

The internal installer ESP could boot WinPE but was not assigned a drive
letter after WinPE started, so Setup lost access to its three SWM source parts.
The first custom WinPE attempt used DiskPart `assign`; physical boot entered
its recovery console because Windows refuses drive-letter assignment to GPT
partitions other than basic-data partitions. Closing that console returned to
APX and preserved GPT and all filesystems.

The corrected Setup index uses `winpeshl.ini` to run `wpeinit`, scan existing
drive letters and, when necessary, invoke the EFI-specific `mountvol W: /S`.
It launches Setup only after verifying `setup.exe` and all three SWMs. It uses
no DiskPart and contains no clean, create, delete, type-change or format
action. The deployed WIM passed complete integrity, metadata and file-data
verification; its embedded files match the repository sources byte for byte
and its SHA-256 is
`b4041a17b34aca0db72e32eb1bcd7d675354f600d4b79efb2ab4a8af8dcb5df2`.
The fixed one-shot boot validator admits that exact digest. GPT, the 111-GiB
hole and permanent BootOrder remain unchanged; no BootNext is armed. The
complete repository suite now passes 1076 tests with 11 expected skips.

Windows Setup subsequently completed image application and reached OOBE using
only the reserved tail. It created a 16-MiB MSR, 110.2-GiB NTFS Windows volume
and 790-MiB recovery partition before the existing 9-GiB internal ESP, now p6.
APX p1/p2 remain unchanged. Windows Boot Manager is Microsoft-signed and
firmware entry 0006 targets p6. Permanent BootOrder is explicitly
`0005,0006,0000,2001,2002,2003`, with Linux first; no BootNext is armed.

OOBE lacked the exact Realtek RTL8852AE driver. APX fetched official Lenovo
Windows 11 package DS551503, verified published package SHA-256
`1defff5645c18427c5f1af5af07a0ebae1dde25c70c3624869d485cef06f0c04`,
extracted only the Realtek 6001.0.10.340 set and proved its INF contains
`PCI\VEN_10EC&DEV_8852&SUBSYS_485217AA`. Its PKCS#7 catalogue names Microsoft
Windows Hardware Compatibility Publisher. The four required files are staged
and post-write hash-verified at `C:\APX\Drivers\Realtek8852AE`; no Windows
system file was replaced. The protected OOBE runner validates firmware, GPT,
Windows/ESP identities, Boot Manager/BCD and the staged driver before arming
only Windows entry 0006 for one boot. The complete suite passes 1078 tests with
11 expected skips.

The first OOBE continuation loaded the staged Lenovo driver successfully: the
offline Windows DriverStore now contains `netrtwlane6.inf` with the exact
RTL8852AE Lenovo hardware ID. OOBE then performed a normal restart and returned
to APX because Linux is intentionally first in permanent BootOrder. The signed
Windows Boot Manager digest is unchanged; BCD changed at that restart as
expected. The OOBE handoff now treats BCD as mutable bounded state, records its
current digest per attempt and provides 32 non-overwriting evidence slots while
still setting only BootNext 0006. No BootNext is currently armed.

## Native Windows ready and repeatable lifecycle — 2026-08-25

The physical Windows installation is complete and usable. The installed
`Windows · NATIVO` catalog entry is schema v2/ready and the native boot runner
now validates the exact NVMe/GPT/partition identities, the Microsoft Secure
Boot signature of the mutable Windows Boot Manager, bounded BCD state and the
Linux-first firmware invariant before setting only Windows BootNext 0006. The
permanent order is `0005,0006,0000,2001,2002,2003`; no BootNext is armed.

The Windows partition contains the APX return helper in ProgramData/Common
Startup plus a Public Desktop fallback. It reserves `SUPER+E` through the
built-in Windows hotkey API and performs a normal restart; Linux-first firmware
then returns to the HUB. `SUPER+SHIFT+E` is the first-sign-in fallback while
Explorer reloads its disabled-hotkey policy.

The HUB can now request one physical `windows-native` Environment at fixed 80,
120 or 160 GiB sizes (120 default). Creation and deletion are implemented as
signed one-action offline UKIs. Create shrinks Btrfs, closes dm-crypt, shrinks
p2, creates the exact Windows layout and prepares internal install media with
the Lenovo RTL8852AE driver and APX return helper. Delete admits only the exact
p3-p6 layout, discards only those ranges, deletes only those partitions and
grows p2; the installed finalizer then grows dm-crypt and Btrfs. Policy retains
at least 256 GiB for APX and permits only one native Windows instance.

The lifecycle service, finalizer, policy, shell UI and switch service are
installed. The current boot validator passes, firmware is unchanged and the
full suite passes 1087 tests with 11 expected skips. The destructive lifecycle
has been tested against a disposable GPT image but has intentionally not yet
deleted/recreated the working physical Windows installation; that remains the
first real-device acceptance test.

The owner changed the Hub `apx` password interactively. The root-only
synchronizer then copied only its admitted password hash into four registered,
stopped graphical Environments and, at the owner's explicit request, Host
`root`. Replacement is atomic and each original `shadow` is backed up mode
0600. Equality was verified without displaying any hash; Host and Hub now
accept the same password.

Opening the Lenovo camera e-shutter exposed the exact SunplusIT capture device
`5986:212b` at stable path `pci-0000:05:00.3-usb-0:3:1.0`. The official Hub
launcher now resolves that full udev identity and leases only its one V4L
capture node, never the metadata node or the USB controller. OpenCV proved a
real 640x480 frame inside the Hub after relaunch.

The Hub has pinned native-PAM Howdy 3 beta commit
`d3ab99382f88f043d15f15c1450ab69433892a1c` and CPU-only Python dlib 20.0.1;
the reproducible PKGBUILDs and exact PAM templates live in `config/howdy-v1`.
Five local face encodings are present (one legacy and four current), successful
and failed snapshots are disabled, remote SSH authentication is disabled, and `workaround=off`
avoids the unstable native prompt workaround. The original root-only mode 0600
was incompatible with unprivileged `hyprlock`: its Howdy child failed with
`PermissionError` before recognition. On 2026-08-31 the live model and config
were corrected to `root:apx` mode 0640, retaining user read-only access, and
the recognition window was increased from four to eight seconds. A direct
comparison as `apx` now reaches normal camera scanning instead of error 1.
After the owner opened the physical e-shutter, all 30 sampled frames contained
a face, but the old model's best score was 6.210 against the retained safe 3.5
limit. The limit was not weakened. The owner used the requested separate-
terminal Howdy flow to enroll four current views; their measured scores were
2.631–3.116. The official comparison returned success, a real cold `sudo`
authenticated without a password, and a real Hyprlock cycle logged
`Identified face as apx`, unlocked and exited zero. Both PAM services retain
their original `system-auth`/`login` password stack immediately after the
sufficient Howdy module. The original PAM/config/model rollback is
`/var/lib/apx/backups/20260825T171900Z-face-auth-pam-v1`; the immediate pre-fix
state is `/var/lib/apx/backups/20260831-face-auth-readability-v2`; the accepted
working state is `/var/lib/apx/backups/20260831-face-auth-working-v2`.

The first owner attempt to open the ready native Windows entry exposed a menu
readiness defect rather than a Windows failure. The sandboxed Environment
switch service has an empty capability bounding set, while its catalogue path
was invoking the full native validator, whose read-only filesystem mounts
require `CAP_SYS_ADMIN`. The validator passed on the Host but necessarily
failed inside the menu service, so the catalogue rewrote the trusted `ready`
record as `preparing` and QuickShell disabled the row before any `native.boot`
request was sent. The catalogue now presents the state from the already
strictly validated, root-owned mode-0400 native marker. On click, the separate
privileged one-shot runner still repeats the full NVMe/GPT/UEFI/signature/
Windows validation before setting BootNext and rebooting. The menu service
retains no mount capability. The live catalogue now reports Windows `ready`,
the physical validator passes, no BootNext is armed, and all 1087 tests pass
with 11 expected skips. Rollback is
`/var/lib/apx/backups/20260825T173000Z-native-windows-menu-ready-v1`.

The owner then physically proved both directions: opening `Windows · NATIVO`
from the Hub reached the installed physical Windows, and the Windows return
action rebooted into the Linux-first Hub. Return v2 removes the Public Desktop
`REGRESSAR AO APX.cmd` icon entirely. The Common Startup entry now runs a
hidden supervising VBS loop that keeps the PowerShell keyboard-hook message
listener alive and retries after bounded two-second delays if neither hotkey
can yet be registered. `SUPER+E` is primary and `SUPER+SHIFT+E` remains the
first-sign-in fallback while Explorer reloads `DisabledHotkeys`.

Future native-Windows creation embeds the official Lenovo RTL8852AE package in
both WinPE and the installed image. A `SetupComplete.cmd` running as Windows
Setup invokes signed `pnputil /add-driver ... /install` without owner action.
Before publishing a new Windows generation as `ready`, the finalizer now
requires the exact root-copied background return assets, absence of the old
Desktop icon, and a bounded DriverStore INF containing the exact Lenovo
`PCI\VEN_10EC&DEV_8852&SUBSYS_485217AA` identity. The normal Windows Update
path then supplies current AMD/NVIDIA, audio, Bluetooth, camera and Lenovo
drivers for the same physical hardware; no applications or owner files are
copied. The physical boot validator enforces the same return/Wi-Fi invariants
on every later open. Current Windows passes; no BootNext is armed, no unit is
failed, and all 1087 tests pass with 11 expected skips. Rollbacks are
`/var/lib/apx/backups/20260825-native-windows-return-v2` and
`/var/lib/apx/backups/20260825T181500Z-windows-repeatable-drivers-return-v2`.

## Environment title and description editing — 2026-08-25

The live Hub Environment menu now has a selected-row `EDITAR` action and an
`F2` keyboard path. Its bounded form edits the visible title (1–64 characters)
and optional description (0–120 characters); the logical Environment name,
generation, role, release and storage identity are explicitly unchanged.

The wire contract exposes only `environment.update-metadata`, bound to target,
generation, title and description. Admission still requires the active official
Hub QuickShell and an idle lifecycle. A fixed root-owned transient runner then
revalidates the exact stopped ordinary registration or ready native-Windows
marker and atomically replaces only those two fields. It has no capabilities
and write access only to the ordinary/native metadata parents. Native-Windows
catalogue and boot validation now treat bounded presentation strings as mutable
while continuing to enforce all physical and firmware identities.

The live Hub and future shell seed match source and QuickShell hot reload logged
`Configuration Loaded`. A same-value protected write against `faculdade`
exercised the real transient runner without changing its visible presentation.
All 1088 tests pass with 11 expected skips; the Windows physical validator
passes, BootNext is absent and no unit is failed. The owner still needs to
exercise one chosen edit through the visible button. Backups are
`/var/lib/apx/backups/20260825T184910Z-environment-metadata-edit-v1` and
`/var/lib/apx/backups/20260825T185053Z-environment-metadata-edit-v1`.

## Native Windows physical-delete preflight correction — 2026-08-25

The first owner-authorized physical delete attempt was safely rejected before
any storage or boot mutation. The installed lifecycle process inherited `/` as
its current directory, while the signed maintenance-image builder requires the
exact repository root. Its fail-closed check therefore reported `repository
differs`; no pending state, maintenance image, BootNext or GPT write survived.
The existing Windows installation remains complete and ready.

The fixed lifecycle runner now supplies
`/root/apx-host-development-mode-v1/apx` explicitly as the working directory
for its bounded subprocesses. Tests assert this invariant, the live runner is
source-exact, and its read-only host/delete validation passes for the current
120-GiB generation. The full suite passes 1089 tests with 11 expected skips.
The destructive real-device acceptance test remains pending an explicit owner
retry from the Hub. Rollback is
`/var/lib/apx/backups/20260825T222335Z-native-windows-lifecycle-cwd-fix-v1`.

## Native Windows initrd partition-type probe correction — 2026-08-26

The first signed-UKI physical delete boot refused safely at its initial GPT
partition-type gate. No discard, mapping close, GPT write or resize had begun.
The cause was a util-linux 2.42.2 interface detail: partition-entry metadata is
not returned by the cached `blkid -s PART_ENTRY_TYPE` form on this Host, while
`blkid -p -s PART_ENTRY_TYPE` returns each exact GPT type.

The offline executor now uses direct probing for MSR, Windows basic-data,
Recovery and Windows ESP. Recovery cleared only the exact failed lifecycle
artifacts after validating the complete unchanged physical layout. The corrected
UKI was subsequently built, Secure-Boot verified, extracted and inspected; its
embedded executor contains all four corrected probes. No BootNext or test image
remains. The 1089-test suite passes with 11 expected skips. The Windows remains
intact and `ready`; physical deletion still requires a new owner confirmation.
Recovery backup:
`/var/lib/apx/backups/20260826T143302Z-native-windows-msr-probe-refusal-v1`.

## Native Windows physical deletion accepted — 2026-08-26

The owner-authorized delete completed on the real NVMe. The signed offline UKI
discarded only the admitted Windows p3-p6 ranges, deleted those four partitions
and expanded APX p2 to 511035383296 bytes. On normal Linux boot, dm-crypt
automatically reopened against the full partition at 511018606080 bytes.

The first finalizer invocation exposed one final noninteractive mismatch:
calling `cryptsetup resize` after the mapping was already full attempted to read
authentication from a service with no input. The finalizer now validates the
exact full mapping instead, and uses device-explicit `btrfs filesystem resize
1:max`. Btrfs occupies the aligned maximum 511018602496 bytes with only 3584
bytes alignment slack and about 450096533504 bytes currently available.

Finalization succeeded and removed every Windows native/pending/storage marker,
maintenance artifact and Windows/APX Setup UEFI entry. Only p1 APX EFI and p2
APX CRYPT remain; permanent BootOrder begins with Linux 0005, BootNext is absent,
and no unit is failed. The catalog no longer has a Windows record. This accepts
real-device deletion and full APX space recovery. Recreating a new native
Windows from the Hub remains the next physical acceptance test. The 1089 tests
pass with 11 expected skips. Backup:
`/var/lib/apx/backups/20260826T144156Z-native-windows-delete-finalize-v1`.

## Self-contained repeatable native Windows lifecycle — 2026-08-26

Native Windows create/delete no longer has a runtime dependency on the mutable
development repository. Reviewed root-owned assets are installed below
`/usr/share/apx/native-windows-lifecycle-v1`, while the bounded builder,
installer preparation, lifecycle runner and finalizer execute from
`/usr/lib/apx`. Repository tests run at deployment, not during owner actions.

Persistent stages make reboot recovery explicit. Delete transitions from
`maintenance` to `finalizing` before idempotent post-boot work and removes its
pending marker last. Create transitions through `preparing-installer` and
`installing`; the prepared-media marker makes preparation reentrant, while an
exact firmware/partition validator resumes APX Setup or Windows Boot Manager
for a maximum of eight restarts. The boot finalizer retries transient failures
three times and the Hub holds lifecycle management busy while a nonfailed
native operation remains pending.

The installed create builder was exercised with `/` as its working directory,
successfully built a Secure-Boot-signed 120-GiB create UKI, and the extracted
executor and initrd unit matched their installed stable assets. The proof image
was removed without BootNext or any GPT write. The full 1089-test suite passes
with 11 expected skips. Real create/install acceptance is still intentionally
pending the owner's next menu action. Rollback:
`/var/lib/apx/backups/20260826T145246Z-self-contained-native-windows-lifecycle-v1`.

## Explicit WinPE installation contract and clean recovery — 2026-08-26

The first recreated Windows generation reached WinPE and applied a real
Windows image, but the old automatic flow still assumed historical partition
numbers and never proved the final BCD/UEFI chain. It left an incomplete OOBE
Windows partition plus `APXWINSETUP`, while the Hub had no trustworthy native
record. The generation was therefore treated as orphaned, not published as an
Environment.

After exact read-only identification, a one-time signed cleanup removed only
those two admitted partitions and the corresponding Microsoft/APX Setup boot
artifacts. APX p2 was expanded back to 511035383296 bytes, dm-crypt reopened at
511018606080 bytes and Btrfs occupies 511018602496 bytes. The disk now contains
only p1 `APX_EFI` and p2 `APX_CRYPT`; no Windows metadata, pending operation,
`BootNext`, Microsoft EFI tree or Windows UEFI entry remains. Estimated Btrfs
free space is 449429082112 bytes.

The replacement create layout is deliberately smaller and identity-bound:
p3 is the requested NTFS `APXWINTARGET`, p4 is the 9-GiB FAT32
`APXWINSETUP`, and the existing p1 `APX_EFI` remains the only ESP. WinPE reads
an embedded generation contract, discovers the physical disk by GPT GUID and
the three partitions by GPT type, PARTUUID, label and size, then assigns its
own temporary drive letters. It validates all split SWM parts and Windows 11
Pro index 6 before formatting only authenticated p3. It applies the image with
DISM `/SWMFile`, stages the APX return/Wi-Fi assets, runs BCDBoot against the
authenticated p1 ESP, and proves `bootmgfw.efi`, BCD, device/osdevice and
`winload.efi` before allowing a reboot. `APXWINSETUP` is retained until a real
user profile and the required return/driver assets prove first-boot completion.

Maintenance no longer selects a visible systemd-boot entry. The lifecycle
runner creates a temporary direct UEFI entry with `efibootmgr --create-only`,
proves that permanent `BootOrder` did not change, removes the menu entry file,
and uses the direct entry only through `BootNext`. The Linux-first permanent
order is unchanged even before reboot; the finalizer deletes the temporary
UEFI entry and signed UKI after return. This prevents the owner from being
dropped into the technical menu containing Windows and multiple APX recovery
choices during create/delete maintenance.

Source and installed lifecycle executors match. The focused 19-test native
storage suite and the complete 1089-test suite pass, with 11 expected skips.
No new Windows creation or reboot was armed. Latest rollback:
`/var/lib/apx/backups/20260826T161719Z-native-windows-explicit-winpe-v2`.

## WinPE optional-tool failure and repository recovery candidate — 2026-08-26

The owner-started 160-GiB physical recreation reached the custom WinPE but
returned to APX before formatting. Read-only inspection proved the new p3 NTFS
`APXWINTARGET` still contains only its 647-byte authenticated contract; p4
`APXWINSETUP` retains the verified `boot.wim`, all three split SWMs and the
same contract as p3 and p1. There is no Microsoft EFI tree, BCD, Windows Boot
Manager entry or `BootNext`. APX p1/p2 and permanent Linux-first `BootOrder`
are unchanged.

The immediate cause is that the embedded command used `findstr`, which is not
present in this WinPE image. Because the first use occurred while locating the
GPT disk, the setup volume was not yet mounted and no persistent WinPE status
could be written. A separate finalizer defect then treated the intentionally
absent `Users` directory as an exceptional filesystem error and exhausted its
three service retries instead of selecting the still-valid APX Setup entry.

The repository candidate removes every `findstr` dependency and searches
captured DiskPart/DISM/BCD output using only built-in `cmd.exe` parsing. It
requires the exact GPT disk and its reported size, exactly one matching GPT
type/label/expected-size partition for each role, three byte-preserved contract
copies, a second disk/target identity check immediately before the only
admitted NTFS format, and a free temporary letter chosen per role. It applies
index 6 with the split-SWM wildcard, then verifies `winload.efi`, the registry
hive, `bootmgfw.efi`, the BCD loader device/osdevice/path, firmware Boot
Manager path and preservation of both APX EFI and setup media before writing
`boot-prepared`.

The finalizer now returns an incomplete result when `Users` is absent. The
menu service keeps a native operation busy for as long as its trusted pending
marker exists, even if the visible phase is `failed`, preventing an overlapping
create/delete request. Exact prepare and explicit-resume adapters are staged in
the repository. Prepare atomically replaces only p4 `boot.wim`, installs the
matching fixed assets and does not reboot or arm `BootNext`; resume independently
revalidates the unchanged GPT, pristine target, repaired WIM and APX Setup UEFI
entry before starting the existing finalizer. Neither adapter has been run on
the Host. The current failed service and physical media therefore remain
untouched pending an explicit deployment decision.

Shell/Python syntax, diff whitespace, the focused native-Windows tests and the
complete repository suite pass: 1090 tests with 11 expected skips.
An isolated read-only-media rehearsal rebuilt a temporary WIM, passed full
WIM metadata/file-data verification and extracted a command byte-identical to
the candidate while preserving the exact embedded contract. The temporary
copy and mounts were removed; physical p4 was not written.

## Menu-owned native Windows failure lifecycle — 2026-08-26

The supported owner workflow is now defined as menu-only: create, observe,
retry, open and delete native Windows through Hub Environments. A failed
creation may no longer remain as an invisible durable lock that requires an
owner to run a repository adapter. The authenticated management status exposes
only the pending generation and selected size when a root-owned create marker
is at `installing` and the visible operation is failed. The menu then presents
`RETOMAR WINDOWS` and a two-click `APAGAR INCOMPLETO` action.

Both actions cross the same official-Hub/QuickShell peer boundary as ordinary
Environment management and are bound to the exact pending generation. Retry
does not format or partition from Linux. It validates the fixed disk, p1-p4
geometry, GPT identities, labels, three identical install contracts, prepared
marker, setup firmware path and the three split SWMs. It rebuilds a copy of
only p4 `boot.wim`, verifies all WIM data and required WinPE executables, then
publishes it atomically with rollback. Only after that separate step succeeds
does the existing finalizer select authenticated APX Setup once; WinPE remains
the sole component permitted to reformat the already reserved p3 target.

Discard converts only the same incomplete create marker into a bounded delete
after building and authenticating the signed offline lifecycle image. It uses
a temporary direct UEFI entry and BootNext without changing permanent
BootOrder. Failure before a successful reboot restores the original pending
create marker and removes the temporary boot artifacts. The existing delete
finalizer then removes p3/p4, Microsoft/APX Setup boot artifacts, grows APX and
removes the pending marker last. Deleting a completed ready Windows continues
to use the existing `APAGAR` action in the same menu. If the offline discard
itself refuses before completing, the failed delete marker exposes only
`TENTAR APAGAR`; it never offers to resume an installation already committed
to deletion.

Repository deployment for the current failed physical generation is staged as
a code/UI-only, non-rebooting rollout. It stops the exhausted finalizer and
installs the fixed menu/runtime assets, but explicitly does not mount or write
p3/p4, arm BootNext, start a recovery or reboot. That rollout has not been run;
the physical Host and current installer media therefore remain unchanged. The
complete repository suite passes 1095 tests with 11 expected skips.

The owner subsequently authorized that bounded rollout. Its first attempt
refused before mutation because AC was offline; with AC online and 76% battery,
the second attempt installed the exact source UI, contract, service, finalizer,
retry and discard executors. QuickShell logged `Reloading configuration` and
`Configuration Loaded`. The switch service is active, the exhausted finalizer
remains failed/stopped, and the pending 160-GiB create remains at `installing`.
There is still no BootNext and neither p3 nor p4 is mounted. No installer-media,
GPT or filesystem change occurred. Rollback:
`/var/lib/apx/backups/20260826T182015Z-native-windows-menu-recovery-v1`.
The owner-visible two-click `APAGAR INCOMPLETO` confirmation is now the only
remaining step before offline cleanup; it has not been accepted yet.

The first visible discard click was rejected before reaching the Host service.
Read-only postflight proved no transient recovery unit, no BootNext, no
maintenance UKI, no pending-marker change and no partition change. The live
Hub nspawn instance still sees the pre-rollout client through its long-lived
read-only bind mount: its inode/digest differs from both the new installed
client and repository source, even though QuickShell already hot-reloaded the
new QML. A controlled Hub relaunch is required to recreate that bind with the
new client.

The owner approved that controlled relaunch and the official authenticated
handoff completed at 19:25 WEST without rebooting the computer. The replacement
Hub is running under nspawn with a new QuickShell process. SHA-256 for the
repository, installed Host and live container copies of the environment-switch
client is identically
`bc2cf6f2099f1326d862bd3dd6bdfbf953a1740d95f3afa513dea50333bba482`;
the live client contains both `native-discard` and `native-retry`. The contract
is also source-exact in all three locations. Postflight still shows the same
160-GiB `create/installing` generation, no BootNext, no management/handoff
lock, no p3/p4 mount and unchanged p1-p4 geometry. The relaunch therefore
fixed only the stale client bind and did not start recovery or alter disk or
firmware state. The menu discard may now be retried by the owner.

The owner retried and confirmed `APAGAR INCOMPLETO` from Environments. The
Host accepted `native.discard` for the exact pending generation and the signed
offline lifecycle completed successfully. Management now reports
`native-delete/complete`, `busy: false` and “Windows apagado; todo o espaço
regressou ao APX.” The native catalogue and pending directory contain no
Windows entry or marker. Physical p3 and p4 are gone; p2 is again a 475.9-GiB
APX LUKS partition, with p1 remaining the 1-GiB APX EFI partition. BootNext is
absent, no Windows/APX Setup/maintenance loader entry remains, no recovery or
management lock is held and the environment switch service is active. The two
`windows-storage-*.status` files under the APX recovery directory predate this
operation (2026-08-25) and are inert historical status records, not boot
entries. The menu is therefore idle and ready for a new native-Windows create.

## Estado atual — incidente Windows fail-closed de 2026-08-30

Uma criação posterior de 160 GiB, geração
`18fe09c4-ed14-40a3-96d2-544d3ba3e628`, revelou duas falhas encadeadas. O
batch WinPE LF-only não conseguiu despachar o label `:file_contains` depois de
formatar exclusivamente p3 e parou com `APX-FORMAT-04`; depois, a ausência de
status foi interpretada pelo finalizador como autorização para rearmar Setup e
reiniciar até 12 vezes. O ficheiro chegou a `resume_attempts=11` e provocou o
ciclo de boot recuperado manualmente.

O estado anterior deste documento fica assim ultrapassado. O finalizador
instalado é agora fail-closed: não contém BootNext/reboot, não tem `Restart=` e
transforma erro WinPE autenticado em `failed`, ou evidência ausente/ambígua em
`recovery-required`. O pending isolado nunca autoriza boot. Retomas só existem
por confirmação explícita, usam `explicit_attempts` separado e têm limite 2.
O batch usa `find.exe` disponível, é CRLF, preserva logs e publica falhas em p4
e p1. O incidente exato tem teste de regressão sem reboot/BootNext.

O sistema físico está Linux-first, sem BootNext e com o finalizador concluído
com sucesso. p3 contém apenas o contrato APX, sem Windows/winload/registry;
p4 contém um BCD de Windows Setup, não de Windows instalado; p1 não contém EFI
Microsoft e não há Windows Boot Manager. A correção requer nova aplicação da
imagem sobre p3 autenticada, não reparação BCD. O pending atual fica em
`recovery-required`, com a evidência `.recovery-20260830` intacta. O suporte só
pode ser reconstruído e arrancado numa ação explícita, com AC ligado.

Detalhes e runbook: `docs/native-windows-fail-closed-v2-2026-08-30.md`.
Auditoria de configuração: `docs/apx-system-state-audit-2026-08-30.md`.

## Retoma explícita da segunda tentativa pelo Hub — 2026-08-30

O segundo arranque físico terminou corretamente em `failed` com
`APX-PART-03`, depois de provar que o DiskPart truncava o label de 12
caracteres de p3 na apresentação tabular. A correção preserva a autenticação
forte de p3 e melhora os diagnósticos persistentes; está descrita em
`docs/native-windows-second-physical-attempt-postmortem-2026-08-30.md`.

Foi encontrada uma lacuna separada no menu: `failed` era aceite como estado
terminal e descartável, mas não como origem de uma nova tentativa explícita.
O Hub passa a oferecer `RETOMAR WINDOWS` também para uma criação autenticada
em `failed`, desde que não exista lock e `explicit_attempts < 2`. O clique
continua a ser a única autorização: até lá não reconstrói p4, não arma
BootNext e não reinicia. Ao clicar, o executor revalida o Host, energia,
firmware e estado, reconstrói/verifica p4 a partir do WinPE corrigido e só
então arma uma única entrada Setup. A falha histórica permanece arquivada; os
campos ativos de falha só são retirados quando essa nova tentativa foi
explicitamente aceite.

## Continuação segura do primeiro arranque Windows — 2026-08-30

Duas gerações físicas sucessivas provaram o mesmo resultado: WinPE aplicou o
Windows e `bcdboot` com sucesso; o primeiro boot iniciou serviços OOBE,
concluiu a fase 4 com código `0` e pediu explicitamente reboot antes do OOBE.
O BootNext único foi consumido e o BootOrder Linux-first recuperou o Hub, como
desenhado. Não houve crash Windows.

O limite anterior misturava duas operações diferentes. As duas tentativas
WinPE continuam limitadas a duas, mas `boot-prepared` passa a usar um contador
separado de até oito continuações manuais. Cada continuação autentica a
geração, p3, status espelhado e Windows Boot Manager, arma um BootNext único e
nunca reconstrói o instalador. O Hub apresenta `PROSSEGUIR WINDOWS` nesta fase.
Detalhes: `docs/native-windows-first-boot-continuation-2026-08-30.md`.

A execução física posterior consumiu quatro continuações porque o OOBE
instalou uma atualização ZDP e pediu reinício. O limite de quatro ocultou o
botão apesar de não existir falha de boot. O orçamento manual passou para oito,
sem retry automático; o limite WinPE continua em dois. O `SetupComplete.cmd`
também passou a reconhecer idempotentemente o driver Realtek já instalado,
confirmando o INF através de uma segunda enumeração antes de aceitar o aviso.

Após a conclusão física, `windows.json` ficou `ready` e o perfil `andre` foi
observado em p3. A integração pós-instalação troca a reserva frágil de WIN+E
por um hook `WH_KEYBOARD_LL`, com diagnóstico em
`%LOCALAPPDATA%\APX\ReturnToHub.log`; só a tecla explícita pede reboot e o
BootOrder Linux-first permanece inalterado. O rádio Bluetooth Realtek
`USB\VID_0BDA&PID_4852` já tinha recebido com sucesso o pacote WHQL
1.9.1046.3002 e reiniciado, pelo que não se força outro driver. A descrição do
cartão Windows foi reduzida para `Windows 11 · 160 GiB`. Ver
`docs/native-windows-post-install-integration-2026-08-30.md`.

O rollout físico do helper v2 está deliberadamente pendente: `ntfs3` recusou
p3 read-write por dirty bit, enquanto `ntfsfix -n` confirmou as estruturas
principais. Nenhum `force`/reparo Linux foi aplicado e p3 não foi escrita. O
boot runner live conserva os hashes v1 para manter Windows acessível até um
`chkdsk C: /scan` seguido de reinício limpo pelo próprio Windows.

O primeiro `native.boot` após `ready` expôs ainda uma gate incompatível:
Secure Boot esteve desativado em todos os boots físicos, embora o firmware
permaneça em User Mode com chaves e binários assinados. O executor passa a
admitir `SecureBoot=0, SetupMode=0`, exigindo em simultâneo assinatura APX do
Linux manager e Microsoft do Windows manager. Setup Mode ou relatório
incoerente continuam recusados. A transição aceita somente os payloads v1/v2
completos conhecidos. O `--validate-only` físico passou sem armar BootNext.

O arranque seguinte chegou ao Windows e regressou ao Linux com BootOrder
inalterado e sem BootNext. Foi corrigida uma corrida apenas observacional: o
HUB esperava pela ativação de uma unidade que iniciava imediatamente o reboot
e acabava por reportar falsamente que o executor não arrancara; a submissão da
unidade transitória usa agora `systemd-run --no-block`.

A publicação física do helper SUPER+E v2 não foi realizada: `ntfs3` recusou o
mount RW antes de escrever porque p3 continua dirty/scheduled-for-check.
`ntfsinfo` confirmou o flag, embora `ntfsfix -n` tenha considerado MFT,
MFTMirr e boot sector íntegros. O instalador foi atualizado para autenticar a
p3/ESP/layout atuais e exigir ambos os diagnósticos. Não foi usado `force`.

Depois do primeiro AutoChk, `ntfsinfo` deixou de falhar por scheduled check,
mas continuou a reportar `Restart state: DIRTY` e unclean filesystem com exit
zero. O preflight passa a rejeitar também essas frases, impedindo que um exit
code enganador chegue sequer à tentativa de mount RW. Falta uma segunda entrada
no Windows seguida de Restart normal; p3 permanece sem o helper v2.

A segunda passagem deixou p3 limpa (`Volume Flags 0x0000`, restart CLEAN).
O helper SUPER+E v2 foi publicado e verificado read-only; os hashes instalados
coincidem com o executor, o atalho legado continua ausente e o backup físico é
`/var/lib/apx/backups/20260831-native-windows-return-v2.M9sjPC`. A p3 terminou
desmontada, o `--validate-only` passou, não existe BootNext e Linux permanece
primeiro no BootOrder. O próximo arranque Windows serve apenas para validar o
hook global e o log `%LOCALAPPDATA%\APX\ReturnToHub.log`.

## Hub connectivity and Fn repair staged physical result — 2026-08-31

The owner-reported Wi-Fi-password, Bluetooth and Lenovo Fn failures were
reproduced at their actual boundaries. The credential stdin/socket path is
intact and secret-safe; the candidate now requires iwd to re-observe the exact
requested SSID before accepting a connection and returns bounded Portuguese
errors for a missing prompt or rejected authentication. Bluetooth was
physically `off-blocked`: power-on now unblocks only the Bluetooth rfkill class
before BlueZ and verifies the resulting powered state. This adds only
`CAP_NET_ADMIN` to the already Host-only v3 service.

The Fn bridge was not running because it required the stale diagnostic name
`AT Raw Set 2 keyboard`; the leased physical node is exactly
`AT Translated Set 2 keyboard`. The fixed-name bridge continues to admit only
the separate i8042 and ITE devices, without uinput or exclusive grabs. The
repository passes 1118 tests with 11 expected skips. Architecture, rollout
limits and physical acceptance are in
`docs/host-connectivity-and-fn-repair-v1-2026-08-31.md`.

The repaired files are physically staged with exact backup at
`/var/lib/apx/backups/20260831T134617Z-host-connectivity-input-v1`. QuickShell
restarted without ending the Hub, and the Fn bridge remains live. The exact
menu client powered Bluetooth off and on and completed an eight-second scan of
15 unpaired devices; no pairing/trust mutation occurred. `Casa` remained fully
connected and no unit failed. The daemon process still predates the staged
file because restarting its inode-bound socket requires a coordinated Hub
relaunch. Bluetooth works in the current session after its bounded rfkill
unblock; the new general Bluetooth and Wi-Fi confirmation paths activate on
the next normal boot or owner-approved relaunch.

## Fn row requires Fn — physical correction — 2026-08-31

The owner's follow-up showed brightness acting on plain F5/F6. The bridge had
admitted brightness aliases from the ordinary AT keyboard, while Hyprland also
kept direct Fn-row `XF86` and F13--F16 bindings. The exact internal ITE device
is now the sole Fn-row authority; ordinary AT F1--F12/media/brightness events
are ignored except for Print Screen, and all parallel compositor mappings for
the Lenovo row were removed. No device is exclusively grabbed.

An old orphan bridge discovered during reload is also closed: a runtime lock
allows one instance, and deployment stops the exact prior process before the
supervised QuickShell restart. The live state has exactly one bridge, zero
alternate Fn-row bindings, matching source/installed/seed/live hashes and no
failed unit. The current rollback set is
`/var/lib/apx/backups/20260831T140531Z-host-connectivity-input-v1`. The full
suite passes 1118 tests with 11 expected skips. Owner confirmation of plain
F1--F12 versus Fn+F1--F12 remains pending.

## Superseding Fn route and graphical desktop integration — 2026-08-31

The later complete-row observation supersedes the earlier claim that the ITE
device was Fn-only: it is a full keyboard and also emits ordinary F1--F12. The
bridge now ignores all raw F codes, accepts only semantic ITE brightness
224/225 and exact AT Print Screen, while Hyprland handles the semantic XF86 and
observed F13--F16 Fn outputs. Firmware `fn_lock=0`; Fn+F8 remains Host-kernel
rfkill. Exactly one bridge is live. Physical plain-F versus Fn acceptance is
still owner-observed.

All graphical Environments and the shared seed now have three project-owned
landscape wallpapers rotating every 15 minutes. `SUPER+F` toggles fullscreen;
`SUPER+P` opens the file manager only outside the Hub. Thunar was removed from
the Hub and retained in the workload roots. The Central de Controlo is
text-oriented; its keyboard action now shows only `TECLADO`, with no icon,
ON/OFF marker or intensity, and the Host terminal label no longer includes
`sessão única`. The immediate recovery set is
`/var/lib/apx/backups/20260831T144833Z-fn-wallpaper-fullscreen-v1`. No commit or
push has been made. The complete suite passes 1121 tests with 11 expected
skips; Host and Hub currently report zero failed service units.

## Lock-screen face retry and colour-only control states — 2026-08-31

Hyprlock now sets `ignore_empty_input=false`. After the initial eight-second
Howdy timeout, empty Enter completes the pending empty password prompt and
causes a fresh PAM cycle; `pam_howdy.so` remains `sufficient` before the normal
login stack. Typed Enter retains the password path, while a successful face
cycle still admits even when the supplied password was absent or wrong. The
running lock process is not replaced in place, so an already-visible old lock
must be unlocked once; the next lock reads the new configuration.

The Central de Controlo no longer contains the Wi-Fi, Bluetooth, volume or
microphone ON/OFF badges. Following the owner's visual refinement, only the
microphone and keyboard cards communicate state through background/border
colour; Wi-Fi, Bluetooth, volume and display use the neutral card style.
Neutral session actions are ordered on the first row and coloured actions on
the second.

The owner's first Enter retry observation came from the lock process that had
started before `ignore_empty_input=false` was installed. The journal confirms
that old process logged `Ignoring empty input`; it has since exited. Fresh locks
only instruct `ENTER: REPETIR CARA` after a failed cycle. Physical retries at
23:47 and 23:48 showed that Hyprlock marks the password-conversation transition
as checking before the next Howdy camera cycle begins. The interim text is now
the accurate credential-neutral `A VALIDAR…`. A 300-ms helper observes the
exact Howdy comparison PID among `/dev/video0` holders, so the separate
`A VERIFICAR A CARA…` line now exists only during real camera ownership. Its
detection was reproduced with the installed comparison process. Wi-Fi and
Bluetooth share a compact 46-pixel summary row; the session caption has a
dedicated gap and the four action cards share the surrounding 40-pixel height,
10-pixel radius, border and body typography. No PAM file, Howdy model or
recognition threshold changed. Seed and all five graphical homes match;
immediate recovery is root-only at
`/var/lib/apx/backups/20260831T225802Z-camera-state-session-cards-v1`. No
commit or push has been made.

## First-frame face status and symmetric animated bar shortcuts — 2026-09-01

Device ownership was still an early proxy: Howdy/OpenCV opens the camera before
the first captured frame. The pinned Howdy package is now revision 3 and
publishes a mode-0600 runtime marker only after `read_frame()` succeeds. Marker
identity includes PID and process start ticks; the shell helper also verifies
the live command line before displaying `A VERIFICAR A CARA…`, and Howdy removes
the marker on exit. A direct live comparison showed the first-frame transition
at 1.702 seconds, the normal timeout at about 9.6 seconds and zero residual
markers. Package revision 3 explicitly includes `config.ini`; the locally
modified configuration and enrolled model remain byte-identical, `root:apx`
0640.

Face success in `/etc/pam.d/hyprlock` now skips the password include and reaches
the common `pam_faillock.so authsucc` cleanup. Password fallback remains the
original `login` include. Existing diagnosis-induced faillock records were
cleared and the current count is zero.

QuickShell applies equal 5-pixel left/right margins to the bar, plus 5-pixel
inner insets for Calendar on the left and the IA/Battery/Control Centre group
on the right. Its Calendar, Environments, IA/model, Battery and Control Centre
buttons all use popup
visibility for active styling, covering `SUPER+D`, `SUPER+E`, `SUPER+I`,
`SUPER+B` and `SUPER+A` with the same scale/opacity animations used after a
click. The first four retain their complete labels; only the established
Control Centre cue changes from `[|]` to `[A]`. The final scale delta is 6%
with cubic easing and no overshoot. Only the newly selected button animates
when opening or switching menus; outside dismissal resets immediately, while
repeating the active button closes with the reverse animation. The opening
kind is armed before popup visibility changes, ensuring that both
activation and deliberate same-button deactivation animate. Bar-button hover
now uses a passive `HoverHandler`; popup selection is also an
active visual state. A stationary cursor therefore retains feedback when a
popup surface opens. A sibling `TapHandler` sends the first click on an active
button directly to its toggle, avoiding a focus-recovery click before closure.
The layer popup now distinguishes mouse and IPC origins: mouse openings request
no keyboard focus until the pointer enters the menu, while keyboard shortcuts
request it immediately. This preserves menu keyboard input without consuming
subsequent clicks on the bar. `HyprlandFocusGrab` follows the same origin/hover
condition rather than activating for every visible popup.
Every top-level QuickShell menu now shares the bar's `root.panel` background
and one-pixel `#26343a` outer border; internal semantic cards remain unchanged.
Application borders are also aligned with the QuickShell
bar: one pixel, opaque `#26343a`, identical for active and
inactive windows, with no cyan/green gradient. Repository, seed and five live
graphical homes match; QuickShell loaded cleanly and Host/Hub have zero failed
units. The full suite passes 1124 tests with 11 expected skips. Recovery is root-only at
`/var/lib/apx/backups/20260831T231335Z-first-frame-bar-shortcuts-v1`. No commit
or push has been made.
