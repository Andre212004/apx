# Host connectivity and Fn repair v1 — 2026-08-31

## Reported failure and physical diagnosis

The owner reported that entering a Wi-Fi password from the Hub control centre
did not establish the connection, Bluetooth appeared not to work, and the
Lenovo `Fn+F1`--`Fn+F12` actions no longer responded.

The active Hub could read typed Wi-Fi and Bluetooth status through Host
services v3. A credential-channel probe passed a dummy passphrase through the
Hub client and Unix socket and received the expected typed rejection for an
absent SSID; the secret did not appear in an argument, file or journal. The
connection backend nevertheless returned success before the requested SSID
was explicitly re-observed, and its failure text did not distinguish a
rejected passphrase from the absence of a prompt.

The Bluetooth service and Realtek controller were present, but BlueZ reported
`PowerState: off-blocked`. The controller's `hci0` rfkill entry was soft
blocked. `bluetoothctl power on` consequently returned
`org.bluez.Error.Failed`, which is the same failure surfaced by the menu.

The QuickShell-owned Fn bridge was absent. Reproduction inside the active Hub
showed it terminating with `exact Lenovo internal keyboards are absent or
ambiguous`. Its required i8042 name was `AT Raw Set 2 keyboard`; the physically
leased normal input node is exactly `AT Translated Set 2 keyboard`. The ITE
device identity remained unchanged.

## Repair boundary

The Fn bridge now admits the physically observed translated i8042 name and the
same exact ITE device. It still refuses missing, duplicate or external
keyboards, does not use uinput and does not grab either keyboard exclusively.

Bluetooth power-on is now one verified Host transition: unblock only the
Bluetooth rfkill class, wait for BlueZ to leave `off-blocked`, ask it to power
the controller, then require the reported state to become powered within five
seconds. The service receives
only the additional `CAP_NET_ADMIN` capability required by `/dev/rfkill`; all
other service hardening and the existing typed Unix-socket boundary remain.
Wi-Fi rfkill state is not changed by this action.

Protected Wi-Fi continues to carry the passphrase only in the QuickShell
process pipe, v3 Unix-socket request body and a no-echo PTY connected to
`iwctl`. The bounded PTY transcript is capped at 16 KiB and is never logged.
The Host now distinguishes a missing credential prompt from authentication or
connection failure and accepts a connect operation only after iwd reports the
requested SSID as connected. Connectivity/portal classification runs only
after that confirmation.

## Rollout and recovery

The live Host-services socket is bind-mounted as one inode into the active Hub.
Restarting the service replaces that inode, so a complete live activation of
the new daemon requires a coordinated Hub relaunch. It must not be performed
silently while the owner may have unsaved applications. Code and unit files
may be staged first; the running daemon remains the prior version until that
coordinated relaunch or the next normal boot.

The Fn file can be updated in place and QuickShell alone restarted; its
supervised shell recreates the bar and bridge without ending Hyprland or other
applications. Bluetooth may be unblocked and powered for the current session
without restarting Host services. Exact pre-rollout files belong in one
root-only backup under `/var/lib/apx/backups`.

To recover, restore the saved Host daemon, systemd unit and Fn bridge, run
`systemctl daemon-reload`, and activate them at the next coordinated Hub
relaunch. Restoring the files does not disconnect Wi-Fi, forget networks,
remove Bluetooth pairings or alter the airplane-mode binding.

## Validation

The repository suite passes 1118 tests with 11 expected skips. Targeted tests
also assert rfkill-before-BlueZ ordering, requested-SSID confirmation, the
physical translated keyboard name, secure credential stdin, and the retained
service hardening. Physical acceptance requires:

1. the Fn bridge remains live and `Fn+F1/F2/F3` changes audio with OSD;
2. Bluetooth powers on from the menu and completes an eight-second scan;
3. an owner-known protected test network accepts its password from the inline
   field and the control centre reports the resulting SSID.

## Physical staged result

The first staging pass correctly refused acceptance because it checked BlueZ
immediately after rfkill returned. Rollback restored all three installed files;
the radio had completed unblocking asynchronously. The implementation and
deployer now wait for BlueZ to leave `off-blocked` before requesting power.

The second pass staged byte-identical daemon, unit and Fn files with backup at
`/var/lib/apx/backups/20260831T134617Z-host-connectivity-input-v1`. QuickShell
restarted without ending Hyprland or applications, and the Fn bridge remained
live as its own Python process. Through the exact Hub client used by the menu,
Bluetooth then powered off, powered on and completed an eight-second scan that
observed 15 unpaired devices. No device was paired or trusted. `Casa` remained
connected with full connectivity and the Host has no failed unit.

The current daemon process predates the staged bytes. Bluetooth works now
because its rfkill state is unblocked; the new general unblock/wait path and
the stricter Wi-Fi requested-SSID confirmation become active on the next
normal boot or an owner-coordinated Hub relaunch. Physical key presses and an
owner-known protected Wi-Fi password remain the two owner-observation checks.

## Fn-only follow-up

The owner then observed that plain F5/F6, and subsequently the rest of the row,
still ran laptop actions without Fn. The decisive capture showed why: the exact
ITE interface is a complete keyboard and emits ordinary F1--F12 too. Treating
its raw F codes as an Fn-only channel was incorrect. The firmware Fn lock is
already off (`fn_lock=0`).

The bridge now rejects every raw F1--F12 code. It accepts only semantic ITE
brightness codes 224/225 and exact AT Print Screen. Hyprland owns the other
semantic XF86 and observed F13--F16 Fn outputs; these mappings are required and
do not fire for ordinary F1--F12. Fn+F8 remains the Host kernel's rfkill path.
Media transport keys remain unrelated, and no input device is grabbed
exclusively.

The first live reload exposed two bridge processes: a previous QuickShell child
had survived its parent and continued running older code. The bridge now holds
a non-blocking runtime singleton lock, and deployment terminates an exact old
command before QuickShell restarts. The accepted live state has exactly one
bridge, semantic compositor bindings and matching source/installed shell
files; no systemd unit is failed. The immediate pre-rollout recovery set for
the combined correction is
`/var/lib/apx/backups/20260831T144833Z-fn-wallpaper-fullscreen-v1`. Physical
confirmation that plain F keys reach applications while Fn+F keys run the
Lenovo actions remains owner-observed acceptance. The complete repository suite
passes 1121 tests with 11 expected skips.
