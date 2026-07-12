# System Container Experiment Specification

Status: ready for review and Stage 0 read-only execution; no mutating stage is
authorized.

## Purpose

This experiment determines whether a bootable Arch `systemd-nspawn` system
container is a credible APX Environment backend. It must produce evidence, not
configure a permanent Environment or prove the entire APX architecture.

The experiment is divided so read-only host inspection, repository modeling,
temporary creation, graphical enablement, and destructive cleanup never share
one implicit approval.

## Fixed Experimental Identity

```text
Experiment name: system-container-v1
Logical Environment: isolation-trial
Derived account: apx-isolation-trial
Canonical home: /home/apx-isolation-trial
Profile: high-security-first
Persistence: disposable
```

This identity is reserved only for the future experiment. Existing paths,
accounts, registrations, subvolumes, machines, images, or container records with
matching names are blockers, never adoption candidates.

## Non-Goals

The first experiment does not:

- replace SDDM or change the normal login flow;
- implement the Hub;
- create a production Environment;
- validate every desktop at once;
- expose the GPU, camera, microphone, raw input, USB, secrets, host D-Bus, or a
  host home directory initially;
- install Odysseus or Codex;
- promise VM-equivalent containment;
- authorize an `apx apply` or privileged helper;
- reuse or modify the manually created `apx-trial` candidate.
- continue when Btrfs quota accounting for the experimental home filesystem is
  visibly disabled; enabling it is a separate host bootstrap decision.

## Approval Boundaries

Each stage needs separate explicit approval after the previous report is
reviewed.

| Stage | Effect | Approval status |
|---|---|---|
| 0. Readiness observation | read-only host evidence | ready to request |
| 1. Repository model and fixtures | repository-only files/tests | authorized by normal development request |
| 2. Disposable root creation | packages/downloads and Btrfs/host mutation | not authorized |
| 3. Headless container boot | starts processes, network, namespaces | not authorized |
| 4. Graphical integration | exposes display/audio/input-related services | not authorized |
| 5. GPU profiles | exposes AMD/NVIDIA devices and libraries | not authorized |
| 6. Failure injection | intentionally interrupts lifecycle operations | not authorized |
| 7. Cleanup | destroys only proven experiment-owned resources | not authorized |

Approval for one stage does not authorize the next. Cleanup is destructive and
requires approval even when it is planned in advance.

## Stage 0: Read-Only Readiness

Stage 0 collects bounded, sanitized evidence without installing packages,
creating files outside the repository, starting containers, or changing
services.

### Required observations

- exact host kernel and architecture;
- installed versions and availability of `systemd-nspawn`, `machinectl`,
  `systemd-dissect`, Btrfs tools, Podman, OCI runtime, and `fuse-overlayfs`;
- whether systemd was built with relevant container features;
- cgroup version and controllers;
- user-namespace availability and applicable sysctl state;
- subordinate UID/GID allocations for fixed APX accounts;
- filesystem and Btrfs context containing the intended experimental storage;
- existing machine/image/container names that collide with the fixed identity;
- current APX account, home, registration, and incomplete-operation conflicts;
- active sessions and display-manager state;
- AMD and NVIDIA PCI/device presence, driver modules, and device nodes;
- NVIDIA container-toolkit/CDI availability and CDI specification state;
- Wayland, PipeWire, portal, notification, and secret-service endpoints visible
  to the current Development Environment;
- free disk and memory as capacity evidence, without declaring a quota policy.

### Observation classifications

Every field is one of:

- `satisfied`: authoritative matching evidence;
- `blocked`: confirmed conflict or missing mandatory prerequisite;
- `requires-host-confirmation`: positive evidence observed only through a
  restricted context;
- `unavailable`: observation could not be obtained;
- `not-applicable`: the selected path does not require the field.

An unavailable observation is never treated as absence. A readiness report is
`ready-for-stage-2-design-review` only when no mandatory field is blocked or
unavailable and restricted positives have authoritative confirmation.

