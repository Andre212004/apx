from dataclasses import replace
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from apx_executor_contract import RequesterContext  # noqa: E402
import apx_waybar_ascii_fixture_handoff as subject  # noqa: E402


class WaybarAsciiFixtureHandoffTests(unittest.TestCase):
    def requester(self, *, hub: bool) -> RequesterContext:
        return RequesterContext(
            "session-fixture-v1",
            "hub" if hub else subject.TARGET_NAME,
            "hub" if hub else "graphical-base",
            subject.HUB_GENERATION if hub else subject.TARGET_GENERATION,
            True,
            True,
            True,
        )

    def test_hub_gets_only_the_exact_target_activation_button(self) -> None:
        buttons = subject.build_fixture_buttons(self.requester(hub=True))
        self.assertEqual(len(buttons), 1)
        self.assertEqual((buttons[0].action_id, buttons[0].label),
                         ("activate", "Abrir WAYBAR TEST"))
        self.assertEqual(
            (buttons[0].plan.operation_kind, buttons[0].plan.logical_name,
             buttons[0].plan.expected_generation),
            ("activate", subject.TARGET_NAME, subject.TARGET_GENERATION),
        )

    def test_workload_gets_only_its_own_return_button(self) -> None:
        buttons = subject.build_fixture_buttons(self.requester(hub=False))
        self.assertEqual(len(buttons), 1)
        self.assertEqual((buttons[0].action_id, buttons[0].label),
                         ("return-to-hub", "Voltar ao HUB"))
        self.assertEqual(
            (buttons[0].plan.operation_kind, buttons[0].plan.logical_name,
             buttons[0].plan.expected_generation),
            ("stop", subject.TARGET_NAME, subject.TARGET_GENERATION),
        )

    def test_stale_or_untrusted_requester_is_refused(self) -> None:
        hub = self.requester(hub=True)
        variants = (
            replace(hub, generation="aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"),
            replace(hub, authoritative=False),
            replace(hub, logical_name=subject.TARGET_NAME, role="graphical-base"),
        )
        for requester in variants:
            with self.subTest(requester=requester):
                with self.assertRaises(subject.WaybarAsciiFixtureHandoffError):
                    subject.build_fixture_buttons(requester)

    def test_catalogue_has_no_effect_or_command_adapter(self) -> None:
        source = (ROOT / "src/apx_waybar_ascii_fixture_handoff.py").read_text()
        for forbidden in (
            "subprocess", "systemctl", "machinectl", "os.system", "/dev/",
            "/var/lib/apx", "socket",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
