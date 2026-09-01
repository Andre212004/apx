# APX Current Handoff

QuickShell popup interaction correction — 2026-09-01: the owner reported that
menus remained visually transparent, mouse-opened Calendar/Environments left
keyboard input in the terminal, and an outside click did not dismiss the menu.
The shared shell now uses consistent `#cc0a1014` surfaces (80% alpha), neutral
dark Control Centre buttons, exclusive keyboard focus for every bar or IPC
opening, and a transparent non-keyboard Top-layer surface below the Overlay
menu to consume the first outside click and close it. The menu and bar remain
directly interactive above/outside that dismissal surface. The Calendar month
grid has a separate matte `root.card` surface so weekday labels and dates remain
legible over the translucent menu.

At the owner's explicit exception to the dirty-checkout rule, only the current
`shell.qml` was installed in the active Hub. Source and live Hub both match
SHA-256 `eebcbf439a5b04b1e52f36958338c9e590ef53c4c664aaf2923ca51777571b5d`;
the immediate predecessor is recoverable from
`/var/lib/apx/backups/20260901T003135Z-quickshell-popup-interaction-v1/`.
The targeted 42-test group passed, the live compositor exposed the expected
430-pixel Overlay menu plus the full application-area Top dismissal surface,
exactly one QuickShell returned, Hub remains the only running Environment and
no unit is failed. The complete repository suite passes 1124 tests with 11
expected skips. No registered Development Environment exists. Per the
owner's boundary, no other dirty-checkout change was installed and the active
seed/runtime remained untouched. The remaining physical acceptance is one
owner click/keyboard check; repository-wide publication is the next milestone.

System VM v2 physical reset — 2026-08-24: the owner rejected the
accumulated VM opening path and requested a simple, near-native rebuild. The
from-first-principles v2 runtime, profiles, provisioning path, minimal
compositor surface and identity-bound adapter are now installed on the exact
disposable physical pilot. No VM was started.

v2 removes QMP/readiness/presentation markers, Host-side process rediscovery,
automatic source switching and nested timers. One runtime owns QEMU, swtpm and
optional Looking Glass under the existing session cgroup. Direct QEMU VGA is
the deterministic default. After Windows guest acceleration setup,
`SUPER+SHIFT+N` selects next-entry RTX/KVMFR native mode; `SUPER+SHIFT+R`
selects direct recovery even from a black surface. The target plan uses 5C/10T
and 19 GiB dynamically, reserving 1C/2T and roughly 7–8 GiB for the live Host.
New guests use sparse raw/NOCOW/native-AIO storage. The owner explicitly
requested removal rather than migration of the existing VM guests: old
`faculdade` generation `ba865d3f-e592-4281-8e76-6bba8402ff2a` and `trabalho`
generation `bd9caf9d-aa17-411e-a0e3-4c9ca21cbe2e` were completely destroyed by
APX, including home/root, snapshots, archives, APX-managed backups, metadata
and plans.

Fresh stopped Windows 11 v2 generations are `faculdade`
`3a2de127-176a-457a-97b4-a3010a4ca4d2` and `trabalho`
`c03e65b5-3310-4ff2-8a37-165769da1205`. Both have the verified Portuguese ISO,
source-matched runtime/profile/Hyprland/VFIO files and NOCOW VM directories.
Both have no raw/qcow2 disk, NVRAM or TPM; first entry therefore starts from
empty state. Historical code/config backups contain no guest-shaped content.

The first post-v16 create failed closed because the v2 template omitted its
VFIO manifest; automatic rollback removed the unpublished root/home. v17 adds
that exact manifest and supports an empty system-Environment catalog. Both
final creates then succeeded. Backups are
`/var/lib/apx/backups/20260824-system-vm-v2-v16/` and
`/var/lib/apx/backups/20260824-system-vm-v2-v17/`. The complete suite passes
1064 tests with 11 expected skips; source/Host/Environment hashes and ISO
digests match, Hub is sole, switch/Host services are active, VFIO is clear and
there is no failed unit.

The next boundary is owner-driven: enter `faculdade`, use the visible direct
QEMU surface to create the new raw disk/NVRAM/TPM and install Windows from the
verified ISO. Native mode remains disabled until Windows NVIDIA/IDD/Looking
Glass setup succeeds; physical direct/native/recovery performance acceptance
then follows `docs/system-vm-v2-architecture-2026-08-24.md`.

First-entry profile-access correction — 2026-08-24: the owner opened
Faculdade and saw a black background with an APX information/error surface.
QEMU never started. The runtime wrote exact error state saying its v2 config
was unavailable; no raw/qcow2 disk, NVRAM or TPM was created. The profile was
byte-correct and owned by uid 1000, but its new intermediate `.config/apx`
directory was `root:root 0700`, so the Environment user could not traverse it.
The session correctly returned to the Hub and restored the RTX.

v18 introduces an explicit `user_directory` provisioner primitive, repairs
`.config`, `.config/apx`, `.config/hypr`, `.local` and `.local/bin` to exact
`1000:1000` ownership in both stopped system Environments, and retains the old
metadata for rollback at
`/var/lib/apx/backups/20260824-system-vm-v2-v18/`. The complete 1064-test suite
passes with 11 expected skips. A uid-1000 probe rooted at the exact future
`/home` bind now reads/parses both profiles, source/Host provisioner hashes
match, both guests remain empty/stopped, Hub is sole, VFIO is clear and no unit
is failed. Next action is an owner retry of Faculdade; Windows/QEMU behavior is
still physically unobserved.

QEMU pre-firmware correction — 2026-08-24: the owner retry reached QEMU, which
then exited with status 1 and logged `mlockall: Operation not permitted` and
`locking memory failed`. This was not a Windows crash: OVMF never ran and the
new raw disk had only one 4-KiB block allocated. v19 removes the unnecessary
whole-process `-overcommit mem-lock=on` request while retaining the systemd
24-GiB VFIO memlock allowance. It also surfaces the last QEMU log diagnostic
instead of only the exit code and aligns the topology test with the measured
Ryzen sibling pairs: guest CPUs `0-9`, Host reserve `10-11`.

The v19 deployment passed 1065 tests with 11 expected skips and is backed up
at `/var/lib/apx/backups/20260824-system-vm-v2-v19/`. Source, template,
Faculdade and Trabalho runtimes match SHA-256
`b63e7b8a8c1dcba9179cd0f81300eaded82f107006c2f41522cfef0ef50b64e7`.
After proving QEMU/Looking Glass/swtpm/VFIO were inactive and both exact
generations stopped, APX removed only the blank-attempt raw file, pristine
NVRAM copy, empty TPM directory and empty lock. The admitted ISO remains at
SHA-256 `c74c96aa06e2548f14c76b5fd6600514c0d4f6eb05a731e4272ab005e8f48ce3`;
logs remain for diagnosis. Next action is an owner-started direct Faculdade
entry; APX intentionally did not start it during deployment.

Windows ISO keyboard-capture correction — 2026-08-24: the v19 retry reached
OVMF and the verified Windows ISO's `Press any key to boot from CD or DVD`
prompt, but direct GTK did not deliver the owner's key before the prompt
expired. QEMU logged no failure and the raw disk still had only one 4-KiB
block allocated. v20 changes the direct display from
`grab-on-hover=off` to `grab-on-hover=on`; with the cursor over the full-screen
VM, keyboard input is captured immediately. It adds no QMP, key injector or
timer. Deployment passed 1065 tests with 11 expected skips; rollback is
`/var/lib/apx/backups/20260824-system-vm-v2-v20/` and the installed runtime
hash is `aadebf461455a6e9f00f301c614b90ca297825a29d18eee0c7f1f107550824b1`.
The blank second-attempt disk/NVRAM/TPM/lock/socket were reset after proving
the Environment stopped and VFIO was clear. ISO and logs are preserved.

Faculdade Windows complete reset — 2026-08-24: after continued visible
instability, the owner explicitly requested total deletion and a clean start.
The exact complete-destroy plan for generation
`98edbee0-a816-4637-9473-9e824c8a6974` was approved and applied. It removed
the Environment home/root subvolumes and purged its disk, NVRAM, TPM,
snapshots, archives, metadata and stored plans. Post-destroy audit found no
recoverable qcow2/NVRAM/TPM/snapshot/archive data. Small historical deployment
directories bearing the Faculdade label contain only launcher/config rollback
files, some shared with `trabalho`, and no guest content.

A new minimal `graphical-base`/`system` Faculdade was created as generation
`ba865d3f-e592-4281-8e76-6bba8402ff2a` and provisioned atomically as
`windows11`. It is stopped and contains the verified Portuguese installer ISO
with SHA-256 `c74c96aa06e2548f14c76b5fd6600514c0d4f6eb05a731e4272ab005e8f48ce3`.
No qcow2, NVRAM or TPM state exists yet: the launcher creates all three fresh
on the first owner-started entry. The new instance carries the stable-display
marker, so installation begins through direct full-screen QEMU GTK/VGA with
no Looking Glass and no Host timer. Hub is sole/healthy and VFIO is clear.
Next action is the owner's interactive clean Windows installation; APX does
not accept licence terms or choose personal setup answers automatically.

Faculdade stable-display fallback — 2026-08-24: after v14, the owner reported
that Windows began and then appeared to crash. Host evidence contains no QEMU
error, VFIO failure, OOM, guest-container termination or supervised QEMU kill;
the launch started at 12:39 and the physical Host was abruptly rebooted about
six minutes later. Together with prior LGMP `primaryLost`/source-restart
evidence, this classifies the visible failure as the Looking Glass transition
between SPICE recovery and IDD/LGMP, not a proven Windows/QEMU crash.

To restore a usable baseline, only `faculdade` now carries the explicit
mode-0444 `looking-glass-disabled-v1` marker. Its launcher uses the direct
full-screen QEMU GTK/VGA recovery display and never starts Looking Glass, so no
SPICE-to-LGMP source switch occurs. The no-Host-timer v14 behavior remains.
The shared launcher/template and existing system VM launchers understand the
marker, but `trabalho` and future templates are not marked disabled. All 1065
tests pass with 11 skips; hashes/marker ownership match, Hub is healthy/sole,
and QEMU/Looking Glass/VFIO residue is absent. Rollback is
`/var/lib/apx/backups/20260824-faculdade-stable-display-v15/`. Do not run the
guest acceleration installer until this stable direct-display baseline is
physically accepted.

VM Host timer fully removed and black-wait made visible — 2026-08-24: the
owner explicitly requested removal of the timer after the v13 trial presented
a black surface. The prior-boot journal proves v13 did not trigger the former
deadline: Faculdade started at 12:24:18 and remained running until the machine
was abruptly rebooted roughly 27 seconds after the request. The latest launcher
log contains a new start and no supervisor QEMU termination. The black interval
was therefore guest/video-source startup with Looking Glass's waiting message
deliberately disabled, not another 60-second recovery.

VM readiness now has no Host deadline at all. The Host waits for QEMU/QMP and
the exact presentation marker for as long as the already-proven Hyprland owner
session exists; native desktops retain their ten-second bound. Looking Glass
waiting status is visible again (`win:disableWaitingMessage=no`) so a cold
Windows boot is not represented as a silent black screen. The launcher still
owns real client/QEMU liveness and `SUPER+E` remains the explicit owner exit.
Host, template, `faculdade` and `trabalho` are synchronized. All 1065 tests pass
with 11 skips; hashes match, Hub is sole/healthy and VFIO is clear. Rollback:
`/var/lib/apx/backups/20260824-vm-no-host-timer-v14/`.

Final false 60-second recovery removal — 2026-08-24: the latest physical trial
again proved QEMU running, both exact markers valid, presentation required and
no forbidden processes, while the extra Host `/proc` Looking Glass discovery
alone remained zero. Windows was visible, stable and usable until that outer
deadline. The process rediscovery was redundant: the Windows launcher itself
owns the actual Looking Glass PID, publishes presentation readiness only after
QMP `query-spice` reports a connected channel, then waits for that PID and
kills QEMU if the client exits.

The outer Host now requires the live exact QEMU executable plus the QMP and
presentation markers, and no longer attempts a second namespace-sensitive
Looking Glass identity proof. Actual client death still ends the launcher and
the supervised session. A regression test asserts this ownership chain. The
v13 correction is installed; source/Host hashes match, only Hub is active,
services are healthy, and no VM/VFIO/failed-unit residue remains. All 1065
tests pass with 11 skips. Exact rollback is
`/var/lib/apx/backups/20260824-vm-launcher-owned-liveness-v13/`. Next action is
one owner-initiated Faculdade acceptance entry.

Urgent Faculdade immediate-return correction — 2026-08-24: the owner reported
that the next entry appeared to return before Windows opened. The current and
previous handoff journals explain the visible immediacy: a failed handoff owns
the restored blocking Hub command and only publishes its error when that Hub
is stopped for the next request. The newly requested VM still ran for the
bounded 60 seconds behind that transition and was then rejected. Its exact
diagnostic remained `qemu=1`, both markers valid, presentation required,
forbidden list empty, trusted live client file valid, but `looking_glass=0`.

The v11 device/inode proof was invalid across the nspawn idmapped home mount;
that identity is mount-namespace-relative. The Host now compares the immutable
live `/proc/<pid>/exe` content of same-sized processes inside the exact outer
cgroup against the SHA-256 of the root-owned B7-799 artefact. It is independent
of truncated names and namespace-relative inode numbers without accepting a
marker alone. The correction is physically installed; hashes match, only Hub
is active, Host services are healthy, and no QEMU/Looking Glass/VFIO/failed
unit residue remains. Rollback is
`/var/lib/apx/backups/20260824-vm-looking-glass-content-v12/`; all 1064 tests
pass with 11 skips. Next action is one owner-initiated Faculdade entry.

Looking Glass live-identity correction — 2026-08-24: the owner's next two
Faculdade trials both provided usable Windows input but were recovered after
the same bounded interval. The new timeout evidence is exact:
`qemu=1`, both readiness markers valid, presentation required, no forbidden
process, but `looking_glass=0`. Thus neither Space nor ordinary input caused
the exit; the Host rejected its own remaining Looking Glass process proof.

The live client is installed as `looking-glass-client`, exposes the truncated
Linux `comm` value `looking-glass-c`, and is byte-identical to the root-owned
B7-799 artefact. The Host now first validates that installed file against the
root artefact and then admits the running process by its exact device/inode
identity inside the existing exact outer cgroup. This handles the kernel name
representation without accepting a marker alone or an arbitrary same-named
binary. The correction is installed; source/Host hashes and live/artifact
bytes match, only Hub is running, services are active, and QEMU/Looking Glass/
VFIO/failed-unit residue is absent. Rollback is
`/var/lib/apx/backups/20260824-vm-looking-glass-identity-v11/`; all 1064 tests
pass with 11 skips. Next is one owner-started >75-second Faculdade trial. Only
after stability is proven should the Windows NVIDIA driver and acceleration
tool be assessed separately.

Faculdade 60-second return correction — 2026-08-24: the owner's first trial
after the VM performance deployment reached a stable visible Windows desktop,
but returned to the Hub immediately when Space was pressed. Host evidence
places the supervisor rejection at the exact 60-second outer-readiness bound;
both exact readiness markers still existed and QMP/SPICE presentation had
succeeded. Space is not an admitted APX or standard Looking Glass exit
binding, so the timing does not establish an input shortcut failure.

The remaining Host proof used Linux `comm`, which is truncated to 15 bytes and
may be renamed by an application. VM acceptance now identifies the exact
`/proc/<pid>/exe` basename for QEMU and Looking Glass while retaining the exact
Host-owned systemd cgroup boundary. A failed 60-second proof now reports JSON
with both process counts, both marker states, certification state and any
forbidden processes. The correction is installed without restarting the Hub;
source and installed hashes match, the Hub is the sole machine, switch/Host
services are active, and no QEMU, Looking Glass, VFIO state or failed unit
remains. Rollback is
`/var/lib/apx/backups/20260824-vm-executable-readiness-v10/`. All 1064 tests
pass with 11 expected skips. The next action is one owner-initiated Faculdade
retest, including ordinary keyboard input after the desktop appears.

Repository VM boot/readiness/performance candidate — 2026-08-24: the owner
chose to retain KVM/VFIO/Looking Glass and requested closure of the boot,
unexpected-return and non-native-feel findings. The candidate is now installed
but not yet physically accepted. Windows QMP readiness uses the
documented buffered 30-second deadline rather than the remaining 12-second
implementation, and the regression test counts the exact deadlines so the
unrelated installer timer cannot satisfy it. A fresh Windows disk sends three
bounded DVD-prompt keys across a narrow 5.5--9.5-second window rather than one
fragile key at 7.2 seconds.

The launcher publishes separate QMP-running and presentation-ready proofs. For
Looking Glass, presentation additionally requires an actual connected SPICE
channel; a live client process without a video/input transport no longer
disarms Host recovery. The Host's VM-only outer window is 60 seconds. A failed
QMP or presentation stage stops the guest and shows a bounded APX Rofi error
with the diagnostic log path before returning, instead of disappearing
without an explanation. Ubuntu publishes the same two-marker contract for its
GTK recovery surface.

The target Legion's Windows and Ubuntu guests now use four physical cores/
eight SMT threads pinned to logical CPUs `0-3,6-9`, reserving physical pairs
`4/10` and `5/11` for AMD display, Looking Glass and APX supervision. Guest RAM
is 12 GiB; the VM Environment is bounded at 14 GiB high/16 GiB maximum with a
14 GiB VFIO memlock ceiling. Looking Glass explicitly enables KVMFR DMA and
one-millisecond frame/cursor polling; relative USB mouse input replaces the
absolute tablet. The Windows acceleration tool schedules a first-login
PowerShell verifier that selects IDD 1920x1080/120 Hz only when that exact mode
is advertised, selects the High Performance power scheme and records display,
GPU and service evidence at
`C:\ProgramData\APX\looking-glass-display.txt`.

The target-bound deployment synchronized both Host graphical-engine copies,
the generic launcher, system template/provisioner and the existing stopped
`faculdade` and `trabalho` Windows Environments. The running Hub was not
restarted and no VM was launched. Source/installed hashes and ownership match;
Hub/switch services remain active, the Hub is the sole machine, no QEMU,
Looking Glass or VFIO residue exists and the Host has no failed unit. Exact
rollback is `/var/lib/apx/backups/20260824-vm-readiness-performance-v9/`.

Emulated E1000E networking and the NVMe/qcow2-on-Btrfs disk remain deliberately
unchanged: replacing either requires verified guest VirtIO drivers and a
before/after physical storage benchmark, and must not trade a bootable Windows
guest for an unmeasured optimization. The complete repository suite passes
1064 tests with 11 expected skips. Next acceptance is owner-initiated: five
cold Faculdade boots, one new-Windows installer boot, confirmation of the
Windows 120 Hz report, Looking Glass DMA/
frame evidence, input observation and `SUPER+E` return. No automatic graphical
transition is permitted during deployment.

Latest VM/QMP, Windows creation and terminal repair — 2026-08-24: the failed
Faculdade entry was a bounded-readiness race, not a guest disk failure. QEMU
opened QMP during a cold start, but the launcher used one fragile two-second
`readline()` and the Host recovery deadline was only ten seconds. Windows and
Ubuntu launchers now parse buffered QMP messages, ignore asynchronous events,
retry reads for a bounded 30 seconds, and the Host grants VM sessions a bounded
35-second readiness window while native desktops remain at ten seconds.

Windows creation had three independent physical faults: two installed shell
seed assets were older than their digest-pinned sources; every graphical
snapshot redundantly reinstalled the release's NVIDIA/lib32 graphics stack;
and the private-root QEMU transaction omitted pacman's required
`--disable-sandbox`. The seed is synchronized, graphical-base packages are no
longer duplicated, and the system provisioner performs one consistent private
`-Syu` transaction. The previously failed residue was removed only through
`recovery-clean-unpublished`; a complete Windows 11 creation then succeeded as
`trabalho` and remains stopped.

`SUPER+Q` silently called absent Alacritty. The shared shell now launches the
installed Kitty in `/home/apx`; source, physical seed, Hub and existing normal
Environments are synchronized, and the live Hub compositor accepted the reload
and reports the SUPER/Q binding. Faculdade remains owner-started only. Hub is
running, Host/services are healthy, no failed unit exists, and all 1063 tests
pass with 11 expected skips. Backup:
`/var/lib/apx/backups/20260823-vm-qmp-seed-v8/`.

Latest black-screen/return/Windows-creation repair — 2026-08-23: the owner's
18:49 trial proved the VM itself reached QMP, SPICE 1920x1080 and then a B7 IDD
BGRA 1920x1080 DMA frame after 23 seconds, with no QEMU or Looking Glass crash.
The visible failure came from stale deployment boundaries: Faculdade's generic
launcher lacked the warning-suppression options, and Looking Glass used an app
id not covered by the compositor's no-shortcut-inhibition rule. The Hub's
persistent bridge client also lacked `--system`, exactly reproducing the
reported Windows 11 creation error before any Host request was sent.

Faculdade now uses the current launcher for both entry points, with the fixed
`apx-system-vm` app id, full-screen/no-inhibition matching and hidden B7 waiting
messages. `SUPER+E` and `SUPER+M` are native compositor exits observed by the
Host supervisor; they have no script, menu, socket or guest dependency.
`SUPER+SHIFT+E` remains the blue menu. The Hub now uses the current `/run`
client and sends a minimal payload for Windows/Ubuntu creation. QuickShell
hot-reloaded without an error; source/template/live hashes match; all 1062
tests pass with 11 expected skips. Hub is running, Faculdade is stopped, and
the rollback is `/var/lib/apx/backups/20260823-vm-black-return-create-v7/`.

Latest accelerated guest/reboot acceptance — 2026-08-23: the owner completed
`ATIVAR-ACELERACAO.cmd` and reported visibly improved response. The persistent
client log proves the matching Windows B7 Host and IDD became active after
4m35s, exported BGRA 1920x1080 frames through KVMFR DMA, and moved input from
SPICE to LGMP. The installer-triggered Windows reboot dropped the source at
5m16s; SPICE recovery reconnected immediately and accelerated frames returned
23 seconds later. The physical Host was powered off at that same boundary, so
there is no VM/client crash behind the reported black interval.

