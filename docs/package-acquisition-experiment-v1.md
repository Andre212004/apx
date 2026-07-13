# Closed Package and Signature Acquisition Experiment v1

Status: real acquisition and double offline signature verification passed on
2026-07-12; files are preserved pending package-metadata inspection or cleanup.

## Authorization

The user authorized exactly the 138 packages and 138 detached signatures bound
to resolution manifest
`574f5d31e7c4ee46b1982fe2baf285d014ba0d712e91aea6d00413ba8fe5e3f9`,
only from the dated Arch Linux Archive, with a combined maximum of 137,308,097
bytes into `/tmp/apx-package-acquisition-20260711-v1`. Installation,
extraction, execution, other downloads, and cleanup were excluded.

## Result

- package files: 138;
- detached signature files: 138;
- package bytes: 128,264,129;
- signature bytes: 30,687;
- combined bytes: 128,294,816;
- partial files: zero;
- unexpected files: zero.

`src/apx_package_acquisition.py` accepted no arguments, reparsed and verified
the canonical manifest before creating a new root, generated exactly alternating
package/signature requests, streamed each through the fixed direct HTTPS and
protected staging boundaries, and stopped if the authorized aggregate would be
crossed.

An independent reopen checked all 138 package sizes and SHA-256 values against
the repository-bound manifest. It also confirmed every signature is a non-empty
regular mode-0600 file within the 64 KiB bound. All 276 identities passed.
Quotas remained full, consistent, and without limit override. No package was
installed, extracted, or executed.

`src/apx_signature_verification.py` then reopened every package and detached
signature. It verified all 138 pairs with GnuPG, required each signing identity
to be a current Arch master or validly certified by at least three of the five
current Arch masters, rejected Arch's revoked identities, and repeated every
check with the separate `gpgv` program. Both passes identified the same signer
for every package. The receipt contains 15 trusted primary signing identities
and has digest
`468116fb5277d91a099d0d4adbc5ca6579a5962965b062c0b6a1f09db9e4ea84`.

## Remaining Boundary

Files remain under operation
`op-574f5d31e7c4ee46b1982fe2baf285d0` in the authorized root. The signature
receipt is under `/tmp/apx-signature-verification-20260711-v1/`. The next stage
may inspect bounded package metadata such as `.PKGINFO` without executing
package content. It must bind name, version, architecture and dependencies to
the verified receipt before any disposable base extraction. Extraction and
Stage 2 remain blocked.
