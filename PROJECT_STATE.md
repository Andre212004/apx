# APX Project State

This is the canonical continuity document for APX. Future work must read it
before proposing or making changes. Any change to the product objective,
development method, confirmed architecture, or accepted deviation must update
this file in the same change.

`CURRENT_HANDOFF.md` is now the concise companion for cross-chat continuity.
It records the latest owner-reported physical checkpoint, next expected audit,
active safety blocks, and immediate repository milestone. `AGENTS.md` requires
future sessions to read both files. The handoff never overrides this canonical
state; disagreement must be resolved explicitly.

The owner has now accepted a temporary development-method deviation for the
disposable Lenovo physical pilot: Codex, Git, and GitHub CLI may run directly as
`root@apx-host` so repository changes and physical lifecycle tests can be
automated. This grants the temporary agent host-wide technical access, but not
standing authority to destroy Hub or Development, change disks, reinstall Arch,
or perform broad cleanup. It may create and destroy only clearly named test
Environments that it created itself. The target-bound entry, prompt, evidence,
and exit boundaries are documented in
`docs/temporary-root-host-development-mode-v1.md`; the preparation helper is
`scripts/physical-pilot/prepare-root-host-development-mode-v1.sh`. This is an
experimental development exception, not APX architecture or production state.
The mode is not active until the owner explicitly runs the guide on the exact
physical host, and its later removal requires a fresh inventory and exact
cleanup approval.

On 2026-07-18 the owner renamed the GitHub account from `Andre212004` to
`andrepereira2004`. The canonical repository URL for current operations is now
`https://github.com/andrepereira2004/apx.git`. Dated evidence may retain the old
URL when it truthfully records what was observed at that time.

The first pure already-installed physical-pilot update contract is now
implemented in `src/apx_physical_update.py` and documented in
`docs/physical-pilot-update-contract-v1.md`. It binds one untrusted bounded
candidate to the exact expected installed revision, component set, tests,
compatibility, rollback, documentation, reconciled audit, machine, Hub,
Development, recovery, journal-health, and capacity evidence. A valid result
reaches only `ready-for-separate-import-approval`; activation requires another
approval and rollback retirement remains a later decision.

`src/apx_physical_update_journal.py` now fixes the ordered staging,
verification, activation, replacement, final verification, publication, and
rollback-retention record. Prepared or partial effects preserve state and block
automatic rollback or cleanup. The implementation contains no artifact reader,
transport, installer, service control, physical rollback, or cleanup adapter.
The physical audit and target-bound release remain mandatory gates.

`src/apx_physical_update_artifact.py` now closes the generic raw-artifact
boundary for physical updates. It accepts only canonical uncompressed tar bytes
containing one canonical manifest and the exact sorted regular component files;
it rejects links, special files, directories, extra members, traversal,
non-root/variable metadata, nonzero timestamps, PAX extensions, oversized
content, duplicate JSON, and every candidate/manifest/content disagreement. It
does not extract, execute, install, select a destination, or change the host.
The update evidence schema now truthfully accepts the owner-approved temporary
root-host development mode by requiring reconciled Development state and a
current root-host inventory instead of falsely requiring a Development
repository. An exact target artifact, transport, effect adapter, interruption
fixtures, immutable release, and separate approvals remain pending.

An exact host-runtime-only candidate was then built twice outside Git from
source revision `909a7de7a257ed7320544bd5faa409b96afc543e`; both 30,720-byte
tar outputs were byte-identical and passed the closed reader. The target-bound
preview is documented in
`docs/physical-runtime-generation-fix-update-2026-07-18.md`. It remains
`blocked` solely because the physical recovery console has not been exercised;
boot-entry metadata is not substituted for that proof. No artifact was
imported, installed, or committed and no release tag was created.

`src/apx_recovery_console.py` now provides the pure, closed receipt and
assessment boundary for that remaining gate. Verification requires distinct
pre-reboot and recovery boot identities, exact boot-component and physical
identity digests, an owner physically using the built-in keyboard to unlock
encrypted root and reach the independent root console, and a post-boot APX
reconciliation proving unchanged Hub, Development, and disposable hold with no
uncertain operation. It also requires explicit evidence of no disk,
encryption, bootloader, package, or APX lifecycle effect. The module performs
no reboot or mutation, and metadata alone cannot satisfy it. The physical
rehearsal still requires the owner at the machine and fresh approval for the
availability-affecting reboot window.

`src/apx_physical_update_effects.py` now closes the non-executing staging and
target-mapping plan. For the first runtime-only candidate it fixes logical
staging at `/var/lib/apx/updates/staging/<update-id>/candidate.tar`, binds the
candidate, installed evidence, ready preview, import approval, artifact bytes,
and every before/after/rollback digest, and maps only `host-runtime` to the
regular mode-0755 `/usr/lib/apx/apx-lab-runtime.py`. `/usr/bin/apx` is a
required exact symlink invariant, not a second replacement target. Physical
mapping of `host-executor` and `hub-client` fails closed until their service and
immutable/current-Hub effects have separate designs. The plan has no
filesystem, service, lifecycle, install, rollback, or cleanup adapter; physical
staging and activation remain unimplemented and unauthorized.

The owner-authorized physical recovery-console rehearsal completed on
2026-07-18. A controlled reboot crossed to a distinct boot identity; the owner
used the built-in keyboard, unlocked encrypted root, reached the independent
root text console, and returned to the root-host session. Exact marker,
machine, boot-entry, kernel, initramfs, Hub, Development, disposable-hold,
disk/encryption, package, systemd, and APX reconciliation passed with zero
uncertain operations. The sanitized receipt in
`docs/physical-recovery-console-rehearsal-2026-07-18.json` is `verified` with
evidence digest
`db70438f786c3282755c44940bc27a5b18095bd31eeb4a904dbce62003634ad2`.
No physical update or lifecycle effect occurred. The earlier update preview is
now stale because it bound recovery evidence as false; a new complete preview
is required and still grants no import or activation authority.

The first post-reboot H0 observation confirms the physical pilot is the clean
headless path, not the historical KDE/SDDM G2 topology. No display manager or
Host graphical package is installed; tty1 is the tested recovery console and
tty2 is inactive; AMD `0000:05:00.0` resolves to card2/renderD129 and uniquely
owns connected internal eDP-2 at 1920×1080; NVIDIA remains separately resolved
and excluded. Stable built-in candidates are the i8042 keyboard and ELAN
touchpad, while the ITE special keys and external Logitech device are outside
H0. Exact facts are in
`docs/hyprland-h0-read-only-observation-2026-07-18.md`.

The dated graphical supply chain was also reconstructed into `/tmp`: all 138
base and 194 role packages repeated double signature and metadata verification,
and the 332-package offline root rebuilt without Host/APX effects. Review found
that package installation alone left locally generated pacman private trust,
machine identity, install timestamps, and a transaction log, so it was not
publishable. `src/apx_hyprland_release_finalize.py` now validates the closed
build, removes only temporary pacman trust, empties identity/log state,
normalizes the 332 install dates, rejects private keys/random seeds/special
files, and hashes the complete normalized tree. The real finalization produced
tree digest `83c58deaa56c83c23eee57dc02ecd3a67ccaede0d75918932f7f3b9557ab3401`
and report digest
`fb8a06d588b3dbf0f48b8626a1effc0df95e4c6dd12bfa995f167fe0376c530a`,
with all secret/runtime counters zero. It remains temporary evidence, not an
APX release; reproducibility, promotion, mediation, watchdog, and H0 approval
remain required.

The pure H0 release-promotion contract now fixes the next boundary: only
`hyprland-h0-v1`, sourced from the exact finalized tree, may target
`/var/lib/apx/releases/hyprland-h0-v1/root`; its internal account is fixed to
Environment-local `apx` UID/GID 1000 and no caller path, command, package,
service, device, or configuration is accepted. A real read-only evidence
capture reverified the tree, absent destination, healthy Btrfs quotas, more
than 470 GiB free, exact generations, disposable hold, and zero uncertainty.
The preview is `ready-for-separate-promotion-approval` with zero blockers and
plan digest
`dc15038fa6147f6f2ba098e90f880898ff4523586117bc0a338f9ea6e067146d`.
At preview time promotion remained unexecuted; the preview itself did not
create an Environment or authorize GPU/input/VT access or Hyprland activation.

The owner then authorized only that immutable release promotion. The first run
safely preserved an exact account-configured partial because the normalized
source had no hostname file to replace. A digest-bound continuation accepted
only that reviewed partial, created the fixed missing hostname, measured the
configured tree, wrote the canonical manifest, set the Btrfs root read-only,
and reverified all neighbours. `hyprland-h0-v1` is now a physical immutable APX
release containing 332 packages, configured-tree digest
`4798a8f6a0396dfab94758a9bb2498364a72948c6b2587593eadc04faca15b92`
and manifest digest
`dc1beaaaf6f073f8c3493d2e6b1d001e4b5f07f431f8a522f2125f242151ea40`.
The source, Hub, Development, disposable hold, and APX uncertainty state are
unchanged. No graphical Environment or session exists yet; device mediation,
watchdog, Environment creation, and physical H0 approval remain separate.

The repository lifecycle runtime now recognizes the closed `graphical-h0` role,
maps it only to the promoted `hyprland-h0-v1` release, and assigns bounded 16
GiB root and 8 GiB home quotas. Its generic headless start path deliberately
refuses this role before any runtime effect, so creation cannot accidentally
grant graphics or bypass the future AMD/input/VT/watchdog adapter. This source
change is not installed on the Host yet and no Environment was created. The
fixed first name and update-before-create sequence are documented in
`docs/hyprland-h0-environment-creation-v1.md`.

An exact Host-runtime-only candidate for that committed change was built twice
outside Git and both 30,720-byte USTAR artifacts were identical. Its artifact
digest is `a1b55982d14fb0bdf7afa8f1dd7991caf9d3a7ad5e24b321510763ad5b675a66`
and the closed reader accepted only candidate runtime digest
`0d7cc0c0c0631b65f68639f8b4994e3e3441a817604487256a30edd82f96da9f`.
Fresh observation then found a post-reboot mismatch: Hub and Development have
no running machine or current unit, but both registrations still claim
`running`. The shutdown journal shows a clean controlled stop during the
recovery reboot. Physical update preview/import remains blocked until those two
registrations are reconciled through a separately authorized exact action.

The owner authorized that exact reconciliation; Hub and Development now
truthfully remain stopped with unchanged generations. The fixed runtime update
adapter retained the previous runtime and installed the verified candidate.
APX then created the first real stopped graphical Environment,
`codex-test-hyprland-h0-v1`, generation
`c4fc5c49-4106-4a56-b1f0-13bffa41a0c1`, from `hyprland-h0-v1`, with 16 GiB
root and 8 GiB separate-home qgroup limits. An intentional generic-start test
refused before any machine or graphical effect. GPU/input/VT/watchdog mediation
and physical Hyprland activation remain unimplemented and separate.

The next pure H0 boundary is now closed. A generation-bound device-lease plan
admits only AMD card2/renderD129, the stable built-in keyboard and ELAN touchpad
identities, and tty2; it excludes NVIDIA, tty1, other input, audio, camera,
network, Host filesystem, and executor access. Its current plan digest is
`3ef21d19a2518d4fcea9d51513cc1eee63f6ff593d4470bcc10955b06e3059cb`.
The Host watchdog contract uses a 120-second deadline, 15-second stop ceiling,
generation-bound termination, full revocation, tty1 return, zero-residue proof,
and no automatic graphical restart. The minimal Portuguese-layout H0 config
was parsed by the installed Hyprland inside the Environment as `config ok`
without devices or a graphical start. No physical lease or session exists yet.

`src/apx_hyprland_h0_watchdog.py` now fixes a non-extendable, generation/plan-
bound watchdog state machine. It cannot complete with tty1 unrestored or any
process, mount, socket, or lease residue. The internal H0 session runner starts
only transient seatd, drops Hyprland to UID/GID 1000 with four exact auxiliary
groups and no capabilities, and traps mediator cleanup. Both remain unexecuted;
an independent Host launcher and hostile interruption tests are still required.

The Host expiry adapter now exists and was rehearsed with no graphical unit or
device grant. It revalidates the fixed generation, stops only the exact H0 unit,
activates tty1, and measures exact nspawn, mount, and unit residue. An initial
false-positive from the outer test command was corrected by matching only an
exact nspawn machine argument; the repeated rehearsal proved tty1 restored and
zero residue. It cannot start/restart graphics, broadly kill, delete, or affect
Hub/Development. The independent arming/launch adapter remains pending.

