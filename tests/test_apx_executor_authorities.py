import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import apx_executor_authorities as subject
from apx_executor_contract import ExecutorRequest, RequesterContext, build_operation_plan
from apx_executor_endpoint import EffectResult
from apx_executor_peer import PeerCredentials


GEN = "69b56acc-fd4d-4499-8009-e1d0108466f4"


class ExecutorAuthoritiesTests(unittest.TestCase):
    def test_factory_binds_peer_target_store_and_effect_adapter(self):
        with tempfile.TemporaryDirectory() as temporary:
            environments = Path(temporary); (environments / "test").mkdir()
            (environments / "test/registration.json").write_text(json.dumps(
                {"name": "test", "generation": GEN, "state": "stopped"}))
            requester = RequesterContext("session-" + "1" * 32, "hub", "hub-graphical",
                                         "2c3dbacc-106f-4053-8603-f649552f5513", True, True, True)
            plan = build_operation_plan("activate", "test", GEN)
            request = ExecutorRequest(1, "apx-executor-v1", "op-" + "2" * 32,
                "activate", "test", GEN, plan.plan_digest, "approval-" + "3" * 32,
                "4" * 64, 9999999999)
            effect = Mock(return_value=EffectResult("accepted", ()))
            with patch.object(subject, "ENVIRONMENTS", environments), \
                 patch.object(subject, "observe_peer", return_value=requester), \
                 patch.object(subject.store, "load_plan"), \
                 patch.object(subject.store, "load_approval"), \
                 patch.object(subject.store, "reserve_nonce"):
                authorities = subject.build_authorities(PeerCredentials(4, 1000, 1000), effect)
                state = authorities.observe_state(request)
            self.assertEqual(state.current_generation, GEN)
            self.assertEqual(state.requester_context, requester)
            self.assertIs(authorities.apply_effects, effect)

    def test_changed_target_generation_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            environments = Path(temporary); (environments / "test").mkdir()
            (environments / "test/registration.json").write_text(json.dumps(
                {"name": "test", "generation": "changed", "state": "stopped"}))
            requester = RequesterContext("session-" + "1" * 32, "hub", "hub-graphical",
                                         "2c3dbacc-106f-4053-8603-f649552f5513", True, True, True)
            plan = build_operation_plan("activate", "test", GEN)
            request = ExecutorRequest(1, "apx-executor-v1", "op-" + "2" * 32,
                "activate", "test", GEN, plan.plan_digest, "approval-" + "3" * 32,
                "4" * 64, 9999999999)
            with patch.object(subject, "ENVIRONMENTS", environments), \
                 patch.object(subject, "observe_peer", return_value=requester):
                authorities = subject.build_authorities(PeerCredentials(4, 1000, 1000), Mock())
                with self.assertRaises(subject.ExecutorAuthoritiesError):
                    authorities.observe_state(request)


if __name__ == "__main__":
    unittest.main()
