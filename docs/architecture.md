# APX Architecture

APX is a personal operating environment platform built on top of Arch Linux.

The operating system remains Linux. APX is an orchestration layer that manages isolated personal environments on a single Arch Linux installation.

## Current System

A read-only APX inspection and creation-planning prototype exists in this repository. No privileged creation or mutating APX runtime exists. Existing manually created users do not yet represent the intended APX storage model. Their homes remain ordinary directories under the existing `@home` subvolume rather than dedicated Btrfs home subvolumes.

Development currently takes place in the Development Environment named `apx-development`. SDDM currently manages graphical sessions. Codex is a temporary development tool and is not part of APX.

## Non-Goals

APX is not:

- a Linux distribution
- a replacement operating system
- a container runtime
- a virtual machine manager
- a second package manager
- a replacement desktop shell
- a development environment inside the Hub

These boundaries matter because APX should stay simple, predictable, and maintainable.

## Host System

An APX system has exactly one host Arch Linux installation.

The host owns:

- one kernel
- one package database
- one KDE Plasma installation
- global system services
- globally installed applications

APX does not duplicate these resources per Environment.

## Shared Applications, Isolated Data

Applications are shared globally through the Arch package database.

The intended Environment isolation applies to:

- user home data
- configuration
- session state
- user-owned processes
- APX metadata

This avoids duplicating applications while preserving independent personal workspaces.

## Environments

An Environment is the primary APX unit.

The intended Environment model maps each Environment to:

- one Linux user
- one dedicated Btrfs home subvolume
- one independent KDE session
- independent configuration
- user-owned processes separated by Linux user ownership
- independent metadata

The Linux user boundary provides ownership and process separation. The Btrfs subvolume provides storage structure, snapshot support, and lifecycle management. The KDE session provides an independent interactive workspace.

### Environment Identity Contract

The confirmed intended identity mapping is:

```text
Logical name: <slug>
Linux account: apx-<slug>
Home path: /home/apx-<slug>
```

The logical name is the APX-facing identifier supplied by a user. The Linux account and home path are derived internally and are never independent caller inputs.

A canonical logical name:

- contains 1 to 27 characters;
- contains only lowercase ASCII letters, ASCII digits, and hyphens;
- begins with a letter;
- ends with a letter or digit;
- contains no repeated hyphens;
- does not begin with `apx-`, because APX adds that prefix;
- is not `root`, `nobody`, or `system`.

In regular-expression form, the structural grammar is:

```text
[a-z](?:[a-z0-9]|-(?=[a-z0-9])){0,26}
```

Reserved names are rejected in addition to the structural grammar. A name is also unavailable when its derived account would conflict with an existing account or reserved system identity. Account and path conflicts are runtime preconditions rather than reasons to broaden the naming grammar.

The built-in identities use the same mapping:

```text
Logical name: hub
Linux account: apx-hub
Home path: /home/apx-hub
Role: hub
```

```text
Logical name: development
Linux account: apx-development
Home path: /home/apx-development
Role: development
```

All other valid logical names have the `standard` role. The Hub does not have a separate identity mechanism.

The identity states are:

- **Candidate Environment:** an observed Linux account or home-like resource matching APX naming conventions without sufficient valid registration. Naming resemblance alone does not establish APX ownership.
- **Registered APX Environment:** an Environment with valid APX-managed metadata that binds one canonical logical name to its derived account, home, role, lifecycle state, and verified storage identity. Registration is intended host architecture; no host registration store exists yet.
- **Consistent Environment:** a registered Environment whose account, home, storage, ownership, and metadata are all confirmed to match the contract.
- **Incomplete Environment:** a candidate or registered Environment for which one or more required resources are confirmed missing, conflicting, or inconsistent. An unregistered candidate is incomplete rather than implicitly registered.
- **Unavailable or unconfirmed state:** APX cannot confirm the identity or a required resource because observation is restricted, ambiguous, or unavailable. Lack of confirmation is not proof of consistency or inconsistency.
- **Archived Environment:** a future registered lifecycle state in which an Environment is not available as an active login Environment but retains APX-managed recovery information. Archival behavior and storage layout remain future intended architecture and are not implemented.

The current read-only prototype's candidate state named `consistent` covers only the account and home observations it implements. It does not establish the formal **Consistent Environment** state defined above.