`src/apx_hyprland_h0_launch_plan.py` now closes the two-unit command plan. It
binds the three fixed asset identities/modes, arms and verifies an independent
120-second expiry timer before any device grant, then describes only the fixed
generation-bound nspawn unit with closed device policy and resource/network
limits. Its plan digest is
`b5836e03a8c59f62018b58a4b9410a1dab1a7ee11c24fd03e64f1dab2b37d6ea`.
The module is pure; asset staging, launch, readiness observation, interruption
execution, and physical display activation have not occurred.

## Human Objective

APX should make one physical Arch Linux computer feel like a collection of
independent, disposable computers without presenting ordinary Linux user
management to the person using it.

Examples include separate Environments for university, individual subjects,
work, games, individual games, and unsafe development experiments. Installing
Steam in one games Environment must not make Steam visible in another
Environment. Installing two separate Steam copies in two Environments, with
different games and data, must be possible. A document created for university
must not appear in a games Environment. Deleting an Environment must remove its
local applications, data, configuration, processes, and state without branching
into or damaging another Environment.

APX is a platform and orchestration layer, not a separate operating system per
Environment. The host retains one Arch Linux installation and one kernel. The
technical mechanism that provides per-Environment applications and stronger
containment is not yet selected.

## Intended User Experience

The owner sees one human identity and a set of named APX Environments. APX may
use separate Linux accounts internally, but the normal interface must not show
the display manager's user chooser or require the owner to reason about those
accounts.

The intended flow is:

```text
Boot -> Hub -> selected Environment -> Hub
```

The delivery order is now CLI-first. The first functional clean installation
may present a headless Hub through the `apx` CLI and headless Environments
through physical console/session transitions. This is an implementation and
validation stage, not a change to the final one-human-identity product. A
graphical Hub and graphical buttons are later clients of the same bounded
protocol, not prerequisites for Environment lifecycle.

The machine enters the Hub directly through a future secure login or unlock
flow. From there the owner creates, configures, launches, archives, restores,
and deletes Environments. A future multi-person model may group Environments by
human identity, for example `andre` and `pai`; its authentication and ownership
model is deliberately deferred.

## Environment Product Contract

Each Environment is intended to behave like a complete logical computer:

- local applications and dependencies;
- local documents and application data;
- local configuration and session state;
- local processes and services;
- a selectable desktop or compositor, such as Hyprland, KDE Plasma, or GNOME;
- lifecycle operations that do not alter other Environments;
- isolation by default, with sharing only through a future explicit policy;
- optional creation from a reviewed template;
- optional local assistants enabled by policy.

Software installation is always scoped to the active Environment. Commands such
as `sudo pacman -S steam`, `yay -S ...`, `apt install ...`, Flatpak operations,
language package managers, vendor installers, and installation scripts must use
only that Environment's files, databases, and services. They must never install
into, upgrade, remove, or otherwise modify the host, APX base, Hub, or another
Environment. Host package management is not exposed through normal Environment
`sudo`.

Environments may inherit a reviewed, versioned APX base at creation. This base
contains common compatibility and presentation defaults without making the
Environments share mutable application or user data. Hardware drivers and
machine-wide network capability normally remain host responsibilities;
Environment-visible integration, fonts, certificates, desktop defaults, and
other safe baseline content may be supplied through the base after their exact
boundary is validated.

APX must support ordinary trusted workloads with strong separation. It should
also support a future higher-security profile for Environments used to run
untrusted code. The profile mechanism and its guarantees require a threat model
before implementation. APX must never describe user accounts or filesystem
permissions alone as VM-equivalent security.

## Hub Product Contract

The Hub is the minimal default APX Environment and the management surface. It
may contain APX management UI, system status, visual customization, and tightly
scoped widgets needed for that role. General-purpose browsers, editors, games,
development tools, and ordinary workload applications do not belong there.

Software cannot be installed interactively into workload Environments from the
Hub as an arbitrary privileged action. The Hub may select reviewed templates,
policies, and declared software sets during creation or configuration through a
future bounded APX management protocol.

The Hub is not an unrestricted administrator. Privileged lifecycle work belongs
to a small, typed, independently validating executor. The Hub must remain
destroyable and reproducible from its definition; its default role does not
justify bypassing Environment lifecycle or isolation rules.

The first Hub may be headless. Its `apx` CLI is a management surface, not a
general development shell. The Hub still excludes Git repositories, Codex,
compilers, editors, development browsers, build outputs, and experimental
scripts. A later graphical Hub must map its buttons to the same typed protocol
and cannot gain broader authority.

The live Hub is not the parent filesystem or template for other Environments.
The Hub and workload Environments are separate products derived from the same
versioned APX base plus different role profiles. Hub-only management UI,
credentials, permissions, metadata, widgets, and state must never propagate to
a workload Environment. Conversely, an accidental change inside the Hub must
not silently change future Environments.

## Local Assistants

Odysseus is intended to provide a local personal assistant inside selected
Environments. Each instance is active only while its Environment is active and
may access only the Environments explicitly allowed through future Hub policy.
The initial model is total separation between assistant instances. Cross-
Environment communication and shared memory are deferred.

Selected development Environments may also include Codex as a coding and
debugging tool. Codex must be treated separately from personal-assistant data
and permissions. The Codex used to build APX today remains temporary development
tooling and is not evidence that this future integration has been designed.

For the accepted owner-controlled physical pilot, Development will also receive
an optional local coding fallback after Codex is working. The initial selection
is Qwen2.5-Coder 7B Instruct through an Environment-local CPU-first Ollama
service and Qwen Code terminal agent. It complements Codex for bounded review,
diagnosis, documentation, and small confirmed changes; it does not approve or
promote its output. The service, model, configuration, indexes, conversations,
and tools belong only to Development, listen on Environment loopback, and stop
with that Environment. GPU acceleration and provisioning separate instances in
other Environments remain gated future work. The complete pilot boundary is in
`docs/local-development-agent-v1.md`.

## Confirmed Platform Boundaries

- one physical Arch Linux host;
- one host kernel;
- APX is the orchestration layer;
- separate internal Linux accounts remain the current identity and ownership
  foundation;
- one intended dedicated Btrfs home subvolume per Environment;
- local applications, data, configuration, and runtime state per Environment;
- only one normal graphical workload Environment active at a time;
- compositor- and desktop-independent lifecycle behavior;
- no visible ordinary Linux account chooser in the intended experience;
- templates are the intended reproducible starting point;
- a versioned common APX base may supply reviewed defaults to every role;
- no implicit cross-Environment data access;
- no Environment package-manager path to the host package database;
- no lifecycle exception that makes the Hub irreplaceable.
- the APX CLI is the first management interface and remains available beneath
  later graphical controls;
- a headless Hub is a valid initial Hub profile;
- graphical interface work follows successful headless lifecycle, isolation,
  storage, package-locality, and recovery validation.

## Decisions Still Required

The following are product requirements but not yet technical decisions:

- per-Environment application mechanism: container/root filesystem, image,
  package overlay, or another design;
- which minimal packages remain in the host package database and which
  graphical/runtime components belong in each Environment's package database;
- isolation boundaries and threat model for normal and high-security profiles;
- namespace, cgroup, capability, seccomp, device, IPC, network, and GPU policy;
- exact Btrfs layout for homes, application layers, templates, snapshots,
  archives, and restoration;
- desktop/compositor packaging and launch model;
- secure automatic entry to the Hub without exposing internal accounts;
- exact clean-bootstrap artifact, trust root, minimal host manifest, and typed
  installation protocol;
- exact non-graphical Hub and Environment session transport;
- session handoff and failure recovery;
- Hub-to-executor authorization protocol;
- template format, provenance, updates, and reproducibility;
- exact host/base/role-template boundary for drivers, firmware, networking,
  fonts, certificates, graphical integration, and defaults;
- multi-person identity, grouping, authentication, and ownership;
- Odysseus permission, memory, model, and lifecycle boundaries;
- Codex provisioning and separation from personal-assistant data.
- the exact Environment administrator policy: which local administrative
  operations are allowed and how local `sudo` is confined without creating a
  path to host administration.

## Provisional Isolation Direction

The first backend to validate is one bootable Arch system container per
Environment using `systemd-nspawn`, a versioned base, Btrfs-backed writable
state, user and network namespaces, reduced capabilities, explicit syscall and
device policy, cgroup limits, and verified teardown. This is a validation
direction, not an accepted implementation.

Podman/OCI remains a serious alternative or complementary runtime. Its rootless
model, image ecosystem, Quadlet integration, seccomp support, and standardized
CDI device injection are valuable, particularly for NVIDIA. A hardware VM may
be required for a future profile whose threat model includes hostile kernel
exploitation. The comparison, gates, and initial threat model are recorded in
`docs/isolation-architecture.md` and `docs/threat-model.md`.

## Provisional Lifecycle and Storage Direction

The repository now has a complete logical v1 proposal in
`docs/environment-lifecycle-and-storage-v1.md`. It separates immutable base and
role-template references from mutable root and home, ephemeral runtime,
immutable snapshot sets, and portable archives. It proposes generation-bound
registration and one write-ahead protocol for create, activate, stop, snapshot,
archive, restore, recovery, and destroy.

This is a review proposal, not confirmed or implemented architecture. Physical
Btrfs behavior is now mapped by a separate flat-subvolume and hierarchical-
qgroup proposal, and the lifecycle contract has passed repository-level review
against the normal and high-security threat objectives. Host topology,
disposable-fixture validation, backend identities, template artifact format,
executor authorization, and session handoff remain acceptance gates. These
proposals deliberately do not make the provisional `systemd-nspawn` backend a
hidden decision.

## Provisional Base and Role-Template Direction

The repository now proposes the safe starting-model system in
`docs/base-and-role-template-model-v1.md`. A minimal common base is separate
from readable role definitions, immutable built releases, and the independent
Environment created from them. Proposed families include Hub, Minimal,
University, Development, Games, and High Security, but no final package list or
release is approved by those names alone.

Templates never come from cloning a live Environment. They exclude personal
data, credentials, machine identity, assistant memory, operation records, and
Hub authority. A new release never silently changes an existing Environment.
V1 permits new creation from an admitted release; migration of an existing
Environment requires a later offline, reversible protocol.

This is a proposal, not an implemented catalogue or builder. Canonical schemas,
the isolated builder, artifact format, exact package manifests, reproducibility
evidence, sanitization fixtures, and per-release review remain required.

## Provisional Privileged Executor Direction

The repository now proposes a bounded Hub-to-executor protocol in
`docs/privileged-executor-protocol-v1.md`. In ordinary terms, the Hub may ask
for predefined APX actions but never receives a general administrator command
channel. The executor independently checks the current state, exact approved
plan, human approval strength, expiry, one-use nonce, operation journal, and
final result.

Routine launch and clean stop may use an unlocked APX session. Creation,
snapshots, archives, and restore require an explicit preview and confirmation.
Destroy, forced stop, and destructive recovery require fresh strong
confirmation and a plain-language explanation of possible data loss. A durable
write-ahead journal supports crash inspection; uncertain state preserves data.

This is a proposal, not an implemented privileged service. Human
authentication, secure Hub entry, final local transport, approval format,
minimal host privilege mapping, and failure-injection evidence remain required.

## Provisional Human Identity and Session Direction

The repository now proposes the complete visible single-owner flow in
`docs/human-identity-and-session-handoff-v1.md`. The person unlocks APX without
seeing internal Linux accounts, enters the Hub, selects an Environment, and can
return to a freshly activated Hub.

The Hub does not remain graphically active in the background. A minimal
host-owned broker provides only lock, transition, progress, and recovery while
APX stops one Environment, verifies teardown, and activates the next. If stop
cannot be proven, the next Environment does not open. If launch fails, the
broker offers bounded recovery without exposing a shell or turning a workload
into a temporary Hub.

APX cannot universally prove that every application saved its work. The
proposal therefore distinguishes ready, known blocker, and unknown safety;
unknown defaults to cancelling the switch. Force-stop requires fresh strong
confirmation. This is a proposal only: SDDM remains current, `greetd` remains a
candidate, and no broker, unlock, handoff, lock, or recovery flow exists.

## Provisional Environment-Local Administration Direction

The repository now proposes the local administration contract in
`docs/environment-local-administration-v1.md`. The owner may install software
and make system-level changes inside one Environment without receiving host
administrator authority. Local `sudo`, pacman, Flatpak, language managers, AUR
builds, vendor installers, hooks, services, and updates remain inside that
Environment's root, home, runtime, devices, network, and limits.

