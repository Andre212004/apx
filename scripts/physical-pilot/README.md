# APX Physical Headless Pilot

These scripts are target-bound to the owner's Lenovo 82JU and Samsung NVMe
serial `S4DYNX0R253702`. They are experimental development adapters, not a
general installer.

Do not run either file independently from memory or adapt away its identity
guards. Follow `docs/physical-headless-development-handoff-v1.md` from a second
device with the complete output reviewed after every phase.

For an already installed pilot, use
`docs/physical-pilot-state-and-cleanup-audit-v1.md` to inventory the host, Hub,
and Development before proposing any cleanup. The audit is read-only; it does
not make unknown files or packages safe to remove.

`install-arch-headless-pilot.sh` is intentionally destructive. It may run only
from official Arch installation media booted physically in UEFI mode and only
after its fixed disk path, byte size, model, serial, and mount checks pass.

`bootstrap-apx-headless-pilot.sh` may run only after the new physical foundation
boots with its marker, fixed hostname, matching Lenovo DMI identity, and Btrfs
APX state. It installs the VM-proven experimental runtime; it does not close
the production trust, authentication, or service-hardening gates.

`recover-development-quota-v1.sh` is the one-time, owner-run recovery for an
existing physical pilot whose Development Environment still has the original
4 GiB root and 2 GiB home limits. It refuses any other machine, profile, role,
runtime state, subvolume layout, quota mode, or starting limits. After exact
approval it raises those two limits in place and installs the matching
role-aware runtime. It does not recreate, snapshot, copy, or delete Development
content. Follow the recovery section in the physical handoff; do not adapt the
script to a different Environment.
