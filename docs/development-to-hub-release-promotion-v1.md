# APX Development-to-Hub Release Promotion v1

Status: logical architecture proposal. No builder, import channel, release
admission, Hub replacement, command, socket, signature authority, or host
mutation described here is implemented or authorized.

## Plain-Language Decision

Codex may help build APX inside the Development Environment without receiving
access to the live Hub or the host. Development produces an untrusted release
candidate. A host-owned APX admission path copies, verifies, and admits that
candidate by exact identity. Only the host-owned executor may then create a new
Hub from the admitted release.

```text
Development + Codex
  -> untrusted release candidate
  -> closed import boundary
  -> host-owned quarantine and verification
  -> separately approved catalogue admission
  -> create replacement Hub
  -> verify replacement
  -> switch or retain previous Hub
```

“Built by Codex” never means “trusted by APX.” Codex writes or reviews source;
it has no executor credential, Hub filesystem access, catalogue write access,
approval authority, or direct installation path.

## Isolation Invariant

Development never mounts, edits, snapshots, clones, enters, or package-manages
the live Hub. The Hub never mounts Development source or build output. There is
no shared writable release directory.

The only permitted crossing is one immutable candidate envelope copied through
a closed import operation. After copying, later changes in Development cannot
change the imported bytes or their identity.

Compromise of Development, its local root, Codex, an editor, compiler, build
script, dependency, or source checkout is assumed possible. It may create a
malicious candidate, but it must not directly create a trusted release or alter
an existing Environment.

## Trusted Roles

| Role | May do | Must not do |
|---|---|---|
| Codex in Development | edit source, tests, definitions, and documentation | approve, admit, install, or control Hub/host |
| Development builder | produce candidate bytes and build evidence | publish directly to trusted catalogue |
| import boundary | copy one bounded candidate into new quarantine | execute it or accept caller-selected host paths |
| verifier | parse and inspect candidate against fixed policy | repair it, widen policy, or treat build claims as facts |
| approval authority | bind the human to one exact admission/replacement plan | change candidate or plan |
| catalogue admission authority | publish one verified immutable release identity | admit partial, mutable, or unknown content |
| executor | create, verify, switch, retain, and later retire Hub generations | accept shell commands or arbitrary package requests |
| recovery controller | keep status, rollback, and text recovery available | become a general host shell or workload Environment |

These are trust responsibilities, not necessarily separate programs. An
implementation may combine processes only if it preserves the authority and
validation boundaries.

## Candidate Envelope

A candidate is a bounded regular file or equally immutable transport object. It
contains only a canonical envelope with:

- schema and APX protocol versions;
- candidate ID and Development build-operation ID;
- source revision and declared source-tree digest;
- exact base and Hub role-definition identities;
- exact package/source manifest and provenance references;
- normalized root/artifact content identity;
- builder, test, reproducibility, and sanitization evidence references;
- compatibility requirements for executor, backend, policy, and host;
- declared safe Hub preference schema, if any;
- total byte count, member count, and complete envelope digest;
- optional development signature used only as provenance evidence.

The first exact metadata subset is now closed and implemented as a pure parser
in `release-candidate-schema-v1.md` and `src/apx_release_candidate.py`.
Signatures remain separate verifier evidence in that schema. Parsing reports
only `parsed-untrusted`; it does not implement the physical envelope, import,
verification, or admission described by this document.

A valid hash or Development signature proves byte identity or claimed origin;
it does not grant trust or admission. Credentials, Codex conversations, model
keys, Git credentials, private signing keys, source working tree, build caches,
host paths, device requests, commands, hooks, or arbitrary first-start scripts
are forbidden.

## Closed Import Boundary

The future CLI may expose a conceptual operation such as:

```text
apx release import-plan <candidate-reference>
```

This spelling is illustrative, not an implemented command. The request selects
only a candidate reference already exported through an accepted bounded
transport. It cannot provide a host destination, unpack command, executable,
package-manager arguments, ownership, mode, device, mount option, or script.

The import path must:

