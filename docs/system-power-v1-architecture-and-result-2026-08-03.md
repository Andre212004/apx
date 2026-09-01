# APX Host system power v1 — architecture and physical result — 2026-08-03

The Hub-authored `HOST_POWER_ACTIONS.md` proposal was accepted with two APX-
specific corrections. A fixed Host group cannot represent Environment user
`apx` because the graphical launcher uses dynamic private UID/GID ranges. The
socket therefore starts `root:root 0600`, is temporarily assigned as `0660` to
the translated active user by the authenticated launcher, and returns to
`0600` during recovery. Prepare and confirm clients also have different PIDs;
tokens are consequently bound to the same translated UID, official generation
and direct Quickshell parent PID rather than an impossible same-client PID.

`apx-system-power-v1.service` is installed, enabled and active. Its versioned
Unix protocol exposes only capabilities, status, prepare reboot/poweroff,
confirm and cancel. Mutations require both the existing official-Hub peer proof
and a direct `/usr/bin/quickshell` parent in the exact graphical unit. A random
30-second token is stored only as a digest, sent back through client stdin and
the socket body, consumed once, tied to the action and omitted from audit.
There is one pending action, a prepare rate limit and no shell/argument surface.

Prepare reports update reboot state and rejects active coordinated-update
states, machine-transition locks and Host shutdown inhibitors. A root-only
reservation closes the race with the update coordinator. After confirm, a
separate runner rechecks update/inhibitor state, takes the common transition
lock, waits for the response to reach Quickshell, invokes exact Hub recovery,
proves no Environment remains and only then asks Host logind for the allowlisted
action. It never ignores inhibitors and has no `systemctl` fallback.

The live mutable Hub now enables REINICIAR and DESLIGAR. Its native confirmation
panel shows blockers and reboot context, and offers CANCELAR/CONFIRMAR. The
token remains in QML memory and is written to the short-lived client through
Quickshell Process stdin; it is not an argument.

The bounded non-destructive physical proof passed direct-Host refusal,
authenticated Hub capabilities, temporary socket ownership, QML/Quickshell,
the existing graphics/audio/network ladder, recovery to tty1, socket closure
and zero machine residue. No reboot or poweroff was executed. The repository
suite passes 935 tests with 11 skips, including authorization, wrong parent,
two-step, replay, expiry, cancellation, update coordination and runner order.
Backups are under `/var/lib/apx/backups/20260803-system-power-v1`.

This remains an exact-Hub physical-pilot adapter until the general graphical
launcher defines the equivalent active-Environment peer identity.

## First real poweroff and recovery-race correction

The first owner-requested real `DESLIGAR` reached authenticated prepare and
confirm, then failed closed before Host logind. The status record identified a
concurrent cleanup race: both the foreground interactive launcher and the
power runner entered Hub recovery, and one removed
`/dev/apx-official-hub-device-leases-v1/state.json` while the other was reading
it. This explains the observed Environment closure without physical poweroff.

Recovery now takes an exclusive Host lock. The power runner also enumerates at
most one exact root `apx-official-hub-graphical-v1.py --interactive`
supervisor, rejects ambiguity, stops an autostart-owned supervisor through its
fixed unit or terminates the exact manual supervisor, waits for its exit and
only then invokes recovery. It retains the zero-machine proof before logind;
there is still no arbitrary process-kill or power-command surface.

The installed launcher and runner match repository SHA-256, 19 focused power
and launcher tests pass, and pre-change copies are under
`/var/lib/apx/backups/20260803-system-power-recovery-v2`. A second real
poweroff/reboot was deliberately not triggered from Codex because it is the
terminal physical proof and ends the active conversation.

## Real reboot verb correction

The next owner button proof showed that recovery and zero-machine validation
completed, but the final call failed with `Unknown command verb 'reboot'`.
This Host's `loginctl` supports `suspend` but not `reboot` or `poweroff`.
Consequently suspend remains an exact `loginctl suspend`, while the two terminal
machine actions now use allowlisted `systemctl reboot` and `systemctl poweroff`
after the existing double inhibitor/update checks, transition lock, exact Hub
recovery and zero-machine proof. `systemctl --help` on the target confirms both
verbs perform full machine shutdown/reboot.

The daemon now launches the oneshot runner with `systemd-run --no-block`, so it
can acknowledge confirmation before recovery closes Quickshell. A disconnected
client can no longer terminate the authority through `BrokenPipeError`. The
installed source matches the repository, 20 focused tests pass and pre-change
copies are under
`/var/lib/apx/backups/20260803-system-power-final-verbs-v3`. The current daemon
process intentionally retains its old socket until the terminal reboot; it
loads the installed asynchronous correction automatically after that boot. Its
runner path is already live and contains the corrected real reboot/poweroff
verbs for the pending button proof.

## Successful real reboot and clean terminal handoff

The owner then pressed `REINICIAR` and the machine crossed a real boot boundary.
The journal records systemd-logind announcing the reboot and the boot ID
changed. The corrected daemon loaded on the new boot, so the previous behaviour
where only the Environment closed is no longer the current implementation.

The final runner invocation now uses `systemctl --no-block reboot` and
`systemctl --no-block poweroff`. This leaves the already-validated inhibitor,
update, transition-lock, exact recovery and zero-machine sequence unchanged,
but lets the oneshot return cleanly after handing the terminal action to PID 1
instead of being killed as shutdown starts. Suspend remains `loginctl suspend`.
Repository and installed runner hashes match at
`0854c965a44202d0a42558859279e0fa8948588032b7ac53943a107659795c37`;
the focused secure-boot, physical-power and graphical-launcher suite passes 24
tests. The pre-change runner is retained under
`/var/lib/apx/backups/20260803-system-power-clean-exit-v4`.
