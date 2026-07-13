# APX Clean-Install Foundation v1

Status: accepted target for the first headless experimental installation. It
does not authorize installation, partitioning, formatting, package changes,
accounts, services, or effects on the current computer.

## Purpose

This document closes the minimum choices needed to implement and rehearse
C0–C6 from `headless-bootstrap-and-cli-first-v1.md`. Hyprland, graphical login,
GPU/input/audio grants, portals, Odysseus, and the graphical Hub remain later.

## Fixed First Target

The first supported profile is:

- x86_64 PC booted in UEFI mode;
- one explicitly selected installation disk using GPT;
- one 1 GiB FAT32 EFI System Partition;
- all remaining admitted space as LUKS2 containing Btrfs;
- Arch `linux` kernel, systemd-boot, and text-only startup;
- `systemd-nspawn` as the C1–C6 Environment backend;
- headless Hub, Development, and disposable test Environments only.

BIOS, dual boot, multiple target disks, LVM, RAID, Secure Boot enrollment,
TPM-only unlock, hibernation, and automatic disk selection are unsupported in
the first profile. Detecting one blocks installation instead of improvising.

## Accepted Headless Backend

`systemd-nspawn` is accepted for the first headless C1–C6 implementation, not
as the final graphical or high-security backend.

It matches APX's complete bootable-system model, the repository has already
booted and cleaned a disposable Arch system tree with it, and it supplies the
needed namespace and systemd lifecycle primitives. Its own documentation warns
that untrusted workloads require user namespaces, so private users are
mandatory rather than optional.

The C1–C6 policy requires:

- systemd as Environment PID 1;
- non-overlapping private UID/GID ranges;
- private network namespace and APX-declared veth/NAT/DNS policy;
- executor-generated closed settings, not caller-written `.nspawn` files;
- fixed capability, syscall, address-family, cgroup, and teardown policy;
- no host home, package database, D-Bus, management socket, arbitrary bind,
  device wildcard, privileged mode, or shared writable root;
- no GPU, physical input, audio, camera, microphone, removable storage, FUSE,
  BPF, nested container engine, or graphical socket during C1–C6.

H0 re-evaluates physical graphics separately and may select a hybrid or OCI
backend without weakening the accepted headless results.

## Storage and Encryption

The target dossier binds stable disk and partition identity, measured capacity,
mounted/in-use state, and absence of unplanned RAID/LVM/swap/boot dependencies.
A bare `/dev/sdX` or `/dev/nvmeXnY` name is never sufficient identity.

Inside LUKS2, v1 uses one Btrfs filesystem with flat top-level subvolumes for
host root, recovery state, APX control state, Environment roots/homes, immutable
releases, snapshots, and operation staging. Traditional qgroups must be enabled
and healthy before an Environment is admitted. The detailed identity and quota
rules remain those in `btrfs-storage-layout-v1.md`.

There is no swap partition and no hibernation in v1. LUKS2 has a human-held
recovery passphrase; no plaintext key enters the repository, Hub, Development,
initramfs, journal, or APX metadata. TPM enrollment is deferred and may not
remove the passphrase recovery path without a later decision.

Formatting cannot begin until a restore-tested backup, boot-tested recovery
medium, exact disk identity, and fresh destructive approval are all present.
After formatting begins, rollback means restoring that backup.

## Boot Profile

V1 uses systemd-boot. The initramfs unlocks the recorded LUKS UUID and mounts
the recorded Btrfs host-root identity. Success means reaching a host-owned
locked/recovery text surface, not exposing root or an internal account.

Kernel, initramfs, boot entry, LUKS UUID, root subvolume, and recovery evidence
are verified together. Environment package managers cannot reach them. Secure
Boot is not claimed by this first experiment.

## Minimal Host Package Names

The fixed source package names are:

- `base`;
- `linux`;
- `linux-firmware`;
- `btrfs-progs`;
- `cryptsetup`;
- `iwd`;
- `python` for the first reviewable APX implementation;
- `gnupg` for APX provenance verification;
- exactly one applicable CPU microcode package: `amd-ucode` or `intel-ucode`;
- only additional firmware proven necessary by target hardware observation.

Exact versions, archives, sizes, SHA-256 digests, package signatures, repository
database digests, and signer evidence are resolved from one dated Arch snapshot
in the final dossier. Package names alone never authorize installation.

