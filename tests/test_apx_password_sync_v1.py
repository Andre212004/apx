from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/physical-pilot/sync-apx-password-from-hub-v1.py"


class ApxPasswordSyncV1Tests(unittest.TestCase):
    def test_sync_uses_only_hash_and_trusted_stopped_registrations(self) -> None:
        source = SCRIPT.read_text()
        self.assertIn('arguments.confirm != "SYNC APX PASSWORD"', source)
        self.assertIn('parser.add_argument("--include-host-root", action="store_true")', source)
        self.assertIn('(Path("/etc/shadow"), "host-root.shadow", "root")', source)
        self.assertIn('account not in {"apx", "root"}', source)
        self.assertIn('!= ["apx-hub"]', source)
        self.assertIn('record.get("state") != "stopped"', source)
        self.assertIn('record.get("role") != "graphical-base"', source)
        self.assertIn('password_hash.startswith("$y$")', source)
        self.assertIn('password_hash.startswith("$6$")', source)
        self.assertIn("os.O_NOFOLLOW", source)
        self.assertIn("os.fchown", source)
        self.assertIn("os.fchmod", source)
        self.assertNotIn("chpasswd", source)
        self.assertNotIn("passwd", source)
        self.assertNotIn("shell=True", source)


if __name__ == "__main__":
    unittest.main()
