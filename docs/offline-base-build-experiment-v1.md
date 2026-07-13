# Offline APX Root Build Experiment v1

Status: passed on 2026-07-12; preserved for the first console boot preview.

## What this means

This did not reinstall Arch Linux on the computer. The existing Arch system was
not a destination. The experiment organized the minimum Arch files for one
future APX Environment underneath the private temporary path
`/tmp/apx-first-console-build-v1/rootfs`.

The host continues to own the kernel and hardware. The prepared root contains
the future Environment's own programs, configuration and package database. A
later Steam installation must target an Environment root like this one rather
than the host.

## Authorized boundary

The user authorized exactly the already verified 138 packages, offline pacman
installation into a new `/tmp/apx-first-console-build-v1`, package scripts and
hooks confined to that root, and a 1 GiB ceiling. Boot, downloads, host package
changes, real host accounts, services, Btrfs, system configuration, previous-
area cleanup and writes outside the destination were excluded.

## Result

- packages recorded by the internal pacman database: 138;
- logical bytes: 559,470,037;
- allocated bytes: 614,490,112;
- files owned by Development UID 1002: zero;
- remaining special or GPG runtime entries: zero;
- machine identity: unique candidate value, recorded only by SHA-256;
- final report digest:
  `741fe1c332c334f9f0667b295ae98e7de686c752c3f415e169e0e48912535b68`.

Keyring setup and package installation ran under a private network namespace.
Every package hash was rechecked before the first destination directory was
created. Libalpm runs hooks and scriptlets inside the alternate root. The
operation did not boot candidate content and did not install into the host.

## Remaining boundary

This root is ready for an exact boot preview, not yet authorized to boot and not
an admitted reusable base release. The preview must fix the process, namespace,
network, device, resource, read-only/writable-layer, timeout, observation,
shutdown and cleanup boundaries. Hyprland is not part of this minimal console
root; graphical role construction follows a successful lifecycle test.

## Reconstruction rule

A later reconstruction from the same authenticated manifest may legitimately
produce different byte totals and a different machine identity because pacman,
GnuPG, and first-root identity material contain per-run state. Finalization must
therefore validate the canonical build-report digest and every closed semantic
invariant—manifest, signature evidence, package counts, byte ceilings,
ownership, and identity presence—rather than requiring the digest of this one
historical run. The resulting final report remains bound to the exact rebuilt
root and is not interchangeable with the historical report above.
