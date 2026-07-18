from pathlib import Path
import subprocess
import unittest


SCRIPT = Path(__file__).parents[1] / "scripts" / "physical-pilot" / "hyprland-h0-session-v1.sh"


class HyprlandH0SessionScriptTests(unittest.TestCase):
    def test_script_is_valid_and_drops_root_before_hyprland(self) -> None:
        subprocess.run(["bash", "-n", str(SCRIPT)], check=True)
        source = SCRIPT.read_text()
        self.assertIn("/usr/bin/seatd -u apx", source)
        self.assertIn("--reuid=1000 --regid=1000 --groups=5,983,987,992", source)
        self.assertIn("--bounding-set=-all", source)
        self.assertIn("/usr/bin/Hyprland --config", source)
        self.assertNotIn("exec /usr/bin/setpriv", source)

    def test_script_revalidates_every_internal_device(self) -> None:
        source = SCRIPT.read_text()
        for identity in ("e2:2", "e2:81", "d:43", "d:4b", "4:2"):
            self.assertIn(identity, source)
        for path in ("/dev/dri/card2", "/dev/dri/renderD129", "/dev/input/event0", "/dev/input/event1", "/dev/tty2"):
            self.assertIn(path, source)

    def test_script_has_cleanup_and_no_broad_or_unrelated_access(self) -> None:
        source = SCRIPT.read_text()
        self.assertIn("trap cleanup EXIT HUP INT TERM", source)
        for forbidden in ("/dev/dri/card1", "/dev/dri/renderD128", "/dev/input/event2", "/dev/snd", "/dev/video", "/dev/tty1", "sudo", "pacman", "curl", "wget"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
