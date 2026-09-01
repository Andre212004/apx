# APX Hyprland H0 Environment Creation Contract v1

Status: repository runtime support, physical runtime update, and stopped
Environment creation completed on 2026-07-18. Graphical activation has not run.

## Practical meaning

The immutable `hyprland-h0-v1` release is the mould. The APX lifecycle must
recognize that mould before it can safely create a normal, disposable
Environment from it.

The new role is exactly `graphical-h0`. It maps only to
`hyprland-h0-v1`. Creation uses the existing generation-bound lifecycle:

1. create a writable Btrfs snapshot of the immutable release root;
2. create a separate writable home subvolume;
3. apply 16 GiB root and 8 GiB home limits;
4. write only the Environment hostname and empty machine identity;
5. publish one stopped registration bound to a new generation.

The first physical name is fixed to `codex-test-hyprland-h0-v1`. It is a
clearly disposable `codex-test-*` Environment and does not replace or modify
Hub or Development.

## Deliberate activation block

The ordinary headless `apx environment start` path does not admit
`graphical-h0`. It refuses before checking a machine, writing a journal event,
or starting a service. `apx environment shell` inherits the same refusal when
the Environment is stopped.

This is intentional. A graphical start must first have a separate H0 adapter
that binds the exact AMD device, built-in keyboard and touchpad, tty2 ownership,
watchdog, timeout, cleanup, and recovery-console checks. The generic container
start must never silently become a graphical-device grant.

## Physical sequence

Repository support alone does not change the Host runtime. The safe sequence
is:

1. build and verify a new exact Host-runtime update from the committed source;
2. import and activate it through the existing update/rollback contract;
3. reconcile Hub, Development, APX journal, quotas, and recovery state;
4. preview the exact stopped Environment creation;
5. create only `codex-test-hyprland-h0-v1` after the creation preview matches;
6. verify its release identity, generation, limits, isolation, and stopped
   state;
7. keep graphical activation blocked until the device/watchdog contract passes.

Runtime update, Environment creation, graphical activation, and later cleanup
remain distinct effects. A failure or uncertain result is preserved for
inspection; it is not automatically deleted or adopted.
