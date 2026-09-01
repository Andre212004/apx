from pathlib import Path
import subprocess
import unittest


SCRIPT = Path(__file__).parents[1] / "scripts" / "physical-pilot" / "hyprland-h0-watchdog-v1.sh"


class HyprlandH0WatchdogScriptTests(unittest.TestCase):
    def test_script_is_valid_fixed_and_requires_expiry_action(self) -> None:
        subprocess.run(["bash", "-n", str(SCRIPT)], check=True)
        source = SCRIPT.read_text()
        self.assertIn('[[ $ACTION == --expire ]]', source)
        self.assertIn("c4fc5c49-4106-4a56-b1f0-13bffa41a0c1", source)
        self.assertIn("apx-h0-graphical-c4fc5c49.service", source)
        self.assertIn("apx-codex-test-hyprland-h0-v1", source)

    def test_recovery_stops_only_h0_returns_tty1_and_observes_residue(self) -> None:
        source = SCRIPT.read_text()
        self.assertEqual(source.count('systemctl stop "$UNIT"'), 1)
        self.assertIn("/usr/bin/chvt 1", source)
        self.assertIn("/proc/self/mountinfo", source)
        self.assertIn("/proc').iterdir()", source)
        self.assertIn('"--machine=" + sys.argv[1]', source)
        self.assertIn("data.split(b'\\0')", source)
        self.assertIn("residue-remains", source)

    def test_script_has_no_start_delete_hub_development_or_broad_kill(self) -> None:
        source = SCRIPT.read_text()
        for forbidden in (
            "systemctl start", "systemctl restart", "machinectl start",
            "machinectl poweroff", "rm -", "rmdir", "btrfs subvolume delete",
            "pkill", "killall", "apx-hub", "apx-development",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
