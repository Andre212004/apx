from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
DEFAULTS = ROOT / "config/work-defaults-v1"
SHELL = ROOT / "config/environment-shell-v1"


class WorkDefaultsTests(unittest.TestCase):
    def test_normal_user_folders_are_environment_local(self) -> None:
        source = (DEFAULTS / "user-dirs.dirs").read_text()
        for name in (
            "Desktop", "Downloads", "Templates", "Public", "Documents",
            "Music", "Pictures", "Videos", "Projects",
        ):
            self.assertIn(f'"$HOME/{name}"', source)
        self.assertNotIn("/var/lib/apx", source)
        self.assertNotIn("/root", source)

    def test_work_defaults_use_local_brave_and_thunar(self) -> None:
        source = (DEFAULTS / "mimeapps.list").read_text()
        self.assertIn("x-scheme-handler/https=brave-browser.desktop", source)
        self.assertNotIn("firefox.desktop", source)
        self.assertIn("inode/directory=thunar.desktop", source)
        for forbidden in ("sudo", "machinectl", "/run/apx", "/var/lib/apx"):
            self.assertNotIn(forbidden, source)

    def test_environment_visual_profile_is_the_capability_aware_hub_shell(self) -> None:
        source = (SHELL / "quickshell/apx/shell.qml").read_text()
        for expected in ("#55e6ff", "#246879", "Adwaita Mono", "environmentIdentity.role"):
            self.assertIn(expected, source)
        self.assertIn('root.isHub ? "[ HUB · ENVIRONMENTS ]"', source)
        self.assertIn('root.isHub ? "Desligar" : "Voltar"', source)

    def test_work_shortcuts_are_local_and_keep_an_emergency_exit(self) -> None:
        source = (SHELL / "hypr/hyprland.lua").read_text()
        self.assertIn('hl.exec_cmd("/home/apx/.local/bin/apx-shell-v1")', source)
        self.assertNotIn("waybar", source.lower())
        for command in ("/usr/bin/rofi", "/usr/bin/brave"):
            self.assertIn(command, source)
        self.assertIn('hl.bind(mainMod .. " + E",', source)
        self.assertIn('hl.bind(mainMod .. " + E",', source)
        self.assertIn("openEnvironments", source)
        self.assertIn('hl.bind(mainMod .. " + F", hl.dsp.window.fullscreen())', source)
        self.assertIn('hl.bind(mainMod .. " + P",', source)
        self.assertIn("openFiles", source)
        self.assertNotIn('local fileManager = "/usr/bin/thunar"', source)
        self.assertIn('hl.bind(mainMod .. " + M",', source)
        self.assertIn('hl.bind(mainMod .. " + M", hl.dsp.exit())', source)
        self.assertNotIn("/run/apx/environment-switch-client-v1.py return", source)
        for forbidden in ("apx-hub --switcher", "host-console", "system-power", "coordinated-update"):
            self.assertNotIn(forbidden, source)

    def test_environment_shell_launcher_is_single_instance(self) -> None:
        source = (SHELL / "local/bin/apx-shell-v1").read_text()
        self.assertIn("apx-shell-launcher-v1.lock", source)
        self.assertIn("/usr/bin/flock -n 9", source)

    def test_wallpapers_rotate_on_a_noninteractive_background_layer(self) -> None:
        source = (SHELL / "quickshell/apx/shell.qml").read_text()
        for wallpaper in ("atlantic-coast.png", "alpine-lake.png", "rainforest-stream.png"):
            self.assertIn(wallpaper, source)
            self.assertTrue((SHELL / "apx/wallpapers" / wallpaper).is_file())
        for required in (
            "interval: 15 * 60 * 1000", "model: Quickshell.screens",
            "WlrLayershell.layer: WlrLayer.Background", "mask: Region {}",
            "fillMode: Image.PreserveAspectCrop",
        ):
            self.assertIn(required, source)

    def test_control_centre_uses_text_instead_of_icons(self) -> None:
        source = (SHELL / "quickshell/apx/shell.qml").read_text()
        # The sole remaining ControlIcon instance belongs to the separate Fn
        # OSD; the control-centre cards contain text only.
        self.assertEqual(source.count("ControlIcon {"), 1)
        self.assertNotIn("WifiSecurityIcon", source)
        for label in ('text: "WI-FI"', 'text: "BLUETOOTH"', 'text: "VOLUME"',
                      'text: "MICROFONE"', 'text: "TECLADO"'):
            self.assertIn(label, source)
        controls = source.split('visible: root.popupKind === "controls"', 1)[1]
        self.assertIn("height: visible ? 46 : 0", controls)
        # Interactive cards share the dark menu-button palette. Microphone and
        # keyboard retain state through a restrained active surface/outline,
        # rather than a large blue fill.
        for palette_entry in (
            'controlButtonSurface: "#101920"',
            'controlButtonHover: "#17242b"',
            'controlButtonActive: "#142c34"',
            'controlButtonOutline: "#26343a"',
        ):
            self.assertIn(palette_entry, source)
        for state_color in (
            '!root.microphoneActive || root.microphoneMuted ? root.controlButtonSurface : root.controlButtonActive',
            'root.keyboardBrightness === 0 ? root.controlButtonSurface : root.controlButtonActive',
        ):
            self.assertIn(state_color, source)
        brightness_card = source.split('text: "Brilho do ecrã"', 1)[0].rsplit(
            "Rectangle {", 1
        )[1]
        self.assertIn("color: root.controlButtonSurface", brightness_card)
        self.assertIn("border.color: root.controlButtonOutline", brightness_card)
        for removed_state_color in (
            'root.wifiDisplayActive() ? "#173f49" : "#182731"',
            'root.bluetoothDisplayPowered() ? "#173f49" : "#182731"',
            'root.volumeMuted ? "#182731"',
            'root.volumeValue < 50 ? "#17313a"',
            'root.displayBrightness < 34 ? "#182731"',
            'keyboardBrightnessSummaryMouse.containsMouse ? "#20323c"',
            'microphoneSummaryMouse.containsMouse ? "#20323c"',
        ):
            self.assertNotIn(removed_state_color, source)
        for forbidden in (
            "wifiPowerButton", "bluetoothPowerButton", "volumeMuteSummaryButton",
            "microphoneMuteSummaryButton", 'text: root.wifiDisplayActive() ? "ON" : "OFF"',
            'text: root.bluetoothDisplayPowered() ? "ON" : "OFF"',
            'text: root.volumeMuted ? "OFF" : "ON"',
            'text: root.microphoneMuted ? "OFF" : "ON"',
            "keyboardBrightnessSummaryButton", "LUZ OFF", "LUZ MÉD", "LUZ MAX",
        ):
            self.assertNotIn(forbidden, source)
        actions = source.split('text: "AÇÕES DA SESSÃO"', 1)[1]
        before_actions = source.split('text: "AÇÕES DA SESSÃO"', 1)[0]
        self.assertIn("width: parent.width; height: visible ? 9 : 0", before_actions[-400:])
        self.assertIn("height: visible ? 85 : 0", actions)
        self.assertGreaterEqual(actions.count("height: 40; radius: 10"), 4)
        self.assertGreaterEqual(actions.count("border.width: 1; border.color:"), 4)
        self.assertLess(actions.index('text: "Bloquear"'), actions.index('id: updateMouse'))
        self.assertLess(actions.index('id: rebootMouse'), actions.index('id: updateMouse'))
        self.assertLess(actions.index('id: updateMouse'), actions.index('id: poweroffMouse'))
        self.assertIn("function openFiles(): void", source)
        self.assertIn("if (!root.isHub && !environmentFilesProcess.running)", source)

    def test_lock_enter_retries_face_or_submits_password(self) -> None:
        lock = (SHELL / "hypr/hyprlock.conf").read_text()
        self.assertIn("ignore_empty_input = false", lock)
        self.assertIn("A VALIDAR…", lock)
        self.assertNotIn("A VERIFICAR A CARA…", lock)
        self.assertIn("ENTER: REPETIR CARA · OU PALAVRA-PASSE", lock)
        self.assertIn("cmd[update:300] /home/apx/.local/bin/apx-face-auth-state-v1", lock)
        face_state = (SHELL / "local/bin/apx-face-auth-state-v1").read_text()
        self.assertIn('apx-howdy-camera-*.active', face_state)
        self.assertIn("observed_ticks", face_state)
        self.assertIn('/usr/lib/howdy/compare.py', face_state)
        self.assertIn('A VERIFICAR A CARA…', face_state)
        self.assertIn('APÓS FALHA  ·  ENTER REPETE A CARA', face_state)
        howdy_patch = (ROOT / "config/howdy-v1/howdy-apx/apx-camera-frame-state.patch").read_text()
        self.assertIn("publish_camera_frame_state()", howdy_patch)
        self.assertIn("frame, gsframe = video_capture.read_frame()", howdy_patch)
        self.assertLess(howdy_patch.index("read_frame()"), howdy_patch.rindex("publish_camera_frame_state()"))
        howdy_pkgbuild = (ROOT / "config/howdy-v1/howdy-apx/PKGBUILD").read_text()
        self.assertIn("pkgrel=3", howdy_pkgbuild)
        self.assertIn("apx-camera-frame-state.patch", howdy_pkgbuild)
        self.assertIn('$pkgdir/etc/howdy/config.ini', howdy_pkgbuild)
        pam = (ROOT / "config/howdy-v1/pam/hyprlock").read_text()
        self.assertIn("[success=ok default=1] pam_howdy.so", pam)
        self.assertIn("[success=done default=die] pam_faillock.so authsucc", pam)
        self.assertNotIn("sufficient      pam_howdy.so", pam)
        self.assertIn("pam_howdy runs first", lock)

    def test_bar_has_small_symmetric_horizontal_margins(self) -> None:
        source = (SHELL / "quickshell/apx/shell.qml").read_text()
        bar = source.split("id: bar", 1)[1].split("id: hotkeyOsdWindow", 1)[0]
        self.assertIn("anchors { top: true; left: true; right: true }", bar)
        self.assertIn("margins { left: 5; right: 5 }", bar)
        self.assertIn("anchors.left: parent.left\n                anchors.leftMargin: 5", bar)
        self.assertIn("anchors.right: parent.right\n                anchors.rightMargin: 5", bar)

    def test_window_border_matches_the_quickshell_bar(self) -> None:
        lua = (SHELL / "hypr/hyprland.lua").read_text()
        fallback = (SHELL / "hyprland/hyprland.conf").read_text()
        defaults = (DEFAULTS / "hyprland.conf").read_text()

        self.assertIn("border_size = 1,", lua)
        self.assertEqual(lua.count('= "rgba(26343aff)"'), 2)
        self.assertNotIn("rgba(33ccffee)", lua)
        self.assertNotIn("rgba(00ff99ee)", lua)
        for source in (fallback, defaults):
            self.assertIn("border_size = 1", source)
            self.assertIn("col.active_border = rgba(26343aff)", source)
            self.assertIn("col.inactive_border = rgba(26343aff)", source)
            self.assertNotIn("col.active_border = rgba(55e6ffff)", source)

    def test_laptop_keys_keep_actions_inside_the_environment(self) -> None:
        source = (SHELL / "hypr/hyprland.lua").read_text()
        helper = (SHELL / "local/bin/apx-laptop-action-v1").read_text()
        self.assertIn("Use only semantic multimedia symbols emitted by firmware while Fn is held", source)
        for key in (
            "XF86AudioMute", "XF86AudioLowerVolume", "XF86AudioRaiseVolume",
            "XF86AudioMicMute", "XF86Display", "XF86TouchpadToggle",
            "XF86TaskPane", "XF86Calculator", 'hl.bind("F13"', 'hl.bind("F14"',
            'hl.bind("F15"', 'hl.bind("F16"',
        ):
            self.assertIn(key, source)
        for action in ("airplane-status", "display-cycle", "apps", "overview", "calculator", "screenshot"):
            self.assertIn(action, helper)
        for normal_key in ('"Insert"', '"Delete"', '"Home"', '"End"', '"Page_Up"', '"Page_Down"'):
            self.assertNotIn(normal_key, source)
        for forbidden in ("sudo", "machinectl", "/var/lib/apx"):
            self.assertNotIn(forbidden, helper)
        self.assertIn("natural_scroll = true", source)


if __name__ == "__main__":
    unittest.main()
