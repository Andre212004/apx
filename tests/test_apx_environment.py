from __future__ import annotations

from io import StringIO
import os
from pathlib import Path
import stat
import sys
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


def stat_result(uid: int = 1003) -> os.stat_result:
    values = [stat.S_IFDIR | 0o700, 0, 0, 0, uid, 0, 0, 0, 0, 0]
    return os.stat_result(values)


def mount_result(
    *, fstype: str = "btrfs", options: str = "ro,nosuid"
) -> apx_cli.CommandResult:
    output = (
        '{"filesystems":[{"target":"/home","source":"/dev/test[/@home]",'
        f'"fstype":"{fstype}","options":"{options}"}}]}}'
    )
    return apx_cli.CommandResult(0, output, "")


def preconditions(**changes: object) -> apx_environment.CreationPreconditions:
    values: dict[str, object] = {
        "account_absent": "confirmed",
        "home_absent": "confirmed",
        "candidate_exists": "no",
        "filesystem_type": "btrfs",
        "filesystem_status": "confirmed",
        "host_confirmation_required": True,
    }
    values.update(changes)
    return apx_environment.CreationPreconditions(**values)


class NamingTests(unittest.TestCase):
    def test_valid_simple_name(self) -> None:
        self.assertIsNone(apx_environment.validate_logical_name("work"))

    def test_valid_internal_hyphen(self) -> None:
        self.assertIsNone(apx_environment.validate_logical_name("client-work2"))

    def test_uppercase_is_rejected(self) -> None:
        self.assertIsNotNone(apx_environment.validate_logical_name("Work"))

    def test_leading_digit_is_rejected(self) -> None:
        self.assertIsNotNone(apx_environment.validate_logical_name("2work"))

    def test_trailing_hyphen_is_rejected(self) -> None:
        self.assertIsNotNone(apx_environment.validate_logical_name("work-"))

    def test_repeated_hyphen_is_rejected(self) -> None:
        self.assertIsNotNone(apx_environment.validate_logical_name("client--work"))

    def test_derived_prefix_is_rejected(self) -> None:
        self.assertIn(
            "apx-",
            apx_environment.validate_logical_name("apx-work") or "",
        )

    def test_reserved_names_are_rejected(self) -> None:
        for name in ("root", "nobody", "system"):
            with self.subTest(name=name):
                self.assertEqual(
                    apx_environment.validate_logical_name(name), "is reserved"
                )

    def test_maximum_length_is_valid(self) -> None:
        self.assertIsNone(apx_environment.validate_logical_name("a" * 27))

    def test_oversized_name_is_rejected(self) -> None:
        self.assertIn(
            "at most 27",
            apx_environment.validate_logical_name("a" * 28) or "",
        )

    def test_shell_metacharacters_are_rejected(self) -> None:
        for name in ("work;id", "work$(id)", "work name"):
            with self.subTest(name=name):
                self.assertIsNotNone(apx_environment.validate_logical_name(name))

    def test_slashes_and_traversal_are_rejected(self) -> None:
        for name in ("../work", "team/work", "."):
            with self.subTest(name=name):
                self.assertIsNotNone(apx_environment.validate_logical_name(name))

    def test_unicode_is_rejected(self) -> None:
        self.assertIsNotNone(apx_environment.validate_logical_name("wörk"))


class IdentityTests(unittest.TestCase):
    def test_account_and_home_are_derived_deterministically(self) -> None:
        first = apx_environment.derive_identity("work")
        second = apx_environment.derive_identity("work")
        self.assertEqual(first, second)
        self.assertEqual(first.account, "apx-work")
        self.assertEqual(first.home, "/home/apx-work")

    def test_hub_role(self) -> None:
        self.assertEqual(apx_environment.derive_identity("hub").role, "hub")

    def test_development_role(self) -> None:
        self.assertEqual(
            apx_environment.derive_identity("development").role, "development"
        )

    def test_standard_role(self) -> None:
        self.assertEqual(apx_environment.derive_identity("work").role, "standard")


