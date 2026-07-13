# APX Clean-Install Dossier Schema v1

Status: closed pure readiness contract. It cannot partition, format, install,
approve, authenticate, download, or mutate a machine.

The dossier consumes target evidence, Arch snapshot/package evidence, and APX
bootstrap evidence. It returns only `blocked` or
`ready-for-separate-approval`. The latter means the evidence is complete enough
to render a destructive plan; it is not permission to execute it.

## Required Target Evidence

- canonical target ID and SHA-256 disk identity evidence;
- x86_64 and UEFI;
- at least 64 GiB on one explicitly selected disk;
- disk is not the running system, has no mounted child, and has no unsupported
  dual-boot/RAID/LVM/multi-disk dependency;
- backup manifest plus successful sample restore;
- recovery-medium digest plus successful boot test;
- working network and trusted time for evidence acquisition;
- fixed locale, keymap, timezone, and hostname;
- CPU vendor `amd` or `intel` for exact microcode selection.

## Required Supply-Chain Evidence

- one dated Arch Linux Archive snapshot;
- closed resolved package manifest and complete signature verification;
- pinned APX source revision and bootstrap package digest;
- APX offline root and release-signer fingerprints;
- verified APX detached signature;
- confirmed signing-key custody/recovery process;
- reviewed executor boundary and completed disposable-install rehearsal.

## Fixed Plan

The canonical plan binds the ten stages in `clean-install-foundation-v1.md`,
the exact target identity, configuration, dated Arch source, package manifest,
microcode package, APX identities, irreversible consequences, and the rule that
fresh strong disk approval is still required.

No password, LUKS passphrase, private key, command, device path, partitioning
argument, mount option, or caller-selected effect appears in the dossier.
Secrets are enrolled only through the future trusted executor interaction.

Unknown fields, duplicate JSON fields, booleans used as integers, malformed
digests/IDs/configuration, missing evidence, and inconsistent CPU/microcode
selection fail closed.