Local root is treated as a potentially hostile attacker, not a trusted safety
boundary. It must be unable to change the host, Hub, base, template, another
Environment, APX metadata, storage management, or outer resource policy. A bad
installer can still damage or expose its own Environment; APX offers honest
warnings and optional stopped-state restore points rather than claiming the
software is safe.

The owner-facing local-administrator confirmation must not copy a host password
or reusable approval into the Environment. Its exact mechanism, backend
enforcement, hostile-root denial tests, and package-manager experiments remain
unimplemented and required.

## Accepted Headless Bootstrap and CLI-First Direction

The preferred first functional APX installation is now a fresh minimal Arch
host with no KDE, Hyprland, SDDM, display manager, or graphical session. The
ordered development path is recorded in
`docs/headless-bootstrap-and-cli-first-v1.md`: verified bootstrap, headless Hub
CLI, headless Development, Environment-local installation and separation,
lifecycle/storage/recovery, first Hyprland Environment, graphical controls, and
only then an optional graphical Hub.

This is a development-method and clean-install decision, not authorization to
erase or reinstall the current machine. A future real installation requires a
separate target-bound dossier with verified repository history, restore-tested
personal backup, boot-tested recovery media, disk plan, minimal package
manifest, pinned APX artifact, exact effects, rollback, and explicit approval.

A Git clone is development source acquisition, not a privileged APX installer.
The steady-state source checkout, Git, Codex, compilers, tests, and build outputs
belong in the Development Environment. The Hub contains only the bounded APX
management client and role-appropriate state. Before any Environment exists, a
temporary host bootstrap staging area is an explicit bounded exception; it is
removed or archived after Development and the installed APX artifact are
independently verified.

Codex remains temporary Development tooling and never becomes a Hub, host,
executor, recovery, or product dependency. It may be removed from Development
only after source/history, remote or separately reachable copy, reproducible
build/test instructions, and Codex-independent CLI/graphical operation are
verified. Removing or destroying Development must not alter Hub or host state.

The physical headless pilot quota policy is now role-aware. Hub and Minimal
retain the experimental 4 GiB root and 2 GiB home limits; Development receives
a bounded 16 GiB root and 8 GiB home so its accepted roughly 4.7 GB local model,
Environment-local packages, Codex state, repository, credentials, and working
space can coexist. These are pilot limits, not production defaults. The first
physical Development was created under the earlier fixed 4/2 GiB policy, so
`scripts/physical-pilot/recover-development-quota-v1.sh` provides a guarded,
in-place migration. It requires the exact physical identity, stopped
Development registration, healthy traditional qgroups, expected subvolume
identities and old limits, then raises only those two limits and installs the
matching role-aware runtime. It preserves Development root/home content and
rolls limits back if final verification or runtime installation fails. Owner
execution and post-recovery physical validation remain required; repository
tests do not claim the recovery has run on the machine.

The first quota recovery release falsely rejected the installed `btrfs-progs`
status layout because its anchored shell expressions did not admit the leading
indentation used by `Enabled: yes`, `Mode: qgroup (full accounting)`, and
`Inconsistent: no`. The corrected parser normalizes only surrounding whitespace
and supports both known field-name/value formats. It still requires enabled
traditional qgroups and consistent accounting, rejects duplicate or malformed
safety fields, and continues to reject limit override or active rescan evidence.

The second quota recovery release reached the installed status parser but
queried qgroups through the `/var/lib/apx` `@apx` subvolume mount, which exposed
only qgroup `0/256` rather than the nested Development root/home qgroups on this
physical layout. The v3 recovery resolves the Btrfs filesystem UUID from the
fixed APX state path, creates a private temporary mount of that exact
filesystem's top-level subvolume ID 5, independently verifies filesystem UUID,
type, and root ID, and uses only that scope for quota status, discovery, limit,
verification, and rollback operations. The mount is removed on every exit.
This does not expose the top level to an Environment or make it persistent.

The same quota-status correction is now also present in both original bootstrap
sources: the VM laboratory bootstrap and its target-bound physical-pilot
counterpart. They accept the two observed `btrfs-progs` field layouts, enable
quotas only when explicitly reported disabled, reject ambiguous or unhealthy
accounting, and verify healthy traditional qgroups after enablement. This is a
repository correction only; it does not change the already frozen initial
physical-pilot tag or claim that either bootstrap was rerun.

The 2026-07-17 audit observed the Ollama package inside physical Development
with no downloaded model. Root-host reconciliation on 2026-07-18 later proved
that this audited Development generation no longer exists. The APX journal
records a complete stop and destroy of generation
`72b3777b-6dba-4175-8d3e-3fb24401bf50`, including completed `remove-home` and
`remove-root` effects, followed 13 seconds later by creation of generation
`b90155f6-ece2-44ae-91fc-42d91d6b35a5`. The replacement is running but has an
empty home, about 8 KiB of APX Environment state, and no GitHub CLI, Ollama,
Qwen Code, Codex, or repository. No registered APX snapshot, archive,
quarantine object, or catalogue object preserves the prior generation. The
journal does not identify who requested destruction. The owner subsequently
confirmed that this was their intentional lifecycle test, so it is not treated
as an unexplained security incident or executor malfunction.

The owner accepts the replacement as an intentionally simple Development
fixture and prefers not to reprovision its former toolchain now. The old
in-place quota-recovery route remains inapplicable to this generation. The
temporary root-host mode and checkout remain the explicitly bounded development
location while this work continues. This delays Phase 10 removal of root-host
development state but does not block repository development or physical tests
using newly created `codex-test-*` disposable Environments. Changing Hub or
Development still requires fresh exact approval.

The first root-host disposable lifecycle test created and cleanly started and
stopped `codex-test-lifecycle-v1`. It proved a running minimal system, 139
internal packages, a distinct PID namespace, link-local-only Environment
networking, no executor socket, no root-host checkout, no Development home, and
zero machine or mount residue after stop. Destruction was deliberately not
executed: the installed runtime generated a destroy plan with a random
generation instead of the registered generation and did not compare them before
destructive effects. A stale same-name plan could therefore target a later
generation.

The repository runtime now binds destroy plans to the current registered
generation and refuses a mismatch before journal, stop, unpublish, or removal.
Regression tests cover plan binding and pre-effect stale refusal. The physical
runtime is not changed by this repository correction. `codex-test-lifecycle-v1`
remains stopped and preserved until a separately reviewed physical runtime
update installs the fix; do not use the existing destroy plan or improvise
cleanup.

**Pinned owner decision — 2026-07-18:** local-model acquisition and execution
are deferred to a future milestone because the wanted model's storage cost is
not currently worthwhile. No Phase 9 or Phase 10 procedure may download a
smaller substitute merely to close the checklist. The current replacement has
neither Ollama nor a model; that minimal state is a valid deliberate outcome.
All Ollama/model lifecycle checks are `not-applicable` until this decision is
separately reopened. Host/Hub isolation, APX lifecycle, storage, quota,
recovery, and all non-model gates remain required. A future verified
package-only state would not by itself require keeping temporary Host bootstrap
material after every other applicable Phase 10 audit gate passes. The repository now proposes the external model
storage boundary in `docs/external-development-model-storage-v1.md`: one exact
encrypted device and attachment identity, visible only to one Development
generation, with bounded capacity, immutable model evidence, fail-closed
disconnect behavior, and no shared writable host or Hub path. This is a
proposal only. No disk, mount, runtime adapter, model relocation, or larger
model is implemented or authorized.

The first external-model-store repository contract is now implemented in
`src/apx_external_model_storage.py`. It parses one closed, duplicate-safe
evidence schema and fails closed on changed device, Development generation,
LUKS/filesystem identity, visibility, ownership, capacity reserve, partial
download, disconnect, recovery, or model-manifest facts. It produces only
`blocked` or `ready-for-separate-design-review` plus a no-effect plan digest.
It has no formatting, unlock, mount, attachment, download, or cleanup function;
the physical evidence, adapter design, failure fixtures, denial tests, and
target-bound destructive dossier remain required.

The same module now implements the closed `ModelArtifactManifest`. It binds a
served tag to its reviewed source, licence, Ollama version, measured size,
manifest digest, unique ordered blob digests, and explicit absence of partial
downloads, credentials, and conversation state. This closes only the pure
model-record contract; physical Ollama path observation and model acquisition
remain pending.

The external-store module also produces a deterministic attach preview only
from complete ready evidence. It fixes a private runtime path, the candidate
Development Ollama data path, ordered effect names, and a generation-bound
operation identity while carrying no command or execution function. The audit
must confirm the real installed Ollama path; physical detach evidence, the
runtime adapter, interruption experiments, and physical approval remain open.

The pure attach/detach journal is now implemented in
`src/apx_external_model_lifecycle.py`. It binds one preview to ordered attach
evidence, permits activation only from verified attached-stopped state,
requires separate detach approval, records ordered detach evidence, and treats
prepared, partial, disconnected, or otherwise uncertain state as preserve and
inspect. Its fixture store rejects replay, stale writers, and transition jumps.
It performs no disk, encryption, mount, service, Environment, or cleanup effect;
physical source adapters and interruption fixtures remain required.

The logical Development-to-Hub promotion boundary is now proposed in
`docs/development-to-hub-release-promotion-v1.md`. Codex and the Development
builder may produce only an untrusted immutable candidate. A closed host-owned
import copies one exact candidate into quarantine without executing it;
independent verification and a separately approved catalogue admission create
an immutable release identity. The executor then creates and verifies a new Hub
generation instead of allowing Development to mount, edit, enter, or
package-manage the live Hub. The old Hub remains a bounded rollback candidate
until separately approved retirement.

The first-Hub bootstrap uses the same logical verification and admission stages
from a temporary bounded pre-Environment staging area. Once the Hub creates
Development, normal Git/Codex/build work moves there. Candidate schema, artifact
format, physical import transport, trust roots, independent build method,
initial Hub manifest, safe preference schema, executor operations, and rollback
retention remain open and unimplemented.

The first graphical clean-host gate is H0. It starts from a verified state with
no graphical session or display manager, proves the independent recovery VT,
then grants only the selected AMD display and mediated built-in keyboard/
touchpad to one disposable Hyprland Environment. G2 remains the separate
secondary gate for migrating a live KDE/SDDM machine. G2 evidence is preserved,
but it no longer blocks the headless C0–C6 ladder or H0 design.

The first closed H0 repository contract is now implemented in
`src/apx_hyprland_h0.py` and documented in
`docs/hyprland-h0-clean-host-v1.md`. It binds reconciled audit, no-display-
manager/session/lease evidence, independent recovery VT, healthy APX state,
exact target AMD identities, explicit NVIDIA exclusion, exactly mediated
built-in keyboard/touchpad, forbidden audio/camera/microphone/broad-input/Host/
executor access, graphical release/config/control identities, watchdog,
timeout, and teardown observer into a no-effect preview. Complete evidence
reaches only `ready-for-separate-physical-approval`.

`src/apx_hyprland_h0_journal.py` now fixes ordered recovery-VT verification,
Hub/Development stop, lease reservation, AMD/input grants, Hyprland launch,
Wayland/control/watchdog verification, teardown, device revocation, zero
residue, and restored headless operation. Every partial or uncertain state
blocks automatic graphical restart and requires recovery-VT inspection. No
physical graphical adapter, package installation, VT switch, device grant,
compositor launch, or cleanup is implemented.

## Accepted First Clean-Install Foundation

`docs/clean-install-foundation-v1.md` fixes the first experimental C0–C6 target:
x86_64 UEFI, one explicitly identified disk, GPT, a 1 GiB EFI System Partition,
LUKS2 plus Btrfs, systemd-boot, text-only Arch, and `systemd-nspawn` with
mandatory private users and no graphical/device grants. This accepts nspawn
only for the headless implementation; H0 and future high-security profiles may
select a different or hybrid backend.

The initial source package-name manifest is `base`, `linux`,
`linux-firmware`, `btrfs-progs`, `cryptsetup`, `iwd`, `python`, and `gnupg`,
plus exactly one applicable CPU microcode package and proven hardware-specific
firmware. Exact versions, archives, hashes, signatures, databases, and signers
must come from one dated Arch snapshot in the target-bound dossier. Git, Codex,
build tools, desktops, display managers, browsers, and workload packages are
excluded from the steady-state host.

