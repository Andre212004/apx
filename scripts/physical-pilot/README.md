# APX Physical Headless Pilot

These scripts are target-bound to the owner's Lenovo 82JU and Samsung NVMe
serial `S4DYNX0R253702`. They are experimental development adapters, not a
general installer.

Do not run either file independently from memory or adapt away its identity
guards. Follow `docs/physical-headless-development-handoff-v1.md` from a second
device with the complete output reviewed after every phase.

`install-arch-headless-pilot.sh` is intentionally destructive. It may run only
from official Arch installation media booted physically in UEFI mode and only
after its fixed disk path, byte size, model, serial, and mount checks pass.

`bootstrap-apx-headless-pilot.sh` may run only after the new physical foundation
boots with its marker, fixed hostname, matching Lenovo DMI identity, and Btrfs
APX state. It installs the VM-proven experimental runtime; it does not close
the production trust, authentication, or service-hardening gates.
