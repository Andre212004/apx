# APX Architecture

APX is an orchestration platform on one Arch Linux installation. It presents
independent named Environments while keeping the Host, Hub and workload state
separate. This document is the concise architecture map. The original detailed
foundation is preserved at
`history/architecture-foundation-through-2026-09-01.md`; current operational
state is in `../PROJECT_STATE.md` and `../CURRENT_HANDOFF.md`.

## Layers

### Host

The Host owns the kernel, boot/recovery path, hardware drivers, physical device
control, machine-wide networking capability, storage admission and the smallest
privileged APX executors. It does not provide an arbitrary root command service
to the Hub or workloads.

### Versioned APX base and role seed

Reviewed, digest-pinned artifacts supply common runtime and presentation
defaults. Role-specific content distinguishes Hub, normal graphical, development
and System Environments. A seed is immutable input to provisioning; the live Hub
is never used as a template.

### Environment

An Environment has a logical name, immutable generation identifier,
registration, Btrfs-backed root/home state, local application/configuration
state, resource policy and supervised runtime. Normal graphical Environments
use systemd-nspawn and an independent copy of the Environment shell seed.
System Environments may use a separately admitted VM profile/runtime when their
workload requires KVM/VFIO boundaries.

### Hub

The Hub is a reproducible Environment and the authoritative management client.
It may request typed lifecycle operations but is not itself the privileged
executor. Workloads can request only a return/stop of their own active
generation and otherwise receive read-only APX information.

## Core invariants

- One logical name maps to one trusted internal identity and current generation.
- Plans and effects bind the exact generation; stale plans fail before mutation.
- Applications, package databases, documents, configuration, processes and
  mutable services are local to an Environment.
- Environment package managers cannot mutate Host or sibling package state.
- Only one normal graphical Environment owns the interactive session at a time.
- Device grants are explicit, role/capability-bound and revoked during handoff.
- Host reserve and quota rules prevent one Environment consuming recovery space.
- Creation, switch, snapshot, archive, restore and destroy preserve explicit
  preconditions, effect journals, terminal states and recovery behavior.
- Unknown or unverifiable state means refusal, never inferred permission.
- Linux account/filesystem separation is not described as VM-equivalent
  containment.

## Management path

```text
QuickShell or apx CLI
        -> typed local intent
        -> authenticated Hub/workload client
        -> Host executor validates identity, generation and state
        -> bounded effect adapter
        -> journalled result and recovery state
```

UI labels, shell text and caller-supplied paths are not authority. The executor
derives targets from trusted registration and active-session evidence.

## Graphical and shared services

Hyprland is the default compositor, not a lifecycle dependency. The shared seed
contains QuickShell, Mako, Hyprland configuration, wallpapers and small local
helpers. Wi-Fi, Bluetooth, audio, brightness, battery and power UI use bounded
Host services so hardware ownership and secrets do not need to be copied into
every Environment. Each Environment receives its own mutable configuration
copy; changing it must not alter siblings or the seed.

## Storage and isolation

Btrfs subvolumes, registrations and operation plans define lifecycle ownership.
Snapshots, archives and backups are distinct objects and must be enumerated in
destructive plans. Capacity is flexible within a protected global Host reserve.

Normal Environments combine independent filesystem/package state, identities,
namespaces, cgroups and explicit device/service policy. These mechanisms reduce
coupling and exposure but share the Host kernel. A higher-security profile and
its threat model remain separate work; System VM v2 is an experimental path for
workloads that need virtual hardware or GPU passthrough.

## Detailed contracts

- `isolation-architecture.md` and `threat-model.md`
- `environment-local-administration-v1.md`
- `human-identity-and-session-handoff-v1.md`
- `hyprland-default-environment-architecture-v1.md`
- `host-shared-services-v3-architecture-and-result-2026-08-02.md`
- `coordinated-updates-and-active-audio-architecture-v1.md`
- `system-vm-v2-architecture-2026-08-24.md`
- `physical-pilot-update-contract-v1.md`

Those documents carry domain detail and dated evidence. When a historical
statement conflicts with the current root state documents, resolve the conflict
explicitly rather than selecting the more convenient claim.

## Open architecture work

- production threat model and guarantees for a high-security Environment;
- durable human authentication/unlock and future multi-person ownership;
- supported non-Hyprland desktop adapters without lifecycle coupling;
- long-term APX base/update provenance and recovery retirement criteria;
- module boundaries for the large runtime, isolation and QuickShell controllers.
