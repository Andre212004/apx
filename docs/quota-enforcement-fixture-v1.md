# Btrfs Quota Enforcement Fixture v1

Status: manually executed leaf-limit fixture passed on 2026-07-12; logical
deletion completed and Btrfs metadata cleanup remains pending. No APX
Environment was created.

## Scope

The user explicitly authorized one temporary custom qgroup enforcement test.
The fixture created the new Btrfs subvolume
`/home/apx-development/apx-quota-fixture-v1`, owned by UID/GID `1002:1002` with
mode `0700`. The automatically assigned leaf qgroup is `0/263`.

A maximum referenced limit of 67,108,864 bytes (64 MiB) was applied. No parent
qgroup, APX hierarchy, account, registration, service, package, or Environment
was created.

## Result

An 80 MiB sequential write was attempted as `apx-development`. Btrfs stopped
the write with `Disk quota exceeded`; the command returned non-zero. The file
reached 67,076,096 bytes and the qgroup reported 67,092,480 referenced and
exclusive bytes, below the 67,108,864-byte limit.

Afterwards, quota status reported:

- traditional full qgroup accounting enabled;
- accounting not inconsistent;
- limit override disabled;
- nine automatic level-0 qgroups.

This proves enforcement for one leaf subvolume on the current filesystem. It
does not yet prove hierarchical inheritance, parent pool limits, snapshot
charging, metadata-pressure behaviour, concurrent writers, restart recovery,
or executor-owned evidence.

## Cleanup State

The user separately approved cleanup, removed the test file, and requested
subvolume deletion by the exact path. The path is absent. Btrfs still reports
subvolume ID `263` as `DELETED` and qgroup `0/263` as `<under deletion>` with
16,384 referenced and exclusive bytes. Quotas remain enabled, full,
consistent, and without limit override; no kernel error was observed.

This is not complete cleanup under `cleanup-completion-v1.md`. The remaining
identity stays pending and must not be manually broadened into unrelated
deletion authority. Completion requires both the deleted-subvolume record and
qgroup to disappear, followed by fresh quota and free-space observation.