The current `apx environment inspect` command inspects a discovered candidate by its exact Linux account name, for example `apx environment inspect apx-hub`. Creation instead accepts the logical Environment name, for example `apx environment create hub --dry-run`. The inspection command does not resolve logical-name aliases.

### Linux User

The Linux user is the primary identity boundary.

It defines:

- file ownership
- process ownership
- user-level permissions
- home directory ownership
- session identity

APX should avoid creating hidden alternate identity systems when Linux users already provide the required primitive.

### Btrfs Home Subvolume

The canonical active home path is `/home/apx-<logical-name>`. Each registered active Environment is intended to bind one Linux account to one dedicated Btrfs subvolume rooted at that path. `/home` may be a mount point or an ordinary directory inside another mount; APX does not require a separate `/home` mount.

The storage terms are distinct:

- **Path:** a pathname such as `/home/apx-work`.
- **Mount point:** the directory at which a filesystem or subvolume is attached. A home path need not be a mount point.
- **Filesystem:** the storage filesystem containing a path.
- **Btrfs filesystem:** a filesystem whose type is confirmed as Btrfs.
- **Btrfs subvolume:** a Btrfs object with its own stable subvolume identity and root. A directory on Btrfs is not necessarily a subvolume.
- **Subvolume ID:** the filesystem-local numeric identifier assigned after creation.
- **Subvolume UUID:** the persistent UUID assigned after creation and used as the primary registered storage identity.
- **Parent UUID:** the UUID describing Btrfs snapshot ancestry, or null for a newly created non-snapshot subvolume.
- **Top-level filesystem path:** the path to the subvolume as resolved within the Btrfs filesystem namespace; it is observational metadata, not the canonical Environment home identity.

A mount target or Btrfs filesystem type alone does not prove that a home is a dedicated subvolume. After creation APX must freshly confirm that the home exists, is a directory, is on Btrfs, is the root of a dedicated subvolume, has the registered subvolume ID and UUID, does not resolve to another Environment's registered subvolume identity, is writable in the intended host context, and has policy ownership and permissions.

Subvolume IDs and UUIDs are unknown before creation and must never be fabricated in a plan. Sandbox-visible mount data is non-authoritative until a future privileged host observer repeats it.

Snapshot, quota, compression, backup, archival-storage, and subvolume top-level layout policies remain intentionally deferred.

### KDE Session

Each Environment is intended to have its own independent KDE Plasma session.

KDE Plasma is shared at the system level, but user configuration, session state, and user-level services are separate per Environment.

### Processes

Processes belong to the Environment user that launched them.

APX should treat process ownership as part of the Environment boundary. Lifecycle operations that stop, archive, restore, or switch Environments must account for running processes.

Process isolation through Linux namespaces is not implemented and is not a confirmed architectural requirement.

### Metadata

The future canonical registration path is:

```text
/var/lib/apx/environments/<logical-name>.json
```

Registration schema version 1 is deterministic UTF-8 JSON with these required fields and no unknown fields:

| Field | Type | Known | Immutable | Consistency use |
|---|---|---|---|---|
| `schema_version` | integer, exactly 1 | before creation | yes | parser compatibility |
| `logical_name` | canonical string | before creation | yes | derives every identity |
| `role` | `hub`, `development`, or `standard` | before creation | yes | must match derivation |
| `account_name` | canonical derived string | before creation | yes | account binding |
| `home_path` | canonical derived absolute path | before creation | yes | home binding |
| `lifecycle_state` | `active` in schema v1 | publication | mutable only through a future versioned lifecycle operation | availability classification |
| `storage` | object | after storage creation and verification | identity fields immutable for the registered resource | storage binding |

The required `storage` object contains:

| Field | Type | Known | Immutable | Consistency use |
|---|---|---|---|---|
| `filesystem_type` | string, exactly `btrfs` | after observation | yes | filesystem check |
| `subvolume_id` | positive integer | after creation | stable for the subvolume on this filesystem | secondary identity check |
| `subvolume_uuid` | canonical UUID string | after creation | yes | primary storage identity |
| `parent_uuid` | canonical UUID string or null | after creation | yes | records observed Btrfs snapshot ancestry |

Registration v1 stores neither UID nor GID because numeric allocation is host-specific and can be resolved from the account. It contains no timestamps, secrets, diagnostics, cached output, commands, executable paths, hostnames, Codex fields, snapshot policy, or authentication data. Registration is not created before verified storage identity is available.

