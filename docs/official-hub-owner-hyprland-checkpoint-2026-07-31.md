# Official Hub owner Hyprland checkpoint — 2026-07-31

This is the authoritative dated handoff for the owner-built Hyprland state of
the official Hub. Read it with `AGENTS.md`, `CURRENT_HANDOFF.md`, and
`PROJECT_STATE.md`. Earlier notes saying that the official Hub has no graphical
packages, that keyboard delivery is unproven, or that another physical launch
is blocked are historical and are superseded by this checkpoint.

## Current physical state

The canonical Environment remains:

- logical name: `hub`;
- role: `hub`;
- generation: `6f63f9a9-daea-40d1-969f-e25ff0752f4d`;
- immutable source release: `hub-headless-v4`;
- current live state at handoff: stopped.

The previous graphical Hub remains preserved and non-authoritative as
`hub-testes`, generation `2c3dbacc-106f-4053-8603-f649552f5513`. It was not
deleted or reused as the official Hub.

The owner completed local-admin enrollment for Environment user `apx`. The
official Hub is no longer a pristine live headless copy: the owner installed
and began configuring Hyprland in its mutable root/home. The immutable
`hub-headless-v4` source release remains unchanged.

At the final read-only check, the Host was on `tty1`, `hub` was stopped, there
was no running machine, `systemctl --failed` was empty, and registration state
was `stopped`.

## Owner-installed graphical state

The official Hub has Hyprland 0.56.1-2 and kitty 0.48.1-1, plus the supporting
packages the owner installed while following the official Hyprland tutorial.
Known supporting packages include Mesa, PipeWire components, portals,
`polkit-kde-agent`, Waybar, seatd, rofi, pavucontrol, and nano.

The owner configuration is inside the Hub at:

```text
/home/apx/.config/hypr/hyprland.lua
```

From inside the Hub it is edited as:

```bash
nano ~/.config/hypr/hyprland.lua
hyprctl reload
hyprctl configerrors
```

The configuration parsed successfully. Current important bindings are:

- `Super+Q`: open kitty;
- `Super+C`: close the active window;
- `Super+M`: end Hyprland and return to Host recovery;
- `Super+arrow`: move focus;
- `Super+1` through `Super+0`: select workspaces;
- `Super+Shift+1` through `Super+Shift+0`: move the active window;
- `Super+V`: toggle floating;
- `Super+S`: toggle the special workspace.

`Super+E` currently names Dolphin and `Super+R` names hyprlauncher, but those
programs were not installed at the checkpoint. Brightness and media bindings
also name optional commands that are not yet fully installed/mediated.

## Installed official-Hub graphical launcher

The current owner-development bridge is:

```bash
entrar_no_HUB
```

It must be run as root on the Host from safe console `tty1`; a non-root Host
account may use `sudo entrar_no_HUB`. It is not equivalent to running
`start-hyprland` directly. The bridge starts the exact official Hub generation,
attaches only the resolved built-in input identities, AMD card/render nodes and
`tty2`, starts Hyprland as Environment UID/GID 1000, opens kitty automatically,
and guarantees Host recovery.

Repository sources:

- `scripts/physical-pilot/apx-official-hub-graphical-v1.py`;
- `scripts/physical-pilot/apx-official-hub-session-v1.sh`;
- `scripts/physical-pilot/entrar_no_HUB`.

Installed Host assets:

- `/var/lib/apx/official-hub-v1/apx-official-hub-graphical-v1.py`;
- `/var/lib/apx/official-hub-v1/apx-official-hub-session-v1.sh`;
- `/usr/local/bin/entrar_no_HUB`.

The interactive watchdog is four hours. The bounded test mode is 75 seconds.
`Ctrl+Alt+F1` remains a visual emergency route to the Host, and cleanup selects
`tty1`, stops exact temporary units, removes Hub network policy, and records the
Hub stopped.

## Physical proof completed

The final bounded launch returned:

```json
{"classification":"verified","hyprland":true,"input_identities":["elan_mouse","elan_touchpad","keyboard_i8042","keyboard_ite"],"keyboard_count":2,"kitty":true,"machine_residue":false,"monitor":"eDP-2","tty1_restored":true}
```

The owner then used two interactive sessions and reported that the graphical
desktop, keyboard, pointer, kitty open/close bindings, and session exit all
worked. This supersedes earlier ambiguous zero-keyboard observations and the
old physical-graphics launch block for this official-Hub bridge. It does not
complete the separate APX Hub-to-workload button-switching milestone.

## Manual textual administration

For a terminal-only Environment session from the Host:

```bash
apx environment shell hub
```

This starts the Hub if needed and enters as Environment user `apx`, with clear
Host/Environment boundary banners. Leave it with `exit`, then stop the Hub when
finished:

```bash
apx environment stop hub
```

Inspect Environment state with:

```bash
apx environment list
```

Owner package management belongs inside the Hub, for example:

```bash
sudo pacman -Syu
sudo pacman -S <package>
sudo pacman -Rns <package>
```

Do not install Hub desktop packages on the Host. Do not launch Hyprland
directly from the textual shell, because that path does not receive the guarded
physical device lease.

## Intended final behavior versus temporary behavior

`Super+M` returning to the Host is temporary development/recovery behavior. The
owner explicitly decided that the normal final desktop must not expose
"return to Host" as an ordinary shortcut. Do not remove the current binding
yet: it remains the tested safe exit until final boot/session lifecycle and a
separate administrative recovery path exist. In the final design, Host access
must remain available for protected recovery but must not be part of the normal
Hub experience.

## Immediate next work

The owner may now develop the Hyprland desktop independently inside the Hub.
The next APX work should not replace or overwrite that mutable owner config.
Remaining integration items are:

1. define and implement final boot directly into the authoritative Hub session;
2. replace the temporary `Super+M` Host-return binding only after recovery is
   available outside the normal desktop UI;
3. mediate and validate audio and brightness hardware;
4. let the owner choose/install the launcher and file manager, then update only
   the corresponding owner bindings;
5. finish locale and optional portal/polkit user-session cleanup;
6. resume the separately scoped APX Hub-to-Environment button/effect work only
   after importing the owner's finished Hub design without using the live Hub
   as an Environment template.

No deletion of `hub`, `hub-testes`, `test`, releases, roots, homes, or rollback
state is authorized by this checkpoint.

## Repository verification

After the final kitty-dispatch correction, focused launcher tests, Python
compilation, shell syntax checks, and `git diff --check` passed. The complete
repository suite then passed:

```text
Ran 858 tests in 1.402s
OK (skipped=11)
```

The worktree remains intentionally dirty with the broader uncommitted APX
development sequence. Nothing was committed or pushed in this checkpoint.
