# Closed Package and Signature Acquisition Experiment v1

Status: separately authorized real acquisition passed on 2026-07-12; files are
preserved pending cryptographic signer verification or separate cleanup.

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

## Remaining Boundary

Files remain under operation
`op-574f5d31e7c4ee46b1982fe2baf285d0` in the authorized root. Database-embedded
signature fields do not replace detached signature verification. The next
stage must verify every reopened package/signature pair with the isolated
trusted keyring, record accepted signer fingerprints, repeat verification with
the independent GnuPG path, and reject the entire candidate on one failure.
Extraction and Stage 2 remain blocked.