The B7 waiting/capture overlays are now suppressed with
`win:disableWaitingMessage=yes`; SPICE clipboard is explicitly off. Future
acceleration runs no longer reboot automatically: the Windows script explains
the possible 90-second black interval and requires an explicit Restart/Later
choice. `SUPER+E` and the redundant `SUPER+M` now request an immediate return
from the Host-owned compositor, independent of Windows, Looking Glass, SPICE,
or guest video; the blue menu moved to `SUPER+SHIFT+E`. The correction is
installed in source, template and the existing Faculdade, with its prior state
at `/var/lib/apx/backups/20260823-faculdade-super-e-direct-v6/`. Source,
template and live hashes match; the full suite passes 1061 tests with 11
expected skips. Hub remains running, Faculdade remains stopped, and the Host
has no failed unit.

Latest Faculdade launch diagnosis — 2026-08-23: the owner requested an
offline diagnosis while remaining on the Host tty1. The 18:23 physical log
proves the rebuilt no-FUSE Looking Glass client started correctly with
Wayland/EGL on AMD, KVMFR/LGMP, UNIX-SPICE input/video, JIT rendering and a
1920x1080 surface. There was no FUSE crash. The generic readiness loop killed
it after ten seconds solely because it searched for 16-byte
`looking-glass-cl`; Linux `TASK_COMM_LEN` publishes the 15-byte
`looking-glass-c`. That exact identity is now deployed.

The same attempt exposed a separate Hub race: boot autostart restarted after
the supervisor deliberately stopped Hub, competing with authenticated Hub
restoration and producing `graphical session result is malformed`. Autostart
now recognizes the trusted root-owned handoff lock before launch and after an
interrupted result, exits successfully, and cannot race the supervisor. Source
and installed hashes match. The full suite passes 1061 tests with 11 expected
skips. The owner remains intentionally on tty1; Hub and Faculdade are stopped,
there is no machine/VFIO residue, and no failed unit remains. Backup:
`/var/lib/apx/backups/20260823-faculdade-open-recovery-v4/`.

Latest near-native presentation and menu repair — 2026-08-23: the owner
confirmed Windows became visible but input-to-display response remained slow.
The Host was almost idle with ~25 GiB available RAM; the actual path was the
software VGA/GTK recovery surface because guest Looking Glass was not yet
active. Faculdade now always uses its verified B7-799 Looking Glass client as
the sole Host window. Its built-in UNIX-SPICE recovery keeps Windows visible
before guest setup, then changes automatically to KVMFR/RTX frames after the
Windows Host/IDD starts. JIT rendering, raw mouse, auto-capture and resolution
sync are enabled; no GTK window remains behind it, and readiness requires both
QEMU/QMP and the Looking Glass client.

`APXTools/ATIVAR-ACELERACAO.cmd` is now present in Windows media. One owner UAC
confirmation installs the matching IDD and Host silently and schedules the one
required guest reboot. The menu colour bug was reversed alpha/RGB ordering;
the deployed theme now uses Rofi's `#RRGGBBAA`, is anchored at the top and
accepts one normal click (`MousePrimary`) rather than the default double-click,
plus Enter/Space. Source/template/live hashes match and 1058 tests pass with 11
expected skips. Backup:
`/var/lib/apx/backups/20260823-faculdade-native-input-menu-v3/`. Hub is running,
Faculdade stopped, Host healthy and the RTX is restored. The next trial and
guest-local UAC confirmation remain owner actions.

Latest physical Faculdade black-screen/menu repair — 2026-08-23: the launcher
log proved QEMU failed at VFIO guest-memory mapping because its transient unit
had only an 8 MiB memlock limit (`vfio_container_dma_map ... Cannot allocate
memory`). VFIO sessions now receive a bounded 10 GiB limit at both outer and
inner units; an independent physical transient-unit proof returned 10,485,760
KiB. This is a ceiling, not reserved memory. Windows and Ubuntu launchers now
require QMP `running` before publishing an exact readiness marker, so a dying
QEMU PID cannot disarm Hub recovery and leave an accepted black screen.

The VM return overlay now treats any accepted selection as the sole
`REGRESSAR AO HUB` action, retries the authenticated broker three times and
uses clean compositor exit as a supervised fallback. It remains Rofi-only but
now has the centred translucent blue/cyan APX card styling requested by the
owner. Source, template and live Faculdade hashes match; 1057 tests pass with
11 expected skips. Backup:
`/var/lib/apx/backups/20260823-faculdade-black-screen-v2/`. The Hub is running,
Faculdade is stopped, Host state is healthy and both RTX functions are back on
their Host drivers. A new visual trial remains owner-initiated.

Latest VM-wide runtime repair — 2026-08-23: every exact
`virtual-machine-v1` Environment now runs through generic `apx-system-vm` with
only D-Bus, native PipeWire/WirePlumber, Hyprland, QEMU/Looking Glass and the
on-demand APX return menu. QuickShell, Waybar, locks/idling, portals,
pipewire-pulse, shared audio-state, model control and Host desktop services are
absent and forbidden by the readiness proof. Looking Glass uses `-display none`
instead of keeping a hidden GTK/VGA display. New Windows/Ubuntu Environments
are forced to the minimal `basic`/`system` plan and receive no desktop
autostart entry. Hyprland remains deliberately present as the lightweight
owner of `SUPER+E`, `SUPER+M`, input, display and supervised return.

The two launch failures are corrected at their actual boundaries: the session
admits `vfio-guest` only for VM mode and no longer kills a healthy Hub after a
redundant IPC fallback; the Host supervisor also reads the retained inner-unit
exit result and rejects non-zero session exits instead of mislabelling them as
an intentional return. Source and live hashes match across both engine copies,
the generic launcher, session, provisioning/management runners, template and
Faculdade. The full suite passes 1056 tests with 11 expected skips. The old
Faculdade autostart entry was moved to the recoverable backup at
`/var/lib/apx/backups/20260823-generic-minimal-vm-v1/`. No automatic visual
transition is permitted while this maintenance/Codex session is active; the
remaining acceptance is one manual Faculty launch followed by `SUPER+E`
return to Hub.

Latest `SUPER+H` and Faculdade control repair — 2026-08-23: the Host console
now opens a fresh root PTY from a uid-bound, single-use ticket issued only to a
provable official-Hub QuickShell child. It no longer reattaches or competes for
a persistent PTY; an existing visible Kitty window is focused and closing it
terminates its shell. Error presentation auto-closes instead of requiring
Enter/ESC. Source, Hub seed and live Hub copies are deployed and the broker was
restarted; the next physical `SUPER+H` press is the remaining acceptance test.

Subsequent physical acceptance confirmed the console window works but exposed
that `SUPER+H` itself still used the shared profile's ordinary terminal target.
The binding is now deployed through QuickShell IPC `openTerminal`, which maps
to the ticketed Host console only in the official Hub. A fresh Hub session is
required for this Lua change; physical shortcut confirmation remains.

The VM-only profile still starts no QuickShell. It now reserves `SUPER+E` for a
minimal Rofi Environment chooser and `SUPER+M` for the Host-supervised return
to Hub; the full-screen guest cannot inhibit those bindings. The switch broker
and runner support direct workload-to-workload handoff and restore Hub on a
stale/invalid request. Source and live `faculdade` copies are deployed; the
physical menu/return trial remains pending.

The owner confirmed `SUPER+E` functions in `faculdade` but requested the APX
visual language and no sibling switching. The deployed overlay is now
dark/cyan/monospace, identifies `FACULDADE` as the current Environment and has
only `REGRESSAR AO HUB`. It no longer requests the catalog or opens targets.

The panel's live kernel state proves 1920x1080 at 120 Hz. Faculdade now selects
the highest-refresh physical mode at scale 1, advertises exact 1920x1080/120 Hz
guest video with a 64 MiB framebuffer, fixes AMD topology with `topoext`, and
uses threaded writeback qcow2 AIO after native-AIO/Btrfs errors in the VM log.
These changes are deployed. They improve sharpness and reliability but do not
claim accelerated Windows 3D; that remains the owner-gated VFIO phase.

The architectural recommendation is an APX-supervised KVM guest with the RTX
3060 passed through by VFIO and Looking Glass presented through the AMD iGPU.
It should feel native while preserving isolation, complete deletion and instant
APX controls. A true hidden dual boot cannot retain those guarantees. IOMMU is
disabled in the current boot and no IOMMU groups are exposed, so no boot entry
or device binding has been changed. Enabling IOMMU, rebooting and auditing the
live groups require explicit owner approval. See
`docs/faculdade-native-feel-vfio-v1-2026-08-23.md`.

Latest dedicated Faculdade/Host-console repair — 2026-08-22: `faculdade` now
has the strict root-owned `virtual-machine-v1` marker and starts QEMU directly
through the supervised graphical session. It runs zero QuickShell/hyprlock
processes, presents Windows full-screen, and reserves only `SUPER+M` for return.
KVM, Secure-Boot-capable OVMF, TPM 2.0, NVMe, NAT, audio and QMP are active.
The official Portuguese installer passed Windows 11 Pro requirements and is
left visibly at Microsoft's licence terms so the owner can accept them
personally. The launcher now reliably answers the ISO prompt on a fresh disk;
after Windows writes more than 512 MiB, later launches prefer the NVMe disk.
The Host-console description in this older checkpoint is superseded by the
2026-08-23 fresh-PTY ticket design above. Temporary framebuffer/firmware
diagnostic artifacts were deleted.

Latest complete-removal policy — 2026-08-22: the owner requires deletion of an
Environment to be an unconditional complete purge. The installed Host executor
now removes all generations of matching snapshots and archives, explicitly
named legacy maintenance backups, `home`, `root`, capability/top-level metadata
including `kvm-v1`, registration and stored plans for that exact logical name.
The effect list is generation-bound and old destroy plans are rejected. Exact
UUID/name matching preserves neighboring Environments. The global append-only
audit journal retains only the deletion fact, never recoverable Environment
content. No `environment-only` or preserve-copies option remains. `faculdade`
has not been deleted; this change was tested with disposable filesystem trees.

Latest Faculdade VM and input recovery — 2026-08-22: `faculdade` now contains
QEMU/KVM, OVMF and swtpm plus a persistent Windows 11 VM definition (12 vCPU,
8 GiB RAM, sparse 120 GiB qcow2, UEFI, TPM 2.0, NAT and virtual graphics). A
strict root-owned `kvm-v1` marker leases only `/dev/kvm`; no Host shares, GPU
passthrough or inbound network are enabled. The launcher starts full-screen on
entry. The official Portuguese (Portugal) x64 ISO is bootable and matched
Microsoft's published SHA-256 exactly. A disposable KVM/UEFI/TPM/NVMe/NAT
smoke boot passed. Windows setup and activation remain interactive owner work.
Details are in
`docs/faculdade-windows11-kvm-v1-2026-08-22.md`.

The current keyboard repair deliberately supersedes the exclusive ITE grab
below. That grab caused ordinary typing to become non-responsive on the physical
laptop, so it was removed. FnLock is off; plain F1--F12 must remain application
keys and multimedia actions must occur only with Fn+F1--F12. The exact-device
observer maps ITE Fn-row events while leaving the ordinary AT keyboard
untouched. Physical confirmation of both paths remains pending.

Latest Fn exclusivity repair — 2026-08-21: the next owner trial proved
brightness routing but showed each ITE raw code also reaching applications
(for example Fn+F5 both lowered brightness and reloaded the browser), while
volume stopped responding. The exact bridge now takes `EVIOCGRAB` exclusively
on the dedicated internal ITE Fn interface and handles raw F1--F3 as volume
mute/down/up. The separate AT keyboard is not grabbed, so ordinary F1--F12 and
all typing remain normal. This relies on the live-captured target separation
between ITE Fn codes and AT ordinary function keys.

Latest physical Fn routing repair — 2026-08-21: the owner confirmed the OSD
design and volume path, but reported no response/feedback for brightness,
microphone, F7/F8/F11/F12/Print and no feedback for the working F10 hardware
toggle. A live evdev capture proved that this Legion mirrors Fn+F4--F12 on the
exact internal ITE keyboard as raw codes `62--68,87,88`, rather than the
configured XF86/F13--F16 symbols. The identity-checked bridge now routes those
ITE-only codes directly to the existing QuickShell/helper actions, while plain
F4--F12 remain on the separate AT keyboard and continue reaching applications.
AT `KEY_SYSRQ/99` is routed to the screenshot action. Direct post-install proof
passed microphone mute/restore, brightness `65535 → 62258 → 65535`, F7/F8/F10/
F11/F12 OSD endpoints, and a real screenshot at
`Screenshot_2026-08-21_23-12-03.png`. The full suite passes 1046 tests with 11
expected skips. Final owner observation of the physical row remains.

Latest hotkey feedback repair — 2026-08-21: the owner confirmed volume/mute and
Fn+F8, but F5/F6 had no effect and none of the actions had visible feedback.
The brightness backend physically passed a controlled raw
`65535 → 62258 → 65535` proof, isolating the issue to keyboard routing. The
exact bridge now accepts F5/F6 and codes 224/225 from either of the two already
identity-checked internal Lenovo keyboard interfaces. The common QuickShell has
a translucent bottom-centred OSD for audio, microphone, brightness, airplane
mode, monitors, launcher, windows, touchpad, calculator and screenshots. A
read-only Host `radio.status` operation is available, while the active OSD reads
the same kernel rfkill soft-block state directly from read-only sysfs so it
survives service-socket replacement. The source, seed, five existing
Environments and active Hub are installed. QuickShell loaded successfully, the
OSD was captured visibly, Hyprland reports `natural_scroll = true`, and a live
brightness proof passed `65535 → 62258 → 65535`. The full suite passes 1046
tests with 11 expected skips. Only owner observation of the physical keys
remains.
The owner additionally requested natural touchpad scrolling, where dragging
two fingers upward moves down through the page; the common profile now enables
that direction.

Latest keyboard behavior — 2026-08-21: the shared Lenovo Legion Environment
profile covers Fn+F1--F12 with the documented display switch, radio, Lenovo
panel, touchpad, task overview and calculator meanings mapped to APX/Hyprland.
Print Screen now saves a real timestamped PNG; Insert, Delete, Home, End, Page
Up and Page Down remain normal application keys. F8 stays on the Host kernel's
rfkill handler, while all other new actions are Environment-local or reuse
existing audio/brightness mediation. The earlier complete suite passed 1044 tests with
11 expected skips. The source, Host seed/runtime, Hub, faculdade, hytale,
Steam and minecraft copies match; the active Hub reloaded without config
errors and published every expected bind. A real full-screen capture succeeded
at `~/Pictures/Screenshots/Screenshot_2026-08-21_22-02-43.png`. Only eDP-1 is
currently connected and the Hub currently has no supported calculator, so F7
is presently a safe no-op and F12 will work after a calculator is installed.
Rollback copies are under
`/var/lib/apx/backups/20260821-laptop-hotkeys-v1/`; see
`docs/legion-keyboard-hotkeys-v1-2026-08-21.md`.

Final AC-powered performance closure — 2026-08-21: Host power reports
`ADP0=1`. Three alternating 256 MiB direct-I/O passes measured ~638 MB/s Host
versus ~655 MB/s Hub writes and ~3.07 versus ~2.97 GB/s reads, so the earlier
apparent 19% storage deficit did not reproduce. Weekly `fstrim.timer` is now
enabled; Btrfs CoW, compression, checksums, snapshots and qgroups were retained.
For GPU isolation, the exact same `vkmark 2025.01` binary, NVIDIA ICD, RTX UUID,
Hyprland, Wayland socket and resolution were used inside APX and from a Host
process outside the APX user namespace/cgroup. Warm-up was 691/691. Three 4K
pairs scored APX 93/192/192 versus Host 92/191/192: 159.0 versus 158.3 average,
about 0.4% nominally in APX's favour and therefore no measurable overhead.
The benchmark-only `vkmark` and `assimp` packages were removed. Structural
performance acceptance is closed; per-game Proton, 1% lows, gamepad, paired
Bluetooth and LAN `iperf3` are optional title/peripheral acceptance because no
game or those external fixtures are currently available.

Latest physical performance remediation — 2026-08-20: the apparent 49%
multi-core loss was the launcher's `CPUQuota=600%`, not nspawn overhead. Hub
and workloads now use `1200%`; the physical outer cgroup reports
`1200000 100000`, and Steam post-fix SHA-256 measured 15.06 GB/s in the full
transition proof and 20.62 GB/s in a short administrative proof instead of
7.15–7.64 GB/s. NVIDIA UVM and UVM-tools are now created, identity-validated
and leased. Because nspawn `--private-network` hides the module catalogue, the
launcher exposes only `/sys/module/nvidia` read-only; NVML and Vulkan now both
enumerate the RTX 3060 inside Hub and Steam while `DevicePolicy=closed`
remains active. Steam has matching 610.43.03 64/32-bit NVIDIA userspace plus
Mesa/RADV/Vulkan 32-bit and `vulkan-tools`; future graphical roots enable
multilib and install the same base. Hyprland enumerated both admitted internal
keyboards, ELAN mouse and touchpad. seatd still logs denied discovery attempts
for devices outside the fixed lease, which is intentional and not an input
failure. Hub and Steam QML were restored byte-for-byte, only Hub is active at
the normal login surface, and 1043 tests pass with 11 expected skips. See
`docs/apx-host-hub-steam-performance-assessment-2026-08-20.md`.

Latest QuickShell interaction change — 2026-08-20: the canonical
calendar menu is fully keyboard reachable, including view/period navigation,
date/month selection, Today/New Event, event edit/delete, and all event-editor
fields and actions. Arrow keys and Tab traverse, Enter/Space activate, Page
Up/Page Down change period, Home selects today, and Escape first leaves the
editor. The compact and expanded output-volume sliders now both update the
visible percentage and serialized Environment-local `wpctl` volume while
dragging. The source and focused tests are updated. The same source is active
in Hub after a successful QuickShell hot reload; IPC confirmed the calendar
surface visible and the Hub-local PipeWire sink remained readable. No graphical
Environment restart was needed. The exact old Hub QML is backed up under
`/var/lib/apx/backups/20260820-quickshell-calendar-volume-v1/`.

Latest Host timezone automation — 2026-08-18: `apx-timezone-v1` is installed
as a separate Host-only service using a root-owned local SSID-to-IANA-timezone
map. No Wi-Fi identifiers are sent externally. The current `Casa` mapping is `Europe/Lisbon`, physically verified against
the owner's current local time without disturbing NTP synchronization. Unknown
networks fail closed by retaining the current zone. New graphical launches
inherit Host `/etc/localtime` through `--timezone=bind`; the already-running
Hub was also repaired in place and verified at the same `Europe/Lisbon` time.

Latest staged Environment timezone change — 2026-08-18: the graphical engine
now requests `systemd-nspawn --timezone=bind`, so future Hub/workload launches
are intended to use the Host's `/etc/localtime` instead of each root's stale
timezone copy. This preserves Host authority and grants no workload location or
clock-setting capability. Repository, `/usr/lib/apx` and `/var/lib/apx/official-hub-v1` engine copies
match byte-for-byte. The Host-side trusted-network timezone service is installed
and active; the current `Casa` policy maps to `Europe/Lisbon`. The active Hub
was repaired in place after its older user-namespaced mount could not be
re-bound dynamically. Future graphical launches use `--timezone=bind`.


Last updated: 2026-08-14 after Environment UI, shortcut lifetime, loading,
Brave and hybrid AMD+NVIDIA work.

Read this file together with `AGENTS.md` and `PROJECT_STATE.md`. This is a short
continuity bridge, not a replacement for the canonical project state.

Latest physical repair: the 2026-08-15 boot failure was caused by NVIDIA
610.43.03's `nvidia-modprobe` returning success without creating
`/dev/nvidiactl`. The Hub launcher now creates only that exact ephemeral node
after confirming the kernel's unique `195 nvidiactl` registration, then checks
major 195/minor 255 as before. The installed launcher matches source and its
pre-change copy is under
`/var/lib/apx/backups/20260815-nvidia-control-hub-repair-v1/`.

Physical launch now passes NVIDIA admission and reaches the Hub login surface
on tty2. Two owner-unlocked observations loaded QuickShell and obtained an
accepted `identity.get`, then the compositor received a clean exit a few
seconds later; the evidence is consistent with the configured `SUPER+M` exit
binding rather than another launcher refusal. A third launch is currently
stable at the password surface. Do not bypass or automate the credential. The
next proof is a normal local unlock without pressing `SUPER+M`, followed by an
authenticated catalogue/management-status read and sustained Hub observation.
Environment creation remains unavailable until that authoritative Hub session
is active, which is expected policy rather than an independent creation fault.
The repository passes 1034 tests with 11 expected skips.

Latest UI repair: the popup was moved from an xdg `PopupWindow` to a focused
`PanelWindow` surface. This keeps pointer and keyboard input available when a
menu is opened by either a click or a compositor IPC shortcut; the Hyprland
focus grab still dismisses it on an outside click. The control centre no longer
duplicates the Atalhos APX toggle; that capability is now a selectable
`shortcuts` module in the Environment creation catalogue and is included in
the Intermediate and Complete presets. The popup now recomputes its horizontal
margin from the opening bar button and starts directly below the bar. Control icons retain the native
symbolic SVG pipeline at an integer size instead of fractional whole-popup
scaling. The Environment creation form is capped at 620×540 and expands into
view with a short top-origin animation. The repaired QML is live in Hub,
`faculdade`, and the future seed.

Latest hotfix: the reported `SUPER+A/B/D/E` failure was not a missing bind.
Hyprland received all four Lua bindings and their exact commands reached
QuickShell, but `PopupWindow.grabFocus` required an input serial that an IPC
shortcut does not have. QuickShell logged that it could not create the grabbing
popup, and each menu immediately returned `visible:false`. The shell now uses
`HyprlandFocusGrab` for `[bar, popup]`, removes the transparent dismissal
PanelWindow and keeps keyboard-opened menus visible. Live proofs returned
`visible:true` for Controls, Calendar, Battery and Environments.