1. open the source without following symbolic links or path replacements;
2. bind source identity, size, type, and complete digest before acceptance;
3. reserve a new executor-owned quarantine identity;
4. stream at most the declared and policy-bounded number of bytes;
5. refuse overwrites, sparse-size tricks, special files, extra members, and
   identity changes during copying;
6. publish the quarantine object only after the full copied digest matches;
7. execute none of the imported bytes;
8. preserve a failed or uncertain import as operation-owned incomplete state;
9. expose only sanitized status to Development and Hub.

The physical transport remains undecided. Candidates include a narrowly scoped
file-descriptor transfer, a content-addressed local import endpoint, or fetching
an exact digest from a separately authenticated release repository. A shared
writable host directory is not acceptable.

## Independent Verification and Admission

Import completion permits inspection, not execution or catalogue use. The
host-owned verifier independently checks:

- canonical schema, bounds, digests, and compatibility;
- exact admitted base, role definition, packages, sources, and signatures;
- normalized file tree, ownership, modes, capabilities, accounts, services,
  listeners, and first-start declarations;
- absence of credentials, personal data, assistant state, machine identity,
  runtime state, Hub authority, journals, registrations, and build paths;
- reproducibility against a second clean build or another accepted independent
  verification method;
- negative fixtures for malicious archives, hooks, services, privileges, and
  policy widening;
- compatibility with the installed executor without allowing the candidate to
  update that executor.

Admission is a separate explicit-confirmation operation bound to the candidate
digest, evidence digest, role, policy, compatibility result, storage effect,
and consequence text. The catalogue publishes a new immutable release identity
atomically. Failed, partial, outdated, or unknown verification cannot appear as
an available Hub release.

An admitted Hub release still has no host authority. Authority is supplied at
runtime through the independently protected APX protocol.

## First Hub Bootstrap

Before any Environment exists, the physical bootstrap console performs the
same logical stages using a pinned bootstrap candidate in a temporary bounded
staging area:

1. verify recovery, source/release identity, and bootstrap prerequisites;
2. install only the minimal host-owned APX trust and execution boundary;
3. import, verify, and admit the first headless Hub release;
4. create and independently verify the first Hub;
5. use the Hub CLI to create the first Development Environment;
6. move normal source/build/Codex work into Development;
7. remove or archive the temporary bootstrap staging only after independent
   verification and recovery checks.

This is the only pre-Environment exception. It does not make the bootstrap
checkout a permanent host development environment.

## Hub Replacement, Not Live Editing

A new Hub interface or bug fix is delivered by reconstruction, not by editing
the running Hub or running `pacman` against it from Development.

The future logical flow is:

1. select an admitted Hub release and render a replacement plan;
2. verify an independent text recovery/controller path;
3. create a new stopped Hub generation with fresh root, home, machine, runtime,
   and registration identities;
4. import only declared safe preferences through a typed schema;
5. boot and test the replacement without granting it broader authority;
6. stop the old Hub or enter the host-owned transition surface;
7. atomically select the verified replacement generation;
8. prove CLI status, executor communication, recovery, and Environment listing;
9. retain the previous Hub generation as a bounded rollback candidate;
10. retire or destroy it only through a later separately approved operation.

The active Hub cannot authorize its own irreversible removal as the only
recovery surface. Unknown mutable Hub state, shell history, caches, credentials,
runtime tokens, approval objects, or journals never migrate automatically.

If replacement verification or switching fails, APX returns to the recovery
controller or previous verified Hub. It does not “fix forward” by granting
Development access to either Hub.

## Safe Preference Migration

The first accepted preference schema should be empty. Later versions may admit
small typed presentation values such as language, time format, theme choice, or
card ordering. Each field has a version, type, bound, default, and migration
rule.

The preference channel never carries executable content, package selections,
paths, environment variables, shell configuration, browser state, credentials,
approval state, executor endpoints, or arbitrary extension data. Unsupported
fields are rejected or left with the old Hub for inspection; they are not
silently copied.

## CLI and Graphical Controls

The CLI is the first client for the entire promotion flow. A future graphical
button maps to the same typed plans and operations:

- inspect candidate and build evidence;
- plan bounded import;
- show verification result;
- plan catalogue admission;
- plan replacement Hub creation;
- test and select replacement;
- show rollback candidate and retention state.

