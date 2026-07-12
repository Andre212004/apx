# Base and Role Template Model v1

Status: product and architecture proposal complete for review; no template
catalogue, builder, release, or Environment creation is implemented.

## Plain-Language Summary

APX needs safe starting points for new Environments. A Games Environment may
need Steam and graphics support. A Development Environment may need Git and
compilers. The Hub needs APX management software but should not contain normal
work applications.

The proposal separates three things:

- the **base**, containing only common essentials;
- a **role template**, describing one reviewed type of Environment;
- the created **Environment**, which becomes an independent personal space.

A template is a recipe, not a copy of a live desktop. It contains no documents,
saved games, browser history, passwords, accounts, assistant memory, or Hub
authority. Publishing a new template version never changes an existing
Environment without a separate user-approved migration.

## Current Reality

The repository has a fixed minimal base proposal and a model for verifying
package evidence from a dated Arch Linux Archive. It has not produced a real
verified base or any role template.

The live Hub, Development Environment, and manually created accounts are not
templates. Their installed programs and mutable state are observations, not
reproducible APX releases.

## Four Layers

```text
host
  -> verified APX base release
       -> verified role-template release
            -> independent Environment root and home
```

### Host

The host owns the kernel, physical hardware integration, boot, and the minimum
trusted APX runtime. A template cannot add host packages, services, users,
drivers, mounts, or administrator rules.

### APX base

The base supplies the smallest common Arch userspace and reviewed integration
needed by every supported Environment. It excludes role-specific applications,
desktops, personal data, credentials, assistants, and Hub authority.

### Role template

A role template declares one complete starting configuration: base version,
packages, desktop profile, isolation profile, resource defaults, permitted
integration, and safe first-start actions.

### Environment

Creation gives the Environment fresh storage and identity. After publication,
its package changes, configuration, applications, documents, and local updates
belong only to it. The template does not remain a writable parent.

## Definition and Release

APX distinguishes a readable template definition from a built template release.

The **definition** explains the intended contents and policy. It is suitable for
human review but is not enough to create an Environment.

The **release** binds the definition to exact verified inputs and build output.
Only an admitted release can be used for creation.

A release identity includes:

- stable template name and role;
- human-readable version;
- complete content digest, which is the real immutable identity;
- exact base release identity;
- template-definition digest;
- complete resolved package and source evidence;
- desktop and isolation policy versions;
- builder and verification-tool identities;
- build-result and independent-validation digests;
- compatibility range and retirement status;
- reviewer identity and admission decision.

Reusing a version label with different content is forbidden. A changed byte,
package, policy, default, or first-start action creates a new release identity.

## Template Catalogue

The Hub may display a reviewed catalogue containing only admitted releases. A
catalogue entry explains in ordinary language:

- what the Environment is for;
- which main applications it includes;
- approximate initial and expected storage use;
- network and device access;
- whether graphics, audio, microphone, camera, USB, or gaming controllers may
  be used;
- security profile and its limitations;
- update status and known compatibility restrictions;
- which information is not included or shared.

The catalogue is informational and content-bound. Changing its friendly name,
icon, or description cannot change the underlying release. The Hub cannot add
an unreviewed local recipe or edit package lists through a hidden advanced mode.

## V1 Template Families

The first catalogue may define these families after individual review:

| Family | Intended purpose | Typical contents | Important exclusions |
|---|---|---|---|
| Hub | APX management and system summaries | APX UI and tightly scoped widgets | browser, editor, games, development tools |
| Minimal | simple trusted workspace | small desktop and basic utilities | role-specific applications |
| University | study and coursework | office, PDF, browser, communication choices | personal university login or documents |
| Development | software development | editor, Git, compiler, build/test tools | personal source code, keys, Codex credentials |
| Games | gaming | launcher/runtime and reviewed graphics integration | accounts, saved games, broad device access by default |
| High Security | risky or untrusted work | minimal tools under restrictive policy | GPU, raw input, secrets, assistants, open network by default |

These names describe product directions, not existing releases or promised
package lists. Hyprland, KDE Plasma, and GNOME variants are separate reviewed
releases when their packages and integration differ. V1 does not build one
template dynamically from arbitrary mix-and-match components.

## Hub Template Rules

