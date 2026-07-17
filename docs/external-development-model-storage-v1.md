# APX External Development Model Storage v1

Status: repository proposal for review. No external disk, partition, encryption
container, filesystem, mount, bind, service, model relocation, or runtime change
is implemented or authorized by this document.

## Purpose

The owner intends to defer the Development-local coding model until a larger
external SSD is available. Extra capacity must not create a shared writable
host path or make model state visible to Hub or another Environment. This
proposal defines the evidence and lifecycle contract that must be closed before
the physical pilot uses that SSD.

The first admitted use is narrow: model weights and model-server cache for one
Development Environment. Repository source, credentials, Codex state, Qwen Code
configuration, prompts, conversations, indexes, and ordinary Development home
data remain in Development's existing root or home unless a later design says
otherwise.

## Required Boundary

The external model store must have:

- one recorded physical device identity, including transport, model, serial,
  size, and stable by-id path;
- encryption separate from the host root, with recovery material never stored
  in Hub, Development, Git, Codex, or the disk itself;
- a filesystem and health policy selected before formatting;
- one APX-owned attachment identity bound to one Development generation;
- no direct visibility in Hub, Minimal, another workload Environment, or a
  high-security Environment;
- no general writable host path exposed inside Development;
- model data and cache ownership mapped to the Environment-local service user;
- explicit capacity limits and host reserve checks;
- a stopped-state attach, detach, replacement, and recovery protocol;
- integrity evidence for each admitted model artifact;
- conservative behavior on disconnect, corruption, identity change, or missing
  keys.

The external SSD is capacity, not an authority source. It cannot contain APX
executor credentials, host trust keys, admission decisions, mutable catalogue
authority, Hub state, or the only recovery copy of the repository.

## Proposed Object and Lifecycle

The logical attachment record should bind:

```text
attachment identity
  -> physical device identity
  -> encrypted volume identity
  -> filesystem identity
  -> model-store identity
  -> Development name and generation
  -> service UID/GID mapping
  -> capacity ceiling and host reserve
  -> admitted model manifests
  -> lifecycle state
```

Changing any physical, cryptographic, filesystem, Environment-generation,
ownership, or model identity blocks automatic attachment. A replacement disk
is a new attachment, not an in-place continuation inferred from a mount path.

Proposed lifecycle states are `absent`, `locked`, `verified-detached`,
`attaching`, `attached-stopped`, `active`, `detaching`, `preserved-uncertain`,
and `failed`. Only a verified stopped Development may move between detached and
attached states. Activation requires the exact attachment already verified.

The repository now implements the safe operational subset in
`src/apx_external_model_lifecycle.py`. Its journal begins from one exact attach
preview, prepares and records each attach step separately, permits Development
activation only after complete attach evidence, requires a separate detach
approval, and records each detach step before reaching verified detached state.
It is an in-memory/pure contract with no host adapter.

## Visibility and Mount Direction

The runtime does not currently implement external attachments. A later adapter
must create a host-owned private mount that is not a general user workspace and
bind only the exact model-store subtree into Development. Hub must receive
neither the mount nor a proxy to the model server.

The bind target should be a fixed service-data path selected after the actual
Ollama package layout is observed. Do not guess `/var/lib/ollama`, create a
symlink from Development into an arbitrary host mount, set `OLLAMA_MODELS` to a
shared host directory, or grant Development the external filesystem root.

A read-only shared model artifact may be evaluated later, but v1 assumes one
Development-owned writable model store. Sharing writable caches, manifests,
locks, partial downloads, or conversation state between Environments is
forbidden.

## Encryption and Recovery

Before formatting, a target-bound dossier must record the exact external SSD
identity and confirm it is not the internal APX NVMe or another backup disk.
The destructive approval must name the external device identity and exact
effect. A path such as `/dev/sda` is never sufficient identity.

The encryption design must specify:

- LUKS version, parameters, and tool versions;
- how the owner unlocks the model store without exposing the secret inside an
  Environment;
- two separately stored recovery records or an explicit accepted alternative;
- a proven unlock and read-only recovery procedure from recovery media;
- key rotation and lost-device behavior;
- what sanitized evidence may enter the repository.

Automatic unlock from a key stored on the same host weakens the lost-device
boundary and is not accepted by this proposal.

## Capacity and Model Integrity

