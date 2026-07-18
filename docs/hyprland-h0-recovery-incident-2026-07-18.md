# Hyprland H0 recovery incident — 2026-07-18

## Outcome

The physical H0 v10 session was manually interrupted by a Host power-off after
approximately 25 seconds because the owner could not return visibly from
Hyprland. No v10 result was produced. After reboot, no H0 machine or transient
graphical unit remained active.

Physical H0 execution is now code-locked. No further physical graphical run is
allowed until a shorter recovery design has passed review and a non-graphical
rehearsal.

## What the previous run proved

H0 v9 completed its bounded 45-second observation and restored tty1. Direct
Hyprland IPC evidence reported the internal `eDP-2` panel enabled, focused and
DPMS-on at 1920x1080 and 120.213 Hz. The Wayland socket existed. The application
marker was not observed, so v9 remained incomplete rather than a full visual
acceptance pass.

## Incident timing and cause

The previous-boot journal records v10 starting at monotonic time 11123.936 and
the Host beginning to stop its graphical unit at 11148.842, about 25 seconds
later. The independent expiry timer had been configured for 120 seconds, while
the controller's normal observation window was 45 seconds.

The evidence does not show an expiry-watchdog failure before power-off. It shows
that the emergency deadline was too long for a physical test that can leave the
owner without an obvious exit path. That is a safety-design failure regardless
of whether the 120-second watchdog would eventually have recovered tty1.

## Required redesign gate

Before re-enabling physical H0, all of the following are required:

1. an independent Host-owned graphical lease no longer than 15 seconds;
2. recovery driven by that lease, not by the interactive controller process;
3. a clearly tested local emergency key path and a second Host-side escape path;
4. a pure and then non-graphical rehearsal proving tty1 restoration;
5. explicit evidence that the expiry timer cannot be cancelled before tty1 and
   zero residue are confirmed;
6. a fresh review of the exact plan digest before any GPU/VT activation.

The v10 application-dispatch experiment is abandoned and must not be adopted as
a successful result.
