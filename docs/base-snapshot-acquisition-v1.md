# APX Base Snapshot Acquisition v1

Status: protocol ready for review; acquisition and host mutation are not
authorized.

## Purpose

This protocol defines how a future approved operation produces the first real
APX headless-base snapshot artifact. It closes the gap between a package-name
resolution and evidence that the exact package bytes came from a fixed Arch
Linux Archive date and passed Arch package-signature verification.

The protocol does not create a base filesystem, install a package, modify a
keyring, write under `/var/lib/apx`, or start a container. Acquisition is a
network and filesystem effect and requires its own approval even though its
output is still non-executable evidence.

## Fixed Inputs

The operation accepts no caller-selected mirror, package, path, key, command,
or verification flag. Policy version `base-snapshot-acquisition-v1` fixes:

- source kind: `arch-linux-archive`;
- repository set: `core`, `extra`;
- architecture set: `x86_64`, plus repository packages marked `any`;
- seed packages: `base`, `ca-certificates`, `dbus-broker`, `iproute2`,
  `iputils`, and `sudo`;
- snapshot date selected by a reviewed repository change;
- HTTPS URI derived exactly from that date;
- output schema version 1;
- resolver/acquirer: pacman sync planning plus download-only with fixed
  operation-owned config, database, cache, and GnuPG paths;
- primary verifier: `pacman-key --verify` with an operation-owned `--gpgdir`;
- independent pass: export only the already trusted signer public key from the
  pacman trust store into operation staging, then use `gpgv` over reopened
  package/signature files;
- staging and publication rules described below.

Changing any fixed input creates a different policy revision and invalidates a
previous plan digest. A Hub request may select an already reviewed base ID but
must never inject these values.

`src/apx_acquisition.py` implements the pure acquisition boundary. It validates
the exact HTTPS origin/date/path, repository and architecture set, safe unique
canonical filenames, per-file and aggregate bounds, and supplied post-transfer
URI, size, digest, regular-file, symlink, and completion evidence. Redirects or
any identity disagreement are rejected. The module has no network client and
does not open, create, or delete files.

`src/apx_staging.py` provides the disposable Level 2 filesystem fixture for
the staging rules. It exclusively reserves a new operation directory under a
caller-provided mode-0700 parent, binds it to the approved plan digest, streams
within fixed bounds, verifies exact length and SHA-256, fsyncs, and publishes
without overwriting. Interrupted or mismatched files retain a `.partial`
identity and cannot become accepted input. This fixture never chooses
`/var/lib/apx` and is not production executor storage.

`src/apx_downloader.py` implements the bounded streaming boundary using an
injected non-redirecting HTTPS opener and protected staging sink. It requires
status 200, unchanged final URI, a single valid Content-Length, and the fixed
maximum plus any already known exact size and digest. Early EOF, excess bytes,
non-byte responses, network/read/sink failure, and digest disagreement abort.
The current tests provide fake responses; no production opener or network
execution command is implemented.

`src/apx_http.py` supplies the fixed direct transport opener. Environment
proxy discovery is disabled, redirects and cookies are absent, TLS uses system
CA validation with hostname checking and a TLS 1.2 minimum, and the GET request
contains only fixed content, encoding, connection, and APX user-agent headers.
It rejects any URI authority or suffix change and sanitizes transport errors.
Unit tests inject an opener; this does not constitute network approval or a
real download.

`src/apx_transfer.py` composes the bounded downloader with the disposable
streaming staging writer. Bytes move directly into one exclusive `.partial`
regular file, remain bounded without whole-file memory buffering, and receive
their final non-overwriting name only when independently computed size and
SHA-256 evidence agree across both boundaries. Failure preserves the partial
for recovery classification and refuses an implicit retry. This composition
still uses only fake responses and caller-provided disposable directories.

The separately authorized first real database-only acquisition is recorded in
`database-acquisition-experiment-v1.md`. It used the fixed zero-argument
`src/apx_database_acquisition.py` operation, stayed within 8,818,209 aggregate
bytes, and independently reproduced both file hashes. This closes the real
repository-database transfer boundary only; package resolution, package and
signature downloads, complete manifest verification, base extraction, and
Stage 2 remain blocked.

`src/apx_repository_db.py` implements the strict no-extraction database parser.
It rechecks the staged regular-file digest, bounds archive expansion and member
count/size, rejects traversal and unexpected members, and validates the package
identity, architecture, sizes, SHA-256, encoded signature, uniqueness, and
dependency fields needed to check resolver output independently.

The first real offline closed resolution is recorded in
`package-resolution-experiment-v1.md`. `src/apx_resolution.py` runs two
print-only passes against an empty root and only copied staged databases, then
cross-checks every result with repository metadata. It selected 138 unique
packages totaling 128,264,129 bytes. Package and detached-signature acquisition
remains separately approval-blocked.

## Trust Inputs

