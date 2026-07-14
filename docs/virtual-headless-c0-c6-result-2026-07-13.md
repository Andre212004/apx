# APX Virtual Headless C0–C6 Result — 2026-07-13

Status: the experimental functional C0–C6 ladder passed in one disposable VM.
This is implementation evidence for the headless design, not authorization or
readiness evidence for installation on a physical computer.

## Scope and Isolation

The run used QEMU 11.0.2 with KVM, Q35, OVMF UEFI, four virtual CPUs, 8 GiB RAM,
and one newly created sparse 64 GiB qcow2 disk. The VM command exposed only that
qcow2 file. It exposed no physical block device, host directory, clipboard, USB
device, credential, SSH agent, or project checkout.

The official Arch installation ISO had SHA-256
`e86295dc0bdf9b85a5a9256810c553239689d2ae8e80eeec81b4e2e910d8a6c0`.
Its detached signature was verified against Arch release signer primary
fingerprint `3E80CA1A8B89F69CBA57D98A76A5EF9054449A5C`.

The VM disk remains outside the repository at
`~/.local/share/apx-virtual-lab/DISPOSABLE-APX-C0-C6/disk.qcow2`. It is retained
only as disposable laboratory evidence and is not an APX release artifact.

## Result by Gate

### C0 — bounded disposable target

Passed for the VM envelope. The installer required the exact approval text,
QEMU/KVM identity, `archiso` hostname, Q35 identity, `/dev/vda`, and exactly
68,719,476,736 bytes before touching storage. The physical host disk was never
visible to the guest installer.

The independently rebuilt development contracts package was also rechecked:
two network-disabled builders produced the same 16,109-byte package with
SHA-256
`9d6e53007bc56e8a9105f4ff65c14097dbec13aa8b0b4c7ddb70912b01b012fd`.
A third offline container had already installed it with zero altered entries
and imported all three Python modules.

This is a laboratory substitute for production trust. APX production signing
keys, the signed functional bootstrap package, and the physical target dossier
do not exist.

### C1 — clean minimal Arch foundation

Passed. A clean UEFI installation booted from the qcow2 disk using
systemd-boot, LUKS2, and Btrfs without a desktop or display manager.

- LUKS UUID: `64c33ed7-42e9-4af0-91bc-4064f0ff36d4`;
- Btrfs UUID: `29344275-3c27-4f4e-88d6-4788e1311ff3`;
- EFI filesystem UUID: `77E4-DD9C`;
- retained checkpoint: `c1-installed-awaiting-reboot`.

The host did not retain Git, GCC, Node.js, npm, Codex, or
`arch-install-scripts`. The contracts package installed offline and its files
and imports were verified.

### C2 — ordinary reproducible Hub

Passed for the experimental runtime. The immutable release
`hub-headless-v3` contains a small unprivileged `apx` client, not the privileged
runtime. The Hub was destroyed, recreated from that release with a new
generation, and started with a private user namespace and private network.
The immutable release remained unchanged.

The host executor owns `/run/apx/executor.sock`. It accepts only fixed JSON
operation schemas and uses Unix peer credentials plus the active Hub's
65,536-ID user-namespace map to authorize a request. Host root using the
unprivileged client was refused, while the active Hub was accepted. The socket
was not mounted into Development.

From inside the Hub, `apx` successfully planned, created, started, stopped, and
destroyed `hub-managed-fixture`. Afterward its registration, Btrfs root and
home, machine, virtual network interface, mount, and processes were absent.

### C3 — independent Development

Passed. `development-headless-v1` has a separate immutable release, mutable
root, persistent home, generation, user namespace, and private virtual network.
Its observed outer UID map differed from the Hub:

- Hub: `0 1278869504 65536`;
- Development: `0 492306432 65536`.

Git, GCC, Node.js, npm, and Codex 0.144.3 existed only in Development. Codex
was installed through Development's own npm database and was absent from the
host, Hub, and immutable Development release.

### C4 — package and data locality

