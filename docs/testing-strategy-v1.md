# APX Testing Strategy v1

Status: staged test proposal; only repository-level tests are currently
authorized and running.

## Plain-Language Summary

APX will become testable gradually. We will not move directly from documents to
changing the real computer.

Each level answers a different question:

1. Do the rules reject unsafe requests?
2. Can disposable fake data exercise failures safely?
3. Can one empty experimental Environment run without touching personal data?
4. Can two Environments prove separation from each other?
5. Can graphical use, applications, hardware, and switching work safely?
6. Can APX recover after crashes and deliberate attacks?

Passing one level does not automatically authorize the next.

## Level 1: Repository Contracts

Status: active today.

These tests run only against code and fake evidence inside the repository. They
do not create users, storage, containers, sessions, services, or packages.

Current coverage includes:

- names, registrations, creation and removal plans;
- read-only host and session observations;
- snapshot evidence and Stage 2 review plans;
- fixed normal and high-security isolation-policy contracts;
- fixed Hub operation plans and approval binding;
- rejection of commands, paths, unknown fields, stale generations, expired
  confirmations, reused nonces, wrong sessions, and changed plans.

Exit requirement: all tests pass deterministically and every new privileged
effect first has a pure contract and negative tests.

## Level 2: Disposable Filesystem Fixtures

Status: not started.

Tests use repository-owned temporary fixtures or an explicitly approved
disposable test area. They model files, journals, manifests, interrupted writes,
and corrupt records without representing them as real host resources.

Required scenarios include:

- crash before and after every journal step;
- duplicate, missing, oversized, and corrupted metadata;
- path replacement and symbolic-link attacks;
- fake storage identity reuse;
- quota and capacity evidence becoming unavailable;
- approval replay and clock rollback;
- recovery preserving uncertain data.

Exit requirement: no test can delete or adopt a fixture without exact recorded
identity and ownership evidence.

## Level 3: One Headless Experimental Environment

Status: designed but not authorized.

This is the first level that changes host state. It requires a separate preview
and explicit approval. The fixed `isolation-trial` identity is used, with no
desktop, GPU, audio, camera, microphone, input devices, personal data, Hub,
Odysseus, or Codex.

The test proves:

- isolated root and home creation;
- independent package database;
- local `sudo pacman` cannot change host packages;
- private processes, mounts, users, IPC, and network;
- enforced CPU, memory, process, and storage limits;
- complete stop and cleanup evidence;
- safe refusal when any identity is uncertain.

Before starting, APX must show exact downloads, storage, accounts, processes,
network effects, rollback limits, and cleanup plan.

Exit requirement: repeated create, boot, local package change, stop, restart,
and separately approved cleanup complete without host or unrelated changes.

## Level 4: Two-Environment Separation

Status: not designed in executable form.

Two disposable Environments install the same harmless package independently.
Tests then attempt, from normal user and local root, to access the other
Environment and the host.

Required denials include:

- files and package databases;
- processes, IPC, sockets, D-Bus, and services;
- mounts, snapshots, metadata, and operation records;
- network identity and undeclared host services;
- devices, secrets, clipboard, and portals;
- CPU, memory, process, and storage-limit removal;
- surviving processes after stop.

Deleting one Environment must leave the other byte-for-byte and semantically
unchanged where the measurement is meaningful.

Exit requirement: every attempted crossing is denied or the architecture is
stopped and revised. “Mostly isolated” is not accepted.

## Level 5: Graphical and Daily-Use Tests

Status: future.

Only after headless separation works do we add, one at a time:

- minimal Wayland display;
- mediated input;
- audio;
- notifications and file portal;
- clipboard and secret storage;
- removable storage;
- AMD graphics;
- NVIDIA graphics;
- Hyprland, KDE Plasma, and GNOME;
- Hub-to-Environment and return flow.

Each addition repeats separation and teardown tests. If a feature needs broad
host access, it remains disabled until a narrower design exists.

Exit requirement: the owner can use and switch Environments without seeing
internal Linux accounts, leaking data, leaving background runtimes, or losing a
recovery route to the Hub.

## Level 6: Attack and Recovery Campaign

Status: future.

Disposable Environments deliberately run malicious fixtures as normal user and
local root. Failures are injected during creation, activation, package
installation, stop, snapshot, archive, restore, and destroy.

The campaign tests:

- hostile package hooks and install scripts;
- resource exhaustion;
- namespace, capability, device, and socket escape attempts;
- stale approvals and journal tampering;
- forced power loss and executor restart;
- broken graphics and incomplete teardown;
- uncertain cleanup and protected-neighbour verification.

High-security shared-kernel tests cannot prove immunity to every future kernel
bug. Workloads requiring that promise need a separately tested virtual-machine
profile.

## User Test Experience

When Level 3 is ready, the user should receive one plain-language test preview:

- what will be created;
- how much storage and memory may be used;
- whether anything will be downloaded;
- which network and process activity will occur;
- confirmation that no personal Environment or Hub data is used;
- how the test stops;
- what cleanup would delete;
- which evidence will prove success or failure.

The user can approve the experiment without also approving cleanup, graphical
access, GPU access, or later levels. Each requires its own decision.

## Stop Conditions

Testing stops immediately when:

