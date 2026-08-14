import importlib.util
import hashlib
from pathlib import Path
import re
import subprocess
import tempfile
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
    def test_official_hub_maps_to_clean_headless_v4(self) -> None:
        self.assertEqual(runtime.RELEASE_IDS["hub"], "hub-headless-v4")
        self.assertIn("hub", runtime.HEADLESS_START_ROLES)

    def test_storage_is_bounded_with_a_global_host_reserve(self) -> None:
        self.assertEqual(runtime.STORAGE_POLICY, "bounded-environments-with-protected-host-reserve")
        self.assertEqual(runtime.HOST_STORAGE_RESERVE_BYTES, 96 * 1024**3)
        self.assertEqual(runtime.ENVIRONMENT_STORAGE_LIMITS["hub"], ("16G", "32G"))
        self.assertEqual(runtime.ENVIRONMENT_STORAGE_LIMITS["development"], ("32G", "64G"))
        self.assertEqual(runtime.ENVIRONMENT_RUNTIME_LIMITS["development"], (
            "600%", "10G", "12G", "4096",
        ))

    def test_hyprland_role_maps_only_to_promoted_release(self) -> None:
        self.assertEqual(runtime.RELEASE_IDS["graphical-h0"], "hyprland-h0-v1")
        self.assertIn("graphical-h0", runtime.ROLES)
        self.assertNotIn("graphical-h0", runtime.HEADLESS_START_ROLES)

    def test_every_creation_populates_the_fixed_internal_home(self) -> None:
        source = RUNTIME_PATH.read_text()
        self.assertIn("home.chmod(0o755)", source)
        self.assertIn('user_home = home / "apx"', source)
        self.assertIn('user_home.mkdir(mode=0o700)', source)
        self.assertIn('os.chown(user_home, 1000, 1000)', source)
        self.assertIn('skeleton = root / "etc/skel"', source)

    def test_normal_shell_is_unprivileged_and_root_is_recovery_only(self) -> None:
        source = RUNTIME_PATH.read_text()
        self.assertIn('user = "root" if recovery_root else "apx"', source)
        self.assertIn('"shell-root"', source)
        self.assertIn('"enroll-local-admin"', source)
        self.assertIn("APX_LOCAL_ADMIN_V1:", source)
        self.assertIn("password enrollment did not complete", source)
        self.assertIn('password not in {"L", "P", "NP"}', source)
        self.assertIn("without trusting machinectl's exit status", source)
        self.assertIn("start the graphical Environment before enrolling its local administrator", source)
        self.assertIn("%wheel ALL=(ALL:ALL) ALL", source)
        self.assertIn("apx ALL=(ALL:ALL) ALL", source)
        self.assertNotIn("NOPASSWD", source)

    def test_terminal_boundary_is_explicit_on_entry_and_return_to_host(self) -> None:
        source = RUNTIME_PATH.read_text()
        self.assertIn("ESTÁS A ENTRAR NO ENVIRONMENT", source)
        self.assertIn("O PRÓXIMO PROMPT NÃO É O HOST", source)
        self.assertIn("SAÍSTE DO ENVIRONMENT", source)
        self.assertIn("ESTÁS DE VOLTA AO HOST 'apx-host' COMO ROOT", source)
        self.assertIn("finally:", source)
        self.assertNotIn('os.execvp("machinectl"', source)

    def test_future_graphical_roles_map_to_one_base_and_cannot_headless_start(self) -> None:
        for role in ("graphical-base", "hub-graphical"):
            self.assertEqual(runtime.RELEASE_IDS[role], "hyprland-base-v2")
            self.assertNotIn(role, runtime.HEADLESS_START_ROLES)
        source = RUNTIME_PATH.read_text()
        self.assertIn('root / "usr/share/apx/config-seeds/hyprland-minimal-v2"', source)
        self.assertIn("copy_graphical_config_seed(seed, destination)", source)

    def test_graphical_seed_copy_is_exact_and_rejects_tampering(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            seed = base / "seed"
            destination = base / "destination"
            for relative in runtime.GRAPHICAL_CONFIG_ASSETS:
                source = Path(__file__).parents[1] / "config/hyprland-base" / relative
                if relative == "hyprland/hyprland.conf":
                    source = Path(__file__).parents[1] / "config/hyprland-base/hyprland.conf"
                target = seed / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(source.read_bytes())
            with patch.object(runtime.os, "chown"):
                runtime.copy_graphical_config_seed(seed, destination)
            self.assertEqual(
                {path.relative_to(destination).as_posix() for path in destination.rglob("*")},
                set(runtime.GRAPHICAL_CONFIG_ASSETS)
                | {relative.split("/", 1)[0] for relative in runtime.GRAPHICAL_CONFIG_ASSETS},
            )

            extra = seed / "unapproved.conf"
            extra.write_text("not admitted")
            with patch.object(runtime.os, "chown"):
                with self.assertRaisesRegex(runtime.Refusal, "unapproved"):
                    runtime.copy_graphical_config_seed(seed, base / "second")

    def test_graphical_seed_copy_rejects_changed_digest_and_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            seed = base / "seed"
            for relative in runtime.GRAPHICAL_CONFIG_ASSETS:
                source = Path(__file__).parents[1] / "config/hyprland-base" / relative
                if relative == "hyprland/hyprland.conf":
                    source = Path(__file__).parents[1] / "config/hyprland-base/hyprland.conf"
                (seed / relative).parent.mkdir(parents=True, exist_ok=True)
                (seed / relative).write_bytes(source.read_bytes())
            (seed / "waybar/style.css").write_text("changed")
            with self.assertRaisesRegex(runtime.Refusal, "digest differs"):
                runtime.copy_graphical_config_seed(seed, base / "destination")
            (seed / "waybar/style.css").unlink()
            (seed / "waybar/style.css").symlink_to("config.json")
            with self.assertRaisesRegex(runtime.Refusal, "regular file"):
                runtime.copy_graphical_config_seed(seed, base / "destination")

    def test_shared_reserve_refuses_new_growth_below_96_gib(self) -> None:
        enough = type("Stats", (), {"f_bavail": 97, "f_frsize": 1024**3})()
        low = type("Stats", (), {"f_bavail": 95, "f_frsize": 1024**3})()
        with patch.object(runtime.os, "statvfs", return_value=enough):
            runtime.verify_shared_storage_reserve()
        with patch.object(runtime.os, "statvfs", return_value=low):
            with self.assertRaisesRegex(runtime.Refusal, "protected Host reserve"):
                runtime.verify_shared_storage_reserve()

    def test_subvolume_limits_bound_referenced_and_exclusive_growth(self) -> None:
        with patch.object(runtime, "run") as run:
            runtime.apply_subvolume_storage_limit(Path("/environment/root"), "32G")
        self.assertEqual(run.call_args_list[0].args[0], [
            "btrfs", "qgroup", "limit", "32G", "/environment/root",
        ])
        self.assertEqual(run.call_args_list[1].args[0], [
            "btrfs", "qgroup", "limit", "-e", "32G", "/environment/root",
        ])

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


class RuntimeHubRoleBoundaryTests(unittest.TestCase):
    def test_hub_roles_are_reserved_for_canonical_hub_name(self) -> None:
        for role in runtime.HUB_ROLES:
            self.assertEqual(runtime.validate_role_assignment("hub", role), ("hub", role))
            with self.assertRaisesRegex(runtime.Refusal, "reserved"):
                runtime.validate_role_assignment("university", role)
        for role in ("development", "minimal", "graphical-base", "graphical-h0"):
            with self.assertRaisesRegex(runtime.Refusal, "Hub name"):
                runtime.validate_role_assignment("hub", role)

    def test_creation_plan_refuses_non_hub_claim_before_release_or_write(self) -> None:
        with patch.object(runtime, "admitted_release") as release, \
             patch.object(runtime, "atomic_json") as write:
            with self.assertRaisesRegex(runtime.Refusal, "reserved"):
                runtime.make_plan("create", "university", "hub-graphical")
        release.assert_not_called()
        write.assert_not_called()

    def test_registration_refuses_forged_hub_role(self) -> None:
        forged = {"name": "university", "role": "hub-graphical", "state": "stopped"}
        with patch.object(runtime, "read_json", return_value=forged):
            with self.assertRaisesRegex(runtime.Refusal, "reserved"):
                runtime.registration("university")

    def test_restore_refuses_hub_archive_to_workload_before_target_creation(self) -> None:
        manifest = {"role": "hub-graphical"}
        with patch.object(runtime, "require_root"), \
             patch.object(runtime, "validate_archive", return_value=Path("/archive")), \
             patch.object(runtime, "read_json", return_value=manifest), \
             patch.object(Path, "exists", return_value=False), \
             patch.object(Path, "mkdir") as mkdir:
            with self.assertRaisesRegex(runtime.Refusal, "reserved"):
                runtime.restore("archive-hub-generation-copy", "university", "RESTORE archive-hub-generation-copy AS university")
        mkdir.assert_not_called()


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
