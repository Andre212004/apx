import json
import os
from pathlib import Path
import tempfile
import unittest

import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import apx_executor_peer as peer


HUB_GEN = "2c3dbacc-106f-4053-8603-f649552f5513"


class ExecutorPeerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        base = Path(self.temp.name)
        self.session = base / "active.json"
        self.environments = base / "environments"
        self.proc = base / "proc"
        (self.environments / "hub").mkdir(parents=True)
        (self.proc / "4321").mkdir(parents=True)
        self.state = {"profile": peer.PROFILE, "session_id": "session-" + "1" * 32,
                      "logical_name": "hub", "role": "hub-graphical",
                      "generation": HUB_GEN,
                      "unit": "apx-graphical-hub-2c3dbacc.service"}
        self.registration = {"name": "hub", "role": "hub-graphical",
                             "generation": HUB_GEN, "state": "running"}
        self.write()

    def tearDown(self):
        self.temp.cleanup()

    def write(self):
        self.session.write_text(json.dumps(self.state))
        (self.environments / "hub/registration.json").write_text(json.dumps(self.registration))
        (self.proc / "4321/cgroup").write_text(
            "0::/system.slice/apx-graphical-hub-2c3dbacc.service\n")

    def observe(self, credentials=None):
        return peer.observe_peer(credentials or peer.PeerCredentials(4321, 1000, 1000),
                                 active_session=self.session,
                                 environments=self.environments, proc=self.proc)

    def test_exact_peer_maps_to_authoritative_hub_context(self):
        context = self.observe()
        self.assertEqual((context.logical_name, context.generation), ("hub", HUB_GEN))
        self.assertTrue(context.authoritative)

    def test_wrong_uid_pid_cgroup_unit_role_or_generation_fails_closed(self):
        variants = (
            lambda: self.observe(peer.PeerCredentials(4321, 0, 0)),
            lambda: self.observe(peer.PeerCredentials(9999, 1000, 1000)),
            lambda: ((self.proc / "4321/cgroup").write_text("0::/user.slice/x\n"), self.observe())[1],
            lambda: (self.state.update(unit="apx-graphical-test-69b56acc.service"), self.write(), self.observe())[2],
            lambda: (self.registration.update(generation="69b56acc-fd4d-4499-8009-e1d0108466f4"), self.write(), self.observe())[2],
        )
        for attempt in variants:
            with self.subTest(attempt=attempt):
                self.state.update({"unit": "apx-graphical-hub-2c3dbacc.service"})
                self.registration.update({"generation": HUB_GEN})
                self.write()
                with self.assertRaises(peer.ExecutorPeerError):
                    attempt()

    def test_symlink_active_state_is_rejected(self):
        target = self.session.with_name("target")
        target.write_text(self.session.read_text())
        self.session.unlink(); self.session.symlink_to(target)
        with self.assertRaises(peer.ExecutorPeerError):
            self.observe()


if __name__ == "__main__":
    unittest.main()
