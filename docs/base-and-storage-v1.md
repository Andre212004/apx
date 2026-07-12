# APX Base and Storage v1

Status: fixed proposal for the disposable headless experiment; host creation is
not authorized.

## Purpose

This proposal defines the smallest reproducible Arch base and storage ownership
needed to test one isolated Environment. It deliberately excludes graphical
software, GPU access, personal data, assistants, and the Hub interface.

## Base Manifest

The initial headless base declares these Arch package names:

```text
base
ca-certificates
dbus-broker
iproute2
iputils
sudo
```

The resolved dependency list and exact versions are unknown until the approved
experiment locks a repository snapshot. Creation must record the repository
source, signing-key state, package filenames, versions, architectures, and
cryptographic digests. A moving mirror response is not a reproducible base.

Read-only resolution against the host's existing package information on
2026-07-11 reported these seed candidates:

```text
base 3-3 any
ca-certificates 20240618-1 any
dbus-broker 37-3 x86_64
iproute2 7.1.0-1 x86_64
iputils 20250605-1 x86_64
sudo 1.9.17.p2-6 x86_64
```

This is evidence only. It neither locks the repositories nor lists resolved
dependencies, so these versions are not yet an accepted base manifest.

A repository-only resolution using freshly downloaded `core.db` and `extra.db`
on the same date produced:

```text
Resolved packages: 138
Resolved manifest SHA-256: 64a8b553a8f9c390fc3e907cea845125cdee8d774a66c8991b1d936a3275b02b
Packages already present in the host cache: approximately 119 MiB
core.db SHA-256: 64100fe591ce94591f1623424db81b9b163b8d89e3218ff74554247054854fef
extra.db SHA-256: a50306a945a24a9564fc59a6531c16a9d90a92c669a180b574379778deb2770e
```

The database endpoints did not publish detached `.sig` files. These hashes
identify the observed resolution but do not authenticate it. Acceptance still
requires downloading every resolved package and verifying its package signature
with the Arch keyring before populating the base.

## Snapshot Evidence Contract

The repository now models snapshot evidence without downloading or installing
anything. A candidate snapshot is accepted as `verified` only when all of the
following are true:

- schema version and snapshot identity are canonical;
- the source is an exact dated Arch Linux Archive location, not a moving mirror;
- the source URI date matches the declared snapshot date;
- `core` and `extra` database SHA-256 digests are recorded;
- the fixed seed package policy matches this document;
- the complete resolved package list is non-empty, uniquely named, and
  canonically ordered;
- every seed package occurs in the resolved list;
- every package records version, architecture, safe basename, SHA-256 digest,
  successful signature verification, and signer fingerprint;
- the canonical resolved-manifest digest matches the package evidence;
- the acquisition-plan digest, exact keyring artifact and hash, independent
  trust-bootstrap digest, and verification-tool identity are recorded;
- an independent second-pass digest matches that closed provenance subject and
  the second pass is explicitly complete.

Malformed structure, a moving source, missing seeds, duplicates, unsafe
filenames, or digest disagreement classify the candidate as `rejected`.
Structurally valid evidence with an unverified signature or absent signer is
`verification-incomplete`. Only complete evidence is `verified`.

The evidence digest identifies the closed candidate manifest. It is not a
substitute for package signature verification, an approval reference, or a
fresh check that the downloaded bytes match the recorded package hashes. No
current real snapshot artifact satisfies this contract yet.

Schema-v1 JSON parsing is strict and bounded: duplicate or unknown fields,
wrong scalar types, package schema extensions, non-boolean signature results,
oversized input, and excessive package counts are rejected. Canonical
serialization round-trips to the same typed manifest. Parsing remains separate
from assessment: syntactically valid evidence can still be rejected or
verification-incomplete.

A signature boolean alone is never sufficient for `verified`. Missing or
incomplete independent validation produces `verification-incomplete`; unsafe
keyring identity or disagreement among provenance digests is rejected.

The bounded production and independent-validation procedure is specified in
[base-snapshot-acquisition-v1.md](base-snapshot-acquisition-v1.md). That
procedure is documented but not approved for execution.

The base excludes desktops, browsers, editors, games, Steam, development tools,
Odysseus, Codex, GPU userspace, credentials, secrets, copied live-machine
identity, AUR packages, and unreviewed installation scripts.

## Software Installation Boundary

After creation, every installer is local to the Environment: `pacman`, `yay`,
`apt` when supplied by a future compatible template, Flatpak, language package
managers, vendor installers, and scripts. None may see the host root, package
database, or another Environment.

The first experiment uses only `pacman` and one harmless fixture package. It
records the host package database before and after the test and requires it to
remain byte-for-byte and semantically unchanged.

## Proposed Storage Identities

```text
/var/lib/apx/bases/<base-id>/root
/var/lib/apx/environments/isolation-trial/root
/home/apx-isolation-trial
/var/lib/apx/operations/isolation-trial.json
/var/lib/apx/environments/isolation-trial.json
```

These are future host paths, not current directories. Base content is immutable;
the Environment root and home are separate writable Btrfs subvolumes. Root and
home require distinct UUIDs, different from the base and every other registered
Environment. A pathname alone is not ownership evidence.

## Initial Resource Budget

```text
Virtual CPUs: 2
Memory high threshold: 2 GiB
Memory maximum: 3 GiB
Process maximum: 512
Writable root budget: 8 GiB
Home budget: 2 GiB
Network: private, outbound only through host mediation
Devices: only minimal pseudo-devices required to boot
```

These are experiment limits, not final defaults. If Btrfs quota support cannot
be confirmed and enforced, Stage 2 is blocked rather than silently unlimited.

## Identity and Local Administration

The host account remains `apx-isolation-trial`. The container has its own user
and group database. Local `sudo` administers only the container userspace. It
receives no host socket, helper, package database, root bind, or device that
turns local administration into host administration.

The internal UID/GID mapping comes from a non-overlapping recorded range. It is
not inferred from the visible host account UID.

## Creation Preconditions

- all proposed paths and identities are authoritatively absent;
- the source and complete resolved package manifest are verified;
- storage, quota support, and capacity are confirmed;
- subordinate UID/GID ranges are valid and non-overlapping;
- systemd machine and image names are unused;
- no conflicting registration or incomplete marker exists;
- the exact plan digest is current;
- Stage 2 has explicit approval.

Snapshot `verified` status satisfies only the source-and-manifest precondition.
It does not authorize downloads, base extraction, Btrfs creation, container
startup, or cleanup.

## Required Postconditions

- base, root, and home storage UUIDs match their records;
- base content is not writable through the Environment;
- local installation changes only Environment-owned state;
- host package database, lock, package list, and files remain unchanged;
- no Hub or Development data is visible;
- resource limits are active and measured;
- shutdown leaves no process, mount, network interface, or machine record;
- registration is published only after every check passes;
- incomplete state is removed only after final verification.

## Rollback Boundary

Before first boot and user modification, an operation-owned empty or verified
unused resource may be removable after fresh proof. After package installation,
login, user data, external modification, publication, or uncertain evidence,
automatic deletion is forbidden. Cleanup then requires separate destructive
approval with explicit data-loss scope.
