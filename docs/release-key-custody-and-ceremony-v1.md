# APX Release Key Custody and Ceremony v1

Status: accepted operational boundary and rehearsal plan. No APX production key
exists and no key generation is authorized by this document.

## Trust Roles

APX uses two distinct roles:

- an offline root authority, used only to certify or revoke release-signing
  identities and publish a new trust bundle;
- a release signer, used offline to sign one exact reviewed package digest and
  its release evidence.

The root private material never enters the normal Arch host, Hub, Development,
Codex, Git repository, build machine, networked machine, backup cloud, or APX
Environment. The release signer also remains outside Hub and Development. Only
public certificates, fingerprints, revocations, signed trust-bundle metadata,
and sanitized ceremony evidence may enter the repository or installed system.

A Development signature may prove where bytes came from, but it is never an
APX admission signature and is not certified as a release signer.

## Required Physical Layout

Before production generation, the owner prepares:

1. one explicitly disposable computer booted from reviewed read-only media;
2. networking physically disabled and absence of radios/network interfaces
   recorded;
3. one separate clean verification computer that receives public material and
   test signatures only;
4. two encrypted root-backup media stored in different physical locations;
5. two encrypted release-signer backup media stored separately from each other
   and from the active signing device;
6. printed or otherwise offline-recorded fingerprints and recovery instructions;
7. an offline record of media identities, seals, locations, access events, and
   destruction/replacement events.

Private-key backups are never copied merely to make a test convenient. At least
one restoration is proven on the disposable offline computer before the
original ceremony is accepted. Recovery evidence records success and public
fingerprints, never passphrases or private bytes.

## Rehearsal Before Production

The complete ceremony is first run with visibly labelled disposable rehearsal
keys. It must follow this order:

1. approve the exact cryptographic profile and tool/media identities;
2. prove the generation computer is disposable and offline;
3. create a rehearsal root, release signer, and revocation material;
4. certify the rehearsal release signer with the rehearsal root;
5. export the public trust bundle and record all fingerprints;
6. create the required encrypted backups;
7. erase the working copy, restore one root and one signer backup, and prove the
   same public fingerprints;
8. sign a fixed harmless test digest;
9. verify certification, signature, expiry, and revocation behavior on the
   second clean computer using only the public trust bundle;
10. simulate signer compromise and prove that a signed revocation/update causes
    the old signer to be rejected;
11. destroy all rehearsal private material and record sanitized absence evidence;
12. review the record before authorizing a separate production ceremony.

Repository unit tests or a paper walkthrough do not count as this physical
rehearsal. The rehearsal requires specifically approved disposable machines and
media outside this repository.

## Production Ceremony

Production follows the successfully reviewed rehearsal without shortcuts. The
final cryptographic profile, tool versions and hashes, boot-media identity,
time source, expiry, owner identity, public fingerprints, backup-media IDs,
restore proof, revocation artifacts, and trust-bundle digest are bound into one
immutable ceremony record.

The production ceremony stops and preserves evidence if:

- networking cannot be proven absent;
- any media, tool, clock, identity, or expected fingerprint is ambiguous;
- a private file reaches an unapproved device;
- backup restoration or independent verification fails;
- generated material differs from the approved profile;
- the record cannot explain every private-material copy.

Stopping never authorizes reuse of uncertain key material. The owner must make
an explicit preserve, destroy, or incident decision using the offline record.

## Signing a Release

The release signer receives one bounded transfer containing only the exact
package digest, source revision, package-definition digest, reproducibility
evidence digest, policy generation, and release identity. It does not receive a
source checkout, build commands, credentials, or caller-selected output path.

The signer displays those identities for confirmation and emits a detached
signature plus sanitized signing evidence. Verification on a separate clean
system must bind the signature to the certified signer, current trust bundle,
non-expired policy, non-revoked status, and exact package bytes. Signing does not
itself admit or install the package.

## Rotation, Revocation, and Recovery

- A release signer is rotated before expiry, on policy/tool change, media loss,
  suspected disclosure, unexplained signing, or failed inventory.
- Root use is exceptional: signer certification/revocation, root rotation, and
  trust-bundle recovery only.
- Compromise causes immediate stop of signing/admission, preservation of
  evidence, offline revocation, a new trust bundle, and explicit review of every
  release signed during the uncertain interval.
- Loss of the active signer uses a proven backup only after inventory and
  fingerprint verification. Ambiguous loss is treated as compromise.
- Loss or compromise of the root requires the separately documented root
  recovery/rotation path; a new self-declared root is not silently trusted.
- Installed APX retains the previous accepted public trust bundle for bounded
  rollback, but never accepts an older bundle that omits a known revocation.

## Remaining Cryptographic Decision

The operational boundary is accepted, but the exact OpenPGP algorithm profile,
key capabilities, expiration periods, GnuPG version, entropy/time checks, and
trust-bundle wire schema remain to be selected and compatibility-tested. Until
those are closed and the physical rehearsal passes, production key generation
and a trusted APX bootstrap package remain blocked.
