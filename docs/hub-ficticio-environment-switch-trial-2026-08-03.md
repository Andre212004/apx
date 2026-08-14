# HUB fictício Environment-switch trial — 2026-08-03

## Current physical state

The disposable graphical Environment `hub-ficticio`, generation
`441ed74c-c89f-47ae-8102-1ce3e09e6b47`, was created through the normal APX
planned lifecycle from the immutable `hyprland-base-v1` release. It has an
independent writable root and home and follows coordinated Host updates by
default. Quickshell 0.3.0 and its six missing dependencies were installed only
in that Environment through root-owned operation-private package staging; the
staging was removed after the successful transaction.

The workload uses a repository-authored red QuickShell profile. Its centre
label identifies `HUB FICTICIO`, its borders and shell accents are red, and a
persistent footer says that it is a workload without Hub privileges. The only
APX mutation exposed by that shell is return to Hub. Host console, coordinated
update and physical-power sockets are not mounted or leased to the workload.
Shared network/Bluetooth/audio services retain the already accepted active-
Environment policy.

`apx-environment-switch-v1` is installed and enabled on the Host. Its Unix
socket is root-only while inactive and leased to only the translated user of
the active graphical Environment. It accepts no names, paths, commands or
arguments from the caller. The fixed trial supports Hub-to-`hub-ficticio` and
self-generation return-to-Hub only. It validates the exact active registration,
private user namespace, graphical unit and direct QuickShell ancestry. A Host
supervisor owns the full Hub -> workload -> Hub sequence and proves tty1 with
zero machines between owners.

The official Hub was safely relaunched once so the new socket and fixed client
could be mounted at session creation. It returned on tty2 with the same Hub
generation. An out-of-Environment Host-root client was refused, while a Hub
user status call returned `active=hub`, `handoff_running=false` and the fixed
workload name.

## Owner trials and recovery correction

The owner confirmed a real transition into `hub-ficticio`. The intermediate
tty1 presentation was rough and the workload appeared to be only a terminal.
Return was not usable: `Super+M` was absent from the old common config, while
the emergency binding was `Super+Shift+E`; the automatic Alacritty certification
window also covered the red shell. The owner rebooted after 58 seconds. Boot
restored the official Hub, but the interrupted supervisor left the workload
registration stale as `running`; no workload machine or active-session record
survived.

The stale registration was safely reconciled to `stopped`. The installed
general launcher suppresses its automatic terminal proof for the red trial.
A second owner attempt reached the workload but exposed errors and still did
not produce a usable return; the owner powered off after about 24 seconds.
Post-boot reconciliation again left the Hub healthy, the workload stopped and
no fake machine or active record. The workload QuickShell journal itself showed
a successful configuration load. A subsequent isolated Hyprland validation
identified the visible errors: the compact single-line `blur` and `shadow`
blocks were not valid for this installed Hyprland parser. Both are now regular
multiline blocks and the same validator reports `config ok`.

Return no longer depends on the switch socket or client. The centre button and
`Super+M` now exit only the workload's own Hyprland; the already waiting
Host-owned supervisor then performs exact cleanup and restores the Hub.
`Super+Shift+E` remains the second local exit. In addition, every trial arms an
independent 120-second Host timer which recovers the fixed workload even if all
workload controls fail. The tty1 login/diagnostic text is cleared after each
recovery and replaced by a small APX transition page before the next graphical
owner starts.

Boot-time Hub entry reconciles an interrupted `hub-ficticio`, waits for all
eight required Host sockets and `/run/apx` is now created by tmpfiles before
normal services. These changes remove both the observed boot socket race and
the possibility that another failed trial requires a hard power-off. The new
round trip still needs one owner test; entry is physically proven, while clean
workload-to-Hub return remains implemented and safety-bounded but not yet
owner-certified.