### Command policy

The future observer may execute only fixed argument arrays for allowlisted,
read-only tools. It must not invoke a shell, accept caller-provided paths or
commands, follow untrusted symlinks, emit environment variables wholesale, or
read credentials. Diagnostics are length-bounded and sanitized.

Stage 0 must not use package-manager mutation, `machinectl pull-*`, container
start commands, mount, Btrfs create/delete/snapshot, account management,
systemctl mutation, or writes under `/etc`, `/var/lib/machines`, `/home`, or
`/var/lib/apx`.

## Stage 1: Repository Model

Before host mutation, repository code may model the experiment through typed
data only:

- fixed experiment schema and protocol version;
- identity derivation and conflict observations;
- readiness observation types and precedence;
- immutable intended base and role references;
- declared namespaces, capabilities, devices, binds, network, and limits;
- per-stage approval state;
- expected resources and ownership provenance;
- postconditions and teardown postconditions;
- bounded rollback classifications;
- deterministic rendering and digest;
- fixture-based tests with no host writes.

The model must reject arbitrary commands, host paths, devices, capabilities,
UID/GID mappings, package lists, and runtime flags. Those are selected from a
versioned internal policy, not supplied by a Hub caller.

Stage 1 also includes a pure snapshot-evidence contract. It accepts only a
dated Arch Linux Archive source, the fixed internal seed policy, complete
canonical package evidence, recorded database and package hashes, and verified
package signatures with signer identities. Its output is one of `rejected`,
`verification-incomplete`, or `verified` plus a deterministic evidence digest.
It performs no network access, file extraction, package operation, or host
write. A `verified` evidence classification does not change the Stage 2
approval state.

## Stage 2: Disposable Root Creation

This future stage is deliberately not executable yet. Its design must specify:

1. verified Arch source and exact package manifest;
2. versioned APX base identity;
3. dedicated Btrfs identities for root and home;
4. non-overlapping subordinate UID/GID allocation;
5. root-owned incomplete-operation marker before mutation;
6. atomic registration only after fresh postcondition verification;
7. no skeleton, secrets, SSH keys, machine identity, or Hub state copied from a
   live Environment;
8. exact disk budget and cleanup provenance.

The package manifest begins headless and minimal. A desktop, GPU userspace,
Odysseus, Codex, games, and general-purpose applications are excluded.

The fixed package names, proposed storage identities, initial resource budget,
preconditions, postconditions, and rollback boundary are defined in
[base-and-storage-v1.md](base-and-storage-v1.md).

The complete repository-level review package, including exact intended
resources, effects, gates, failure classes, risks, rollback rules, destructive
operation separation, and remaining blockers, is maintained in
[stage2-approval-dossier.md](stage2-approval-dossier.md). Its deterministic
rendering is available through `apx host stage2-dossier`.

## Stage 3: Headless Boot

The first boot profile is deny-by-default:

- private user, PID, IPC, mount, UTS, and network namespaces;
- no host networking namespace;
- no host home or arbitrary bind;
- no GPU, sound, camera, microphone, raw input, removable storage, or FUSE;
- no host D-Bus or secret service;
- no added capabilities beyond the reviewed minimum;
- no-new-privileges where compatible;
- explicit syscall filter;
- cgroup CPU, memory, process, and IO limits;
- writable paths limited to registered Environment state;
- clean shutdown through container init followed by independent teardown
  verification.

### Headless acceptance tests

- container systemd reaches the declared target;
- host and container machine IDs differ and are stable according to policy;
- container root cannot observe another Environment home;
- container package database differs from the host and another fixture;
- installing a harmless fixture package changes only container-owned state;
- local `sudo pacman` can install and remove a fixture package while the host
  package database checksum, lock, package list, and files remain unchanged;
- a malicious fixture package hook cannot access the host package database,
  host root, Hub, or another Environment;
