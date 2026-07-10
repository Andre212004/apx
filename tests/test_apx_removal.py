from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import os
import stat
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_removal
import apx_cli


def metadata(uid: int = 1003, mode: int = 0o700) -> os.stat_result:
    return os.stat_result([stat.S_IFDIR | mode, 0, 0, 0, uid, uid, 0, 0, 0, 0])


def evidence(**changes):
    values = dict(
        logical_name="trial", account_name="apx-trial", canonical_home="/home/apx-trial",
        account=SimpleNamespace(pw_name="apx-trial", pw_uid=1003, pw_gid=1003, pw_dir="/home/apx-trial"),
        home_state="present", home_metadata=metadata(), subvolume="yes", sessions=0,
        processes="none", mounts="none", contents="empty", usage="4096 bytes", registration="absent",
    )
    values.update(changes)
    return apx_removal.RemovalEvidence(**values)


class RemovalPlanTests(unittest.TestCase):
    def test_ps_empty_exit_one_confirms_no_processes(self) -> None:
        runner = lambda argv, timeout: apx_cli.CommandResult(1, "", "")
        self.assertEqual(apx_removal._processes(runner, "apx-trial"), ("confirmed", ""))

    def test_ready_state(self) -> None:
        report = apx_removal.build_removal_report(evidence())
        self.assertEqual(report.overall, "ready for a separately approved removal operation")

    def test_active_sessions_processes_and_mounts_block(self) -> None:
        report = apx_removal.build_removal_report(evidence(sessions=1, processes="present (2)", mounts="present"))
        self.assertEqual(report.overall, "blocked")
        blocked = {item.name for item in report.checks if item.classification == "blocked"}
        self.assertTrue({"Active sessions", "Running processes", "Associated mounts"} <= blocked)

    def test_unknown_home_and_btrfs_evidence_is_incomplete(self) -> None:
        report = apx_removal.build_removal_report(evidence(contents="unavailable", usage="unavailable", subvolume="unavailable"))
        self.assertEqual(report.overall, "incomplete because evidence is unavailable")

    def test_nonempty_home_is_ready_but_identified_as_loss(self) -> None:
        report = apx_removal.build_removal_report(evidence(contents="non-empty (2 top-level entries: a, b)", usage="10 bytes"))
        self.assertEqual(next(x.classification for x in report.checks if x.name == "Home contents"), "ready")
        self.assertIn("non-empty", " ".join(report.loss))

    def test_non_btrfs_home_has_explicit_ready_type(self) -> None:
        report = apx_removal.build_removal_report(evidence(subvolume="no"))
        check = next(x for x in report.checks if x.name == "Btrfs home type")
        self.assertEqual((check.classification, check.evidence), ("ready", "no"))

    def test_noncanonical_home_blocks(self) -> None:
        account = SimpleNamespace(pw_uid=1003, pw_gid=1003, pw_dir="/tmp/wrong")
        report = apx_removal.build_removal_report(evidence(account=account))
        self.assertEqual(report.overall, "blocked")

    def test_nonexistent_environment(self) -> None:
        report = apx_removal.build_removal_report(evidence(account=None, home_state="absent", home_metadata=None, contents="absent", usage="0 bytes", subvolume="not applicable"))
        self.assertEqual(report.overall, "Environment does not exist")
        self.assertEqual(report.plan, ())

    def test_hub_is_protected(self) -> None:
        report = apx_removal.build_removal_report(evidence(logical_name="hub", account_name="apx-hub", canonical_home="/home/apx-hub"))
        self.assertEqual(report.overall, "protected Environment")
        self.assertEqual(report.plan, ())

    def test_plan_and_output_are_deterministic(self) -> None:
        first = apx_removal.build_removal_report(evidence())
        second = apx_removal.build_removal_report(evidence())
        self.assertEqual(first, second)
        self.assertEqual(len(first.plan), 9)
        self.assertEqual(apx_removal.render_removal_report(first), apx_removal.render_removal_report(second))
        self.assertIn("Overall result:", apx_removal.render_removal_report(first).splitlines()[-1])


if __name__ == "__main__":
    unittest.main()
