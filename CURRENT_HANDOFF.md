# APX Current Handoff

Last updated: 2026-07-18 after root-host reconciliation and the decision to
defer local-model installation.

Read this file together with `AGENTS.md` and `PROJECT_STATE.md`. This is a short
continuity bridge, not a replacement for the canonical project state.

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
digest `b5836e03a8c59f62018b58a4b9410a1dab1a7ee11c24fd03e64f1dab2b37d6ea`.
It binds the exact config/session/watchdog files, requires the 120-second timer
active before any grant, and contains only the closed five-device nspawn unit
with private networking and resource limits. It remains non-executing. Next
implement safe asset staging plus the bounded readiness/teardown adapter; do
not bypass that adapter by running the emitted commands manually.

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
- the 709-test suite succeeds in the root-host checkout with eight expected
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
