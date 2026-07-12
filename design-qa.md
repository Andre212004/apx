# APX Hub Prototype Design QA

- Source visual truth: `prototypes/hub-demo/reference/taskbar-target.png` and
  `prototypes/hub-demo/reference/management-target.png`
- Implementation screenshots:
  `prototypes/hub-demo/screenshots/taskbar-open-final.png`,
  `prototypes/hub-demo/screenshots/management-final.png`, and
  `prototypes/hub-demo/screenshots/management-1024-v2.png`
- Full-view comparison evidence:
  `prototypes/hub-demo/screenshots/compare-taskbar-final.png` and
  `prototypes/hub-demo/screenshots/compare-management-final.png`
- Focused comparison evidence:
  `prototypes/hub-demo/screenshots/focus-switcher-v2.png`; the subsequent
  compact-list fix is visible in `taskbar-open-final.png`
- Primary viewport: 1440 × 1024
- Responsive viewport: 1024 × 768
- States: Environment switcher open and full management view

## Findings

No actionable P0, P1, or P2 findings remain.

- Fonts and typography: the implementation uses the installed Adwaita Sans/Noto
  Sans stack and preserves the target's clear display/body hierarchy. Portuguese
  labels remain readable without clipping at both tested viewports.
- Spacing and layout rhythm: the taskbar, file window, attached vertical
  switcher, management sidebar, grouped Environment rows, and approved-model
  section follow the source hierarchy. The compact switcher now matches the
  target density and contains exactly five choices.
- Colors and visual tokens: off-white surfaces, deep ink, restrained teal,
  semantic green, warning amber, borders, and low elevation match the selected
  calm visual direction with accessible contrast.
- Image quality and asset fidelity: the wallpaper is a dedicated generated
  raster asset at the target aspect. All visible application, Environment,
  action, window, and tray icons come from the installed KDE Breeze icon theme;
  none are handcrafted SVG/CSS substitutes.
- Copy and content: the desktop is clearly labelled as a demonstration. The
  switcher is deliberately terse; full descriptions and destructive warnings
  live in contextual/full-management flows.
- Interaction and accessibility: native buttons/dialogs, keyboard focus,
  Escape, Shift+F10/context-menu access, labels, reduced-motion handling, and
  blocked warning state are present. Browser self-test passed with zero captured
  JavaScript errors.

## Comparison History

1. Initial pass — P1: Development was marked as requiring verification while
   still exposing Open and destructive context actions.
   Fix: warning state now exposes Verify and Details only; left-click routes to
   verification instead of transition.
   Evidence: `management-final.png`.
2. Initial pass — P2: management header wrapped and visually overlapped at
   1024 × 768 during entry animation.
   Fix: responsive header stacks, action buttons share the available row, and
   page margins/type scale reduce at the breakpoint.
   Evidence: `management-1024-v2.png`.
3. Focused pass — P2: Environment switcher was wider and denser than the target
   because every choice included secondary descriptive copy.
   Fix: switcher reduced to 235 px and now displays icon, name, and state only;
   details remain available on right-click.
   Evidence: `taskbar-open-final.png`.

## Open Questions

- The real Hyprland taskbar technology and compositor integration are not
  selected. This prototype validates interaction and appearance only.
- The management view intentionally shows five Environments rather than the
  three visible in the original management mock because the user explicitly
  requested approximately five daily switch targets.

## Implementation Checklist

- [x] Left-click APX control expands exactly five Environment choices.
- [x] Right-click APX control exposes create, archived, and full management.
- [x] Right-click Environment exposes safe contextual actions.
- [x] Warning state fails closed.
- [x] Create/delete flows remain visibly demo-only.
- [x] Full management follows the selected light direction.
- [x] 1440 × 1024 and 1024 × 768 layouts verified in Brave.
- [x] Browser interaction self-test passed with zero captured errors.

## Follow-up Polish

- P3: replace the temporary generic APX Breeze activity icon after an APX brand
  mark is designed and approved.
- P3: refine exact taskbar spacing after the real Hyprland bar implementation is
  selected.

final result: passed