The owner was restored from the old `faculdade` Environment to Hub. Return is
now enabled even while Host identity is still publishing: the Hub-only Host
console socket supplies a non-privileged local role proof, and a workload uses
local compositor exit as the bounded fallback while retaining authenticated
Host-driven return once identity is ready. The fixed QML is active in Hub,
copied into `faculdade`, and installed in the future seed. See
`docs/environment-shortcut-popup-and-return-hotfix-v1-2026-08-14.md`.

Latest physical checkpoint: the Hub is active on tty2 under the supervised
loading-validation chain. Its watchdog is healthy, QuickShell IPC responds and
the shared runtime is `/run/apx/session-1000`. `SUPER+A`/`SUPER+E` survived a
real Hub-to-Hub transition; their per-Environment toggle was exercised
disabled→enabled and was left enabled. The Host login remained inactive and
`masked-runtime` throughout the transition, with no getty journal repaint.
There are no failed Host units after cleanup.

Creation UI now has clear Basic/Base APX, Intermediate/Daily Use and
Complete/Work titles. Drawers and individual rows are title-only; right click
reveals the description and exact program list. Accepted creation closes the
form immediately, eliminating its background flash. Future Environments use
Brave, inherit the APX shortcuts and receive the revised Control Centre without
APX Host or Host Terminal authority.

Hybrid launches now expose AMD internal plus NVIDIA HDMI/DP KMS, the NVIDIA
render node and `/dev/nvidia{0,ctl,-modeset}`. Future roots receive exact
driver-matched `nvidia-utils 610.43.03-3`, `egl-gbm`, and verified Brave
`1:1.93.136-1` from digest-pinned Host artifacts. HDMI-A-1 was physically
disconnected at the last check, so actual two-monitor modesetting is the only
remaining hardware observation. Do not claim that final proof until a cable
reports connected and Hyprland lists both outputs.

The old `faculdade` profile predates these changes and failed closed during a
physical launch; Hub restored automatically. The owner already intends to
delete current profiles, so no in-place migration was performed. Full suite:
1032 tests, 11 expected skips, all passing. See
`docs/environment-creation-shortcuts-loading-brave-hdmi-v1-2026-08-14.md`.

Current physical checkpoint: the exact Hub is active. One `APX HOST ROOT`
Kitty is attached to one persistent Host Bash/PTY and one Codex process; all
three relevant services (`apx-host-console-v1`, Environment switch and Hub
graphical) are active and there are no failed Host units.

Latest UI result: creation profiles now explain their intended use and concrete
software additions. Capability drawers and rows are title-only by default;
right click on an individual capability reveals its explanation and exact
base/installed program list. The workload Control Centre height and footer were
repaired, with Apps, Lock, Files and Return in a readable 2×2 grid. Hub, Work,
Jogos, the common seed and the installed creation runtime are source-matched.
The active Hub QuickShell restarted successfully; the persistent Host terminal
and Hyprland session were not interrupted. Backups are under
`/var/lib/apx/backups/20260813-environment-ui-clarity-v1/`.

Latest hardware result: HDMI-A-1, DP-1 and DP-2 are physically on NVIDIA card1;
the internal eDP-2 is on AMD card2. The old hybrid launch leased only AMD KMS
and NVIDIA render, making external connectors invisible. Installed Hub and
generic launchers now lease both card/render pairs and set AMD:NVIDIA in
`AQ_DRM_DEVICES`. This takes effect on the next normal graphical launch. Do not
restart the active Hub merely for evidence; connect a real HDMI display for the
next owner-selected launch and then confirm both outputs with `hyprctl monitors
all`. See
`docs/environment-ui-and-hybrid-external-monitors-v1-2026-08-13.md`.

Latest incident and repair: Environments created through the new menu copied
the correct shell files but left the newly implicit `~/.local` ancestor as
`root:root 0755`. The `apx` shell launcher therefore could not create
`~/.local/state`, exited before writing its log or starting QuickShell, and the
generic launcher rejected the destination after ten seconds. The runtime now
explicitly owns and modes every generated ancestor beneath the user Home.
Existing stopped `jogos` and `andre` Homes were repaired to `apx:apx 0700` at
`~/.local`; their data was not replaced.

The same incident proved that a destination startup exception skipped the
runner's Hub-launch block. The supervisor now retains the destination error,
performs bounded workload cleanup, releases its generation-bound handoff lock,
and restores the Hub before surfacing the failure. Source and installed runtime
and runner match; the complete suite passes 1021 tests with 11 skips. Exact
pre-change files are under
`/var/lib/apx/backups/20260813-environment-shell-parent-ownership-v1/`.
The current Hub was not interrupted for a forced round trip; the next normal
owner-selected entry into `andre` or `jogos` is the physical visual proof.

The owner's first repaired `andre` session then remained healthy but ended at
exactly 120 seconds. This was the startup failsafe, not a QuickShell or
compositor crash: it stayed armed for the entire interactive session. The
runner now disarms it only after validating the root-owned active descriptor
against the trusted registration's name, role, release, running state,
generation, exact outer unit and positive PID. A genuinely incomplete startup
retains the 120-second recovery. The installed runner matches source and the
suite now passes 1022 tests with 11 skips. Normal use beyond two minutes is the
remaining physical observation.

The same session confirmed that fresh graphical accounts are intentionally
locked before local password enrollment (`apx:!` in shadow). Therefore the
owner's attempted sudo password could never succeed; this was not mistyping.
No Hub password may be copied or sent through chat. While the target
Environment is running, the secure recovery console can enroll its own secret:
switch to tty1, authenticate as Host root, run
`apx environment enroll-local-admin andre`, enter a new Environment-local
password twice, then return to tty2. The missing graphical enrollment UX is
still a product gap; do not describe sudo as ready in a freshly created
Environment until this bounded owner step completes.

Latest implementation: the physical Hub Environment button now opens a clean
native list with Work directly selectable and **Criar**, **Selecionar**, and
**Apagar** actions. Creation is the fixed `graphical-base` v2 model with
Hyprland, Rofi and the common QuickShell; deletion requires stopped state, the
selected generation and a second confirmation. The old explanation, ESC/Host
footer and Rofi chooser are gone. Create/destroy are serialized, journalled and
publish bounded progress. Work still exposes only return-to-Hub.

The active shell QML loaded in about 0.53 seconds and physical QuickShell calls
to catalogue/progress were accepted. Transition requests now show a full-screen
QuickShell progress overlay followed by a Host-owned tty1 APX progress surface,
so normal teardown does not reveal a Host prompt. Launcher readiness no longer
adds a fixed two-second stability wait: it requires two complete observations
50 ms apart. The full suite passes 1020 tests with 11 skips. No Environment was
created/deleted and no physical round trip was forced during this live Host PTY
session. Backups and rollback are in
`/var/lib/apx/backups/20260813-environment-menu-management-v1/`; see
`docs/environment-menu-management-and-loading-v1-2026-08-13.md`.

Latest owner decision: `Super+E` opens Environments; `Super+M` exits the Hub
to Host using Hyprland's internal dispatcher. The Hub Control Centre contains
“Sair para o Host” instead of “Escolher Environment”. These bindings and the
new Control Centre are loaded in the active Hub. Do not test `Super+M` or the
button merely for evidence while this Host PTY is attached; both intentionally
end the graphical Hub. QuickShell startup now uses two 50 ms readiness samples
instead of a fixed four-second sleep. The actual QML load measured about 0.5 s.

## Owner-selected emergency shortcut — 2026-08-12

The owner clarified on 2026-08-13 that `Super+H` in Hub must attach to the
same persistent Host PTY, not open a local shell or a competing Codex. Live
process evidence confirms the current Codex is already the single foreground
Codex under `apx-host-console-v1.service`, reached through the Hub Kitty
client. Closing Kitty only detaches it; reopening must reattach it.
The singleton opener first focuses an existing Host window, avoiding a second
client that the broker would have to reject.

The latest decision above supersedes the earlier E/M assignment and Control
Centre entry. During diagnosis, an `apx@apx-hub` machinectl
login caused logind to remove `/run/user/1000` after that transient login
closed, unlinking the live Hyprland/QuickShell sockets. Never create a user
machinectl session in an active graphical Environment. The current Hub needs
one controlled relaunch after installation; its persistent Host PTY survives.

The owner reported being trapped in an Environment because the expected
keyboard recovery route was unavailable. Host evidence showed that Work had
already returned successfully and the visible session was Hub: `apx-hub`
owned tty2, the handoff runner was still waiting for that Hub, and the switch
journal contained accepted returns.

The Host-owned official recovery path was invoked. The first recovery raced
with the still-active handoff supervisor and cleared that supervisor and its
lock; a second serialized recovery, after the runner was inactive, stopped the
remaining Hub session. Final direct evidence was `tty1`, no machine, inactive
Hub graphical unit, inactive handoff unit, and no handoff lock.

That 2026-08-12 recovery left the machine at the Host console, but this is now
historical: the Hub is currently running. The owner explicitly selected `Super+E`, not `Super+M`,
as the emergency compositor exit. The normal graphical button remains the
typed Work-to-Hub flow, `Super+F` opens files, and the later clarification
above assigns `Super+M` only to opening the menu. `Ctrl+Alt+F1` and the Host-owned `--recover` command remain
additional recovery routes. A direct Hub `Super+E`-equivalent compositor exit
has restored tty1; the physical Work keypress remains pending observation.

## Repeated Hub/Work round trip proven — 2026-08-12

The owner-reported return failure was reproduced in the journal. The Host
accepted the workload request but the old design left compositor exit to the
unprivileged client; Work therefore survived until the 120-second failsafe.
Return is now Host-driven after the same exact PID/UID/cgroup/generation
admission: systemd asynchronously stops only the active generation-scoped
outer unit, and the existing supervisor performs cleanup and Hub restoration.

The supervisor releases only its own inode-matched lock before waiting for the
restored Hub, so that Hub may immediately start the next transition. Boot
reconciliation now covers every trusted `graphical-base` v2 registration,
instead of only the historical `hub-ficticio`. UI failures are visible, an
accepted request cannot be spammed while teardown is pending, and every
accept/reject is journalled without sensitive payload. The owner subsequently
selected `Super+E` as the executor-independent emergency escape to Host
recovery. `Super+M` opens the menu without directly transitioning; Thunar
moved to `Super+F`.

Physical evidence includes repeated Hub → Work → Hub cycles. A return accepted
at 07:01:20 was followed by more than 23 minutes of healthy Hub watchdog
classifications. Three further complete cycles passed at 07:29, 07:30 and
07:31. Final cleanup left both registrations stopped, no machine, no active
record and no handoff lock. Btrfs quota is consistent. Repository regression
passes 1019 tests with 11 expected skips. Installed files match source; exact backups are
under `/var/lib/apx/environment-switch-v1/backups-20260812-host-driven-return-v2/`.
The generic boot reconciler awaits observation on the next normal reboot; do
not reboot solely for that proof. See
`docs/environment-switch-round-trip-hardening-v2-2026-08-12.md`.

The later shortcut decision is installed in Hub, Work, both reviewed seed
formats and the creation runtime. Direct Hub → tty1 via compositor exit was
observed at 10:10:50. Two attempted Work direct-exit proofs were pre-empted by
normal button returns, so physical `Super+E` in Work remains an honest pending
observation. Current state is tty1 with Hub and Work stopped.

Current handoff state after the owner's clean 07:34 exit is Hub stopped, Work
stopped, tty1 free, switch service active, no handoff lock and no failed Host
units.

## Persistent Host-console reattachment staged — 2026-08-12

The owner confirmed the practical continuity failure: the Hub/window can
disappear while Host-root Codex still owns its conversation, leaving `resume`
correctly blocked but no visible route to the live PTY. The broker and client
now stage persistent detach/reattach semantics. Reopening the Host terminal
from the exact authenticated Hub reconnects to the same Bash/Codex; `exit` or
Ctrl-D terminates it. Detached display output is memory-only and capped at
1 MiB. Workloads still receive no Host-console socket.

Do not restart `apx-host-console-v1.service` from the current conversation: its
PTY still uses the old running broker and would be terminated before handoff.
The source-matched broker/client are already installed and backed up without
restarting the live PID 729. After this conversation and its Host shell exit,
restart the service from tty1 or another independent root route, then prove
only the persistent PTY reattachment by reopening the Host terminal to the
same live foreground program. The graphical Hub → Work → Hub path is now
separately proven.

## Work created; initial round trip completed — 2026-08-12

`work` now exists as the visible **Work** Environment from
`hyprland-base-v2`, with independent 32 GiB root and 64 GiB home limits. It has
Firefox, Rofi, Thunar/GVFS, Flatpak/Flathub and the standard private desktop
folders. Its dark/cyan desktop resembles Hub but is correctly labelled Work and
contains no Host console, Host power, coordinated-update or Environment-admin
surface. `Super+D`, `Super+F` and `Super+B` launch Rofi, Thunar and Firefox.
The panel is the normal typed return-to-Hub flow; `Super+E` is the direct
emergency compositor exit and `Super+M` only opens that panel.

The Hub button is now `APX · HUB · ENVIRONMENTS`, with a richer state/session/
update menu. The switch daemon and client have a stable live-socket fallback,
and a request from inside the running Hub successfully sees Work in the
catalogue. The Work Hyprland configuration passes offline parsing. A later
supervised physical run kept Work's Hyprland and Waybar active for about 42
seconds, ended cleanly and launched Hub, proving the Work → Hub path.

The proof fixed three real first-run defects: Hub watchdog discovery is scoped
to the official unit; the generic launcher passes the current full graphics
policy; and an authenticated Waybar/Hyprland client can request return without
an impossible QuickShell parent. Work now exports Wayland variables to D-Bus
activation before portal consumers start. Both graphical sessions were then
closed locally, so tty1 is free at this handoff; normal use starts again through
the enabled direct-Hub boot service or a deliberate Host launch.

The complete repository regression passes 1011 tests with 11 expected skips;
installed runtime, switch service/client, session script and systemd unit match
their repository sources byte for byte. Host failed-unit count is zero.

The Work account has wheel membership and password-required sudo policy, but is
locked until the owner securely enrolls a local password. No password was
copied from Hub and no temporary or passwordless authority was created. This
affects sudo only, not normal graphical login or applications. See
`docs/work-environment-v1-2026-08-12.md`.

## Codex lock and handoff restart correction — 2026-08-11

The owner's earlier Codex conversation was not corrupted or blocked by the new
conversation. A Host-root `codex resume` remained alive on tty1 at a pending
approval and held that thread's writer lock. It was terminated gracefully and
the lock was released; its session file remains available to resume. This is
Host development state, not proof of per-Environment application independence.

The direct-Hub autostart unit is restored from `Restart=always` to
`Restart=on-failure`. A clean Hub exit is part of the supervised transition to
a workload, so unconditional restart could race that transition. The source,
test and installed unit must match; applying the unit requires only daemon
reload and must not restart the current graphical Hub.

## Recovered boot and graphical base v2 — 2026-08-11

The owner-reported black/partial display was a boot-chain regression, not a
dead panel.  The kernel renamed the internal AMD backlight and the Host power
service failed its namespace setup; the Hub then reached Hyprlock correctly but
the graphical watchdog rejected that pre-authentication state and tore it
down.  Backlight resolution is now hardware-path-based, the login lock is an
accepted exact state, and the power socket is optional for desktop startup.
The Hub is currently running on tty2 at the APX password screen; enter the
normal `apx` password to reach the desktop.  Do not restart it merely to test
these changes.

Host services are healthy with zero failed units.  The current Hub has 600%
CPU, 10/12 GiB memory high/max and 4096 tasks; its Btrfs root/home limits are
16/32 GiB and quota accounting is consistent.  Normal startup opens no Kitty.
Ollama now primes the NVIDIA device nodes and treats an early `nvidia-smi`
failure as transient rather than permanently skipping the model. The physical
proof loaded `qwen3-coder:30b` with an 8192 context and approximately 4.7 GiB on
the RTX 3060 while the exact SSD remained read-only.

The sealed `hyprland-base-v2` release contains 540 packages and normal desktop
defaults: valid pacman keyring, local password-required sudo, build tools,
`clear`/`less`, Thunar/GVFS, Flatpak+Flathub, notifications, Secret Service,
portals, removable-media support, generated locales, network services and
paccache.  Disposable certification proved systemd/logind/D-Bus, user manager
and user bus.  Runtime, graphical template catalogue, generic launcher and
switch admission all expect v2, and installed copies match source.  The running
switch daemon was intentionally not restarted because that would replace the
Unix socket inode bound into the stable live Hub; the installed v2 admission is
used on the next service/Host start, before any creation UI is enabled.

The control centre is back at native scale `1` under the 150% desktop scale;
the rejected 100% physical trial is not active.  Icons use direct Qt SVG
rendering with no `MultiEffect`.  Inspect sharpness after unlocking.  Real
Bluetooth scanning is proven, but no unknown device was paired.  The full test
suite passes 1004 tests with 11 skips.  Next work is the Environments creation
flow plus hot-plug/device selection, background/session policy, mediated file
transfer, backup and accessibility certification.

## Host/Hub daily usability correction — 2026-08-11

The reported Host-console `clear` failure was reproduced: the PTY advertised
`xterm-kitty`, while the minimal Host had no matching terminfo entry. Source and
installed daemon now use the compatible `xterm-256color` profile. Restarting
the daemon does not alter the already-open Host console; close it and open a new
`Terminal do Host` window to receive the corrected environment.

The owner reproduced `apx is not in the sudoers file` in the already-running
Hub desktop. The account database contained `wheel`, but Hyprland and both
Kitty processes inherited the launcher's fixed supplementary-group list, which
omitted GID 998 (`wheel`). The launcher now includes it. The local
password-required sudo policy also grants
the intended authority directly to `apx` as well as through `%wheel`; it is
valid mode 0440, active immediately, and the stale-process reproduction now
reaches the expected `a password is required` result. No password was reset,
no `NOPASSWD` rule was added, and Environment root remains non-root on the Host.
Future enrollment writes and validates both rules. Official Arch repositories
still do not contain a package named `brave`; AUR or another reviewed
Environment-local installation route is a separate decision.

The owner's subsequent AUR clone failed because the existing Kitty inherited
Hyprland's working directory `/`, not because Git lacked permission in the
Environment. The shared session now changes to `/home/apx` before starting
Hyprland, and the live Super+Q binding explicitly starts Kitty there; the live
configuration reloaded successfully. Already-open shells keep their own `$PWD`
and need `cd ~` once. `git`, `base-devel`, and `makepkg` are already installed,
so manual AUR builds are available even though no AUR helper is preinstalled.

The owner then built `yay` successfully and downloaded/verified `brave-bin`,
but observed severe desktop latency. Memory and I/O pressure were zero; CPU
pressure recorded 23.97% over 60 seconds during the Go build/compression, while
the whole Hub intentionally shares a 200% CPU quota. New regular Kitty windows
run Bash at nice 10 with idle I/O priority while Kitty itself stays normal, and
the current Bash was adjusted live. This preserves UI responsiveness without
raising the Environment quota. The Brave transaction later failed on the
signature for cached `nspr-4.39-1`; the sync databases were ten days old. Do
not disable signatures. Run one full `sudo pacman -Syu less`, then retry
`yay -S brave-bin`. `less` is confirmed absent and must enter the next base.

The 100% control-centre trial was physically too small and its transformed
post-effect icons still looked pixelated. The live accepted state is now 125%
physical (`5/6` under the 150% desktop scale); IPC reports 283x291 logical
pixels for the closed 340x350 design. Icons use Qt `ToolButton.icon` tinting
directly and no longer use a hidden image plus `MultiEffect`. The overview and
expanded Bluetooth states are under
`audit/2026-08-11-environment-consistency/`.

The same audit found that the Hub root/home qgroups have no limits and quota
accounting is inconsistent/rescan-needed; the Environment currently sees the
full 476 GB Host filesystem. `systemd-logind` is failed and `user@1000.service`
is inactive, so ordinary user services, inhibitors and some desktop integration
are not reliable. Treat storage enforcement and a complete user session as P0
before general Environment creation. Full prioritization is in
`docs/environment-consistency-and-normal-linux-gap-audit-2026-08-11.md`.

The normal launcher no longer opens Kitty automatically; only `--test` does.
The current already-open automatic Kitty is intentionally left untouched so no
user work is closed. The change applies on the next Hub launch/reboot.

A real authenticated Bluetooth scan was observed as `Discovering=yes` and
returned twelve nearby devices, including named devices. The scan stops after
the intended eight-second bound. Pair/connect code is present, but no device
was selected or paired without the owner. The control centre's 150%-scale icon
rendering and press feedback were corrected in source and the live Hub QML.
Screenshots and measurements are under
`audit/2026-08-11-control-centre/`; full notes are in
`docs/host-hub-usability-investigation-2026-08-11.md`.

## Host-local coding model installation — 2026-08-05

The exact Samsung 870 QVO 1 TB external SSD passed SMART and non-use checks;
the owner-authorized wipe removed its old NTFS content. It is now a dedicated
TPM2/PCR-7-bound LUKS2 + Btrfs model store mounted privately at
`/var/lib/apx/model-store`. There is no stored recovery key because the disk is
limited to replaceable public model artifacts. Firmware/Secure Boot policy loss
therefore means reformat and redownload, and the cable must not be removed while
the model is active.

The target-bound udev/systemd adapter, Host Ollama Vulkan service, loopback-only
API, Qwen Code defaults and guarded `apx-local-code` launcher are installed from
repository sources. The RTX 3060 was detected through NVK with about 5.4 GiB
available. The selected and downloaded daily model is `qwen3-coder:30b` rather
than the newer 80B Coder-Next because 19 GB fits this machine's 28 GiB RAM while
48.4 GB plus context does not. Direct inference, Qwen Code connectivity, clean
stop, TPM re-unlock, remount, model persistence and exact udev rule matching
passed. A real hot-unplug was deliberately not attempted. The full Qwen Code
tool prompt has a measured several-minute cold-start cost; the 30-minute model
retention reduces repeated session latency. See
`docs/host-local-coder-external-ssd-v1-2026-08-05.md`.

## Legion hardware profiles awaiting first owner selection — 2026-08-04