- host, Hub, base, or unrelated Environment state changes unexpectedly;
- an unavailable observation is needed to claim safety;
- identity or ownership becomes uncertain;
- quota or capacity enforcement is inconsistent;
- a process, mount, network object, device client, or session survives stop;
- a request accepts an unknown command, path, device, or policy;
- rollback would require guessing or deleting modified data;
- the observed isolation is weaker than the user-facing claim.

Stopping a test is a successful safety response, not permission to bypass the
failed check.

## Evidence and Handoff

Every level produces a concise report explaining:

- what was tested;
- what passed;
- what failed or could not be confirmed;
- what changed;
- what remained untouched;
- what data or resources remain;
- whether cleanup is safe and separately approved;
- whether the next level is eligible for review.

Technical logs remain bounded and separate. They do not contain unrelated
personal data or secrets.

## Current Readiness

Level 1 is established and growing. Level 2 has started with a repository-only
executor journal fixture. It tests ordered journal transitions, interrupted and
uncertain effects, corruption, stale writers, atomic replacement, restrictive
file modes, and symbolic-link refusal in disposable temporary directories. It
also tests canonical trust-evidence sealing, tamper detection, observer-class
boundaries, raw-diagnostic minimization, and strict parsing. It does not perform
lifecycle effects or use an authoritative host path. Pure capacity fixtures
also exercise dynamic growth, independent Environment/pool/physical ceilings,
host and metadata reserves, unhealthy quota states, and malformed evidence.
The pure installation fixture verifies that backup and recovery precede host
testing, KDE remains available through parallel graphical validation, cutover
does not imply cleanup, and complete evidence yields only cleanup review.
The Stage 2 final-gate fixture independently fails every boolean gate, rejects
cross-plan and malformed digests, and proves that complete evidence still
requires a separate execution approval.
The acquisition boundary fixture rejects alternate origins, insecure schemes,
redirects, URL credentials and suffixes, traversal, unsafe or duplicate names,
unreviewed repositories and architectures, ordering changes, byte-limit
violations, incomplete files, symbolic links, and transfer identity mismatch.
The disposable acquisition-staging fixture tests exclusive reservation,
plan-binding changes, restrictive modes, no-overwrite publication, bounded
streaming, exact hashes and sizes, preserved partial failures, symbolic-link
and non-regular-entry refusal, and unsafe parent or filename rejection.
The bounded downloader fixture simulates exact responses, redirects, status
failures, missing or contradictory lengths, early and excessive bodies,
digest disagreement, non-byte data, network/read/staging failures, and timeout
policy without making a network connection.
The direct HTTPS opener fixture verifies proxy suppression, redirect refusal,
TLS minimum and certificate/hostname requirements, fixed non-secret request
headers, strict archive authority, timeout bounds, response-URI identity, and
sanitized HTTP/network failures.
The transfer/staging integration fixture streams unknown database bytes in
small chunks, proves no final publication before matching evidence, preserves
partial bytes on simulated network failure, and refuses retry over an existing
partial operation.
One separately authorized real network fixture acquired only the dated Arch
`core.db` and `extra.db`, stayed within its per-file and aggregate bounds,
published exactly two regular files, and reproduced both hashes on independent
reopen. Package acquisition, extraction, and installation were not exercised.
Repository-database parser fixtures cover file digest and symlink refusal,
archive traversal and unexpected members, expansion bounds, duplicate package
and field identities, malformed text/numbers/hashes/signatures/architectures,
and canonical package metadata without extracting archive contents.
Closed-resolution fixtures reject missing seeds, duplicate or unknown packages,
malformed rows, version/architecture/filename/size/URL disagreement, missing
or duplicate database evidence, output/count/aggregate bounds, and bad plan
identity. The real offline resolver produced identical independent passes.
The fixed package acquisition reparses the authorized manifest before any
effect, produces exactly package/signature pairs, refuses existing or non-`/tmp`
roots, and blocks tampered evidence before network use. The real run stayed
bounded and its independent reopen verified 276 expected regular files.
Offline signature-verification fixtures reject cryptographic failure, missing
valid results, insufficient current master certification, and disagreement
between GnuPG and `gpgv`. The real run verified all 138 package/signature pairs
twice and both paths agreed on 15 trusted primary signing identities.
Package-metadata fixtures reject missing or duplicate identities, malformed or
oversized values, invalid sizes, and inside/outside identity disagreement. The
real bounded metadata-only run matched all 138 package archives without full
extraction, execution, installation, or network access.
Complete-cleanup fixtures cover both user scopes, strong approval, exact
resource sets and digests, identity disagreement, runtime/open-handle/mount/
network and neighbor gates, `DELETED`, `<under deletion>`, `<stale>`, account
and registration residue, factual reclaim, pending identity reuse, and the
Hub's persistent read-only progress card.
Level 3
already has architecture and review documents, but its real
base, executor, authentication, quota topology, and host-changing approval are
not ready.

One separately authorized real-host quota leaf fixture and its complete cleanup
have passed. The path disappeared first while subvolume `263` and qgroup
`0/263` remained pending; only their later verified absence and healthy quota
state completed the test. This is evidence for one leaf, not permission to
treat hierarchical APX quota topology or Stage 3 Environment creation as ready.

The project must not describe future user testing as available until the exact
experiment preview, rollback boundary, and independently verified cleanup are
implemented and reviewed.

The Hub browser prototype is also a Level 1 fixture: Brave executes its
left-click, right-click, contextual-action, and management-view smoke tests
against in-memory data. This visual proof does not advance host readiness or
authorize Level 3.
