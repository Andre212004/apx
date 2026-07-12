# APX Installation and Migration v1

Status: pure staged installation contract implemented; no installer, package
change, graphical cutover, or legacy cleanup is implemented or authorized.

## Objective

APX is introduced beside the current working KDE session. It first proves one
headless Environment, cross-Environment denial, the Hub, graphical handoff,
application installation isolation, and destructive recovery. Only then may it
be offered as the default session. KDE and its packages remain a separately
reviewed cleanup scope.

This avoids converting an unfinished APX experiment into the only way to use or
repair the computer.

## Fixed Phases

1. Inventory the current system without changing it.
2. Verify a restorable personal backup and bootable Arch recovery media.
3. Bootstrap APX in parallel while preserving the current desktop.
4. Validate one bounded headless Environment.
5. Validate two-Environment isolation and hostile denial tests.
6. Validate the Hub and graphical handoff beside KDE.
7. Validate an application installed in exactly one Environment.
8. Validate incomplete-operation recovery and separately approved deletion.
9. Make APX eligible to become the default while retaining KDE recovery.
10. Render an optional package-by-package legacy cleanup review.

No phase inherits destructive authority from an earlier phase.

## Recovery Before Bootstrap

The project history must exist on a separately reachable remote. Personal
backup is not considered verified merely because files were copied; a sample
restore must succeed. Arch recovery media must boot and reach the installation
storage. The current graphical session remains selectable until APX graphical
and rollback gates have passed.

## Legacy Cleanup

Cleanup never means "remove everything that looks like KDE". A future preview
classifies packages and files as APX-required, host-required, user data,
legacy-desktop-specific, shared dependency, or unknown. Unknown and shared
items are preserved. Boot, kernel, firmware, networking, storage,
authentication, recovery, APX source, and personal data are excluded.

Even complete APX validation produces only `cleanup-review-only`. A human must
approve the exact classified removal plan separately.

## Implemented Contract

`src/apx_installation.py` contains the deterministic plan, evidence gates,
phase assessment, and plain-language renderer. It has no commands, paths to
mutate, package list, or apply mode. It cannot install APX or remove KDE.
