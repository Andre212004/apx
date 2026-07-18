from dataclasses import replace
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import apx_hyprland_h0_device_lease as lease
import apx_hyprland_h0_launch_plan as launch


def device_plan():
    observation = lease.H0DeviceObservation(
        lease.GENERATION, "dc1beaaaf6f073f8c3493d2e6b1d001e4b5f07f431f8a522f2125f242151ea40", "0000:05:00.0", "amdgpu", "card2-eDP-2",
        True, True, True, True, True, True, True, True,
        tuple((name, host, major, minor) for name, host, _, major, minor, _ in lease.DEVICES),
    )
    return lease.build_device_lease_plan(observation)


class H0LaunchPlanTests(unittest.TestCase):
    def test_expiry_is_independent_and_ordered_before_graphical_unit(self) -> None:
        plan = launch.build_launch_plan(device_plan())
        self.assertIn("--on-active=120s", plan.expiry_command)
        self.assertNotIn(launch.GRAPHICAL_UNIT, " ".join(plan.expiry_command))
        self.assertLess(plan.ordered_gates.index("start-independent-expiry-timer"), plan.ordered_gates.index("start-generation-bound-graphical-unit"))
        self.assertIn("verify-expiry-timer-active-before-any-device-grant", plan.ordered_gates)

    def test_graphical_command_is_fixed_closed_and_binds_only_exact_devices(self) -> None:
        plan = launch.build_launch_plan(device_plan())
        command = " ".join(plan.graphical_command)
        for required in (
            "DevicePolicy=closed", "--private-network", "--private-users=no",
            "--no-new-privileges=yes", "MemoryMax=1536M", "TasksMax=512",
            "/dev/dri/card2", "/dev/dri/renderD129", "/dev/input/event0",
            "/dev/input/event1", "/dev/input/event3:/dev/input/event0",
            "/dev/input/event11:/dev/input/event1", "/dev/tty2", "/run/apx-h0/session",
        ):
            self.assertIn(required, command)
        for forbidden in ("/dev/dri/card1", "/dev/dri/renderD128", "/dev/tty1", "/dev/snd", "/dev/video0", "--network-veth"):
            self.assertNotIn(forbidden, command)

    def test_assets_are_digest_and_mode_bound(self) -> None:
        plan = launch.build_launch_plan(device_plan())
        self.assertEqual(tuple(item[2] for item in plan.assets), (0o400, 0o500, 0o500))
        for _, digest, _ in plan.assets:
            self.assertEqual(len(digest), 64)
            int(digest, 16)

    def test_stale_or_changed_lease_fails_closed(self) -> None:
        for changed in (replace(device_plan(), plan_digest="0" * 64), replace(device_plan(), timeout_seconds=121)):
            with self.assertRaises(launch.H0LaunchPlanError):
                launch.build_launch_plan(changed)

    def test_module_is_pure(self) -> None:
        source = Path(launch.__file__).read_text()
        for forbidden in ("subprocess", "os.", "Path(", "open(", "systemctl", "machinectl"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