Passed for the tested package paths. Pacman installed `tree` 2.3.2 into the
mutable Development root only. It remained absent from the host, Hub, and
immutable release. Two separate minimal fixtures installed the same package
independently; destroying one preserved the other and the host.

Development home data survived stop/start, but the offline test project was
not visible in the Hub. The APX executor socket and `apx` command were both
absent from Development.

### C5 — lifecycle, storage, and conservative recovery

Passed for create, start, clean stop, snapshot, archive, restore to a new
identity, destroy, quota enforcement, and the injected failures listed below.

- Btrfs full qgroup accounting was enabled, consistent, and not overriding
  limits;
- each experimental root had 4 GiB referenced and exclusive limits;
- each experimental home had 2 GiB referenced and exclusive limits;
- a stopped Development snapshot was read-only;
- archive
  `archive-development-38d6938c-b0b8-4a19-8d7d-72500a91614e-9967345f-3d3d-4aa5-b0f4-cbb2ca18b800`
  contained separate compressed Btrfs streams and SHA-256 identities;
- restore created `development-restored` with a new generation and preserved
  the installed package, Codex binary, and home marker;
- clean stop left no machine, veth, mount, or process residue.

The first restore exposed a missing forced read-only-property transition. The
runtime preserved the partial result and reported an uncertain operation. An
explicitly approved cleanup removed it, the code was corrected, and retry
passed. A create fault injected immediately after root creation exited with
code 86; the unpublished root was preserved and reported uncertain until an
explicit cleanup was approved. Recovery then returned zero uncertain
operations.

### C6 — real offline daily workflow and reboot

Passed twice with QEMU launched using `-nic none`; this was distinct from an
earlier invalid attempt where QEMU's implicit network device remained present.
On the valid boots the guest host had only `lo`, and host, Hub, and Development
could not reach `1.1.1.1`.

Development initialized a Git project, compiled a C program with GCC, and ran
it successfully under `/home/offline-project-true`. Development was then
stopped, all runtime residue disappeared, and the Hub restarted without seeing
the project.

The final cold boot ID was
`e989a683-fc3f-4989-8d9f-11aaeba33611`. The executor started automatically,
the Hub's typed client worked, external network access failed as expected,
`systemctl --failed` was empty, and recovery reported zero uncertain
operations. The guest was then stopped cleanly.

## Failures That Improved the Runtime

The run did not hide failed attempts:

- the first reproducibility attempt differed because `.BUILDINFO` captured
  distinct absolute build paths; a canonical in-builder path fixed it;
- the first claimed offline boot still had QEMU's implicit NIC and was rejected
  as evidence; it was repeated with `-nic none`;
- restore initially needed `btrfs property set -f`; partial state was preserved
  until approved cleanup;
- create recovery originally did not classify a final `started` operation as
  uncertain; the recovery classifier was corrected;
- the first executor start passed a `Path` object to the Python 3.14 socket API;
  the Hub correctly refused to start without the endpoint, the socket bind was
  corrected, and the test was repeated with a new immutable Hub release.

## Retained Checkpoints

The qcow2 image contains these laboratory checkpoints:

1. `c1-installed-awaiting-reboot`;
2. `c5-lifecycle-package-isolation-passed`;
3. `c6-hub-executor-passed`;
4. `c6-final-offline-reboot-passed`.

They are experiment aids, not APX backup or rollback proof.

## What This Does Not Prove

The experiment proves that the chosen headless architecture can work end to
end in the reviewed VM. It does not yet prove:

- production release signing, custody, quarantine, or catalogue admission;
- the bounded raw archive reader for untrusted release artifacts;
- PAM owner authentication, the final broker, or physical console handoff;
- minimum-privilege production service hardening;
- hostile local-root containment against kernel attacks;
- every before/after interruption point in the formal rehearsal matrix;
- the user's real firmware, disk, backup, recovery media, keyboard, network,
  GPU, or Hyprland path.

Consequently, the functional virtual C0–C6 milestone is positive, while the
formal production C0–C6 rehearsal and installation on the physical computer
remain blocked.
