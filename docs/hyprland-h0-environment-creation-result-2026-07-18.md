# APX Hyprland H0 Environment Creation Result — 2026-07-18

Status: runtime update and stopped disposable Environment creation completed;
graphical activation remains blocked by design.

## Runtime update result

The owner authorized reconciliation of the post-reboot Hub and Development
registration mismatch. Both machines were already absent and their shutdown
journal was clean. APX recorded both unchanged generations as stopped without
altering their root or home data.

The exact Host-runtime-only update then passed its final preflight and was
installed:

- update ID: `update-a1b55982d14fb0bdf7afa8f1dd7991ca`;
- before SHA-256:
  `5151b89ed53561c1e1f12b05b0b0c50dee483caa8e47f4c2ee397d767ded2b17`;
- after SHA-256:
  `0d7cc0c0c0631b65f68639f8b4994e3e3441a817604487256a30edd82f96da9f`;
- `/usr/bin/apx` remains the exact alias of the runtime target;
- the previous 25,467-byte runtime is retained mode 0500 under the fixed APX
  rollback directory;
- the staged candidate remains mode 0600 and the installed result is mode 0400;
- no service, Environment, package, GPU, input, VT, display, or cleanup effect
  was part of the update.

## Stopped Environment result

The exact creation plan digest was
`db823cf0817f1a94dcbf7ef2958106aac4f2a5b7ad1000dbccdb73d6211237d7`.
It created only:

- name: `codex-test-hyprland-h0-v1`;
- role/release: `graphical-h0` / `hyprland-h0-v1`;
- generation: `c4fc5c49-4106-4a56-b1f0-13bffa41a0c1`;
- writable root snapshot qgroup `0/286`, 16 GiB referenced and exclusive
  limits;
- separate empty home qgroup `0/287`, 8 GiB referenced and exclusive limits;
- stopped registration with no observed machine.

The Environment contains `/usr/bin/Hyprland` with SHA-256
`3b7b97d49334e604833f456c514875708d2ad43a7482c3aa95172595180b7407`.
Its root snapshot retains the promoted release as its Btrfs parent.

An intentional `apx environment start` denial test returned the dedicated H0
device/recovery refusal. `machinectl` confirmed that no corresponding machine
was created. APX remained healthy, systemd had zero failed units, and Hub,
Development, and the earlier disposable hold retained their exact generations.

## Next boundary

This is now a real APX Environment containing Hyprland, but not yet a running
graphical Environment. The next adapter must grant only the selected AMD DRM
nodes and built-in input devices on tty2, enforce a watchdog and maximum run
time, preserve tty1 recovery, prove cleanup, and return to a headless state.
Neither the generic start command nor this result authorizes that activation.
