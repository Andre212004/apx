# APX Current Handoff

Last updated: 2026-07-31 after the owner installed Hyprland in the official
Hub and completed the first fully verified physical graphical sessions.

Read this file together with `AGENTS.md` and `PROJECT_STATE.md`. This is a short
continuity bridge, not a replacement for the canonical project state.

## Immediate next-chat state — 2026-07-31

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
four-hour Host watchdog are also current recovery mechanisms, not final UX.

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
- Phase 10 cleanup has not run.
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
