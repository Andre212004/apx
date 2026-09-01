-- APX VM v2: Hyprland is only the display/input and recovery boundary.
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

hl.on("hyprland.start", function ()
    hl.exec_cmd("/home/apx/.local/bin/apx-system-vm")
end)

-- These bindings are compositor-owned and work even with a black or frozen
-- guest. Direct mode is the dependable installer/recovery surface. Native
-- mode gives the RTX to Windows and presents KVMFR through Looking Glass.
local runtime = "/home/apx/.local/bin/apx-system-vm"
hl.bind("SUPER + E", hl.dsp.exit())
hl.bind("SUPER + M", hl.dsp.exit())
hl.bind("SUPER + SHIFT + R", hl.dsp.exec_cmd(runtime .. " --set-presentation-and-exit direct"))
hl.bind("SUPER + SHIFT + N", hl.dsp.exec_cmd(runtime .. " --set-presentation-and-exit native"))

hl.window_rule({
    name = "apx-system-vm-v2",
    match = { class = "^apx-system-vm$" },
    fullscreen = true,
    no_shortcuts_inhibit = true,
})

hl.window_rule({
    name = "apx-system-vm-v2-gtk",
    match = { title = "^(Windows 11|Ubuntu) · .+$" },
    fullscreen = true,
    no_shortcuts_inhibit = true,
})

hl.window_rule({
    name = "apx-vm-error",
    match = { class = "^(Rofi|rofi)$" },
    float = true,
    no_shortcuts_inhibit = true,
})
