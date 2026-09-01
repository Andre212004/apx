# General graphical handoff and Host controls — 2026-08-03

The proven physical launcher is now reusable for admitted `graphical-base`
Environments without merging their homes or package sets. The Hub retains
Quickshell and Kitty; the certified `test` Environment retained Waybar and
Alacritty. Both physical proofs reached Hyprland on `eDP-2`, exact input,
ALC287 playback/capture, Wi-Fi and Bluetooth, then returned to tty1 with no
machine or lease residue. Long logical names use a short generation-bound
machine/veth identity to avoid Linux interface truncation collisions.

Shared Host-service, audio and update sockets now start `root:root 0600`. The
active launcher alone leases them as `0660` to the translated Environment user
and revokes them on exit. Wi-Fi/Bluetooth and audio accept the authenticated
active graphical Environment. Coordinated updates and physical power remain
Hub-only. Audio volume/mute survived the Hub/test handoff and the state records
the active Environment while a session exists.

Creation planning records `follow-host` by default and accepts the explicit
`--exclude-host-updates` selection through the lab client/executor protocol.
The live graphical Hub still has no completed production creation screen, so
this is a real backend/default but not a claim that a new graphical checkbox
screen exists. The update preview was `ready-for-approval`, with no exclusions
and Host plus eight Environments; `pacman -Qu` reported no Host package delta.
No mass update was applied because the owner paused new recovery work and there
was no useful package transaction to certify.

The live Hub adds BLOQUEAR and SUSPENDER. Lock runs unprivileged `hyprlock` in
the Hub. Suspend uses the Host two-step token, sleep inhibitors and update lock;
it locks first and calls logind without closing the Environment, preserving its
audio/session state. Hibernation is intentionally absent until swap/resume is
proven. Workload lock UI/packages remain Environment-local rather than being
silently copied from the Hub.

No new recovery mechanism or forced rollback exercise was added. The general
foreground launcher retains guaranteed cleanup in `finally`, but an independent
health watchdog for non-Hub interactive sessions remains deferred with the
owner's recovery pause. Repository validation passes 939 tests with 11 skips.
