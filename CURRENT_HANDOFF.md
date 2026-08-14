# APX Current Handoff

Last updated: 2026-08-14 after Environment UI, shortcut lifetime, loading,
Brave and hybrid AMD+NVIDIA work.

Read this file together with `AGENTS.md` and `PROJECT_STATE.md`. This is a short
continuity bridge, not a replacement for the canonical project state.

Latest UI repair: the popup was moved from an xdg `PopupWindow` to a focused
`PanelWindow` surface. This keeps pointer and keyboard input available when a
menu is opened by either a click or a compositor IPC shortcut; the Hyprland
focus grab still dismisses it on an outside click. The control centre no longer
duplicates the Atalhos APX toggle; that capability is now a selectable
`shortcuts` module in the Environment creation catalogue and is included in
the Intermediate and Complete presets. Control icons retain the native
symbolic SVG pipeline at an integer size instead of fractional whole-popup
scaling. The repaired QML is live in Hub, `faculdade`, and the future seed.

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