class PlanningTests(unittest.TestCase):
    def test_eligible_architecture_still_has_blocked_apply(self) -> None:
        plan = apx_environment.create_plan(
            apx_environment.derive_identity("work"), preconditions()
        )
        self.assertEqual(
            plan.architectural_eligibility, "eligible-for-future-apply"
        )
        self.assertEqual(plan.apply_availability, "blocked")

    def test_conflict_blocks_architectural_eligibility(self) -> None:
        plan = apx_environment.create_plan(
            apx_environment.derive_identity("work"),
            preconditions(account_absent="no"),
        )
        self.assertEqual(plan.architectural_eligibility, "blocked")

    def test_unavailable_or_ambiguous_observation_requires_confirmation(self) -> None:
        for status in ("unavailable", "ambiguous"):
            with self.subTest(status=status):
                plan = apx_environment.create_plan(
                    apx_environment.derive_identity("work"),
                    preconditions(
                        filesystem_type="unavailable",
                        filesystem_status=status,
                    ),
                )
                self.assertEqual(
                    plan.architectural_eligibility,
                    "requires-host-confirmation",
                )

    def test_non_btrfs_parent_blocks_plan(self) -> None:
        plan = apx_environment.create_plan(
            apx_environment.derive_identity("work"),
            preconditions(filesystem_type="ext4"),
        )
        self.assertEqual(plan.architectural_eligibility, "blocked")

    def test_stable_digest_and_output(self) -> None:
        plan = apx_environment.create_plan(
            apx_environment.derive_identity("work"), preconditions()
        )
        self.assertEqual(
            apx_environment.plan_digest(plan),
            apx_environment.plan_digest(plan),
        )
        self.assertEqual(
            apx_environment.render_creation_plan(plan),
            apx_environment.render_creation_plan(plan),
        )

    def test_digest_changes_with_name(self) -> None:
        work = apx_environment.create_plan(
            apx_environment.derive_identity("work"), preconditions()
        )
        study = apx_environment.create_plan(
            apx_environment.derive_identity("study"), preconditions()
        )
        self.assertNotEqual(
            apx_environment.plan_digest(work),
            apx_environment.plan_digest(study),
        )

    def test_digest_changes_with_relevant_precondition(self) -> None:
        first = apx_environment.create_plan(
            apx_environment.derive_identity("work"), preconditions()
        )
        second = apx_environment.create_plan(
            apx_environment.derive_identity("work"),
            preconditions(home_absent="no"),
        )
        self.assertNotEqual(
            apx_environment.plan_digest(first),
            apx_environment.plan_digest(second),
        )

    def test_output_has_no_timestamp_or_random_state(self) -> None:
        output = apx_environment.render_creation_plan(
            apx_environment.create_plan(
                apx_environment.derive_identity("work"), preconditions()
            )
        )
        self.assertNotIn("Timestamp", output)
        self.assertNotIn("Random", output)
        self.assertIn("future plan binding only", output)

    def test_changes_are_descriptions_and_rollback_is_bounded(self) -> None:
        output = apx_environment.render_creation_plan(
            apx_environment.create_plan(
                apx_environment.derive_identity("work"), preconditions()
            )
        )
        self.assertIn("Planned changes:", output)
        self.assertIn("when safe", output)
        self.assertIn("Do not delete pre-existing or user-owned data.", output)


