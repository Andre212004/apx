import importlib.util
import hashlib
import os
from pathlib import Path
import re
import subprocess
import sys
import unittest
from unittest.mock import patch


RUNTIME_PATH = Path(__file__).parents[1] / "scripts" / "virtual-lab" / "apx-lab-runtime.py"
RECOVERY_PATH = Path(__file__).parents[1] / "scripts" / "physical-pilot" / "recover-development-quota-v1.sh"
SPEC = importlib.util.spec_from_file_location("apx_lab_runtime", RUNTIME_PATH)
assert SPEC and SPEC.loader
runtime = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runtime)


class RuntimeQuotaTests(unittest.TestCase):
    def test_role_quota_policy_is_bounded_and_development_is_larger(self) -> None:
        self.assertEqual(runtime.QUOTA_LIMITS["hub"], {"root": "4G", "home": "2G"})
        self.assertEqual(runtime.QUOTA_LIMITS["minimal"], {"root": "4G", "home": "2G"})
        self.assertEqual(runtime.QUOTA_LIMITS["development"], {"root": "16G", "home": "8G"})

    def test_apply_limits_uses_role_policy_for_both_qgroup_limits(self) -> None:
        completed = type("Result", (), {"stdout": "300\n"})()
        with patch.object(runtime, "environment_dir", return_value=Path("/state/development")), \
             patch.object(runtime, "run", return_value=completed) as run:
            runtime.apply_limits("development", "development")
        self.assertEqual(
            [call.args[0] for call in run.call_args_list],
            [
                ["btrfs", "inspect-internal", "rootid", "/state/development/root"],
                ["btrfs", "qgroup", "limit", "16G", "0/300", "/var/lib/apx"],
                ["btrfs", "qgroup", "limit", "-e", "16G", "0/300", "/var/lib/apx"],
                ["btrfs", "inspect-internal", "rootid", "/state/development/home"],
                ["btrfs", "qgroup", "limit", "8G", "0/300", "/var/lib/apx"],
                ["btrfs", "qgroup", "limit", "-e", "8G", "0/300", "/var/lib/apx"],
            ],
        )

    def test_unknown_role_is_refused(self) -> None:
        with self.assertRaises(runtime.Refusal):
            runtime.apply_limits("development", "unknown")