The Host physically reports Quiet/Normal/Performance platform profiles,
Hybrid Graphics support, current Hybrid mode and no firmware iGPU-only mode.
The staged Hub UI therefore implements AMD-only as APX exclusion of the already
`D3cold` NVIDIA device, Hybrid as AMD display plus NVIDIA offload, and NVIDIA as
the firmware MUX dedicated mode.  GPU selection has a 30-second confirmation,
marks reboot required, and then uses the existing independent reboot warning.
The launcher is prepared for dynamic AMD/NVIDIA DRM numbering.  No profile was
changed and no reboot was run.  The installed components need one normal Hub
relaunch/reboot before the running Hub can see the replaced socket/client/QML;
then each of the three GPU policies still needs owner-triggered physical proof.
See `docs/legion-hardware-profiles-v1-2026-08-04.md`.

## Secure no-password boot in staged migration — 2026-08-03

The owner chose Secure Boot + measured UKI + TPM unlock. The first signed UKI
boot passed with `Measured UKI: yes` and `Measured OS: yes`; LUKS password slot
0 remains and there is no TPM token. The current signed image is
`/EFI/APX/apx-system-v1.efi`. Duplicate boot choices were removed, the normal
menu is hidden, the recovery entry is explicitly labelled, `quiet splash` is
embedded and tty1 is the sole automatic recovery console from the next boot.

The owner corrected the PXE-first firmware order and enabled Secure Boot.
Physical Host evidence proves `Secure Boot: enabled (user)`, measured UKI/OS,
the APX signed entry and `/EFI/APX/apx-system-v1.efi` stub. LUKS still has only
password slot 0. TPM PCR 7 is now eligible but intentionally waits until the
normal APX session password and initial hyprlock are proven.
See
`docs/secure-boot-measured-uki-tpm-unlock-v1-2026-08-03.md`.

The transient `apx-host login:` screen is exactly one tty1 recovery getty, not
leaked terminals. Inspection found one task, 544 KiB and 15 ms CPU. The installed
autostart now clears it before launching the Hub while preserving recovery; the
next boot must prove the visual result. The owner privately set the existing
Hub `apx` password. Source-matched hyprlock/hypridle initial login, five-minute
lock and ten-minute display-off are installed and parser-clean, with no auto-
suspend. The immediate next proof is `BLOQUEAR` followed by a successful unlock
with that password; only then reboot into the initial-login gate. See
`docs/apx-login-idle-and-clean-transition-v1-2026-08-03.md`.

## Pending one-time Hub relaunch — Bluetooth v3 and dynamic identity — 2026-08-03

The Host now has installed source-matched shared-services v3 Bluetooth control
(power, bounded scan, status, connect/disconnect/remove and interactive
KeyboardDisplay pairing) beside unchanged v1/v2.  Backups are under
`/var/lib/apx/host-services-v3/backups-20260803-bluetooth-v1`.  The live Hub QML
preserves all owner customization and adds only a Bluetooth manager button.
Because v3 was restarted while the Hub was active, that running container still
holds the retired bind-mounted socket inode; v1/v2 and BlueZ remain healthy,
but one normal Hub relaunch is required before v3 can be validated from inside.
Do not call real-device pairing certified yet.  See
`docs/bluetooth-control-and-cross-environment-handoff-v1-2026-08-03.md`.

The environment-switch service is also installed source-matched with a dynamic
trusted catalog for the Hub and Host-authenticated self-identity for workloads.
The fixed `hub-ficticio` target was removed from the service/client/runner and
the owner has now destroyed that disposable Environment. Workloads still have
only local compositor exit back to the Hub and no sibling switch or Host-console
path. Backups are under
`/var/lib/apx/environment-switch-v1/backups-20260803-catalog-v1`. A future new
disposable workload is required for physical round-trip proof.

The owner also accepted a persistent per-Environment session-restore toggle,
disabled by default, with a save prompt on exit.  Only application-level
browser/LibreOffice adapters are intended; arbitrary Wayland process freezing
is rejected.  This is documented architecture, not implemented behavior.  See
`docs/environment-catalog-identity-and-session-restore-v1-2026-08-03.md`.

## Immediate next-chat state — 2026-08-03

The stopped disposable `hub-ficticio` was explicitly destroyed through its
generation-bound APX plan. Its root, Home and registration are absent; the
catalogue contains only the running official Hub and `machinectl` contains only
`apx-hub`. A historical red-shell file remains in the root-owned backup area
but is neither registered nor launchable.

Newest partial physical result:
`docs/hub-ficticio-environment-switch-trial-2026-08-03.md`. The independent
`hub-ficticio` workload exists from `hyprland-base-v1` with generation
`441ed74c-c89f-47ae-8102-1ce3e09e6b47`, a red Quickshell, and no mounted Host
console/update/power endpoints. The enabled closed Host switch service accepts
only exact Hub -> `hub-ficticio` and active self-return -> Hub from a direct
Quickshell child. The official Hub was safely relaunched and authenticated
status passed with no handoff active; a Host-root caller was refused. The owner
proved entry into `hub-ficticio` twice, but neither attempt returned and the
second exposed Host-console text before a power-off. Both boots reconciled the
workload to stopped with the Hub healthy. Return is now local to the workload:
the button, `Super+M`, and emergency binding exit its own compositor so the Host
supervisor restores the Hub. A separate 120-second Host failsafe forces return,
and tty1 now shows a clean APX transition page. Repeat the round trip; it can no
longer require a hard power-off, but do not claim clean return until observed.

Newest installed boot change:
`docs/direct-hub-boot-v1-architecture-and-pending-result-2026-08-03.md`.
systemd-boot timeout zero and direct Hub entry are owner-confirmed: the menu and
redundant Host-root prompt disappeared. Root tty1 remains recovery. Plymouth
`spinner` is now installed in the rebuilt initramfs to present the still-required
LUKS secret graphically. No display manager, PAM change, Host user or TPM token
was added. Measured UKI is now proven; Secure Boot enforcement and TPM unlock
remain staged. A photo or live capture is still required for a true aesthetic
audit of the firmware/Plymouth screens.

Newest result: `docs/exact-hub-confirmed-host-console-v1-2026-08-03.md`.
The official Hub alone has `TERMINAL DO HOST`. One click opens a fixed Host-root
Bash PTY; the phrase/token confirmation was removed. Exact Quickshell ancestry
and one-console locking remain. Initial PTY dimensions are forwarded so
full-screen programs such as Codex render correctly. This is deliberately unrestricted
Host administration and therefore a conscious weakening of separation after
confirmation. Workload launchers do not mount or lease the socket. The owner
removed the proposed return-to-tty button and its protocol operation entirely.
Inspection confirmed both previously opened consoles closed cleanly and left no
unexpected Bash, Kitty, client or Codex process behind.
The owner then opened the corrected console and resumed Codex successfully.
Kernel inspection showed a valid `33 × 70` PTY, Host root identity, Codex as the
foreground group, exactly one live console and healthy Host/Hub services.

Newest result:
`docs/general-graphical-handoff-and-host-controls-2026-08-03.md`. The generic
launcher physically passed with `test` while retaining Waybar/Alacritty and
separate packages; the exact Hub also re-passed. Audio state, Wi-Fi and
Bluetooth follow the authenticated active Environment. All six shared/control
sockets return to `root:root 0600` when inactive. Updates and power remain
Hub-only. The Hub now has BLOQUEAR and two-step SUSPENDER; suspend preserves the
Environment. The update preview is ready with no exclusions and the creation
backend defaults to `follow-host`, but the production graphical creation screen
is not complete. No mass update, forced rollback or new recovery mechanism was
run, per owner direction. The suite passes 939 tests with 11 skips.

The newest result is
`docs/system-power-v1-architecture-and-result-2026-08-03.md`.
`apx-system-power-v1` is installed, enabled and active. REINICIAR/DESLIGAR now
use a Host-enforced two-step path tied to the exact Quickshell, coordinate with
updates, respect inhibitors, close the active Environment and call logind only
after zero-machine proof. The inactive socket is `root:root 0600`; the exact
launcher leases it only to the translated active user. The non-destructive
physical proof passed; no reboot or poweroff was executed. The suite passes 935
tests with 11 skips. The live Hub proposal document records every accepted
item, both justified design corrections and implemented status.

The first subsequent real DESLIGAR request found a recovery race: the
foreground launcher and Host power runner concurrently cleaned the same device
lease state. The service failed closed after closing the Environment and did
not power off the Host. The installed v2 correction serializes recovery and
quiesces an exact root Hub launch supervisor before takeover; installed/source
hashes match and 19 focused tests pass. Backups are under
`/var/lib/apx/backups/20260803-system-power-recovery-v2`.

The next REINICIAR press closed and relaunched the Hub but did not reboot. Host
evidence proved exact recovery succeeded and the only failure was the final
unsupported `loginctl reboot` verb. The installed v3 runner now uses confirmed
`systemctl --no-block reboot/poweroff` after the same inhibitor, lock, recovery
and zero-machine gates; suspend remains `loginctl suspend`. The daemon also has
asynchronous runner launch and broken-client tolerance. The owner proved the
corrected real reboot with a changed boot ID; the current daemon loaded on the
new boot. Installed/source runner hashes match, 24 focused tests pass, and the
latest backup is under
`/var/lib/apx/backups/20260803-system-power-clean-exit-v4`.

The newest result is
`docs/coordinated-updates-and-audio-physical-result-2026-08-03.md`.
`apx-coordinated-update-v1` and `apx-audio-state-v1` are installed, enabled and
active. The live exact Hub has `[ UPDATE ]`, a confirmation preview and a
one-second `MIC ATIVO` indicator. New Environment creation defaults to
`follow-host`; owner exclusion remains available. A bounded physical proof
passed the exact ALC287 sink/source, authenticated update preview and complete
audio/device revocation, returning to tty1 with no residue.

No real mass package transaction was run. Next evidence still needs two
disposable admitted graphical Environments, one excluded target and a forced
package failure with retained rollback snapshots. Cross-Environment audio also
waits for the general graphical launcher. Do not call the exact-Hub result a
production-wide handoff. The complete suite passes 927 tests with 11 skips.

The owner subsequently rejected any reusable shared package cache, shared
folders and a cross-Environment file portal. Update downloads may use only
root-owned operation-private staging invisible to Environments. Application
notifications stay local and disappear with the inactive session; only
Host-originated machine-health/update alerts remain candidates for a separate
global channel.

The latest focused checkpoint is
`docs/host-shared-services-v3-architecture-and-result-2026-08-02.md`.
`apx-host-services-v3` is installed, enabled and active beside v1/v2. It adds
detailed Wi-Fi objects, snapshot, events, structured errors and a no-argv,
no-tempfile passphrase route to Host iwd. The mutable Hub Quickshell now uses a
compatibility adapter for v3 Wi-Fi while retaining v2 Bluetooth. The bounded
physical proof passed and returned to tty1 with no residue.

Do not retire v1/v2. A protected-network enrollment still needs an
owner-approved disposable access point, and persistence/revocation still need
two admitted graphical Environments. The general graphical launcher remains
the blocker for that proof. Audio remains Environment-local; power mutations
and updates require separate higher-risk contracts. The suite passes 913 tests
with 11 skips.

The latest checkpoint is
`docs/official-hub-health-watchdog-and-shell-stability-2026-08-02.md`. The
fixed four-hour interactive expiry is removed. Normal Hub sessions now receive
an independent Host health check after 60 seconds and every 30 seconds
thereafter; recovery requires three consecutive unhealthy observations. The
bounded `--test` path still has its separate 75-second expiry. A physical
interactive run returned seven consecutive `classification=healthy` results
before normal exit, followed by tty1 restoration and zero residue.
The complete repository suite passes 905 tests with 11 skips.

The earlier reported Hub crash was the old four-hour expiry, not a Hyprland
crash. Quickshell did also terminate independently in Qt Wayland/Core paths.
The live Hub runner now prevents duplicate instances, keeps a rotating verbose
log at `~/.local/state/apx-shell-v1/quickshell.log`, records exit status and
falls back to Waybar. The owner's live QML was preserved and this experimental
shell was not promoted to the common seed. Installed/source launcher SHA-256
is `8e0d4e0dbde40f6dca496ae34a2d233235096531971bddf37983da63a60ce8d4`;
installed/source runner SHA-256 is
`c96816092296251547c08e9bac53f6f893fbf4044f953b6be7b774b94b1adba4`.

The newest checkpoint is
`docs/official-hub-private-users-local-admin-result-2026-08-02.md`. The official
Hub graphical launcher now uses a dynamic 65,536-ID private user namespace and
idmapped Home while retaining password-required sudo to root inside the Hub.
Host-service peer authentication translates shifted peer IDs and continues to
reject Environment root. A temporary exact sudo proof passed; its sudoers file
was removed.

Host `seatd` brokers only the admitted primary AMD/input/tty devices. Exact
temporary device proxies live under `/dev`, not nodev-mounted `/run`, and the
outer unit enforces `DevicePolicy=closed`. The final physical proof passed
Hyprland, Quickshell, Kitty, local audio, Host menus, AMD display, NVIDIA NVK,
`private_users=true`, `local_admin=true`, tty1 recovery and zero machine
residue. The suite passes 902 tests with 11 skips. Bluetooth began powered on
and remained on; certification now restores the initial state. Diagnostic
`strace`/`libunwind` were removed; signed Host `seatd` remains.

The owner can enter with `entrar_no_HUB` and use normal `sudo pacman ...`; the
prompt is for the password enrolled for Hub user `apx`. This launcher remains
an exact-generation physical-pilot bridge, not the general Environment
launcher.

Subsequent owner entries proved that the auxiliary AMD-open preflight itself
was unreliable: it ran in a different transient inner service from Hyprland
and could be denied even while repeated real compositor certifications passed.
It has been removed. The bounded actual Hyprland renderer/socket/eDP-2/input
readiness is now the fail-closed graphical proof; failure still recovers tty1
and all lease state.

The corrected launcher passed a complete `--test` proof and the actual
`--interactive` path reached the Hyprland socket before controlled Host
recovery. Final state was tty1/stopped with no lease, seatd or sudo-proof
residue. Installed/source launcher SHA-256 is
`7cb78f591254980248ffc48ef1d35caacbe849b860bab2d4186d4c319ce1ef7f`.

The newest checkpoint is
`docs/quickshell-ascii-v1-and-hub-codex-result-2026-08-01.md`. The live Hub now
starts Quickshell with a cyan, slightly rounded ASCII bar and anchored compact
popovers for Wi-Fi, Bluetooth, audio and battery; Waybar is retained as crash
fallback. A full physical proof passed and recovered to tty1 without machine
residue. This is a Hub-only design trial: do not promote it to the common seed
or mutate `hyprland-base-v1` until the owner has reviewed it in use.

Codex CLI 0.146.0 is temporarily installed only for Hub user `apx` at
`~/.local/bin/codex`, with Node/npm local to the Hub. No credentials were
copied from Host/root. The owner must run `codex login` inside the Hub. Do not
add Codex, Node or npm to `desktop-essential-v1` or graphical templates.

The newest focused checkpoint is
`docs/desktop-context-menus-v2-and-nvidia-result-2026-08-01.md`. The official
Hub has working ASCII click menus for known Wi-Fi networks, Host Bluetooth
power/already-paired devices, local PipeWire volume/output, and read-only
battery details. `apx-host-services-v2.service` is installed, enabled and
active beside v1. Unknown Wi-Fi credentials, new Bluetooth pairing, and Host
power profiles are intentionally pending.

NVIDIA render offload is physically verified in the Hub with nouveau/NVK as
`NVIDIA GeForce RTX 3060 Laptop GPU (NVK GA106)`; AMD remains display owner and
only the NVIDIA render node is leased. The shared Waybar configuration contains
the same menu bindings for future Environment copies. It is not yet functional
in arbitrary normal Environments because no admitted general graphical
launcher mounts/authenticates the bundle and immutable `hyprland-base-v1`
lacks the new Environment-local NVK package. Those are the next architecture
and release tasks; do not mutate the v1 release.

The latest installed launcher fixes an interactive-entry regression: normal
`entrar_no_HUB` no longer executes the Bluetooth/Wi-Fi/NVIDIA certification
cycles or requires Bluetooth initially off. Those mutations are exclusive to
`--test`. A physical interactive run remained active for 1 minute 54 seconds
and recovered cleanly to tty1. Final Bluetooth is powered off, no machine is
running, and no systemd unit is failed.

The newest checkpoint is
`docs/host-services-v1-architecture-and-result-2026-08-01.md`.
`apx-host-services-v1.service` is installed, enabled and active. Host Wi-Fi
continues to use `iwd`; NetworkManager is absent. Host NTP is enabled and
synchronized. BlueZ 5.87-2 and bluez-utils are installed and enabled on the
Host, with the final controller powered off.

The current official Hub launcher mounts only the fixed client, pure contract
and Unix socket. Waybar shows Host Wi-Fi, Bluetooth and NTP status. Bluetooth
click performs the only admitted mutation, a typed power toggle. A bounded
physical run proved an on/off round trip and restored off state, alongside
Waybar/audio/graphics/input readiness, tty1 recovery and no machine residue.
Host-side or inactive callers are refused. Wi-Fi switching and Bluetooth
pairing remain pending protocols; no arbitrary iwd/BlueZ command is exposed.

The newest base-profile checkpoint is
`docs/desktop-essential-v1-physical-result-2026-07-31.md`.
`desktop-essential-v1` and `waybar-ascii-v1` are installed as root-owned,
digest-bound Host seeds. Every future `graphical-base` or `hub-graphical`
creation now receives an independent copy automatically. This was physically
proved by stopped `codex-test-essential-v1`, generation
`7ba06c0e-e7fe-4bb4-abcf-3d7ae5682c35`, with exact config/style hashes and no
manual post-create overlay. The installed runtime/source hash is
`2f7755328232152d47f4e5af996001ce325a3d632b53913a2c84339d777ca092`.

Local playback audio, network status, system-time display, and the common ASCII
presentation are the ready baseline. `pavucontrol` is optional and already in
the Hub. Wi-Fi administration and kernel time remain Host-owned. The newer Host
services checkpoint adds authenticated Bluetooth status and power control;
pairing and Wi-Fi mutation remain pending.

The complete repository suite passes 897 tests with 11 skips. Host tty1 is
active, no Environment machine or failed unit remains, and the APX recovery
journal contains no uncertain operation.

The newest focused checkpoint is
`docs/waybar-ascii-v1-physical-result-2026-07-31.md`.

The authoritative Hub's Waybar parsing and autostart are fixed. Its common
ASCII layout is versioned under `config/waybar-ascii-v1`; the Hub has no
workspace selector, while normal Environments place five workspace buttons
immediately to the right of the date. A physical bounded run verified Waybar
and local playback audio, with capture excluded, and recovered to tty1 without
residue. The network item represents private `host0`; Host Wi-Fi is not
delegated. Bluetooth was unavailable at that dated checkpoint and is
superseded by the Host services checkpoint above.

Disposable `codex-test-waybar-v1`, generation
`1df14250-c628-49d4-961e-44ad22fd67a4`, exists stopped with an independent copy
of the Environment profile. The immutable base release was not changed. The
APX button is presently visual only because the installed broker is stale and
the official Hub/base lacks the matching typed client and descriptor. Next
work is the separately versioned exact-generation handoff bundle and physical
Hub-to-fixture-to-Hub proof. That earlier Waybar-only checkpoint passed 872
tests with 11 skips; the newer desktop-essential checkpoint above supersedes
that count.

The authoritative current checkpoint is:

`docs/official-hub-owner-hyprland-checkpoint-2026-07-31.md`

The canonical `hub` remains generation
`6f63f9a9-daea-40d1-969f-e25ff0752f4d`, sourced from immutable release
`hub-headless-v4`. Its mutable live root/home now contain the owner's Hyprland
0.56.1-2 and kitty 0.48.1-1 installation and owner configuration at
`~/.config/hypr/hyprland.lua`. Local-admin enrollment is complete. The
preserved, non-authoritative old graphical Hub remains `hub-testes`, generation
`2c3dbacc-106f-4053-8603-f649552f5513`.

The new guarded official-Hub launcher is installed. From Host `tty1`, root runs
`entrar_no_HUB`; it starts the exact Hub, leases the resolved built-in input
devices plus AMD graphics and tty2, starts Hyprland as Environment user `apx`,
and opens kitty automatically. A bounded proof verified Hyprland, `eDP-2`, two
keyboard devices, ELAN mouse/touchpad identities, a real kitty window, complete
recovery to tty1, and no machine residue. The owner then confirmed two usable
interactive sessions, including keyboard, pointer, terminal open/close, and
session exit.

`Super+M` is intentionally temporary: it ends Hyprland and returns to Host
recovery during development. The owner decided that the final normal desktop
must not expose a return-to-Host shortcut. Do not remove it until final boot and
protected administrative recovery are implemented. `Ctrl+Alt+F1` and the
health-based Host watchdog are also current recovery mechanisms, not final UX.
The historical four-hour expiry was removed on 2026-08-02.

For terminal-only maintenance, root may use `apx environment shell hub`, leave
with `exit`, and then use `apx environment stop hub`. Do not run
`start-hyprland` directly in that shell; physical graphics/input are provided
only through the guarded launcher.

Final observed state was Host `tty1`, Hub registration `stopped`, no running
machine, and no failed systemd unit. The complete repository suite passed 858
tests with 11 skips after the final launcher correction. Nothing was committed
or pushed.

Immediate next work is owner-led Hyprland customization inside the Hub. APX
integration must preserve the owner's mutable config. Later work is final boot
into Hub, replacement of the temporary exit binding, audio/brightness
mediation, locale/portal cleanup, owner-selected launcher/file manager, and
then the separately scoped APX Hub-to-Environment button/effect path.

## Superseded 2026-07-30 cutover checkpoint

The following section records the previous clean-headless delivery and is
historical. Statements that the official Hub has no Hyprland/kitty, that
keyboard input is unproven, or that another official-Hub launch is blocked are
superseded by the 2026-07-31 checkpoint above.

