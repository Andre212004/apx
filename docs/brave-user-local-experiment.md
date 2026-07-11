# User-local Brave experiment

## Scope

This experiment evaluates an official extracted Brave release owned by the
`apx-development` Environment. It does not replace or modify the global Arch
`brave-bin` package. It is development evidence, not implemented APX lifecycle
behavior.

## Confirmed experiment design

- Back up the development Brave profile and verify the backup before the first
  local-build launch.
- Accept only the Linux archive published by the official
  `brave/brave-browser` release and verify its SHA-256 value against both the
  official checksum asset and the digest returned by GitHub's release API.
- Install each release beneath a version-named user directory and switch an
  atomic `current` symbolic link only after extraction succeeds.
- Keep downloads, validation profiles, desktop integration, backups, and the
  installation inside the development user's home.
- Use a uniquely named user desktop entry. Preserve the prior MIME defaults so
  changing the default browser is reversible.
- Roll back by restoring the prior MIME defaults, removing the unique desktop
  entry, repointing or removing `current`, and restoring the verified profile
  copy if profile rollback is required.

## Observed result on 2026-07-11

The official Brave 1.92.139 Linux amd64 archive matched the official published
SHA-256 checksum and GitHub release-asset digest. The archive ran from the
development user's home and opened a writable copy of the existing 1.92.139
profile. The global `brave-bin` installation remained present and unchanged.

The KDE user desktop entry and HTTP, HTTPS, and HTML defaults resolved to the
local build. The session exposed PipeWire/PulseAudio, the desktop portal,
Plasma notifications, and KDE Wallet services. The development home and the
version directory were mode `0700`, so other Environment users cannot traverse
to the executable under the confirmed Linux-user boundary.

## Problems and incomplete validation

- The extracted `chrome-sandbox` is not setuid. Sampled Brave child processes
  had `NoNewPrivs` enabled but reported no seccomp filters. The internal sandbox
  report did not complete, so the browser sandbox cannot yet be accepted as
  fully validated.
- GPU initialization reported `ZINK: vkCreateInstance failed
  (VK_ERROR_INCOMPATIBLE_DRIVER)`. Hardware acceleration was not proven.
- Audio service reachability was confirmed, but audible playback was not.
- Portal, notification, and KDE Wallet services were reachable, but interactive
  file-dialog, notification-delivery, and password round trips were not
  completed.
- A browser-managed download and a real version-to-version update were not
  completed.
- Cross-user denial follows from the `0700` home boundary; direct execution as
  `apx-hub` and `apx-trial` was not attempted because this experiment used no
  privilege escalation.

## Architecture status

The extracted user-local build is a viable packaging experiment but is not yet
an accepted APX application-isolation mechanism. Sandbox and GPU failures must
be resolved, and the remaining interactive checks must pass, before APX should
prefer it over the current global package. Update automation remains an idea
under evaluation and must retain the same official-asset verification,
versioned-directory, atomic-link, and rollback properties.
