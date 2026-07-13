# Arch Repository Database Acquisition Experiment v1

Status: separately authorized real network acquisition passed on 2026-07-12;
files preserved pending later package resolution or separately approved cleanup.

## Authorized Scope

The user authorized exactly `core.db` and `extra.db` from the Arch Linux
Archive dated 2026-07-11, with a maximum of 64 MiB per file and 128 MiB total,
into a new `/tmp` staging root. Installation, extraction, other downloads, and
cleanup were excluded.

The zero-argument fixed operation used plan digest
`f1cce5db72b63a928a77f0bc3854cd01f1a25408b158e0df37ce8bfd5e2f4a63`
and operation ID `op-f1cce5db72b63a928a77f0bc3854cd01`.

## Result

| File | Bytes | SHA-256 |
|---|---:|---|
| `core.db` | 128,880 | `12aea0ea6b5a16125064a19c7e8415d22e19b4517896d09eb2eb6cb2ee60b295` |
| `extra.db` | 8,689,329 | `5a5f994a35a6cf65ff2adb6b5f61aa4349aba62f8ee2a286d45b8d80819f43f7` |

Aggregate transfer was 8,818,209 bytes. Both files were streamed into exclusive
partial staging and published only after bounded transfer and staging evidence
agreed. An independent reopen and `sha256sum` reproduced both hashes.

The operation directory and files are owned by UID/GID `1002:1002` with modes
`0700` and `0600` respectively. Exactly two regular files are present; no
partial or extra entry exists. Quotas remained full, consistent, and without
limit override. No package was installed, extracted, or executed.

## Preserved Boundary

The evidence remains at
`/tmp/apx-arch-databases-20260711-v1/op-f1cce5db72b63a928a77f0bc3854cd01`.
It is not yet a verified base. The next stage may reopen these exact identities
to resolve a closed package manifest. It must not silently redownload or replace
them. Cleanup requires separate approval and complete-cleanup verification.