The first headless session is a broker-owned pseudoterminal, not a host shell or
machine selector. The first owner authentication method is a host-owned
password with fresh re-entry for strong confirmation, separate from the LUKS
recovery passphrase. The first APX host artifact is a signed, versioned Arch
`.pkg.tar.zst` with complete SHA-256 identity. Exact PAM/service code, real APX
trust keys/custody, schemas, privileged implementation, disposable-install
rehearsal, and target dossier remain unimplemented and required.

The first pure installation/promotion contracts are now implemented without
host effects. `src/apx_release_candidate.py` parses the exact headless-Hub
candidate schema, computes canonical identity, classifies every parsed candidate
as untrusted, and produces a reference-only quarantine import plan. It accepts
no command, path, destination, URL, signature shortcut, policy override, or
unknown field. `src/apx_clean_install_dossier.py` parses target and supply-chain
evidence and returns only `blocked` or `ready-for-separate-approval`; even the
latter still requires fresh strong disk approval and has no apply function.

The schemas and fixed future CLI vocabulary are recorded in
`docs/release-candidate-schema-v1.md`,
`docs/clean-install-dossier-schema-v1.md`, and
`docs/clean-install-cli-contract-v1.md`. The promotion and installation fixture
state machines are now implemented in `src/apx_release_promotion.py` and
`src/apx_clean_install_journal.py`. Promotion keeps import, verification,
admission, and immutable catalogue publication separate; its store accepts only
one exact allowed plan and compare-and-swap transition. The installation journal
expands all ten stages into ordered fixed effects, requires a separate approval
for each applicable current stage, and never automatically deletes uncertain
state. Its store accepts only one exact ready dossier and one-step transitions.

The release member and reproducibility contract is now closed in
`docs/release-artifact-manifest-v1.md` and implemented as a pure validator in
`src/apx_release_artifact.py`. It binds the candidate to a canonical ordered
tree and compressed-artefact digest; rejects special files, privileged modes,
path escapes, mutable identity/runtime state, personal homes, credentials, and
Development state; and requires exact independently rebuilt outputs. It does
not read or extract an archive and cannot admit a release.

The first packaging rehearsal is closed as an unsigned definition only in
`docs/bootstrap-development-package-v1.md` and
`src/apx_contracts_package.py`. `apx-contracts-development` contains exactly
three non-mutating validators, four package-owned contract documents, and the
repository licence declaration, with fixed source-to-target mappings, `python`
as its sole runtime dependency, no command/service/hook/installer, and exact
two-build evidence. It is deliberately not the production bootstrap package.
The project licence is now Apache-2.0. Commit
`c6f61ff7259fa71039c087023018731c6f3a774d` freezes the source used by the
first package rehearsal. `packaging/apx-contracts-development/PKGBUILD` binds
its Git-archive digest and exact eight payload files. An initial two-directory
build correctly failed reproducibility because Arch records absolute build
paths in `.BUILDINFO`. Two later clean builds at one canonical path produced
byte-identical 21,601-byte unsigned packages with SHA-256
`3895d89e34a95b38bc5559a49b87cd338725b3889a42122932fd2a0fe3fff76a`.
The retained sanitized evidence is in
`docs/bootstrap-development-package-build-2026-07-13.md`. This is same-
Development-environment evidence only; two separately created frozen builders
remain required, and the package was not installed, trusted, or published.

The independent follow-up is now positive. Two separate network-disabled Arch
containers from one pinned builder image produced byte-identical 16,109-byte
packages with SHA-256
`9d6e53007bc56e8a9105f4ff65c14097dbec13aa8b0b4c7ddb70912b01b012fd`.
A third disposable offline container installed the result; pacman reported zero
altered entries and all three modules imported. The full frozen identities are
appended to `docs/bootstrap-development-package-build-2026-07-13.md`. This
closes the development contracts-package build proof, not the functional APX
bootstrap or production trust.

The production trust operational boundary and mandatory physical rehearsal are
now defined in `docs/release-key-custody-and-ceremony-v1.md`. Root and release
signer roles are separate and offline; private material may never enter the
host, Hub, Development, Codex, Git, or a networked builder; two separated
encrypted backups and a proven restore are required; compromise, rotation,
revocation, signing, and sanitized evidence paths are explicit. This is a plan,
not a completed ceremony. Exact cryptographic profile/tool versions and an
explicitly approved offline disposable-machine rehearsal still block real-key
generation.

The disposable C0–C6 proof is now specified in
`docs/disposable-clean-install-rehearsal-v1.md`: one unmistakably disposable
x86_64 UEFI VM, one new 64 GiB virtual disk, no host shares or secrets, retained
text recovery, exact external evidence, checkpoints only for fault injection,
power loss before/after every destructive/publication boundary, and the full
Hub/Development/package-locality/lifecycle/offline-recovery ladder.

The experimental functional ladder passed on 2026-07-13 in a disposable QEMU/
KVM VM backed only by one new sparse 64 GiB qcow2 disk. A guarded installer
produced a minimal UEFI/systemd-boot/LUKS2/Btrfs Arch host without graphics.
An experimental headless runtime then demonstrated immutable role releases,
independent mutable roots and homes, private user and network namespaces,
Environment-local pacman and npm installation, quotas, stop with zero runtime
residue, snapshot, archive, restore to a new generation, destruction,
conservative recovery, and a real cold boot with QEMU `-nic none`.

The recreated `hub-headless-v3` contains only an unprivileged typed client. A
host-owned Unix-socket executor accepts fixed operation schemas and authorizes
the peer only when its host UID belongs to the active Hub's private 65,536-ID
map. The Hub used it to create, start, stop, and destroy a fixture. Host root
using the client was refused, and Development had neither the socket nor the
`apx` command. The full result, identities, failure corrections, checkpoints,
and limits are in `docs/virtual-headless-c0-c6-result-2026-07-13.md`.

This closes the functional virtual milestone, not the production-shaped formal
rehearsal. The signed functional bootstrap, production trust/custody,
untrusted-archive reader, broker/PAM authentication, minimum-privilege service
hardening, exhaustive before/after interruption matrix, hostile local-root
containment, physical recovery/backup dossier, hardware validation, and H0
remain required.

The owner has accepted a separate hands-on physical development pilot because
the current computer is dedicated to APX work and the GitHub repository is the
required source recovery copy. This does not waive disk-identity checks or turn
the pilot into a production release. The target is bound to Lenovo product
`82JU`, board `LNVNB161216`, and the 512,110,190,592-byte Samsung NVMe
`S4DYNX0R253702`. Any mismatch stops the run.

`docs/physical-headless-development-handoff-v1.md` is the autonomous ChatGPT
handoff from official Arch media to a headless Hub and separate Development.
The destructive installer and temporary host bootstrap are frozen through the
immutable `physical-headless-pilot-v1` Git tag; only the later Development
checkout follows `master` for ongoing work.
The two initial scripts under `scripts/physical-pilot/` are deliberately separate from
the VM installer: one erases only the exact reviewed NVMe after repeating its
model/serial/size checks and exact typed approval; the other admits only the
installed physical marker and exact Lenovo DMI identity before installing the
experimental runtime. On 2026-07-17 the owner reported that Phases 1 through 8
of the physical handoff had been completed on the target, including the initial
installation, Hub, Development, GitHub, and Codex setup. Phase 9 is partial:
Ollama is reported installed inside Development without a downloaded model;
quota recovery and the remaining package-only local-agent evidence are
pending. On 2026-07-18 the owner pinned model installation as a future-only
milestone and directed Phase 10 review to proceed without it. Phase 10 remains
subject to every non-model gate and separate cleanup approval. This is an owner
progress report, not independently captured repository evidence; the read-only
physical state and cleanup audit must reconcile the machine before cleanup or
a later host update.

This is an accepted development-method deviation, not a claim that the
production blockers are closed. The initial host Git checkout and Git package
are bounded bootstrap staging and must be removed only after Development has a
persistent checkout, working GitHub authentication, Codex, the accepted
local-agent checks, and the separately reviewed physical audit. Ongoing source,
build, GitHub, Codex, Ollama, model, and
Qwen Code work remains Development-only. The Hub still receives only the typed
client and no development tools or assistant endpoint.

Forty-eight focused tests cover canonical round trips, direct-object bypass,
duplicate/unknown/missing fields, commands and paths, wrong types, limits,
digests, fixed policies, every dossier gate, invalid dates/configuration,
deterministic plans, security-relevant digest changes, stale writers, forged
initial state, multi-step jumps, approval separation, every fake install effect,
interruption recovery, archive member policy, link containment, candidate/tree
binding, exact release rebuild comparison, closed package contents, and exact
package rebuild evidence. The complete suite now runs 635 tests: 631 pass and
four external-fixture checks are explicitly skipped because reboot removed
their bound `/tmp` evidence. There are no test failures or errors. No physical
candidate import, archive extraction, signature
verification, trusted catalogue, installer effect, disk operation, executor
effect, or production Hub creation is implemented. The separate guarded
VM-only runtime is experimental evidence and is not wired into the production
CLI.

The dated readiness audit is in
`docs/clean-install-readiness-2026-07-13.md`. A destructive installation remains
blocked by absent production trust keys/custody, bootstrap package, physical
quarantine/archive-verification/catalogue/Hub-replacement machinery, privileged
production executor/broker/authentication, reviewed physical effect adapters,
the remaining formal interruption matrix, and target-specific evidence. The VM
proves the functional architecture; it does not authorize running the
laboratory installer on the physical computer.

## Implemented Today

The repository contains documentation, a non-mutating production-oriented
Python prototype, and a clearly separated guarded disposable-VM laboratory. The
main `src/` prototype implements read-only candidate, account, home, filesystem,
Btrfs, registration,
session, process, removal-blocker, host-readiness, and Brave-isolation
inspection. It also implements deterministic dry-run creation and removal
planning, formal registration parsing, consistency classification, rollback
classification, a read-only Stage 0 system-container readiness observer, and
extensive tests. The repository now also contains a pure typed contract for an
immutable Arch Linux Archive base snapshot. It deterministically distinguishes
rejected structure, incomplete signature evidence, and fully verified fixture
evidence without downloading or installing packages. Its schema-v1 JSON
boundary rejects duplicate and unknown fields, wrong types, unsafe extensions,
oversized evidence, and excessive package counts, and supports deterministic
canonical round trips. The prototype also renders a fixed, non-executing
snapshot-acquisition plan and a review-only Stage 2 dossier with typed intended
resources, exact candidate paths and limits, gates, effects, failure states,
risks, rollback rules, destructive-operation separation, blockers, and stable
digests. A fixed `apx host snapshot-readiness` observer models read-only capture
of pacman/GnuPG versions, installed package identities, and regular-file
identity/hash evidence for the three fixed Arch keyring inputs; it accepts no
caller paths or packages and performs no trust mutation.

The documented lifecycle and storage proposal defines logical objects, stable
and transitional states, snapshot consistency, archive publication,
restore-to-new-identity, explicit destruction scope, and conservative
incomplete-operation recovery. None of that proposal is a mutating
implementation.

The repository also implements a pure, non-mutating Environment isolation-
policy contract in `src/apx_policy.py`. It provides exactly two fixed reviewed
profiles: `normal-desktop` and `high-security-headless`. It deterministically
rejects writable host binds, privileged mode, mapping Environment root to host
root, direct devices, lingering, missing required namespaces, incomplete
teardown requirements, policy drift, and false VM-equivalent claims. This is a
testable specification, not runtime enforcement or proof of containment.

The repository now also implements the pure Hub-to-executor contract in
`src/apx_executor_contract.py`. It exposes only the fixed create, activate,
stop, force-stop, snapshot, archive, restore, destroy, and recovery operation
families. Strict bounded parsing rejects unknown or duplicate fields, commands,
paths, malformed identities, and wrong types. Assessment binds the exact fixed
plan, consequences, Environment generation, active Hub session, approval
strength, five-minute maximum lifetime, one-use nonce state, and authoritative
current-state confirmation. It performs no authentication, nonce reservation,
host observation, or mutation.

The repository now implements the executor journal state machine in
`src/apx_executor_journal.py`. Before an effect may be reported as complete,
the journal must identify that exact next effect; completion requires fresh
final evidence. Every transition binds the preceding record, and strict
parsing rejects corruption, extensions, reordering, and malformed state.
Recovery permits automatic rollback only for clearly APX-owned, empty,
unpublished, and unused resources. Published, used, modified, foreign,
identity-uncertain, and effect-outcome-uncertain resources are preserved for
review. A repository-only fixture store exercises atomic replacement, stale-
writer rejection, restrictive file modes, and refusal to follow symbolic
links. This is durable test-fixture behaviour, not the future authoritative
host journal, authentication, replay reservation, or a mutating executor.

