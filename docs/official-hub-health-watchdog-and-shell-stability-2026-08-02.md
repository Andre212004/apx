# Official Hub health watchdog and shell stability — 2026-08-02

## Result

The official Hub interactive launcher no longer ends a healthy session after a
fixed four-hour lifetime. Interactive sessions now use an independent Host
health watchdog: the first check runs after 60 seconds and subsequent checks
run every 30 seconds.

A healthy check requires the exact Hub registration and active-session state,
the outer unit, nspawn machine and inner compositor unit, the expected
Hyprland process and control socket, enabled `eDP-2`, and the admitted keyboard
devices. Healthy checks clear prior failure state. An unhealthy active session
must fail three consecutive checks before recovery, avoiding teardown for a
single transient observation. A stopped session is classified inactive rather
than treated as a failure.

The bounded `--test` path deliberately retains its independent 75-second
expiry. This keeps physical certification bounded without imposing a lifetime
on normal owner sessions.

## Physical evidence

An interactive physical run on 2026-08-02 produced seven consecutive
`classification=healthy` results, from 16:59:04 through 17:02:11, at roughly
30-second intervals. The session then ended normally and the owner launcher
reported:

```json
{"classification":"session-ended","machine_residue":false,"owner_exit":true,"tty1_restored":true}
```

Final observation was `tty1`, stopped Hub, no watchdog timer or failure-state
file, and no seatd or device-lease residue.

The complete repository suite passes 905 tests with 11 skips.

The recovery service now explicitly permits writes to the exact
`/run/seatd.sock` path while keeping `ProtectSystem=strict`. This closes the
earlier recovery failure in which the service could not unlink the seatd
socket from its read-only filesystem view.

## Quickshell containment

The earlier apparent whole-Hub crash had two independent causes in the logs:

- the old launcher intentionally reached its four-hour expiry and recovered;
- Quickshell had separately terminated several times inside otherwise healthy
  Hyprland sessions, including Qt Wayland/Core stack traces.

The live Hub keeps the owner's current QML unchanged. Its shell runner now
uses `quickshell --no-duplicate`, records timestamped verbose output and exit
status under `~/.local/state/apx-shell-v1/quickshell.log`, rotates that log at
1 MiB, and executes Waybar as the fallback if Quickshell exits. A compositor
teardown was correctly recorded as a broken Wayland connection followed by
the fallback path. This contains a shell-process failure and preserves evidence
without claiming that the upstream Qt/Quickshell fault itself is fixed.

The Quickshell runner change is installed only in the live mutable official
Hub. It does not promote the experimental shell to the common graphical seed
or overwrite the owner's QML.

Installed/source official graphical launcher SHA-256:

`8e0d4e0dbde40f6dca496ae34a2d233235096531971bddf37983da63a60ce8d4`

Installed/source Quickshell runner SHA-256:

`c96816092296251547c08e9bac53f6f893fbf4044f953b6be7b774b94b1adba4`