Buttons never call Codex, Git, a compiler, package manager, shell, or executor
command directly. Codex helps implement those buttons in Development; the
installed buttons remain ordinary clients after Codex is removed.

## Approval Separation

Building needs no host approval because it is confined to Development.
Crossing later boundaries requires distinct decisions:

| Boundary | Minimum decision |
|---|---|
| candidate import into quarantine | explicit preview and confirmation |
| release admission to trusted catalogue | separate explicit confirmation |
| creation/test of replacement Hub | separate explicit confirmation |
| selecting replacement as current Hub | unlocked session plus verified recovery path; exact final class remains open |
| destruction of previous Hub | fresh strong confirmation |

Approval for one boundary never implies approval for the next. A candidate
digest or release name cannot be substituted after approval.

## Failure and Attack Tests

Before implementation can be trusted, fixtures must prove refusal for:

- malicious Codex/build output and compromised Development local root;
- changed source during import, symbolic links, special files, oversized or
  sparse content, duplicate members, traversal, decompression bombs, and digest
  mismatch;
- forged Development signature or valid signature over disallowed content;
- credentials, model keys, assistant conversations, Hub tokens, journals, and
  registrations embedded in the candidate;
- package hooks, set-user-ID files, capabilities, unexpected services,
  listeners, accounts, devices, mounts, and first-start commands;
- candidate attempts to replace executor, verifier, policy, trust roots,
  recovery controller, or host packages;
- stale admission approval, changed policy, replayed nonce, and incompatible
  executor generation;
- crash before and after every import, admission, creation, verification,
  selection, rollback, and retirement journal step;
- failed new Hub, failed old-Hub stop, failed selection, reboot during switch,
  and unavailable previous generation;
- Development attempting to read Hub data or mutate quarantine/catalogue after
  publication.

The key acceptance result is that hostile Development can at worst propose bad
bytes that are rejected or retained in bounded quarantine. It cannot directly
change the host, Hub, catalogue, another Environment, or executor authority.

## Acceptance Gates

1. Freeze canonical candidate, evidence, quarantine, catalogue, and admission
   schemas.
2. Implement the selected canonical member manifest and then select the bounded
   physical import transport and raw archive reader.
3. Define the initial Hub package manifest and empty preference schema.
4. Implement pure parsers, plan digests, state machines, and hostile fixtures.
5. Select independent build/reproducibility and signing/trust mechanisms.
6. Map import, verification, catalogue, and Hub-replacement effects to minimum
   executor privileges.
7. Prove a fake Development cannot reach the fake Hub or trusted catalogue and
   can only submit a bounded candidate.
8. Prove replacement, rollback, reboot, and interruption first with disposable
   filesystem fixtures.
9. Rehearse first-Hub bootstrap and Development creation on an explicitly
   approved disposable installation.
10. Only then prepare a target-bound fresh-install dossier.

## Decisions Still Open

- exact package container/compression production settings;
- raw archive streaming/parser implementation;
- import transport and exact caller authentication;
- source/release signing and local admission trust roots;
- independent builder and reproducibility method;
- initial Hub package manifest;
- safe preference schema;
- executor operation names and approval class for final Hub selection;
- rollback retention count, duration, and storage policy;
- how the recovery controller selects a last-known-good Hub after reboot.

This proposal closes the logical isolation path from Codex-assisted Development
to a recreated Hub. It does not close those physical implementation decisions.

The internal canonical member schema, bounds, sanitization rules, candidate
binding, and exact-rebuild comparison are now closed in
`release-artifact-manifest-v1.md` and `src/apx_release_artifact.py`. This closes
metadata policy only: no archive bytes are opened, extracted, trusted, or
published by that pure validator.

The ordered promotion record and in-memory compare-and-swap fixture are now
implemented in `src/apx_release_promotion.py`. Repository tests prove exact
import/verification/admission separation, fresh admission approval, immutable
catalogue identity, stale-writer refusal, no overwrite, forged initial-plan
refusal, multi-step-jump refusal, and preserve-on-uncertainty recovery. This is
logical fixture evidence only; no byte import, archive verifier, signature
authority, host catalogue, or Hub replacement exists.