For `parent_uuid`, null means Btrfs reported no snapshot parent UUID when the storage identity was registered. That is the expected value for a newly created non-snapshot subvolume. It does not independently prove the resource's complete history, so provenance and fresh identity checks remain separate requirements.

Naming resemblance does not establish APX ownership. A candidate is an account or home-like resource matching APX naming conventions without sufficient valid registration. A registered Environment has a schema-valid canonical record, but registration alone does not prove current host consistency. A consistent Environment has fresh agreement across registration, account, home, Btrfs identity, ownership, permissions, and policy. An incomplete Environment has a valid registration or operation marker plus a confirmed missing or conflicting postcondition. Unavailable or ambiguous observation remains unconfirmed, not inconsistent. Archived remains future intended architecture and is rejected by registration schema v1.

The registration directory is future root-owned host state. This milestone implements only pure serialization and parsing; it does not read or write the real path.

### Linux Account and Permission Policy

Future creation requests accept only the logical name. APX derives the account, home, and role. The host allocates a normal UID and GID; APX verifies them afterward and does not store them in registration v1. Each account uses a private primary group with the same name. No supplementary groups are assigned by the creation contract. The Hub receives no broad group privilege, and development receives no administrative privilege.

The account must be a normal local login identity suitable for graphical login. The exact shell is an unresolved fixed host policy: a future reviewed policy selects it, and callers cannot supply a shell or executable path. Password enrollment and authentication are separate lifecycle/security concerns; creation accepts no password material.

If the account already exists, creation is not satisfied even when its name resembles APX. APX must not adopt, modify, or delete it. A derived account owned by an unrelated identity blocks creation and requires manual resolution.

The home owner is the Environment account, the group is its private primary group, and the initial mode is `0700`. Mode `0755` exposes names and readable content too broadly; `0750` could support a future reviewed shared-access group but adds no current benefit. APX therefore chooses isolation with `0700`. ACLs are not part of v1. Ownership, group, and mode are mandatory postconditions. Pre-existing content is never adopted, overwritten, recursively changed, or deleted by creation.

Future `/var/lib/apx/environments` is `root:root` mode `0755`; individual non-secret registrations are `root:root` mode `0644` so unprivileged inspection is possible without write authority. Future incomplete-operation state, if used, lives under a root-owned `0700` directory with `0600` records and is not registration.

### Formal Environment Creation Operation

Creation is a closed typed state transition, never an arbitrary script:

1. `validate_identity` (unprivileged and privileged, observational): validate the logical name and derive identity. Reversible because nothing changes; evidence is a canonical identity.
2. `load_registration_state` (both, observational): validate registration absence and reject malformed/conflicting records. Evidence is an authoritative registration lookup.
3. `observe_preconditions` (both, observational; privileged result authoritative): check account, home, candidate, parent paths, Btrfs context, compatibility, plan currency, and authorization.
4. `reserve_incomplete_operation` (future privileged, mutating): atomically record operation identity and provenance. It is removable while it remains owned by this operation.
5. `create_btrfs_subvolume` (future privileged, mutating): create the canonical home subvolume before account creation. Evidence is fresh Btrfs identity. This order prevents account tooling from creating an ordinary home directory.
6. `create_linux_account` (future privileged, mutating): create the derived account with host allocation, canonical home, fixed host shell policy, private primary group, no supplementary groups, and automatic home creation/skeleton population suppressed.
7. `set_home_ownership` (future privileged, mutating): set the subvolume root to the resolved account and private group.
8. `set_home_permissions` (future privileged, mutating): set exactly `0700`, with no initial ACL.
9. `stage_registration` (future privileged, mutating): construct root-only canonical registration using freshly verified Btrfs identity, without publishing it.
10. `verify_environment` (future privileged, observational): freshly verify all resource postconditions against the staged record.
11. `write_registration` (future privileged, mutating): atomically publish the verified root-owned registration.
12. `verify_environment` (future privileged, observational): repeat fresh full verification including published registration ownership and content.
13. `complete_operation` (future privileged, mutating): remove the incomplete marker only after verification.
14. `verify_consistent_environment` (future privileged, observational): freshly verify every postcondition, including marker absence, before reporting the Environment consistent.

