# APX Installation and Migration v1

Status: two-path installation proposal. The existing pure staged assessment
models in-place migration only; no clean installer, package change, graphical
cutover, or legacy cleanup is implemented or authorized.

## Objective

The preferred first functional APX installation starts from a fresh minimal
Arch host with no KDE, Hyprland, SDDM, display manager, or graphical session.
It proves the APX bootstrap, headless Hub CLI, headless Development Environment,
cross-Environment denial, local package installation, lifecycle, storage, and
recovery before adding Hyprland or graphical controls. The complete order is in
`headless-bootstrap-and-cli-first-v1.md`.

Introducing APX beside an existing KDE session remains a secondary migration
campaign. KDE and its packages remain a separately reviewed cleanup scope.

Both paths preserve an independent recovery surface. A clean install uses a
physical text console; an in-place migration retains the existing desktop until
its handoff gates pass. Neither path converts unfinished APX into the only way
to repair the computer.

## Preferred Clean Headless Path

1. Verify repository history, personal backup, and bootable recovery media.
2. Install and verify a minimal Arch host without a graphical stack.
3. Acquire a pinned APX source/release and build a reviewed artifact; do not run
   an arbitrary Git checkout as a root installer.
4. Preview and apply only the typed minimal APX bootstrap effects.
5. Create and recreate a headless Hub with the bounded `apx` CLI.
6. Create a separate headless Development Environment containing Git, Codex,
   compilers, tests, source, and build outputs.
7. Prove Environment-local packages, two-Environment isolation, lifecycle,
   storage, reboot, incomplete-operation recovery, and deletion.
8. Prove non-graphical daily operation and physical-console recovery.
9. Run H0, the first-graphical-session campaign, from a verified state with no
   display manager or graphical owner.
10. Add Hyprland controls and an optional graphical Hub only after the CLI path
    remains independently usable.

No phase authorizes disk formatting, package installation, or host mutation on
the current machine. A future clean-install dossier must bind the exact target,
backup, disk plan, package manifest, artifact, effects, and recovery route.

## Secondary In-Place KDE Migration

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
storage. For in-place migration, the current graphical session remains
selectable until APX graphical and rollback gates have passed. For a clean
headless install, the physical text recovery surface and boot media remain
usable until H0 and return to the headless Hub pass.

## Legacy Cleanup

Cleanup never means "remove everything that looks like KDE". A future preview
classifies packages and files as APX-required, host-required, user data,
legacy-desktop-specific, shared dependency, or unknown. Unknown and shared
items are preserved. Boot, kernel, firmware, networking, storage,
authentication, recovery, APX source, and personal data are excluded.

Even complete APX validation produces only `cleanup-review-only`. A human must
approve the exact classified removal plan separately.

## Implemented Contract

`src/apx_installation.py` contains the deterministic in-place plan, evidence
gates, phase assessment, and plain-language renderer. It has no commands, paths
to mutate, package list, or apply mode. It cannot install APX, perform the new
clean bootstrap, or remove KDE.
