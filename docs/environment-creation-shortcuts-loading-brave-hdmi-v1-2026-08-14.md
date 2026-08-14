# Environment creation, shortcuts, loading, Brave and HDMI — 2026-08-14

## Owner-facing result

- Creation profiles are labelled `BÁSICO · BASE APX`, `INTERMÉDIO · DIA A
  DIA` and `COMPLETO · TRABALHO`.
- Drawer headings and capability rows show only their title. Right click on a
  capability expands its purpose and the exact programs supplied; there is no
  flashlight/info ornament in the collapsed row.
- An accepted create request closes the form immediately. Only the catalogue
  and progress state remain visible, preventing the creation form from
  flashing behind the normal Environment list.
- Future graphical Environments use Brave for the browser shortcut and MIME
  defaults. Firefox is no longer installed by the web/documents capability.
- The workload Control Centre uses the Hub's everyday controls and a readable
  layout, while deliberately excluding APX Host and Host Terminal authority.
- `SUPER+A` and `SUPER+E` are part of the common Environment seed. A Control
  Centre toggle can disable/re-enable both bindings per Environment; enabled is
  the default.

## Shortcut lifetime repair

The graphical session previously used logind's `/run/user/1000`. A transient
PAM or `machinectl shell apx@...` session could end later and make logind remove
that directory while Hyprland and QuickShell were still alive. Their IPC
sockets disappeared, so `SUPER+A` and `SUPER+E` silently stopped working after
a handoff.

Host-supervised APX sessions now use `/run/apx/session-1000`, which is owned by
the graphical supervisor rather than by a transient login. A physical
Hub-to-Hub transition preserved the Hyprland and QuickShell socket trees;
watchdog returned `healthy`, the shortcut helper returned `enabled`, and a
QuickShell IPC call succeeded after the restored session was active.

## Loading surface

The Host-owned tty1 APX progress surface is now exclusive for the full
graphical handoff. Stopping `getty@tty1` was insufficient because systemd could
start it again during recovery. The supervisor therefore applies a runtime-only
mask with `--now` before closing the current GUI. A newer handoff retains that
mask; APX removes it and restores the recovery login only when no handoff lock,
machine or GUI owns the display and tty1 is genuinely active.

A physical Hub-to-Hub transition proved `getty@tty1` remained
`masked-runtime` and inactive while tty2 and the restored Hub were active. No
getty journal entry occurred during the validation interval, so the Host login
prompt cannot repaint over the APX loading page.

## Hybrid AMD/NVIDIA external displays

This Legion routes internal eDP-2 through AMD card2 and HDMI-A-1/DP through
NVIDIA card1. Hybrid launches now lease both KMS card/render pairs, create and
lease the NVIDIA auxiliary character devices, and set
`AQ_DRM_DEVICES=/dev/dri/card2:/dev/dri/card1`.

Future roots receive `egl-gbm` plus the exact Host-driver-matched
`nvidia-utils 610.43.03-3` from a digest-pinned Host-owned package artifact.
Brave is supplied the same way from the verified `brave-bin 1:1.93.136-1`
artifact. The running Hub sees all NVIDIA devices and the exact userspace
version. Final dual-monitor modesetting remains pending because HDMI-A-1 was
physically `disconnected` at the final check on 2026-08-14.

Existing pre-change Environment `faculdade` was deliberately not migrated. A
physical launch failed closed and restored Hub automatically; the owner had
already decided to delete existing profiles and create fresh ones.

## Verification

- Full repository suite: 1032 tests, 11 expected skips, all passing.
- Installed and source switch runner SHA-256:
  `78af71882edafdc5faedffeef48799d075528eaf0db4c1ca97eecc85a04839fc`.
- Hub watchdog after transition: `healthy`, no recovery.
- Host failed units after cleanup: none.
- Exact pre-change physical files are retained under
  `/var/lib/apx/backups/20260814-shortcuts-loading-hdmi-v1/`.