Admission must reserve space for the model, download staging, conversion,
indexes, cache growth, filesystem metadata, and recovery work. A larger disk
does not justify an unlimited attachment. The runtime must refuse activation
when the model store or internal host reserve is unhealthy.

Each model record should include upstream name, representation, licence,
source, exact served tag, observed byte size, available manifest/blob digests,
acquisition time, tool versions, maximum expansion budget, partial-download
state, and confirmation that credentials and conversations are excluded.

An Ollama tag alone is not a durable integrity identity. The eventual adapter
must capture the immutable manifest and referenced blob identities after the
exact installed Ollama behavior is observed.

`ModelArtifactManifest` in `src/apx_external_model_storage.py` now implements
this pure record. It requires one reviewed source vocabulary, Ollama tool
identity, a positive measured size, one exact manifest digest, a unique sorted
blob set, and explicit absence of partial downloads, credentials, and
conversations. Its canonical digest can be bound into `AttachmentEvidence`.
It reads supplied metadata only and cannot inspect or download a model.

## Disconnect and Failure Rules

Removing the cable while Development is active is a failure, not a normal
detach. APX must stop admitting writes, preserve uncertain state, and refuse to
claim a clean stop until process, mount, open-handle, filesystem, and service
evidence is complete. It must not silently redirect model writes into the
underlying empty mount directory on the internal disk.

Normal detach requires:

1. stop the coding agent and model server;
2. verify no open file or process uses the attachment;
3. stop Development and prove runtime teardown;
4. flush and detach the exact private bind and filesystem;
5. close the encrypted volume;
6. verify absence and record the final state.

On filesystem error, missing device, changed serial, failed unlock, incomplete
download, digest mismatch, or uncertain teardown, preserve data and block
activation. Repair and destructive cleanup require separate procedures and
approval.

The pure recovery assessment now distinguishes no recorded effect, partial
attach, attached-stopped, active, partial detach, verified detached, and an
effect whose outcome is unknown. Unknown or partial outcomes always block
Development activation and automatic cleanup. A test-only compare-and-swap
store rejects stale writers, replay, and multi-step jumps.

## Required Physical Evidence

Before implementation, the owner-run read-only audit must capture the external
SSD's stable identity and topology; health capabilities; internal Development
and host free space; installed Ollama service user, paths, environment, and
model-directory behavior in a safe fixture; current runtime namespace mapping;
the intended model's real size and memory requirements; and the recovery-media
ability to identify and unlock only the external device.

Do not include serials in public documentation without the owner's explicit
choice. A target-bound private dossier may retain them when needed for safety.

## Acceptance Gates

External model storage remains blocked until the repository contains and tests:

1. a closed attachment and evidence schema (now implemented as the pure
   `AttachmentEvidence` contract in `src/apx_external_model_storage.py`);
2. a pure validator that rejects identity, ownership, capacity, state, and
   model-manifest mismatches (now implemented without any effect adapter);
3. a no-effect attach/detach plan with exact paths and operation identity (the
   deterministic attach preview and pure ordered attach/detach lifecycle are
   now implemented; physical adapters remain pending);
4. a minimum-privilege runtime adapter design;
5. stopped-state, disconnect, partial-download, full-disk, corruption, and
   changed-device fixtures;
6. Hub and second-Environment denial tests;
7. a target-bound destructive formatting dossier and separate approval;
8. complete cleanup and recovery verification.

Only after those gates pass may the physical handoff replace the internal 7B
example with an explicitly admitted larger model and external-store procedure.

The implemented validator can classify evidence only as `blocked` or
`ready-for-separate-design-review`. It cannot format, unlock, mount, attach,
detach, download, admit, or remove anything, and even a ready result still
requires the remaining gates and a separate destructive dossier.

`build_attach_preview` now turns only complete ready evidence into a
deterministic `preview-only` record. It fixes the private host location under
`/run/apx/model-stores/<attachment-id>`, the candidate Development service path
`/var/lib/ollama`, the ordered effect names, and a generation-bound operation
identity. These are review inputs, not shell commands or execution authority.
Tomorrow's audit must confirm that `/var/lib/ollama` is the installed package's
real service-data path before this candidate path can be accepted.

The lifecycle module cannot call `cryptsetup`, `mount`, `umount`, `systemd`,
APX, Ollama, or a disk API. Its effect names describe what a future independently
reviewed adapter would have to prove. Completing the pure journal is therefore
not evidence that an SSD was attached or that the physical feature is ready.