The owner decided that the current graphical Hub is disposable test
infrastructure. It is now preserved as the ordinary, non-authoritative
Environment `hub-testes`. The canonical `hub` is now a clean
Arch text environment: no Hyprland, kitty, Waybar, portal, theme, wallpaper, or
APX graphical configuration. The owner will install the stable Arch Hyprland
package and the officially recommended kitty terminal personally, then follow
the current Hyprland Master Tutorial. APX management UI is integrated only
after the owner finishes that design.

The guarded physical transition is complete:

- a pure graphical-input proof contract and a physical adapter with a
  30-second independent watchdog;
- a two-build `hub-headless-v4` builder that admits base Arch, `sudo`, and the
  headless APX client but rejects graphical packages and configuration;
- Environment-local password enrollment, normal `apx` shell entry, separately
  named root recovery entry, and explicit entry/exit terminal boundary banners;
- a fixed Hub egress policy that admits DHCP/public Internet while denying Host
  services, private networks, and sibling veth interfaces;
- a journaled cutover that renames the whole current Hub to `hub-testes`,
  removes its Hub authority, and publishes a prepared headless candidate
  without deleting any root, home, release, or existing `test`.

Two new independent `pacstrap` builds initially exposed expected timestamped
certificate/GnuPG/linker state and were retained in diagnostic quarantine.
After deterministic regeneration of that state, two fresh builds matched
exactly. Immutable release `hub-headless-v4` was published with tree digest
`3c21ba4145314cd8e6c09b1178adb3f1a904e9e406af03695676b4c21310a0c5`
and manifest digest
`5cbb6524dd562e7fb82cb21afedf5f7f6f2a5dd09c91e390d1049d01542b39dc`.

The cutover completed under plan
`b4f9c2a949d98d3032875400af4fada2fe1a06f5b1978c0f0a248e4044336392`.
Official Hub generation is `6f63f9a9-daea-40d1-969f-e25ff0752f4d`;
preserved `hub-testes` generation remains
`2c3dbacc-106f-4053-8603-f649552f5513`. The textual runtime and fixed network
adapter are installed.

Physical validation booted the official Hub to systemd `running`, observed 138
current Arch base packages, UID-1000 user `apx`, no graphical package or
`~/.config`, successful HTTPS to archlinux.org, blocked access to the Host
gateway, and correct entry/exit boundary banners. Final recovery is tty1 with
the Hub stopped, no running machine, no failed unit, and no network-policy
residue. The only intentional owner step is
`apx environment enroll-local-admin hub`, which sets the private local password
and enables password-required sudo without disclosing the password to Codex.

The owner's first enrollment attempt exposed that `machinectl shell` returns
Host status zero even when its inner command fails, so the absent marker was
falsely reported as already enrolled. Physical inspection proved the marker,
wheel membership, sudo policy, and password were all still absent/locked. The
installed runtime now reads a fixed structured state line from inside the Hub,
checks the password status after `passwd`, and writes the marker only after
password, wheel, and exact sudo policy all pass. Source and installed runtime
match SHA-256
`e7bc41258559fdec5074c2b2f7f9b115cf595323dcf22805f69451bccfea4209`;
all 855 tests pass with 11 skips. The owner should repeat the same enrollment
command; no cleanup or marker removal is needed.

The repository suite passed all 855 tests with 11 skips. `git diff --check`
and compilation of the guarded physical adapters pass.

The complete current diagnostic record, including the root cause, is:

`docs/graphical-hub-input-handoff-2026-07-19.md`

The installed resolver and repository source currently match. A bounded
assisted proof on 2026-07-30 observed 3,247 real ELAN events and a changed
Hyprland cursor position. It observed zero keyboard events and the temporary
`Super+F12` marker did not appear. Recovery passed completely: tty1 restored,
Hub and `test` stopped, no machine/unit residue, and zero failed units. Two
later tty1 keyboard-count attempts also returned zero, but the test timing was
not explicitly synchronized with the owner, so they are ambiguous rather than
proof that both internal keyboard candidates are inactive.

On 2026-07-30 the owner explicitly moved the graphical input/button proof out
of the immediate critical path and requested delivery of the clean textual Hub.
The cutover no longer treats graphical-input evidence as a prerequisite because
it does not activate or delete the graphical Hub: that whole generation is
preserved, stopped, as `hub-testes`. The synchronized count-only tty1 probe and
full bounded graphical proof remain required before resuming button work later.

The installed `apx-graphical-input-proof-v1.py` measures both candidates
simultaneously and matches repository SHA-256
`5dc0ee3be9f2adc3f43a8ab4c19ef7b9040614db3d66bf7f4e564432d5ae8107`.
It remains inactive until later synchronized owner-assisted invocation.

Current installed prototype facts:

- global command: `entrar_no_HUB`;
- executor: `apx-executor-v1.service`, local Unix socket only;
- official Hub generation: `6f63f9a9-daea-40d1-969f-e25ff0752f4d`;
- preserved `hub-testes` generation: `2c3dbacc-106f-4053-8603-f649552f5513`;
- test generation: `69b56acc-fd4d-4499-8009-e1d0108466f4`;
- keyboard candidates: internal i8042 `AT Raw Set 2` and internal USB ITE
  048d:c101; the event-producing identity is not yet synchronized/proven;
- pointer identities: both mouse and touchpad capabilities on internal
  AMDI0010 ELAN, resolved dynamically rather than pinned to event numbers;
- broker currently still grants the old i8042 identity plus both ELAN nodes,
  AMD card2/renderD129, and tty2;
- watchdog currently returns to tty1 after 180 seconds;
- the APX switcher is configured to open automatically in Hub and test;
- no successful Hub-to-test button handoff has occurred yet.

## Active physical-graphics safety block

Physical H0 v9 directly proved an active AMD-driven `eDP-2` output and Wayland
socket, but no application client. During v10 the owner powered off after about
25 seconds because the graphical session had no obvious usable exit. The old
absolute Host deadline was 120 seconds and had not yet expired. Physical H0 is
therefore code-locked and v10 is abandoned, not a successful result.

Repository recovery-v2 work reduces the normal observation window to 10
seconds, the independent Host deadline to 15 seconds, and stop ceiling to 3
seconds. Do not re-enable or physically launch it until pure tests and a
non-graphical exact-unit interruption rehearsal pass and their evidence is
reviewed. No ricing choice is required for this safety work; visual
customization remains a later Environment-local layer.

The recovery-v2 suite passed its then-current 714 tests (11 skipped), and the non-graphical
exact-unit rehearsal also passed. A first protected-home path failure was
safely recovered and established that watchdog assets must run from private
`/var/lib/apx/h0` state. The corrected 15-second timer stopped only a dummy
`sleep`, selected tty1, and left zero residue or failed units. Physical graphics
remain code-locked until a fresh review; passing this rehearsal does not
automatically re-enable them.

## Hyprland-by-default decision

The 2026-07-30 headless official-Hub bootstrap above supersedes the initial Hub
template choice in this historical section. It does not change the longer-term
goal of extracting a reviewed, independently rebuilt graphical base after the
owner develops it.

The owner selected a common minimal Hyprland base for every normal Environment,
including the Hub. Configurations are copied independently at creation. Every
starter includes a minimal Waybar APX control; the Hub adds the GTK management
application. Environment-local `sudo pacman` is unrestricted, including in the
Hub, while Host and sibling package state remain inaccessible. Essential
graphics/input/network/audio are default; camera, microphone, controller, and
removable storage are opt-in.

The repository contracts and source assets exist, but the physical
`hyprland-base-v1` release does not. Next work is verified package acquisition,
two reproducible builds, and disposable non-Hub validation. Preserve the
current headless Hub as rollback and do not replace or graphically activate it
while physical H0 remains code-locked.

## Owner-Reported Physical State

The owner reports that the target-bound physical handoff completed Phases 1
through 8 on the Lenovo APX development computer:

- minimal encrypted Arch host installed;
- headless Hub created;
- separate Development Environment created;
- Git, GitHub authentication, Codex, build tools, and the repository placed in
  Development;
- Ollama package installed inside Development;
- no Ollama model downloaded.

The dated 2026-07-17 read-only audit is preserved in
`docs/apx-physical-pilot-state-and-cleanup-audit-v1-2026-07-17.md`. On
2026-07-18 root-host read-only checks agreed on the fixed physical identity,
pilot marker, healthy APX status, running Hub and Development, zero failed
units, expected mounts, and healthy full Btrfs quota accounting. Detailed
Development qgroup limits remain unavailable through the `/var/lib/apx`
subvolume view and still require the guarded quota-recovery procedure.

The owner renamed the GitHub account from `Andre212004` to
`andrepereira2004` on 2026-07-18. Current clones, helpers, package metadata, and
instructions use `https://github.com/andrepereira2004/apx.git`; the dated audit
retains the old URL as historical evidence.

## Owner-Confirmed Lifecycle Test

Read-only root-host reconciliation on 2026-07-18 found that the Development
audited on 2026-07-17 was subsequently destroyed and replaced. The APX journal
records complete stop and destroy of generation
`72b3777b-6dba-4175-8d3e-3fb24401bf50`, including `remove-home` and
`remove-root`, followed 13 seconds later by creation of generation
`b90155f6-ece2-44ae-91fc-42d91d6b35a5` and its successful activation.

The replacement is running but has an empty home, approximately 8 KiB of APX
Environment state, and no GitHub CLI, Ollama, Qwen Code, Codex, or Development
repository. No registered APX snapshot, archive, quarantine, or catalogue
object contains the prior generation. The owner confirmed that they intentionally
performed this lifecycle test. Treat it as owner-confirmed test history, not an
unexplained security incident or executor malfunction.

Consequences:

- the 2026-07-17 audit is historical, not current Development evidence;
- Phase 10 removal of temporary root-host development state is deferred while
  root-host development continues;
- the old in-place quota-recovery procedure must not run against the replacement;
- all root-host bootstrap, recovery, and temporary-development checkouts must
  remain preserved;
- the replacement remains an intentionally simple Development fixture;
- repository development and tests with new `codex-test-*` disposable
  Environments may continue;
- changing Hub or Development still requires fresh exact owner approval.

## Pinned Local-Model Decision

The owner decided on 2026-07-18 that installing a local Ollama model is not
currently worthwhile because the wanted model consumes too much storage. It is
a future milestone, not a prerequisite for Phase 10.

- Do not download a smaller substitute merely to complete Phase 9.
- Preserve the current no-Ollama, zero-model state as intentional.
- Treat Ollama and model response, persistence, and restart tests as
  `not-applicable` while the decision remains pinned.
- Continue to require APX storage/quota health, lifecycle teardown, Host/Hub
  isolation, repository recovery, and every applicable non-model gate.
- Reopening model installation or external storage requires a separate owner
  decision and the already documented design/approval gates.

## Next Owner Action

The owner has chosen to temporarily install and run Codex, Git, and GitHub CLI
as `root@apx-host` on the disposable physical pilot so physical APX tests can be
automated. The repository-only preparation is documented in:

`docs/temporary-root-host-development-mode-v1.md`

The temporary root-host mode is active and is the accepted development location
for now. Keep the replacement Development simple and do not install Ollama,
Codex, GitHub CLI, or a repository there. Continue repository implementation
and physical validation through reviewed `codex-test-*` disposable
Environments. Preserve Hub, Development, APX recovery records, and all root-host
checkouts. Do not begin Phase 10 root-host cleanup while this mode remains in
use. Changing Hub or Development still requires fresh explicit approval for
the exact effects.

The prior read-only audit procedure remains:

`docs/physical-pilot-state-and-cleanup-audit-v1.md`

That session must collect and sanitize Host, Hub, Development, APX storage,
package, service, listener, Ollama, repository, and temporary-file evidence. It
must not clean, install, download, start, stop, mount, unmount, or otherwise
change the machine.

The current replacement Development has no Ollama package. A future reprovision
may restore the package-only configuration, but must not download a model to
complete Phase 9 or Phase 10.

## Active Disposable-Test Hold

`codex-test-lifecycle-v1` generation
`1ec52013-e715-413a-bb48-b4691cf31ee9` was created, started, observed, and
cleanly stopped on 2026-07-18. Its isolation and stop evidence passed, but it is
intentionally preserved because the installed runtime's destroy plan is not
generation-bound. Do not apply destroy plan
`868d54ef7e965d9e019c7995af0b46b2b835bd72ae05e187f238e57e1b2bbaee`
or generate a replacement plan with the installed runtime.

The repository fix binds destruction to the registered generation and refuses
stale plans before effects. The next physical step is a separately reviewed
runtime update, not manual cleanup. Hub and Development remain unchanged.

The exact runtime-only candidate preview is recorded in
`docs/physical-runtime-generation-fix-update-2026-07-18.md`. Its deterministic
30,720-byte artifact passed the closed reader and every supplied gate except
`recovery-console-not-verified`. Do not import or activate it and do not treat
the installed boot entry as proof of a tested recovery console.

The repository now has a pure closed recovery receipt contract in
`src/apx_recovery_console.py` and the exact future rehearsal is documented in
the candidate dossier. It performs no reboot and cannot turn boot metadata into
positive evidence. The remaining physical rehearsal requires the owner at the
machine and fresh approval for the exact reboot window; it is not implied by
the standing root-host development permission.

The next repository-only boundary is also closed: the fixed import/effect plan
accepts only the runtime-only candidate, a ready exact preview and matching
artifact evidence. It maps one regular Host runtime target and preserves the
`/usr/bin/apx` symlink as an invariant. It cannot create staging or install the
runtime. Executor and Hub-client physical mappings deliberately remain
unsupported rather than guessed.

The owner-authorized recovery-console rehearsal completed successfully on
2026-07-18. The reboot crossed a real boot boundary; built-in keyboard,
encrypted-root unlock, root text console, unchanged boot components, unchanged
Hub/Development/disposable generations, intact LUKS/Btrfs layout, zero failed
units, no package transaction, healthy APX, and zero uncertain operations were
reconciled. The sanitized receipt is closed-contract `verified` with digest
`db70438f786c3282755c44940bc27a5b18095bd31eeb4a904dbce62003634ad2`.
The old blocked preview is retained as history and is now stale; produce a new
preview before requesting any separate import approval.

Hyprland work now follows clean-host H0. A current read-only observation fixed
the AMD card2/renderD129/eDP-2 boundary, excluded NVIDIA, selected stable i8042
keyboard and ELAN touchpad candidates, and confirmed tty1 recovery/tty2
experiment availability with no display manager or graphical owner. The entire
dated 332-package graphical chain was rebuilt and verified in `/tmp`. A newly
implemented finalizer removed generated private trust and identity/time/log
state, producing normalized tree digest
`83c58deaa56c83c23eee57dc02ecd3a67ccaede0d75918932f7f3b9557ab3401`.
At that observation point nothing had been promoted or launched. The later
promotion result is recorded below.

The immutable-release promotion preview is complete and has zero blockers. It
binds only `hyprland-h0-v1`, the exact normalized tree and current reconciled
machine/APX state. Plan digest:
`dc15038fa6147f6f2ba098e90f880898ff4523586117bc0a338f9ea6e067146d`.
At preview time no promotion had run. The later owner decision authorized only
creation of that one immutable release; Environment creation and graphical
activation remain separate operations.

The owner authorized and the Host completed creation of the immutable
`hyprland-h0-v1` release. Its 332-package root is read-only with configured-tree
digest `4798a8f6a0396dfab94758a9bb2498364a72948c6b2587593eadc04faca15b92`.
The initial exact partial was preserved and completed only through a
digest-bound continuation; nothing was deleted. Hub, Development, disposable
hold, source, and APX health remained unchanged. There is still no graphical
Environment or Hyprland session. Next work is exact Environment creation plus
GPU/input/VT/watchdog contracts, each separately bounded before physical H0.

Repository runtime support for the next boundary now exists: `graphical-h0`
maps only to `hyprland-h0-v1`, has 16 GiB root and 8 GiB home limits, and is
refused by the generic headless start before any effect. The intended first
stopped Environment is `codex-test-hyprland-h0-v1`. The changed runtime is not
installed on the Host and that Environment does not exist yet. First publish an
exact runtime update through the retained rollback contract, reconcile the
Host, and only then preview/create the stopped disposable Environment. Physical
graphics still require the separate AMD/input/VT/watchdog adapter.

The exact runtime candidate was subsequently rebuilt twice and passed the
closed artifact reader: 30,720 bytes, artifact digest
`a1b55982d14fb0bdf7afa8f1dd7991caf9d3a7ad5e24b321510763ad5b675a66`,
candidate runtime digest
`0d7cc0c0c0631b65f68639f8b4994e3e3441a817604487256a30edd82f96da9f`.
It remains untrusted in temporary storage and was not imported. Fresh Host
observation found Hub and Development absent from `machinectl` and without
current units, although both registrations still claim `running`; the journal
shows they shut down cleanly for the recovery reboot. Reconciliation of those
two registrations is the immediate physical blocker and requires a fresh exact
owner instruction because it directly changes Hub and Development state.

The owner supplied that exact authorization. Reconciliation completed with
unchanged generations, and update `update-a1b55982d14fb0bdf7afa8f1dd7991ca`
installed the verified runtime while retaining the previous bytes for rollback.
The real stopped Environment `codex-test-hyprland-h0-v1` now exists as
generation `c4fc5c49-4106-4a56-b1f0-13bffa41a0c1`, sourced from
`hyprland-h0-v1`, with 16 GiB root and 8 GiB home limits. Generic activation
was tested and refused before creating a machine. The immediate milestone is
now the exact AMD/input/tty2/watchdog activation and recovery adapter; no
physical Hyprland session has run.

The pure device/config boundary is also complete. Current read-only evidence
produces plan digest
`3ef21d19a2518d4fcea9d51513cc1eee63f6ff593d4470bcc10955b06e3059cb`,
allowing only AMD card2/renderD129, stable built-in keyboard/touchpad identities,
and tty2 for 120 seconds. tty1, NVIDIA, other input, audio, camera, network,
Host files, and executor access remain excluded. The installed Hyprland parsed
`config/hyprland-h0.conf` as the internal `apx` user and returned `config ok`
without any device or graphical effect. Next implement and hostile-test the
fixed transient unit, independently armed watchdog, readiness observer, and
unconditional teardown; do not physically launch while owner recovery is
unavailable.

The non-extendable watchdog state machine and internal session runner are now
implemented and unit-tested. The runner validates all internal device numbers,
starts only transient seatd, drops Hyprland to UID/GID 1000 with exact tty,
video, render, and input groups, removes all capabilities, and traps mediator
cleanup. The watchdog refuses deadline extension and cannot complete with tty1
unrestored or any process, mount, socket, or lease residue. Neither has been
physically executed. Next create the independent Host launcher so watchdog
arming cannot die with the graphical unit, then test interruption without
granting physical devices.

The fixed Host expiry script is now implemented and zero-effect rehearsed. It
stops only `apx-h0-graphical-c4fc5c49.service`, activates tty1, and requires the
exact nspawn machine, Environment mounts, and unit activity all to disappear.
The final rehearsal returned `tty1-restored zero-residue` with APX healthy. It
cannot start/restart, delete, broadly kill, or touch Hub/Development. Next work
is only the independent timer arming plus graphical-unit launch/observer path.

The pure independent-timer plus graphical-unit launch plan is complete with
digest `9c5342a5859a93a09dcafefe8b6d53d370a2028e712d3321ee61d15d93cf9305`
after final review fixed internal seatd to `SEATD_VTBOUND=0` so only the Host
controls tty1/tty2.
It binds the exact config/session/watchdog files, requires the 120-second timer
active before any grant, and contains only the closed five-device nspawn unit
with private networking and resource limits. It remains non-executing. Next
implement safe asset staging plus the bounded readiness/teardown adapter; do
not bypass that adapter by running the emitted commands manually.

The exact staging adapter is now published and physically complete. The config,
session runner, and watchdog exist under the fixed private H0 Host directory
with exact 0400/0500 modes and reviewed hashes; the result explicitly records
no graphical activation. APX is healthy/stopped, tty1 remains active, and no
timer, graphical unit, device grant, or Hyprland process exists. The remaining
physical boundary is the not-yet-implemented launch/readiness/teardown adapter.

That exact adapter is now implemented with 45-second observation inside the
independent 120-second watchdog. It revalidates real connector/driver/tty1,
display-manager absence, assets, generation, devices, failed units, and old
residue, then always invokes recovery in a `finally` path. The v2 assets still
need exact staging before the first physical run.

Physical v2 was attempted. The independent timer armed and recovery returned to
tty1 with no machine or Hyprland process, but nspawn rejected the touchpad bind
because its stable by-path contains `:`. V3 now requires the stable links to
resolve exactly to current `event3`/`event11`, then uses those colon-free source
paths for fixed internal `event0`/`event1`. Current v3 plan digest:
`83750219fbf0f0ac0569ba8965849c3f42b98235fa81ca6149f730b912f05eed`.

Physical v3 then passed the bounded technical H0 run: timer-before-graphics,
machine observed, transient seatd accepted UID 1000, unprivileged Hyprland
observed for the full 45-second window, tty1 restored, machine/mount residue
absent, units inactive, and APX healthy. Sanitized result:
`docs/hyprland-h0-physical-result-2026-07-18.json`. Do not yet claim visual or
input acceptance until the owner reports what appeared. Follow up the blocked
absent-card1 enumeration and create the missing Environment-local `/home/apx`
before daily-use work.

The current home gap is fixed: Environment-local `/home/apx` and `.cache` are
mode 0700, UID/GID 1000, inside the separate 8 GiB home. Runtime source now
creates this automatically for future graphical Environments; this latest
runtime source is not installed yet. APX remains healthy/stopped. Visual/input
owner observation from v3 is still required before claiming graphical H0 user
acceptance.

When the owner returns with results:

1. preserve the raw result outside Git if it contains secrets or unnecessary
   machine identifiers;
2. redact and map the evidence into the four audit classifications;
3. update this file and `PROJECT_STATE.md` with verified facts only;
4. decide whether Phase 9 quota recovery is still required;
5. decide whether Phase 10 cleanup is ready;
6. produce an exact cleanup plan but do not execute it without separate owner
   approval;
7. confirm the installed Ollama service-data path before accepting
   `/var/lib/ollama` in an external-SSD adapter.

## Current Repository Milestones

The repository currently has:

- a post-battery-loss read-only observation with no failed units, no registered
  machines, no graphical session, and only the expected active pilot executor;

