# Environment Isolation Architecture

Status: provisional architecture direction; implementation is not authorized.

This document translates the APX product contract into isolation requirements,
compares viable mechanisms, and selects the smallest direction worth validating
experimentally. It does not claim that the design works on the current host.

## Required Outcomes

An acceptable architecture must demonstrate all of the following:

1. Two Environments can install the same package independently.
2. An application installed in one Environment is absent from the other.
3. Package upgrades inside one Environment do not mutate the host or another
   Environment.
4. Deleting an Environment removes its root filesystem, local applications,
   home, configuration, and runtime state without deleting shared base content.
5. Hyprland, KDE Plasma, and GNOME can be evaluated without changing APX
   lifecycle semantics.
6. GPU, audio, input, display, portals, notifications, removable devices, and
   networking are granted explicitly rather than inherited accidentally.
7. Internal Linux accounts and container identities remain hidden behind the
   APX human-facing identity.
8. A stopped Environment has no surviving processes, user services, mutable
   mounts, or local assistant.
9. Templates and base updates are reproducible, versioned, and reversible.
10. APX reports precise isolation guarantees and never calls a shared-kernel
    container equivalent to a VM against kernel exploits.

## Layer Model

```text
Physical Arch host
├── kernel, drivers, firmware, devices, network uplink
├── minimal APX lifecycle executor
└── versioned APX base root filesystem
    ├── Hub role image
    ├── workload role/template image
    └── Environment writable state
        ├── root filesystem changes and installed packages
        ├── home and documents
        ├── configuration and secrets
        └── runtime state
```

The diagram describes ownership, not a final directory layout. Base and role
content should be immutable or content-addressed. An Environment's mutable
state must have an explicit storage identity and deletion provenance.

## Compared Mechanisms

| Mechanism | Complete Arch userspace | Independent packages | Lifecycle fit | Isolation controls | Desktop/GPU fit | APX assessment |
|---|---:|---:|---:|---:|---:|---|
| Linux user plus home only | no | no | good | weak | native | rejected as final architecture |
| Extracted user-local applications | no | partial | weak | weak | application-specific | experiment only |
| Package overlay without container boundary | partial | yes | complex | weak | native | rejected as primary boundary |
| Podman/OCI container | possible | yes | application-oriented | strong configurable primitives | CDI is attractive; full desktop needs proof | retained alternative/runtime |
| `systemd-nspawn` system container | yes | yes | machine and systemd-oriented | namespaces, capabilities, syscall, network and filesystem policy | direct device/bind model; must be proven | provisional primary candidate |
| Hardware VM | yes | yes | heavier and duplicates kernel | strongest candidate boundary | GPU sharing/passthrough is complex | optional future maximum-security profile |

The Linux-user-only design cannot meet independent package requirements.
Extracted applications do not provide a coherent package lifecycle. A plain
overlay can separate files but does not create the required process, network,
IPC, device, or privilege boundary.

Podman provides rootless user namespaces, image storage, seccomp integration,
cgroup/systemd integration through Quadlet, and standardized device injection.
It remains attractive for application services and possibly an Environment
backend. Its normal abstraction is an OCI workload rather than a bootable
personal system, so full login session and desktop behavior must be proven
before it could replace a system-container backend.

`systemd-nspawn` directly models a bootable system tree and integrates with
machine and systemd lifecycle. Its documented settings include private users,
private networks, capability reduction, syscall filters, read-only roots,
overlays, inaccessible paths, and bounded bind mounts. This matches APX's
complete-Environment model most directly, but does not automatically make the
container safe: every device and privileged bind expands the attack surface.

## Provisional Direction

The first architecture experiment should evaluate one bootable Arch system
container per Environment using `systemd-nspawn`, with:

- a versioned read-only APX base or reproducible base snapshot;
- a dedicated Btrfs root/state identity per Environment;
- a separate dedicated home subvolume or clearly identified home snapshot;
- systemd as container init;
- user namespace enabled with non-overlapping subordinate IDs;
- a private network namespace with host-mediated connectivity;
- a private IPC and process namespace;
- a reduced capability set and `NoNewPrivileges` where compatible;
- an explicit syscall policy;
- no arbitrary host path binds;
- individually declared devices;
- cgroup accounting and resource limits;
- fresh shutdown verification before snapshot, archive, or deletion.

