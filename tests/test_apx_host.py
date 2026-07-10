from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import os
import stat
import sys
import tempfile
import unittest
from unittest.mock import Mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_cli
import apx_host


def metadata(kind: int = stat.S_IFDIR, mode: int = 0o755) -> os.stat_result:
    return os.stat_result([kind | mode, 0, 0, 0, 0, 0, 0, 0, 0, 0])


class Account:
    def __init__(self, name: str, uid: int, home: str) -> None:
        self.pw_name = name
        self.pw_uid = uid
        self.pw_gid = uid
        self.pw_dir = home


class HostReadinessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.accounts = [
            Account("apx-hub", 1001, "/home/apx-hub"),
            Account("apx-development", 1002, "/home/apx-development"),
        ]
        self.mount = apx_cli.MountObservation(
            "confirmed", "btrfs", "/home", "/dev/test[/@home]",
            "rw,relatime", False, "test",
        )
        self.registration = SimpleNamespace(state="absent")
        self.marker = SimpleNamespace(absent="confirmed")
        self.sessions = SimpleNamespace(status="confirmed")
        self.runner = Mock(
            return_value=apx_cli.CommandResult(0, "active\n", "")
        )
        self.which = Mock(side_effect=lambda name: f"/usr/bin/{name}")

    def report(self, **changes: object) -> apx_host.HostReadinessReport:
        values: dict[str, object] = {
            "accounts": self.accounts,
            "mount": self.mount,
            "registration": self.registration,
            "incomplete_operation": self.marker,
            "sessions": self.sessions,
            "command_runner": self.runner,
            "which_func": self.which,
            "authoritative_host": True,
        }
        values.update(changes)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sessions = root / "sessions"
            sessions.mkdir()
            (sessions / "plasma.desktop").write_text("[Desktop Entry]\n", encoding="utf-8")
            display_link = root / "display-manager.service"
            display_link.symlink_to("/usr/lib/systemd/system/sddm.service")

            def observe(path: str | os.PathLike[str]) -> os.stat_result:
                if str(path) == apx_host.TRIAL_HOME:
                    raise FileNotFoundError
                if str(path) == "/home":
                    return metadata()
                return os.lstat(path)

            values.setdefault("lstat_func", observe)
            values.setdefault("session_directories", (sessions,))
            values.setdefault("display_manager_link", display_link)
            return apx_host.observe_host_readiness(**values)

    def state(self, report: apx_host.HostReadinessReport, name: str) -> str:
        return next(check.classification for check in report.checks if check.name == name)

    def test_host_ready(self) -> None:
        report = self.report()
        self.assertEqual(report.overall, "ready-for-manual-experiment")

    def test_restricted_context_positive_evidence_requires_host_confirmation(self) -> None:
        report = self.report(authoritative_host=False)
        self.assertNotIn("ready", {check.classification for check in report.checks})
        self.assertEqual(report.overall, "requires-host-confirmation")

    def test_target_account_conflict(self) -> None:
        report = self.report(accounts=self.accounts + [Account("apx-trial", 1003, "/home/apx-trial")])
        self.assertEqual(self.state(report, "apx-trial account absent"), "blocked")
        self.assertEqual(report.overall, "blocked")

    def test_target_home_conflict(self) -> None:
        def exists(path: str | os.PathLike[str]) -> os.stat_result:
            return metadata()
        report = self.report(lstat_func=exists)
        self.assertEqual(self.state(report, "/home/apx-trial absent"), "blocked")

    def test_registration_conflict(self) -> None:
        report = self.report(registration=SimpleNamespace(state="valid"))
        self.assertEqual(self.state(report, "trial registration absent"), "blocked")

    def test_incomplete_marker_present(self) -> None:
        report = self.report(incomplete_operation=SimpleNamespace(absent="not-satisfied"))
        self.assertEqual(self.state(report, "trial incomplete marker absent"), "blocked")

    def test_non_btrfs_target_and_read_only_filesystem(self) -> None:
        non_btrfs = self.report(mount=SimpleNamespace(
            status="confirmed", filesystem_type="ext4", target="/home",
            options="rw", read_only=False,
        ))
        read_only = self.report(mount=SimpleNamespace(
            status="confirmed", filesystem_type="btrfs", target="/home",
            options="ro", read_only=True,
        ))
        self.assertEqual(self.state(non_btrfs, "filesystem containing /home"), "blocked")
        self.assertEqual(self.state(read_only, "mount options"), "blocked")

    def test_unsafe_parent_symlink(self) -> None:
        def symlink_parent(path: str | os.PathLike[str]) -> os.stat_result:
            if str(path) == apx_host.TRIAL_HOME:
                raise FileNotFoundError
            return metadata(stat.S_IFLNK)
        report = self.report(lstat_func=symlink_parent)
        self.assertEqual(self.state(report, "safe target parent"), "blocked")

    def test_unavailable_mount_observation(self) -> None:
        report = self.report(mount=SimpleNamespace(
            status="unavailable", filesystem_type=None, target=None,
            options=None, read_only=None,
        ))
        self.assertEqual(self.state(report, "filesystem containing /home"), "unavailable")
        self.assertEqual(report.overall, "requires-host-confirmation")

    def test_unavailable_system_bus_and_sddm_active(self) -> None:
        unavailable = self.report(
            sessions=SimpleNamespace(status="unavailable"),
            command_runner=Mock(return_value=apx_cli.CommandResult(1, "", "bus unavailable")),
        )
        active = self.report()
        self.assertEqual(self.state(unavailable, "current sessions"), "unavailable")
        self.assertEqual(self.state(unavailable, "SDDM service state"), "unavailable")
        self.assertEqual(self.state(active, "SDDM service state"), "ready")

    def test_sddm_unavailable(self) -> None:
        report = self.report(which_func=lambda name: None if name == "sddm" else f"/usr/bin/{name}")
        self.assertEqual(self.state(report, "SDDM installation"), "blocked")

    def test_graphical_session_definition_found_and_absent(self) -> None:
        found = self.report()
        with tempfile.TemporaryDirectory() as directory:
            absent = self.report(session_directories=(Path(directory),))
        self.assertEqual(self.state(found, "graphical session definitions"), "ready")
        self.assertEqual(self.state(absent, "graphical session definitions"), "blocked")

    def test_overall_readiness_precedence(self) -> None:
        checks = (
            apx_host.ReadinessCheck("x", "a", "unavailable", "x"),
            apx_host.ReadinessCheck("x", "b", "blocked", "x"),
        )
        self.assertEqual(apx_host.classify_overall(checks), "blocked")

    def test_not_applicable_does_not_affect_readiness(self) -> None:
        checks = (
            apx_host.ReadinessCheck("x", "a", "ready", "x"),
            apx_host.ReadinessCheck("x", "b", "not-applicable", "x"),
        )
        self.assertEqual(
            apx_host.classify_overall(checks), "ready-for-manual-experiment"
        )

    def test_manual_plan_is_deterministic(self) -> None:
        first = self.report()
        second = self.report()
        self.assertEqual(first.manual_plan, second.manual_plan)
        self.assertEqual(len(first.manual_plan), 9)
        self.assertIn("late commit boundary", first.manual_plan[4])

    def test_only_read_only_commands_are_invoked(self) -> None:
        self.report()
        commands = [call.args[0] for call in self.runner.call_args_list]
        self.assertEqual(commands, [("systemctl", "is-active", "sddm.service")])
        rendered = repr(commands).lower()
        for forbidden in (
            "sudo", "useradd", "groupadd", "btrfs", "chown", "chmod",
            "pacman", "write", "restart", "start ", "enable",
        ):
            self.assertNotIn(forbidden, rendered)

    def test_render_contains_overall_and_nonexecuting_plan(self) -> None:
        rendered = apx_host.render_host_readiness(self.report())
        self.assertIn("Overall readiness: ready-for-manual-experiment", rendered)
        self.assertIn("Manual experiment plan (not executed):", rendered)


if __name__ == "__main__":
    unittest.main()
