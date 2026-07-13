# APX Release Candidate Schema v1

Status: closed repository contract for the first Hub candidate. It performs no
file import, archive extraction, signature verification, catalogue admission,
Hub creation, or host mutation.

## Scope

V1 describes one immutable headless Hub root candidate produced in Development.
It is deliberately narrower than the complete future promotion system.

The candidate metadata is canonical UTF-8 JSON with exactly these fields:

| Field | V1 rule |
|---|---|
| `schema_version` | integer `1` |
| `candidate_id` | `candidate-` plus 32 lowercase hex characters |
| `build_operation_id` | `build-` plus 32 lowercase hex characters |
| `role` | `hub-headless` |
| `architecture` | `x86_64` |
| `source_revision` | 40 or 64 lowercase hex characters |
| `source_tree_sha256` | lowercase SHA-256 |
| `base_release_id` | bounded opaque release identifier |
| `base_release_digest` | lowercase SHA-256 |
| `role_definition_digest` | lowercase SHA-256 |
| `package_manifest_digest` | lowercase SHA-256 |
| `normalized_root_digest` | lowercase SHA-256 |
| `build_evidence_digest` | lowercase SHA-256 |
| `test_evidence_digest` | lowercase SHA-256 |
| `reproducibility_evidence_digest` | lowercase SHA-256 |
| `sanitization_evidence_digest` | lowercase SHA-256 |
| `artifact_format` | `apx-root-tar-zst-v1` |
| `artifact_size` | integer from 1 byte through 4 GiB |
| `artifact_member_count` | integer from 1 through 500,000 |
| `artifact_sha256` | lowercase SHA-256 |
| `backend` | `systemd-nspawn-headless-v1` |
| `policy` | `apx-hub-headless-v1` |
| `executor_protocol` | `apx-executor-v1` |
| `preferences_schema` | `apx-hub-preferences-empty-v1` |

Unknown, duplicate, missing, wrongly typed, noncanonical, empty, or oversized
values fail closed. JSON booleans are not integers. The complete metadata is at
most 64 KiB. Its candidate digest is SHA-256 over canonical JSON with sorted
keys and compact separators; it is calculated rather than stored inside itself.

The artifact digest identifies bytes but does not verify archive safety,
provenance, signature, package contents, sanitization, or admission. V1 parsing
therefore returns `parsed-untrusted`, never `verified` or `admitted`.

## Import Plan

A pure import plan binds:

- candidate and build identities;
- candidate metadata digest;
- artifact format, size, member count, and digest;
- fixed quarantine policy `apx-quarantine-v1`;
- fixed effects: reserve new quarantine identity, copy bounded immutable bytes,
  verify copied digest, and publish only the quarantine object;
- fixed forbidden effects: execute, extract, overwrite, admit, create Hub,
  change host packages, or accept a caller-selected destination.

The plan contains no source path, destination path, command, executable, shell,
package arguments, UID/GID, device, mount, environment variable, hook, or
network URL. Physical import remains unimplemented.

## Deliberate Omissions

Signatures are not fields in v1 candidate metadata. They are separate evidence
bound later by the verifier/admission plan so a valid signature cannot make
malformed metadata parseable. Catalogue, approval, quarantine file identity,
archive member schema, and Hub replacement schemas remain separate contracts.
