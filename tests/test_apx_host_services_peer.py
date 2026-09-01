import json
from pathlib import Path
import tempfile
import unittest

import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import apx_host_services_peer as subject  # noqa: E402


class HostServicesPeerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.active = root / "active.json"
        self.registration = root / "registration.json"
        self.proc = root / "proc"
        peer_root = self.proc / "4321/root/etc/apx"
        compositor_root = self.proc / "9876/root/etc/apx"
        peer_root.mkdir(parents=True)
        compositor_root.mkdir(parents=True)
        (peer_root / "official-hub-base-v1").write_text("fixture\n")
        (compositor_root / "official-hub-base-v1").write_text("fixture\n")
        (self.proc / "4321/cgroup").write_text(
            f"0::/system.slice/{subject.UNIT}/container/payload\n"
        )
        (self.proc / "4321/uid_map").write_text("0 524288 65536\n")
        (self.proc / "4321/gid_map").write_text("0 524288 65536\n")
        (self.proc / "9876/cgroup").write_text(
            f"0::/system.slice/{subject.UNIT}/container/payload\n"
        )
        (self.proc / "9876/comm").write_text("Hyprland\n")
        self.active.write_text(json.dumps({
            "profile": subject.PROFILE, "generation": subject.GENERATION,
            "unit": subject.UNIT, "pid": 9876,
        }))
        self.registration.write_text(json.dumps({
            "name": "hub", "role": "hub", "generation": subject.GENERATION,
            "state": "running",
        }))

    def tearDown(self):
        self.temp.cleanup()

    def authorize(self, peer=None):
        subject.authorize_official_hub_peer(
            peer or subject.HostServicesPeer(4321, 525288, 525288),
            active=self.active, registration=self.registration,
            proc=self.proc,
        )

    def test_exact_official_hub_peer_is_authorized(self) -> None:
        self.authorize()

    def test_host_uid_stale_generation_stopped_registration_and_wrong_cgroup_refuse(self) -> None:
        attempts = (
            lambda: self.authorize(subject.HostServicesPeer(4321, 1000, 1000)),
            lambda: (self.active.write_text(json.dumps({
                "profile": subject.PROFILE, "generation": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
                "unit": subject.UNIT, "pid": 9876,
            })), self.authorize())[1],
            lambda: (self.registration.write_text(json.dumps({
                "name": "hub", "role": "hub", "generation": subject.GENERATION, "state": "stopped",
            })), self.authorize())[1],
            lambda: ((self.proc / "4321/cgroup").write_text("0::/user.slice/session.scope\n"), self.authorize())[1],
        )
        original_active = self.active.read_text()
        original_registration = self.registration.read_text()
        original_cgroup = (self.proc / "4321/cgroup").read_text()
        for attempt in attempts:
            with self.subTest(attempt=attempt):
                self.active.write_text(original_active)
                self.registration.write_text(original_registration)
                (self.proc / "4321/cgroup").write_text(original_cgroup)
                with self.assertRaises(subject.HostServicesPeerError):
                    attempt()

    def test_root_other_user_and_identity_mapping_are_refused(self) -> None:
        for peer in (
            subject.HostServicesPeer(4321, 524288, 524288),
            subject.HostServicesPeer(4321, 525289, 525289),
        ):
            with self.subTest(peer=peer), self.assertRaises(subject.HostServicesPeerError):
                self.authorize(peer)
        (self.proc / "4321/uid_map").write_text("0 0 4294967295\n")
        with self.assertRaises(subject.HostServicesPeerError):
            self.authorize(subject.HostServicesPeer(4321, 1000, 1000))

    def test_split_short_and_malformed_maps_are_refused(self) -> None:
        bad_maps = (
            "0 524288 1000\n1000 600000 64536\n",
            "0 524288 65535\n",
            "not a map\n",
        )
        for value in bad_maps:
            with self.subTest(value=value):
                (self.proc / "4321/uid_map").write_text(value)
                with self.assertRaises(subject.HostServicesPeerError):
                    self.authorize()

    def test_symlinked_trusted_state_is_refused(self) -> None:
        target = self.active.with_name("active-target.json")
        target.write_text(self.active.read_text())
        self.active.unlink()
        self.active.symlink_to(target)
        with self.assertRaises(subject.HostServicesPeerError):
            self.authorize()

    def test_wrong_official_compositor_process_is_refused(self) -> None:
        (self.proc / "9876/comm").write_text("python\n")
        with self.assertRaises(subject.HostServicesPeerError):
            self.authorize()


if __name__ == "__main__":
    unittest.main()
