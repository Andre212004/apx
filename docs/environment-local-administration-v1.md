# Environment-Local Administration v1

Status: product and security proposal complete for review; no local
administrator confirmation, package isolation, or enforcement is implemented.

## Plain-Language Summary

The owner should be able to install programs and change system settings inside
an Environment without becoming administrator of the physical computer.

For example:

```text
sudo pacman -S steam
```

inside `Games-1` installs Steam only in `Games-1`. Running the same command in
`Games-2` produces a separate installation. Removing `Games-1` removes its
Steam installation without touching `Games-2`, the Hub, or the host.

Local administrator access is powerful inside its own Environment. It can
break that Environment, delete its files, install unsafe software, or expose
its data through the network. APX limits the damage boundary; it cannot make an
untrusted installer harmless to the Environment that runs it.

## Current Reality

Per-Environment package installation and local administrator confinement are
not implemented. The repository has proposals for a system-container backend,
storage, templates, lifecycle, sessions, and a privileged host executor, but no
running Environment currently provides this contract.

The existing Arch host package database remains the real machine package state.
No current `sudo` command should be treated as safely Environment-local merely
because it was started from an APX-related Linux account.

## Two Different Administrator Roles

APX separates:

- **Environment administrator:** may change only one Environment;
- **host administrator:** may change the physical APX installation.

Normal Environment users receive only the first. Host administration belongs
to the small APX executor and separate maintenance workflows. The Hub does not
turn an Environment administrator request into a host command.

The word `root` is therefore contextual. Root inside an isolated Environment
is not host root. The backend must enforce that difference even if software
inside the Environment is malicious.

## What Local Administration May Change

Subject to the Environment's own policy and storage limits, local
administration may change:

- its root filesystem and local package database;
- programs and dependencies installed inside it;
- its internal users, groups, passwords, and service configuration;
- its own `/etc`, `/usr`, `/var`, caches, logs, and temporary state;
- files in its own home;
- services that run only while that Environment is active;
- user-level and Environment-local Flatpak installations;
- language packages, development tools, games, launchers, and vendor software;
- local firewall or application settings that cannot override host mediation.

These changes may persist between activations because they belong to that
Environment's writable root and home.

## What It Can Never Change

Local administration cannot change or obtain write access to:

- the host root filesystem or package database;
- host package locks, cache, signing keys, boot files, kernel, modules, or
  firmware;
- APX bases or admitted template releases;
- the Hub root, home, credentials, metadata, or management authority;
- another Environment's root, home, processes, services, sockets, or network;
- APX registrations, operation journals, approvals, audit records, or replay
  protection;
- Btrfs top-level access, subvolume ownership, snapshots, quotas, or archives;
- host systemd, login manager, display manager, PAM, users, or administrator
  configuration;
- undeclared devices, host D-Bus, host runtime sockets, or host secret stores;
- the host's network policy, physical Wi-Fi credentials, or inbound exposure;
- the broker or privileged executor executable, policy, socket, or state.

These are structural denials. A warning, convention, Linux username, or package
manager setting is not sufficient enforcement.

## Local Administrator Confirmation

The intended experience does not ask the owner to understand an internal Linux
account or reuse the host administrator password inside an Environment.

When a command requests local administrator access, APX should show a clear
Environment-scoped confirmation such as:

> Allow this command to make system-level changes inside “Games-1”? It cannot
> administer the physical computer, but it may change or damage this
> Environment and its files.

The confirmation binds the active Environment and local request. It does not
create a host executor approval. Host credentials, approval keys, and reusable
unlock tokens are never copied into the Environment.

The exact mechanism is open. It may use an Environment-local authentication
agent receiving a short-lived scoped result from the host session broker, but
must not expose a reusable host socket or secret to local root. Until that
channel is threat-modelled and tested, ordinary per-Environment credentials are
a safer experiment fallback than passwordless unrestricted `sudo`.

## Sudo Policy

Normal-profile Environments may offer local `sudo` after explicit owner
confirmation. The resulting process may become root only in that Environment's
user and runtime boundary.

V1 must not use:

- passwordless unrestricted `sudo` by default;
- the host owner's password copied into Environment PAM state;
- host `/etc/sudoers`, PAM files, shadow database, or authentication sockets;
- a helper that accepts an arbitrary command and runs it on the host;
- supplementary host groups such as storage, disk, wheel, docker, libvirt, or
  device-administration groups as an isolation substitute.

High-security Environments disable local `sudo` by default. Enabling it is a
visible policy change because malicious code that reaches local root has more
ways to attack the shared kernel and Environment boundary.

APX assumes local root may become hostile. Security tests therefore run from
local root, not only from the normal Environment user.

## Package Managers

Every Environment has its own package database, package lock, configuration,
keyring state, cache, installed-file set, and local repositories. None is a
writable bind or shared database from the host, base, Hub, or another
Environment.

### Pacman

`pacman` reads and changes the Environment root. Its hooks and install scripts
run as local root inside the same boundary. They can start only local services
and see only allowed mounts, network, devices, and sockets.

Installing a kernel or host-oriented package inside an Environment cannot
replace the running host kernel. It may be useless or break that Environment,
so templates and the Hub should explain incompatible packages where known
without pretending to make them impossible.

### Yay and AUR helpers

AUR packages execute community build instructions and are therefore untrusted
code. Builds occur inside the Environment using Environment-local temporary
storage, package tools, network policy, and resource limits. They receive no
host build cache, signing secret, source repository, or cross-Environment cache
by default.

Installing from AUR may compromise the entire Environment. APX should warn the
user before first enabling that source class. High-security profiles deny it by
default.

### Flatpak

Both user and “system” Flatpak scopes must remain inside the Environment. A
system Flatpak installation means system-wide for that Environment, not the
physical APX host.

Flatpak portals do not automatically grant host-home access. File selection,
devices, secrets, notifications, and other portal functions follow the active
Environment policy.

### Language package managers

Tools such as npm, pip, Cargo, RubyGems, Go tooling, and similar managers write
only inside Environment root/home/cache paths. Global installation refers to
the Environment, never the host.

Shared download caches are deferred. They create cross-Environment content,
privacy, corruption, locking, and ownership risks and cannot be introduced as
an invisible performance optimization.

### Vendor installers and scripts

Downloaded installers, shell scripts, launchers, and self-updaters run with the
same Environment boundary and network/device policy. APX cannot verify every
vendor's behavior. It can show origin and requested local administration, take
an optional snapshot, and limit the damage to the selected Environment.

No installer can ask the Hub to “finish installation” with host authority.

## Package Hooks and Services

Package hooks, service enablement, timers, sockets, and background processes are
Environment-local. They start only within that Environment's lifecycle unless
a future explicit policy permits a narrowly defined persistent service.

The default remains no lingering after stop. Successful stop verifies that
package services, local user managers, containers started inside the
Environment, mounts, and network processes are gone.

A package cannot create a host service by writing a unit file inside its local
`/etc` or `/usr`. Host systemd never reads Environment-local service directories
as host configuration.

## Devices and Network

Local root cannot expand the devices or network access selected by APX policy.
Changing local groups, permissions, udev rules, firewall rules, or service
configuration cannot make a denied host device or socket appear.

Granted access can still be dangerous. For example:

- GPU access expands the shared-kernel/driver attack surface;
- microphone or camera access can expose private information;
- raw input can observe keystrokes;
- network access can upload Environment data;
- removable storage can import or export files.

The Hub explains these consequences when enabling a profile. Package
installation cannot silently broaden it.

## Resource Limits

Local root cannot remove or raise APX's host-enforced CPU, memory, process,
storage, network, or runtime limits. Commands inside the Environment may show
or change local settings, but the outer limit remains authoritative.

When disk quota is reached, package installation fails inside that Environment.
APX reports that the Environment is out of allocated space rather than claiming
the host is full. Increasing the limit is a separate Hub operation with a clear
capacity consequence.

## Local Updates

An Environment may update its own packages independently. This does not update
the immutable base, template release, host, or another Environment.

The registration records the starting base/template release, not a false claim
that the Environment still matches it byte for byte. APX may report local drift
such as:

- unchanged from starting release;
- locally updated;
- locally modified beyond package records;
- state cannot be fully classified.