class PhysicalRecoveryTests(unittest.TestCase):
    def recovery_env(self) -> dict[str, str]:
        return {
            **os.environ,
            "PATH": f"{Path(sys.executable).parent}:{os.environ.get('PATH', '')}",
        }

    def validate_quota_status(self, output: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", str(RECOVERY_PATH), "--validate-quota-status"],
            input=output,
            text=True,
            capture_output=True,
            env=self.recovery_env(),
        )

    def limit_for_qgroup(self, identity: int, output: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", str(RECOVERY_PATH), "--limit-for-qgroup", str(identity)],
            input=output,
            text=True,
            capture_output=True,
            env=self.recovery_env(),
        )

    def test_recovery_script_is_valid_and_bound_to_matching_runtime(self) -> None:
        subprocess.run(["bash", "-n", str(RECOVERY_PATH)], check=True)
        source = RECOVERY_PATH.read_text()
        expected = re.search(r"^readonly RUNTIME_SHA256=([0-9a-f]{64})$", source, re.MULTILINE)
        self.assertIsNotNone(expected)
        self.assertEqual(expected.group(1), hashlib.sha256(RUNTIME_PATH.read_bytes()).hexdigest())

    def test_recovery_requires_identity_inactivity_old_limits_and_approval(self) -> None:
        source = RECOVERY_PATH.read_text()
        for required in (
            "systemd-detect-virt",
            "apx-physical-headless-pilot-v1",
            "machinectl show apx-development",
            '"state": "stopped"',
            'OLD_ROOT_BYTES=4294967296',
            'OLD_HOME_BYTES=2147483648',
            'APPROVAL=\'RESIZE development FROM 4G+2G TO 16G+8G\'',
            "trap rollback ERR",
        ):
            self.assertIn(required, source)

    def test_quota_status_accepts_both_supported_btrfs_formats(self) -> None:
        outputs = (
            "Status: enabled\nMode: qgroup\nInconsistent: no\n",
            "Quotas on /var/lib/apx:\n  Enabled: yes\n  Mode: qgroup (full accounting)\n  Inconsistent: no\n  Override limits: no\n",
        )
        for output in outputs:
            with self.subTest(output=output):
                self.assertEqual(self.validate_quota_status(output).returncode, 0)

    def test_quota_status_refuses_disabled_non_qgroup_and_inconsistent(self) -> None:
        outputs = (
            "Enabled: no\nMode: qgroup (full accounting)\nInconsistent: no\n",
            "Enabled: yes\nMode: squota (simple accounting)\nInconsistent: no\n",
            "Enabled: yes\nMode: qgroup (full accounting)\nInconsistent: yes\n",
        )
        for output in outputs:
            with self.subTest(output=output):
                self.assertNotEqual(self.validate_quota_status(output).returncode, 0)

    def test_recovery_uses_verified_private_btrfs_top_level_for_every_qgroup_operation(self) -> None:
        source = RECOVERY_PATH.read_text()
        for required in (
            'filesystem_uuid=$(findmnt -n -o UUID -T "$STATE")',
            'mount -t btrfs -o subvolid=5 "UUID=$filesystem_uuid" "$TOP_LEVEL"',
            '[[ $(findmnt -n -o UUID -T "$TOP_LEVEL") == "$filesystem_uuid" ]]',
            '[[ $(btrfs inspect-internal rootid "$TOP_LEVEL") == 5 ]]',
            'trap cleanup_top_level EXIT',
        ):
            self.assertIn(required, source)
        qgroup_lines = [line for line in source.splitlines() if "btrfs qgroup" in line]
        self.assertGreaterEqual(len(qgroup_lines), 10)
        self.assertTrue(all('"$TOP_LEVEL"' in line for line in qgroup_lines))
        self.assertNotIn('btrfs qgroup show --raw -reF "$STATE"', source)
        self.assertNotIn('btrfs qgroup show --raw -reF "$TOP_LEVEL"', source)
        self.assertIn('btrfs qgroup show --raw -re "$TOP_LEVEL"', source)

    def test_qgroup_filter_regression_for_top_level_mount(self) -> None:
        filtered_output = (
            "qgroupid         rfer         excl     max_rfer     max_excl path\n"
            "0/5                 0            0         none         none <toplevel>\n"
        )
        unfiltered_output = (
            "qgroupid         rfer         excl     max_rfer     max_excl path\n"
            "0/5                 0            0         none         none <toplevel>\n"
            "0/279      2147483648   2147483648   4294967296   4294967296 @apx/environments/development/root\n"
            "0/280      1073741824   1073741824   2147483648   2147483648 @apx/environments/development/home\n"
        )

        self.assertNotEqual(self.limit_for_qgroup(279, filtered_output).returncode, 0)
        root = self.limit_for_qgroup(279, unfiltered_output)
        home = self.limit_for_qgroup(280, unfiltered_output)
        self.assertEqual((root.returncode, root.stdout.strip()), (0, "4294967296 4294967296"))
        self.assertEqual((home.returncode, home.stdout.strip()), (0, "2147483648 2147483648"))
        self.assertNotEqual(self.limit_for_qgroup(281, unfiltered_output).returncode, 0)

        duplicate_output = unfiltered_output + (
            "0/279      2147483648   2147483648   4294967296   4294967296 @duplicate/root\n"
        )
        self.assertNotEqual(self.limit_for_qgroup(279, duplicate_output).returncode, 0)


if __name__ == "__main__":
    unittest.main()
