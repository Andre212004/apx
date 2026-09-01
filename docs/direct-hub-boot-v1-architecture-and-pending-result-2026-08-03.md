# Direct Hub boot v1 — architecture and pending result — 2026-08-03

The owner requested removal of the repetitive APX Headless boot menu and Host
root login while retaining secure machine entry. The installed v1 flow is:

`firmware -> fixed APX boot entry -> LUKS passphrase -> official graphical Hub`

`systemd-boot` remains the boot loader. Its default stays the fixed
`apx-headless.conf`, editing remains disabled, and the menu timeout changes from
three seconds to zero. The recovery menu remains available through the boot
loader key path. A dated copy of the previous loader config is retained.

The LUKS passphrase remains mandatory. It is now presented by the installed
Plymouth `spinner` graphical boot UI instead of the raw cryptroot terminal
prompt. The mkinitcpio `plymouth` hook and `splash` kernel option are installed,
and the regenerated initramfs contains the graphical unlock path. TPM 2.0 is
present, but Secure Boot and a measured UKI are not established. Automatic TPM
unlock is therefore not adopted: it would remove the only meaningful pre-boot
authentication without a complete verified-boot policy. No TPM token was
enrolled, LUKS keyslot 0 remains intact, and the encrypted-root layout is
unchanged.

After encrypted root is unlocked, enabled
`apx-official-hub-autostart-v1.service` waits for tty1 and the existing Host
services, refuses any pre-existing Environment machine, reconciles only a stale
fixed `hub-ficticio` trial, and runs the exact official Hub launcher. It creates
no Host user, changes no PAM rule, installs no display manager and exposes no
session chooser.

The ordinary root getty remains on tty1 as recovery. A successful Hub occupies
tty2. If launch fails, systemd makes at most three restart attempts in two
minutes; tty1 remains available. A normal owner exit does not restart the Hub.

Current Arch repositories provide greetd/tuigreet and SDDM, but neither solves
pre-boot encrypted-root unlock. Both add Host PAM/session and seat ownership
that the exact launcher does not need. Direct entry after successful graphical
LUKS authentication removes the redundant Host-root prompt with less new
authority; Plymouth is the sole new boot-UI package.

Rollback disables `apx-official-hub-autostart-v1.service`, restores
`/boot/loader/loader.conf.before-direct-hub-20260803`, removes `splash` and the
mkinitcpio Plymouth hook, rebuilds the initramfs, and reloads systemd; manual
`entrar_no_HUB` remains unchanged.

The owner has now physically confirmed that the boot menu and redundant Host
root password disappeared and that the official Hub opened automatically after
LUKS. The first service invocation lost a concurrent socket race and its fixed
five-second retry succeeded. The updated launcher now waits explicitly for all
eight required sockets and tmpfiles creates `/run/apx` before services. The new
Plymouth cryptroot presentation requires the next reboot for visual proof.

The owner subsequently requested removal of the remaining boot password.
Inspection confirmed that this prompt is LUKS keyslot 0, not a root or Hub
login. TPM 2.0 is available, but Secure Boot remains disabled and there is no
measured UKI or TPM token. Automatic unlock is therefore not silently enabled:
doing so in the current boot chain would let a modified unverified boot path
request the TPM-held disk key. The owner must explicitly choose between a
verified-boot/TPM rollout, immediate reduced-security TPM enrollment, or
retaining the current encrypted pre-boot authentication.
