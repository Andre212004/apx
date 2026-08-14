# Environment menu input and control-centre repair — 2026-08-14

## Reported regression

After the first popup-focus repair, the menus could be opened but the owner
could not use the mouse or keyboard inside them. The Control Centre also
duplicated the shortcut toggle and exposed too many unrelated actions in one
flat list. The status icons appeared soft on the 150% display.

## Repair

- The shared menu is now a focused `PanelWindow`, with `OnDemand` keyboard
  focus and a compositor focus grab for outside-click dismissal. This avoids
  the input-serial requirement of an IPC-opened xdg popup.
- `Atalhos APX` is now a real `shortcuts` module in Environment creation. Its
  detail lists the four global actions: `SUPER+A/B/D/E`. Intermediate and
  Complete select it by default; Basic remains minimal.
- The duplicated shortcut switch was removed from the Control Centre, leaving
  the session actions grouped under a compact heading.
- Control icons keep the native Adwaita symbolic SVG source and render at an
  integer 18px-or-larger target instead of scaling the entire popup fractionally.

## Live proof

The current Hub layer catalogue reports the popup at `x=928, y=98, w=340,
h=440`, in the QuickShell layer above the bar. The repaired QML is byte-identical
in the source, Hub, `faculdade`, and future Environment seed. The full suite
passes with 1032 tests and 11 expected skips.
