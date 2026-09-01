from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import apx_session_control as control


class SessionControlTests(unittest.TestCase):
    def test_hub_exposes_environment_management(self) -> None:
        for role in control.HUB_ROLES:
            model = control.build_session_control(role)
            self.assertTrue(model.management_enabled)
            self.assertTrue(any(action.mutates_environments for action in model.actions))
            self.assertIn("create", {action.action_id for action in model.actions})
            self.assertIn("destroy", {action.action_id for action in model.actions})

    def test_workloads_expose_return_and_read_only_actions_only(self) -> None:
        forbidden = {"create", "snapshot", "archive", "restore", "destroy", "switch"}
        for role in control.WORKLOAD_ROLES:
            model = control.build_session_control(role)
            self.assertFalse(model.management_enabled)
            self.assertFalse(any(action.mutates_environments for action in model.actions))
            self.assertFalse(forbidden & {action.action_id for action in model.actions})
            self.assertEqual(model.actions[0].action_id, "return-to-hub")

    def test_unknown_role_fails_closed(self) -> None:
        with self.assertRaises(ValueError):
            control.build_session_control("caller-claims-hub")