- a role-aware APX control model: full lifecycle management only in the Hub,
  with return-to-Hub and read-only status controls in workload Environments;
- executor-level Hub authorization based on trusted active-session evidence,
  including refusal of forged/non-Hub management and sibling-stop requests;
- a pure APX-control launcher decision that binds the active graphical session
  to verified registration and passes a derived role to the local UI only;
- a laboratory runtime boundary that reserves Hub roles for logical name
  `hub` across creation, registration reads, and restore, and copies only the
  three digest-bound graphical configuration assets into a new independent
  home;
- a Hub-only, generation-bound optional capability plan for camera,
  microphone, controller, and removable storage, all absent by default and
  changeable only while the target is stopped with explicit confirmation;
- a production Hub-client pre-freeze gate that cannot itself admit the current
  GTK demonstration into a release;
- an effect-free exclusive Hub/workload/Hub handoff state machine and fake
  executor, including failure injection at every stage and terminal
  broker-owned recovery;
- exact typed intent binding from Hub controls to the executor catalogue and a
  self-generation-only workload return intent;
- a bounded production executor-v1 Unix client and endpoint core with trusted
  authority injection, atomic nonce reservation, and incomplete classification
  after post-reservation adapter failure;
- an effect-free integrated button/executor/broker round trip that finishes in
  `hub-active`, plus an explicit physical manual-test assessment that remains
  blocked on the absent graphical release/client/install/adapters and H0 lock;
- corrected fail-closed Btrfs quota parsing in both original bootstrap sources;
- guarded physical Development quota recovery release v3;
- a detailed physical state and cleanup audit;
- a pure external-model-store evidence validator;
- a closed model artifact manifest;
- a deterministic, non-executing SSD attach preview;
- a pure attach, activation, detach, interruption, and recovery journal;
- a pure physical-pilot update candidate and installed-evidence validator;
- a separate-import/separate-activation update preview;
- an ordered update journal that retains the previous version for rollback;
- a closed non-extracting physical-update artifact manifest and reader;
- reconciled update gates for the intentional simple Development plus current
  root-host-mode inventory;
- a pure H0 clean-host Hyprland readiness, preview, journal, and recovery
  contract;
- the 800-test suite succeeds in the root-host checkout with eleven expected
  external-fixture or privilege-context skips. One test fixture was corrected
  so subordinate-UID
  behavior no longer depends on the UID running the suite.

The external-model-store code cannot format, unlock, mount, bind, download,
start, stop, detach, or remove anything. Physical adapters remain blocked on
the audit and later target-bound approval.

## Work That May Continue Without the Audit

Safe repository-only work may continue on:

- the closed physical-pilot update bundle and rollback contract;
- pure schemas, previews, journals, and hostile-input tests;
- minimum-privilege effect mapping as documentation;
- production trust, broker, authentication, and executor design;
- documentation consistency and test coverage.

Do not implement an external-SSD mount adapter, assume the Ollama data path,
create a new physical install/update tag, or instruct physical cleanup before
the audit is reviewed.

## Immediate Repository Milestone

The pure part of the physical update contract is now implemented in
`src/apx_physical_update.py` and `src/apx_physical_update_journal.py`, with the
plain-language contract in `docs/physical-pilot-update-contract-v1.md`. It binds:

- current installed identity and expected revision;
- exact update artifact and member manifest;
- tests and compatibility evidence;
- explicit consequences and approval separation;
- ordered staging, verification, activation, rollback retention, and recovery;
- refusal on stale state, changed machine identity, uncertain APX operation,
  missing recovery, or mismatched Hub/Development generation.

No real host update is authorized by this milestone. The next repository work
may define the exact update member manifest and minimum-privilege adapter
boundaries, but physical adapter code and a release tag remain blocked until
the audit is reviewed.

The independent graphical milestone is now the H0 clean-host contract in
`src/apx_hyprland_h0.py`, `src/apx_hyprland_h0_journal.py`, and
`docs/hyprland-h0-clean-host-v1.md`. It is pure only: no graphics or devices are
changed. After the audit, the next graphical work is an H0-specific read-only
capture of AMD connector/card/render identities, built-in input identities,
VTs, and the installed graphical-role gap.

## Hard Stops

- The working computer remains an experimental physical pilot, not production.
- Formal recovery-retirement work remains paused. The owner-authorized Host
  simplification described below has run without removing recovery design.
- Local model installation is pinned as a future-only milestone and is not a
  Phase 10 prerequisite.
- The external SSD has not been selected, inspected, formatted, or attached.
- Do not use `sudo` or modify the host from an ordinary repository session.
- Root-host modification is allowed only after the owner explicitly invokes
  `docs/temporary-root-host-development-mode-v1.md` on the identity-matched
  physical pilot; it is not standing permission in Development or other chats.
- Do not commit or push unless the owner explicitly asks; the owner has asked
  the current development sequence to be published, but future sessions must
  evaluate their own request context.

## Latest Graphical Checkpoint

The physical Host now has a twice-reproduced immutable `hyprland-base-v1`
release with 402 packages. The stopped real logical Environment `test` exists
as generation `69b56acc-fd4d-4499-8009-e1d0108466f4` and derives the runtime
machine name `apx-test`. The earlier incorrectly doubled logical name is
preserved under quarantine rather than deleted. The current Environment has
seven independent configuration assets. Its actual
Hyprland config returned `config ok` inside a device-free validation and the
Host has no failed unit. No graphical session was launched.

The closed desktop client is now installed into `test` and a separate stopped
graphical Hub candidate. It reads only `/run/apx/session-ui-v1.json`, accepts
only Host-issued typed activate/return requests, and refuses caller-supplied
roles, commands, paths, or management from workloads. The current headless Hub
registration remains unchanged. The immediate milestone is the Host descriptor
issuer plus independent recovery-bounded broker/device adapter required for the first
real `hub -> apx-test -> hub` visual test. Do not bypass those gates by directly
starting Hyprland; the previous H0 code lock remains active.

The accepted storage policy is now flexible shared capacity, not configurable
per-Environment caps. Repository creation contracts protect a 32 GiB global
Host/recovery reserve. The old physical leaf limits have deliberately not yet
been removed: first install and verify a hierarchical shared-pool guard, then
remove the leaf caps atomically with rollback evidence.

The Host session issuer and first physical round-trip plan are now closed and
tested. The latest real read-only observation verified tty1 active, tty2
unused, connected card2-eDP-2, exact AMD/input identities, no graphical owner,
no display manager, no failed unit, no machine, no uncertain APX operation,
present Hub candidate, and stopped `test`. The exact recovery-bounded plan
digest is
`7603c8d17c787ed4122cff9520f49392c0865412967b5a53e9b595ff8dec43f3`.
No devices or graphical process were activated. Next implement and rehearse the
effect adapter with a harmless dummy unit before publishing the graphical Hub.

That milestone is now complete. The harmless Host timer rehearsal passed, and
the real stopped `test` passed two-level recovery plus structured machine,
Hyprland, Wayland, Waybar, `eDP-2`, tty1, and zero-residue evidence. The
graphical Hub is now the stopped registered Hub at generation
`2c3dbacc-106f-4053-8603-f649552f5513`; the complete old headless Hub is retained
at `/var/lib/apx/quarantine/retained-hub-headless-v3-d68ee7a2`. Next rebuild the
round-trip plan against this published generation, then perform a bounded Hub
visual launch before enabling button-driven switching.

The rebinding is complete. Current published-Hub round-trip plan digest:
`2def2bb58aeb6aa3b15cfd7764421c94e94cbd1c092fccddefcf7eeb3787c64f`.
The previous `7603...` plan is retained only as evidence of the successful
pre-publication `test` run. The current next action is the bounded Hub visual
launch; the executor-v1 socket still must be installed before button switching.

Executor installation review found that its tested generation field is an
integer but physical Hub/test registrations use UUIDs. Do not install or bridge
the socket by truncating/hashing those UUIDs. The immediate repository task is
an exact UUID-capable executor protocol (or explicit durable serial binding),
followed by replay/stale-generation tests and only then local socket install.

The UUID protocol gap is resolved in source and focused tests: physical UUIDv4
generations are transported exactly, while malformed/truncated/uppercase and
stale bindings are rejected. No conversion or hash mapping is used. The next
immediate task is the atomic plan/approval/nonce store plus Unix peer
authentication; `/run/apx/executor-v1.sock` remains deliberately absent until
that server can reach only the generation-bound broker adapter.

The atomic executor store is complete and its empty root-only physical
directories now exist at `/var/lib/apx/executor-v1/{plans,approvals,nonces}`.
Immutable plan/approval records, symlink/type/owner/schema/digest checks, and
single-use nonce reservation pass. The store contains no authorization yet.
Next implement Unix peer-to-active-machine authentication and the socket
wrapper; do not start the service with a permissive or no-op effect adapter.

Unix peer authentication, bounded framing, transport, and authority composition
now pass. Peer PID/UID/GID, cgroup unit, active-session record, registration
role/name/UUID/running state, current target generation, nonce state, plan, and
approval are all independently rechecked. The code opens no network port.
`executor-v1.sock` is still absent by design: next implement the real
generation-bound activate/stop effect adapter and only then install the service.

The published Hub itself now has structured physical visual evidence:
`apx-hub`, Hyprland, Wayland, Waybar and `eDP-2` all appeared under the 15-second
Host watchdog, then tty1 and zero residue reverified. Both Hub and `test` can
therefore render safely. The remaining task is no longer compositor readiness;
it is persistent active-session publication plus the executor effect that
stops one exact unit and starts the other before returning success.

## Owner-authorized minimal Host cleanup — 2026-08-03

The physical Host now retains only the running `hub` Environment. Seven
stopped development/test Environments were destroyed through the installed APX
lifecycle (`development`, `hub-testes`, `test`, and four `codex-test-*`
fixtures). Superseded Hub v1/v3 releases, the experimental H0 release and
evidence, quarantine trees, old installed-file backups, two obsolete clean
repository copies, loose staging files, the pacman cache, and archived journal
excess were removed. The current repository, Codex state, official Hub v4,
current development/minimal/Hyprland creation bases, APX journals and plans,
and all active shared-service implementations remain. Host explicit packages
remain at 16 with zero orphans because every one has a current boot, hardware,
APX creation, Hub graphics, networking/Bluetooth, or development purpose.

The cleanup reduced used Host storage from about 8.7 GiB to 6.1 GiB. Host
systemd is running with zero failed units, the Hub/Hyprland and all APX Host
services remain active, and Wi-Fi, Bluetooth, time and audio state passed live
authenticated checks. The update repository-permission defect discovered in
the retained failed dry run was fixed and a signed database-only synchronization
passed without installing packages. Because restarting the coordinator changes
the Unix socket inode, the currently running Hub still holds its old bind mount;
relaunch the Hub once after closing the present Host-console/Codex session.
Future launches bind the corrected live socket normally.

## Captive portal extension — 2026-08-03

Host Shared Services v3 now has source and installed support for RFC 8910
CAPPORT announced through DHCPv4, DHCPv6 or IPv6 Router Advertisements, RFC
8908 CAPPORT, bounded Arch HTTP probing, structured
`unknown/none/limited/portal/full` state, explicit recheck and a Host-selected
portal URL. The Hub has WebKitGTK/Python GObject and a single-purpose ephemeral
APX Wi-Fi login window; it has no Chromium, Firefox, browser desktop entry or
persistent web profile. The live normal-network and systemd-sandbox checks
returned `full`, the isolated window rendered under the current Hyprland
session, and focused privacy/timeout/false-positive tests pass. See
`docs/host-wifi-captive-portal-v1-physical-result-2026-08-03.md`.

The new `apx-host-services-v3` daemon is active and stable. Its new Host socket
has a different inode, while the running Hub intentionally retains the old
file-bind inode. The updated source, unit, client, UI adapter, Quickshell
controls and Hub packages are installed. Close this Host-console session and
restart only the Hub once; it will mount the new v3 socket normally and no Host
reboot is required.

## Active Lenovo profile controls — 2026-08-04

The battery menu is live with the two firmware-backed GPU choices supported by
this exact `82JU`: Híbrido and NVIDIA. The nonexistent iGPU-only/AMD choice was
removed. Quiet, Normal, and Performance map to Lenovo platform-profile and
apply without reboot; GPU staging displays a warning and needs reboot.

`apx-system-power-v1.service` is running the new hardware-profile authority.
The current Hub's stale `/run` file bind is bypassed through the root-owned
`/home/.apx-host-bridge/system-power-v1.sock`; authorization is unchanged and
GPU writes still require the direct Quickshell parent plus a 30-second,
single-use Host token. An authenticated Hub read returned Hybrid/balanced and
the exact two-mode catalogue. No firmware setting was changed during the fix.

The complete pre-profile Quickshell was restored at the owner's request after
an audit proved that the first profile integration had used a stale, shorter
shell. Calendar midnight tracking, popup dismissal and animations, microphone
volume/mute, volume mute, and the complete control centre are present again.
Only the Lenovo hardware-profile blocks and the live authenticated power
transport differ from the 06:56 backup. Quickshell reloaded without warnings,
the calendar store was preserved, and all 20 focused tests pass.

The restored control centre additionally exposes an internal-screen brightness
slider. It applies continuously throttled updates while the thumb moves, and F5/F6 call the
same mediated operation. The slider remains enabled while writes are in flight,
uses the same visual dimensions as the compact volume slider, and its leading
keyboard-light icon cycles 0/1/2 like Fn+Space. This compact control replaces
the removed full-width “LUZ DO TECLADO” status button and shows those states as
dim/off, cyan/intermediate, and cyan-filled with a white icon/maximum. The privileged service
still admits only the fixed `amdgpu_bl2` and
`platform::kbd_backlight` controls. Microphone mute now reads back
`@DEFAULT_AUDIO_SOURCE@` from the actual Hub PipeWire session, preventing the
old Host `input_name=null` poll from visually undoing mute. F1–F4 now enter
through Quickshell IPC, update the visible state immediately, and then confirm
the operation through PipeWire. F10 toggles the exact ELAN touchpad, and
PrintScreen saves through `grim` under `Pictures/Screenshots`. F8 remains the
firmware/kernel RFKill path and is not replaced by a connection-only toggle.
Lenovo F5/F6 are handled by a Quickshell-owned exact-input bridge after both
keysym and raw Hyprland bindings failed to receive them. It opens only the
already-admitted ITE and AT internal keyboards, accepts ITE brightness codes
224/225 or the Legion F5/F6 fallback 63/64, and calls the same shell methods as
the slider so the visible bar and panel change together.

## Local-model SSD control handoff — 2026-08-05

The external model store is active, read-only and serving `qwen3-coder:30b`.
The end-to-end safe-detach/reactivate cycle passed: detached means no Ollama,
mount or LUKS mapper and a mode-`000` Host mountpoint. The authenticated control
daemon is enabled. The current Hub reaches it through the root-owned live
bridge and reports the model as active; later launches use the normal leased
`/run` binding. No Hub restart is required. The UI now separates model
start/stop from SSD mount/safe-unmount, and the four-state lifecycle passed.

## Control-centre dismissal fix — 2026-08-13

The Hub menus have their original anchored-popup behaviour again: Calendar,
Control Centre, IA, Battery and Environments open below their respective bar
buttons instead of becoming centred layer-shell panels. Clicking outside
dismisses them, while Escape and the existing bar toggle remain alternatives.
The corrected QML is live in the running Hub and the shell tests pass.

The anchored menus also have direct keyboard toggles: `SUPER+A` opens Control
Centre, `SUPER+D` Calendar, `SUPER+I` the Hub IA/model menu, and `SUPER+B`
Battery. Firefox remains available on `SUPER+SHIFT+B`; the application launcher
remains on `SUPER+R`.

The intermittent blank Host-console reattachment was traced to the broker
discarding terminal-rendering bytes after delivery to the previous Kitty
window. The updated broker retains a bounded replay stream, resets and
reconstructs a replacement terminal, then requests a foreground redraw. The
code is installed, but the running broker intentionally remains untouched to
preserve the current Codex conversation; it becomes active when this Host
console session ends and the service is subsequently restarted.

## Environment creation menu and deletion — 2026-08-13

The Hub Environment menu now opens without selecting or keyboard-highlighting
an Environment. The creation screen likewise starts without a focused control
and with all four capability drawers closed; the Intermediate profile remains
the recommended preconfigured value, independently of keyboard focus. Arrow
keys begin and move navigation, Enter activates rows, presets, drawers,
capability toggles and actions, Tab/Shift+Tab traverse the creation form, and
Escape returns to the previous menu. The QML is live in Hub, Work and Jogos and
is also installed in the seed for future Environments. QuickShell reloaded the
configuration successfully.

Destroy is now idempotent for the exact completed target and generation. A
duplicate request caused by stale UI state returns success instead of reporting
that an already removed Environment is unregistered, while other missing or
mismatched targets remain refused. The service is active with the corrected
implementation. The complete suite passes: 1026 tests, 11 skipped.

Profile and module navigation is now spatial rather than one-dimensional.
Left/right moves only between Basic, Intermediate and Complete (and between
two module columns); up/down leaves the profile row for the control visibly
above or below it. The failed `bola` creation was traced to a temporarily
mismatched shell-seed digest during the preceding live update. Its unpublished,
stopped residue was removed through the journal-gated recovery command and no
uncertain operation remains. An exact retry of a name with a similarly proven
failed unpublished residue now recovers it automatically; arbitrary existing
paths remain refused. The transient failure state was returned to idle.

The owner's subsequent complete-profile `bola` creation exposed two real
physical-only assumptions. First, the running Hub's private-user mapping makes
its on-disk root owner the active ID shift rather than Host UID 0. Password
inheritance now anchors the fixed Environment directory at Host root, then
requires `root`, `etc` and mode-0600 regular `shadow` to share the exact
Environment-root owner; reads and writes use no-follow file descriptors and
bounded sizes. Second, pacman 7's `alpm` downloader cannot traverse the
mode-0700 Environment pool during an alternate-root installation. The closed
package invocation now uses pacman's explicit `--disable-sandbox` downloader
mode while retaining the exact Environment `--root`/`--dbpath` and signature
policy.

`bola` was recovered and recreated end to end as requested: description
`Pomba`, profile Complete, all 18 modules, generation
`fc8d4191-1cf9-474d-a873-018eb98518db`, state stopped. Firefox, LibreOffice,
FFmpeg, CUPS, Podman, Rust, Node/npm, SANE and the selected supporting packages
are registered locally. The `apx` account is password-enabled, in `wheel`, has
the local sudo policy, and its password hash exactly matches the active Hub.
No uncertain operation remains. The complete suite passes: 1028 tests, 11
skipped.

## Graphical Environment automatic-return resolution — 2026-08-18

The unexpected Environment-to-Hub return is resolved in the physical pilot.
Do not continue timer/watchdog debugging unless the symptom is reproduced.

The definitive fault was a stale common graphical engine at
`/usr/lib/apx/apx-official-hub-graphical-v1.py`.

The workload wrapper selects that adjacent engine before the `/var/lib`
fallback. The stale copy expected the obsolete `/run/user/1000` Hyprland
runtime, while current APX graphical sessions use `/run/apx/session-1000`.

Live investigation proved the affected `faculdade` Hyprland process was
healthy: correct cgroup, valid `.socket.sock`, successful `hyprctl` monitor and
device queries, active `eDP-1`, and two keyboards.

The `/usr/lib` copy was synchronised with the current repository and
`/var/lib` engine. All three then matched SHA256
`3ea93c79492b9b3b6808f980e1c9dd11a9bef2c2b80fa917a77975b41a31f0d4`.

The following interactive `faculdade` run remained stable.

The 120-second failsafe, Hypridle, explicit return, missing input/display and
Hub watchdog recovery were ruled out.

Next development focus: improvements to the Environments themselves.

Later hardening should remove or validate duplicate engine deployment paths
and add direct runtime-contract tests.

Detailed incident:
`docs/environment-handoff-runtime-readiness-fix-2026-08-18.md`.

## System Environments and Faculdade VFIO — 2026-08-23

The Hub creator now offers Arch native, Windows 11 system, and Ubuntu system
choices. The authenticated wire contract, management runner and atomic
provisioner carry the selected system kind; catalogue rows show small Windows
or Ubuntu tags. System disks, firmware, media, configuration and trusted
markers live under the Environment lifecycle, and failed provisioning invokes
the normal full destroy plan.

The Host boot has IOMMU enabled and the RTX 3060 graphics/audio pair is alone
in group 11. A signed KVMFR module, B7-799 client and matching Windows Host/IDD
installers are staged. VFIO bind and restore pass. At compositor level,
`SUPER+E` and `SUPER+M` return directly to Hub even during guest reboot or a
black frame; `SUPER+SHIFT+E` opens the APX-styled blue menu.

Do not trigger Environment transitions automatically while a Codex session is
active. Two failed-closed attempts repeatedly interrupted the owner. The final
diagnosis was a stale `/usr/lib/apx/apx-official-hub-graphical-v1.py` shadowing
the canonical engine after VFIO bind. The generic launcher now selects the
canonical `/var/lib` engine explicitly and the duplicate installed copy is
synchronised. The owner should perform the next visual launch manually.

That manual visual launch reproduced a two-stage failure. The `faculdade`
session exited immediately because the shared session script still accepted
only `amd|hybrid|nvidia` even though the Host launcher had correctly selected
the new `vfio-guest` policy. The recovery Hub then ran normally with Hyprland
and QuickShell, but was terminated about 25 seconds later by the new IPC
fallback loop: it made the whole session depend on a redundant dispatch return
even when the Lua callback had already started the owner shell.

The repository session contract now admits `vfio-guest` only together with
`virtual-machine`, observes an already-running owner workload before issuing
the duplicate-safe IPC fallback, and leaves final workload readiness to the
existing Host-side authoritative proof. Do not attempt another visual launch
until the live `/var/lib` session copy is updated; this turn did not explicitly
invoke the temporary root-Host development guide. After installation, the
owner should again initiate the launch manually.


