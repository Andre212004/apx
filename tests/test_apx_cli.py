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
from unittest.mock import Mock, patch


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


def mount_json(
    *,
    fstype: str = "btrfs",
    options: str = "rw,relatime",
    filesystems: str | None = None,
) -> str:
    if filesystems is not None:
        return filesystems
    return (
        '{"filesystems":[{"target":"/home","source":"/dev/test[/@home]",'
        f'"fstype":"{fstype}","options":"{options}"}}]}}'
    )


def successful_mount_result(**kwargs: str) -> apx_cli.CommandResult:
    return apx_cli.CommandResult(0, mount_json(**kwargs), "")


def successful_btrfs_result() -> apx_cli.CommandResult:
    return apx_cli.CommandResult(0, "Name: apx-development\nUUID: test\n", "")


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
        self.command_runner = Mock(
            side_effect=[successful_mount_result(), successful_btrfs_result()]
        )

    def run_command(self, argv: list[str]) -> tuple[int, str, str]:
        stdout = StringIO()
        stderr = StringIO()
        code = apx_cli.run(
            argv,
            accounts_provider=lambda: self.accounts,
            stat_func=self.stat_mock,
            command_runner=self.command_runner,
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
        self.command_runner.assert_not_called()


class MountObservationTests(unittest.TestCase):
    def observe(self, result: apx_cli.CommandResult) -> apx_cli.MountObservation:
        runner = Mock(return_value=result)
        observation = apx_cli.observe_mount("/home/apx-test", runner)
        runner.assert_called_once_with(
            ("findmnt", "--json", "--target", "/home/apx-test"), 3.0
        )
        return observation

    def test_valid_btrfs_result(self) -> None:
        result = self.observe(successful_mount_result())
        self.assertEqual(result.status, "confirmed")
        self.assertEqual(result.filesystem_type, "btrfs")
        self.assertEqual(result.target, "/home")
        self.assertEqual(result.source, "/dev/test[/@home]")

    def test_valid_non_btrfs_result(self) -> None:
        result = self.observe(successful_mount_result(fstype="ext4"))
        self.assertEqual(result.filesystem_type, "ext4")

    def test_ro_mount(self) -> None:
        result = self.observe(successful_mount_result(options="ro,nosuid"))
        self.assertTrue(result.read_only)
        self.assertEqual(result.status, "confirmed")

    def test_rw_mount(self) -> None:
        result = self.observe(successful_mount_result(options="rw,nosuid"))
        self.assertFalse(result.read_only)
        self.assertEqual(result.status, "confirmed")

    def test_missing_ro_rw_is_ambiguous(self) -> None:
        result = self.observe(successful_mount_result(options="nosuid,nodev"))
        self.assertIsNone(result.read_only)
        self.assertEqual(result.status, "ambiguous")

    def test_malformed_json_is_unavailable(self) -> None:
        result = self.observe(apx_cli.CommandResult(0, "{", ""))
        self.assertEqual(result.status, "unavailable")
        self.assertIn("malformed JSON", result.explanation)

    def test_unexpected_schema_is_unavailable(self) -> None:
        result = self.observe(apx_cli.CommandResult(0, '{"filesystems":{}}', ""))
        self.assertEqual(result.status, "unavailable")
        self.assertIn("unexpected JSON schema", result.explanation)

    def test_empty_result_is_unavailable(self) -> None:
        result = self.observe(
            apx_cli.CommandResult(0, '{"filesystems":[]}', "")
        )
        self.assertEqual(result.status, "unavailable")
        self.assertIn("no filesystem", result.explanation)

    def test_multiple_results_are_ambiguous(self) -> None:
        data = (
            '{"filesystems":['
            '{"target":"/","source":"a","fstype":"btrfs","options":"rw"},'
            '{"target":"/home","source":"b","fstype":"btrfs","options":"rw"}]}'
        )
        result = self.observe(apx_cli.CommandResult(0, data, ""))
        self.assertEqual(result.status, "ambiguous")

    def test_missing_executable_is_unavailable(self) -> None:
        result = self.observe(
            apx_cli.CommandResult(None, "", "", "missing executable")
        )
        self.assertEqual(result.status, "unavailable")
        self.assertIn("missing executable", result.explanation)

    def test_timeout_is_unavailable(self) -> None:
        result = self.observe(apx_cli.CommandResult(None, "", "", "timeout"))
        self.assertEqual(result.status, "unavailable")
        self.assertIn("timeout", result.explanation)

    def test_unexpected_nonzero_is_unavailable(self) -> None:
        result = self.observe(apx_cli.CommandResult(7, "", "unexpected"))
        self.assertEqual(result.status, "unavailable")
        self.assertIn("exit code 7", result.explanation)


class BtrfsObservationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.mount = apx_cli.MountObservation(
            "confirmed", "btrfs", "/home", "/dev/test", "rw", False, "observed"
        )

    def observe(self, result: apx_cli.CommandResult) -> apx_cli.BtrfsObservation:
        runner = Mock(return_value=result)
        observation = apx_cli.observe_btrfs(
            "/home/apx-test", self.mount, runner
        )
        runner.assert_called_once_with(
            ("btrfs", "subvolume", "show", "/home/apx-test"), 5.0
        )
        return observation

    def test_confirmed_subvolume(self) -> None:
        result = self.observe(successful_btrfs_result())
        self.assertEqual(result.subvolume, "yes")

    def test_narrowly_confirmed_non_subvolume(self) -> None:
        result = self.observe(
            apx_cli.CommandResult(
                1, "", "ERROR: Not a Btrfs subvolume: Invalid argument\n"
            )
        )
        self.assertEqual(result.subvolume, "no")

    def test_non_btrfs_is_not_applicable_and_skips_command(self) -> None:
        mount = apx_cli.MountObservation(
            "confirmed", "ext4", "/", "/dev/test", "rw", False, "observed"
        )
        runner = Mock()
        result = apx_cli.observe_btrfs("/home/apx-test", mount, runner)
        self.assertEqual(result.filesystem, "no")
        self.assertEqual(result.subvolume, "not applicable")
        runner.assert_not_called()

    def test_permission_denied_is_unavailable(self) -> None:
        result = self.observe(
            apx_cli.CommandResult(1, "", "ERROR: Permission denied")
        )
        self.assertEqual(result.subvolume, "unavailable")
        self.assertIn("Permission denied", result.explanation)

    def test_missing_executable_is_unavailable(self) -> None:
        result = self.observe(
            apx_cli.CommandResult(None, "", "", "missing executable")
        )
        self.assertEqual(result.subvolume, "unavailable")
        self.assertIn("missing executable", result.explanation)

    def test_inaccessible_path_is_unavailable(self) -> None:
        result = self.observe(
            apx_cli.CommandResult(1, "", "No such file or directory")
        )
        self.assertEqual(result.subvolume, "unavailable")
        self.assertIn("inaccessible", result.explanation)

    def test_timeout_is_unavailable(self) -> None:
        result = self.observe(apx_cli.CommandResult(None, "", "", "timeout"))
        self.assertEqual(result.subvolume, "unavailable")
        self.assertIn("timeout", result.explanation)

    def test_unexpected_nonzero_is_not_classified_as_no(self) -> None:
        result = self.observe(apx_cli.CommandResult(1, "", "unknown failure"))
        self.assertEqual(result.subvolume, "unavailable")
        self.assertNotEqual(result.subvolume, "no")

    def test_success_with_malformed_output_is_ambiguous(self) -> None:
        result = self.observe(apx_cli.CommandResult(0, "unexpected", ""))
        self.assertEqual(result.subvolume, "ambiguous")

    def test_diagnostic_is_sanitized(self) -> None:
        result = self.observe(
            apx_cli.CommandResult(1, "", "failure\nwith\tcontrol\x1b[31m")
        )
        self.assertNotIn("\n", result.explanation)
        self.assertNotIn("\x1b", result.explanation)


class CommandRunnerTests(unittest.TestCase):
    @patch("apx_cli.subprocess.run")
    def test_runner_uses_safe_arguments_timeout_and_locale(
        self, subprocess_run: Mock
    ) -> None:
        subprocess_run.return_value = subprocess.CompletedProcess(
            ("findmnt",), 0, "output", ""
        )
        result = apx_cli.run_command(
            ("findmnt", "--json", "--target", "/home/apx-test"), 3.0
        )
        self.assertEqual(result.returncode, 0)
        arguments, = subprocess_run.call_args.args
        self.assertEqual(
            arguments,
            ("findmnt", "--json", "--target", "/home/apx-test"),
        )
        options = subprocess_run.call_args.kwargs
        self.assertFalse(options["shell"])
        self.assertEqual(options["timeout"], 3.0)
        self.assertEqual(options["env"]["LC_ALL"], "C")
        self.assertNotIn("sudo", arguments)
        self.assertNotIn(arguments[0], {"mount", "umount", "chown", "chmod"})

    @patch("apx_cli.subprocess.run", side_effect=FileNotFoundError)
    def test_runner_structures_missing_executable(self, _run: Mock) -> None:
        result = apx_cli.run_command(("findmnt",), 3.0)
        self.assertEqual(result.failure, "missing executable")

    @patch("apx_cli.subprocess.run")
    def test_runner_bounds_output(self, subprocess_run: Mock) -> None:
        subprocess_run.return_value = subprocess.CompletedProcess(
            ("findmnt",), 1, "x" * 9000, "y" * 9000
        )
        result = apx_cli.run_command(("findmnt",), 3.0)
        self.assertEqual(len(result.stdout), apx_cli.COMMAND_OUTPUT_LIMIT)
        self.assertEqual(len(result.stderr), apx_cli.COMMAND_OUTPUT_LIMIT)


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
