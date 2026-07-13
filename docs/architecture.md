# APX Architecture

APX is a personal operating environment platform built on top of Arch Linux.

The operating system remains Linux. APX is an orchestration layer that manages isolated personal environments on a single Arch Linux installation.

## Current System

A read-only APX inspection and creation-planning prototype exists in this repository. No privileged creation or mutating APX runtime exists. Existing manually created users do not yet represent the intended APX storage model. Their homes remain ordinary directories under the existing `@home` subvolume rather than dedicated Btrfs home subvolumes.

Development currently takes place in the Development Environment named `apx-development`. SDDM currently manages graphical sessions. A 2026-07-13 read-only observation found active Development KDE on `tty4` and an inactive but live Hub KDE session on `tty1` through SDDM autologin; this is current state, not intended one-session APX behavior. Codex is a temporary development tool and is not part of APX.

## Non-Goals

APX is not:

- a Linux distribution
- a replacement operating system
- necessarily a virtual-machine manager with one kernel per Environment
- a second package manager
- a replacement desktop shell
- a development environment inside the Hub

These boundaries matter because APX should stay simple, predictable, and maintainable.

## Host System

An APX system has exactly one host Arch Linux installation.

The host owns:

- one kernel
- the boot and hardware integration needed to start Environments
- global system services

The boundary between minimal host software and Environment-local software is
under evaluation. One host kernel is confirmed; one globally shared application
and package set is not.

For the preferred clean-install path, the host begins without a graphical
desktop or display manager. It acquires a pinned APX source/release, installs a
reviewed versioned artifact through a future typed bootstrap, creates a headless
Hub, then creates a separate Development Environment. A mutable Git checkout is
not a privileged installation interface.

## Environment-Local Applications and Data

Applications and their dependencies are intended to be local to an Environment.
Installing an application in one Environment must not expose it in another, and
deleting the Environment must remove its application state without affecting
the others.

The intended Environment isolation applies to:

- applications and dependencies
- user home data
- configuration
- session state
- user-owned processes
- APX metadata

The implementation mechanism is not selected. Container/root filesystem,
image, package overlay, namespace, and similar approaches must be compared
against desktop, GPU, update, template, deletion, and security requirements.

### Host, Base, Role, and Environment Layers

The intended design distinguishes four concerns:

- **Host:** kernel, hardware drivers, firmware, physical device management,
  machine-wide networking capability, and the minimum APX runtime.
- **APX base:** a reviewed, versioned, reproducible baseline that may provide
  common runtime integration, fonts, certificates, and safe defaults.
- **Role template:** Hub, development, gaming, university, or another declared
  software and policy profile layered on the base.
- **Environment state:** local applications, data, configuration, secrets, and
  runtime state belonging to one Environment.

These are intended responsibilities, not an implemented storage layout. Wi-Fi
credentials and secrets require particular care: the host may provide network
connectivity without copying credentials into every Environment. The precise
boundary must be threat-modeled and validated.

The live Hub is not a base image. Both Hub and workload Environments derive from
the APX base plus different role templates. Hub management authority, metadata,
credentials, widgets, and mutable state must not be inherited by workloads.

### Environment Package Management

Each Environment has its own writable software databases and root filesystem
state. Package managers and installers issued inside it resolve against that
local state. This includes `pacman`, `yay`, `apt`, Flatpak, language package
managers, vendor installers, and installation scripts. Therefore
`sudo pacman -S steam` inside `APX-Jogos1` installs Steam only there; the same
command in `APX-Jogos2` creates a separate installation.

Environment-local administrative privilege is not host administrative
privilege. The Environment must not expose the host package database, host root
filesystem, host package-manager lock, host signing configuration with private
material, or a socket/helper that accepts arbitrary host package requests. APX
host and base updates use a separate, explicitly authorized maintenance path.

The complete proposed local-administrator, package-manager, service, device,
update, recovery, and denial-test contract is maintained in
`environment-local-administration-v1.md`.