The staged route to user testing is documented in `docs/testing-strategy-v1.md`.
Repository contracts and fake evidence are tested first; one headless disposable
Environment, two-Environment attack tests, graphical features, and destructive
recovery each require later separate readiness evidence and explicit approval.

The read-only CLI now provides `apx host doctor`, a plain-language front door
to the fixed `isolation-trial` Stage 0 checks. It reports stop, wait, or ready
for review without executing any plan. Positive evidence observed without an
authoritative host channel remains unconfirmed, while any visible identity,
path, registration, or mandatory-tool conflict blocks progress immediately.
The command explicitly excludes the existing manually created `apx-trial`
candidate from reuse, modification, or deletion.

The repository now implements a pure trust-evidence seal in
`src/apx_trust_evidence.py`. It binds one bounded set of readiness checks to
the exact snapshot-acquisition plan, observation time, observer class, and any
preceding seal. Raw diagnostic output is not retained; each observation is
represented by a SHA-256 digest. Only complete evidence from the future
authoritative executor can become `verified`; restricted observations remain
pending and any failed requirement remains blocked. Strict canonical parsing
rejects unknown, duplicate, missing, wrongly typed, reordered-identity, or
tampered evidence. This does not create or persist a real host seal, download a
base, or provide executor attestation.

The fixed Stage 0 isolation observer now checks Btrfs quota accounting with the
read-only `btrfs quota status /home` operation. It requires traditional full
accounting, consistent state, and normal limit enforcement. The user separately
authorized and performed quota enablement and a complete rescan on 2026-07-12
for `/dev/nvme0n1p2`, which contains `/`, `/home`, `/var`, and `/.snapshots`.
The reported state is enabled, full qgroup accounting, not inconsistent, no
limit override, eight automatic level-0 qgroups, and no configured limits. APX
did not perform this host mutation. Custom hierarchy, limit assignment, bounded
enforcement testing, and quota recovery remain unimplemented.

Production Environment storage is confirmed to be elastic rather than
preallocated: an Environment using 10 GiB consumes approximately its actual
charged extents, while another may grow to 40 GiB without reserving that space
in advance. Safety still requires independently enforced per-Environment and
APX-pool ceilings plus a non-APX host reserve. Automatic growth is allowed only
while all capacity and quota-health gates remain satisfied. The Stage 2 trial's
8 GiB root and 2 GiB home limits are deliberately small experimental safety
bounds, not product defaults. Exact production reserve and fairness policy
remain to be measured and selected.

`src/apx_capacity.py` now implements the pure elastic-growth and Stage 2
capacity gates. Growth is not preallocated: a request is allowed only within
the independently supplied Environment headroom, APX-pool headroom, physical
free space after the host reserve, and healthy quota evidence. The disposable
Stage 2 experiment fixes a conservative 64 GiB host reserve, 16 GiB combined
operation headroom, and 2 GiB metadata margin. These are experimental safety
values, not production defaults. The current real host has sufficient reported
free space and healthy top-level quota mode, but the bounded enforcement
fixture and authoritative metadata-capacity evidence have not run, so the
capacity gate remains blocked.

The user then manually executed the separately authorized leaf quota fixture
documented in `docs/quota-enforcement-fixture-v1.md`. Qgroup `0/263` enforced a
64 MiB referenced limit: an attempted 80 MiB write stopped at 67,076,096 bytes
with `Disk quota exceeded` and a non-zero result. Quota accounting remained
full, consistent, and without limit override. The user separately approved and
completed cleanup. After a normal restart, subvolume ID `263` and qgroup
`0/263` disappeared, the automatic level-0 count returned from nine to eight,
and quotas remained healthy. This proves one leaf limit and eventual complete
cleanup, not the intended hierarchy, snapshots, concurrency, executor
recovery, or attestation; the complete capacity gate therefore remains blocked.

The repository implements only the pure in-place migration assessment in
`src/apx_installation.py`; `docs/installation-migration-v1.md` now separates it
from the preferred clean headless path. Installation beside the current KDE
session, G2 cutover, and optional legacy cleanup remain secondary gates. The
new clean path requires remote project history, restore-tested backup,
boot-tested recovery media, typed bootstrap, headless Hub/Development,
two-Environment isolation, local package proof, lifecycle/storage/recovery,
H0, then graphical controls. Even complete in-place evidence permits only a
package-by-package cleanup review and never authorizes KDE removal. No clean or
in-place installer or cleanup implementation exists.

`src/apx_stage2_gate.py` now implements the pure final conjunction gate for
the first bounded host experiment. It requires exact dossier and acquisition-
plan identity, verified snapshot and authoritative trust evidence, ready
capacity evidence, absent intended identities, verified parents and
subordinate IDs, verified quota hierarchy, captured host invariants, bounded
network approval, authenticated/unexpired/unused human approval, authoritative
journaling, and separate cleanup scope. No single positive can override a
missing gate. Complete evidence yields only eligibility for a separate Stage 2
execution approval and never includes graphical use, KDE removal, or cleanup.

`src/apx_acquisition.py` now implements the pure network/file boundary for the
fixed dated Arch base acquisition. It accepts only HTTPS at the exact Arch
Linux Archive origin and date, the reviewed repositories and architectures,
safe unique canonical filenames, and bounded file/aggregate sizes. Credentials,
ports, queries, fragments, redirects, traversal, unexpected repositories,
wrong ordering, duplicate files, incomplete transfers, symbolic links, and
hash/size/identity disagreement fail closed. It validates supplied manifests
and post-transfer evidence only; it performs no network or filesystem access.

`src/apx_staging.py` now implements a repository-only acquisition staging
fixture. It reserves one new operation directory in a caller-provided
disposable parent, binds it to the plan digest, uses restrictive modes and
no-follow opens, enforces file and aggregate bounds while streaming, verifies
exact size and SHA-256, and publishes without replacement only after durable
validation. Partial or mismatched bytes remain explicitly partial and are
never adopted. Existing state, symlinks, non-regular entries, changed modes or
plan binding, duplicate names, and unsafe filenames fail closed. It never
selects or writes a production host path and is not the authoritative store.

The repository now implements the pure complete-cleanup contract in
`src/apx_cleanup.py` and documents it in `docs/cleanup-completion-v1.md`.
Deletion offers `environment-only`, which preserves enumerated snapshots and
archives, or `complete-purge`, which includes every enumerated Environment
copy. Completion requires selected resources, account, registration, runtime,
mounts, open handles, network state, deleted-subvolume records, and qgroups to
be absent; quota state must remain consistent and protected neighbors
unchanged. `<under deletion>` and `<stale>` remain visible as `freeing-space`.
Identity reuse is forbidden until complete. Observed physical reclaim is
reported without claiming it must equal logical size. The Hub now supports a
read-only `cleaning` card and retains it until final evidence passes. No
destructive executor is implemented.

`src/apx_downloader.py` now implements a bounded streaming HTTPS transfer
contract with an injected non-redirecting opener and protected-byte sink. It
requires the exact archive host/date/path, a safe matching filename, status
200, unchanged final URI, one valid Content-Length, approved maximum and any
known exact size/hash. It closes and rejects redirects, early EOF, excess
bytes, malformed or non-byte responses, timeouts/open/read failures, digest
disagreement, and staging rejection. Tests use fake responses; the module does
not construct a network opener or perform a real download by itself.

`src/apx_http.py` now implements the fixed direct HTTPS opener for the Arch
Linux Archive. It disables environment proxies, cookies, and redirects; uses
the system CA trust with hostname verification and TLS 1.2 minimum; sends only
fixed non-secret GET headers; and rejects alternate schemes, hosts,
credentials, ports, query strings, fragments, changed final URI, invalid
timeouts, and sanitized connection/status failures. Tests inject responses;
no real acquisition has been performed.

The repository now composes bounded download and protected staging through
`src/apx_transfer.py`. `StreamingStagingWriter` writes chunks directly to one
exclusive partial regular file, enforces per-file and aggregate bounds during
the stream, and publishes without overwrite only after transfer and staging
size/hash evidence agree. Network or validation failure preserves the partial
identity and blocks blind retry. Integration tests use fake responses and
disposable directories; the composition does not select a production path.

`src/apx_database_acquisition.py` now implements the zero-argument fixed first
database acquisition: exactly dated `core.db` and `extra.db`, 64 MiB each and
128 MiB aggregate, into one new fixed `/tmp` root. The user separately
authorized and ran it on 2026-07-12. It transferred 8,818,209 bytes, published
exactly two mode-0600 regular files, and independent reopen/hash verification
matched both recorded SHA-256 values. Quotas stayed healthy; no installation,
extraction, execution, other download, or cleanup occurred. Exact evidence and
the preserved boundary are in `docs/database-acquisition-experiment-v1.md`.

`src/apx_repository_db.py` now strictly reopens staged Arch database archives
without extraction. It binds the regular-file SHA-256, bounds compressed and
expanded bytes and record counts, rejects traversal and unexpected archive
members, and validates unique safe package names/files, version, architecture,
sizes, SHA-256, base64 signature, and dependency fields. The two real staged
databases passed: 296 `core` and 14,842 `extra` package records. This validates
metadata structure only; it does not yet accept a resolved package closure.

`src/apx_resolution.py` now implements fixed offline resolution against only
the staged databases and an empty root/local package database. It runs pacman
print-only twice, requires identical output, cross-checks every selected field,
enforces seeds, uniqueness, 512-package and 4-GiB bounds, canonicalizes results,
and writes exclusive mode-0600 evidence. The real run selected 138 unique
packages totaling 128,264,129 bytes with manifest digest
`574f5d31e7c4ee46b1982fe2baf285d014ba0d712e91aea6d00413ba8fe5e3f9`.
No network, download, install, or extraction occurred. Exact evidence is in
`docs/package-resolution-experiment-v1.md`.

`src/apx_package_acquisition.py` now implements the zero-argument acquisition
bound to that exact manifest. The user separately authorized and ran it on
2026-07-12. Direct protected streaming published exactly 138 package and 138
detached-signature regular files totaling 128,294,816 bytes, below the
137,308,097-byte authorization. Independent reopen verified every package size
and SHA-256, signature non-empty/size/mode bounds, zero partials, and zero
unexpected entries. Quotas remained healthy; no install, extraction, execution,
other download, or cleanup occurred. Evidence is in
`docs/package-acquisition-experiment-v1.md`. Cryptographic signer verification
and independent second pass remain blocked.

The repository now implements a pure future-Hub view model in `src/apx_hub.py`.
It renders deterministic Environment and template cards, plain-language state,
warnings, and fixed request kinds from supplied evidence without reading or
changing the host. It enables normal actions only while one verified Hub is
active and the overall system is ready. Active, incomplete, unconfirmed,
duplicate, incompatible, or multi-active state fails closed. Delete requires
strong confirmation; unconfirmed state exposes only retry and read-only detail.
The complete visible flow is proposed in `docs/hub-experience-v1.md`; no
graphical application or functional lifecycle button exists.

The intended daily Hub interaction is now clarified: the owner uses a normal
Hyprland desktop with one APX taskbar control. Left-click expands about five
Environment choices directly upward; left-clicking one requests handoff.
Right-clicking a choice exposes its allowed management actions. Right-clicking
the APX control exposes create, archived Environments, and full management. The
full selected light management direction remains a secondary screen.

`prototypes/hub-demo` implements this interaction with in-memory demonstration
data, including create/delete confirmations and the full management screen. It
has browser-executed interaction tests and visual QA evidence, but no import of
APX host code, executor connection, Hyprland integration, persistence, or real
lifecycle effect.

Stage 0 has now been exercised on the real host without mutation. It confirmed
the fixed experimental identity is unused, `/home` is writable Btrfs with
capacity available, cgroup v2 and user namespaces are available, subordinate
IDs exist for `apx-development`, no systemd machine/image name collision was
found, and both AMD and NVIDIA hardware are present. The fixed Stage 2 headless
experiment plan is implemented but remains approval-blocked.

It does not create users or subvolumes, install isolated applications, launch or
switch Environments, write canonical registration, enforce isolation, manage
templates, run Odysseus, integrate Codex, or provide a Hub UI. Current manual
accounts have ordinary directories under the existing `@home` subvolume. SDDM
is the last confirmed display manager. The user-local Brave work is an
experiment, not an accepted application architecture.

## Development Method

1. Keep current observations, confirmed product intent, selected architecture,
   experiments, and open questions explicitly separate.
2. Translate the human objective into invariants and threat models before
   choosing mechanisms.
