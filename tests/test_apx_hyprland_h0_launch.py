from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import apx_hyprland_h0_launch as subject


class H0PhysicalLaunchTests(unittest.TestCase):
    def test_physical_execution_is_safety_locked_after_recovery_incident(self) -> None:
        self.assertFalse(subject.PHYSICAL_RUN_ENABLED)
        source = Path(subject.__file__).read_text()
        self.assertIn("if not PHYSICAL_RUN_ENABLED", source)

    def test_adapter_is_exact_bounded_and_always_invokes_watchdog(self) -> None:
        source = Path(subject.__file__).read_text()
        self.assertEqual(subject.OBSERVE_SECONDS, 45)
        self.assertIn('timer_started = _run(["systemctl", "is-active"', source)
        self.assertIn('finally:', source)
        self.assertIn('_run([str(STATE / "watchdog"), "--expire"]', source)
        self.assertIn('"/usr/bin/chvt", "2"', source)

    def test_adapter_has_no_delete_broad_kill_hub_or_development_effect(self) -> None:
        source = Path(subject.__file__).read_text()
        for forbidden in ("rmtree", "unlink(", "btrfs subvolume delete", "pkill", "killall", "apx-hub", "apx-development", "systemctl reboot", "poweroff"):
            self.assertNotIn(forbidden, source)

    def test_result_requires_timer_machine_hyprland_and_complete_recovery(self) -> None:
        source = Path(subject.__file__).read_text()
        for required in ("timer_started", "machine_observed", "hyprland_observed", "wayland_socket_observed", "monitor_observed", "foot_observed", "tty1", "machine_absent", "unit_inactive"):
            self.assertIn(required, source)
        self.assertIn('_process_present(b"/usr/bin/foot")', source)

    def test_diagnostic_capture_is_bounded_and_uses_the_hyprland_proc_root(self) -> None:
        source = Path(subject.__file__).read_text()
        self.assertIn('root/run/user/1000/hypr', source)
        self.assertIn('[:262144]', source)
        self.assertIn('os.O_EXCL | os.O_NOFOLLOW', source)
        self.assertIn('"/usr/bin/hyprctl", "-j", query', source)


if __name__ == "__main__":
    unittest.main()
