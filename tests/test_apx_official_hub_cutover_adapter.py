from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/physical-pilot/apx-official-hub-cutover-v1.py"


class OfficialHubCutoverAdapterTests(unittest.TestCase):
    def test_adapter_preserves_old_hub_and_uses_digest_bound_approval(self) -> None:
        source = SCRIPT.read_text()
        compile(source, str(SCRIPT), "exec")
        for required in (
            'TEST = STATE / "environments/hub-testes"',
            "os.rename(CURRENT, TEST)", "os.rename(CANDIDATE, CURRENT)",
            "CUTOVER OFFICIAL HUB", "plan.plan_digest",
            '"hub_authority"] = False', '"stage": "prepared"',
            'Path("/etc/hostname").read_text().strip()',
        ):
            self.assertIn(required, source)
        self.assertNotIn('"/usr/bin/hostname"', source)
        for forbidden in ("rmtree(CURRENT", "rmtree(TEST", "subvolume\", \"delete"):
            self.assertNotIn(forbidden, source)

    def test_interruption_recovery_rolls_back_or_finishes_without_delete(self) -> None:
        source = SCRIPT.read_text()
        self.assertIn('stage == "old-renamed"', source)
        self.assertIn("os.rename(TEST, CURRENT)", source)
        self.assertIn('stage in {"new-published", "complete"}', source)
        self.assertIn("state is ambiguous; state was preserved", source)


if __name__ == "__main__":
    unittest.main()
