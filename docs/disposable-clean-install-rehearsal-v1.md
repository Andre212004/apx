# APX Disposable Clean-Install Rehearsal v1

Status: closed repository-side rehearsal plan. The experimental functional
C0–C6 ladder passed in a disposable VM on 2026-07-13; results and limitations
are recorded in `virtual-headless-c0-c6-result-2026-07-13.md`. The exhaustive
formal interruption matrix and production-trust rehearsal have not passed.

## Goal

The first destructive proof runs only in an explicitly disposable x86_64 UEFI
virtual machine. It proves the minimal Arch-to-headless-APX path, interruption
behavior, Hub recreation, Development isolation, Environment-local package
installation, lifecycle/storage recovery, and a non-graphical daily workflow.

Success in a VM is necessary but not sufficient for installation on the user's
computer. It does not prove that computer's firmware, disk, GPU, networking,
recovery media, or backup.

## Fixed VM Envelope

- x86_64 virtual CPU with UEFI firmware, secure-boot state recorded;
- 4 virtual CPUs, 8 GiB RAM, and one new 64 GiB disposable virtual disk;
- one virtual display only for firmware/console visibility, with no desktop in
  the guest through C6;
- one virtual network adapter whose enabled/disabled state is recorded at each
  phase;
- no host directory, clipboard, drag-and-drop, USB, secret, SSH agent, user
  home, Git credential, or writable installation-media sharing;
- serial/text console retained as the recovery surface;
- host and virtual-disk identity recorded before any destructive approval;
- VM and disk names unmistakably include `DISPOSABLE-APX-C0-C6`.

The hypervisor and exact Arch ISO are target inputs, not silently chosen by the
repository. Their versions and complete SHA-256 identities must be placed in a
fresh rehearsal dossier. The virtual disk must not be backed by or mapped to a
physical disk.

## Evidence and Checkpoints

Evidence lives outside the guest disk being destroyed and contains no secret.
Every record binds run ID, VM/disk/firmware/ISO identity, source revision,
package/trust manifests, stage plan digest, timestamps, result, and artifact
digests. Console output is bounded and sanitized.

Checkpoint snapshots are allowed only as experiment evidence and interruption
injection points. They are not accepted as APX rollback proof. Each resumed run
records whether it started from a pristine disk, a named checkpoint, or a real
guest reboot.

Required checkpoints are:

1. pristine VM before ISO boot;
2. dossier reviewed, before disk approval;
3. immediately before and after each storage effect;
4. minimal Arch installed, before first real reboot;
5. recovered text host after reboot;
6. APX host package installed but trusted state empty;
7. headless Hub created and verified;
8. headless Development created and verified;
9. C4 isolation fixtures present;
10. C5 lifecycle interruption matrix complete;
11. C6 final clean shutdown and cold boot.

## Run Order

1. Prove C0 recovery/provenance inputs and restore the pristine checkpoint.
2. Generate a fresh VM-bound dossier; review it without applying effects.
3. Enter a fresh strong approval naming the disposable virtual disk exactly.
4. Execute only the next fixed installation-journal effect, verify it, and
   retain sanitized evidence.
5. Inject power loss once before and once after each destructive or publication
   boundary; verify conservative recovery and no implicit deletion.
6. Complete the fixed minimal Arch profile and prove a real cold reboot to the
   text recovery surface.
7. Install only the independently rebuilt and verified APX bootstrap package,
   initialize empty host-owned state, and prove C1.
8. Import/admit the exact first Hub release, create it as an ordinary
   Environment, destroy/recreate it, and prove C2.
9. Create Development independently, install Git/Codex/build tools only there,
   stop it, and prove C3 isolation and zero residue.
10. Run the hostile C4 package-locality matrix across Development, Hub, host,
    base, and a second fixture Environment.
11. Run every C5 lifecycle operation, interruption point, reboot recovery,
    quota/capacity check, archive/restore identity check, and destruction proof.
12. Cold boot without network and prove the full C6 text-only daily and recovery
    workflow without Codex.

No phase is skipped because a later one appears to work. A restored hypervisor
snapshot does not substitute for APX journal/recovery behavior.

## Failure Rules

Any identity mismatch, unexpected device, unreviewed network use, missing
evidence, test failure, ambiguous effect, host-share exposure, secret in logs,
unexplained package visibility, unrecoverable journal, or failure to return to
the text console stops the run. The disk and evidence are preserved until an
explicit inspection/destruction decision.

A failure never authorizes trying the same steps on the real computer. The
repository contracts or implementation are corrected, tests rerun, and the VM
starts again from the pristine checkpoint with a new run ID.

## Remaining Formal Entry Blockers

The full production-shaped rehearsal cannot run truthfully yet because these
inputs are absent:

- a clean frozen functional runtime revision and reviewed bootstrap package;
- implemented bounded archive reader, trusted catalogue, executor, broker,
  authentication, and real installation-effect adapters;
- selected cryptographic profile, completed physical key rehearsal, and
  production public trust bundle/signatures;
- complete failure injection before and after every formal effect boundary;
- fresh production-shaped VM dossier and explicit virtual-disk approval.

The laboratory scripts now provide a guarded VM-only implementation for the
functional ladder. They are not the production effect adapters named by this
plan.