3. Prefer small reversible experiments with explicit backup, rollback, and
   acceptance criteria.
4. Treat restricted or sandbox-visible evidence as non-authoritative when host
   confirmation is required.
5. Specify typed operations, preconditions, postconditions, provenance, failure
   states, and recovery before adding privileged mutation.
6. Never expose an arbitrary privileged command channel through the Hub.
7. Test deterministic contracts and failure behavior before host experiments.
8. Do not modify the host from repository work without a separately reviewed
   milestone and explicit user approval.
9. Record conclusions from every experiment, including failed and inconclusive
   results.
10. Update this file whenever a goal, method, decision, or justified deviation
    changes.
11. Derive shared defaults from an explicit versioned base, never by cloning the
    live Hub or another mutable Environment.
12. Treat every package operation initiated inside an Environment as local to
    that Environment; host package changes require a separate host-level APX
    maintenance path and explicit authority.

## Deviation Policy

A deviation is acceptable when evidence shows that the current method cannot
meet the product contract safely, reliably, or maintainably. The same change
must record:

- the previous rule or assumption;
- the evidence that invalidated or limited it;
- the replacement decision;
- safety and compatibility consequences;
- migration or rollback implications;
- validation performed or still required.

The first recorded architectural correction is the application model. Earlier
documents assumed globally installed applications with only user data isolated.
The clarified product objective requires applications and their dependencies to
be local to each Environment. The technical replacement is intentionally open
until package, desktop, GPU, security, update, and storage experiments identify
a defensible mechanism.

The second clarification concerns common defaults. Total duplication is not a
product requirement: Environments may receive a shared baseline at creation.
For reliability and least privilege, the baseline is a declarative, versioned
artifact rather than the live Hub. This prevents Hub-only authority or mutable
state from leaking into workload Environments while still allowing consistent
hardware integration, fonts, networking support, and desktop defaults.

### Temporary Ollama Development Deviation

Until per-Environment application roots and services exist, the
`apx-development` account may temporarily use the already-present host Ollama
executable for Odysseus development. This is a development convenience, not an
accepted APX application-isolation mechanism or evidence that Ollama is local
to the Environment.

The previous rule remains the product requirement: the executable,
dependencies, service, configuration, models, and mutable state must eventually
belong to one Environment. Current evidence shows a host Ollama client at
`/usr/local/bin/ollama` and no implemented Environment package or service
boundary. A manual `apx-development` process successfully served the
user-selected model directory and Odysseus reached it through
`host.containers.internal:11434` only while Ollama listened on `0.0.0.0:11434`.
Closing the terminal stopped the process and produced an expected unavailable
response until it was restarted. This validates a lifecycle signal, not a
genuinely local installation or safe final network boundary.

The temporary replacement is deliberately narrow:

- do not install, update, or remove the host Ollama package or executable;
- do not create or enable a host system service;
- run Ollama manually as `apx-development` only when needed;
- select an explicit model directory owned by `apx-development` rather than a
  shared model directory;
- keep Odysseus configuration and mutable model state in the Development
  Environment account;
- do not describe Unix-account ownership as process, package, or GPU isolation.

This deviation shares the host executable, kernel, GPU devices, and any
executable-level vulnerability with the host. It does not prevent another
authorized host account from using the global executable, and its resource use
is not yet contained by an APX cgroup policy. Rollback is to stop the manually
started process and remove only the explicitly selected user-owned model state.
No host package rollback is part of this deviation because it authorizes no
host package change.

The selected model directory, manual start/stop behavior, listening-address
dependency, and a successful Odysseus request were exercised. Binding to
`0.0.0.0` may expose an unauthenticated API beyond the intended Environment and
is unacceptable as the final design. Disk/GPU resource behavior, private
Environment networking, readiness, authenticated management, crash recovery,
and teardown still require validation. The deviation must be retired when the
selected Environment backend can own Ollama and its service.

## Next Milestone

The package names, storage identities, resource limits, rollback boundary, and
snapshot evidence contract for Stage 2 are fixed in
`docs/base-and-storage-v1.md`. A dated 2026-07-11 acquisition candidate with
fixed derived source, staging/evidence paths, limits, phases, blockers, and
digest is ready for review. The trust mechanism is selected: explicitly freeze
the trusted host's installed `archlinux-keyring`, use it to authenticate a
matching isolated keyring archive, use pacman for fixed-path resolution and
download-only acquisition, `pacman-key` for primary detached verification, and
GnuPG for the reopened-file second pass. The next external-effect milestone is
to authenticate the matching keyring archive, approve bounded acquisition,
produce the real artifact, and verify every package signature and digest. Stage
2 creation remains a later separate approval. It must preserve these cases:

The acquisition phases, trust boundary, staging rules, independent validation,
publication semantics, failure classes, and remaining approval inputs are
specified in `docs/base-snapshot-acquisition-v1.md`. Exact intended Stage 2
resources, effects, gates, risks, rollback, destructive separation, and
blockers are summarized in `docs/stage2-approval-dossier.md`. Neither procedure
is authorized to run. Matching archive authentication, real signatures,
authoritative quota/capacity evidence, approval protocol, future executor
attestation, and separate human approvals remain unresolved.

The trust/tool identity observer was executed through an explicitly authorized
host context. It observed `archlinux-keyring 20260707.1-1`, pacman
`7.1.0.r9.g54d9411-2`, pacman-key `7.1.0`, GnuPG `2.4.9-1`, 17 keyring package
files with zero altered files, and the three fixed keyring hashes now frozen in
the acquisition plan. The CLI conservatively reported
`requires-host-confirmation` because the prototype has no privileged attestation
channel. The evidence closes the unknown version/file/hash inputs for planning,
but executor attestation and approval for the complete base acquisition remain
blockers.

A separately approved keyring-only acquisition then downloaded
`archlinux-keyring-20260707.1-1-any.pkg.tar.zst` and its detached signature into
operation-owned `/tmp` staging. The package SHA-256 is
`b47fc9c8066377e73d72bdb6a166bbbd829d5dcc745e424ef32436bd673cbc0d`;
pacman-key reported a full-trust good signature by fingerprint
`0429897DE5F3BDAC537A30696D42BDD116E0068F`. Direct use of the distributed
`archlinux.gpg` with gpg/gpgv failed due to its format. Exporting only the
trusted signer public key allowed a successful independent gpgv pass; the
exported key hash is
`0fcc071d58801d83e29a68f0ac0008c142f675cdfd8d8b7a27362ac1ec578470`.
Read-only metadata matched package name, version, architecture, and packager.
No package was installed. This closes the matching keyring archive blocker but
does not authorize or complete base acquisition.

The dated Arch repositories were resolved non-mutatingly to a closed set of 138
packages. A separately authorized download acquired exactly those packages and
their 138 detached signatures. Every package hash matches the closed manifest;
all signatures passed offline verification using current Arch master trust and
revocation inputs, followed by an independent `gpgv` pass that agreed on every
signer. The signature receipt digest is
`468116fb5277d91a099d0d4adbc5ca6579a5962965b062c0b6a1f09db9e4ea84`.
This completes acquisition and authenticity verification, not the base
snapshot. A bounded metadata-only pass has also matched the internal name,
version, and architecture of all 138 packages to the signed manifest. It
records 552,949,311 declared installed bytes and metadata digest
`0722db2c4a04f46d8617b7607e534dfd8429de6482bfbdaf57e3e69162a4f294`.
At that point a separately reviewed disposable extraction/build stage remained
required. No installation or host mutation was authorized by that evidence.

A separately authorized disposable extraction has now opened the complete
verified package set only under `/tmp`. The candidate contains 23,144 regular
files, 1,191 directories, 7,519 symbolic links and zero special files. It uses
606,330,880 allocated bytes under its 1 GiB ceiling. An independent tree walk
reproduced these results. Its tree digest is
`0f4e517a27ec474f63a3de74cec5df4f1a3adaee9a235a9c7e3c736a4e1622c1`.
This proves bounded assembly of a candidate filesystem; it does not admit a
base release, create an Environment, execute candidate content, or authorize a
host change. Candidate sanitization and structural validation are next.

Read-only candidate admission has now passed evidence integrity, core runtime
presence, and absence of machine-local identity. It truthfully reports four
blockers: raw extraction has development-fixture ownership, the local pacman
installed-package database is absent, isolated boot/stop has not passed, and no
generation-bound lifecycle record exists. The assessment digest is
`fcd1cc097f5ffb494225b73fe5bbbb627686a448b6542ae31587daa26900543a`.
`docs/first-environment-test-plan-v1.md` defines the closed route: rebuild a
correct offline disposable root, preview the isolated systemd-nspawn boundary,
perform one bounded networkless console boot, then verify complete stop and
cleanup. This remains a proposal and authorizes no package execution, boot, or
host mutation. A graphical Hyprland role follows a successful console gate.

The separately authorized first-console Phase A build has now created a correct
offline root only at `/tmp/apx-first-console-build-v1`. This is not a second
host Arch installation: it is the private filesystem intended for one future
Environment. Pacman installed the exact 138 verified local packages into that
root with networking disabled and recorded all 138 in its own local database.
The root uses 614,490,112 allocated bytes, has zero files owned by the
Development Environment identity, and retained zero special runtime entries
after bounded GPG finalization. Its final report digest is
`741fe1c332c334f9f0667b295ae98e7de686c752c3f415e169e0e48912535b68`.
No content has been booted. The next gate is an exact read-only boot preview;
actual systemd-nspawn execution requires separate approval.

The exact non-executing Phase B preview is now implemented. It preserves the
source through a volatile overlay, disables external networking and persistent
registration, shares no host path, applies private user mapping and a closed
device policy, and caps the test at 120 seconds, 512 MiB memory, 256 tasks, and
50% CPU. Its digest is
`676d22c1d3b9f8d5f9005d20583addeafdc0abdf42986b38b9c67cda29b8fd28`.
No container was started. Phase C boot and transient cleanup still require an
exact separate approval.

The first Phase C attempt was authorized against that digest but stopped before
systemd because nspawn requires comma-separated capability names. It returned
code 1, left zero matching processes and mounts, and preserved the source. The
failed-attempt report digest is
`daddc5109d728b2c9083114019da457568fa38488e5917409aa28c1f3fc5f413`.
The same protection list is now encoded with the required punctuation under
corrected preview digest
`53c30a3c55c1a6b5b196d9f73694b3b6851e7cab84fdcd6f4bcace24bdb91944`.
The executor intentionally refuses this corrected plan until separate approval.

The corrected plan was separately authorized and passed parsing, but the host's
`/tmp` filesystem cannot supply ID-mapped mounts. The attempt again stopped
before systemd with zero process/mount residue and an unchanged source. Its
report digest is
`0de4390b36caeb65f35fcc527ce92420615e263457b90bd09b2637295295bda7`.
Private-user isolation will not be removed. The new v3 preview creates a bounded
exact runtime copy below `/tmp/apx-first-console-runtime-v3`, permits ownership
shifting only in that disposable copy, retains all prior runtime limits, and
requires complete copy cleanup. Its digest is
`6853311174a1cf4b3822f663a96fc9715e8871f4b36e00ab7dd38400c4bc07a6`.
The executor refuses v3 until separate authorization.

V3 was separately authorized. It created and content-verified the bounded copy,
then stopped before systemd because nspawn forbids ownership shifting together
with its implicit read-only overlay. It left zero process/mount residue, removed
the copy, and preserved the source. Report digest:
`d13733fdf7ebf09a88b9072127a350f670997f40976cc517206a6afaedf428ae`.
The v4 preview removes only that redundant overlay: the disposable runtime copy
itself receives all writes and must still be removed. Every other boundary is
unchanged. V4 preview digest:
`0db2db8bdf726e4855244bb3201fb0290f2b5d15da1c6eaf7ee97494307c79c3`.
The executor refuses v4 until separate authorization.

V4 was separately authorized and retained a container PID 1 until the bounded
120-second timeout, after which it left zero process/mount residue, removed the
runtime copy, and preserved the source. It is not a passed boot because no
systemd readiness marker appeared and the private-user boundary rejected the
core rlimit. Report digest:
`6bd0d43a800b416201613932f93b8e2fe49c3f37dd834338cc5667c619a3c1f0`.
V5 enables explicit systemd console/status output and disables core-file
storage through a fixed policy only in the disposable copy. Every other limit
and cleanup rule remains. V5 preview digest:
`93aa2e816680a6f570ea584352063ab4841e5a1eca11cfc4ca0df466c9840c0e`.
The executor refuses v5 until separate authorization.

