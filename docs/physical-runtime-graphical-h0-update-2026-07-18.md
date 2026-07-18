# Physical Runtime Graphical-H0 Update Candidate — 2026-07-18

Status: exact candidate built twice and verified; physical preview is blocked
by stale post-reboot Hub and Development registration state. Nothing was
imported, installed, started, stopped, or deleted.

## Purpose

This Host-runtime-only candidate keeps the earlier generation-bound destruction
fix and adds the minimum lifecycle knowledge needed to create a stopped
Hyprland H0 Environment:

- admit only the `graphical-h0` role;
- map it only to the promoted `hyprland-h0-v1` release;
- apply 16 GiB root and 8 GiB home limits;
- refuse generic activation of the graphical role before any runtime effect.

It does not contain the future GPU, input, VT, watchdog, or Hyprland launch
adapter.

## Exact candidate

- source revision: `aa5368315560341b4c6ab7d6736483bd80339134`;
- installed parent revision: `02fd4bafd7b851bce0bc0d9aa140bdca89240088`;
- update ID: `update-a1b55982d14fb0bdf7afa8f1dd7991ca`;
- installed runtime SHA-256:
  `5151b89ed53561c1e1f12b05b0b0c50dee483caa8e47f4c2ee397d767ded2b17`;
- candidate runtime SHA-256:
  `0d7cc0c0c0631b65f68639f8b4994e3e3441a817604487256a30edd82f96da9f`;
- artifact SHA-256:
  `a1b55982d14fb0bdf7afa8f1dd7991caf9d3a7ad5e24b321510763ad5b675a66`;
- artifact size: 30,720 bytes;
- manifest SHA-256:
  `62f5070ba016ac497f69dae6b6de78cbd2e07d033afd16306015cb3d8197f5fa`;
- members: mode-0600 `manifest.json`, then mode-0755
  `components/host-runtime`;
- test receipt:
  `e71b5dba3bae19934b618a8f093970452b1e9a7603785d53ed1143cca6ae7951`;
- tests: 682 passed, 8 expected skips, 0 failures.

Two independent in-memory USTAR builds were byte-identical. The repository's
closed, non-extracting reader accepted the exact artifact and recovered only
the expected runtime digest. The temporary mode-0600 artifact remains outside
Git under `/tmp`; it is untrusted and has not entered APX state.

## Newly observed blocker

The 2026-07-18 recovery reboot cleanly shut down both nspawn machines at 11:03.
The current boot began at 11:08. No `apx-environment-hub.service` or
`apx-environment-development.service` exists in the current boot and
`machinectl` lists neither machine. Their registrations nevertheless still say
`state=running`:

- Hub generation `d68ee7a2-268a-4534-b033-8f5313943fcf`;
- Development generation `b90155f6-ece2-44ae-91fc-42d91d6b35a5`.

The stopped disposable hold remains generation
`1ec52013-e715-413a-bb48-b4691cf31ee9`; systemd has zero failed units; the APX
journal reports no uncertainty; the immutable Hyprland release remains
read-only; more than 469 GiB is available.

This is a clean registration/runtime mismatch, not evidence that either
Environment is running. A truthful physical update preview must remain blocked
until the owner separately authorizes reconciliation of the Hub and
Development registrations to stopped, or separately directs their activation.
The candidate must not be imported or activated on unreconciled evidence.
