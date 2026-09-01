# APX face authentication v1

## Result

The official Hub admits only the Lenovo integrated camera capture interface,
identified by udev path `pci-0000:05:00.3-usb-0:3:1.0`, USB ID `5986:212b`,
UVC interface `00`, and `:capture:` capability. The runtime does not lease the
camera metadata node or a broad USB device.

Howdy uses its native PAM module, pinned at commit
`d3ab99382f88f043d15f15c1450ab69433892a1c`, with CPU-only Python dlib 20.0.1.
The local face model `/etc/howdy/models/apx.dat` and configuration are owned by
`root:apx` mode 0640. This lets the unprivileged `hyprlock` PAM consumer read
the model without letting the Hub user alter it; root-only mode 0600 makes
`hyprlock` fail before recognition. Failed and successful image snapshots are
disabled and face authentication is disabled over SSH.

`sudo` and `hyprlock` first try `pam_howdy.so`, then retain the original
`system-auth` or `login` stack. Face recognition is therefore a convenience
mechanism, not the only credential; the APX password remains the recovery
path. The Hyprlock stack sends both a successful face and a successful password
through `pam_faillock.so authsucc`, so either valid credential clears old failed
password records instead of allowing them to accumulate behind face unlocks.

Hyprlock deliberately permits an empty Enter submission. After Howdy's
eight-second search has timed out, pressing Enter completes the waiting empty
password prompt and starts a fresh PAM cycle. That cycle again runs Howdy
before the normal password stack. If text was entered, a valid password still
unlocks; if the password is absent or wrong but the face succeeds on the new
cycle, Howdy's `sufficient` result unlocks without requiring the password.
Hyprlock refuses concurrent submissions while PAM is actively checking, so
repeated Enter presses do not queue parallel camera checks. After Enter, the
field says only `A VALIDAR…` while the current password conversation closes.
Howdy publishes a private runtime marker only after `read_frame()` returns its
first camera frame. A 300-ms lock-screen status probe validates that marker's
PID, process start time and command line before showing `A VERIFICAR A CARA…`;
before capture begins and after it ends, it shows the Enter instruction. This
avoids treating Howdy's earlier `/dev/video0` reservation as active capture.
After a failed cycle the field explicitly offers `ENTER: REPETIR CARA`.
Ordinary failed password accounting remains unchanged.

## Owner use

1. Open the physical camera e-shutter.
2. For `sudo`, look at the camera after running the command. Howdy currently
   searches for up to eight seconds. If it times out, press Enter if necessary
   and enter the normal APX password.
3. For the lock screen, look at the camera when `hyprlock` appears. If the
   initial search times out, press Enter with the field empty to try the face
   again. Alternatively type the normal password and press Enter; either a
   successful face cycle or the valid password unlocks.
4. Close the e-shutter whenever face authentication is not wanted; this does
   not disable password authentication.

## Recovery

The original PAM files, Howdy configuration and enrolled model are stored at
`/var/lib/apx/backups/20260825T171900Z-face-auth-pam-v1`. The pre-camera Hub
launcher is stored at
`/var/lib/apx/backups/20260825T175200Z-face-auth-v1`.

The state immediately before the 2026-08-31 model-readability correction is
stored at `/var/lib/apx/backups/20260831-face-auth-readability-v2`.
The accepted state after current-view enrollment and successful real `sudo`
and Hyprlock tests is stored at
`/var/lib/apx/backups/20260831-face-auth-working-v2`.
The immediate pre-change shell and lock-screen files for Enter-based face retry
are stored at
`/var/lib/apx/backups/20260831T160340Z-face-retry-control-colors-v1`.
The state immediately before first-frame signalling, Hyprlock faillock cleanup
and the matching shell refinements is stored at
`/var/lib/apx/backups/20260831T231335Z-first-frame-bar-shortcuts-v1`. The live
Howdy package is `howdy-apx 3.0.0beta.r592.d3ab993-3`; it explicitly packages
`/etc/howdy/config.ini`, so package upgrades preserve the locally enrolled APX
configuration through pacman's normal protected-config handling.

To disable face admission without removing packages, set `disabled = true` in
the Hub's `/etc/howdy/config.ini`. To perform a complete rollback, restore the
saved `sudo` and `hyprlock` files with their mapped ownership, then restart the
Hub. Never remove or replace the `system-auth`/`login` fallback lines. After
enrolling or replacing the model, restore `root:apx` ownership and mode 0640
on both `config.ini` and `models/apx.dat` before testing `hyprlock`.
