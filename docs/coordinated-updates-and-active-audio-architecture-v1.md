# Coordinated updates and active-audio handoff architecture v1

Status: owner-accepted intended architecture with pure contracts, creation
policy and Hub UI prototype implemented. Package mutation and general graphical
audio handoff are not yet installed or physically certified.

## Decisions

### Coordinated updates

An update requested from the authoritative Hub targets the Host and every
registered Environment whose update policy is `follow-host`. New Environments
receive that policy by default. During creation the owner sees a checked
`Seguir atualizações do Host` control and may explicitly opt out; an existing
Environment may later change between `follow-host` and `excluded` through an
authenticated Hub action.

“Update equally” means one coordinated transaction and one frozen signed
repository view. It does not mean every Environment has the same packages.
Each target resolves its own installed package set against the same repository
snapshot, so an editor existing only in Development is updated there without
being installed in Hub or another Environment.

The Hub is the control surface, not the package owner. It cannot pass arbitrary
commands, package names or pacman flags to the Host executor.

### Active audio

Audio settings are machine-continuous and access is session-exclusive. Before
an Environment loses authority, APX captures only:

- output volume, mute and selected output;
- input volume, mute and selected input.

It does not persist application/stream titles, audio content or recordings.
APX then stops that Environment's local PipeWire, revokes its exact playback
and capture device leases, proves the old Environment can no longer open them,
leases the devices only to the incoming active Environment, starts its local
PipeWire and applies the stored values. Authority is published only after both
revocation and restore verification pass.

This keeps application graphs isolated while making `80%`, speaker mute and
microphone mute appear global to the owner. A stopped or inactive Environment
has no PipeWire process with a physical device lease and therefore cannot keep
listening or changing volume.

## Update transaction

The admitted sequence is:

1. Hub requests a read-only preview.
2. Host freezes one signed repository database view.
3. Host inventories the Host and every Environment policy.
4. Each included target resolves its own package transaction against that same
   view; packages are downloaded into operation-private Host staging and
   signature-verified before mutation. This staging is never mounted into an
   Environment, is not a reusable cross-Environment cache and follows the
   update journal's explicit retention/cleanup decision.
5. The plan shows included/excluded Environments, package changes, required
   restarts, disk use and rollback capacity.
6. A separate owner confirmation stops Hub and all included Environments.
7. APX snapshots Host system state and every included Environment root and
   Home independently; Home is preserved for controlled recovery and is never
   rolled back automatically merely because packages changed.
8. The Host applies first, then included Environments in canonical name order,
   offline from the private verified staging set.
9. The first failure stops the transaction. APX does not continue through the
   remaining Environments and does not silently delete any rollback set.
10. Verification covers boot/recovery, registrations, package databases,
    network, audio handoff and graphical readiness before publication.
11. Snapshot retirement is a later explicit operation.

An excluded Environment stays unchanged and is visibly marked as potentially
incompatible with the updated Host. It may be updated manually or re-enrolled
later. Exclusion is not a promise that an arbitrarily old Environment will work
forever with a new kernel, driver or device protocol.

## Safety boundaries

- Updates are never implemented as `for env; pacman -Syu` from a Hub terminal.
- Running Environments, missing snapshots, an incomplete private staged package set, uncertain
  APX journal state or insufficient capacity block activation.
- There is one update lock for the entire machine.
- No writable or reusable package cache is shared between Environments.
- Credentials, arbitrary hooks and unsigned repositories remain excluded.
- Kernel, firmware, microcode and drivers are Host targets only.
- Environment-local application packages remain Environment targets only.
- An Environment package failure cannot cause automatic deletion or downgrade
  of unrelated Home data.
- Reboot is a separate, visible consequence and authorization.

## Current implementation

- `src/apx_update_coordinator.py` implements default/owner-selected policy and
  a deterministic blocked/ready transaction plan.
- `scripts/virtual-lab/apx-lab-runtime.py` records `follow-host` by default and
  accepts `--exclude-host-updates` during creation planning.
- `prototypes/hub-demo` contains the checked creation control.
- `src/apx_audio_handoff.py` implements bounded output/input state and the
  exclusive handoff effects.
- Unit tests cover defaults, exclusions, same-repository/offline requirements,
  blockers, audio bounds and exclusive capture authority.
- The physical pilot now has enabled Host services for authenticated preview,
  policy selection, explicit confirmation, operation-private staging, Btrfs
  snapshots, sequential application, retained failure state and reboot notice.
- The exact official Hub now leases the udev-resolved ALC287 playback and
  capture nodes only for its active generation. Its local PipeWire publishes
  the analog nodes and a root-owned service restores volume and mute.
- A bounded physical certification passed authenticated preview, audio source
  and sink, Quickshell, full device revocation and tty1 recovery. No real
  package mutation was performed during certification.

## Required next physical stages

1. Prove two disposable Environment updates from one frozen repository view,
   including one excluded Environment and one forced failure/rollback.
2. Prove playback and microphone revocation across two disposable graphical
   Environments before enabling capture in normal Environments.
3. Generalize the exact-generation graphical launcher and authenticated peer
   proof before exposing either service to arbitrary graphical Environments.

The exact Hub pilot is active, but mass package mutation and cross-Environment
audio handoff remain experimental and are not yet production-certified.
