# Waybar ASCII v1 physical result — 2026-07-31

## Scope

This checkpoint records the owner-authorized Hub Waybar correction, the
reviewed reusable profile, playback-audio mediation, and creation of one
independent disposable graphical Environment. It does not claim that the APX
graphical handoff or Bluetooth mediation is complete.

## Hub result

The live authoritative Hub keeps its independent owner configuration. Its
Waybar now starts with Hyprland and uses the reviewed Hub profile: date on the
left, the ASCII APX control in the centre, and volume, private network,
Bluetooth status, and battery on the right. Hub has no workspace selector.

The exact-generation physical launcher now leases only the target-bound
internal analogue playback nodes and timer. It does not lease the capture PCM.
The Environment starts its own PipeWire, WirePlumber, and Pulse compatibility
service. A bounded launch returned `classification=verified`, Waybar true,
audio playback true with a readable default-sink volume, Hyprland and kitty
true, all expected input identities, tty1 restored, and no machine residue.

The network module is intentionally bound to `host0`. It reports the
Environment's private Host-mediated network as `[ NET ]`; it does not pretend
that an Environment owns or reconfigures the Host's physical Wi-Fi adapter.

Bluetooth remains display-only and unavailable. The physical `hci0` sysfs
identity is globally visible across the shared kernel and there is no admitted
exclusive, revocable controller lease or mediator. No raw controller access,
Host daemon sharing, or broad device permission was added.

## Reusable profile

`config/waybar-ascii-v1/` contains two reviewed independent defaults:

- `hub-config.json`: the Hub layout without workspaces;
- `environment-config.json`: the same layout with the Hyprland workspace
  selector immediately to the right of the date;
- `style.css`: the common monochrome ASCII presentation.

This is the source profile for a future admitted graphical-base revision. It
does not mutate immutable `hyprland-base-v1`, and the mutable live Hub is never
used as a template.

## Independent fixture

`codex-test-waybar-v1`, generation
`1df14250-c628-49d4-961e-44ad22fd67a4`, was created from immutable
`hyprland-base-v1`. It is stopped and independently owns its root and home. Its
local Waybar copies exactly match the reviewed Environment profile and include
five persistent numbered workspace buttons.

## APX button boundary

Both profiles define the visual APX button and only invoke the fixed local
client path `/usr/bin/apx-hub --switcher`. That client is not installed in the
current official Hub or base release. The currently installed graphical
executor/effect prototype is stale and fixed to the preserved old
`hub-testes` and `test` generations. Therefore the button is not described as
working and no direct `systemctl`, `machinectl`, arbitrary command, or Host
path was added to Waybar.

The pure fixture catalogue in `src/apx_waybar_ascii_fixture_handoff.py`
defines the two future buttons without applying effects. The exact authoritative
Hub gets only `Abrir WAYBAR TEST`, bound to activation of generation
`1df14250-c628-49d4-961e-44ad22fd67a4`. That exact workload gets only
`Voltar ao HUB`, bound to stopping its own generation. Stale, inactive,
unauthenticated, or non-authoritative requester evidence is refused.

The next implementation milestone is a new typed handoff bundle bound to the
authoritative Hub generation and chosen target generation: client, immutable
or reviewed overlay, session descriptor, Unix socket, Host broker/effect
adapter, single-owner transition, watchdog, tty1 recovery, and a physical
round trip. Workload Environments may request only their own stop/return to the
Hub; only the authoritative active Hub may activate another Environment.

## Verification

The earlier `[ BT LOCKED ]` state in this dated checkpoint was superseded on
2026-08-01 by the authenticated Host BlueZ status and power-toggle mediator.
Wi-Fi status and NTP status are also now supplied by the Host endpoint. See
`docs/host-services-v1-architecture-and-result-2026-08-01.md`.

The complete repository suite passed 872 tests with 11 skips. JSON parsing,
Python compilation, `git diff --check`, the Waybar profile contract, audio
device bounds, Waybar readiness check, seed recovery, and exact fixture hashes
all passed. No commit or push was performed.