Templates may declare initial packages, but later local package operations
remain owned by the Environment. Deleting the Environment deletes those package
changes subject to the normal explicit data-loss and provenance checks.

## Environments

An Environment is the primary APX unit.

The intended Environment model maps each Environment to:

- one Linux user
- one dedicated Btrfs home subvolume
- one independent graphical login session
- independent applications and dependencies
- independent configuration
- user-owned processes separated by Linux user ownership
- independent metadata

The Linux user boundary provides internal identity and ownership separation. It
is not, by itself, a VM-equivalent containment boundary. The Btrfs subvolume
provides part of the storage structure, while the application/runtime storage
model remains to be designed. The login session provides an independent
interactive workspace.

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

Candidate inspection also performs a bounded read-only lookup of the corresponding registration and, when it is valid, freshly compares it with host-visible account, home, filesystem, Btrfs, registration-file, UUID-uniqueness, and incomplete-operation observations. It reports the registration observation separately from the prototype's legacy candidate state and renders every formal postcondition state before the combined classification. It does not infer formal consistency from the narrower legacy candidate checks or from unavailable sandbox evidence.

### Experimental Host Readiness

The current `apx host check` command is a read-only, experiment-specific inspection for the proposed standard Environment `trial` (`apx-trial`, `/home/apx-trial`). It checks the existing Hub and Development identities, target absence, APX metadata absence, `/home` storage context, Hyprland availability, display-manager configuration, graphical session definitions, current sessions, and account-policy prerequisites. It does not provide a general host-management framework and does not execute the rendered manual plan.

Every readiness check is classified independently as `ready`, `blocked`, `requires-host-confirmation`, `unavailable`, or `not-applicable`. Confirmed conflicts make overall readiness `blocked`. Unavailable authoritative evidence or positive observations made only through a restricted execution context make overall readiness `requires-host-confirmation`. Only complete authoritative matching evidence produces `ready-for-manual-experiment`. Manual creation remains a separately approved future action; the lack of an APX apply mode is not itself a readiness failure.

Visible conflicts fail closed even when positive evidence from the same
observer still requires authoritative host confirmation. This may delay an
experiment after a false-positive collision, but it prevents APX from treating
an existing account, home, registration, or tool conflict as permission to
continue. `apx host doctor` applies this principle to the newer fixed headless
isolation experiment and renders a short consequence-led result.

`/home` may be a distinct mount or a directory within another mount. Readiness depends on the containing filesystem being an authoritatively confirmed writable Btrfs context and on `/home` being a safe non-symlink directory, not on `/home` having a dedicated mount.

### Linux User

The Linux user is the current internal identity and ownership boundary.

It defines:

- file ownership
- process ownership
- user-level permissions
- home directory ownership
- session identity

The person sees one APX identity and named Environments, not these internal
accounts or a normal display-manager user chooser. A future multi-person model
may group Environments beneath separate human identities. Authentication and
group ownership are not yet designed.

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

A mount target or Btrfs filesystem type alone does not prove that a home is a dedicated subvolume. After creation APX must freshly confirm that the home exists, is a directory, is on Btrfs, is the root of a dedicated subvolume, has the registered subvolume ID and UUID, does not resolve to another Environment's registered subvolume identity, and has policy ownership and permissions. Current-context writability is supporting evidence rather than an independent consistency postcondition.

Subvolume IDs and UUIDs are unknown before creation and must never be fabricated in a plan. Sandbox-visible mount data is non-authoritative until a future privileged host observer repeats it.

Snapshot, quota, compression, backup, archival-storage, and subvolume top-level layout policies remain intentionally deferred.

### Graphical Session

Each Environment is intended to have its own independent graphical login
session. Hyprland, KDE Plasma, GNOME, and other viable choices should be
supported without defining APX lifecycle semantics.

User configuration, session state, and user-level services are separate per Environment. APX must not rely on KDE autostart, Plasma-specific behavior, or KDE APIs for lifecycle management.

Normal Environment user services start with the Environment's systemd user manager and stop when its final login session ends. `Linger=no` is the default. Persistent background execution requires a future explicit Hub-level exception; it is not a normal Environment property.

