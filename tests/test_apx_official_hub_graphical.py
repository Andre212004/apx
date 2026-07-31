from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "scripts/physical-pilot/apx-official-hub-graphical-v1.py"
SESSION = ROOT / "scripts/physical-pilot/apx-official-hub-session-v1.sh"


class OfficialHubGraphicalTests(unittest.TestCase):
    def test_launcher_binds_current_hub_identity_and_recovers(self) -> None:
        source = LAUNCHER.read_text()
        compile(source, str(LAUNCHER), "exec")
        for required in (
            "6f63f9a9-daea-40d1-969f-e25ff0752f4d",
            'RELEASE = "hub-headless-v4"', "--recover", "finally:", "recover()",
            "apx-official-hub-graphical-expiry", 'run(("chvt", "1"), False)',
            '"remove", "--environment", "hub"', "Super+Q", "Super+M",
            "open_and_verify_kitty", "Kitty did not create a Hyprland window",
            '"--property=TimeoutStopSec=3s"', 'process_pids(b"Hyprland")',
            'root/etc/apx/official-hub-base-v1',
            '"dispatch", \'hl.dsp.exec_cmd("kitty")\'',
        ):
            self.assertIn(required, source)

    def test_launcher_admits_only_fixed_internal_devices(self) -> None:
        source = LAUNCHER.read_text()
        for required in (
            "platform-i8042-serio-0", "pci-0000:05:00.3-usb-0:4:1.0",
            '"048d"', '"c101"', "platform-AMDI0010:01",
            "DevicePolicy=closed", "/dev/dri/card2", "/dev/dri/renderD129", "/dev/tty2",
        ):
            self.assertIn(required, source)
        for fixed_event in ("/dev/input/event3", "/dev/input/event5", "/dev/input/event9"):
            self.assertNotIn(fixed_event, source)

    def test_session_runs_owner_config_as_apx_not_root(self) -> None:
        source = SESSION.read_text()
        for required in (
            "/home/apx/.config/hypr/hyprland.lua", "/usr/bin/start-hyprland",
            "--reuid=1000", "--regid=1000", "--bounding-set=-all",
            "LIBSEAT_BACKEND=seatd", "AQ_DRM_DEVICES=/dev/dri/card2",
            "APX_KEYBOARD_I8042_DEVICE", "APX_KEYBOARD_ITE_DEVICE",
        ):
            self.assertIn(required, source)
        self.assertNotIn("sudo", source)


if __name__ == "__main__":
    unittest.main()