The host owns the kernel drivers. An Environment receives only the userspace
libraries and device access required by its policy. NVIDIA must be evaluated
against exact host-driver/userspace compatibility. OCI CDI is a standardized
and currently well-supported NVIDIA device mechanism, which is an advantage for
Podman and a reason not to close the backend decision before GPU experiments.
AMD `/dev/dri` access also needs explicit group, user-namespace, and library
validation rather than a blanket device bind.

## Isolation Profiles

The repository now encodes two fixed, non-mutating policy contracts in
`src/apx_policy.py`: `normal-desktop` and `high-security-headless`. The pure
model rejects changes that add writable host binds, privileged runtime mode,
host UID zero mapping, direct devices, lingering, missing namespaces, incomplete
teardown, or a VM-equivalent claim. This tests the intended rules only; it does
not enforce them on the host or prove a backend can satisfy them.

### Normal

Intended for trusted personal workloads such as university, work, and games.
It may grant display, audio, input, GPU, network, portals, and selected removable
storage. It still isolates filesystems, packages, processes, IPC, and network
identity by default.

### High Security

Intended for untrusted code and risky experiments. The initial target denies
GPU, raw input, host IPC, host networking, removable devices, secrets, and host
filesystem binds unless individually justified. It applies tighter resource,
capability, syscall, and outbound-network policies.

This profile remains shared-kernel containment. If the threat model includes a
credible hostile kernel exploit, APX must require a hardware VM or another
stronger boundary rather than silently weakening the claim.

## Base and Template Rules

- The live Hub is never a template.
- Base artifacts are versioned, immutable, verified, and reproducible.
- Role templates declare additions and policy; they do not carry mutable user
  state or secrets.
- Environment creation records exact base and role versions.
- Updating the base creates a new version; it does not mutate an active
  Environment invisibly.
- Rollback retains the prior verified base reference until validation succeeds.
- Wi-Fi connectivity may be mediated by the host; credentials are not copied by
  default.
- Fonts and certificates require provenance and update policy even when common.

## Rejected Shortcuts

- cloning the live Hub;
- sharing `/usr` read-write between Environments;
- exposing the host package database inside an Environment;
- mounting an entire host home, `/dev`, `/run`, or D-Bus namespace;
- using `--privileged` or an equivalent broad capability grant;
- claiming high security merely because a different Linux UID is used;
- allowing an Environment template to request arbitrary binds, devices,
  commands, or privileged options.

## Validation Gates

The provisional direction is not accepted until non-destructive experiments
provide evidence for:

- independent package installation and deletion;
- boot, clean shutdown, and forced-failure recovery;
- Btrfs snapshot identity and rollback;
- Wayland login/session behavior;
- Hyprland, KDE Plasma, and GNOME feasibility;
- AMD and NVIDIA rendering, compute, and driver update behavior;
- PipeWire audio, portals, notifications, secrets, and input;
- network separation and host-mediated Wi-Fi;
- no cross-Environment filesystem, process, IPC, or package visibility;
- normal-profile usability and high-security-profile denials;
- complete process, mount, device, and assistant teardown.

Failure of the system-container approach should cause a documented comparison
against Podman/OCI or a hybrid backend, not ad hoc privilege expansion.

The staged validation protocol, fixed experimental identity, approvals,
evidence format, and cleanup gates are specified in
[system-container-experiment.md](system-container-experiment.md).

## Primary Technical References

- [systemd-nspawn settings](https://www.freedesktop.org/software/systemd/man/systemd.nspawn.html)
- [Podman run security, user namespace, device, and systemd options](https://docs.podman.io/en/latest/markdown/podman-run.1.html)
- [Podman Quadlet integration](https://docs.podman.io/en/latest/markdown/podman-systemd.unit.5.html)
- [NVIDIA Container Toolkit CDI support](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/cdi-support.html)
- [Btrfs send and receive](https://btrfs.readthedocs.io/en/stable/Send-receive.html)
