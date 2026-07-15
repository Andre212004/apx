import importlib.util
import hashlib
from pathlib import Path
import re
import subprocess
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


if __name__ == "__main__":
    unittest.main()