V5 was separately authorized and again retained container PID 1 to timeout,
then removed the copy with zero process/mount residue and an unchanged source.
Explicit console logging still produced no readiness marker, so it is not a
passed boot. Report digest:
`a68561a540c9cd2c8801df3e1696dded28581119fdd0577a2040938e2fa40156`.
V6 keeps the same isolation and adds at most 30 seconds of read-only `/proc`
observation to prove the PID 1 executable, four distinct namespaces, systemd
runtime marker, 138 internal package records, and hidden host Development home.
Its preview digest is
`7585522ccf01168db8efa4b6d6382d23f475bbc4b64d0f68580e127e189617ad`.
The executor refuses v6 until separate authorization.

V6 was separately authorized, observed for 30 seconds, returned code 0 after a
clean-stop request, removed the copy, left zero residue, and preserved the
source. Its observer missed PID 1 because it incorrectly required systemd's
mutable process title to retain an initial argument. Report digest:
`8d9cd684d9f670ba8ce08ac0bb751e490cbe73cae7d07610d18738c6f0816df1`.
V7 identifies the systemd executable and separately requires namespace PID 1
from the kernel's read-only `NSpid` field. No runtime boundary changes. V7
preview digest:
`0f59742d68e041b7bc2147dce7a2a901dd575ed0c99929875f1ac844dbcc883b`.
The executor refuses v7 until separate authorization.

V7 was separately authorized and produced the first positive isolated boot:
systemd was namespace PID 1, PID/mount/user/network namespaces differed, the
internal systemd runtime and 138 package records were visible, and the host
Development home was absent. Clean stop returned code 0, removed the copy, left
zero residue, and preserved the source. Report digest:
`310e12efec05eec8dcf7d52bc0192bf9289037c62d6b2ba83400e8c309be233e`.
The only false result came from expecting an invocation marker for a target
unit, which systemd does not publish. V8 uses the concrete user-session service
marker plus absence of `/run/nologin`; no isolation or execution behavior
changes. V8 preview digest:
`d0fa74a7695412a7cbc7560e70f879a3248562417754a1ac3895dd263c40e2f9`.
The executor refuses v8 until separate authorization.

V8 was separately authorized and repeated all positive isolation/lifecycle
evidence, but user-session readiness remained false after 30 seconds. It then
stopped cleanly with code 0, removed the copy, left zero residue, and preserved
the source. Report digest:
`e3a93175545bdeeeb56f1421eaee6bea98963f3c0bac33761c77a58185058b3d`.
V9 adds only fixed read-only `systemctl` queries inside the container for
overall state, multi-user/user-session state, failed units, and pending jobs.
It cannot change a unit. V9 preview digest:
`1f3bbd7c8b9701dd523c8185379093e82a8b9966e177dec229c296acc39aafa6`.
The executor refuses v9 until separate authorization.

V9 was separately authorized and completed the first console lifecycle gate.
Inside the isolated root, systemd reported `running`, multi-user and user-session
units were active, and no failed unit or pending job existed. All prior PID 1,
namespace, 138-package, hidden-host-home, clean-stop, zero-residue, copy-removal,
and source-preservation evidence repeated. V9 report digest:
`f129d383b0b6c4cc8a80882a46a7237c16becb76693a1af97b2f20ea11b44432`.
The final evidence-only assessment passed all six gates with digest
`de0266fa91884d05c84887a4a91740e52db82c3067d5fc454337f3509c6998b6`.
The next milestone is a separately versioned Hyprland graphical role: resolve
and authenticate its exact packages, define private display/GPU/input/audio/
portal/session boundaries, then perform a disposable graphical boot before
wiring the real Hub UI. The console result does not authorize those downloads
or device/session effects.

The first Hyprland graphical role is now resolved offline against the same
dated 2026-07-11 Arch databases. Fourteen explicit seeds produce 194 new
packages, 264,648,263 compressed bytes, and 1,022,339,199 declared installed
bytes; base plus role totals 332 packages. The manifest digest is
`e2f6adfc19e00dfe7cae21b4eab1650437edf24d817dc355a9af449d1cd9b25e`.
No network, download, installation, extraction, or graphical execution occurred.

The host has AMD PCI `0000:05:00.0` using `amdgpu` and NVIDIA PCI
`0000:01:00.0` using `nouveau`. `docs/hyprland-graphical-role-v1.md` selects
only AMD for G0 headless rendering, keeps KDE available for G1 nested display,
and defers physical KMS/input handoff to G2. NVIDIA, raw input, audio, and host
Wayland/PipeWire/D-Bus/portal sockets are not part of G0. Waybar is not the
final panel; the expanding APX taskbar control remains a dedicated component
with a desktop-independent lifecycle contract. Package acquisition and every
graphical/device/session effect require later approvals.

The graphical role packages were then separately authorized and acquired from
the dated Archive: exactly 194 packages plus 194 signatures totaling
264,707,836 bytes. Independent reopen matched all package sizes and hashes and
found zero missing, unexpected, or partial files. No package was installed,
extracted, or executed and no GPU/system effect occurred. Detached-signature
trust verification and the independent second cryptographic pass remain the
next gate before any role build.

All 194 graphical package signatures subsequently passed offline GnuPG trust
validation and an independent `gpgv` pass; both paths agreed on every signer
across 25 trusted primary identities. Evidence digest:
`15ee100d7be5bfef16278f476503c2b2d7e3546fb3027b5f3a541180dc302863`.
The first attempt safely exposed an overly broad interpretation of bare
`KEYEXPIRED` warnings from unrelated historical subkeys. The corrected policy
still blocks `EXPKEYSIG`, expired signatures, revoked/unknown/bad signatures,
and insufficient Arch master trust. No install, extraction, execution, GPU, or
system effect occurred. Bounded metadata inspection and a separately approved
disposable graphical-role build are next.

Bounded `.PKGINFO` inspection has now matched the internal identity of all 194
graphical packages to the signed manifest and reproduced 1,022,339,199 declared
installed bytes. Metadata digest:
`89ed0ab7623a93972bb403af33bbda4ee1ebb2717d285455fa4a240adea455df`.
No other package content was extracted or executed. A separately approved
offline build into a disposable copy is now the next gate; GPU and graphical
execution remain later and separate.

The separately authorized offline Hyprland role build has now copied the proven
console root to `/tmp/apx-hyprland-build-v1` and installed only those 194
verified packages into the copy with external networking disabled. Its internal
database contains 332 packages and the result uses 1,739,587,584 allocated
bytes under the 3 GiB ceiling. Full source content digests before and after
matched; zero Development-owned entries and zero special runtime files remain.
An independent read reproduced the report digest
`9331a5cf181fa550cc163a179a340aa17cc1f01aa6b2167585e8b909b087ce0e`,
package count, and Hyprland/UWSM/Foot presence. Nothing graphical was launched
and no GPU, display, input, audio, host session, Btrfs, persistent service, real
user, prior-area cleanup, or main-Arch package effect occurred. The next gate
is a separately bounded G0 headless launch using only the intended AMD render
device; it must preserve KDE and deny physical display and input access.

A 2026-07-13 reconstruction after `/tmp` cleanup reproduced the exact dated
database hashes, 138-package manifest, double signature evidence, and package
metadata digest. Its offline base build kept the same package count and storage
ceiling but legitimately differed by 40 logical bytes and generated a new
Environment machine identity. The finalizer previously required the historical
build-report digest and therefore blocked a valid reconstruction. The accepted
reconstruction rule now verifies the canonical report digest plus the closed
manifest, signature evidence, package counts, byte ceilings, ownership, and
identity invariants. It does not treat per-run GnuPG/log/identity bytes as a
reproducibility identity. A new final report remains bound to that exact rebuilt
root and does not replace the historical evidence digest.

The same reconstruction encountered repeated Wi-Fi interruption during the
194-package graphical acquisition. The staging correctly preserved completed
files and one `.partial` entry but intentionally refused implicit adoption. A
fixed recovery path now revalidates the plan, directory and file metadata,
expected names, package sizes, and package hashes, removes only recognized
partial files, and fetches only missing requests. Preserved signatures receive
no trust from resumption and must still pass the complete offline double
verification. This is a transport recovery rule, not package admission.

The recovered acquisition completed all 388 package/signature files with zero
partials. All 194 graphical packages then repeated the two independent
signature passes and exact metadata digest. The rebuilt graphical root contains
332 packages, uses 1,739,587,584 allocated bytes, preserves its reconstructed
base, and has zero Development-owned or special runtime entries. Its new
root-bound report digest is
`79aec029862f03c169afde83c97a1eb3fc67918b5826823f6c5b3e1f64831f56`;
G0 v13 is now bound to that digest rather than the removed historical `/tmp`
root.

G0 v13 completed with report digest
`abbb2428c5b288c9ffdc7cf624c607f908d2fab98e1e1a5da029af6334b03ef5`.
It passed container PID 1, private namespaces, 332 packages, transient seatd,
zero other DRM visibility, source preservation, zero process/mount residue,
and runtime removal. Hyprland still did not open AMD or publish `HEADLESS-0`.
The retained trace plus Aquamarine 0.12.1 source establish that the DRM backend
enumerates and selects canonical `cardN` devices. `AQ_NO_KMS_REQUIREMENT`
permits a card without outputs but does not turn the physical AMD render node
into a separately selectable compositor card. Exposing `/dev/dri/card2` would
add physical KMS authority and is forbidden in G0. This is an accepted negative
hardware/backend result, not permission to broaden the grant. G1 nested without
direct DRM is next; exclusive AMD KMS belongs only to a separately reviewed G2
after KDE teardown is proven.

A non-executing G1 v1 preview is now bound to the rebuilt 332-package root and
the current KDE socket `/run/user/1002/wayland-0`. It keeps the container network
private and the device policy closed, with no direct DRM, input, audio, D-Bus,
PipeWire, portal, or host-home path. Its one added surface is a read-only bind of
the exact Wayland socket to a fixed internal path. This is a provisional
functional test, not an accepted isolation boundary: direct Wayland protocol
exposure and host-session lifetime still require mediation. No G1 container or
window has been launched. The exact non-executing preview digest is
`42f2b4a128e95c6b9e12e0f9feb6f59147711e4a9920b7a62fa0dc2884f0dc03`.

The G1 campaign then completed the nested graphical gate. V1 confirmed that the
private-user mapping correctly prevented the internal UID from connecting to
the KDE socket as host UID 1002. V2 used a temporary ACL for only the exact
shifted UID and restored the original ACL byte-for-byte; it reached the Wayland
backend but lacked a renderer. V3 added only AMD `/dev/dri/renderD129`, never a
KMS `cardN`, and produced `WAYLAND-1`; v3/v4 exposed and safely recovered from
an outer-wrapper teardown defect. V5 signaled inner Hyprland directly and
passed: `WAYLAND-1` at 1280×720/60, a 4,319-byte internal screenshot, Hyprland
exit code 0, 332 packages, private namespaces, one render node, hidden host
Development home, exact ACL restoration, unchanged source, runtime removal,
and zero process/mount residue. Report digest:
`7e2328625de5fde3ba15b1f249f2108922fe14b1de475d88f4b42af32386bb82`.

This is a functional and cleanup proof, not acceptance of direct KDE Wayland
protocol exposure as final isolation. Production mediation remains required.
For the current KDE/SDDM machine, the next physical compatibility gate is G2:
prove KDE teardown, exclusive AMD KMS and mediated input ownership, bounded
failure recovery, and return without residue. For the preferred fresh headless
installation, H0 is the first physical gate and G2 is not a prerequisite.

That G2 design and acceptance contract is now recorded in
`docs/hyprland-g2-exclusive-session-design-v1.md`. It fixes a no-network,
AMD-only, disposable boundary; separates the broker, executor, and Environment
adapter; orders KDE stop, authoritative release proof, exact device grant,
hidden launch, reveal, revocation, teardown, and verified return; and defines
mandatory failure exercises. It explicitly forbids wildcard DRM/input grants
and treating a blank display as proof of release.

The companion `docs/hyprland-g2-broker-recovery-boundary-v1.md` now selects the
candidate boundary for this experiment only: one host-owned text recovery VT,
one separate Hyprland experiment VT, temporary exact SDDM quiescence, and a
host-owned per-run mediator that provides revocable descriptor access only to
the approved GPU and input identities. The recovery controller has a closed
interface and no shell, while the executor owns deadlines, journal, revocation,
and authoritative state. This does not adopt SDDM, `greetd`, a production
broker, or a mediator implementation. No executable G2 preview is safe yet:
the exact controller and SDDM mechanisms, installed-version adapter and host
observations, stable device resolution, mediator compatibility, fixtures,
physical recovery rehearsal, and fresh approval remain absent.

