# APX Current Handoff

Last updated: 2026-07-17 through preparation of the temporary root-host
development mode.

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

These are owner-reported facts. They have not yet been reconciled through the
repository's read-only physical audit. Do not silently promote them to verified
evidence.

## Next Owner Action

The owner has chosen to temporarily install and run Codex, Git, and GitHub CLI
as `root@apx-host` on the disposable physical pilot so physical APX tests can be
automated. The repository-only preparation is documented in:

`docs/temporary-root-host-development-mode-v1.md`

This decision supersedes the earlier immediate plan to perform the audit first,
but it does not convert the existing evidence into verified canonical state and
does not authorize cleanup. Before enabling the mode, publish the repository
change so the physical host can obtain the exact reviewed guide and helper.

Once the temporary mode is active, the first Codex task is to reconcile the
existing read-only evidence and automate the remaining Phase 9 and Phase 10
gates. Codex may create and destroy its own clearly named disposable test
Environments. Hub, Development, disks, reinstall, and broad cleanup still need
fresh owner approval.

The prior read-only audit procedure remains:

`docs/physical-pilot-state-and-cleanup-audit-v1.md`

That session must collect and sanitize Host, Hub, Development, APX storage,
package, service, listener, Ollama, repository, and temporary-file evidence. It
must not clean, install, download, start, stop, mount, unmount, or otherwise
change the machine.

Expected Ollama outcome is currently package-only. `ollama list` should confirm
whether there are zero models; do not download a model to complete the audit.

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
- a pure H0 clean-host Hyprland readiness, preview, journal, and recovery
  contract;
- 635 tests in the current milestone: 631 passing and four expected skips.

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
- Local model installation is deliberately deferred.
- The external SSD has not been selected, inspected, formatted, or attached.
- Do not use `sudo` or modify the host from an ordinary repository session.
- Root-host modification is allowed only after the owner explicitly invokes
  `docs/temporary-root-host-development-mode-v1.md` on the identity-matched
  physical pilot; it is not standing permission in Development or other chats.
- Do not commit or push unless the owner explicitly asks; the owner has asked
  the current development sequence to be published, but future sessions must
  evaluate their own request context.
