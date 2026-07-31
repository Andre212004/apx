from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import apx_session_descriptor_issuer as subject
from apx_desktop_session import parse_desktop_session
from apx_executor_contract import RequesterContext, build_operation_plan


def action(kind="activate", name="test", generation=8):
    return subject.IssuedDesktopAction(
        "activate" if kind == "activate" else "return-to-hub",
        "Abrir apx-test" if kind == "activate" else "Voltar ao HUB",
        build_operation_plan(kind, name, generation),
        "op-" + "1" * 32, "approval-" + "2" * 32, "3" * 64,
    )


class SessionDescriptorIssuerTests(unittest.TestCase):
    def test_hub_bundle_binds_descriptor_plan_approval_and_request(self):
        requester = RequesterContext("hub-seat0", "hub", "hub-graphical", 4, True, True, True)
        bundle = subject.issue_session_descriptor(requester, (action(),), issued_at=100, expires_at=200)
        parsed = parse_desktop_session(bundle.descriptor)
        self.assertEqual(parsed.actions[0].request, bundle.requests[0])
        self.assertEqual(bundle.approvals[0].session_id, requester.session_id)
        self.assertEqual(bundle.plans[0].plan_digest, bundle.requests[0].plan_digest)

    def test_workload_gets_only_generation_bound_self_stop(self):
        requester = RequesterContext("test-seat0", "test", "graphical-base", 8, True, True, True)
        bundle = subject.issue_session_descriptor(
            requester, (action("stop", "test", 8),), issued_at=100, expires_at=200)
        self.assertEqual(parse_desktop_session(bundle.descriptor).actions[0].action_id, "return-to-hub")

    def test_forged_role_cross_stop_and_long_lifetime_fail_closed(self):
        hub = RequesterContext("hub-seat0", "hub", "hub-graphical", 4, True, True, True)
        workload = RequesterContext("test-seat0", "test", "graphical-base", 8, True, True, True)
        cases = (
            (hub, (action("stop", "hub", 4),), 100, 200),
            (workload, (action("stop", "other", 9),), 100, 200),
            (hub, (action(),), 100, 401),
        )
        for requester, actions, issued, expires in cases:
            with self.assertRaises(subject.SessionDescriptorIssuerError):
                subject.issue_session_descriptor(requester, actions, issued_at=issued, expires_at=expires)


if __name__ == "__main__":
    unittest.main()