### Processes

Processes belong to the Environment user that launched them.

APX should treat process ownership as part of the Environment boundary. Lifecycle operations that stop, archive, restore, or switch Environments must account for running processes.

Process isolation through Linux namespaces is not implemented. Stronger
containment is now a product requirement, especially for an optional high-
security profile, but the threat model and mechanism are not yet selected.

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

The registration directory is future root-owned host state. Registration serialization and parsing remain pure. The current observer may read the real path when the execution context permits, but it never writes there.

The read-only prototype may inspect that future path but never creates it or writes registration data. A caller-injected directory is supported only as an internal/test boundary; CLI users cannot supply arbitrary registration paths. A validated logical name maps to exactly `<logical-name>.json`, with no recursive search.

Registration observation states are `absent`, `valid`, `malformed`, `unsupported`, `conflicting`, and `unavailable`. A missing configured directory or canonical file means only that no registration exists in the canonical configured location; it does not classify the full host Environment as absent. Invalid UTF-8, invalid or duplicate-key JSON, schema-shape errors, and files larger than 64 KiB are malformed. Exactly 64 KiB is accepted for strict parsing. A non-v1 schema is unsupported. A schema-valid record that does not bind the logical identity implied by its canonical filename is conflicting. Permission failures, non-regular paths, unsupported safe-open primitives, and restricted-context failures are unavailable. Diagnostics are fixed summaries and never include file content or raw exceptions.

The configured registration directory itself and the canonical registration file must not be symbolic links. Both are opened read-only with no-follow semantics, and the file is opened relative to the already opened directory. The Arch Linux implementation requires `O_NOFOLLOW`, `O_DIRECTORY`, and `O_CLOEXEC`; if those primitives are unavailable, observation is explicitly unavailable rather than falling back to unsafe opening. A symbolic link is reported unavailable even if it would resolve within the same filesystem or directory. Parent components of the configured directory are part of the trusted configuration boundary; no CLI input can change them.

`registered` means the registration is valid and every host observation made so far is available and matching, but at least one required postcondition has not yet been attempted. `unconfirmed` means at least one required observation was attempted or required but is unavailable or ambiguous. `consistent` requires every required postcondition to be freshly confirmed. The current CLI attempts the full read-only verification, but sandbox restrictions, missing metadata, or incomplete Btrfs output keep the result `unconfirmed`; a confirmed mismatch produces `incomplete`.

Read-only verification records numeric home and registration UID/GID, resolves owner and group names when the local databases permit, records exact permission bits, and observes writability only in the current execution context. Current-context writability is rendered evidence but is not by itself a formal consistency decision because it depends on the inspecting identity. Home and registration symlinks are never followed.

Numeric ownership in an account's configured `/etc/subuid` or `/etc/subgid` range is not unnamed or unknown merely because `getpwuid` or `getgrgid` has no entry. APX preserves the host numeric ID and may render its allocated rootless owner and namespace ID. For the usual rootless mapping, the account's real UID maps namespace ID 0 and subordinate range offset zero maps namespace ID 1. Range allocation identifies the owning rootless namespace; it does not by itself prove which container created a path.

The bounded Btrfs parser accepts a positive `Subvolume ID`, canonical UUIDs, and a `Parent UUID` of `-`, `none`, or `None` as an explicitly observed null snapshot parent. Missing fields remain unavailable; duplicates or malformed values are ambiguous. A successful subvolume command confirms only dedicated-subvolume status unless each identity field is also valid.

UUID uniqueness scans at most 1024 non-recursive directory entries, validates canonical JSON filenames, skips the current Environment, and compares only valid schema-v1 registrations. Confirmed duplicate UUIDs are `not-satisfied`. Malformed or conflicting non-registrations are ignored as invalid records; an unavailable, symlinked, or unsupported potentially relevant registration prevents confirmed uniqueness. No scanned file is followed through a symlink.

