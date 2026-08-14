# Host and Hub usability investigation — 2026-08-11

## Scope

This physical-pilot pass investigated the Host console, Environment-local
administration, the automatic Hub terminal, Bluetooth discovery and connection
support, and the perceived softness/latency of the Hub control centre. It did
not begin the future Environment-creation UI work.

## Host console

The console daemon created a normal interactive Bash PTY but set
`TERM=xterm-kitty`. The minimal Host has `/usr/bin/clear` and an
`xterm-256color` terminfo entry, but `infocmp xterm-kitty` returned no match.
That mismatch, rather than a non-Linux console, caused `clear` and could also
break other terminfo-driven applications.

The fixed console advertises `xterm-256color`. Kitty remains the graphical
frontend. The current console process retains its original environment, so a
new console must be opened after the daemon restart to observe the fix.

## Environment-local sudo and Brave

The running `apx-hub` proves all intended local-admin facts:

- `sudo 1.9.17.p2-6` is installed;
- `apx` belongs to groups `apx` and `wheel`;
- `/etc/sudoers.d/10-apx-local-admin` is root-owned mode `0440`;
- its policy retains `%wheel ALL=(ALL:ALL) ALL` and grants the same authority
  directly to the intended local administrator `apx`;
- the `apx` account has a password.

Sudo therefore requires the Hub/APX user password by design and grants root
inside only that Environment. The private user namespace maps that root to a
non-root Host identity, while Host service authorization continues to reject
Environment root. No password reset or passwordless policy was introduced.
A temporary one-command proof made `sudo -n /usr/bin/id -u` return Environment
UID `0`; its exact sudoers drop-in was then removed and absence rechecked.

The later owner report `apx is not in the sudoers file` exposed a real
launcher bug that account-database inspection alone had missed. Hyprland and
the open Kitty processes inherited an explicit supplementary-group list that
did not include `wheel`; a fresh login did. The graphical launch list now adds
the exact wheel GID. Naming `apx` directly in the password-required policy also
fixes the open session without a restart and makes enrollment independent of
group refresh timing.
An exact reproduction with the stale group list now returns only `a password
is required`, proving that sudo recognizes the user while still requiring the
local password.

`pacman -Ss '^brave'` also confirms there is no official Arch package named
`brave`. Brave is normally obtained from a non-official route such as the AUR;
that packaging question is separate from sudo authority and should be handled
inside the chosen Environment.

The existing desktop also started Hyprland from `/`, which made Kitty inherit a
root-owned working directory and caused `git clone` to fail there for an
ordinary user. The graphical session now changes to `/home/apx` before starting
the compositor. The live Super+Q binding explicitly uses Kitty's
`--directory /home/apx`, while already-open shells require one manual `cd ~`.
The Hub already contains `git`, `base-devel`, and `makepkg`, so the manual AUR
workflow itself is available; only an integrated helper/store remains absent.

## Automatic terminal

The launcher called `open_and_verify_kitty()` after every successful launch.
That was legacy certification behavior, not a desktop requirement. It now runs
only in `--test`; normal interactive startup leaves the desktop clean. The
already-open window was not killed because it can contain owner work.

## Bluetooth

The authenticated v3 client started a bounded eight-second BlueZ scan. During
the scan, both `bluetoothctl show` and D-Bus reported discovery active. The
completed result reported twelve nearby devices and discovery returned to off.
This proves that the button's backend performs a real radio scan.

The same closed service exposes pair, pair-response, pair-status,
connect/disconnect and remove operations. No arbitrary nearby device was paired
or connected during this pass: that requires an owner-selected peripheral and,
depending on the device, a PIN/passkey confirmation. The implementation is
present; end-to-end physical connection remains uncertified.

## Control-centre rendering and latency

The display runs 1920×1080 at 120 Hz with Hyprland scale 1.5. Several SVG icons
were rendered at 12 or 13 logical pixels, which becomes a fractional 18 or 19.5
device pixels before a colorization effect. The source assets themselves are
valid vector Adwaita icons. The control now requests source textures using the
screen device-pixel ratio, enables mipmapping, and uses 16 logical pixels for
an exact 24-device-pixel result at the current scale.

The status adapter measured about 215 ms per complete Wi-Fi/Bluetooth/status
refresh; direct Bluetooth status measured about 66 ms. Popup opening is local
and immediate, while mutations already use optimistic UI states. Press/release
feedback was reduced from 70+120 ms to 40+70 ms so the visual response settles
faster. The machine was not CPU- or memory-bound during the audit.

At the owner's later request, the controls popup was first reduced from the
desktop's 150% scale to 100% physical size. Physical review found that trial too
small and the post-processed icons still looked pixelated. The accepted second
pass uses 125% physical size (`5/6`) without changing the global display scale.
The live IPC reports 283x291 logical pixels for the closed 340x350 layout. Icon
rendering now uses Qt's native `ToolButton.icon` source/color path and removes
the hidden image plus `MultiEffect`. Quickshell reloaded without QML errors;
overview and expanded Bluetooth captures are under
`audit/2026-08-11-environment-consistency/`.

## AUR build responsiveness and package freshness

The first `yay` build installed Go and completed successfully. During its Go
compile and package compression, Host CPU pressure reached 23.97% over 60
seconds; memory pressure and I/O pressure were both zero. The Hub is capped at
200% CPU and all terminal work originally competed at equal priority with
Hyprland and Quickshell. Regular Kitty launches now keep Kitty itself at normal
priority but start Bash and its descendants at nice 10 and idle I/O priority.
The open owner shell received the same priority adjustment live.

The later `brave-bin` dependency transaction failed because the current pacman
databases dated August 1 while the cached `nspr-4.39-1` package no longer had a
matching detached signature on the first mirror. Package signature checking
must remain enabled. A full `pacman -Syu` refresh/upgrade is required before
retrying; refreshing databases without the matching upgrade would create an
unsupported partial-upgrade risk. The current image also lacks `less`, which
should be installed in that same transaction and included in the next base.

## Visual evidence

Accepted captures are stored in `audit/2026-08-11-control-centre/`:

1. `01-current-desktop.png` — initial desktop; healthy, but it shows the
   unwanted automatic Kitty and the owner-opened Host console.
2. `02-control-centre.png` — control-centre overview; structurally healthy,
   with clear grouping, though the pre-fix action icons are visibly small.
3. `03-bluetooth.png` — Bluetooth detail before scanning; healthy empty state
   and a clear search action.

The later `04-bluetooth-results.png` was rejected as audit evidence because the
idle lock activated before capture. Screenshot evidence alone cannot prove
keyboard focus, screen-reader semantics or real peripheral pairing.
