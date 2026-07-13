# Closed Package Resolution Experiment v1

Status: real offline resolution passed on 2026-07-12; package and signature
downloads remain separately approval-blocked.

## Inputs and Isolation

The operation reopened the exact verified `core.db` and `extra.db` identities,
copied them into a new mode-0700 `/tmp` root, and ran pacman print-only twice
with a fresh empty installation root and local package database. Database,
cache, GnuPG, hook, log, servers, architecture, and the six seeds were fixed.
No refresh, download, install, extraction, scriptlet, or host database was used.

Both outputs matched byte-for-byte. Each selected row was cross-checked against
the strict database parser's version, architecture, filename, compressed size,
SHA-256, encoded signature, repository, and exact dated URL.

## Result

- packages: 138;
- unique names and filenames: 138 each;
- aggregate package bytes: 128,264,129;
- manifest digest:
  `574f5d31e7c4ee46b1982fe2baf285d014ba0d712e91aea6d00413ba8fe5e3f9`;
- serialized evidence SHA-256:
  `d8e097489369c2898c5433f416c2ddf5287ed24c04403b36c1e7c3ca7cda301d`.

The mode-0600 evidence is preserved at
`/tmp/apx-package-resolution-20260711-v1/resolution-manifest.json`.

## Remaining Boundary

The next separately approved operation must download exactly these 138 package
files and 138 detached `.sig` files within the existing 4 GiB policy, then
verify reopened bytes and signers before extraction. Existing database and
resolution evidence cannot be silently replaced or regenerated.
