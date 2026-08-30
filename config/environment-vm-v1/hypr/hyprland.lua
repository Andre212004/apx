-- APX dedicated virtual-machine surface. Hyprland remains only as the
-- physical display/input boundary; the guest is the sole visible workload.
-- The physical Legion panel is 1920x1080 at 120 Hz. `highrr` keeps the APX
-- presentation boundary at the highest native refresh instead of accepting a
-- lower preferred fallback; scale 1 preserves a pixel-for-pixel VM surface.
hl.monitor({ output = "", mode = "highrr", position = "auto", scale = 1 })

hl.env("XCURSOR_SIZE", "24")
hl.env("HYPRCURSOR_SIZE", "24")

hl.config({
    general = {
        gaps_in = 0,
        gaps_out = 0,
        border_size = 0,
        allow_tearing = true,
        layout = "dwindle",
    },
    decoration = {
        rounding = 0,
        active_opacity = 1.0,
        inactive_opacity = 1.0,
        shadow = { enabled = false },
        blur = { enabled = false },
    },
    -- This is a presentation boundary, not a Linux desktop. Keep compositor
    -- work at the minimum while QEMU/Looking Glass owns the visible surface.
    animations = { enabled = false },
    misc = {
        force_default_wallpaper = 0,
        disable_hyprland_logo = true,
        disable_splash_rendering = true,
    },
    input = {
        kb_layout = "pt",
        kb_model = "pc105",
        follow_mouse = 1,
        touchpad = { natural_scroll = true },
    },
})

-- Start the guest from the compositor's own startup event.  This gives QEMU
-- the complete Wayland/PipeWire session environment and avoids depending on
-- a later IPC race while the dedicated surface is still coming up.
hl.on("hyprland.start", function ()
    hl.exec_cmd("/home/apx/.local/bin/apx-system-vm")
end)

-- These APX-owned shortcuts remain above the guest even while QEMU or Looking
-- Glass has keyboard focus. SUPER+E and SUPER+M exit this compositor directly;
-- the foreground Host supervisor then restores the Hub. This emergency path
-- needs no client process, menu, socket, SPICE transport, or guest response.
-- The styled confirmation menu remains on SUPER+SHIFT+E.
local environmentMenu = "/home/apx/.local/bin/apx-vm-environment-menu-v1"
hl.bind("SUPER + E", hl.dsp.exit())
hl.bind("SUPER + M", hl.dsp.exit())
hl.bind("SUPER + SHIFT + E", hl.dsp.exec_cmd(environmentMenu))

hl.window_rule({
    name = "apx-windows11-fullscreen",
    match = { class = "^apx-system-vm$" },
    fullscreen = true,
    no_shortcuts_inhibit = true,
})

-- Compatibility for the safe GTK/VGA recovery surface and older provisioned
-- clients. The deterministic app id above is the primary Looking Glass rule.
hl.window_rule({
    name = "apx-system-vm-compatibility",
    match = { title = "^(Windows 11 · .+|Ubuntu · APX|Looking Glass \\(client\\))$" },
    fullscreen = true,
    no_shortcuts_inhibit = true,
})

hl.window_rule({
    name = "apx-environment-top-sheet",
    match = { class = "^(Rofi|rofi)$" },
    float = true,
    no_shortcuts_inhibit = true,
})