- process, IPC, mount, and network namespaces differ from the host;
- host-only sockets and services are unreachable unless declared;
- resource exhaustion is contained by the configured limits;
- shutdown leaves no container process, namespace, mount, veth, or user manager;
- restart preserves only declared persistent state;
- snapshot/rollback restores the exact earlier fixture state.

## Stage 4: Graphical Integration

Graphical access is added one capability at a time in this order:

1. isolated Wayland session endpoint;
2. input through a mediated session mechanism, not blanket `/dev/input`;
3. PipeWire audio with Environment-scoped permissions;
4. notifications;
5. file portal without host-home exposure;
6. clipboard policy;
7. secret storage isolated from the host and other Environments;
8. removable storage through explicit user action.

The first compositor should be the smallest viable test compositor, not a full
KDE/GNOME installation. Hyprland, KDE Plasma, and GNOME validation follows only
after the graphical boundary works and has denial tests.

## Stage 5: GPU Profiles

AMD and NVIDIA are separate profiles and may have different backend outcomes.

### Common requirements

- enumerate exact device nodes and userspace libraries;
- confirm user-namespace ownership and access;
- deny unselected GPUs and unrelated device nodes;
- test rendering and compute separately;
- repeat after a host driver update;
- verify teardown and absence of surviving GPU clients;
- record the security loss introduced by device access.

### NVIDIA decision gate

Compare direct `systemd-nspawn` device/library exposure with Podman/OCI CDI.
CDI's standardized, generated device specification is an explicit advantage.
If nspawn requires fragile blanket library binds or cannot survive driver
updates reliably, NVIDIA graphical workloads must use an OCI/hybrid backend or
remain unsupported until a safe mechanism exists.

## Stage 6: Failure Injection

Failures are injected only into disposable experiment-owned resources:

- interruption after incomplete marker;
- interruption after root creation;
- interruption after account or identity creation;
- container boot timeout;
- graphical service failure;
- network setup failure;
- shutdown timeout with processes remaining;
- registration staging and publication failures;
- base update failure;
- snapshot and restore failure;
- cleanup refusal after external modification.

Every failure must classify remaining resources without guessing. Automatic
rollback deletes only resources proven created by this operation, still unused,
unmodified, unpublished, and safe to remove. Otherwise it preserves them and
reports manual recovery evidence.

## Stage 7: Cleanup

Cleanup is accepted only when:

- the exact experiment identity and operation provenance match;
- the Environment is stopped;
- no processes, sessions, mounts, namespaces, veths, or device clients remain;
- no resource has unknown ownership or external modification;
- data-loss scope is rendered before approval;
- post-cleanup absence is freshly verified;
- shared base content is retained unless separately proven experiment-owned and
  separately approved for deletion.

Broad recursive deletion and pathname-only ownership are forbidden.

## Evidence Record

Each executed stage should produce a deterministic report containing:

- experiment and schema version;
- policy version and fixed identity;
- stage and approval reference without secret material;
- each observation, classification, and sanitized evidence summary;
- created resource identities and provenance;
- postcondition and teardown results;
- unresolved or non-authoritative evidence;
- rollback eligibility and retained resources;
- overall result: `passed`, `failed`, `requires-confirmation`, or `incomplete`.

Timestamps may exist in an execution journal but must not alter the plan digest.
Raw logs remain separate and bounded; secrets and unrelated host data are never
embedded in the report.

## Immediate Testable Deliverable

The Stage 0 readiness observer and fixed Stage 2 plan are implemented. The next
permitted work is to produce and independently validate a complete repository
artifact conforming to the snapshot-evidence contract, using a separately
reviewed acquisition procedure. Repository fixtures may exercise validation
now; fetching packages or signatures remains a host/network effect requiring a
separate bounded approval.

The fixed `apx host snapshot-readiness` observer may collect read-only
keyring/tool identity evidence before acquisition review. It accepts no caller
paths, packages, or commands and does not mutate trust state.

Implementing or running Stages 2 through 7 requires new explicit approval and
may require changes to the repository's current phase rules.