The future incomplete-operation location is `/var/lib/apx/incomplete-operations/<logical-name>.json`. Its directory and canonical record are inspected with no-follow, directory-relative metadata calls only. A missing directory or record confirms marker absence; a regular canonical record makes absence `not-satisfied`; unsafe or unreadable state is unavailable. Inspection never creates, removes, or repairs a marker.

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

Success requires a fresh observation confirming all of the following: registration parses as supported schema; account exists; account name and home match derivation; role matches registration; home exists and is a directory; filesystem is Btrfs; home is the root of the dedicated registered subvolume; subvolume ID, UUID, and parent UUID match registration; no other Environment registration binds the same subvolume UUID; owner is the canonical account UID; group is the account's private primary GID; mode is `0700`; registration is `root:root` mode `0644`; no incomplete marker remains; and the resulting classification is consistent. Current-context writability may be reported but does not independently determine consistency.

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

Approval binds the operation type, plan schema, logical name, derived account and home, role, normalized relevant preconditions, ordered typed mutations, and helper compatibility. It never authorizes arbitrary commands, different identities or paths, a broader operation, or failed preconditions. The digest is content identity, not authentication or authorization. A bounded approval, replay-protection, journal, and recovery protocol is now proposed in `privileged-executor-protocol-v1.md`; the human authentication technology and final transport remain unresolved and nothing is implemented.

Plan validity includes account, home, registration and candidate absence; parent and target path identity; Btrfs filesystem identity/capability; supported registration and plan versions; and future helper protocol compatibility. Transient diagnostics, timestamps, and random values are excluded. Content identity, host-state freshness, and authorization lifetime are separate. Digest equality cannot establish freshness: the privileged component must always re-observe, and any failed current precondition overrides a matching digest.

### Unprivileged and Privileged Boundary

Unprivileged `apx` may validate names, derive identity, read permitted registration, observe without mutation, classify unavailable state, build/render/digest plans, request human approval, later submit a typed request, and inspect results. It must not create accounts or subvolumes, change permissions, write root-owned registration, run arbitrary privileged commands, or treat a digest as authorization.

Future root-owned `apx-admin` may accept one small versioned typed request, validate independently, recheck authoritative preconditions, perform only the ordered bounded mutations, publish registration, verify postconditions, and return structured results. It must not expose a shell; accept arbitrary commands, executables, paths, account/home identities, UID, GID, shell, groups, or permissions; trust unprivileged observations; treat a digest as authorization; read unrelated home data; or contain Codex-specific behavior. No helper exists in the current system.

## The Hub

The Hub is an Environment dedicated to APX management.

The Hub is not a general desktop and must not become a development workspace. It
may include APX management UI, system status, visual customization, and tightly
scoped widgets. General-purpose browsers, editors, games, and workload software
do not belong there.

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

Initial boundaries are Linux users, Btrfs subvolumes, graphical login sessions, process ownership, filesystem permissions, and metadata files or records.

### Applications and Data Belong to Environments

Workload applications, their dependencies, data, configuration, and runtime
state must be local to their Environment. The exact package/root filesystem
mechanism remains under evaluation and must not be encoded before validation.

Reviewed immutable content may be shared or inherited from a versioned APX base
without permitting mutable cross-Environment application or data sharing.

### The Hub Is Clean

The Hub must remain focused on APX management, presentation, system summaries,
and tightly scoped widgets. Development tools, general-purpose applications,
build artifacts, source repositories, and implementation work belong in
dedicated Environments.

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
- The host architecture is one Arch installation and one kernel.
- Workload applications, dependencies, data, configuration, session state,
  processes, and metadata are separated by Environment.
- Package installation from inside an Environment always targets its own
  package database and root filesystem, never the host or another Environment.
- Each Environment corresponds to one dedicated Linux user and one intended dedicated Btrfs home subvolume.
- Each Environment has its own graphical login session, with only one graphical Environment active at a time.
- The Hub is an Environment dedicated to APX management.
- The Hub is the default Environment in the intended session model.
- The first Hub may be headless and use the bounded `apx` CLI as its management
  surface.