Latest physical audio repair — 2026-08-18: shared internal analog playback was
traced through Environment-local PipeWire to the leased ALC287 PCM. The failure
was below PipeWire: the Host ALSA `Master Playback Switch` was off even though
the Speaker/Headphone per-route controls were on. Enabling the Host master
changed the physical HDA output pins from muted `0x80` to enabled `0x00`.

The common graphical engine now calls Host-owned
`ensure_audio_master_playback()` after exact audio identity/device validation
and before device-lease preparation. It uses the raw ALSA control interface via
`libasound.so.2`, requires the exact boolean `Master Playback Switch`, enables
and verifies it, and fails closed otherwise. Environment-local PipeWire remains
the authority for logical volume/mute; Environments gain no new physical mixer
authority.

Timezone correction — 2026-08-18: trusted network `Casa` now maps to
`Europe/Lisbon`, replacing the incorrect `America/Sao_Paulo` mapping. The Host
remains authoritative and graphical Environments inherit `/etc/localtime`
through `--timezone=bind`.


## APX 2026-08-18 final desktop/time/audio checkpoint

The physical internal-audio failure is closed. The Host graphical lifecycle
now enables `Master Playback Switch` and raises `Master Playback Volume` to the
codec's neutral hardware maximum before the narrow ALSA device lease. The owner
physically confirmed audible output. Environment-local PipeWire remains the
logical volume/mute authority.

The Host and active Hub are both on `Europe/Lisbon`; the QuickShell clock was
physically observed at the correct local time after the active Hub's stale
`/etc/localtime` link was repaired. New graphical lifecycles use
`systemd-nspawn --timezone=bind`.

QuickShell popup opening animations are owner-approved. The control-centre
output-volume slider now previews its percentage immediately and applies
coalesced real PipeWire volume changes continuously while being dragged, with
the exact release position guaranteed as the final write.

## Active handoff — native Windows reservation, 2026-08-25

Normal Environment creation is physically repaired and proven. The special
catalogue entry `Windows` / `NATIVO` is installed and currently returns
`state=preparing`, `display_name=Windows`; it cannot be opened or deleted yet.
The physical reservation is complete and finalized. The signed offline UKI
recorded `success:128849354240`; GPT p2 is 746457088 sectors, dm-crypt is
746424320 sectors, Btrfs is 382169251840 bytes with zero slack, and the exact
120 GiB tail is unallocated. Current Btrfs write/read/flush/generation counters
are zero. `/var/lib/apx/native-environments/windows-storage-v1.json` is
root-owned mode 0400, and the catalogue description now confirms the reserved
storage.

The owner has no USB drive. An internal installer is therefore complete: p3 is
a 9-GiB FAT32 ESP named `APX_WINSETUP`, with verified Microsoft-signed Windows
Setup files and three split SWM parts; the exact preceding 111 GiB is still
unallocated for Windows. `Boot0003 APX Windows Setup` targets p3, is not in the
unchanged permanent BootOrder `2001,0005,0000,2002,2003`, and no BootNext is
armed. Secure Boot remains enabled with both original APX trust and the needed
Microsoft authorities. Direct verification of all APX EFI loaders succeeds.
The complete repository suite passes 1076 tests with 11 expected skips.

The partition-selection tutorial and post-install return procedure are in
`docs/native-windows-physical-120gib-v1-2026-08-25.md`. The corrected next
action is recorded below after the completed WinPE diagnosis.

Owner-driven boots reached the current Windows Setup UI, but Setup then showed
`Install driver to show hardware`. Every attempt returned to APX without a GPT
or filesystem change; the exact 111-GiB hole and APX partitions remain intact.
Firmware-created fallback duplicates for p3 were identity-checked and deleted,
and the exact APX BootOrder was restored.

The target storage is a directly attached Samsung PM981/SM981-class NVMe
controller `144d:a808`, class `010802`, with AMD SATA in AHCI mode and no RAID
or VMD layer. Lenovo's 82JU Windows 11 catalogue has no RAID/RST storage driver.
The exact Setup boot WIM contains Microsoft's signed `stornvme.sys` and an INF
matching `PCI\CC_010802`. The diagnostic boot returned `0x80070103` when
reloading that INF, while DiskPart successfully showed Disk 0 at 476 GB with
111 GB free. Storage discovery is therefore working. All three SWM parts and
all 11 images also passed complete cross-part verification.

The actual failure was source-media discovery: WinPE booted from the internal
ESP but assigned no drive letter to it, after which Setup emitted the generic
multimedia/DVD/USB/disk-controller prompt. The first custom WinPE attempt used
DiskPart `assign`, but physical boot entered its recovery console because that
command cannot assign a letter to a GPT partition other than a basic-data
partition. The owner closed the console and WinPE returned safely to APX.

The deployed v2 Setup-index WinPE runs `wpeinit`, scans existing letters and,
if needed, invokes the ESP-specific `mountvol W: /S`. It checks `setup.exe` and
all three SWMs before launching Setup and uses no DiskPart. There is no
partition create/delete/clean/type-change/format instruction. The installed
WIM and embedded files passed full verification; SHA-256 is
`b4041a17b34aca0db72e32eb1bcd7d675354f600d4b79efb2ab4a8af8dcb5df2`.
The fixed boot validator has been updated and passes `--validate-only` without
arming a boot. No BootNext exists and permanent BootOrder remains
`2001,0005,0000,2002,2003`.

That installer action is complete and is superseded by the OOBE handoff below.

## Active handoff — Windows OOBE Wi-Fi and Linux-first boot

The v2 media path worked and Windows Setup applied the image using only the
reserved tail. Current physical layout is APX p1/p2 unchanged, Windows MSR p3
16 MiB, Windows NTFS p4 110.2 GiB, Windows Recovery p5 790 MiB and the former
internal setup ESP as p6 9 GiB. Windows Boot Manager entry 0006 targets p6.

OOBE stopped only at network discovery. Physical Wi-Fi is Realtek RTL8852AE
`10ec:8852`, Lenovo subsystem `17aa:4852`. Official Lenovo Windows 11 package
DS551503 was downloaded and matched its published SHA-256
`1defff5645c18427c5f1af5af07a0ebae1dde25c70c3624869d485cef06f0c04`.
The extracted Realtek 6001.0.10.340 INF contains exact ID
`PCI\VEN_10EC&DEV_8852&SUBSYS_485217AA`; its catalogue identifies Microsoft
Windows Hardware Compatibility Publisher. Only its INF, CAT, SYS and data file
were staged at `C:\APX\Drivers\Realtek8852AE`, then verified after a read-only
remount. No existing Windows file was replaced.

Permanent UEFI BootOrder is `0005,0006,0000,2001,2002,2003`, Linux first and
Windows second. There is no BootNext. The one-shot OOBE executor
`scripts/physical-pilot/boot-native-windows-oobe-v1.sh` passes validation of
hardware, GPT, p4/p6 identities, Secure Boot, Windows Boot Manager/BCD and all
staged driver hashes. Complete suite: 1078 tests, 11 expected skips.

Next exact action: after a new owner readiness confirmation, run the OOBE
executor with `--reboot`. On the OOBE network page select `Instalar
controlador`, browse to `C:\APX\Drivers\Realtek8852AE`, confirm the folder,
connect to Wi-Fi and finish OOBE. If a Windows restart returns to APX before
the desktop, use a new exact one-shot Windows handoff. After desktop proof,
publish `Windows · NATIVO` as ready and change the installed native runner from
the obsolete same-ESP `bootctl auto-windows` design to validated firmware
BootNext entry 0006. `SUPER+E` cannot cross operating systems; returning from
Windows is a normal restart to the Linux-first firmware default.

The owner selected that folder, connected to Wi-Fi and saw Windows continue
installing before its restart returned to APX. Offline verification confirms
`netrtwlane6.inf` is now installed in the Windows DriverStore with the exact
Lenovo RTL8852AE ID. There is no new OOBE/setup error at that timestamp. The
Windows Boot Manager executable is unchanged and signed; BCD changed normally
during the continuation. The OOBE executor is now safely repeatable: each
attempt records the current bounded BCD digest and firmware state in a new
non-overwriting slot, while permanent BootOrder stays Linux-first. It passes
`--validate-only`; no BootNext is armed. Next action is one more owner-approved
`--reboot` to Windows entry 0006 so OOBE resumes where it stopped.

## Current handoff — native Windows and APX face authentication ready

The preceding OOBE instruction is superseded: Windows 11 is fully installed and
functional. `Windows · NATIVO` is ready in the HUB. The installed runner uses
firmware BootNext 0006 only after validating the exact physical storage and the
signed Windows manager; permanent firmware order remains Linux 0005 first and
no BootNext is armed. The Windows return helper is staged invisibly in Common
Startup without a Public Desktop icon: `SUPER+E` restarts to the Linux-first HUB, with
`SUPER+SHIFT+E` as the initial Explorer-policy fallback.

Repeatable native Windows create/delete is installed. The HUB accepts one
instance at 80/120/160 GiB and uses a signed offline lifecycle UKI. Delete is
strictly bound to the expected p3-p6 identities/layout and returns space through
the boot-time finalizer. Source and installed shell hashes match, the current
native validator passes, and all 1087 tests pass with 11 expected skips. Do not
claim the destructive real-NVMe lifecycle has been accepted: it has only been
rehearsed with disposable GPT storage because exercising it now would erase the
working Windows installation.

The owner changed the Hub password locally. Four stopped graphical
Environments and Host `root` were synchronized from that protected hash with
atomic replacement and mode-0600 backups; no secret or hash was printed. The
Host console and Hub now use the same password.

The Lenovo camera is admitted to the Hub by its full immutable udev identity;
only `/dev/video0` capture is leased. Howdy native PAM and CPU-only dlib are
installed from pinned repository PKGBUILDs, the local `APX-owner` model is
mode 0600, snapshots and SSH face auth are disabled, and the normal password
stack remains the fallback. A raw recognition test, a real owner `sudo`, and a
real `hyprlock` cycle all succeeded physically. Rollback is
`/var/lib/apx/backups/20260825T171900Z-face-auth-pam-v1`; the earlier camera
launcher backup is `/var/lib/apx/backups/20260825T175200Z-face-auth-v1`.

The native Windows row is openable again. Its first post-install menu attempt
never reached `native.boot`: the capability-empty switch service called the
full validator from its catalogue path, and the validator's read-only mounts
were correctly denied inside that sandbox. The catalogue now trusts the exact
root-owned mode-0400 `ready` marker only for presentation; the privileged
one-shot boot runner still revalidates all physical storage, UEFI and signed
Windows content before arming BootNext. The active catalogue returns `ready`,
the full validator passes, BootNext is absent, and the switch service has no
added capability. Close and reopen the Environments panel before the next
owner click so QuickShell reloads the corrected catalogue. Rollback:
`/var/lib/apx/backups/20260825T173000Z-native-windows-menu-ready-v1`.

The owner physically accepted Hub → native Windows and the explicit Windows →
Hub return. Return v2 is now installed offline in the current Windows: there is
no APX icon on the Public Desktop, while a hidden supervised Common Startup
helper owns `SUPER+E` (`SUPER+SHIFT+E` remains the first-login fallback) and
retries registration if Explorer is not ready. Future create media includes
the same assets and runs the official Lenovo RTL8852AE driver through
`SetupComplete.cmd`/`pnputil` automatically. A generation cannot become
`ready`, and cannot later open, unless its exact background helper exists, the
old icon is absent, and DriverStore contains an INF matching the Lenovo
`PCI\VEN_10EC&DEV_8852&SUBSYS_485217AA` identity. Windows Update remains
responsible for current AMD/NVIDIA and other optional vendor revisions once
network is available; programs and owner data are never cloned. Current
validation and all 1087 tests pass; BootNext is absent and no unit is failed.

## Current handoff — editable Environment presentation

The live Hub menu now exposes `EDITAR` after selecting any stopped Environment
or ready native Windows entry; `F2` opens the same form. It changes only the
visible title and optional legend. The internal name, generation, system type,
partitions and data do not move or change.

The request is generation-bound and admitted only from the active official Hub
QuickShell. The separate root-owned writer validates the exact protected record
and atomically changes only `display_name` and `description` under a transient
no-capability sandbox. This applies to ordinary Environments and Windows; the
native boot validator continues to enforce every disk/UEFI/driver/return-helper
identity independently of the chosen display text.

QuickShell loaded the live source cleanly at 19:50:54, the future seed and
installed runtime are source-exact, and a same-value `faculdade` write passed
the real protected runner. All 1088 tests pass with 11 skips, all relevant
services are active, Windows validation passes, no BootNext is armed and no unit
is failed. The remaining manual acceptance is one owner-selected edit in the
menu. Latest rollback:
`/var/lib/apx/backups/20260825T185053Z-environment-metadata-edit-v1`.

## Current handoff — first physical delete attempt safely refused

The owner's first `Windows · NATIVO` delete request on the real NVMe did not
reach maintenance and did not change storage. The signed-UKI builder correctly
refused because its repository working-directory invariant was not supplied by
the transient lifecycle runner. There was no reboot, BootNext, pending marker,
maintenance UKI or GPT change; the existing Windows remains `ready` and its
four physical partitions remain intact.

The lifecycle runner now executes every fixed command with the validated
repository as its explicit working directory. A regression assertion and an
installed-runner mock exercise cover that boundary. The live delete preflight
passes against the exact 120-GiB generation, Linux remains BootCurrent/default
and first in BootOrder, no operation is pending, and the full suite passes 1089
tests with 11 expected skips. The owner may retry the same delete from the Hub;
do not trigger it automatically. Rollback:
`/var/lib/apx/backups/20260825T222335Z-native-windows-lifecycle-cwd-fix-v1`.

## Current handoff — physical delete reached initrd and safely refused

The next owner retry successfully built and booted the signed maintenance UKI,
but the offline executor refused at `msr-type` before its first `blkdiscard`.
On util-linux 2.42.2, cached `blkid -s PART_ENTRY_TYPE` returns no value for a
partition device; direct low-level probing requires `blkid -p`. The real GPT
types, starts, sizes, filesystems and identities all remain exactly correct.
Windows p3-p6 and the shrunken APX p2 were unchanged, so the Windows row still
correctly remains present.

All four partition-type gates now use direct probing. The exact failed pending,
status, UKI and entry artifacts were backed up and removed only after validating
that no disk change occurred. A freshly built signed UKI was then extracted and
its embedded executor was proven to contain all four corrected probes; the test
UKI/entry were removed without arming BootNext. AC is online, battery is 49%,
Linux remains first/default, no unit is failed, and all 1089 tests pass with 11
expected skips. The owner must explicitly retry delete in the Hub. Recovery
backup: `/var/lib/apx/backups/20260826T143302Z-native-windows-msr-probe-refusal-v1`.

## Current handoff — physical native Windows deletion accepted

The owner retry completed the destructive offline stage successfully: p3-p6
were discarded and removed, p2 returned to 511035383296 bytes, dm-crypt reopened
at 511018606080 bytes, and the success marker was exact. The boot-time finalizer
initially stopped because `cryptsetup resize` was redundant after systemd had
already reopened the enlarged mapping and attempted to read authentication from
the noninteractive service. Btrfs was grown explicitly to its aligned maximum
of 511018602496 bytes (3584 bytes of unavoidable 4-KiB alignment slack).

The finalizer now requires the already-full dm-crypt size instead of invoking
interactive resize, then performs idempotent `btrfs filesystem resize 1:max`.
Its successful rerun removed pending/native metadata, storage marker, lifecycle
status, maintenance UKI/entry, Windows Boot Manager and APX Setup firmware
entries. BootOrder is Linux-first without BootNext, no unit is failed, the APX
storage summary contains no Windows and reports 450096533504 bytes available.
The Hub completion state is `Windows apagado; todo o espaço regressou ao APX.`
All 1089 tests pass with 11 expected skips. Physical delete is now accepted;
physical recreate/install remains the next owner test. Finalization backup:
`/var/lib/apx/backups/20260826T144156Z-native-windows-delete-finalize-v1`.

## Current handoff — lifecycle is now self-contained and resumable

The owner rejected a workflow that depended on Codex manually completing the
last steps. The installed native-Windows lifecycle no longer reads executable
assets from the development repository. Its root-owned immutable build hook,
mkinitcpio configuration, boot entry, offline executor/unit and Windows return
assets now live under `/usr/share/apx/native-windows-lifecycle-v1`; fixed
executors remain under `/usr/lib/apx`.

Delete persists a `finalizing` stage before post-boot cleanup, so reruns are
idempotent and pending is removed last. Create persists `preparing-installer`
and `installing`, records an exact prepared-installer marker, makes installer
preparation repeatable, and automatically resumes an exact APX Setup or Windows
Boot Manager entry for at most eight Windows restarts. The finalizer retries a
transient failure up to three times at boot; the Hub treats a live Windows phase
as busy. Completion still requires the driver, background return helper and
absence of the obsolete Desktop icon before publishing `ready`.

The deployed builder was executed from `/`, built and signed an exact create
UKI using only installed assets, and the UKI was extracted byte-for-byte against
the installed executor/unit. No BootNext, pending operation, maintenance image
or disk change remains. All 1089 tests pass with 11 expected skips. Rollback:
`/var/lib/apx/backups/20260826T145246Z-self-contained-native-windows-lifecycle-v1`.

## Current handoff — orphan removed and visible maintenance menu eliminated

The incomplete Windows/OOBE generation that occupied the reserved tail without
a Hub record has been removed through an exact signed offline cleanup. Current
NVMe state is only p1 `APX_EFI` (1 GiB) and full-size p2 `APX_CRYPT`; Btrfs is
511018602496 bytes with about 449429082112 bytes estimated free. There is no p3
or p4, Windows/native/pending marker, `BootNext`, Microsoft EFI tree, Windows
Boot Manager entry, APX Setup entry or lifecycle image. Linux entry 0005 is
current and first in permanent `BootOrder`.

The newly installed WinPE v2 contract creates exactly p3 `APXWINTARGET` and p4
`APXWINSETUP`, preserves shared p1 `APX_EFI`, identifies every object by fixed
disk/GPT/partition identities rather than drive letters, applies Windows 11 Pro
index 6 from the split SWMs, writes BCDBoot to the true ESP and refuses reboot
until both EFI and BCD/loader validation pass. Setup media is not reclaimed
until first Windows login and required APX-return/Wi-Fi assets are confirmed.

The strange systemd-boot selection screen seen during the cleanup was a
technical maintenance entry being selected through the normal APX boot menu.
The deployed runner now bypasses that menu: it uses a direct temporary UEFI
entry created with `--create-only`, verifies permanent `BootOrder` is exactly
unchanged, removes the systemd-boot entry before reboot, and arms only
`BootNext`. The post-boot finalizer removes that temporary firmware entry and
UKI. No new create or reboot has been armed; the owner must explicitly start
the next Windows creation from the Hub.

Installed/source comparisons pass, the environment switch service is active,
no systemd unit is failed, and all 1089 tests pass with 11 expected skips.
Rollback: `/var/lib/apx/backups/20260826T161719Z-native-windows-explicit-winpe-v2`.

## Current handoff — 160-GiB WinPE stopped before format; repair staged

The owner created native Windows generation
`890c5a4c-3b84-41ea-af57-2fb0043243b5` at 160 GiB. Offline storage creation
and installer preparation succeeded. The physical disk now has unchanged p1
`APX_EFI`, 315.94-GiB p2 APX Linux, 151-GiB p3 NTFS `APXWINTARGET` and 9-GiB
p4 FAT32 `APXWINSETUP`. WinPE displayed `findstr is not recognized` and
returned to Linux before its first format.

Read-only mounts proved p3 contains only `APX/install-contract-v2.ini`; p4
still has the exact three SWMs and the same contract as p3 and p1. There is no
`EFI/Microsoft`, `bootmgfw.efi`, BCD, Windows Boot Manager firmware entry or
`BootNext`. Linux is current and first in permanent `BootOrder`. No WinPE/DISM
process remains. The Host has about 23 GiB RAM available; the active menu
service uses about 12.5 MiB and QuickShell about 192 MiB RSS.

The finalizer is failed at its three-attempt start limit because its completion
probe tried to iterate a missing `Users` directory. The visible management
state records this failure and the trusted lifecycle remains pending at
`installing`, attempt zero. The repository correction treats missing `Users`
as incomplete, keeps the menu busy while any native pending marker exists,
eliminates all WinPE `findstr` calls, dynamically chooses free drive letters,
checks DiskPart size/type/label plus the replicated exact contract, revalidates
the target before formatting and retains full DISM/BCDBoot/BCD/firmware gates.

Two exact adapters are ready but have not been executed:
`repair-current-native-windows-winpe-findstr-v3.sh --prepare` performs a
non-rebooting atomic p4 WIM/runtime repair with rollback, and
`resume-current-native-windows-install-v3.sh --reboot` revalidates everything
before allowing the finalizer to arm APX Setup once. Do not delete, recreate or
format p3/p4, do not remove the pending/installer markers, and do not manually
start the failed finalizer before the prepare adapter has completed.

The corrected sources pass the complete 1090-test repository suite with 11
expected skips. They deliberately differ from the still-installed Host assets;
no deployment, `BootNext` or reboot was performed in this session.
The corrected command was also rebuilt into a temporary copy of the current
`boot.wim`; complete WIM verification and byte comparisons passed. That copy
was removed and p3/p4 are unmounted and unchanged.

## Current handoff — recovery moved into Environments menu

The owner explicitly requires every normal Windows lifecycle action to be
performed from the Hub Environments menu. The repository now closes the failed
creation gap: trusted failed `installing` state exposes `RETOMAR WINDOWS` and a
two-click `APAGAR INCOMPLETO`, both bound to the root-owned pending generation.
The ordinary `APAGAR` path remains the final acceptance action after Windows
has reached `ready`.

Retry validates the exact p1-p4 layout, contracts, prepared marker, setup UEFI
path and split SWMs before atomically rebuilding only p4 `boot.wim` from the
installed fixed WinPE source. It neither partitions nor formats from Linux and
does not arm boot itself. The authenticated finalizer is started only after the
refresh passes and then selects APX Setup once. Discard uses the signed offline
delete path; it restores the original pending marker and removes temporary UEFI
artifacts if the reboot cannot be committed.

