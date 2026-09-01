# APX login, idle lock and clean Host transition v1 — 2026-08-03

The owner confirmed that firmware PXE noise is gone and the signed APX UKI now
boots directly to the graphical LUKS prompt. Host evidence proves `Secure Boot:
enabled (user)`, `Measured UKI: yes`, `Measured OS: yes` and current stub
`/EFI/APX/apx-system-v1.efi`. LUKS still contains only password slot 0; TPM
enrollment remains pending.

The visible `apx-host login:` flash is not a collection of terminal windows.
There is exactly one recovery `agetty` on tty1. It has one task, used 544 KiB at
inspection and consumed 15 ms CPU over the first five minutes. The official Hub
uses tty2. Plymouth quit, tty1 getty and Hub autostart became ready together;
the raw prompt remained visible for roughly the half-second required to start
the Hub machine and compositor.

The installed autostart now clears tty1 immediately after proving the recovery
console and before waiting for or launching the Hub. It does not start another
process or remove recovery: tty1 still has the same single getty, and pressing
Enter after intentionally switching to tty1 restores its prompt. Source and
installed SHA-256 are
`7a096f29a13f09501439226452ce1b5c76e0276bb31ba42455ab118be0ab08c6`.
The visual result awaits the next physical boot.

## Windows-like single-password flow

The accepted target separates disk and session authentication:

`signed measured boot -> TPM PCR-7 LUKS unlock -> hyprlock APX login -> Hub`

This mirrors the useful distinction between BitLocker and Windows sign-in.
The original LUKS password slot remains a recovery secret and is not reused as
the daily APX login. The Hub already has `hyprlock` 0.9.6, `hypridle` 0.1.8 and
an `apx` account with a password hash. No Host graphical account, display
manager or PAM bridge is introduced.

Repository staging adds an APX-themed hyprlock profile using the existing Hub
cyan, dark surfaces and Adwaita Mono type. The Hub runner fails closed through
Hyprland exit if the initial lock cannot run, starts Quickshell only after a
successful initial authentication, and starts at most one hypridle. Hypridle
locks after five minutes and turns the display off after ten, respects idle
inhibitors and does not auto-suspend the Host. Explicit APX suspend continues
to use the existing Host-mediated action.

The owner set the `apx` account password interactively without exposing it to
Codex, logs or command arguments; `passwd -S` confirms a password update dated
2026-08-03. The runner and both profiles are now installed with source-matching
hashes. An isolated missing-display launch parsed hypridle without configuration
errors. The first hyprlock check found one removed upstream option, which was
deleted; its second parse reached only the intentionally missing Wayland socket
with no configuration error. No validation process remains.

Activation still requires two physical proofs. First invoke the existing
`BLOQUEAR` control and unlock with the new APX password. Then prove one boot
with both LUKS recovery and the initial APX login. Only after those pass should
the TPM token be enrolled and the normal UKI rebuilt. Password keyslot 0 remains
throughout.