- The APX CLI is implemented and validated before graphical management controls;
  later buttons remain clients of the same typed protocol.
- The intended lifecycle is `Boot -> Hub -> Environment -> Hub`.
- The Hub must not become a development workspace.
- No implementation decision may require a unique lifecycle exception for the Hub.
- Linux accounts are hidden internal identity and ownership boundaries, not a
  complete VM-equivalent security boundary.
- Hyprland, KDE Plasma, GNOME, and other viable graphical choices must not alter
  APX service and session lifecycle semantics.
- The normal interface presents one human identity and no ordinary Linux user
  chooser.
- The Hub and workloads derive independently from a versioned APX base; the
  live Hub is never cloned into other Environments.
- Selected Environments may run isolated Odysseus or Codex assistants under
  explicit future Hub policy.
- Normal Environment services use `Linger=no` and stop with the Environment's final login session.
- Git, Codex, source, compilers, tests, and build outputs belong in Development,
  never Hub or the steady-state host.
- The preferred clean-install validation order proves headless lifecycle,
  isolation, storage, package locality, and recovery before Hyprland or another
  graphical Environment.

## Ideas Under Evaluation

- The display-manager and session-handoff mechanism remains under evaluation; `greetd` has not been adopted.
- H0 is the first graphical gate for a clean headless host. It starts with no
  graphical owner or display manager and returns through an independent text
  recovery path.
- The separate G2 exclusive-session design records the physical handoff safety
  boundary. Its companion broker/recovery proposal selects a two-VT,
  host-owned recovery direction for that experiment only; an executable
  preview remains blocked on exact mechanisms, fixtures, evidence, and fresh
  approval. The KDE/SDDM release proposal adds a generation-bound, two-pass
  conjunction so no single logout response, blank display, or missing process
  can authorize physical device handoff. Observation is split between an
  unprivileged collector, exact session-local adapter, narrow privileged
  read-only source, and separate effect executor.
  G2 is now the secondary in-place KDE/SDDM migration campaign and does not
  block the primary headless bootstrap or H0.
- The per-Environment application/root filesystem and normal/high-security
  isolation mechanisms remain under evaluation.

The provisional first backend to validate is a bootable Arch system container
using `systemd-nspawn`, Btrfs-backed state, user/network namespaces, explicit
device policy, and verified teardown. This is not an implementation decision
until the gates in [isolation-architecture.md](isolation-architecture.md) pass.
The initial security assumptions and required validation are documented in
[threat-model.md](threat-model.md).

The repository-level Stage 2 candidate is now modeled as a deterministic,
review-only package: a dated archive acquisition plan, five typed intended
resources, creation gates, postconditions, failure states, risks, rollback
rules, destructive-operation separation, blockers, and a dossier digest. This
is a proposal under review, not host state, approval, or an executor. See
[stage2-approval-dossier.md](stage2-approval-dossier.md).

## Open Questions

- What permissions should the Hub have to manage other Environments without creating a unique lifecycle exception?
- How should APX safely stop or hand off user processes during Environment switching?
- What exact display-manager/session-manager integration should APX use?
- What fixed login shell policy should future account creation use?
- What authentication mechanism should implement the proposed approval
  strengths and secure Hub session?
- What replay-resistant typed protocol should carry the approved dossier to a
  future independently validating executor?
- Which exact trusted-host `archlinux-keyring` version/file hashes and matching
  archive digest should instantiate the selected explicit bootstrap mechanism?
- What exact Btrfs qgroup hierarchy and fresh enforcement check should bind the
  8 GiB root and 2 GiB home budgets?
- What snapshot, quota, compression, backup, and archival-storage policies should APX adopt?
- What package, root filesystem, namespace, device, network, and security model
  provides Environment-local applications with defensible isolation?
- Which drivers, firmware, network facilities, fonts, certificates, and desktop
  defaults belong to the host, APX base, or role templates?
- How should Odysseus and optional Codex instances be provisioned and confined?
- How should future human identities own and group Environments?
