from __future__ import annotations

from contextlib import redirect_stderr
from io import StringIO
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_cli


class Account:
    def __init__(self, name: str, uid: int, home: str) -> None:
        self.pw_name = name
        self.pw_uid = uid
        self.pw_dir = home


def stat_result(*, uid: int, directory: bool = True) -> os.stat_result:
    mode = (stat.S_IFDIR if directory else stat.S_IFREG) | 0o700
    values = [mode, 0, 0, 0, uid, 0, 0, 0, 0, 0]
    return os.stat_result(values)


class ParserTests(unittest.TestCase):
    def test_status_parser(self) -> None:
        args = apx_cli.create_parser().parse_args(["status"])
        self.assertEqual(args.command, "status")

    def test_environment_list_parser(self) -> None:
        args = apx_cli.create_parser().parse_args(["environment", "list"])
        self.assertEqual(args.environment_command, "list")

    def test_environment_inspect_parser(self) -> None:
        args = apx_cli.create_parser().parse_args(
            ["environment", "inspect", "apx-hub"]
        )
        self.assertEqual(args.name, "apx-hub")


class DiscoveryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.accounts = [
            Account("ordinary-user", 1000, "/home/ordinary-user"),
            Account("apx-research", 1003, "/home/apx-research"),
            Account("apx-development", 1002, "/home/apx-development"),
            Account("apx-hub", 1001, "/home/apx-hub"),
        ]

    def matching_stat(self, path: str) -> os.stat_result:
        uid_by_path = {
            "/home/apx-hub": 1001,
            "/home/apx-development": 1002,
            "/home/apx-research": 1003,
        }
        return stat_result(uid=uid_by_path[path])

    def test_detects_named_and_other_candidates_and_ignores_unrelated(self) -> None:
        candidates = apx_cli.discover_candidates(self.accounts, self.matching_stat)
        self.assertEqual(
            [candidate.name for candidate in candidates],
            ["apx-hub", "apx-development", "apx-research"],
        )
        self.assertEqual(candidates[0].role, "hub")
        self.assertEqual(candidates[1].role, "development")
        self.assertEqual(candidates[2].role, "candidate")

    def test_deterministic_ordering(self) -> None:
        forward = apx_cli.discover_candidates(self.accounts, self.matching_stat)
        reverse = apx_cli.discover_candidates(
            reversed(self.accounts), self.matching_stat
        )
        self.assertEqual(forward, reverse)

    def test_missing_home_is_inconsistent(self) -> None:
        def missing(_path: str) -> os.stat_result:
            raise FileNotFoundError

        candidate = apx_cli.discover_candidates([self.accounts[3]], missing)[0]
        self.assertFalse(candidate.home_exists)
        self.assertIsNone(candidate.home_is_directory)
        self.assertEqual(candidate.state, "inconsistent")

    def test_non_directory_home_is_inconsistent(self) -> None:
        candidate = apx_cli.discover_candidates(
            [self.accounts[3]], lambda _path: stat_result(uid=1001, directory=False)
        )[0]
        self.assertFalse(candidate.home_is_directory)
        self.assertEqual(candidate.state, "inconsistent")

    def test_matching_ownership_is_consistent(self) -> None:
        candidate = apx_cli.discover_candidates(
            [self.accounts[3]], lambda _path: stat_result(uid=1001)
        )[0]
        self.assertTrue(candidate.ownership_matches)
        self.assertEqual(candidate.state, "consistent")

    def test_ownership_mismatch_is_inconsistent(self) -> None:
        candidate = apx_cli.discover_candidates(
            [self.accounts[3]], lambda _path: stat_result(uid=9999)
        )[0]
        self.assertFalse(candidate.ownership_matches)
        self.assertEqual(candidate.state, "inconsistent")

    def test_observation_error_is_unavailable(self) -> None:
        def denied(_path: str) -> os.stat_result:
            raise PermissionError("denied")

        candidate = apx_cli.discover_candidates([self.accounts[3]], denied)[0]
        self.assertIsNone(candidate.home_exists)
        self.assertEqual(candidate.state, "unavailable")


class CommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self.accounts = [Account("apx-hub", 1001, "/home/apx-hub")]
        self.stat_mock = Mock(return_value=stat_result(uid=1001))

    def run_command(self, argv: list[str]) -> tuple[int, str, str]:
        stdout = StringIO()
        stderr = StringIO()
        code = apx_cli.run(
            argv,
            accounts_provider=lambda: self.accounts,
            stat_func=self.stat_mock,
            stdout=stdout,
            stderr=stderr,
        )
        return code, stdout.getvalue(), stderr.getvalue()

    def test_status_stable_output(self) -> None:
        code, output, error = self.run_command(["status"])
        self.assertEqual(code, 0)
        self.assertEqual(error, "")
        self.assertEqual(
            output,
            "APX status\n"
            "Mode: read-only prototype\n"
            "Candidate environments: 1\n"
            "Consistent candidates: 1\n"
            "Warnings: 0\n",
        )

    def test_list_stable_output(self) -> None:
        code, output, _error = self.run_command(["environment", "list"])
        self.assertEqual(code, 0)
        self.assertEqual(
            output,
            "NAME     UID   HOME           ROLE  STATE\n"
            "apx-hub  1001  /home/apx-hub  hub   consistent\n",
        )

    def test_inspect_requires_exact_candidate_name(self) -> None:
        code, output, error = self.run_command(
            ["environment", "inspect", "apx-hub"]
        )
        self.assertEqual(code, 0)
        self.assertIn("Environment candidate: apx-hub\n", output)
        self.assertEqual(error, "")

    def test_unknown_candidate_returns_two(self) -> None:
        code, output, error = self.run_command(
            ["environment", "inspect", "apx-unknown"]
        )
        self.assertEqual(code, 2)
        self.assertEqual(output, "")
        self.assertEqual(
            error, "Unknown Environment candidate: apx-unknown\n"
        )

    def test_inspect_rejects_partial_candidate_name(self) -> None:
        code, output, error = self.run_command(
            ["environment", "inspect", "apx"]
        )
        self.assertEqual(code, 2)
        self.assertEqual(output, "")
        self.assertEqual(error, "Unknown Environment candidate: apx\n")

    def test_internal_observation_error_returns_one(self) -> None:
        stderr = StringIO()
        with redirect_stderr(StringIO()):
            code = apx_cli.run(
                ["status"],
                accounts_provider=Mock(side_effect=RuntimeError("failed")),
                stdout=StringIO(),
                stderr=stderr,
            )
        self.assertEqual(code, 1)
        self.assertEqual(stderr.getvalue(), "APX observation error: failed\n")

    def test_injected_observations_do_not_touch_real_machine(self) -> None:
        self.run_command(["status"])
        self.stat_mock.assert_called_once_with("/home/apx-hub")


class EntryPointTests(unittest.TestCase):
    def test_entry_point_works_outside_repository_working_directory(self) -> None:
        with tempfile.TemporaryDirectory() as working_directory:
            result = subprocess.run(
                [str(ROOT / "apx"), "status"],
                cwd=working_directory,
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("APX status\n", result.stdout)
        self.assertEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main()
