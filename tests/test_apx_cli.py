from __future__ import annotations

from contextlib import redirect_stderr
from io import StringIO
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_cli
import apx_environment


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
    return apx_cli.CommandResult(
        0,
        "Name: apx-development\n"
        "Subvolume ID: 256\n"
        "UUID: 11111111-1111-4111-8111-111111111111\n"
        "Parent UUID: -\n",
        "",
    )


class ParserTests(unittest.TestCase):
    def test_status_parser(self) -> None:
        args = apx_cli.create_parser().parse_args(["status"])
        self.assertEqual(args.command, "status")

    def test_host_check_parser(self) -> None:
        args = apx_cli.create_parser().parse_args(["host", "check"])
        self.assertEqual((args.command, args.host_command), ("host", "check"))

    def test_host_validate_parser(self) -> None:
        args = apx_cli.create_parser().parse_args(["host", "validate"])
        self.assertEqual((args.command, args.host_command), ("host", "validate"))

    def test_host_check_complete_report_returns_zero(self) -> None:
        stdout = StringIO()
        with patch("apx_cli.observe_registration", return_value=SimpleNamespace(state="absent")), \
             patch("apx_cli.observe_incomplete_operation", return_value=SimpleNamespace(absent="confirmed")), \
             patch("apx_cli.observe_mount", return_value=SimpleNamespace(status="unavailable")), \
             patch("apx_cli.observe_sessions", return_value=SimpleNamespace(status="unavailable")), \
             patch("apx_cli.observe_host_readiness", return_value=SimpleNamespace(checks=(), overall="requires-host-confirmation", manual_plan=())):
            result = apx_cli.run(
                ["host", "check"],
                accounts_provider=lambda: (),
                stdout=stdout,
            )
        self.assertEqual(result, 0)
        self.assertIn("Overall readiness: requires-host-confirmation", stdout.getvalue())

    def test_environment_list_parser(self) -> None:
        args = apx_cli.create_parser().parse_args(["environment", "list"])
        self.assertEqual(args.environment_command, "list")

    def test_environment_removal_plan_parser(self) -> None:
        args = apx_cli.create_parser().parse_args(["environment", "removal-plan", "trial"])
        self.assertEqual((args.environment_command, args.logical_name), ("removal-plan", "trial"))

    def test_environment_inspect_parser(self) -> None:
        args = apx_cli.create_parser().parse_args(
            ["environment", "inspect", "apx-hub"]
        )
        self.assertEqual(args.name, "apx-hub")

    def test_session_list_parser(self) -> None:
        args = apx_cli.create_parser().parse_args(["session", "list"])
        self.assertEqual(args.command, "session")
        self.assertEqual(args.session_command, "list")


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

    def run_inspect_with_registration(
        self, account: str, registration_name: str | None, content: str | None
    ) -> tuple[int, str, str]:
        uid = 1001
        self.accounts = [Account(account, uid, f"/home/{account}")]
        self.stat_mock = Mock(return_value=stat_result(uid=uid))
        self.command_runner = Mock(
            side_effect=[successful_mount_result(), successful_btrfs_result()]
        )
        with tempfile.TemporaryDirectory() as directory:
            if registration_name is not None and content is not None:
                (Path(directory) / f"{registration_name}.json").write_text(
                    content, encoding="utf-8"
                )
            stdout = StringIO()
            stderr = StringIO()
            code = apx_cli.run(
                ["environment", "inspect", account],
                accounts_provider=lambda: self.accounts,
                stat_func=self.stat_mock,
                command_runner=self.command_runner,
                registration_directory=directory,
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
        self.assertIn("Registration:\n", output)
        self.assertEqual(error, "")

    def test_inspect_maps_accounts_to_canonical_registration_files(self) -> None:
        for account, logical_name in (
            ("apx-hub", "hub"),
            ("apx-development", "development"),
            ("apx-work", "work"),
        ):
            identity = apx_environment.derive_identity(logical_name)
            value = apx_environment.serialize_registration(
                apx_environment.EnvironmentRegistration(
                    1, logical_name, identity.role, identity.account, identity.home,
                    "active",
                    apx_environment.StorageIdentity(
                        "btrfs", 256,
                        "11111111-1111-4111-8111-111111111111", None,
                    ),
                )
            )
            code, output, error = self.run_inspect_with_registration(
                account, logical_name, value
            )
            with self.subTest(account=account):
                self.assertEqual(code, 0)
                self.assertEqual(error, "")
                self.assertIn(f"Expected path: ", output)
                self.assertIn(f"/{logical_name}.json\n", output)
                self.assertIn("  Observation: valid\n", output)
                self.assertIn(f"  Logical name: {logical_name}\n", output)
                self.assertIn("Formal classification: incomplete\n", output)

    def test_absent_and_malformed_registration_render_safely(self) -> None:
        absent_code, absent, _ = self.run_inspect_with_registration(
            "apx-work", None, None
        )
        malformed_code, malformed, _ = self.run_inspect_with_registration(
            "apx-work", "work", "{secret contents"
        )
        self.assertEqual(absent_code, 0)
        self.assertIn("  Observation: absent\n", absent)
        self.assertIn("Formal classification: candidate\n", absent)
        self.assertEqual(malformed_code, 0)
        self.assertIn("  Observation: malformed\n", malformed)
        self.assertIn(
            "  Reason: registration JSON does not match schema version 1\n",
            malformed,
        )
        self.assertNotIn("secret contents", malformed)

    def test_valid_registration_with_confirmed_home_mismatch_is_incomplete(self) -> None:
        identity = apx_environment.derive_identity("work")
        value = apx_environment.serialize_registration(
            apx_environment.EnvironmentRegistration(
                1, "work", identity.role, identity.account, identity.home, "active",
                apx_environment.StorageIdentity(
                    "btrfs", 256,
                    "11111111-1111-4111-8111-111111111111", None,
                ),
            )
        )
        self.stat_mock = Mock(return_value=stat_result(uid=9999))
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / "work.json").write_text(value, encoding="utf-8")
            stdout = StringIO()
            code = apx_cli.run(
                ["environment", "inspect", "apx-work"],
                accounts_provider=lambda: [
                    Account("apx-work", 1001, "/home/apx-work")
                ],
                stat_func=self.stat_mock,
                command_runner=Mock(
                    side_effect=[successful_mount_result(), successful_btrfs_result()]
                ),
                registration_directory=directory,
                stdout=stdout,
                stderr=StringIO(),
            )
        self.assertEqual(code, 0)
        self.assertIn("Formal classification: incomplete\n", stdout.getvalue())

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
        self.assertEqual(result.subvolume_id, 256)
        self.assertEqual(result.subvolume_uuid, "11111111-1111-4111-8111-111111111111")
        self.assertIsNone(result.parent_uuid)
        self.assertTrue(result.parent_uuid_observed)
        self.assertEqual(result.identity_status, "confirmed")

    def test_missing_or_malformed_identity_is_not_confirmed(self) -> None:
        missing = self.observe(apx_cli.CommandResult(0, "Name: work\n", ""))
        malformed = self.observe(
            apx_cli.CommandResult(
                0,
                "Name: work\nSubvolume ID: x\nUUID: invalid\nParent UUID: invalid\n",
                "",
            )
        )
        self.assertEqual(missing.identity_status, "unavailable")
        self.assertEqual(malformed.identity_status, "ambiguous")
        self.assertIsNone(malformed.subvolume_uuid)
        self.assertFalse(malformed.parent_uuid_observed)

    def test_duplicate_and_malformed_identity_fields_are_ambiguous_per_field(self) -> None:
        duplicate = self.observe(
            apx_cli.CommandResult(
                0,
                "Subvolume ID: 256\nSubvolume ID: 257\n"
                "UUID: 11111111-1111-4111-8111-111111111111\n"
                "Parent UUID: -\n",
                "",
            )
        )
        malformed = self.observe(
            apx_cli.CommandResult(
                0,
                "Subvolume ID: 0\n"
                "UUID: 11111111-1111-4111-8111-111111111111\n"
                "Parent UUID: -\n",
                "",
            )
        )
        self.assertEqual(duplicate.subvolume_id_status, "ambiguous")
        self.assertEqual(malformed.subvolume_id_status, "ambiguous")
        self.assertEqual(duplicate.subvolume_uuid_status, "confirmed")

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