The companion `docs/hyprland-g2-kde-release-proof-v1.md` now selects the
authoritative outgoing-session release contract. KDE adapter acceptance is
only permission to observe; release requires two complete, generation-bound
passes across login session and seat, cgroups and descendants, user services
and assistants, graphical IPC, AMD DRM/connector ownership, selected input and
VT ownership, mounts, namespaces, helpers, and SDDM absence. Refusal, timeout,
missing facts, identity change, or contradiction blocks the device grant and
enters recovery. The installed KDE/Plasma request, exact SDDM runtime operation,
host-version observation APIs, pure evaluator fixtures, read-only preview, and
fresh approval remain required. This documentation authorizes no host effect.

The first non-disruptive G2 host observation is recorded in
`docs/hyprland-g2-read-only-observation-2026-07-13.md`. The installed stack is
Plasma/KWin 6.7.2, SDDM 0.21.0, and systemd 261.1. The host login manager showed
the active Development KDE session on `seat0`/`tty4` and a second live inactive
Hub KDE session on `seat0`/`tty1` retained by `sddm-autologin`; the latter still
had its own KWin, Xwayland, Plasma, portals, audio, secret, and lock processes.
Consequently G2 must gracefully release and independently prove both graphical
session generations absent, not only the foreground desktop. SDDM must also be
quiesced against greeter respawn and Hub autologin before any KMS grant.

The same observation proved that component versions, login/session/cgroup
identity, SDDM lineage, Wayland socket identity, AMD PCI/card/connector ancestry,
ordinary DRM pathname descriptors, and input ancestry are readable. It found
current AMD users including Xwayland, Plasma Shell, Brave, and a KDE logout
greeter. KWin was not represented as an ordinary `/dev/dri/*` pathname in that
scan while logind still marked the AMD devices as seat-managed, so `fuser` and
`/proc/*/fd` absence cannot be the sole DRM release proof. DRM master/logind
reference/lease inspection, a version-bound two-session observer schema, exact
Plasma logout behavior, SDDM quiescence, recovery VT, and device mediator remain
blocked. No logout, service action, or device effect occurred.

A follow-up read-only availability check found the DRM debugfs boundary is
root-only and the login-manager seat API exposes active/session ownership but
not the complete DRM master/lease tree. `modetest` exists but was deliberately
not run because opening the primary DRM node is outside the non-disruptive
availability gate. The selected release direction is a narrow executor-owned
cross-check of all resolved primary/render descriptors, matching kernel DRM
client state when available, and logind seat/session state. The executor exposes
only a typed result. This is still unimplemented and untested; no new user,
Hub, adapter, or Environment access to debugfs or DRM is proposed.

The logical G2 observer/evaluator schema is now recorded in
`docs/hyprland-g2-release-observer-schema-v1.md`. It discovers every graphical
session from the physical seat instead of trusting fixed session numbers,
classifies systemd user-manager records separately without ignoring their
resources, freezes SDDM/greeter/autologin topology, and records process/cgroup,
IPC, mount, namespace, recovery, selected input, and separate AMD primary,
render, master, lease, login-manager, connector, and NVIDIA-exclusion fields.
Its public outcome is only `released`, `blocked`, or `unknown`; only two complete
clean observations in the same boot/generation after the bounded stability
interval can report `released`. Any reboot invalidates the prior baseline and
all transient identifiers. Unknown sources, topology disagreement, or changed
identity fail closed. The schema is complete logical architecture, not an
implementation. Source-adapter/evaluator implementation and fixtures, SDDM and
Plasma operations, recovery controller, device mediator, bounded-evidence
validation, a fresh post-reboot preview, and approval remain required.

The logical source/privilege mapping is now recorded in
`docs/hyprland-g2-observer-source-adapters-v1.md`. It separates an unprivileged
collector, one exact outgoing-session KDE adapter, a narrow privileged read-only
source, and the independently approved effect executor. Every schema area is
mapped to package provenance, login1/systemd D-Bus, cgroup/proc, sysfs, Wayland
object metadata, matching kernel DRM client state, input ownership,
mount/namespace identity, or recovery-controller evidence. The privileged
reader accepts only signed-plan identities, re-resolves them, never opens a DRM
or input node, never runs `modetest`, and returns bounded typed facts rather
than raw debugfs/proc output. No general root shell, sudo path, group/ACL change,
world-readable debugfs, broad polkit rule, or runtime privilege widening is
proposed.

The DRM schema was corrected to admit only an exact baseline-bound host kernel
console/fbdev client for the recovery VT while still requiring zero outgoing or
unexpected primary/render clients, no lease, no outgoing logind device
reference, matching connector identity, and NVIDIA exclusion. An unclassified
kernel client remains `unknown`. First denial limits are 10 seconds and 4 MiB
per observation, a two-second minimum stability interval, a 30-second pair
deadline, and fixed count/string ceilings. The adapter design and limits are
not implemented or validated; installed-version fixtures, a fresh post-reboot
read-only preview, exact Plasma/SDDM effects, recovery controller, device
mediator, and explicit effect approval remain required.

The first separately authorized G0 attempt passed its system-container,
namespace, exact-device, source-preservation, and teardown boundaries. It
exposed only AMD `/dev/dri/renderD129`, with zero other DRM nodes, and left zero
processes or mounts before removing the runtime copy. Hyprland briefly started
but exited without publishing `HEADLESS-0`, opening the render device, or
creating a screenshot, so G0 has not passed. Report digest:
`40d8a76dbe8c7f1e602b90868b68a6b31f101cc7a08a3065ef3240fda0d995a3`.
The first runner did not retain its bounded output, preventing a proven cause.
A non-executing v2 correction uses an ordinary UID 1000 only inside the runtime
copy and preserves up to 1 MiB of diagnostic output in a separate evidence
directory. It retains every prior isolation and cleanup boundary and requires
fresh authorization before another GPU-visible execution.

G0 v2 was separately authorized and again passed container PID 1, private
namespaces, 332 internal packages, exact AMD-only visibility, unchanged source,
zero residue, and runtime-copy removal. Running as ordinary internal UID 1000
did not resolve rendering: retained diagnostics show Aquamarine failed at
`CBackend::create()` before Hyprland opened the render node or published
`HEADLESS-0`. Report digest:
`c2d19362a2cdab0787938da8caf634a1aeb08c8e8f729637d776bf7984233f72`.
Current official documentation confirms the render-only environment flags.
A prepared, non-executed v3 keeps the identical device boundary, creates the
missing internal cache path, and enables bounded Hyprland/Aquamarine tracing.

G0 v3 was separately authorized and again preserved the complete outer safety
boundary, but still did not open AMD or create `HEADLESS-0`. Its report digest
is `20f23e577319176e3dc1373649bcd7620f9705fffa15fdf3494894f8dbc695ea`.
The runtime copy was removed and the bounded trace was retained under the
protected v3 evidence root. A subsequent read was refused because the host
authentication window had expired. The next action is read-only diagnosis of
that existing trace, not another graphical execution or broader device access.

The user supplied the protected v3 trace. Hyprland loaded the intended config
and then failed at `CBackend::create()`; the later `lspci` and working-directory
messages are crash-report side effects. The test incorrectly forced unsupported
`LIBSEAT_BACKEND=noop`; current libseat offers seatd, logind, embedded seatd,
and automatic selection. A prepared, non-executed v4 removes only that invalid
override and captures any crash report before deleting the runtime copy. It
does not broaden device, session, namespace, time, or persistence authority.

G0 v4 was separately authorized and its preserved crash report proved that
Aquamarine found neither a seatd socket nor a logind primary session for the
disposable user. It therefore never opened AMD. Every outer isolation and
teardown check passed; report digest:
`5974fa90c3b66277dbcc1c32b1fb383d00c6c269cb72070d0cfadff7d4355518`.
A prepared, non-executed v5 runs the already-packaged seatd binary only in the
foreground inside the disposable container, with a private socket owned by the
disposable user. It creates/enables no service and retains exact AMD render-only
visibility, private namespaces, bounded time, source preservation, and cleanup.

G0 v5 was separately authorized. Its transient seatd process stopped before
creating the socket because the packaged Arch version rejects `-s`; Hyprland
therefore repeated the known no-seat failure. Isolation, unchanged source, zero
residue, and runtime removal passed. Report digest:
`8e178e66be24cde9907d87862dceb2ef7ee18cf6325d15a8345cbb3badae10d6`.
Arch seatd defaults to `/run/seatd.sock`; prepared, non-executed v6 removes only
the incompatible option and retains every safety boundary.

G0 v6 started the transient mediator but uncovered a teardown bug in the test
runner: it signaled the outer namespace wrapper rather than inner seatd and
raised before normal cleanup. APX immediately observed the exact v6 processes
and mount, stopped the container, verified mount disappearance, and deleted only
the authorized v6 runtime copy. No v6 evidence report was published, so the
render result is inconclusive. Prepared v7 targets the inner daemon PID and
registers emergency teardown for unexpected runner exceptions. The user's
standing authorization permits further G0 versions only within the unchanged
AMD-render-only, no-network/input/audio/KMS, 120-second, disposable boundaries.

G0 v7 passed transient-seat startup, direct inner-process teardown, and all
prior cleanup gates. Seatd nevertheless kept the client inactive because it
could not bind to an intentionally absent physical VT, so no device opened.
Report digest:
`43a7d155b5c9f8f39928416d5b6d718961bf4f945935e6983e34e8b9f108cb7b`.
Official Arch seatd documents `SEATD_VTBOUND=0` for a seat not bound to a VT.
Prepared v8 adds only that setting and does not add KMS, input, or another
device.

G0 v8 activated the official non-VT-bound seat, but seatd and Aquamarine proved
the nspawn-created render entry could not be canonicalized or opened. Cleanup
again passed; report digest:
`555e54af0d09c4937afe74b06464d6ea941e0bc06046b2a320647205b0d7e5c7`.
Prepared v9 replaces only that unusable bind with an ephemeral internal
`/dev/dri/apx-amd-render` character node carrying the exact authorized AMD
major/minor `226:129`. The closed outer device policy remains unchanged and no
KMS, input, or other device is added.

G0 v9 again cleaned up safely but did not publish the headless output. Report
digest: `7370f014e3f8b847c47f511a669b13d3483b6d2f82e20c5b9ffa45f6f3def78d`.
The root-owned evidence read was blocked after host authentication expired.
Prepared v10 repeats the same runtime and device boundary while assigning only
the new evidence directory/files to Development UID 1002, avoiding repeated
administrator reads without exposing runtime or source content.

G0 v10 made evidence directly readable and proved the current Aquamarine build
does not accept an arbitrary alias for the explicit DRM device. It continued to
seek the standard AMD render name. Cleanup passed; report digest:
`c3e20c7fa4b0d2e762aaadd1046d5f8588209ff56c4b27deb5bc968a34cbe6e2`.
Prepared v11 retains the ephemeral character node and exact major/minor
`226:129` but names it `/dev/dri/renderD129` as expected by the backend.

G0 v11 still failed to open the standard-named node, while cleanup passed;
report digest:
`9fe499eecc102200d01a4c81637ef14e83823b0d7eb3f650f8964a95129e2854`.
The node-creation umask could remove write permission. Prepared v12 explicitly
sets `0666` to match the authorized host render node and records the internal
user's bounded pre-launch stat evidence.

G0 v12 left zero observed process, mount, and runtime-copy residue, but its
outer authorization wrapper remained stuck after the Python child ended and no
final report was published. The render result is inconclusive. Prepared v13
writes a bounded Development-readable progress journal from the beginning so
the last completed stage survives any outer-wrapper failure. The prepared
evidence path and files remain executor-owned and only group-readable by the
Development identity; fixed ownership, permissions, and no-follow opening keep
read access from becoming control over a privileged evidence path.

- two Environments independently installing the same application;
- deletion without residual application or user data;
- desktop operation under Hyprland, KDE Plasma, and GNOME;
- GPU, audio, input, portals, notifications, secrets, and removable devices;
- normal and high-security profiles;
- updates, rollback, templates, snapshots, backup, and recovery;
- reproducible common-base updates without mutable cross-Environment state;
- Odysseus limited to one active Environment;
- no ordinary Linux user chooser during boot or switching.

No container creation, package change, Btrfs mutation, or privileged operation
is authorized merely by the plan. The first host mutation requires a fresh
review of the exact base source, disk budget, created resources, backup,
rollback, and approval request.
