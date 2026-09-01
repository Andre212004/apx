# Environment landscape wallpaper and desktop controls v1 — 2026-08-31

## Owner-visible result

Every graphical APX Environment now uses the same project-owned set of three
landscape wallpapers: an Atlantic coast, an alpine lake and a rainforest
stream. QuickShell owns one non-interactive background layer per screen and
selects a new image every 15 minutes. The seed and the existing Hub, Hytale,
Steam, Minecraft and Faculdade homes contain byte-identical assets, so both
current and newly created Environments receive the behavior.

`SUPER+F` toggles real Hyprland fullscreen. `SUPER+P` requests the private file
manager only in workload Environments. The Hub refuses that request and its
Thunar package was removed; the workload roots retain Thunar. The Hub continues
to expose its Host terminal, now labelled only `Terminal do Host`.

The Central de Controlo uses text instead of icon components. Its top-level
Wi-Fi, Bluetooth, volume, microphone and keyboard actions expose no ON/OFF
badges. Their background and border colours communicate inactive, active and,
where applicable, low/medium/high state. The later owner refinement keeps this
card-level colour state only for microphone and keyboard. Wi-Fi, Bluetooth,
volume and display brightness now use the neutral card style; their interactive
details and sliders still expose the actual values. The keyboard action remains
labelled only `TECLADO`, with no level number or intensity name; clicking it
still cycles the light. The separate transient hotkey OSD is outside the menu
and keeps its feedback role. Wi-Fi and Bluetooth use the compact 46-pixel
summary row instead of the earlier oversized 82-pixel row.

Session actions use a consistent visual order: neutral `Bloquear` and
`Reiniciar`/`Ficheiros` actions occupy the first row; coloured `Update`/`Apps`
and destructive `Desligar`/`Voltar` actions occupy the second row. Their final
geometry matches the other control cards: 40-pixel height, 10-pixel radius,
one-pixel border and the shared body typography. A dedicated 9-pixel gap moves
the `AÇÕES DA SESSÃO` caption away from the preceding Host controls.

The top bar now has equal 5-pixel left and right margins. This reduces its
horizontal span by 10 pixels and guarantees the same visible clearance at both
screen edges. Within the bar, Calendar has a further 5-pixel left inset and
the right-side IA/Battery/Control Centre group has a 5-pixel right inset. The
Calendar (`SUPER+D`), Environments (`SUPER+E`), IA/model
(`SUPER+I`), Battery (`SUPER+B`) and Control Centre (`SUPER+A`) buttons all
derive their active state from the currently visible popup. Opening any of
those menus from its keyboard shortcut therefore drives the same opacity and
scale animation as clicking the corresponding bar button. The animation keeps
each button's complete normal label; only the established Control Centre cue
changes from `[|]` to `[A]` while its menu is open. The final motion is subtle:
a 6% scale transition with cubic easing and no overshoot. Opening animates only
the selected button. Dismissing a menu elsewhere or changing to another menu
resets the previous button immediately; pressing the already-active button or
shortcut again closes its menu with the matching reverse animation. Activation
is armed before popup visibility changes, so both opening and deliberate
same-button closing animate rather than only the closing transition.
Bar-button hover uses a passive pointer handler rather than
`MouseArea.containsMouse`. A selected button also remains visually active while
its menu is open, so opening the separate popup surface cannot make a stationary
cursor appear to have left the button.
Clicks use a sibling `TapHandler`, so the first click on an already-active
button reaches its toggle even after popup focus/hover transitions and closes
the menu immediately; it does not require a focus-recovery click.
Mouse and IPC openings now both request exclusive layer-shell keyboard focus
for the menu lifetime, so Calendar and Environments accept arrows, Tab and
Enter immediately after a bar click. A transparent non-keyboard Top-layer
surface covers the application area below the Overlay menu and closes the
popup on the first outside click; the bar is outside that surface and keeps its
direct toggle behavior. `HyprlandFocusGrab` remains a secondary cleanup
boundary rather than the only outside-click mechanism.
All top-level QuickShell menus and the bar use the same `#e60a1014` surface,
equivalent to 90% alpha, with a one-pixel `#26343a` border. Internal cards
retain semantic state colours, while Control Centre button surfaces use the
same neutral dark palette as the other menus instead of saturated blue.

Application windows use the same one-pixel opaque `#26343a` border as the
QuickShell bar. Active and inactive windows deliberately share that neutral
border, replacing the former cyan/green active gradient around terminals and
other applications.

## Implementation and recovery

The wallpaper layer and menu live in
`config/environment-shell-v1/quickshell/apx/shell.qml`; the fullscreen and file
manager bindings live in both reviewed Hyprland configurations. The graphical
seed manifest authenticates all three PNGs with a dedicated 4 MiB per-wallpaper
limit while ordinary configuration assets retain their 1 MiB limit.

The immediate pre-rollout backup is root-only at
`/var/lib/apx/backups/20260831T144833Z-fn-wallpaper-fullscreen-v1`. It contains
the previous shell/configuration files and the exact Hub Thunar package. Restore
that set and reinstall its package only if the owner explicitly requests a
rollback.

## Validation boundary

Repository tests cover the semantic Fn route, wallpaper manifest and rotation,
text-only keyboard action, Hub refusal of `openFiles`, workload file-manager
availability, both fullscreen bindings, symmetric bar margins and all five
popup/button active-state mappings. They also cover opaque menu colour,
exclusive keyboard focus and the outside-click dismissal layer. Physical owner
acceptance remains the final check for each key chord and pointer interaction.
The complete repository suite passes 1124 tests with 11 expected skips. The
visual wallpaper layer was captured in the active Hub; an earlier final menu
capture was interrupted by the normal protected session lock and no
authentication bypass was attempted.
