# Environment shortcut popup and return hotfix — 2026-08-14

## Observed failure

The owner reported that `SUPER+A`, `SUPER+B`, `SUPER+D` and `SUPER+E` appeared
to do nothing, then became trapped in the pre-change `faculdade` Environment
because its **Voltar ao Hub** control was disabled.

The four bindings were present in both the loaded Lua configuration and
Hyprland's live bind catalogue. Directly invoking their exact `hl.exec_cmd`
payload reached QuickShell, but `popupStatus` returned the requested kind with
`visible:false`. QuickShell logged the decisive Wayland error: it could not
create a grabbing popup because the parent had not received input. IPC-launched
commands have no pointer input serial, so `PopupWindow.grabFocus: true` mapped
and immediately dismissed each menu. This was a popup-focus defect, not a
missing SUPER modifier or missing binding.

## Repair

The shell now uses Quickshell 0.3's Hyprland-native focus grab:

- `PopupWindow.grabFocus` is false, avoiding the input-serial requirement.
- `HyprlandFocusGrab` owns `[bar, popup]` while the popup is visible.
- The former full-screen transparent dismissal `PanelWindow` is removed.
- A genuine click outside clears the focus grab and closes the popup.

This follows the upstream Quickshell guidance for Hyprland popup dismissal:
`https://quickshell.org/docs/v0.3.0/types/Quickshell.Hyprland/HyprlandFocusGrab/`.

The return control no longer depends exclusively on the Host-authorized
identity becoming ready. Presence of the Host-console socket proves the
official Hub locally; the socket is never mounted into workloads. While a
workload identity is still publishing, **Voltar ao Hub** stays enabled and
uses `hyprctl eval hl.dsp.exit()` as a bounded local fallback. The existing
Host handoff supervisor remains responsible for cleanup and Hub restoration.
Once identity is ready, the normal authenticated Host-driven return remains
preferred.

## Physical result

The owner was already restored from `faculdade` to the exact Hub by the
existing supervisor. The corrected QML loaded successfully in the live Hub.
Exact compositor-launched proofs left each popup visible:

- `toggleControls`: `kind=controls`, `visible=true`
- `toggleCalendar`: `kind=calendar`, `visible=true`
- `toggleBattery`: `kind=battery`, `visible=true`
- `openEnvironments`: `kind=environments`, `visible=true`

The same QML is installed in the current Hub, the existing `faculdade` Home,
and the reviewed seed for future Environments. Pre-change copies are under
`/var/lib/apx/backups/20260814-shortcuts-return-hotfix-v1/`.
