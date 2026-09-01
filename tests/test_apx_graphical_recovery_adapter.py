from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/physical-pilot/apx-graphical-recovery-v1.py"


class GraphicalRecoveryAdapterTests(unittest.TestCase):
    def test_adapter_is_fixed_to_plan_units_deadline_and_tty1(self):
        source = SCRIPT.read_text()
        compile(source, str(SCRIPT), "exec")
        for required in (
            "7603c8d17c787ed4122cff9520f49392c0865412967b5a53e9b595ff8dec43f3",
            "--on-active=3s", "independent expiry timer did not arm",
            '"/usr/bin/chvt", "1"', '"/usr/bin/sleep", "60"',
            "graphics=false devices=false environment=false",
        ):
            self.assertIn(required, source)

    def test_adapter_has_no_graphical_or_device_grant_command(self):
        source = SCRIPT.read_text()
        for forbidden in ("Hyprland", "DeviceAllow", "/dev/dri", "/dev/input", "systemd-nspawn"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