The Arch `base` package currently supplies pacman, the Arch keyring, systemd,
systemd-sysvcompat, shell/core utilities, IP tools, and account tools. The
systemd package currently supplies systemd-boot, networkd, resolved, nspawn,
machinectl, and machined. The dated dossier must recheck these facts.

Git, Codex, compilers, `base-devel`, editors, browsers, desktops, display
managers, portals, Docker, Podman, libvirt, and workload packages are absent
from the steady-state host. Temporary tools on the Arch installation medium do
not become host packages.

## Networking

The host uses systemd-networkd and systemd-resolved plus `iwd` for Wi-Fi.
Credentials remain host-owned. Environments receive private network namespaces
through fixed APX mediation, never the host network namespace or management
sockets. Offline recovery must remain possible.

## Owner and Headless Session

V1 separates the temporary installation authority, one APX human owner, and
hidden per-Environment identities.

The first owner authentication method is a host-owned password with fresh
re-entry for strong confirmation. It is separate from the LUKS recovery
passphrase. Hashes, PAM conversation, approvals, and unlock state never enter
an Environment. Exact PAM/service code is still an implementation gate;
biometrics, PIN, tokens, and autologin are deferred.

The normal headless interface is a broker-owned pseudoterminal attached only to
the lifecycle-managed Hub or selected Environment session. It exposes no host
shell, machine chooser, Linux username, or caller-selected command.
`machinectl shell/login` is diagnostic recovery tooling, not the user flow.

## Bootstrap and Trust

The first host APX artifact is a versioned Arch `.pkg.tar.zst` built from a
pinned revision. It is identified by complete SHA-256 and a detached APX
release signature before local installation.

It may contain only reviewed CLI/planner libraries, bounded executor/verifier/
broker code, fixed schemas/policy, and package-owned documentation. It contains
no Environment root, credentials, private key, source checkout, build tools,
downloader, or arbitrary installation script.

The trust design uses an offline APX root public-key fingerprint and a certified
release-signing key. A target approval repeats source revision, package digest,
signer, effects, and rollback. Development signatures provide provenance only;
they do not grant admission.

No production APX key or custody process exists yet. Offline generation,
storage, release certification, rotation, revocation, and recovery must be
closed before a real bootstrap package is trusted.

## Ordered Installation Stages

The installer is not one unrestricted script. It has ten plan-bound stages:

1. observe target, firmware, boot, CPU, storage, network, time, and recovery;
2. produce the exact disk/package/APX dossier;
3. obtain fresh disk-destruction approval;
4. create and verify GPT, ESP, LUKS2, Btrfs, and subvolumes;
5. install and verify the closed Arch manifest/configuration;
6. install systemd-boot and pass real reboot/recovery testing;
7. install verified APX host package and initialize empty trusted state;
8. import, admit, and create the first headless Hub;
9. create the first Development Environment with Git/Codex inside it only;
10. prove C3–C6 separation and recovery before graphical work.

Every stage re-observes state, binds a plan digest, journals before effects,
verifies after effects, and stops on ambiguity. Approval never flows implicitly
to the next stage.

## Required Before Real Installation

1. canonical target-observation and installation-dossier schemas;
2. a non-mutating exact dossier renderer;
3. pure state machines for all ten stages and interruption recovery;
4. hostile/ambiguous disk, package, signature, path, journal, and approval
   fixtures;
5. closed release-candidate and catalogue schemas;
6. reviewed minimum-privilege executor with no arbitrary command channel;
7. disposable VM or spare-disk rehearsal including reboot and failed stages;
8. C1–C6 evidence, including two-Environment packages and hostile local root;
9. real APX trust keys under the accepted custody process;
10. final target-bound dossier and fresh explicit approval.

## Official Technical Basis

- <https://wiki.archlinux.org/title/Installation_guide>
- <https://archlinux.org/packages/core/any/base/>
- <https://archlinux.org/packages/core/x86_64/systemd/>
- <https://man.archlinux.org/man/systemd-nspawn.1>
- <https://archlinux.org/packages/core/x86_64/btrfs-progs/>
- <https://archlinux.org/packages/core/x86_64/cryptsetup/>

Moving package pages do not pin versions; the future dated dossier does.

## Target-Specific Inputs Still Required

- exact disk and confirmation that its old data may be destroyed;
- backup location, sample restore, and booted recovery medium;
- locale, keyboard, timezone, hostname, and network enrollment;
- APX owner display name and secret enrollment;
- firmware/boot behavior and absence of unsupported disk topology.

These facts belong in the final dossier and cannot be guessed by source code.
