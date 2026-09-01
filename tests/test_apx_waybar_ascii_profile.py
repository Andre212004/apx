import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "config/waybar-ascii-v1"


class WaybarAsciiProfileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.hub = json.loads((PROFILE / "hub-config.json").read_text())
        self.environment = json.loads((PROFILE / "environment-config.json").read_text())

    def test_profiles_differ_only_by_workspace_presentation_and_tooltip(self) -> None:
        self.assertEqual(self.hub["modules-left"], ["clock"])
        self.assertEqual(
            self.environment["modules-left"], ["clock", "hyprland/workspaces"]
        )
        self.assertNotIn("hyprland/workspaces", self.hub)
        self.assertEqual(self.environment["hyprland/workspaces"]["format"], "[ {id} ]")
        for field in (
            "modules-center", "modules-right", "clock", "pulseaudio",
            "custom/apx-network", "custom/apx-bluetooth", "custom/apx-time", "battery",
        ):
            self.assertEqual(self.hub[field], self.environment[field])

    def test_network_represents_private_connectivity_not_host_wifi_control(self) -> None:
        for profile in (self.hub, self.environment):
            network = profile["custom/apx-network"]
            self.assertEqual(network["exec"], "/run/apx/host-services-client-v1.py waybar-network")
            self.assertEqual(network["return-type"], "json")
            self.assertNotIn("iwctl", json.dumps(network))

    def test_audio_menu_preserves_fixed_environment_local_scroll_actions(self) -> None:
        for profile in (self.hub, self.environment):
            audio = profile["pulseaudio"]
            self.assertEqual(audio["on-click"], "/run/apx/desktop-menu-v2.py audio")
            self.assertTrue(audio["on-scroll-up"].startswith("wpctl set-volume"))
            self.assertTrue(audio["on-scroll-down"].startswith("wpctl set-volume"))

    def test_host_owned_status_uses_only_the_fixed_unprivileged_client(self) -> None:
        for profile in (self.hub, self.environment):
            for module, mode in (
                ("custom/apx-network", "waybar-network"),
                ("custom/apx-bluetooth", "waybar-bluetooth"),
                ("custom/apx-time", "waybar-time"),
            ):
                item = profile[module]
                self.assertEqual(item["exec"], f"/run/apx/host-services-client-v1.py {mode}")
            self.assertEqual(
                profile["custom/apx-network"]["on-click"],
                "/run/apx/desktop-menu-v2.py wifi",
            )
            self.assertEqual(
                profile["custom/apx-bluetooth"]["on-click"],
                "/run/apx/desktop-menu-v2.py bluetooth",
            )
            self.assertEqual(profile["battery"]["on-click"], "/run/apx/desktop-menu-v2.py battery")

    def test_apx_button_uses_only_the_typed_session_client(self) -> None:
        for profile, action in ((self.hub, "/run/apx/environment-switch-client-v1.py hub-menu"),
                                (self.environment, "/run/apx/environment-switch-client-v1.py return")):
            control = profile["custom/apx-environments"]
            self.assertEqual(control["exec"], "/run/apx/environment-switch-client-v1.py waybar-identity")
            self.assertEqual(control["return-type"], "json")
            self.assertEqual(control["on-click"], action)
            self.assertEqual(control["interval"], 5)
            rendered = json.dumps(control)
            for forbidden in ("machinectl", "systemctl", "sudo", "/var/lib/apx"):
                self.assertNotIn(forbidden, rendered)

    def test_shared_style_preserves_ascii_aesthetic(self) -> None:
        style = (PROFILE / "style.css").read_text()
        for required in ("font-family: monospace", "#workspaces button.active", "#custom-apx-environments"):
            self.assertIn(required, style)


if __name__ == "__main__":
    unittest.main()
