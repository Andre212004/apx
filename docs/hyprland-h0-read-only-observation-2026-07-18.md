# APX Hyprland H0 Read-Only Observation — 2026-07-18

Status: current physical foundation observed and temporary graphical package
root rebuilt/finalized. No Host package, APX release, Environment, GPU/input
grant, VT switch, compositor, service, or cleanup effect occurred.

## Physical headless foundation

- Host identity: `apx-host`, physical (`systemd-detect-virt=none`).
- Display managers: SDDM and greetd packages absent; their units and the
  display-manager alias are not found/inactive.
- Graphical owner: only the root text login on `seat0`/tty1; no graphical login
  session or graphical lease was observed.
- Recovery: tty1 is the owner-tested encrypted-root text path from receipt
  `db70438f786c3282755c44940bc27a5b18095bd31eeb4a904dbce62003634ad2`;
  tty2 is inactive and available as the candidate experiment VT.
- APX: Hub and Development healthy; `codex-test-lifecycle-v1` stopped; zero
  uncertain operations.

## Exact display boundary

- AMD target: PCI `0000:05:00.0`, driver `amdgpu`, `/dev/dri/card2`,
  `/dev/dri/renderD129`.
- Internal connector: `card2-eDP-2`, connected/enabled, preferred observed mode
  1920×1080.
- NVIDIA excluded device: PCI `0000:01:00.0`, driver `nouveau`, card1/renderD128.
  Its DP/HDMI/eDP connectors were all disconnected/disabled.
- No DRM or input node was opened by the observation.

## Exact initial input candidates

- built-in primary keyboard: `AT Translated Set 2 keyboard`, stable path
  `platform-i8042-serio-0`, currently event3;
- built-in touchpad: `ELAN06FA:00 04F3:31DD Touchpad`, stable path
  `platform-AMDI0010:01`, currently event11;
- the ITE special-key device and externally connected Logitech G305 are not in
  the H0 input set;
- event numbers are observations only; a future mediator must re-resolve and
  verify stable ancestry immediately before granting access.

## Reconstructed graphical package root

The dated 2026-07-11 chain was reproduced from scratch after reboot:

- database bytes: 8,818,209;
- base resolution: 138 packages, manifest
  `574f5d31e7c4ee46b1982fe2baf285d014ba0d712e91aea6d00413ba8fe5e3f9`;
- graphical role: 194 additional packages, manifest
  `e2f6adfc19e00dfe7cae21b4eab1650437edf24d817dc355a9af449d1cd9b25e`;
- base signatures: 138 packages verified twice, evidence
  `468116fb5277d91a099d0d4adbc5ca6579a5962965b062c0b6a1f09db9e4ea84`;
- graphical signatures: 194 packages verified twice, evidence
  `15ee100d7be5bfef16278f476503c2b2d7e3546fb3027b5f3a541180dc302863`;
- graphical metadata digest:
  `89ed0ab7623a93972bb403af33bbda4ee1ebb2717d285455fa4a240adea455df`;
- built package count: 332; allocated bytes: 1,739,587,584; build report
  `e446f61394ef0025f2b854db81ba24e364e898836a5ac54bb5df97f9e0fe2335`.

The review found locally generated pacman private trust, machine identity,
transaction timestamps, and log state in the temporary package root. The new
finalizer removed/normalized only that temporary state and then measured the
complete tree:

- finalized logical bytes: 1,596,400,395;
- finalized allocated bytes: 1,736,671,232;
- package install dates normalized: 332;
- private-key, random-seed, pacman-trust, Development-owner, and special-file
  entries: all zero;
- empty machine identity and pacman log: verified;
- final tree digest:
  `83c58deaa56c83c23eee57dc02ecd3a67ccaede0d75918932f7f3b9557ab3401`;
- final report digest:
  `fb8a06d588b3dbf0f48b8626a1effc0df95e4c6dd12bfa995f167fe0376c530a`.

Key role versions include Hyprland 0.55.4, Aquamarine 0.12.1, seatd 0.9.3,
Mesa 26.1.4, libinput 1.31.3, Xwayland 24.1.13, uwsm 0.26.6, foot 1.27.0,
and fuzzel 1.14.1. The Hyprland executable digest is
`3b7b97d49334e604833f456c514875708d2ad43a7482c3aa95172595180b7407`.

## Remaining blockers before H0

1. Reproduce the finalized tree digest independently or explain and bind every
   allowed variance before promotion.
2. Define and fixture-test promotion into one immutable graphical APX release,
   including Environment-local user/home/config creation without Host packages.
3. Implement the exact AMD KMS/render lease and selected-input mediator.
4. Implement the host-owned tty1 recovery controller, tty2 experiment control,
   watchdog, teardown, and zero-residue observer.
5. Create one disposable generation-bound graphical Environment and a complete
   H0 evidence preview.
6. Obtain a separate owner approval for the exact physical experiment.

Until these gates pass, the finalized root remains temporary evidence only and
must not be copied into `/var/lib/apx` or launched on the physical display.
