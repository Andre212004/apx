# APX Disposable Virtual Lab

These files are the guarded implementation used for the 2026-07-13 functional
headless C0–C6 proof. They are not a physical-computer installer and are not a
production APX package.

## Files

- `install-arch-c1-foundation.sh` performs the one destructive clean install
  inside the reviewed Arch ISO guest;
- `bootstrap-apx-headless-runtime.sh` installs the experimental host runtime and
  builds immutable Hub, Development, and Minimal releases;
- `apx-lab-runtime.py` owns the experimental lifecycle and Btrfs effects;
- `apx-lab-executor.py` exposes fixed typed operations to the active Hub only;
- `apx-lab-client.py` is the unprivileged CLI placed in the Hub.

## Safety Boundary

The C1 installer refuses unless all of these fixed facts match:

- exact disposable-disk approval text;
- QEMU/KVM virtualization;
- the Arch ISO's `archiso` hostname;
- Q35 virtual-machine identity;
- `/dev/vda` as a block device of exactly 64 GiB;
- `/dev/vda` not mounted.

The runtime bootstrap separately requires KVM, guest hostname `apx-virtual`, and
`/var/lib/apx` on Btrfs. These checks are defense in depth, not permission to
try the scripts on a physical installation. The guest must expose only a new
qcow2 disk and must not expose a host or physical block device.

## Result

The exact identities, successful gates, corrected failures, retained
checkpoints, and remaining production blockers are in
`docs/virtual-headless-c0-c6-result-2026-07-13.md`.
