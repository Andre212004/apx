from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
QML = ROOT / "config/quickshell-ascii-v1/shell.qml"
RUNNER = ROOT / "config/quickshell-ascii-v1/apx-shell-v1.sh"


class QuickshellAsciiProfileTests(unittest.TestCase):
    def test_profile_has_ascii_cyan_bar_and_anchored_popover(self) -> None:
        source = QML.read_text()
        for required in (
            'property color cyan: "#55e6ff"', 'font.family: "monospace"',
            'label: "[ APX · HUB · ENVIRONMENTS ]"', "PopupWindow", "anchor.item = target",
            "grabFocus: true", "radius: 10", "Flickable", "contentHeight",
        ):
            self.assertIn(required, source)

    def test_profile_uses_typed_host_actions_and_local_audio_only(self) -> None:
        source = QML.read_text()
        for required in (
            "/run/apx/host-services-ui-v3.py", '"wifi-scan"', '"wifi-connect"',
            '"bluetooth-power"', '"bluetooth-connect"', "/run/apx/desktop-menu-v2.py", "/usr/bin/wpctl",
            "@DEFAULT_AUDIO_SINK@", "GPU PROFILE :: HYBRID",
        ):
            self.assertIn(required, source)
        for forbidden in ("nmcli", "iwctl", "bluetoothctl", "sudo", "nvidia-smi"):
            self.assertNotIn(forbidden, source)

    def test_runner_restarts_quickshell_if_it_exits(self) -> None:
        source = RUNNER.read_text()
        self.assertIn('quickshell --no-duplicate --path "$config"', source)
        self.assertIn("/home/apx/.local/state/apx-shell-v1", source)
        self.assertIn("Quickshell terminou com estado", source)
        self.assertIn("while true", source)
        self.assertNotIn("rm -", source)

    def test_initial_login_fails_closed_and_idle_lock_is_single_instance(self) -> None:
        source = RUNNER.read_text()
        self.assertIn("apx-initial-login-v1", source)
        self.assertIn("hyprlock --immediate-render --no-fade-in", source)
        self.assertIn("hyprctl dispatch exit", source)
        self.assertIn("pidof hypridle", source)
        self.assertIn("hypridle --quiet --config", source)
        self.assertIn("actual compositor readiness", source)
        self.assertIn("ready_observations", source)
        self.assertIn("/usr/bin/sleep 0.05", source)
        self.assertNotIn("/usr/bin/sleep 4", source)

    def test_lock_and_idle_profiles_follow_the_hub_palette(self) -> None:
        lock = (ROOT / "config/quickshell-ascii-v1/hyprlock.conf").read_text()
        idle = (ROOT / "config/quickshell-ascii-v1/hypridle.conf").read_text()
        for value in ("85, 230, 255", "10, 16, 20", "Adwaita Mono", "PALAVRA-PASSE APX"):
            self.assertIn(value, lock)
        self.assertIn("timeout = 300", idle)
        self.assertIn("timeout = 600", idle)
        self.assertNotIn("suspend", idle)


if __name__ == "__main__":
    unittest.main()
