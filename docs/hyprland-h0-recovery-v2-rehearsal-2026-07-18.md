# Hyprland H0 recovery v2 rehearsal — 2026-07-18

## Scope and result

Recovery v2 was rehearsed on the physical Host without Hyprland, GPU, input
devices, tty2, a container, or any APX Environment lifecycle operation. The
exact graphical unit name contained only `/usr/bin/sleep 300` under a closed
device policy. The independent Host timer was armed first with a 15-second
deadline.

The final rehearsal passed:

- expiry timer observed active before the dummy unit;
- exact dummy unit stopped on deadline;
- tty1 active after recovery;
- graphical, expiry-timer, and expiry-service units inactive;
- no H0 machine registered;
- no failed systemd units;
- watchdog output: `h0-watchdog: tty1-restored zero-residue`.

No physical graphical execution is authorized by this result. The launcher
remains code-locked.

## Useful failed rehearsal

The first rehearsal deliberately used the repository watchdog path below
`/root`. The timer had `ProtectHome=yes`, so systemd correctly could not access
that executable and returned `203/EXEC`. The dummy sleep unit was then stopped
through the exact manual recovery path, tty1 was selected, and the failed
transient service was reset. Zero residue was confirmed before retrying.

This failure establishes an important invariant: the independent recovery
executable must be staged and digest-verified under private APX Host state, not
executed from a protected home or development checkout.

## Successful staged identity

The successful rehearsal used the preserved private file:

`/var/lib/apx/h0/h0-recovery-v2-rehearsal/watchdog`

Its SHA-256 matched the reviewed repository script:

`5c7d63bb2dd505f7f1c916fa1d3dd3083c4f8e591e11d2514424e2e2af7402e9`

## Remaining block

Before another physical graphical run, the exact staged recovery-v2 assets and
plan must be reviewed again. The physical launcher interlock must remain false
until that explicit code change is separately justified and tested. Ricing and
desktop appearance are intentionally outside this recovery gate.
