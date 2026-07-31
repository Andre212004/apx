from dataclasses import replace
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import apx_hyprland_h0_watchdog as watchdog


def armed():
    return watchdog.arm_watchdog(generation=watchdog.GENERATION, plan_digest=watchdog.PLAN_DIGEST, monotonic_second=1000)


class H0WatchdogTests(unittest.TestCase):
    def test_happy_path_preserves_absolute_deadline_and_requires_zero_residue(self) -> None:
        state = watchdog.record_device_grant(armed(), monotonic_second=1001)
        state = watchdog.record_graphical_ready(state, monotonic_second=1010)
        state = watchdog.request_teardown(state)
        partial = watchdog.observe_teardown(state, tty1_restored=True, processes=1, mounts=0, sockets=0, leases=0)
        self.assertEqual(partial.phase, "teardown")
        complete = watchdog.observe_teardown(partial, tty1_restored=True, processes=0, mounts=0, sockets=0, leases=0)
        self.assertEqual(complete.phase, "complete")
        self.assertTrue(watchdog.recovery_decision(complete, monotonic_second=1015).safe_complete)

    def test_expiry_always_revokes_returns_tty1_and_never_restarts(self) -> None:
        decision = watchdog.recovery_decision(armed(), monotonic_second=1015)
        self.assertTrue(decision.expired)
        self.assertIn("revoke-five-devices", decision.actions)
        self.assertIn("activate-tty1", decision.actions)
        self.assertIn("do-not-restart-graphics", decision.actions)

    def test_deadline_cannot_be_extended_and_late_grants_fail(self) -> None:
        with self.assertRaises(watchdog.H0WatchdogError):
            watchdog.recovery_decision(replace(armed(), deadline=1016), monotonic_second=1010)
        with self.assertRaises(watchdog.H0WatchdogError):
            watchdog.record_device_grant(armed(), monotonic_second=1015)

    def test_stale_generation_plan_order_and_bad_residue_fail_closed(self) -> None:
        cases = (
            lambda: watchdog.arm_watchdog(generation="00000000-0000-4000-8000-000000000000", plan_digest=watchdog.PLAN_DIGEST, monotonic_second=1),
            lambda: watchdog.arm_watchdog(generation=watchdog.GENERATION, plan_digest="0" * 64, monotonic_second=1),
            lambda: watchdog.record_graphical_ready(armed(), monotonic_second=1001),
            lambda: watchdog.observe_teardown(watchdog.request_teardown(armed()), tty1_restored=True, processes=-1, mounts=0, sockets=0, leases=0),
        )
        for case in cases:
            with self.assertRaises(watchdog.H0WatchdogError): case()

    def test_module_is_pure(self) -> None:
        source = Path(watchdog.__file__).read_text()
        for forbidden in ("subprocess", "systemctl", "machinectl", "open(", "Path(", "os.", "sleep("):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
