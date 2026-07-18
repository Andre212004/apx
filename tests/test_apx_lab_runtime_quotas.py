import importlib.util
import hashlib
from pathlib import Path
import re
import subprocess
import unittest
from unittest.mock import patch


RUNTIME_PATH = Path(__file__).parents[1] / "scripts" / "virtual-lab" / "apx-lab-runtime.py"
RECOVERY_PATH = Path(__file__).parents[1] / "scripts" / "physical-pilot" / "recover-development-quota-v1.sh"
PHYSICAL_BOOTSTRAP_PATH = Path(__file__).parents[1] / "scripts" / "physical-pilot" / "bootstrap-apx-headless-pilot.sh"
VM_BOOTSTRAP_PATH = Path(__file__).parents[1] / "scripts" / "virtual-lab" / "bootstrap-apx-headless-runtime.sh"
SPEC = importlib.util.spec_from_file_location("apx_lab_runtime", RUNTIME_PATH)
assert SPEC and SPEC.loader
runtime = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runtime)


class RuntimeQuotaTests(unittest.TestCase):
    def test_role_quota_policy_is_bounded_and_development_is_larger(self) -> None:
        self.assertEqual(runtime.QUOTA_LIMITS["hub"], {"root": "4G", "home": "2G"})
        self.assertEqual(runtime.QUOTA_LIMITS["minimal"], {"root": "4G", "home": "2G"})
        self.assertEqual(runtime.QUOTA_LIMITS["development"], {"root": "16G", "home": "8G"})
        self.assertEqual(runtime.QUOTA_LIMITS["graphical-h0"], {"root": "16G", "home": "8G"})

    def test_hyprland_role_maps_only_to_promoted_release(self) -> None:
        self.assertEqual(runtime.RELEASE_IDS["graphical-h0"], "hyprland-h0-v1")
        self.assertIn("graphical-h0", runtime.ROLES)
        self.assertNotIn("graphical-h0", runtime.HEADLESS_START_ROLES)

    def test_graphical_creation_populates_only_the_fixed_internal_home(self) -> None:
        source = RUNTIME_PATH.read_text()
        self.assertIn('if role == "graphical-h0":', source)
        self.assertIn('graphical_home = home / "apx"', source)
        self.assertIn('graphical_home.mkdir(mode=0o700)', source)
        self.assertIn('os.chown(graphical_home, 1000, 1000)', source)

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

    def test_generic_start_refuses_graphical_role_before_any_effect(self) -> None:
        with patch.object(runtime, "require_root"), \
             patch.object(runtime, "registration", return_value={"role": "graphical-h0"}), \
             patch.object(runtime, "machine_running") as machine_running, \
             patch.object(runtime, "append_event") as append_event, \
             patch.object(runtime, "run") as run:
            with self.assertRaisesRegex(runtime.Refusal, "separate H0"):
                runtime.start("codex-test-hyprland-h0-v1")
        machine_running.assert_not_called()
        append_event.assert_not_called()
        run.assert_not_called()


class RuntimeDestroyGenerationTests(unittest.TestCase):
    def test_destroy_plan_binds_the_registered_generation(self) -> None:
        record = {"name": "codex-test-one", "generation": "current-generation"}
        with patch.object(runtime, "registration", return_value=record), \
             patch.object(runtime, "atomic_json"):
            plan = runtime.make_plan("destroy", "codex-test-one")
        self.assertEqual(plan["generation"], "current-generation")

    def test_stale_destroy_plan_refuses_before_journal_or_stop(self) -> None:
        plan = {
            "schema": 1,
            "action": "destroy",
            "name": "codex-test-one",
            "generation": "stale-generation",
            "effects": list(runtime.EFFECTS["destroy"]),
        }
        with patch.object(runtime, "require_root"), \
             patch.object(runtime, "load_plan", return_value=plan), \
             patch.object(
                 runtime,
                 "registration",
                 return_value={"name": "codex-test-one", "generation": "current-generation"},
             ), \
             patch.object(runtime, "append_event") as append_event, \
             patch.object(runtime, "stop") as stop:
            with self.assertRaisesRegex(runtime.Refusal, "generation is stale"):
                runtime.destroy("0" * 64, "DESTROY codex-test-one")
        append_event.assert_not_called()
        stop.assert_not_called()


class PhysicalRecoveryTests(unittest.TestCase):
    def validate_quota_status(self, output: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", str(RECOVERY_PATH), "--validate-quota-status"],
            input=output,
            text=True,
            capture_output=True,
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


class BootstrapQuotaTests(unittest.TestCase):
    def test_bootstrap_sources_are_valid_and_do_not_use_the_obsolete_grep(self) -> None:
        for path in (PHYSICAL_BOOTSTRAP_PATH, VM_BOOTSTRAP_PATH):
            with self.subTest(path=path):
                subprocess.run(["bash", "-n", str(path)], check=True)
                source = path.read_text()
                self.assertNotIn("grep -q 'Enabled:.*no'", source)
                self.assertIn("quota_state", source)

    def test_bootstrap_sources_fail_closed_and_recheck_after_enabling_quotas(self) -> None:
        for path in (PHYSICAL_BOOTSTRAP_PATH, VM_BOOTSTRAP_PATH):
            with self.subTest(path=path):
                source = path.read_text()
                for required in (
                    'fields.get("mode") in {"qgroup", "qgroup (full accounting)"}',
                    'fields.get("inconsistent") == "no"',
                    'fields.get("override limits") != "yes"',
                    'fields.get("rescan status") != "running"',
                    "Btrfs quota accounting is not healthy after enablement",
                ):
                    self.assertIn(required, source)


if __name__ == "__main__":
    unittest.main()
