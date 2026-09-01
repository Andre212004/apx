from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MENU = ROOT / "scripts/physical-pilot/apx-desktop-menu-v2.py"


class DesktopMenuV2Tests(unittest.TestCase):
    def test_menu_is_ascii_typed_and_contains_no_shell(self):
        source = MENU.read_text(); compile(source, str(MENU), "exec")
        for required in ("[ WIFI MENU ]", "[ BLUETOOTH MENU ]", "[ AUDIO MENU ]",
                         "[ BATTERY MENU ]", 'CLIENT = "/run/apx/host-services-client-v2.py"',
                         'CLIENT_V3 = "/run/apx/host-services-client-v3.py"', '"--credential-stdin"',
                         '"-password"',
                         '"wifi-connect"', '"bluetooth-connect"', '"/usr/bin/pavucontrol"'):
            self.assertIn(required, source)
        for forbidden in ("shell=True", "os.system", "eval(", "input("):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__": unittest.main()