`deploy-native-windows-menu-recovery-v1.sh` is the staged non-rebooting rollout
for the current Host. It installs code/UI only, stops the exhausted finalizer
and deliberately cannot mount/write the Windows volumes, arm BootNext, start
the finalizer or reboot. It has not been executed. Consequently the live menu,
runtime and p4 still remain as reported in the preceding handoff; no physical
state changed while implementing this menu-owned flow. Syntax, whitespace,
focused recovery tests and the complete 1095-test suite pass, with 11 expected
skips.

## Current handoff — menu recovery controls activated

The owner authorized the code/UI-only rollout. It first refused cleanly with
AC offline and changed nothing. After AC became online (battery 76%), it
installed exact source copies of the QuickShell menu, wire contract, client,
switch service, corrected finalizer, WinPE source, retry executor and discard
executor. The focused 42-test preflight passed and QuickShell recorded
`Configuration Loaded`. Backup:
`/var/lib/apx/backups/20260826T182015Z-native-windows-menu-recovery-v1`.

Postflight proves the switch service active, exact installed recovery/refresh
sources, pending generation `890c5a4c-3b84-41ea-af57-2fb0043243b5` still at
`create/installing` for 160 GiB, no BootNext and no p3/p4 mounts. The finalizer
is deliberately still failed/stopped. No disk, installer-media, filesystem or
firmware write was performed by deployment. The menu now exposes
`RETOMAR WINDOWS` and the two-click `APAGAR INCOMPLETO`; neither action has
been selected. Since the owner intends a fresh create, the immediate physical
action is owner confirmation of `APAGAR INCOMPLETO` in Environments, followed
by the signed offline reboot/delete/finalization sequence.

The owner's first two-click attempt displayed an error, but the destructive
request never crossed the client boundary. There is no recovery unit or
accepted `native.discard` journal event; pending remains `create/installing`,
the prior successful-create status is unchanged, p3/p4 remain intact, and
BootNext/maintenance artifacts are absent. Exact digest/inode comparison found
that the already-running Hub container retains the old environment-switch
client through its read-only bind mount, while the Host path and QML are the
new source-exact versions. Hot-reloading QML cannot replace a bind-mounted
inode. The next bounded action is an owner-approved controlled Hub relaunch so
the container receives the new client; do not retry discard before that.

The owner then approved the controlled Hub relaunch. The official authenticated
handoff closed the old session and opened a replacement at 19:25 WEST without
rebooting the computer. Repository, installed Host and live-container client
digests now all equal
`bc2cf6f2099f1326d862bd3dd6bdfbf953a1740d95f3afa513dea50333bba482`,
and the live client exposes both `native-discard` and `native-retry`; the wire
contract is likewise source-exact in all three locations. The switch service
and replacement Hub are active, locks are absent, pending is still the same
160-GiB `create/installing` generation, BootNext is absent, p3/p4 are unmounted
and disk geometry is unchanged. It is now safe for the owner to retry the
two-click `APAGAR INCOMPLETO` action from Environments. No recovery action has
yet been started by this relaunch.

The owner subsequently retried and confirmed `APAGAR INCOMPLETO` in the menu.
The exact-generation `native.discard` request was accepted and the offline
delete/finalization completed. Current authenticated menu state is
`native-delete/complete`, `busy: false`; the catalogue has no Windows entry,
the pending/native Windows markers are absent, p3/p4 are removed and p2 has
expanded back to 475.9 GiB. There is no BootNext, active recovery unit,
management/recovery lock or Windows/APX Setup/maintenance loader entry. The
remaining `windows-storage-*.status` files are inert records dated 2026-08-25,
not active lifecycle artifacts. The supported next step is now a fresh native
Windows creation initiated by the owner solely from Environments.

## Current handoff — 2026-08-30 boot-loop recovery

This section supersedes the earlier handoffs. A later create/160 generation
`18fe09c4-ed14-40a3-96d2-544d3ba3e628` failed in WinPE with
`APX-FORMAT-04 / formatted-target-label`, then the old finalizer automatically
rearmed Setup from `stage=installing` until `resume_attempts=11`. The owner
recovered Linux from live media by reversibly renaming the pending file.

The fail-closed finalizer, recovery executor, switch integration, preparation
scripts, WinPE source and systemd unit are now installed source-exact. The
recovered pending was copied back only after protection was active and was
consumed once into `recovery-required`. The original
`windows-pending.json.recovery-20260830` remains unchanged. Linux is current
and first in BootOrder, BootNext is absent, and the finalizer is inactive with
`Result=success`, status 0 and no restart policy.

p3 has valid NTFS metadata but contains only the APX contract; DISM never
applied Windows. p4 is a valid setup volume whose BCD boots `sources/boot.wim`.
There is no Windows tree, winload, EFI Microsoft tree or Windows firmware
entry. Therefore the only recovery is an explicit re-application after the
boot.wim is rebuilt with the corrected CRLF/find.exe batch. It must not be
started while AC is offline, and no automatic process may arm it.

The complete suite passes 1102 tests with 11 expected skips. See
`docs/native-windows-fail-closed-v2-2026-08-30.md` and
`docs/apx-system-state-audit-2026-08-30.md`.

## Current handoff — owner-controlled third attempt from the Hub

The second physical attempt returned safely to Linux and produced authenticated
`APX-PART-03 / partition-identities / windows-target`. Post-mortem proved p3
was not formatted during that attempt and still contains only its APX
contract; DISM and bcdboot did not run. The root cause was DiskPart's
11-character tabular label display truncating `APXWINTARGET`. Commit
`e6fd060f7146b95a7516e10b8dd69d86b8643ef3` corrects the p3 probe while
retaining full-label and byte-identical contract checks after mount and again
immediately before format. It also persists raw command output, exit codes,
DISM logs and terminal diagnostics to p4 and APX_EFI and pauses on failure.

The owner now wants to initiate the next attempt from the Hub rather than a
Host-side command. The durable marker is an authenticated `create/failed`
generation with `explicit_attempts=1`; Linux is first, BootNext is absent, AC
is online and battery is charging. The Hub previously exposed retry only for
`prepared`, `boot-prepared` and `recovery-required`, accidentally hiding the
button for an authenticated terminal `failed` result. The corrected admission
includes `failed` in both the status surface and exact-generation recovery
executor. It does not mutate the pending state or firmware merely by becoming
visible. `RETOMAR WINDOWS` remains the explicit action that revalidates the
machine, rebuilds and verifies p4 from the corrected source, increments the
bounded explicit attempt from 1 to 2, arms one BootNext and reboots. No third
automatic retry exists.

## Current handoff — Windows first-boot continuation

The owner created a fresh generation
`1c5b5631-fb0e-4384-bf6f-b23eb1798f70`, then explicitly entered WinPE and
Windows. WinPE published authenticated `boot-prepared`; DISM, driver injection
and bcdboot succeeded. The Windows Panther log proves essential OOBE services
started, setup phase 4 completed and setup exited with code `0`. Windeploy then
requested an immediate reboot before OOBE. No crash dump exists.

That Windows-requested reboot returned to Linux because the one-shot Windows
BootNext had already been consumed and Linux remains first permanently. The
remaining defect is APX accounting: the two-attempt limit counted one WinPE
launch plus one Windows launch, hiding retry exactly when normal Windows setup
needed its next boot. Installation attempts and first-boot continuations are
now separated. WinPE remains capped at two; authenticated `boot-prepared`
continuations are manual and capped at eight. The menu labels the latter
`PROSSEGUIR WINDOWS`. No automatic boot or permanent BootOrder change is
introduced. See `docs/native-windows-first-boot-continuation-2026-08-30.md`.

The subsequent physical OOBE run proved why four was insufficient. OOBE
reached `IMAGE_STATE_COMPLETE`; Windows Update installed a ZDP update and
requested a reboot, which safely returned to Linux after consuming the
one-shot BootNext. The current pending generation is still `boot-prepared`
with `explicit_attempts=1` and `boot_attempts=4`. The manual OOBE budget is now
eight, so the Hub can expose `PROSSEGUIR WINDOWS` again without any automatic
retry. SetupComplete's Realtek provisioning also treated an already-present,
up-to-date driver as failure; the idempotent check now verifies the INF through
`pnputil /enum-drivers /files` before recording success with a warning.

Windows subsequently completed and the finalizer published the physical
generation as `ready`. Post-install integration replaces the unreliable global
WIN+E registration with a `WH_KEYBOARD_LL` listener that suppresses Explorer's
chord only while APX is active, logs to `%LOCALAPPDATA%\APX\ReturnToHub.log`,
and reboots only on the explicit key event. Offline evidence shows the Realtek
Bluetooth `USB\VID_0BDA&PID_4852` driver 1.9.1046.3002 installed, services
created, device restarted and SetupAPI `SUCCESS`; no replacement driver is
warranted. The Hub description is shortened to `Windows 11 · 160 GiB`. See
`docs/native-windows-post-install-integration-2026-08-30.md`.

Physical deployment of the v2 helper stopped before writing because ntfs3
refused dirty p3 read-write. `ntfsfix -n` reports the MFT, MFT mirror and boot
sector intact; no force option and no Linux-side repair were used. The live
boot runner intentionally retains v1 hashes, so Windows remains bootable. Run
an elevated `chkdsk C: /scan` in Windows and choose Restart; after Linux
returns, deploy the two return files and only then deploy the new validators.

The first ready-state native boot was correctly non-mutating but refused due
to an incompatible Secure Boot gate. This machine had Secure Boot disabled
throughout installation while remaining in firmware User Mode with enrolled
keys and signed APX/Microsoft boot managers. The runner now accepts coherent
enabled or disabled User Mode, rejects Setup Mode/mismatched reports, validates
both boot-manager signatures, and admits only the complete known v1 or v2
return payload during rollout. Physical `--validate-only` passed with no
BootNext; the Hub can launch the current Windows again.

The next one-shot launch reached Windows and returned normally: Linux remains
BootCurrent/first in BootOrder and BootNext is absent. A journal-only false
rejection was caused by the Hub waiting while the transient executor initiated
reboot; native boot submission now uses `systemd-run --no-block` and retains
all validation inside the runner.

Do not force-mount p3. The first v2 return-helper deployment made no write:
`ntfs3` refused RW because the volume is dirty and `ntfsinfo` reports that it
is scheduled for check. The deployer now targets authenticated p3 and detects
this state explicitly. Boot Windows from the Hub, allow AutoChk, run elevated
`chkdsk C: /f` if requested, and return through normal Restart. Deploy v2 only
after `ntfsinfo -m /dev/nvme0n1p3` succeeds.

One AutoChk/Windows return removed the scheduled-check refusal, but the NTFS
log still reports `Restart state: DIRTY` and unclean filesystem while returning
exit zero. The deployer now checks these exact diagnostics as well as the exit
status. No RW mount was attempted. Boot Windows once more, let it reach the
desktop, then use normal Restart back to the Hub before re-auditing p3.

The second pass cleaned p3 (`Volume Flags 0x0000`, restart CLEAN). The v2
SUPER+E helper is now physically installed with read-only hash verification
and backup at
`/var/lib/apx/backups/20260831-native-windows-return-v2.M9sjPC`. The legacy
desktop shortcut was already absent; deployment now safely supports and rolls
back either legacy state. p3 is unmounted, native `--validate-only` passes,
BootNext is absent, and Linux remains first. On the next explicit Windows boot,
wait for the desktop, confirm the helper log says `keyboard hook ready`, then
press SUPER+E once to test the normal return to the Hub.

## Current handoff — 2026-08-31 face-auth readability correction

The owner reported that both Hub unlock and `sudo` always required the
password. Howdy, dlib, the enrolled `APX-owner` model, both PAM entries and the
leased `/dev/video0` were still present. The journal showed every unprivileged
attempt failing as `unknown error 1`; an exact reproduction as `apx` exposed a
`PermissionError` reading the root-only mode-0600 model. That permission was
never compatible with `hyprlock`, whose PAM stack runs in the unprivileged
locker process.

The live Hub config and model are now `root:apx` mode 0640, so `apx` can read
but not alter either file, and the recognition window is eight rather than
four seconds. The original password fallback remains unchanged in both PAM
services. A direct comparison as `apx` now reaches a normal timeout rather
than error 1. Before the owner opened the e-shutter, OpenCV read 218 frames but
detected no face. After it was opened, all 30 sampled frames contained a face,
but the old model's best score was 6.210 against the retained safe 3.5 limit.
The limit was not weakened. The owner used the requested separate-terminal
Howdy flow and enrolled four current views. Their measured scores were
2.631–3.116; the official comparison returned zero. A cold real `sudo`
identified `apx` without a password, and a real Hyprlock cycle logged
`Identified face as apx`, unlocked and exited zero. Host and Hub have no failed
unit. The immediate pre-fix backup is
`/var/lib/apx/backups/20260831-face-auth-readability-v2`; the exact accepted
PAM/config/model state is
`/var/lib/apx/backups/20260831-face-auth-working-v2`.

## Current handoff — 2026-08-31 connectivity and Fn repair

The active Hub proved that the Fn bridge exits immediately: it expected
`AT Raw Set 2 keyboard`, while the exact leased i8042 node is
`AT Translated Set 2 keyboard`. Bluetooth is present but BlueZ reports
`off-blocked`; direct `bluetoothctl power on` fails while `hci0` remains
soft-blocked. The Wi-Fi credential pipe/socket probe reaches the typed Host
contract without exposing its dummy secret.

The repository candidate corrects the physical keyboard name, performs
Bluetooth rfkill-unblock before BlueZ power-on with five-second state
verification, and accepts Wi-Fi connection only after iwd re-observes the
requested SSID. Missing-prompt and rejected-password errors are bounded and
owner-readable. The v3 unit adds only `CAP_NET_ADMIN`, required for rfkill.
The full suite passes 1118 tests with 11 expected skips. A running v3 socket is
inode-bound into the Hub, so service activation must be coordinated with a Hub
relaunch; do not silently close the owner's applications. See
`docs/host-connectivity-and-fn-repair-v1-2026-08-31.md`.

Staging is now physically complete at
`/var/lib/apx/backups/20260831T134617Z-host-connectivity-input-v1`. QuickShell
restarted without ending Hyprland and the corrected Fn bridge remains live.
The Hub menu client successfully powered Bluetooth off/on and scanned 15
unpaired devices; `Casa` remained connected with full Internet and there is no
failed unit. The first staging attempt was rolled back after exposing an
rfkill/BlueZ readiness race; both implementation and deployer now wait for
`off-blocked` to clear. The live daemon is intentionally still the pre-stage
process. The new general radio and requested-SSID confirmation paths activate
at the next normal boot or a coordinated Hub relaunch. Remaining owner checks
are physical Fn key presses and one protected Wi-Fi password known to the
owner; no credential should be sent to Codex.

## Current handoff — 2026-08-31 Fn-only correction

The owner confirmed that some actions still fired without Fn, specifically
plain F5/F6. The remaining causes were a broad bridge branch that admitted
brightness codes from the normal AT keyboard and direct Hyprland `XF86`/
F13--F16 fallbacks. The exact ITE interface is now the only authority for the
complete Lenovo Fn row. AT F1--F12/media/brightness events are ignored, apart
from Print Screen, and the parallel compositor bindings are absent. Media
transport next/play/pause/previous bindings remain because they are not this
Fn row.

A live reload also revealed an orphaned older bridge. The script now holds a
singleton runtime lock, and the deployer stops an exact old command before
QuickShell restarts. Current evidence: one bridge process, zero forbidden
alternate binds, matching repository/installed Hyprland, bridge and runtime
hashes, zero failed units, and 1118 passing tests with 11 expected skips. The
latest root-only recovery set is
`/var/lib/apx/backups/20260831T140531Z-host-connectivity-input-v1`. Ask the
owner to verify that plain F1/F2/F3 and F5/F6 remain application keys while the
corresponding Fn combinations perform audio and brightness actions. No commit
or push has been made.

## Current handoff — 2026-08-31 Fn, fullscreen and shell integration

The earlier ITE-only raw-F design is superseded. Physical capture established
that ITE is a complete keyboard, so raw F1--F12 cannot prove Fn. The installed
singleton bridge ignores all raw F codes and handles only semantic ITE
brightness plus exact AT Print Screen. Hyprland retains semantic XF86/F13--F16
Fn bindings, and firmware `fn_lock=0`. Do not remove those semantic bindings;
owner confirmation of plain F versus Fn remains pending.

The active Hub and all registered graphical Environment homes match the seed
for the current QuickShell configuration and three generated landscape PNGs.
The background rotates every 15 minutes. `SUPER+F` is fullscreen everywhere;
`SUPER+P` calls `openFiles`, which refuses in the Hub and launches Thunar only
in workloads. The Hub Thunar package is removed, while Hytale, Steam, Minecraft
and Faculdade retain `/usr/bin/thunar`.

The Central de Controlo keyboard tile contains only the text `TECLADO`; it has
no icon, ON/OFF label or level. The Hub terminal is labelled `Terminal do Host`
without `sessão única`. The normal screen lock interrupted the final menu
screenshot and was left intact. Recovery is the root-only backup
`/var/lib/apx/backups/20260831T144833Z-fn-wallpaper-fullscreen-v1`. No commit or
push has been made. The complete suite passes 1121 tests with 11 expected
skips; Host and Hub currently report zero failed service units.

## Current handoff — 2026-08-31 lock retry and control colour states

The owner requested a deliberate face retry after Howdy times out. The reviewed
and installed Hyprlock profile now accepts empty Enter. This closes the current
empty password conversation and starts PAM again, where `pam_howdy.so` runs
before the unchanged password stack. A typed valid password still unlocks; a
successful new face cycle also unlocks after an absent or wrong password. The
live Hyprlock process predates the file and was not killed because doing so
would briefly remove the active lock. Unlock it once normally; subsequent locks
use the new behavior.

The live QuickShell has also removed the remaining Wi-Fi, Bluetooth, volume and
microphone ON/OFF badges. A later owner refinement removes card-level state
colour from Wi-Fi, Bluetooth, volume and display; only microphone and keyboard
retain it. Neutral session actions are on the top row and coloured actions are
on the bottom row. The first retry attempt was observed on the old long-lived
lock process, so it still discarded empty Enter. That process has now exited;
the next lock loads `ignore_empty_input=false` and exposes an explicit
`ENTER: REPETIR CARA` after failure. The first fresh physical retries then
proved that Hyprlock's checking state covers the password-conversation
transition before Howdy starts the next camera cycle. It is therefore labelled
only `A VALIDAR…`. A separate 300-ms status helper shows `A VERIFICAR A CARA…`
only while the exact Howdy comparison process owns `/dev/video0`; this direct
probe was reproduced successfully against the live camera. Wi-Fi and Bluetooth
use a compact 46-pixel summary row. The session caption is separated from the
previous controls and all four action buttons now share the other cards'
geometry, border and typography while retaining the requested neutral-top and
coloured-bottom ordering. Seed and all five graphical homes match; recovery is
root-only at
`/var/lib/apx/backups/20260831T225802Z-camera-state-session-cards-v1`. No PAM
or face-model bytes changed. No commit or push has been made.

## Current handoff — 2026-09-01 first-frame face state and bar shortcuts

The preceding `/dev/video0` ownership probe is superseded. Howdy package
`3.0.0beta.r592.d3ab993-3` now creates a per-process runtime marker immediately
after its first successful `read_frame()`. The 300-ms Hyprlock helper validates
the marker's PID, `/proc` start ticks and Howdy command line, so `A VERIFICAR A
CARA…` cannot appear merely because OpenCV opened the device. A live direct
comparison remained on the retry instruction for 1.702 seconds, changed to the
camera message with the first frame, returned after the eight-second search and
left zero markers. The Howdy package explicitly retains `config.ini`; its exact
bytes, the enrolled model, ownership, permissions and recognition thresholds
are unchanged.

Hyprlock now routes a successful face around the password include but through
the same `pam_faillock.so authsucc` cleanup reached by a valid password. The
three stale records created during earlier retry diagnosis were reset; the
current record count is zero. The fallback login/password stack is retained.

The QuickShell bar has symmetric 5-pixel horizontal margins. Calendar also
sits 5 pixels inward from the left, and the IA/Battery/Control Centre group
sits 5 pixels inward from the right. Calendar (`SUPER+D`), Environments
(`SUPER+E`), IA/model (`SUPER+I`), Battery
(`SUPER+B`) and Control Centre (`SUPER+A`) now all bind their bar-button active
state to popup visibility, so mouse and keyboard openings share the same scale
and opacity animations. Calendar, Environments, IA/model and Battery retain
their complete labels throughout; only Control Centre changes `[|]` to `[A]`.
The final scale delta is 6% with cubic easing and no overshoot. Only selection
animates during an ordinary open/switch: outside dismissal and
the previously selected button reset immediately. Repeating the already-active
button or shortcut closes that menu with the reverse animation.
The opening kind is armed before popup visibility changes, so both activation
and deliberate same-button deactivation execute their transitions.
Bar-button hover is tracked by a passive `HoverHandler`, and the selected
button remains visually active while its popup is open. This prevents the
separate popup surface from clearing hover feedback under a stationary cursor.
Button clicks are handled by a sibling `TapHandler`, ensuring the first click
on an already-active button closes its menu instead of merely recovering
pointer ownership.
The root cause was the mouse-opened layer popup requesting keyboard focus.
Mouse openings now stay non-focusable until the pointer enters the menu, while
IPC keyboard openings request focus immediately. Bar clicks therefore retain
their hand cursor and reach the active toggle without focus-recovery clicks.
The surrounding `HyprlandFocusGrab` uses the same condition instead of becoming
active for every visible popup.
All top-level menus now match the bar's outer surface exactly: `root.panel`
background and one-pixel `#26343a` border; internal semantic cards are unchanged.
Hyprland's active and inactive application borders are both the same one-pixel
opaque `#26343a` used by the QuickShell bar; the cyan/green active gradient is
removed from the canonical Lua and fallback configurations. Seed and all five
graphical homes match; one QuickShell
instance loaded cleanly. The full suite passes 1124 tests with 11 expected
skips; Host and Hub have zero failed units. Immediate
root-only recovery is
`/var/lib/apx/backups/20260831T231335Z-first-frame-bar-shortcuts-v1`. No commit
or push has been made.
