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
- the 635-test suite succeeds in the root-host checkout with ten expected
  external-fixture skips. One test fixture was corrected so subordinate-UID
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
