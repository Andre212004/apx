from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/physical-pilot/apx-publish-graphical-hub-v1.py"


class PublishGraphicalHubTests(unittest.TestCase):
    def test_adapter_preserves_old_hub_and_has_rollback_path(self):
        source = SCRIPT.read_text()
        compile(source, str(SCRIPT), "exec")
        for required in ("retained-hub-headless-v3", "os.rename(CURRENT, RETAINED)",
                         "os.rename(RETAINED, CURRENT)", '"graphical_activation=false"',
                         '"role": "hub-graphical"'):
            self.assertIn(required, source)
        self.assertNotIn("rmtree", source)
        self.assertNotIn("unlink(", source)


if __name__ == "__main__":
    unittest.main()