Local updates can break the desktop, package database, boot, or hardware
compatibility of that Environment. APX should offer an optional stopped-state
snapshot before significant upgrades. It cannot guarantee rollback for external
accounts, remote services, or data changed after the snapshot.

Host and base updates use separate maintenance workflows. They cannot be
triggered through Environment `pacman` or local `sudo`.

## Hardware Compatibility

Some hardware userspace, especially graphics integration, must remain compatible
with the host driver. APX records the relevant host/profile compatibility and
checks it at activation.

Local root may install a conflicting library inside its Environment. That may
make graphics fail there, but cannot replace host drivers. APX reports the
incompatibility and offers recovery; it does not silently bind host libraries
or grant broader devices to make the application work.

## Recovery from a Bad Installation

Before a risky installation or large upgrade, the user may choose “Create a
restore point first.” APX stops the Environment, creates a verified snapshot,
and then reopens it before installation begins.

If the Environment later fails, the user can:

- retry or repair inside the same Environment;
- inspect what changed where reliable package evidence exists;
- restore into a new Environment identity from the earlier snapshot;
- preserve the broken Environment for file recovery;
- delete it only through the normal explicit data-loss flow.

APX does not automatically erase a broken Environment or pretend every package
change can be perfectly reversed.

## Multiple Package Systems

An Environment may use several package systems, but APX does not merge their
ownership databases. Pacman, Flatpak, language tools, and vendor installers can
overwrite or conflict with each other's files inside the Environment.

APX can report known sources and storage usage, but “remove everything installed
by this application” is guaranteed only when the relevant package system can
prove ownership. Deleting the entire Environment remains the clean complete
boundary.

## Audit and Privacy

APX records security-relevant facts such as a local-administrator approval,
policy change, snapshot reference, storage-limit change, or failed boundary
check. It does not collect shell history, source code, package search terms,
document names, or full installer output as host audit data by default.

Detailed local package logs stay inside the Environment and are deleted with
it unless explicitly archived.

## Required Denial Tests

Tests must run as both the normal Environment user and hostile local root. They
must prove inability to:

- read or write host, Hub, base, template, or sibling storage;
- see or lock the host package database;
- execute a command through the host executor;
- create a host account, service, mount, subvolume, snapshot, or network rule;
- access undeclared devices, host D-Bus, secrets, or runtime sockets;
- escape process, user, mount, IPC, network, and cgroup boundaries;
- exceed storage and compute limits;
- leave processes or mounts after verified stop;
- convert an Environment-local approval into host approval;
- persist authentication material into a snapshot or archive.

Malicious package hooks, maintainer scripts, AUR builds, service units, Flatpak
portals, language installers, and vendor scripts are required fixtures.

## Failure Rules

- Unavailable boundary evidence blocks activation or local-administrator
  enablement.
- Package-manager success never proves host isolation; host and neighbor state
  are independently checked in experiments.
- Local root compromise is treated as an expected attacker condition.
- Compatibility failure never expands mounts, devices, capabilities, or host
  authority automatically.
- Local package corruption remains inside the Environment and is reported
  honestly.
- A failed installation cannot authorize deletion or automatic restore.
- Host maintenance cannot be disguised as an Environment package operation.

## Acceptance Gates

Before implementation:

1. Select and validate the backend's local-root mapping and reduced privilege
   boundary.
2. Design the Environment-local confirmation mechanism without copying host
   credentials or exposing a reusable host channel.
3. Define normal and high-security local-administrator policies.
4. Build two disposable fixtures with independent package databases and prove
   duplicate installation, update, removal, and deletion.
5. Run malicious local-root and package-hook denial tests against the host,
   Hub, base, and sibling Environment.
6. Validate pacman, Flatpak, one language manager, and one untrusted build path
   separately.
7. Prove services and nested runtimes stop completely.
8. Test quota exhaustion, package database corruption, interrupted upgrade,
   incompatible graphics userspace, and snapshot-based recovery.
9. Define user-facing warnings for AUR, scripts, vendor installers, devices,
   network access, and force recovery.

No gate authorizes package installation, account changes, container startup, or
host mutation.
