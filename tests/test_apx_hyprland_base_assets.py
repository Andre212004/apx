import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/hyprland-base/hyprland.conf"
WAYBAR = ROOT / "config/hyprland-base/waybar/config.json"
GTK_APP = ROOT / "prototypes/hub-gtk/apx_hub_app.py"


class HyprlandBaseAssetTests(unittest.TestCase):
    def test_minimal_config_has_portuguese_input_and_fixed_controls(self) -> None:
        source = CONFIG.read_text()
        for required in (
            "kb_layout = pt", "/usr/bin/waybar", "/usr/bin/mako",
            "/usr/bin/alacritty", "/usr/bin/rofi", "/usr/bin/fastfetch",
            "/usr/bin/apx-hub --switcher",
            "bind = SUPER, M, exit",
            "bind = SUPER, F, exec, /usr/bin/thunar",
            "bind = SUPER SHIFT, M, exit",
        ):
            self.assertIn(required, source)
        for forbidden in ("sudo", "pacman", "/dev/", "/var/lib/apx", "curl", "wget"):
            self.assertNotIn(forbidden, source)

    def test_waybar_has_apx_control_and_only_local_ui_commands(self) -> None:
        value = json.loads(WAYBAR.read_text())
        self.assertEqual(value["modules-left"][0], "custom/apx")
        control = value["custom/apx"]
        self.assertEqual(control["on-click"], "/usr/bin/apx-hub --switcher")
        self.assertEqual(control["on-click-right"], "/usr/bin/apx-hub --management")
        rendered = json.dumps(value)
        for forbidden in ("sudo", "systemctl", "machinectl", "pacman", "/var/lib/apx"):
            self.assertNotIn(forbidden, rendered)

    def test_gtk_client_derives_role_from_fixed_session_descriptor(self) -> None:
        source = GTK_APP.read_text()
        self.assertNotIn('"--role"', source)
        self.assertIn("build_session_control(session.role)", source)
        self.assertIn("if management and not control.management_enabled", source)
        self.assertNotIn("subprocess", source)
        self.assertNotIn("os.system", source)

        environment = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
        help_result = subprocess.run(
            [sys.executable, str(GTK_APP), "--help"],
            text=True, capture_output=True, env=environment,
        )
        self.assertEqual(help_result.returncode, 0)
        self.assertNotIn("--role", help_result.stdout)
        self.assertIn("--switcher", help_result.stdout)

    def test_gtk_client_has_only_the_typed_desktop_action_adapter(self) -> None:
        source = GTK_APP.read_text()
        compile(source, str(GTK_APP), "exec")
        self.assertNotIn("Dados de demonstração", source)
        self.assertIn("execute_desktop_action(action)", source)
        self.assertIn("load_desktop_session()", source)
        for forbidden in ("subprocess", "os.system", "systemctl", "machinectl", "sudo", "pacman"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
