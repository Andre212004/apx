# APX Hub Demo

Static, dependency-free visual prototype. It uses only demonstration data and
does not import or call APX host code.

## Run

```text
python3 -m http.server 4173 --directory prototypes/hub-demo
```

Open `http://127.0.0.1:4173/`.

## Interactions

- Left-click the APX taskbar icon to expand five Environment choices.
- Right-click the APX icon for creation, archives, and full management.
- Right-click an Environment for recovery, archive, details, and delete flows.
- Use “Abrir gestão completa” for the selected light Hub management design.
- Add `?state=open` or `?state=management` for stable screenshot states.
- Add `?selftest=1` to execute the in-browser interaction smoke test.

The generated wallpaper is project-owned preview artwork. Icons are copied from
the locally installed KDE Breeze theme for prototype use.
