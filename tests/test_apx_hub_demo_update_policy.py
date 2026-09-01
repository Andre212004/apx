from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class HubDemoUpdatePolicyTests(unittest.TestCase):
    def test_creation_dialog_defaults_to_coordinated_updates_and_records_opt_out(self):
        html = (ROOT / "prototypes/hub-demo/index.html").read_text()
        script = (ROOT / "prototypes/hub-demo/app.js").read_text()
        self.assertIn('name="followHostUpdates" checked', html)
        self.assertIn("Seguir atualizações do Host", html)
        self.assertIn('data.get("followHostUpdates") === "on"', script)
        self.assertIn("updates ${followsHostUpdates ?", script)


if __name__ == "__main__": unittest.main()
