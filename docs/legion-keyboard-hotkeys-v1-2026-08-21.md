# Lenovo Legion keyboard hotkeys v1 — 2026-08-21

## Owner-visible behavior

This target-bound profile follows Lenovo's documented Legion 5 15ACH6H hotkey
row. Lenovo documents F7 as display switching, F9 as the Lenovo application
panel, and F11 as the open-application overview. APX maps those Windows-oriented
actions to their Environment-local Linux equivalents:

- Fn+F1 mutes output audio; Fn+F2/F3 lower/raise it; Fn+F4 mutes the microphone;
- Fn+F5/F6 lower/raise the internal display brightness through the existing
  Host-mediated brightness control;
- Fn+F7 cycles connected screens through extended, mirrored, external-only and
  laptop-only layouts; with no external screen connected it changes nothing;
- Fn+F8 remains the kernel Lenovo `KEY_RFKILL` path and toggles the soft block
  for the exposed Wi-Fi and Bluetooth radios;
- Fn+F9 opens the Environment application launcher, the closest APX equivalent
  to the Lenovo Vantage/application panel;
- Fn+F10 enables or disables the exact internal ELAN touchpad;
- Fn+F11 opens the Environment window overview. The current base uses Rofi's
  window list rather than thumbnail rendering because no overview plugin is
  part of the reviewed base;
- Fn+F12 opens the first supported calculator installed in that Environment and
  safely does nothing when none is installed;
- Print Screen writes a timestamped PNG below `~/Pictures/Screenshots`;
- Insert, Delete, Home, End, Page Up and Page Down are not compositor shortcuts
  and continue to reach the focused application normally.
- Two-finger touchpad scrolling is natural: dragging upward moves down through
  the page, as requested by the owner.

Every handled action now presents one compact bottom-centred QuickShell OSD.
The surface is translucent, stays above applications without taking keyboard
focus, fades after 1.5 seconds, and shows a progress bar for volume, microphone
level and display brightness. Binary actions state explicitly whether they are
active, disabled, unavailable or completed. The shell reads kernel rfkill soft
blocks directly from read-only sysfs, so Fn+F8 gets accurate **Modo de avião ·
Ativado/Desativado** feedback even if a Host-service socket is replaced. A typed
read-only Host `radio.status` view is also available to other consumers. Neither
path gives an Environment radio mutation authority.

The bindings accept both the standard `XF86` key symbols and the F13--F16
fallback symbols emitted by some firmware paths on this exact Legion
generation. Fn+F8 is deliberately not reimplemented in the Environment: the
Host kernel already owns the separate Lenovo radio-control input and its rfkill
handler, which avoids granting an Environment direct radio authority.

The physical target's observed route is more specific: a live evdev capture
showed Fn+F4--F12 on the exact internal ITE keyboard as raw codes
`62--68,87,88`. Plain F4--F12 arrive through the separate exact AT keyboard.
The bridge exclusively grabs the ITE interface and also handles its raw
F1--F3 codes `59--61` for volume. This prevents Fn codes leaking into focused
applications while leaving ordinary AT F1--F12 untouched. Print Screen is
handled as AT `KEY_SYSRQ/99`. The raw F8 copy asks
for delayed read-only rfkill feedback after the Host kernel performs the actual
toggle; the raw F10 copy reports the firmware-owned touchpad state change.

The first physical trial found F1--F4 and F8 working but no F5/F6 response. A
direct mediated proof changed the AMD backlight from raw 65535 to 62258 and
back to 65535, isolating the problem to key routing rather than the Host
brightness service. The firmware can send either F5/F6 or brightness codes
224/225 through either exact internal AT or ITE descriptor. The bridge now
accepts those four codes from either of those two already identity-checked
descriptors; it still refuses external and ambiguous keyboards.

Lenovo reference:
<https://download.lenovo.com/pccbbs/pubs/legion_5_15imh6/html_en/EN/SHARED_feature_intro_hotkeys_legion_5.html>

## Scope and recovery

Screen layout, application launching, touchpad state, window selection,
calculator launch and screenshots are Environment-local. Audio and brightness
retain their existing APX mediation. The shared source and installed seed make
the behavior available to newly created graphical Environments; existing
Environment homes must receive the same three reviewed files explicitly.

To roll back, restore the prior `hyprland.lua`, remove
`~/.local/bin/apx-laptop-action-v1`, and reload or restart the Environment's
Hyprland session. This does not alter firmware, the physical FnLock setting, or
the normal application-level navigation keys.