Package authenticity depends on a reviewed Arch Linux keyring artifact. For the
first experiment, the trusted host is an explicit trust anchor: an authoritative
read-only observation must freeze the installed `archlinux-keyring` package
version, relevant `/usr/share/pacman/keyrings` regular-file identities and
hashes, and host package-database binding. That frozen evidence authenticates a
matching dated `archlinux-keyring` archive, which then supplies an isolated
operation-owned verification keyring. The operation records both sides of this
bootstrap, package signer fingerprints, every verification result, and tool
versions.

The live host keyring is never used implicitly or mutated. If the installed
package identity, files, ownership, hashes, or package-database evidence are
unavailable or inconsistent, bootstrap is blocked. Updating trust while
verifying the candidate is forbidden. An unknown, expired, revoked, or
otherwise unacceptable signer blocks the candidate; the operation must not
fetch a key opportunistically, locally sign a new key, use `TrustAll`, or weaken
signature policy.

HTTPS protects transport but is not package authenticity. Repository database
hashes identify the exact observed indexes. The absence of detached database
signatures must be recorded and does not waive package-signature verification.

This follows Arch's documented model: official packages require trusted
signatures while database signatures remain optional, `pacman-key` supports an
alternate GnuPG directory and detached verification, and pacman supports
print/download-only operation with alternate database/cache/GnuPG paths. See
[Arch package signing](https://wiki.archlinux.org/title/Pacman/Package_signing),
[pacman-key(8)](https://man.archlinux.org/man/pacman-key.8), and
[pacman(8)](https://man.archlinux.org/man/pacman.8.en).

## Operation Phases

### 1. Plan

Render a deterministic, non-executing plan containing the policy version,
snapshot ID and date, derived archive URIs, repositories, architecture, seeds,
trust-input identity, resource ceiling, expected output location, and approval
state. Diagnostic text and timestamps are excluded from the plan digest.

### 2. Create isolated staging

After approval, create one new operation-owned staging directory at a fixed
policy path. It must be absent beforehand, must not be a symlink, and must have
sufficient capacity. Record its device/inode identity and create an incomplete
marker before the first download.

Staging must not be the host package cache, an Environment package cache, the
future immutable base, or a directory searched by the host package manager.
Existing files are never adopted.

### 3. Acquire repository databases

Download the dated `core` and `extra` databases once into staging with bounded
size and timeout. Record final URI, byte length, and SHA-256. Redirects outside
the fixed Arch Linux Archive origin are rejected. A changed response during a
retry invalidates the operation rather than silently replacing evidence.

### 4. Resolve a closed package set

Resolve the fixed seeds and all dependencies exclusively against the staged
databases. The resolver must not consult live host sync databases, local
package state, AUR metadata, a moving mirror, or an unrecorded cache.

The result is uniquely named and canonically ordered. Each record contains
name, version, architecture, repository, filename, expected size when
available, and dependency relationship. Duplicate names, unresolved
dependencies, architecture disagreement, traversal, or replacement after
resolution aborts the operation.

### 5. Acquire packages and signatures

Download exactly the resolved filenames and detached signatures from the same
dated archive origin. Enforce per-file and aggregate byte ceilings. Partial
files retain operation provenance but are never eligible evidence. No package
hook, install script, archive extraction, or transaction runs during
acquisition.

### 6. Verify bytes and signatures

For every package, verify its safe basename, resolved metadata, SHA-256,
detached signature, accepted signer fingerprint, and embedded name, version,
and architecture without extraction or script execution.

One failure rejects or leaves the entire candidate verification-incomplete;
there is no partial accepted base. Diagnostics are bounded and sanitized and
remain outside the canonical evidence digest.

### 7. Independently validate evidence

Build canonical schema-v1 evidence and calculate database, package, resolved
manifest, and complete-evidence SHA-256 digests. A separate pass reopens every
staged regular file without following symlinks, recomputes hashes, repeats
signature and metadata checks, and invokes the repository's typed assessment.
It must not trust in-memory acquisition results.

### 8. Publish evidence, not a base

Only a `verified` result may be atomically published as a repository-reviewed
snapshot evidence artifact. Publication includes no package bytes unless a
later storage policy selects a content-addressed artifact store. It does not
authorize extraction, Btrfs creation, installation, registration, or Stage 2.

## Evidence Schema

The canonical artifact contains bounded structured evidence:

```text
schema_version
snapshot_id
source_kind
source_uri
snapshot_date
database_sha256[]
seed_packages[]
packages[]:
  name
  version
  architecture
  filename
  sha256
  signature_verified
  signer_fingerprint
resolved_manifest_sha256
acquisition_plan_digest
keyring_artifact
keyring_sha256
trust_bootstrap_digest
verification_tool
independent_validation_completed
independent_validation_digest
```

The journal additionally records repository membership, dependency edges,
sizes, trust provenance, tool versions, approval reference, operation identity,
and diagnostics. The artifact contains no credentials, environment dump,
hostnames, arbitrary commands, timestamp identity, or executable content.

Before acquisition, `src/apx_trust_evidence.py` can seal a supplied readiness
report to one exact acquisition-plan digest. The bounded canonical seal records
check identities and classifications but stores only a SHA-256 digest of each
raw observation. It also binds canonical UTC observation time, observer class,
and an optional preceding seal. Restricted-observer evidence can never become
verified; it remains pending until repeated through the future authoritative
executor. Any blocked check blocks the seal in every observer context. This is
a pure contract and parser, not a host evidence store or executor attestation.

## Resource and Failure Bounds

The plan states maximum database bytes, individual package bytes, aggregate
bytes, package count, timeouts, and staging capacity. Exceeding a bound aborts.

Failures are classified as `no-effect`, `owned-partial`, `evidence-published`,
or `ownership-uncertain`. Automatic cleanup may remove only freshly proven,
operation-owned, unpublished staging that has not been externally modified.
Published evidence, uncertain resources, shared caches, and anything outside
the fixed staging identity require review. Cleanup remains an explicit
destructive approval.

## Acceptance Gates

Acquisition passes only when:

- every fixed input and derived URI matches the approved plan;
- database identities and hashes remain stable across validation;
- dependency resolution is closed and deterministic;
- every package and seed is present exactly once;
- all hashes, signatures, signers, and package metadata validate;
- the independent pass reproduces the canonical digests;
- no host package database, lock, cache, keyring, service, or Environment state
  changed;
- the typed assessment returns `verified`;
- evidence is published atomically;
- Stage 2 remains explicitly blocked.

## Open Approval Inputs

Before execution, review must authoritatively record the installed keyring and
tool versions, bind the matching archive artifact and digest, approve the fixed
staging/publication parents and resource ceilings, confirm redirect policy and
cleanup authority, and produce the expected real package manifest.

Until then, the 2026-07-11 hashes remain observation evidence only.

The repository fixes a candidate date, derived source, staging/evidence paths,
resource ceilings, phases, blockers, and deterministic digest in `apx host
snapshot-plan`. The trust mechanism and tool roles are selected; their exact
host-observed versions, keyring file/archive hashes, real manifest, signatures,
authoritative capacity evidence, and approvals remain deliberately unresolved
rather than guessed.

`apx host snapshot-readiness` is the repository's fixed observer for the first
two identity blockers. It checks only fixed executable names, fixed installed
package queries, fixed version queries, and the three fixed Arch keyring files.
Symlinks or non-regular keyring paths block readiness. The observer never
refreshes/imports/signs keys and never downloads or writes.

A human-authorized host execution observed `archlinux-keyring 20260707.1-1`,
pacman `7.1.0.r9.g54d9411-2`, pacman-key `7.1.0`, and GnuPG `2.4.9-1`; package
verification reported 17 files and zero altered files. The fixed keyring hashes
are now bound into the plan:

```text
archlinux.gpg      4f9f55c7702ff580f808a86e4eeed7d471252684c03089427c69796e88253516
archlinux-revoked  aafbc33d6be7e200dd6226dbb467623a38a00db431826258bccfaf5cebfef6a1
archlinux-trusted  384c7daf07a89ec6610859142b009ca5c0b3062ed3ab2d3c50629fef9d002e8f
```

Their canonical bootstrap digest is
`8e0b6245df90b87e501d3a315a2536a6d8d93670e27a27224c6b8a9c1b664ab6`.
The observer correctly retained `requires-host-confirmation` because the
prototype has no privileged attestation channel; future executor attestation
and replay-resistant approval binding remain required.

## Keyring Bootstrap Acquisition Result

A separately approved bounded acquisition downloaded only the matching package
and detached signature into operation-owned `/tmp` staging. No package was
installed and no archive content was written outside staging.

```text
package: archlinux-keyring-20260707.1-1-any.pkg.tar.zst
size: 1270069 bytes
SHA-256: b47fc9c8066377e73d72bdb6a166bbbd829d5dcc745e424ef32436bd673cbc0d

signature size: 119 bytes
signature SHA-256: 100aea3aa09b14e818e84ff26ffcaed5c340e638942bc8949c2bfba7a19ee091
signer: Christian Hesse <eworm@archlinux.org>
fingerprint: 0429897DE5F3BDAC537A30696D42BDD116E0068F
```

`pacman-key --verify` reported a full-trust good signature. Direct `gpgv` and
direct `gpg` against `/usr/share/pacman/keyrings/archlinux.gpg` failed because
that distribution keyring is not directly consumable as a GnuPG key database;
this failed attempt is retained as evidence rather than hidden. Exporting only
the already trusted signer public key from `/etc/pacman.d/gnupg` into the
operation homedir produced a keyring with SHA-256
`0fcc071d58801d83e29a68f0ac0008c142f675cdfd8d8b7a27362ac1ec578470`.
`gpgv` then independently reported a good signature over the reopened files.

Read-only `.PKGINFO` inspection confirmed:

```text
pkgname = archlinux-keyring
pkgver = 20260707.1-1
arch = any
packager = Christian Hesse <eworm@archlinux.org>
```

This closes the matching keyring archive identity, digest, signature, signer,
and metadata blocker. It does not authenticate a complete base manifest,
authorize further downloads, or provide future executor attestation.