def session_properties(
    *,
    session_id: str = "3",
    name: str = "apx-development",
    uid: str = "1002",
    state: str | None = "active",
    active: str | None = "yes",
    session_type: str | None = "wayland",
    session_class: str | None = "user",
    seat: str | None = "seat0",
    remote: str | None = "no",
    vt: str | None = "2",
    extra: str = "",
) -> str:
    values = {
        "Id": session_id,
        "Name": name,
        "User": uid,
        "State": state,
        "Active": active,
        "Type": session_type,
        "Class": session_class,
        "Seat": seat,
        "Remote": remote,
        "Service": "test-service",
        "VTNr": vt,
    }
    lines = [f"{key}={value}" for key, value in values.items() if value is not None]
    if extra:
        lines.append(extra)
    return "\n".join(lines) + "\n"


class SessionObservationTests(unittest.TestCase):
    def setUp(self) -> None:
        accounts = [
            Account("apx-hub", 1001, "/home/apx-hub"),
            Account("apx-development", 1002, "/home/apx-development"),
        ]
        self.candidates = apx_cli.discover_candidates(
            accounts, lambda path: stat_result(uid=1001 if path.endswith("hub") else 1002)
        )

    def observe(
        self,
        enumeration: apx_cli.CommandResult,
        details: dict[str, apx_cli.CommandResult] | None = None,
    ) -> tuple[apx_cli.SessionListObservation, Mock]:
        details = details or {}

        def execute(arguments: tuple[str, ...], _timeout: float) -> apx_cli.CommandResult:
            if arguments[1] == "list-sessions":
                return enumeration
            return details[arguments[2]]

        runner = Mock(side_effect=execute)
        return apx_cli.observe_sessions(self.candidates, runner), runner

    def test_no_sessions(self) -> None:
        result, runner = self.observe(apx_cli.CommandResult(0, "", ""))
        self.assertEqual(result.sessions, ())
        self.assertEqual(result.status, "confirmed")
        runner.assert_called_once_with(
            ("loginctl", "list-sessions", "--no-legend", "--no-pager"), 3.0
        )

    def test_one_graphical_apx_session_and_exact_commands(self) -> None:
        result, runner = self.observe(
            apx_cli.CommandResult(0, "3 1002 apx-development seat0 tty2\n", ""),
            {"3": apx_cli.CommandResult(0, session_properties(), "")},
        )
        session = result.sessions[0]
        self.assertEqual(session.username, "apx-development")
        self.assertEqual(session.graphical, "yes")
        self.assertEqual(session.status, "confirmed")
        show_arguments, timeout = runner.call_args_list[1].args
        self.assertEqual(
            show_arguments,
            (
                "loginctl", "show-session", "3", "--no-pager",
                "--property=Id", "--property=Name", "--property=User",
                "--property=State", "--property=Active", "--property=Type",
                "--property=Class", "--property=Seat", "--property=Remote",
                "--property=Service",
                "--property=VTNr",
            ),
        )
        self.assertEqual(session.vt, "2")
        self.assertEqual(timeout, 3.0)
        self.assertNotIn("sudo", show_arguments)
        self.assertNotIn(show_arguments[0], {"systemctl", "login", "logout"})

    def test_apx_tty_session_is_not_graphical(self) -> None:
        result, _ = self.observe(
            apx_cli.CommandResult(0, "7 1001 apx-hub seat0 tty1\n", ""),
            {
                "7": apx_cli.CommandResult(
                    0,
                    session_properties(
                        session_id="7", name="apx-hub", uid="1001",
                        session_type="tty",
                    ),
                    "",
                )
            },
        )
        self.assertEqual(result.sessions[0].graphical, "no")

    def test_multiple_sessions_and_numeric_aware_ordering(self) -> None:
        enumeration = "10 1002 apx-development - -\nc1 1002 apx-development - -\n2 1002 apx-development - -\n"
        details = {
            session_id: apx_cli.CommandResult(
                0, session_properties(session_id=session_id), ""
            )
            for session_id in ("10", "c1", "2")
        }
        result, _ = self.observe(apx_cli.CommandResult(0, enumeration, ""), details)
        self.assertEqual(
            [session.session_id for session in result.sessions], ["2", "10", "c1"]
        )

    def test_unrelated_users_are_filtered(self) -> None:
        result, _ = self.observe(
            apx_cli.CommandResult(0, "4 2000 ordinary-user - -\n", ""),
            {
                "4": apx_cli.CommandResult(
                    0,
                    session_properties(name="ordinary-user", uid="2000"),
                    "",
                )
            },
        )
        self.assertEqual(result.sessions, ())

    def test_missing_properties_are_unavailable(self) -> None:
        result, _ = self.observe(
            apx_cli.CommandResult(0, "3 1002 apx-development - -\n", ""),
            {
                "3": apx_cli.CommandResult(
                    0,
                    session_properties(state=None, session_type=None, seat=None),
                    "",
                )
            },
        )
        session = result.sessions[0]
        self.assertEqual(session.state, "unavailable")
        self.assertEqual(session.graphical, "unavailable")
        self.assertEqual(session.status, "unavailable")

    def test_identity_conflict_is_ambiguous(self) -> None:
        result, _ = self.observe(
            apx_cli.CommandResult(0, "3 1001 apx-hub - -\n", ""),
            {"3": apx_cli.CommandResult(0, session_properties(), "")},
        )
        self.assertEqual(result.sessions[0].username, "ambiguous")
        self.assertEqual(result.sessions[0].status, "ambiguous")

    def test_detailed_session_id_conflict_is_ambiguous(self) -> None:
        result, _ = self.observe(
            apx_cli.CommandResult(0, "3 1002 apx-development - -\n", ""),
            {
                "3": apx_cli.CommandResult(
                    0, session_properties(session_id="different"), ""
                )
            },
        )
        self.assertEqual(result.sessions[0].status, "ambiguous")

    def test_one_failed_session_does_not_discard_another(self) -> None:
        enumeration = "3 1002 apx-development - -\n7 1001 apx-hub - -\n"
        result, _ = self.observe(
            apx_cli.CommandResult(0, enumeration, ""),
            {
                "3": apx_cli.CommandResult(0, session_properties(), ""),
                "7": apx_cli.CommandResult(None, "", "", "timeout"),
            },
        )
        self.assertEqual(len(result.sessions), 2)
        self.assertEqual(result.sessions[0].status, "confirmed")
        self.assertEqual(result.sessions[1].status, "unavailable")

    def test_missing_loginctl_is_unavailable(self) -> None:
        result, _ = self.observe(
            apx_cli.CommandResult(None, "", "", "missing executable")
        )
        self.assertEqual(result.status, "unavailable")
        self.assertIn("missing executable", result.explanation or "")

    def test_logind_unavailable_is_structured(self) -> None:
        result, _ = self.observe(
            apx_cli.CommandResult(1, "", "System has not been booted with systemd")
        )
        self.assertEqual(result.status, "unavailable")
        self.assertIn("exit code 1", result.explanation or "")

    def test_enumeration_timeout_is_unavailable(self) -> None:
        result, _ = self.observe(apx_cli.CommandResult(None, "", "", "timeout"))
        self.assertEqual(result.status, "unavailable")
        self.assertIn("timeout", result.explanation or "")

    def test_malformed_enumeration_and_session_id_are_not_executed(self) -> None:
        result, runner = self.observe(
            apx_cli.CommandResult(0, "--bad 1002 apx-development\nmalformed\n", "")
        )
        self.assertEqual(result.status, "ambiguous")
        self.assertIn("Malformed", result.explanation or "")
        self.assertEqual(runner.call_count, 1)

    def test_malformed_property_output_is_ambiguous(self) -> None:
        result, _ = self.observe(
            apx_cli.CommandResult(0, "3 1002 apx-development - -\n", ""),
            {
                "3": apx_cli.CommandResult(
                    0, session_properties(extra="malformed-property"), ""
                )
            },
        )
        self.assertEqual(result.sessions[0].status, "ambiguous")

    def test_conflicting_type_is_graphically_ambiguous(self) -> None:
        result, _ = self.observe(
            apx_cli.CommandResult(0, "3 1002 apx-development - -\n", ""),
            {
                "3": apx_cli.CommandResult(
                    0, session_properties(extra="Type=tty"), ""
                )
            },
        )
        self.assertEqual(result.sessions[0].session_type, "ambiguous")
        self.assertEqual(result.sessions[0].graphical, "ambiguous")

    def test_session_cap_is_reported_and_bounded(self) -> None:
        enumeration = "\n".join(
            f"{number} 2000 ordinary-user - -" for number in range(101)
        )
        details = {
            str(number): apx_cli.CommandResult(
                0,
                session_properties(
                    session_id=str(number), name="ordinary-user", uid="2000"
                ),
                "",
            )
            for number in range(100)
        }
        result, runner = self.observe(
            apx_cli.CommandResult(0, enumeration + "\n", ""), details
        )
        self.assertTrue(result.truncated)
        self.assertIn("truncated to 100", result.explanation or "")
        self.assertEqual(runner.call_count, 101)

    def test_render_unavailable_result(self) -> None:
        result = apx_cli.SessionListObservation(
            (), "unavailable", "loginctl missing executable.", False
        )
        self.assertEqual(
            apx_cli.render_session_list(result),
            "APX sessions\n"
            "Status: unavailable\n"
            "Sessions: none\n"
            "Explanation: loginctl missing executable.",
        )

    def test_unavailable_logind_command_returns_zero(self) -> None:
        stdout = StringIO()
        stderr = StringIO()
        code = apx_cli.run(
            ["session", "list"],
            accounts_provider=lambda: [
                Account("apx-development", 1002, "/home/apx-development")
            ],
            stat_func=lambda _path: stat_result(uid=1002),
            command_runner=Mock(
                return_value=apx_cli.CommandResult(
                    None, "", "", "missing executable"
                )
            ),
            stdout=stdout,
            stderr=stderr,
        )
        self.assertEqual(code, 0)
        self.assertIn("Status: unavailable\n", stdout.getvalue())
        self.assertEqual(stderr.getvalue(), "")


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

    def test_entry_point_disables_bytecode_writes(self) -> None:
        with tempfile.TemporaryDirectory() as working_directory:
            cache_prefix = Path(working_directory) / "python-cache"
            environment = os.environ.copy()
            environment["PYTHONPYCACHEPREFIX"] = str(cache_prefix)
            result = subprocess.run(
                [str(ROOT / "apx"), "status"],
                cwd=working_directory,
                check=False,
                capture_output=True,
                text=True,
                env=environment,
            )
            cache_created = cache_prefix.exists()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(cache_created)


if __name__ == "__main__":
    unittest.main()
