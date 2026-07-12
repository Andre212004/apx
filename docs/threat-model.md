# APX Environment Threat Model

Status: initial product threat model; validation pending.

## Assets

- data, applications, configuration, secrets, and assistant memory belonging to
  each Environment;
- Hub lifecycle authority and APX metadata;
- host integrity, kernel, boot chain, hardware, and package/runtime state;
- base images, templates, snapshots, archives, and backups;
- human credentials and future multi-person ownership boundaries;
- GPU, audio, input, camera, microphone, removable storage, and network access.

## Trust Boundaries

```text
Human -> Hub UI -> typed APX executor -> host lifecycle primitives
                    |                     |
                    v                     v
              verified policy       Environment boundary
                                          |
                            applications, data, assistants
```

The Hub UI is not trusted to validate privileged operations by itself. The
executor independently validates a closed typed request, current authoritative
state, policy, provenance, and postconditions. Templates and downloaded base
artifacts are untrusted until verified and admitted by policy.

## Expected Adversaries and Failures

- an ordinary application accidentally reading or damaging another
  Environment;
- malicious or compromised software inside an Environment;
- untrusted code consuming CPU, memory, processes, disk, or network;
- a template attempting to request excessive devices, mounts, or capabilities;
- a local assistant exceeding its configured Environment access;
- stale, malicious, or compromised base/template content;
- confused-deputy requests sent from the Hub to a privileged executor;
- symlink, path traversal, race, identity reuse, or stale-plan attacks;
- incomplete creation, shutdown, snapshot, archive, restore, or deletion;
- accidental propagation of Hub credentials or authority;
- a future second human accessing another person's Environments.

## Normal-Profile Security Objectives

- deny cross-Environment files, processes, IPC, package state, and secrets;
- prevent Environment root from becoming host root through ordinary container
  privileges;
- expose only declared host devices and services;
- mediate network identity and inbound exposure;
- enforce storage and compute limits sufficient to protect host availability;
- terminate and verify Environment processes and mounts at lifecycle end;
- make every destructive action explicit, provenance-bound, and recoverable
  where promised.

## High-Security-Profile Objectives

In addition to normal objectives:

- default-deny devices, host binds, portals, secrets, and outbound network;
- minimize syscalls and capabilities;
- prevent access to GPU and raw input unless a separate reviewed profile grants
  them;
- cap CPU, memory, process count, disk use, and execution time;
- exclude personal-assistant memory and credentials;
- provide a clear warning that the host kernel remains shared.

## Out of Scope for Shared-Kernel Guarantees

A container cannot honestly promise VM-equivalent containment against every
kernel vulnerability, hostile driver interaction, firmware compromise, physical
access, boot-chain compromise, or hardware side channel. Workloads requiring
that guarantee need a separately designed VM profile or different machine.

## Mandatory Security Invariants

- No arbitrary privileged shell or command channel.
- No caller-selected host path, UID, GID, device, capability, or executable.
- No live Hub cloning.
- No implicit cross-Environment bind mounts or shared writable roots.
- No registration publication before complete fresh verification.
- No deletion based only on a pathname or naming convention.
- No environment launch from an unverified base/template reference.
- No assistant cross-Environment access without future explicit policy and
  consent.
- No use of unavailable evidence as proof of safety.
- No high-security label without passing its denial and escape test suite.
- No Environment `sudo`, package manager, Flatpak operation, language package
  manager, vendor installer, hook, install script, or lock may reach or mutate
  the host, base, Hub, or another Environment.

## Required Validation Families

- filesystem traversal, symlink, mount, and shared-storage denial;
- UID/GID mapping and user-namespace isolation;
- process, IPC, D-Bus, socket, and service discovery denial;
- capability, seccomp, device, and namespace inspection;
- network ingress, egress, DNS, and host-service reachability;
- cgroup exhaustion and disk quota behavior;
- malicious template and malformed metadata handling;
- stale plan, race, identity reuse, and interrupted-operation recovery;
- GPU, audio, portal, secrets, clipboard, input, and removable-device leakage;
- Odysseus and Codex data/tool permission boundaries;
- Hub authority non-propagation and multi-person separation.
- malicious package, install-script, package-hook, and local-root attempts to
  reach the host package database or host administration.

Severity and acceptance thresholds will be added when the experimental backend
and exact policy vocabulary are defined.