The Hub release may contain the APX management UI, status presentation, visual
customization, and reviewed widgets needed for its role. The package containing
the UI does not contain administrator credentials.

Hub authority is supplied at runtime through the bounded broker/executor
protocol. It is not a file, group membership, reusable token, socket copied into
the template, or permission that survives in a snapshot.

The Hub definition must explicitly reject:

- general-purpose browsers and editors;
- development tools and source repositories;
- games and workload applications;
- personal assistant memory;
- live operation journals or registrations;
- approval keys, owner credentials, or recovery secrets;
- mutable state copied from the current Hub.

Hub recreation starts from an admitted Hub release plus separately defined,
safe user preferences. Unknown live Hub state is preserved for inspection, not
silently promoted into the rebuilt Hub.

## Package and Source Rules

A template definition declares package intent from approved source classes. A
release records the exact resolved packages, versions, architectures, archive
names, hashes, signatures, and signer identities.

The initial v1 source class is the verified dated Arch repository mechanism
already proposed for the minimal base. Additional source classes such as AUR,
Flatpak, language package registries, vendor repositories, or downloaded
installers require their own provenance, signature, sandboxed build, update,
and removal policy before a template can use them.

This restriction applies to template construction, not to the product promise
that installers used inside a running Environment affect only that Environment.
Local installation may make an Environment differ from its starting release;
it never changes the release or another Environment.

## Desktop and Hardware Profiles

A template release selects one reviewed desktop profile. The profile declares
packages and integration needs but cannot directly request host paths, device
nodes, commands, capabilities, or administrator options.

Hardware access comes from a separate versioned APX policy chosen from an
allowlist during creation or activation. For example, a Games template may be
compatible with reviewed AMD and NVIDIA profiles, but it cannot grant itself
every device.

The same separation applies to audio, camera, microphone, controllers,
removable storage, network exposure, portals, clipboard, and secrets. Friendly
template descriptions must state meaningful consequences of those choices.

## First-Start Actions

Some values must be unique to the newly created Environment. A release may
declare only typed, internally implemented first-start actions such as:

- generate a fresh machine identity;
- create the fixed internal Environment user;
- apply reviewed desktop defaults;
- enable a service from an internal allowlist;
- create empty application-data directories;
- record the Environment and release identity locally;
- display required first-use notices.

It cannot provide a shell script, command string, arbitrary executable,
download URL, host path, user-selected package hook, or reusable secret. Actions
run inside the new Environment boundary and are verified before registration.

## Personalization

Personalization occurs after creation and belongs to the Environment. Examples
include wallpaper, browser profile, university login, Steam account, source
code, SSH keys, editor settings, assistant memory, and saved games.

Templates may provide reviewed defaults but not personal values. A future user
preference system may reapply safe presentation choices across Environments,
but it must list every shared field and never become a hidden home-directory
copy.

## Build Pipeline

A template release is produced in an isolated, disposable builder with no
access to the live Hub, user homes, host credentials, APX approval state, or
another Environment.

The proposed pipeline is:

1. parse and validate the bounded template definition;
2. verify the referenced base and all source evidence;
3. resolve an exact closed package set;
4. build or populate a fresh staging root without host package mutation;
5. apply only typed template defaults and sanitization;
6. remove build-only state, caches not required by policy, logs, identity, and
   secrets;
7. make the candidate immutable;
8. inspect files, packages, services, accounts, permissions, and forbidden
   content;
9. independently rebuild or validate the same declared inputs;
10. compare canonical manifests and normalized output;
11. publish release evidence only after every check succeeds;
12. admit the release to the catalogue through a separate review decision.

Failed or partial builds remain unpublished operation-owned staging. They are
never launchable and are not automatically deleted if ownership or modification
is uncertain.

## Reproducibility

Reproducibility means APX can explain and independently recreate the starting
state from frozen inputs. At minimum, two clean builds must agree on:

- exact package manifest;
- normalized file-tree content and metadata;
- enabled services and accounts;
- template defaults and policy references;
- absence of machine-specific and personal state.

Expected nondeterministic fields must be excluded by design or normalized under
a reviewed rule. APX does not call a release reproducible merely because it
boots twice.

## Sanitization

Before publication, APX checks for forbidden content including:

- machine ID, random host identity, hostname, and runtime state;
- passwords, password hashes, private keys, tokens, cookies, or credentials;
- browser profiles, histories, downloads, and user documents;
- SSH, GnuPG, package-signing, or approval private material;
- assistant memory, prompts, conversations, or model credentials;
- Hub registrations, journals, socket endpoints, or management authority;
- build-environment paths, temporary files, caches, and uncontrolled logs;
- unexpected set-user-ID files, capabilities, services, accounts, devices,
  mounts, or network listeners.

Text scanning alone is not enough. The verifier also compares the complete
filesystem and system declaration against expected allowlists and structured
rules.

## Environment Creation

Creating from a release produces fresh root, home, account, storage, machine,
registration, and operation identities. The release is read-only and is never
the writable root shared by multiple Environments.

The creation plan shows:

- selected family and exact release;
- main included software;
- desktop and security profile;
- storage and resource limits;
- network and device consequences;
- download and build requirements;
- first-start actions;
- known compatibility limits.

After creation, verification proves that the new Environment can modify its own
packages without changing the base, template, host, Hub, or another Environment.

## Updates

Publishing a new base or template release does not silently update existing
Environments. The Hub may report:

- current release still supported;
- newer compatible release available;
- migration requires review;
- current release retired because of a serious problem;
- local Environment changes make compatibility uncertain.

V1 allows new Environments to use a newly admitted release. Existing
Environments continue using their recorded starting state and may update their
own local packages inside their isolation boundary.

Changing an existing Environment to a new base/template release requires a
future offline migration protocol with snapshot, compatibility checks,
rollback, and generation replacement. That protocol is deliberately not
invented as an in-place package command here.

For the Hub, reconstruction may use the last known-good release or a newly
approved release. APX must explain whether safe Hub preferences can be restored;
live Hub authority and unknown mutable state never migrate automatically.

## Retirement and Emergency Response

Removing a release from the catalogue prevents new creation but does not delete
existing Environments. If a release has a serious security or compatibility
problem, APX warns clearly and may block new activation only when an accepted
policy shows that continuing would endanger the host or other Environments.

An emergency block must identify the affected release digest, reason, policy
version, available recovery path, and the consequences of continuing or
stopping. It cannot become a remote arbitrary kill switch or silently delete
data.

## Template Import and Export

V1 does not accept templates created by exporting a live Environment. A future
promotion workflow may start from a snapshot only after explicit sanitization,
reconstruction from declared sources, independent review, and proof that no
personal or privileged state remains.

External template import is untrusted until full schema, provenance, signature,
content, policy, and compatibility validation. A friendly name or valid archive
digest does not make a template safe.

## Records and Privacy

Template evidence records public package and build provenance, policy, reviewer,
compatibility, and verification results. It does not record the contents of
personal Environments or inspect them to improve a template.

Local catalogue usage may record which release created an Environment, but
should not report that information externally without future explicit consent.

## Failure Rules

- Unknown or moving sources cannot produce an admitted release.
- Build success without independent verification remains incomplete.
- A partial release never appears in the Hub catalogue.
- A template cannot request broader host authority to fix compatibility.
- Missing sanitization evidence blocks publication.
- Updating a catalogue cannot mutate an existing Environment.
- Local Environment changes cannot alter a template release.
- Hub authority is never inherited from template files.
- Uncertain staging data is preserved for bounded recovery.

## Acceptance Gates

Before implementation:

1. Define canonical definition, release, catalogue, and evidence schemas.
2. Fix the first real role package manifests and plain-language descriptions.
3. Select the isolated builder and immutable artifact representation.
4. Implement fixture-only sanitization and reproducibility tests.
5. Define approved source policies beyond the verified Arch repository, if any.
6. Map desktop and hardware profiles without caller-selected host resources.
7. Prove two independent builds match under the chosen normalization rules.
8. Build malicious fixtures containing credentials, Hub authority, unexpected
   services, package hooks, and personal data and prove admission rejects them.
9. Design the later offline migration protocol before offering upgrades to
   existing Environments.
10. Review every first catalogue entry separately; this document does not
    approve their final software lists.

No gate authorizes downloads, package installation, template construction, or
host mutation.
