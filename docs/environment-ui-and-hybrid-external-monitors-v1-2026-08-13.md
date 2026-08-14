# Environment UI clarity and hybrid external monitors v1 — 2026-08-13

## Result

The common Environment QuickShell now makes creation profiles and capability
choices explicit without keeping the form visually dense. The three starting
profiles say what they are for and name their principal additions. Capability
drawers show only their numbered title. Each individual capability normally
shows only its title and selection state; a right click expands its short
purpose and the exact relevant package/program list. Base capabilities are
marked `BASE`, while packages actually added during creation are marked
`INSTALA`.

The common Control Centre no longer clips its workload footer. Its normal
workload height is 350 logical pixels and the four Environment actions use a
two-column grid: Apps, Lock, Files, and Return to Hub. Workloads retain the same
Wi-Fi, Bluetooth, output/input audio, display brightness and keyboard-light
controls as Hub. The two privileged Hub-only rows remain absent: the persistent
Host terminal and APX exit to Host.

Hub, Work and Jogos received the same source-matched shell. The immutable seed
for future Environments and the installed creation runtime were updated too.
The active Hub QuickShell restarted successfully without restarting Hyprland or
the persistent Host terminal. Exact pre-change copies are under
`/var/lib/apx/backups/20260813-environment-ui-clarity-v1/`.

## HDMI root cause and repair

The exact Legion exposes these physical connector routes in hybrid mode:

- AMD `0000:05:00.0`, current `card2`: connected internal `eDP-2`.
- NVIDIA `0000:01:00.0`, current `card1`: HDMI-A-1, DP-1, DP-2 and the
  discrete-mode eDP-1 connector.

APX previously leased the AMD card and render nodes to Hyprland and only the
NVIDIA render node for application offload. HDMI and DisplayPort therefore did
not exist in the Environment's DRM catalogue, even though the wildcard
Hyprland monitor rule was already correct.

In hybrid mode the launcher now resolves, validates, leases and binds both the
NVIDIA card and render nodes in addition to AMD. The session constructs
`AQ_DRM_DEVICES` as AMD first and NVIDIA second. AMD remains the primary
renderer for normal battery-friendly desktop work; NVIDIA supplies the
connectors physically wired to external displays. The Host seat broker receives
both card nodes, and the same path is used by Hub and normal graphical
Environments. Discrete NVIDIA mode remains a one-card path.

The installed launchers match source, but the running Hub was deliberately not
restarted merely for proof. The new device catalogue takes effect on the next
normal graphical Hub/Environment launch. A real HDMI hot-plug with a monitor
attached remains the required physical acceptance test; without a connected
external display only connector ownership, not scanout, can be proven.

## Verification

- The complete repository suite passes 1030 tests with 11 expected skips.
- Focused shell, Environment management, official Hub and common graphical
  launcher tests pass.
- The active Hub accepted and kept the revised QuickShell running.
- Source, Hub, Work, Jogos and the future-Environment shell seed share one
  digest.
- Source and installed runtime/launchers share their respective digests.
- No failed Host units were present after the live shell reload.

## Rollback

Restore the corresponding files from
`/var/lib/apx/backups/20260813-environment-ui-clarity-v1/`, preserving recorded
ownership and modes. Restarting only QuickShell is sufficient for a shell-only
rollback. Launcher/session rollback takes effect at the next graphical launch;
do not interrupt an active Environment solely to apply it.