Automatic home creation must be suppressed because otherwise account tooling could create a normal directory or populate it before the subvolume exists. No implementation command line is part of this contract.

### Creation Preconditions and Eligibility

Every precondition is one of `confirmed`, `not-satisfied`, `unavailable`, or `ambiguous`. Only confirmed counts as satisfied. Not-satisfied blocks architectural eligibility. Unavailable or ambiguous requires authoritative host confirmation and blocks apply.

| Precondition | Unprivileged observation | Future privileged recheck | Digest/staleness | Human review |
|---|---|---|---|---|
| logical name valid and identity canonical | yes | yes | yes | rendered |
| valid registration absent | where readable | required | yes | conflicts |
| malformed/conflicting registration absent | where readable | required | yes | conflicts |
| derived account absent | yes | required | yes | conflicts |
| derived home absent | yes | required | yes | conflicts |
| conflicting candidate absent | yes | required | yes | conflicts |
| registration target absent | where readable | required | yes | conflicts |
| parent paths valid and non-symlink | partial | required | yes | anomalies |
| target storage context confirmed Btrfs | partial | required | yes | yes |
| host observation authoritative | no in sandbox | required | yes | yes |
| helper supports plan/request versions | no helper yet | required | yes | yes |
| approved plan current | digest only | required through fresh observation | yes | yes |
| human authorization valid | no | required | approval binding | explicit |

### Creation Postconditions

Success requires a fresh observation confirming all of the following: registration parses as supported schema; account exists; account name and home match derivation; role matches registration; home exists and is a directory; filesystem is Btrfs; home is the root of the dedicated registered subvolume; subvolume ID, UUID, and parent UUID match registration; no other Environment registration binds the same subvolume UUID; home is writable in the intended host context; owner is the resolved account; group is the private primary group; mode is `0700`; registration is `root:root` mode `0644`; no incomplete marker remains; and the resulting classification is consistent.

A mutation sequence that exits successfully but fails or cannot complete these observations is not successful. Verification must not reuse planning observations.

### Partial Failure and Rollback

The invariant is: never delete or overwrite a resource unless APX proves that this operation created it and it has not become user-owned, used, or externally modified.

| State | Automatic response |
|---|---|
| nothing created | remove only an operation marker owned by this operation |
| subvolume only | remove it only with matching operation provenance, fresh identity, confirmed emptiness, and no external modification |
| account only | unexpected ordering; remove only if provenance matches and it has never logged in, run processes, owned data, or been modified |
| subvolume and account | reverse account then subvolume only under the same strict unused/provenance checks |
| ownership partially applied | preserve unless every created resource and current identity is proven; classify incomplete |
| registration staged | remove only the private staged file owned by the operation |
| registration published but verification failed | preserve all resources and registration; classify incomplete for recovery |

Broad recursive deletion is forbidden. A matching pathname is not provenance. Pre-existing resources, uncertain provenance, user-modified resources, and any home that may have been used are never automatic rollback candidates.

Atomic publication of final registration is the destructive rollback commit boundary. Before publication, narrowly proven unused operation-owned resources may be reversed. After publication—or earlier first use—automatic destructive rollback stops. Successful final verification and marker removal establish completion; failure after publication remains incomplete rather than being deleted.

### Host Confirmation and Plan Staleness

Unprivileged `apx` creates and renders a normalized plan. A human reviews and explicitly approves that exact operation. Future `apx-admin` independently validates the request, checks supported versions, re-observes authoritative host state, rejects stale or changed plans, performs only typed approved steps, and verifies the result.

Approval binds the operation type, plan schema, logical name, derived account and home, role, normalized relevant preconditions, ordered typed mutations, and helper compatibility. It never authorizes arbitrary commands, different identities or paths, a broader operation, or failed preconditions. The digest is content identity, not authentication or authorization. Authentication mechanism, approval lifetime, and privileged request protocol version remain unresolved; no reusable token format is defined.

Plan validity includes account, home, registration and candidate absence; parent and target path identity; Btrfs filesystem identity/capability; supported registration and plan versions; and future helper protocol compatibility. Transient diagnostics, timestamps, and random values are excluded. Content identity, host-state freshness, and authorization lifetime are separate. Digest equality cannot establish freshness: the privileged component must always re-observe, and any failed current precondition overrides a matching digest.