class CreationCommandTests(unittest.TestCase):
    def run_create(
        self,
        *,
        name: str = "work",
        accounts: list[Account] | None = None,
        stat_func: object | None = None,
        command_result: apx_cli.CommandResult | None = None,
        command_runner: Mock | None = None,
    ) -> tuple[int, str, str, Mock]:
        stdout = StringIO()
        stderr = StringIO()
        runner = command_runner or Mock(
            return_value=command_result or mount_result()
        )
        if stat_func is None:
            def missing(_path: str) -> os.stat_result:
                raise FileNotFoundError
            selected_stat = missing
        else:
            selected_stat = stat_func
        code = apx_cli.run(
            ["environment", "create", name, "--dry-run"],
            accounts_provider=lambda: accounts or [],
            stat_func=selected_stat,
            command_runner=runner,
            stdout=stdout,
            stderr=stderr,
        )
        return code, stdout.getvalue(), stderr.getvalue(), runner

    def test_account_and_home_absent(self) -> None:
        code, output, error, _ = self.run_create()
        self.assertEqual(code, 0)
        self.assertIn("Account absent: confirmed", output)
        self.assertIn("Home absent: confirmed", output)
        self.assertEqual(error, "")

    def test_existing_account_and_matching_candidate_block(self) -> None:
        account = Account("apx-work", 1003, "/home/apx-work")
        code, output, _, _ = self.run_create(accounts=[account])
        self.assertEqual(code, 0)
        self.assertIn("Account absent: no", output)
        self.assertIn("Candidate exists: yes", output)
        self.assertIn("Architectural eligibility: blocked", output)

    def test_existing_home_blocks(self) -> None:
        code, output, _, _ = self.run_create(stat_func=lambda _path: stat_result())
        self.assertEqual(code, 0)
        self.assertIn("Home absent: no", output)
        self.assertIn("Architectural eligibility: blocked", output)

    def test_non_btrfs_parent_blocks(self) -> None:
        _, output, _, _ = self.run_create(command_result=mount_result(fstype="ext4"))
        self.assertIn("Home filesystem: ext4", output)
        self.assertIn("Architectural eligibility: blocked", output)

    def test_unavailable_filesystem_requires_confirmation(self) -> None:
        _, output, _, _ = self.run_create(
            command_result=apx_cli.CommandResult(
                None, "", "", "missing executable"
            )
        )
        self.assertIn("Filesystem observation: unavailable", output)
        self.assertIn("requires-host-confirmation", output)

    def test_ambiguous_mount_requires_confirmation(self) -> None:
        _, output, _, _ = self.run_create(
            command_result=mount_result(options="nosuid,nodev")
        )
        self.assertIn("Filesystem observation: ambiguous", output)
        self.assertIn("requires-host-confirmation", output)

    def test_only_read_only_findmnt_command_is_invoked(self) -> None:
        _, _, _, runner = self.run_create()
        runner.assert_called_once_with(
            ("findmnt", "--json", "--target", "/home"), 3.0
        )
        arguments = runner.call_args.args[0]
        forbidden = {
            "sudo", "useradd", "usermod", "groupadd", "btrfs", "chown",
            "chmod", "systemctl", "mkdir", "mount",
        }
        self.assertTrue(forbidden.isdisjoint(arguments))

    def test_invalid_name_returns_two_without_observation(self) -> None:
        runner = Mock()
        code, output, error, _ = self.run_create(
            name="apx-work", command_runner=runner
        )
        self.assertEqual(code, 2)
        self.assertEqual(output, "")
        self.assertIn("Invalid Environment logical name", error)
        runner.assert_not_called()

    def test_internal_failure_returns_one(self) -> None:
        code, output, error, _ = self.run_create(
            command_runner=Mock(side_effect=RuntimeError("failed"))
        )
        self.assertEqual(code, 1)
        self.assertEqual(output, "")
        self.assertEqual(error, "APX observation error: failed\n")

    def test_dry_run_is_required_and_arbitrary_identity_options_rejected(self) -> None:
        parser = apx_cli.create_parser()
        with self.assertRaises(SystemExit) as dry_run_error:
            parser.parse_args(["environment", "create", "work"])
        self.assertEqual(dry_run_error.exception.code, 2)
        with self.assertRaises(SystemExit) as identity_error:
            parser.parse_args(
                ["environment", "create", "work", "--dry-run", "--home", "/tmp/x"]
            )
        self.assertEqual(identity_error.exception.code, 2)

    def test_plan_performs_no_file_writes(self) -> None:
        with patch("builtins.open", side_effect=AssertionError("write attempted")):
            code, _, _, _ = self.run_create()
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
