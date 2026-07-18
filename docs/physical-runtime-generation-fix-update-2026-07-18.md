# Physical Runtime Generation-Fix Update Candidate — 2026-07-18

Status: exact candidate assembled and independently parsed; blocked. No import,
activation, Host change, Hub/Development stop, rollback, cleanup, or release tag
is authorized by this document.

## Purpose

The installed experimental physical runtime generates destroy plans with a
random generation and does not compare the plan generation with the registered
Environment generation before destructive effects. The first disposable
root-host test detected this before destruction. `codex-test-lifecycle-v1`
remains stopped and preserved.

The candidate changes only `host-runtime` so destroy plans inherit the current
registered generation and stale plans fail before journal, stop, unpublish,
home removal, or root removal.

## Exact identities

- source revision: `909a7de7a257ed7320544bd5faa409b96afc543e`;
- installed parent: `02fd4bafd7b851bce0bc0d9aa140bdca89240088`;
- installed runtime SHA-256:
  `5151b89ed53561c1e1f12b05b0b0c50dee483caa8e47f4c2ee397d767ded2b17`;
- candidate runtime SHA-256:
  `77353bb778d4a5b9cfbb2e81e485f24144cac3e700822135c9de17e83bdb2f3d`;
- installed `/usr/bin/apx` and `/usr/lib/apx/apx-lab-runtime.py` are
  byte-identical;
- the installed parent commit reproduces the installed runtime hash exactly.

The candidate/installed diff contains only generation binding in
`make_plan("destroy")` and a pre-effect generation comparison in `destroy()`.

## Closed artifact

The deterministic uncompressed tar was built twice outside Git and both builds
were byte-identical.

- update ID: `update-b84a22063fd5d315f1b13d76f16f2ca8`;
- artifact bytes: `30720`;
- artifact SHA-256:
  `b84a22063fd5d315f1b13d76f16f2ca8b0666898a67f5f60c1d202662341c4fc`;
- manifest SHA-256:
  `d4cfee6bfdbcc3c1dde6f72bc50e6e6b273790b3cb1187ca3379c8bdf718f036`;
- member count: `2`;
- components: exactly `host-runtime`;
- members: mode-0600 `manifest.json`, then mode-0755
  `components/host-runtime`;
- UID/GID and mtime are zero; owner names and PAX data are empty;
- no commands, hooks, credentials, keys, links, directories, special files,
  path traversal, or extra members are carried.

The artifact exists only in temporary root-host build space and remains
untrusted. It is not committed, imported, staged under APX state, or installed.

## Evidence receipts

- 642-test receipt:
  `c723ba38477a87efe8d53f9b469de18e78a9c8d49b1e2e8c7d0428c07a8917e4`;
- compatibility receipt:
  `ac1629649684e072975e87d4e688610121bd15750d855ab1d63bddf19674240a`;
- rollback manifest:
  `1ef84c400f7e21b0e8c5359e3974e413de4e44e4efa8fd559be3151723206e56`;
- documentation set:
  `6e5978d5b2920b6cb60e90325ba8c8b1973269560f188e1c133fa853d963b8c1`;
- candidate digest:
  `52c8cb100e0af47d5b50578bee35882a66923caf04de1c91c774b4301603d9c5`;
- installed-evidence digest:
  `b58f9dd4702e2df5e6937f2b2125430c874781e45114a297ee763280d5496866`;
- consequence digest:
  `4f854a1d07259a1dc9896fbad9c7a7b0c2377faacf3f1c0846fffbade8dc7418`;
- preview plan:
  `7ca656275356657c6a1a3140addd40eb7830579da8867399b21e92559b897b2d`.

The suite had zero failures and ten expected external-fixture skips. Focused
artifact, update, journal, and stale-destroy tests also passed.

## Reconciled installed evidence

- physical marker and machine identity match through sanitized digests;
- installed runtime, executor, and Hub-client hashes are exact;
- Hub release/generation and simple Development generation are exact;
- the dated audit and root-host reconciliation are bound;
- APX reports no uncertain operation and Hub remains clean;
- the owner-confirmed simple Development state is reconciled;
- root-host inventory and GitHub recovery source are current;
- Host available capacity exceeds 470 GiB;
- the stopped disposable-test hold is recorded and preserved.

## Preview result

Classification: `blocked`.

Only blocker: `recovery-console-not-verified`.

The systemd-boot APX entry, EFI loader, kernel, initramfs, and encrypted-root
arguments exist. Metadata does not prove a human-accessible recovery console
was exercised in the current physical state, so the gate remains false.

