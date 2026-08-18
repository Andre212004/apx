# NVIDIA control-node Hub boot repair v1 — 2026-08-15

## Incident

After the 2026-08-15 boot, `apx-official-hub-autostart-v1.service` failed three
times with `No such file or directory: '/dev/nvidiactl'` and then reached its
start limit. Environment creation was consequently unavailable because only
the authenticated active Hub may request it.

The NVIDIA 610.43.03 open kernel module was loaded and bound to the expected
RTX 3060. `/dev/nvidia0`, `/dev/nvidia-modeset`, both NVIDIA DRM nodes and the
UVM nodes existed. The kernel advertised `195 nvidiactl` in `/proc/devices`,
but repeated `/usr/bin/nvidia-modprobe -c 0` calls returned zero without
creating `/dev/nvidiactl`.

## Repair

`resolve_nvidia_auxiliary_devices()` still invokes the trusted root-owned
`nvidia-modprobe` helper first. If only `/dev/nvidiactl` is absent, the launcher
now requires exactly one kernel registration whose name and major are
`nvidiactl` and `195`. It then creates only character device 195:255 with mode
0666. The existing validation subsequently checks all three NVIDIA auxiliary
nodes and refuses any type or device-number mismatch.

This is not a wildcard `/dev` grant and does not weaken the closed device
lease. Missing, duplicated or different kernel registration evidence blocks
the launch without creating a node.

## Physical result and rollback

The installed launcher matches the repository source. The repair created the
expected 195:255 node, passed the exact AMD+NVIDIA lease construction, started
the Hub container, Hyprland and QuickShell, and produced an authenticated
`identity.get` response. Two unlocked sessions then received a clean
compositor exit shortly after QuickShell loaded; no launcher error or failed
Host unit accompanied the exit. The configured `SUPER+M` binding is a direct
compositor exit, so sustained proof must be repeated without that key.

The complete repository suite passes 1034 tests with 11 expected skips.

The current physical checkpoint is a fresh Hub launch waiting at its normal
password surface on tty2. The credential was neither requested nor bypassed.
An authenticated catalogue and management-status read after that local unlock
remain the final creation-path proof.

The exact pre-change launcher and its digest are stored under
`/var/lib/apx/backups/20260815-nvidia-control-hub-repair-v1/`. Rollback requires
returning to tty1, stopping the Hub through its normal recovery path, restoring
that one launcher, and removing `/dev/nvidiactl` only after proving no NVIDIA
or APX process has it open. The old launcher will reproduce the boot refusal
on this kernel state, so rollback is diagnostic rather than service-restoring.
