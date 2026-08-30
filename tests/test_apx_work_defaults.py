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
        for command in ("/usr/bin/rofi", "/usr/bin/thunar", "/usr/bin/brave"):
            self.assertIn(command, source)
        self.assertIn('hl.bind(mainMod .. " + E",', source)
        self.assertIn('hl.bind(mainMod .. " + E",', source)
        self.assertIn("openEnvironments", source)
        self.assertIn('hl.bind(mainMod .. " + F",', source)
        self.assertIn('hl.bind(mainMod .. " + M",', source)
        self.assertIn('hl.bind(mainMod .. " + M", hl.dsp.exit())', source)
        self.assertNotIn("/run/apx/environment-switch-client-v1.py return", source)
        for forbidden in ("apx-hub --switcher", "host-console", "system-power", "coordinated-update"):
            self.assertNotIn(forbidden, source)

    def test_environment_shell_launcher_is_single_instance(self) -> None:
        source = (SHELL / "local/bin/apx-shell-v1").read_text()
        self.assertIn("apx-shell-launcher-v1.lock", source)
        self.assertIn("/usr/bin/flock -n 9", source)

    def test_laptop_keys_keep_actions_inside_the_environment(self) -> None:
        source = (SHELL / "hypr/hyprland.lua").read_text()
        helper = (SHELL / "local/bin/apx-laptop-action-v1").read_text()
        for key in (
            "XF86AudioMute", "XF86AudioLowerVolume", "XF86AudioRaiseVolume",
            "XF86AudioMicMute", "XF86Display", "XF86TouchpadToggle",
            "XF86TaskPane", "XF86Calculator", '"F13"', '"F14"',
            '"F15"', '"F16"',
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
