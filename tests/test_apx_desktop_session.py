from dataclasses import asdict
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import apx_desktop_session as subject
from apx_executor_contract import ExecutorRequest, build_operation_plan


def request(kind="activate", name="test", generation=7):
    plan = build_operation_plan(kind, name, generation)
    return ExecutorRequest(1, "apx-executor-v1", "op-" + "1" * 32, kind, name,
                           generation, plan.plan_digest, "approval-" + "2" * 32,
                           "3" * 64, 9999999999)


def descriptor(role="hub-graphical", active="hub", actions=None):
    actions = actions or [{"action_id": "activate", "label": "Abrir apx-test",
                           "request": asdict(request())}]
    return json.dumps({"profile": subject.PROFILE, "session_id": "seat0-hub-1",
                       "active_environment": active, "role": role,
                       "actions": actions}).encode()


class DesktopSessionTests(unittest.TestCase):
    def test_hub_accepts_only_closed_activate_requests(self):
        session = subject.parse_desktop_session(descriptor())
        self.assertEqual(session.actions[0].request.logical_name, "test")

    def test_workload_accepts_only_its_bound_return(self):
        item = {"action_id": "return-to-hub", "label": "Voltar ao HUB",
                "request": asdict(request("stop", "test", 7))}
        session = subject.parse_desktop_session(
            descriptor("graphical-base", "test", [item]))
        self.assertEqual(session.actions[0].request.operation_kind, "stop")

    def test_cross_environment_return_and_arbitrary_fields_are_rejected(self):
        cases = [
            descriptor("graphical-base", "test", [{"action_id": "return-to-hub",
                "label": "Voltar", "request": asdict(request("stop", "other", 8))}]),
            json.dumps({**json.loads(descriptor()), "command": "sh"}).encode(),
        ]
        for value in cases:
            with self.assertRaises(subject.DesktopSessionError):
                subject.parse_desktop_session(value)

    def test_action_reaches_only_typed_executor_client(self):
        action = subject.parse_desktop_session(descriptor()).actions[0]
        expected = object()
        with patch.object(subject, "exchange_executor_request", return_value=expected) as exchange:
            self.assertIs(subject.execute_desktop_action(action), expected)
        exchange.assert_called_once_with(action.request)

    def test_fixed_descriptor_path_cannot_be_replaced_by_caller(self):
        with self.assertRaises(subject.DesktopSessionError):
            subject.load_desktop_session(Path("/tmp/forged"))


if __name__ == "__main__":
    unittest.main()
