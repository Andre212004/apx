from dataclasses import replace
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import apx_hyprland_h0_device_lease as lease


def observation() -> lease.H0DeviceObservation:
    return lease.H0DeviceObservation(
        lease.GENERATION, "d" * 64, "0000:05:00.0", "amdgpu", "card2-eDP-2",
        True, True, True, True, True, True, True, True,
        tuple((name, host_path, major, minor) for name, host_path, _, major, minor, _ in lease.DEVICES),
    )


class H0DeviceLeaseTests(unittest.TestCase):
    def test_exact_plan_is_generation_device_and_timeout_bound(self) -> None:
        plan = lease.build_device_lease_plan(observation())
        self.assertEqual(plan.environment, "codex-test-hyprland-h0-v1")
        self.assertEqual(plan.timeout_seconds, 120)
        self.assertEqual(plan.recovery_vt, "/dev/tty1")
        self.assertEqual(plan.experiment_vt, "/dev/tty2")
        self.assertIn("DevicePolicy=closed", plan.runtime_properties)
        self.assertIn("DeviceAllow=/dev/dri/card2 rw", plan.runtime_properties)
        self.assertIn("never-restart-graphical-session-automatically", plan.watchdog_actions)

    def test_nvidia_broad_input_audio_camera_and_recovery_vt_are_denied(self) -> None:
        plan = lease.build_device_lease_plan(observation())
        for path in ("/dev/dri/card1", "/dev/dri/renderD128", "/dev/tty1", "/dev/snd", "/dev/video0"):
            self.assertIn(path, plan.denied)
        allowed = {item[1] for item in plan.devices}
        self.assertNotIn("/dev/input", allowed)
        self.assertNotIn("/dev/tty1", allowed)
        internal = {item[0]: item[2] for item in plan.devices}
        self.assertEqual(internal["built-in-keyboard"], "/dev/input/event0")
        self.assertEqual(internal["built-in-touchpad"], "/dev/input/event1")

    def test_every_clean_host_gate_fails_closed(self) -> None:
        fields = (
            "connector_connected", "recovery_vt_active", "experiment_vt_inactive",
            "no_graphical_owner", "no_display_manager", "hub_stopped",
            "development_stopped", "no_uncertain_apx_operation",
        )
        for field in fields:
            with self.subTest(field=field), self.assertRaises(lease.H0DeviceLeaseError):
                lease.build_device_lease_plan(replace(observation(), **{field: False}))

    def test_generation_gpu_connector_and_any_device_drift_fail(self) -> None:
        changes = (
            {"environment_generation": "00000000-0000-4000-8000-000000000000"},
            {"amd_pci": "0000:01:00.0"}, {"amd_driver": "nouveau"},
            {"connector": "card1-eDP-1"}, {"device_identities": observation().device_identities[:-1]},
        )
        for change in changes:
            with self.subTest(change=change), self.assertRaises(lease.H0DeviceLeaseError):
                lease.build_device_lease_plan(replace(observation(), **change))

    def test_module_is_pure_and_contains_no_effect_adapter(self) -> None:
        source = Path(lease.__file__).read_text()
        for forbidden in ("subprocess", "systemctl", "machinectl", "open(", "os.", "Path("):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