The closed evidence schema is implemented in `src/apx_recovery_console.py`.
It cannot reboot the Host or manufacture a positive receipt. It accepts a
receipt only when it binds the physical machine marker, selected boot entry,
kernel, initramfs, distinct before/recovery boot IDs, owner presence, built-in
keyboard use, encrypted-root unlock, root console access, and the post-boot APX
reconciliation. Every field is exact and every safety assertion is mandatory.
Metadata-only observation, a same-boot observation, a non-physical observer,
an unknown field, or a non-boolean assertion fails closed.

## Separately authorized recovery-console rehearsal

This procedure is a future availability-affecting physical operation, not
authorization to run it now. It requires the owner at the machine and fresh
approval for the exact reboot window.

1. Before reboot, record sanitized digests of the APX physical marker, machine
   identity, selected systemd-boot entry, kernel and initramfs, the current boot
   ID, exact Hub and Development generations, the disposable hold, and the APX
   uncertain-operation result.
2. Reboot through the already installed APX recovery entry. Do not edit the
   entry, kernel arguments, disks, encryption, bootloader, packages, or APX
   registrations.
3. With the owner physically present, use the built-in keyboard to unlock the
   encrypted root and confirm an independent root text console. Do not enter
   passphrases, keys, tokens, command output containing secrets, or raw machine
   identifiers in the receipt.
4. Record the recovery boot ID and observation time with timezone. The boot ID
   must differ from the pre-reboot value.
5. Return to the ordinary installed boot path, then reconcile APX from the root
   Host: Hub and Development generations must be unchanged, the disposable
   hold must still exist, and no uncertain operation may be present.
6. Record explicit negative evidence that no disk-layout, encryption,
   bootloader, package, or APX lifecycle change occurred. Parse and assess the
   sanitized receipt with the repository contract.

Any failed or unknown check keeps the update blocked. The rehearsal does not
authorize candidate import, activation, rollback, cleanup, or destruction.

## Minimum-privilege effect map

This is a design boundary, not an implemented adapter.

| Effect | Exact allowed object | Forbidden expansion |
|---|---|---|
| Reserve staging | one new mode-0700 operation directory under fixed logical root `/var/lib/apx/updates/staging` | existing path adoption, caller path, symlink |
| Copy bytes | exact 30,720-byte artifact | network fetch, redirect, overwrite, executable staging |
| Verify artifact | exact two tar members and all bound hashes | extraction, execution, alternate member |
| Reverify installed | exact marker, component hashes, generations, journal, capacity, recovery receipt | mutation or inferred positive evidence |
| Activation approval | one candidate/installed/plan digest tuple | reusable or wildcard approval |
| Stop lifecycle | exact current simple Development and Hub generations | destroy, force stop, another Environment |
| Retain rollback | exact installed runtime plus metadata in one immutable rollback set | deletion or replacement of prior rollback |
| Install candidate | logical `host-runtime` mapped by a separately reviewed fixed adapter | arbitrary path, client/executor replacement, package action |
| Verify final | runtime hash, APX state, exact generations, disposable hold, zero uncertainty | cleanup or destroy retry |
| Publish identity | one installed-update identity with rollback retained | tag creation, rollback retirement, history rewrite |

No stage grants Hub, Development, or a disposable Environment access to update
staging, rollback bytes, or Host install authority.

## Recovery by boundary

- Before a prepared effect, no physical outcome is claimed.
- During staging, preserve and revalidate; do not adopt or clean automatically.
- Before replacement, changed evidence cancels activation.
- After rollback retention, preserve both sets and inspect.
- During/after install uncertainty, recovery must identify actual installed and
  rollback hashes. No automatic rollback is allowed.
- Publish only after final verification and while rollback remains retained.
- Staging cleanup and rollback retirement are later separate operations.

## Remaining gates

1. Obtain a fresh reboot-window approval, then exercise and record the physical
   recovery-console path with the owner present, without modifying Hub,
   Development, disks, encryption, bootloader, packages, or APX state.
2. Rebuild the artifact after any source change and reproduce every digest.
3. Implement and hostile-test the minimum-privilege adapter that executes the
   now-fixed staging and host-runtime mapping; the non-executing plan contract
   is complete.
4. Exercise interruption fixtures before/after rollback retention and install.
5. Reobserve all evidence immediately before an import preview.
6. Obtain separate import approval, then a separate activation approval.
7. Keep rollback retirement out of both approvals.

Until all gates pass, do not install this candidate and do not destroy
`codex-test-lifecycle-v1`.