### Unprivileged and Privileged Boundary

Unprivileged `apx` may validate names, derive identity, read permitted registration, observe without mutation, classify unavailable state, build/render/digest plans, request human approval, later submit a typed request, and inspect results. It must not create accounts or subvolumes, change permissions, write root-owned registration, run arbitrary privileged commands, or treat a digest as authorization.

Future root-owned `apx-admin` may accept one small versioned typed request, validate independently, recheck authoritative preconditions, perform only the ordered bounded mutations, publish registration, verify postconditions, and return structured results. It must not expose a shell; accept arbitrary commands, executables, paths, account/home identities, UID, GID, shell, groups, or permissions; trust unprivileged observations; treat a digest as authorization; read unrelated home data; or contain Codex-specific behavior. No helper exists in the current system.

## The Hub

The Hub is an Environment dedicated to APX management.

The Hub is not a general desktop and must not become a development workspace. It exists to manage Environments and APX lifecycle operations.

The Hub is subject to the same architectural model as every other Environment. There are no special exceptions for the Hub beyond its purpose and permissions.

The Hub must be destroyable and recreatable like every other Environment. No implementation decision may require a unique lifecycle exception for the Hub.

The Hub is the default Environment in the intended APX session flow.

## Development Environment

The APX Development Environment is separate from the Hub.

Development tools such as Git, GitHub CLI, Codex, ChatGPT, browsers, IDEs, and build tooling belong in the Development Environment. They do not belong in the Hub.

Development activity includes source code, documentation drafts, repository management, experiments, build outputs, issue work, and pull request work.

## Lifecycle Operations

The future APX implementation is intended to manage:

- listing Environments
- creating Environments
- archiving Environments
- restoring Environments
- snapshotting Environments
- creating and applying templates
- launching Environment sessions

These operations should be designed around the Environment model rather than around ad hoc host mutations.

Initial lifecycle concepts include:

- active
- archived
- restorable
- template

These states are provisional and should be refined when lifecycle workflows are specified in detail.

## Architectural Decisions

### APX Uses Existing Linux Boundaries

APX should use ordinary Linux primitives before inventing APX-specific abstractions.

Initial boundaries are Linux users, Btrfs subvolumes, KDE sessions, process ownership, filesystem permissions, and metadata files or records.

### Applications Are Global

The system has one package database.

APX should not create per-Environment package databases unless a future architecture document proves that the added complexity is necessary.

### The Hub Is Clean

The Hub must remain focused on APX management. Development tools, build artifacts, source repositories, and implementation work belong in the Development Environment.

### One Graphical Environment at a Time

The intended session-management model runs only one graphical Environment at a time.

The target flow is:

```text
Boot -> Hub -> Environment -> Hub
```

This is documented in more detail in [session-management.md](session-management.md).

### Documentation Comes First

Implementation should follow documented architecture. When a design question is unresolved, the repository should capture the decision before code encodes it.

## Confirmed Intended Architecture

- APX is an orchestration layer on top of Arch Linux, not a replacement operating system.
- The host architecture is single Arch installation, single kernel, single package database, and single system-level KDE Plasma installation.
- Applications are globally installed.
- Environment data, configuration, session state, processes, and metadata are separated by Environment.
- Each Environment corresponds to one dedicated Linux user and one intended dedicated Btrfs home subvolume.
- Each Environment has its own KDE session, with only one graphical Environment active at a time.
- The Hub is an Environment dedicated to APX management.
- The Hub is the default Environment in the intended session model.
- The intended lifecycle is `Boot -> Hub -> Environment -> Hub`.
- The Hub must not become a development workspace.
- No implementation decision may require a unique lifecycle exception for the Hub.
- Linux user boundaries are sufficient as the primary identity and ownership boundary.

## Ideas Under Evaluation

- `greetd` is the preferred candidate under evaluation for replacing SDDM in the future session handoff model.

## Open Questions

- What permissions should the Hub have to manage other Environments without creating a unique lifecycle exception?
- How should APX safely stop or hand off user processes during Environment switching?
- What exact display-manager/session-manager integration should APX use?
- What fixed login shell policy should future account creation use?
- What authentication mechanism and lifetime should bind human approval to a future privileged request?
- What snapshot, quota, compression, backup, and archival-storage policies should APX adopt?
