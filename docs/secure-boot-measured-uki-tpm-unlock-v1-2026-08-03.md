# APX Secure Boot, measured UKI and TPM unlock v1 — 2026-08-03

The owner selected removal of the remaining boot password through verified
boot and TPM-backed automatic unlock, not through an unverified TPM enrollment.
The observed prompt is LUKS2 keyslot 0, not Host root or Hub login. The target
has UEFI, TPM 2.0 with SHA-256 PCRs and a 1 GiB ESP with sufficient free space.
Before migration, Secure Boot is disabled in firmware user mode, manufacturer
keys are present, no UKI is measured and no TPM token is enrolled.

## Intended chain

The accepted chain is:

`UEFI Secure Boot -> signed systemd-boot -> signed UKI -> systemd-stub
measurement -> systemd initrd -> TPM-bound LUKS unlock -> official Hub`

The UKI embeds the kernel, AMD microcode, initramfs and immutable kernel command
line. Under Secure Boot, external command-line changes are ignored. The signing
private key remains root-only on encrypted root; only its public certificate and
signed EFI binaries are present on the unencrypted ESP.

The TPM unlock token will be bound to PCR 7 only after Secure Boot is enabled
and the machine has booted the signed UKI. PCR 7 represents the enforced Secure
Boot policy, so a disabled or altered trust policy falls back to LUKS rather
than releasing the disk key. Kernel updates remain possible because newly
built UKIs are signed by the same protected APX key. A stronger signed-PCR-11
policy may be evaluated later, but is not required for v1 and must not be
misrepresented as implemented.

## Staged migration and recovery

The migration is deliberately split across physical boots:

1. Back up the current ESP metadata and boot configuration on encrypted Host
   storage. Generate a root-only APX signing key and certificate.
2. Build and inspect `/EFI/Linux/apx-secure-luks-v1.efi`, retaining the current
   `apx-headless.conf`, kernel and initramfs. Temporarily show the boot menu and
   select the UKI for one boot only.
3. Prove `Measured UKI: yes` while LUKS still requires its original passphrase.
4. Prepare signed systemd-boot and firmware key auto-enrollment. The owner uses
   firmware setup to clear existing Secure Boot keys into Setup Mode. The next
   boot enrolls the APX key and requires a further reboot with Secure Boot
   enabled.
5. Prove `Secure Boot: enabled`, the signed UKI and unchanged password keyslot.
   Only then enroll a TPM2 token bound to PCR 7 and build the normal UKI with
   `rd.luks.options=<UUID>=tpm2-device=auto`.
6. Preserve the signed LUKS-only recovery UKI and password keyslot 0. Prove one
   automatic boot, then restore the zero-second default menu.

At every pre-TPM stage, failure returns to the original LUKS entry while Secure
Boot is disabled. After Secure Boot enrollment, the signed LUKS-only UKI is the
recovery path. The password slot is never wiped. Firmware factory-key restore,
disabling Secure Boot and an Arch installation medium remain external recovery
paths. TPM enrollment is not performed from the current unverified boot.

## Current implementation state

`systemd-ukify`, `tpm2-tools`, `sbsigntools`, `efitools` and `dosfstools` are
installed. A root-only 10-year APX signing key and public certificate were
generated under `/etc/kernel`; certificate SHA-256 fingerprint is
`E4:56:FA:DE:B0:AE:FC:C9:2B:AA:85:9E:46:9A:35:56:92:C6:9D:D1:22:96:97:E3:A2:57:FE:C2:7D:D4:AB:A1`.
The original ESP and configuration are backed up on encrypted Host storage at
`/var/lib/apx/secure-boot-v1/backups-20260803-pre-uki`. The original firmware
PK, KEK, db and dbx databases are also exported as ESL files under
`/var/lib/apx/secure-boot-v1/firmware-keys-before-enrollment-20260803`.

The owner completed the first physical gate. The machine crossed a real boot
boundary through `apx-secure-boot-v1.conf`; `bootctl status` reported both
`Measured UKI: yes` and `Measured OS: yes`. LUKS password slot 0 unlocked the
disk and remains intact. Secure Boot was still disabled, as required for this
gate, and no TPM token was enrolled.

The normal signed image is now `/boot/EFI/APX/apx-system-v1.efi`, built with
the immutable LUKS-only command line plus `quiet splash`. `sbverify` matches the
APX certificate and its SHA-256 is
`8d9d12f67dabab362aae610ee9ccf765657af0313a478b8b3acba9dcb14709cb`.
The former duplicate auto-discovered UKI was moved off the ESP into the
encrypted recovery archive. The boot menu is again hidden with a zero-second
timeout; its normal entry is titled `APX System`, the retained verbose entry is
explicitly titled `APX Legacy Recovery (LUKS)`, and the editor remains disabled.
The ESP FAT dirty bit and orphaned clusters were repaired, then the ESP was
remounted with root-only `fmask=0077,dmask=0077`.

Signed systemd-boot copies are installed at the vendor and fallback paths and
verify against the same APX certificate. PK, KEK and db automatic-enrollment
files remain under `/boot/loader/keys/auto`, and `secure-boot-enroll force` is
configured. The owner cleared the firmware keys and completed the enrollment
boot. EFI then reported `SetupMode=0`, `VendorKeys=0` and `SecureBoot=0`, proving
custom APX keys were installed before enforcement.

That physical boot revealed an independent firmware-order defect. `BootCurrent`
was `0005` (`Linux Boot Manager`), but the persistent order places PXE/network
categories before it. This exactly explains the repeated `Checking Media` and
`EFI PXE 0 for IPv6 ... boot failed` screens before the disk finally boots. The
owner subsequently moved `Linux Boot Manager` ahead of PXE/network boot and
enabled Secure Boot without changing keys. The resulting Host evidence reports
`Secure Boot: enabled (user)`, `Measured UKI: yes`, `Measured OS: yes`, current
entry `apx-secure-boot-v1.conf` and stub `/EFI/APX/apx-system-v1.efi`. The signed
boot gate has therefore passed. PCR-7 TPM enrollment is now eligible, but waits
until the separate APX session-password gate is set and proven so the migration
never leaves normal startup without owner authentication.

To keep the graphical transition exclusive, logind is configured for only the
tty1 recovery console (`NAutoVTs=1`, `ReserveVT=1`) from the next boot. This
prevents a tty2 getty from interpreting graphical escape sequences as a login
name. The actual Plymouth screen still needs a photograph or live capture for
a visual spacing/typography audit; the changes here address the verified boot
flow, duplicate choices and console interference rather than inventing an
unseen redesign.
