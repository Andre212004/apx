# Quickshell ASCII v1 and temporary Hub Codex result — 2026-08-01

## Result

The mutable official Hub now starts a first Quickshell desktop shell instead
of Waybar. It keeps the existing ASCII language, uses cyan accents and slightly
rounded surfaces, and opens compact anchored popovers below the Wi-Fi,
Bluetooth, audio and battery controls. Popovers dismiss on outside click and
their content can scroll. The old Waybar profile remains installed and the
small `apx-shell-v1` runner starts it automatically if Quickshell exits.

This is deliberately a Hub-only visual trial. It has not replaced the
versioned `waybar-ascii-v1` common seed and has not mutated the immutable
`hyprland-base-v1` release. Once the owner accepts or adjusts the design, a new
Quickshell package/config release and normal-Environment profile can be
designed independently rather than cloning the live Hub.

The popovers call only the existing typed Host-services v2 client for Wi-Fi
and Bluetooth. Audio remains Environment-local through `wpctl`. Battery and
GPU state are informational: HYBRID remains the proven profile (AMD display,
NVIDIA render on demand). AMD-primary and NVIDIA-primary session profiles are
not presented as working buttons because their admission/restart backend does
not yet exist.

## Temporary Codex exception

At the owner's explicit request, the live Hub alone has Node.js, npm and
`@openai/codex` installed. Codex is under `/home/apx/.local`, is on the apx
login PATH, and reports `codex-cli 0.146.0`. No Host/root Codex credentials or
configuration were copied. The Hub user must authenticate separately with
`codex login`. This temporary development tooling is not part of
`desktop-essential-v1`, a graphical template, or an immutable release.

The three generated design preview copies were removed from
`~/Imagens/APX-design`. Their generation originals remain in the Host Codex
image cache, so the removed Hub copies can be recreated if needed.

## Package-manager correction

Installing Quickshell exposed a stale Host-owned pacman-local entry for the old
`vulkan-tools 1.4.350.1-1` beside the newly installed `1.4.357.0-1` entry. The
exact stale directory was removed after inspecting both records. `pacman -Dk`
then reported no database errors and the current package is
`vulkan-tools 1.4.357.0-1`.

## Physical evidence

The corrected exact-generation launcher required one active Quickshell
process. Its bounded physical `--test` result was `classification=verified`
with Quickshell, Hyprland, Kitty, two Portuguese-configured keyboards, local
playback audio, iwd Host networking, synchronized Host time, BlueZ power
round-trip, typed context-menu backend and RTX 3060 NVK render all verified.
Recovery restored tty1 and left no machine residue.
