# Coordinated updates and active audio physical result — 2026-08-03

The physical pilot now runs `apx-coordinated-update-v1` and
`apx-audio-state-v1` as enabled Host services. Both authenticate the exact
active official Hub user; direct Host callers were rejected. Existing
registrations without metadata follow the Host by default, creation records
`follow-host` unless `--exclude-host-updates` is selected, and an authenticated
policy operation records explicit exclusions.

The Hub `[ UPDATE ]` action opens a preview and requires the literal
confirmation `CONFIRMAR`. The installed runner freezes signed sync databases
in a root-controlled operation directory whose files remain root-only, resolves and verifies each target's own
packages, stops included Environments, snapshots Host and each Environment,
applies Host first and stops on the first failure while retaining status and
snapshots. It never provides a reusable shared cache or automatic reboot. The
preview passed physical authentication; no real package transaction or
rollback was executed, so destructive certification remains pending.

The exact ALC287 identity now resolves playback and capture nodes. Temporary
proxies belong only to the translated active user and are deleted on recovery.
The Hub's local PipeWire publishes exact analog sink/source nodes, restores the
root-owned volume/mute state, reports microphone activity once per second and
clears it on exit. The first proof correctly failed because proxies belonged
to translated root; fixing the actual ownership boundary produced a final
pass for audio, authenticated preview, Quickshell, graphics, input, shared Host
services, local admin and NVIDIA, followed by tty1 recovery with no residue.

This remains an exact-Hub pilot. Cross-Environment handoff and a real staged
package update need two admitted disposable graphical Environments and a
controlled failure proof before production promotion.

During the owner-authorized Host simplification on 2026-08-03, a retained
failed dry run exposed that pacman's unprivileged `alpm` downloader could not
traverse the private operation path. The coordinator and runner now give only
execute/traverse permission on the required parent directories (`0711`), while
plans, status and other operation files remain root-only (`0600`). A live
repository-only validation downloaded the signed `core.db` and `extra.db`
views successfully and then removed its temporary data; it installed no
package and did not stop the Hub. The failed dry-run residue was removed. The
already-running Hub must be relaunched once before its bind-mounted update
socket sees the restarted coordinator; subsequent Hub launches receive the
correct socket automatically.
