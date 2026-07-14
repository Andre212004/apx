# APX Clean-Install Readiness — 2026-07-13

Status: not ready for destructive installation. Repository architecture and
pure contracts advanced, and a VM-only functional C0–C6 run passed. No physical
computer or disk effect is authorized.

## Ready

- CLI-first clean-install order and C0–C9 gates;
- fixed x86_64 UEFI/LUKS2/Btrfs/systemd-boot C1–C6 profile;
- fixed minimal host package-name manifest;
- `systemd-nspawn` accepted for the headless experiment with mandatory private
  users and no graphical/device grants;
- Development-to-Hub isolation and promotion model;
- closed release-candidate metadata and pure quarantine import plan;
- closed target/supply evidence and clean-install dossier contract;
- fixed future command vocabulary with no caller commands/paths/effects;
- fake promotion store with separate quarantine, verification, admission, and
  immutable catalogue states;
- fake ten-stage installation journal with per-stage approvals, exact effects,
  compare-and-swap, and conservative recovery;
- closed archive-member and reproducibility manifest that rejects special
  files, privileged modes, escaping links, mutable/personal/Development state,
  and any non-identical rebuild;
- Apache-2.0 project licence recorded;
- closed unsigned `apx-contracts-development` definition with exactly eight
  read-only files, fixed mappings/dependency/licence, no executable integration,
  and exact two-build evidence;
- clean source commit and pinned Arch recipe; same-Development-environment
  and two independent network-disabled Arch builders now match byte for byte;
  a third offline container installs with zero altered entries and imports all
  packaged modules;
- accepted offline root/release-signer custody, backup/restore, signing,
  rotation, revocation, compromise, and mandatory physical rehearsal boundary;
- closed disposable x86_64 UEFI VM envelope, evidence/checkpoint policy,
  interruption matrix, C0–C6 run order, failure rules, and entry blockers;
- guarded disposable-VM installation and experimental headless runtime scripts;
- clean UEFI/LUKS2/Btrfs/systemd-boot Arch installation cold-booted from one
  new qcow2 disk with no graphical packages;
- ordinary destroyable Hub release using an unprivileged typed client and a
  host executor that authorizes only the active Hub user namespace;
- independent Hub and Development roots, homes, UID maps, private networks,
  package databases, runtime teardown, snapshots, archive/restore, quotas,
  conservative recovery, and true `-nic none` offline cold boot demonstrated;
- complete dated VM evidence and limitations recorded in
  `virtual-headless-c0-c6-result-2026-07-13.md`;
- 48 focused new tests passing;
- repository suite at 562 passing tests, four explicit external-fixture skips
  caused by the prior reboot, and no failures or errors.

## Blocking a Real Installation

1. The custody/rotation/revocation/recovery procedure is documented, but its
   exact cryptographic profile, physical rehearsal, and production root and
   release-signing keys do not exist.
2. No reviewed APX `.pkg.tar.zst` bootstrap package exists.
3. No physical candidate import, quarantine, archive verifier, catalogue, or
   Hub replacement implementation exists.
4. The VM has a narrow typed mutating executor, but no production-hardened
   minimum-privilege executor, broker, PAM owner-authentication service, trusted
   evidence store, or approval authority exists.
5. VM-only effect adapters exist for GPT, ESP, LUKS2, Btrfs, package
   installation, systemd-boot, and reboot verification, but reviewed
   production/physical-target adapters do not.
6. The functional VM ladder and selected failure injections passed, but the
   exhaustive before/after interruption matrix has not run for every effect.
7. Functional C1–C6 passed on a fresh VM installation, including independent
   package roots and two fixtures. Hostile local-root/kernel containment and
   the production-shaped trust/bootstrap path have not passed.
8. No target-specific disk, backup restore, recovery boot, locale, keyboard,
   timezone, hostname, network, or owner-enrollment evidence has been supplied.
9. Four external-fixture checks are correctly skipped after reboot; their
   package/base/graphical evidence must be reconstructed before those physical
   experiments can be claimed as rerun.

## Next Required Repository Work

1. Implement the bounded raw archive reader that checks every header and byte
   against the closed member manifest without extracting or executing it.
2. Select the exact cryptographic/tool profile, perform the documented physical
   rehearsal, review it, and only then authorize separate offline real-key
   generation.
3. Implement minimum-privilege effect adapters only after their pure models and
   failure tests pass.
4. Turn the guarded VM bootstrap/runtime into reviewed, signed, independently
   verifiable artifacts and complete the remaining interruption matrix.
5. Collect final physical-target facts and generate a fresh target-bound
   dossier only after the production gates pass.

## Installation Decision

Starting from scratch in the reviewed VM now produces a functional experimental
headless APX system. Repeating those laboratory scripts on the physical
computer would still bypass production trust, authentication, recovery-media,
backup, hardware, and service-hardening gates. The physical installation
decision therefore remains `blocked`.

The first functional user-visible milestone is complete in the disposable VM.
The next milestone is to convert that proof into production-shaped artifacts
and complete the remaining formal gates; only then may a real-machine dossier
be considered.

## Owner-Controlled Physical Development Pilot

After this production-readiness decision, the owner separately accepted a
target-bound hands-on pilot because the computer is dedicated to APX
development and the public GitHub repository is the source recovery copy. The
pilot does not change the production decision above.

`physical-headless-development-handoff-v1.md` fixes the observed Lenovo and
Samsung NVMe identities, requires a second-device ChatGPT handoff, repeats
read-only inspection from official Arch media, and permits erasure only after
the installer independently matches path, exact size, model, serial, UEFI,
physical execution, and exact approval text. Its bootstrap reuses the
VM-proven experimental runtime to reach Hub and Development, then moves Git,
GitHub authentication, Codex, compilers, and the source checkout into
Development and removes temporary host staging.

These physical-pilot scripts have not been executed. They are an explicitly
accepted risk for this personal development target, not signed production
artifacts or a general installer.
