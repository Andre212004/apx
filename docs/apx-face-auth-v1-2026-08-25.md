# APX face authentication v1

## Result

The official Hub admits only the Lenovo integrated camera capture interface,
identified by udev path `pci-0000:05:00.3-usb-0:3:1.0`, USB ID `5986:212b`,
UVC interface `00`, and `:capture:` capability. The runtime does not lease the
camera metadata node or a broad USB device.

Howdy uses its native PAM module, pinned at commit
`d3ab99382f88f043d15f15c1450ab69433892a1c`, with CPU-only Python dlib 20.0.1.
The local face model `/etc/howdy/models/apx.dat` is root-owned mode 0600.
Failed and successful image snapshots are disabled and face authentication is
disabled over SSH.

`sudo` and `hyprlock` first admit `pam_howdy.so` as `sufficient`, then retain
the original `system-auth` or `login` stack. Face recognition is therefore a
convenience mechanism, not the only credential; the APX password remains the
recovery path.

## Owner use

1. Open the physical camera e-shutter.
2. For `sudo`, look at the camera after running the command. If Howdy times
   out, press Enter if necessary and enter the normal APX password.
3. For the lock screen, look at the camera when `hyprlock` appears. Enter the
   normal password if recognition fails or the camera is closed.
4. Close the e-shutter whenever face authentication is not wanted; this does
   not disable password authentication.

## Recovery

The original PAM files, Howdy configuration and enrolled model are stored at
`/var/lib/apx/backups/20260825T171900Z-face-auth-pam-v1`. The pre-camera Hub
launcher is stored at
`/var/lib/apx/backups/20260825T175200Z-face-auth-v1`.

To disable face admission without removing packages, set `disabled = true` in
the Hub's `/etc/howdy/config.ini`. To perform a complete rollback, restore the
saved `sudo` and `hyprlock` files with their mapped ownership, then restart the
Hub. Never remove or replace the `system-auth`/`login` fallback lines.
