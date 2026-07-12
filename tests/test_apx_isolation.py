from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from dataclasses import replace
import json
import stat
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_cli
import apx_isolation


class Account:
    def __init__(self, name: str) -> None:
        self.pw_name = name


class IsolationReadinessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.commands: list[tuple[str, ...]] = []

    def runner(self, arguments, timeout):
        self.commands.append(tuple(arguments))
        if tuple(arguments) == ("lspci", "-Dnnk"):
            return apx_cli.CommandResult(
                0,
                "VGA controller [1002:aaaa] AMD\n3D controller [10de:bbbb] NVIDIA\n",
                "",
            )
        return apx_cli.CommandResult(0, "confirmed fixture evidence\n", "")

    @staticmethod
    def absent(path: str):
        raise FileNotFoundError(path)

    def report(self, **changes):
        values = {
            "accounts": (),
            "registration": SimpleNamespace(state="absent"),
            "incomplete_operation": SimpleNamespace(absent="confirmed"),
            "command_runner": self.runner,
            "which_func": lambda name: f"/usr/bin/{name}",
            "lstat_func": self.absent,
            "read_text_func": lambda path: "apx-development:100000:65536\n",
            "authoritative_host": True,
        }
        values.update(changes)
        return apx_isolation.observe_isolation_readiness(**values)

    def state(self, report, name):
        return next(check.classification for check in report.checks if check.name == name)

    def test_authoritative_ready_fixture(self) -> None:
        report = self.report()
        self.assertEqual(report.overall, "ready-for-stage-2-design-review")
        self.assertTrue(all(isinstance(command, tuple) for command in self.commands))

    def test_restricted_positive_evidence_requires_confirmation(self) -> None:
        report = self.report(authoritative_host=False)
        self.assertEqual(report.overall, "requires-host-confirmation")
        self.assertNotIn("satisfied", {check.classification for check in report.checks})

    def test_identity_conflicts_block(self) -> None:
        account = self.report(accounts=(Account(apx_isolation.EXPERIMENT_ACCOUNT),))
        home = self.report(lstat_func=lambda path: SimpleNamespace())
        registration = self.report(registration=SimpleNamespace(state="valid"))
        marker = self.report(incomplete_operation=SimpleNamespace(absent="not-satisfied"))
        self.assertEqual(account.overall, "blocked")
        self.assertEqual(home.overall, "blocked")
        self.assertEqual(registration.overall, "blocked")
        self.assertEqual(marker.overall, "blocked")

    def test_missing_mandatory_and_optional_tools_differ(self) -> None:
        report = self.report(which_func=lambda name: None)
        self.assertEqual(self.state(report, "system container runtime"), "blocked")
        self.assertEqual(self.state(report, "Podman alternative backend"), "not-applicable")

    def test_missing_or_ambiguous_subordinate_ids_block(self) -> None:
        missing = self.report(read_text_func=lambda path: "other:100000:65536\n")
        duplicate = self.report(
            read_text_func=lambda path: (
                "apx-development:100000:65536\n"
                "apx-development:200000:65536\n"
            )
        )
        self.assertEqual(
            self.state(missing, "subuid allocation for apx-development"), "blocked"
        )
        self.assertEqual(
            self.state(duplicate, "subgid allocation for apx-development"), "blocked"
        )

    def test_machine_or_image_collision_blocks(self) -> None:
        def collision(arguments, timeout):
            if arguments[:2] == ("machinectl", "list"):
                return apx_cli.CommandResult(0, "isolation-trial container running\n", "")
            return apx_cli.CommandResult(0, "fixture\n", "")

        report = self.report(command_runner=collision)
        self.assertEqual(self.state(report, "registered systemd machines"), "blocked")

    def test_gpu_presence_and_absence_are_separate(self) -> None:
        def amd_only(arguments, timeout):
            if arguments == ("lspci", "-Dnnk"):
                return apx_cli.CommandResult(0, "VGA compatible controller [1002:abcd] AMD\n", "")
            return apx_cli.CommandResult(0, "fixture\n", "")

        report = self.report(command_runner=amd_only)
        self.assertEqual(self.state(report, "AMD graphics"), "satisfied")
        self.assertEqual(self.state(report, "NVIDIA graphics"), "blocked")

    def test_failed_command_is_unavailable(self) -> None:
        def failed(arguments, timeout):
            return apx_cli.CommandResult(1, "", "denied")

        report = self.report(command_runner=failed)
        self.assertEqual(self.state(report, "kernel and architecture"), "unavailable")
        self.assertEqual(report.overall, "requires-host-confirmation")

    def test_only_fixed_read_only_commands_are_used(self) -> None:
        self.report()
        self.assertEqual(
            self.commands,
            [
                ("uname", "-srvmo"),
                ("systemctl", "--version"),
                ("findmnt", "--json", "--output", "TARGET,FSTYPE,OPTIONS", "--target", "/sys/fs/cgroup"),
                ("sysctl", "-n", "user.max_user_namespaces"),
                ("findmnt", "--json", "--output", "TARGET,SOURCE,FSTYPE,OPTIONS,AVAIL", "--target", "/home"),
                ("machinectl", "list", "--no-legend", "--no-pager"),
                ("machinectl", "list-images", "--no-legend", "--no-pager"),
                ("lspci", "-Dnnk"),
            ],
        )

    def test_render_is_deterministic_and_contains_no_plan_to_apply(self) -> None:
        report = self.report()
        first = apx_isolation.render_isolation_readiness(report)
        second = apx_isolation.render_isolation_readiness(report)
        self.assertEqual(first, second)
        self.assertIn("Mode: read-only Stage 0 observation", first)
        self.assertIn("do not create a container", first)

    def test_plain_doctor_waits_for_untrusted_positive_evidence(self) -> None:
        rendered = apx_isolation.render_isolation_doctor(
            self.report(authoritative_host=False)
        )
        self.assertIn("Result: WAIT", rendered)
        self.assertIn("Nothing was changed", rendered)
        self.assertIn("apx-trial account will not be reused", rendered)

    def test_plain_doctor_stops_on_a_failed_requirement(self) -> None:
        rendered = apx_isolation.render_isolation_doctor(
            self.report(which_func=lambda name: None)
        )
        self.assertIn("Result: STOP", rendered)
        self.assertIn("system container runtime", rendered)


class IsolationPlanTests(unittest.TestCase):
    def test_plan_is_fixed_deterministic_and_blocked(self) -> None:
        first = apx_isolation.build_isolation_experiment_plan()
        second = apx_isolation.build_isolation_experiment_plan()
        self.assertEqual(first, second)
        self.assertEqual(len(first.steps), 10)
        self.assertEqual(len(first.digest), 64)
        self.assertEqual(first.approval, "blocked-pending-explicit-stage-2-approval")

    def test_plan_contains_no_commands_or_caller_controlled_values(self) -> None:
        plan = apx_isolation.build_isolation_experiment_plan()
        self.assertFalse(hasattr(plan, "commands"))
        self.assertFalse(hasattr(plan, "arguments"))
        self.assertEqual(plan.logical_name, "isolation-trial")
        self.assertEqual(plan.account_name, "apx-isolation-trial")
        self.assertEqual(
            apx_isolation.BASE_PACKAGES,
            ("base", "ca-certificates", "dbus-broker", "iproute2", "iputils", "sudo"),
        )
        self.assertEqual(dict(apx_isolation.RESOURCE_POLICY)["memory_max"], "3GiB")

    def test_render_is_stable_and_non_executing(self) -> None:
        plan = apx_isolation.build_isolation_experiment_plan()
        output = apx_isolation.render_isolation_experiment_plan(plan)
        self.assertIn("Mode: plan only; no host changes", output)
        self.assertIn(f"Plan digest: {plan.digest}", output)
        self.assertIn("Base packages: base, ca-certificates", output)
        self.assertIn("root_budget=8GiB", output)
        self.assertNotIn("sudo ", output)


class SnapshotAcquisitionPlanTests(unittest.TestCase):
    def test_plan_is_fixed_deterministic_bounded_and_blocked(self) -> None:
        first = apx_isolation.build_snapshot_acquisition_plan()
        second = apx_isolation.build_snapshot_acquisition_plan()
        self.assertEqual(first, second)
        self.assertEqual(first.snapshot_date, "2026/07/11")
        self.assertEqual(first.repositories, ("core", "extra"))
        self.assertEqual(first.seed_packages, apx_isolation.BASE_PACKAGES)
        self.assertEqual(
            first.keyring_artifact,
            "archlinux-keyring-20260707.1-1-any.pkg.tar.zst",
        )
        self.assertEqual(
            first.keyring_artifact_sha256,
            "b47fc9c8066377e73d72bdb6a166bbbd829d5dcc745e424ef32436bd673cbc0d",
        )
        self.assertEqual(
            first.keyring_signer_fingerprint,
            "0429897DE5F3BDAC537A30696D42BDD116E0068F",
        )
        self.assertEqual(first.host_keyring_package, "archlinux-keyring 20260707.1-1")
        self.assertEqual(first.host_keyring_files, apx_isolation.OBSERVED_HOST_KEYRING_FILES)
        self.assertEqual(len(first.trust_bootstrap_digest), 64)
        self.assertIn("trusted-host-installed", first.trust_bootstrap)
        self.assertIn("pacman-7.1.0", first.resolver_tool)
        self.assertIn("pacman-key-7.1.0", first.verification_tool)
        self.assertIn("gnupg-2.4.9", first.independent_validation_tool)
        self.assertEqual(first.approval, "blocked-plan-only")
        self.assertEqual(len(first.digest), 64)
        self.assertEqual(dict(first.limits)["aggregate_download_max"], "4GiB")
        self.assertEqual(dict(first.limits)["resolved_package_max_count"], "512")

    def test_plan_contains_no_commands_or_caller_selected_values(self) -> None:
        plan = apx_isolation.build_snapshot_acquisition_plan()
        self.assertFalse(hasattr(plan, "commands"))
        self.assertFalse(hasattr(plan, "arguments"))
        self.assertFalse(hasattr(plan, "mirror"))
        self.assertTrue(plan.source_uri.startswith("https://archive.archlinux.org/"))
        self.assertTrue(plan.staging_path.startswith("/var/lib/apx/staging/"))
        self.assertGreaterEqual(len(plan.blockers), 4)

    def test_render_is_stable_complete_and_non_executing(self) -> None:
        plan = apx_isolation.build_snapshot_acquisition_plan()
        output = apx_isolation.render_snapshot_acquisition_plan(plan)
        self.assertEqual(output, apx_isolation.render_snapshot_acquisition_plan(plan))
        self.assertIn("no network, downloads, filesystem writes, or host changes", output)
        self.assertIn("Keyring artifact: archlinux-keyring-20260707.1-1", output)
        self.assertIn("Keyring artifact SHA-256: b47fc9c8", output)
        self.assertIn("pkgver: 20260707.1-1", output)
        self.assertIn("Resolver/acquirer: pacman-7.1.0", output)
        self.assertIn("Independent verifier: gnupg-2.4.9", output)
        self.assertIn("retry_max: 2", output)
        self.assertIn(f"Plan digest: {plan.digest}", output)

    def test_digest_covers_limits_paths_and_blockers(self) -> None:
        plan = apx_isolation.build_snapshot_acquisition_plan()
        self.assertEqual(
            plan.digest,
            apx_isolation.compute_snapshot_acquisition_plan_digest(plan),
        )
        variants = (
            replace(plan, limits=plan.limits + (("extra", "1"),)),
            replace(plan, staging_path="/different"),
            replace(plan, keyring_artifact_sha256="0" * 64),
            replace(plan, blockers=plan.blockers + ("new blocker",)),
        )
        for variant in variants:
            self.assertNotEqual(
                plan.digest,
                apx_isolation.compute_snapshot_acquisition_plan_digest(variant),
            )


class SnapshotTrustReadinessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.commands = []

    def runner(self, arguments, timeout):
        self.commands.append(tuple(arguments))
        return apx_cli.CommandResult(0, "fixture evidence", "")

    @staticmethod
    def regular_file(path):
        return SimpleNamespace(
            st_mode=stat.S_IFREG | 0o644,
            st_dev=1,
            st_ino=2,
            st_size=3,
            st_uid=0,
            st_gid=0,
        )

    def report(self, **changes):
        values = {
            "command_runner": self.runner,
            "which_func": lambda name: f"/usr/bin/{name}",
            "lstat_func": self.regular_file,
            "authoritative_host": True,
        }
        values.update(changes)
        return apx_isolation.observe_snapshot_trust_readiness(**values)

    def test_authoritative_fixture_is_ready_and_uses_only_fixed_commands(self) -> None:
        report = self.report()
        self.assertEqual(report.overall, "ready-for-stage-2-design-review")
        self.assertEqual(
            self.commands,
            [
                ("pacman", "-Q", "--", "archlinux-keyring", "pacman", "gnupg"),
                ("pacman", "-Qkk", "archlinux-keyring"),
                ("pacman", "--version"),
                ("pacman-key", "--version"),
                ("gpg", "--version"),
                ("sha256sum", *apx_isolation.SNAPSHOT_TRUST_FILES),
            ],
        )

    def test_missing_tool_or_non_regular_keyring_file_blocks(self) -> None:
        missing_tool = self.report(which_func=lambda name: None)
        non_regular = self.report(
            lstat_func=lambda path: SimpleNamespace(st_mode=stat.S_IFLNK)
        )
        self.assertEqual(missing_tool.overall, "blocked")
        self.assertEqual(non_regular.overall, "blocked")

    def test_unavailable_command_and_restricted_positive_need_confirmation(self) -> None:
        failed = self.report(
            command_runner=lambda arguments, timeout: apx_cli.CommandResult(
                1, "", "denied"
            )
        )
        restricted = self.report(authoritative_host=False)
        self.assertEqual(failed.overall, "requires-host-confirmation")
        self.assertEqual(restricted.overall, "requires-host-confirmation")

    def test_render_is_deterministic_and_explicitly_non_mutating(self) -> None:
        report = self.report()
        output = apx_isolation.render_snapshot_trust_readiness(report)
        self.assertEqual(
            output,
            apx_isolation.render_snapshot_trust_readiness(report),
        )
        self.assertIn("read-only fixed observation", output)
        self.assertIn("do not download or mutate trust state", output)


class Stage2DossierTests(unittest.TestCase):
    def test_dossier_is_fixed_deterministic_and_blocked(self) -> None:
        first = apx_isolation.build_stage2_approval_dossier()
        second = apx_isolation.build_stage2_approval_dossier()
        self.assertEqual(first, second)
        self.assertEqual(len(first.resources), 5)
        self.assertEqual(len(first.digest), 64)
        self.assertEqual(
            first.approval,
            "blocked-pending-review-and-separate-explicit-stage2-approval",
        )
        self.assertEqual(
            first.acquisition_plan_digest,
            apx_isolation.build_snapshot_acquisition_plan().digest,
        )

    def test_resources_have_identity_proof_and_publication_state(self) -> None:
        dossier = apx_isolation.build_stage2_approval_dossier()
        for resource in dossier.resources:
            self.assertTrue(resource.identity_evidence)
            self.assertEqual(resource.initial_state, "must-be-absent")
            self.assertTrue(resource.publication_state)
        root = next(item for item in dossier.resources if item.resource_type == "environment-root")
        home = next(item for item in dossier.resources if item.resource_type == "environment-home")
        self.assertEqual(root.quota, "8GiB")
        self.assertEqual(home.quota, "2GiB")
        self.assertIn("Btrfs UUID", root.identity_evidence)
        self.assertIn("operation provenance", home.identity_evidence)

    def test_cleanup_never_relies_on_pathname_and_is_separately_approved(self) -> None:
        dossier = apx_isolation.build_stage2_approval_dossier()
        rollback = " ".join(dossier.rollback_rules)
        destructive = " ".join(dossier.destructive_operations)
        self.assertIn("pathname", rollback)
        self.assertIn("never proves", rollback)
        self.assertIn("separate cleanup approval", destructive)
        self.assertIn("never recursively delete", destructive)

    def test_dossier_covers_required_review_sections(self) -> None:
        dossier = apx_isolation.build_stage2_approval_dossier()
        for values in (
            dossier.downloads,
            dossier.host_effects,
            dossier.preconditions,
            dossier.postconditions,
            dossier.failure_states,
            dossier.risks,
            dossier.rollback_rules,
            dossier.destructive_operations,
            dossier.blockers,
        ):
            self.assertTrue(values)
        output = apx_isolation.render_stage2_approval_dossier(dossier)
        self.assertIn("Mode: review only", output)
        self.assertIn("Intended resources:", output)
        self.assertIn("Separately approved destructive operations:", output)
        self.assertIn(f"Dossier digest: {dossier.digest}", output)

    def test_dossier_digest_covers_resources_gates_and_blockers(self) -> None:
        dossier = apx_isolation.build_stage2_approval_dossier()
        self.assertEqual(
            dossier.digest,
            apx_isolation.compute_stage2_dossier_digest(dossier),
        )
        changed_resource = replace(dossier.resources[0], quota="changed")
        variants = (
            replace(dossier, resources=(changed_resource,) + dossier.resources[1:]),
            replace(dossier, preconditions=dossier.preconditions + ("new gate",)),
            replace(dossier, blockers=dossier.blockers + ("new blocker",)),
        )
        for variant in variants:
            self.assertNotEqual(
                dossier.digest,
                apx_isolation.compute_stage2_dossier_digest(variant),
            )


class BaseSnapshotTests(unittest.TestCase):
    @staticmethod
    def package(name: str, **changes) -> apx_isolation.SnapshotPackage:
        values = {
            "name": name,
            "version": "1-1",
            "architecture": "x86_64",
            "filename": f"{name}-1-1-x86_64.pkg.tar.zst",
            "sha256": "a" * 64,
            "signature_verified": True,
            "signer_fingerprint": "A" * 40,
        }
        values.update(changes)
        return apx_isolation.SnapshotPackage(**values)

    def manifest(self, packages=None, **changes):
        selected = tuple(
            packages
            or [
                self.package(name, architecture="any" if name == "base" else "x86_64")
                for name in apx_isolation.BASE_PACKAGES
            ]
        )
        resolved_digest = apx_isolation.compute_resolved_manifest_sha256(selected)
        provenance = {
            "resolved_manifest_sha256": resolved_digest,
            "acquisition_plan_digest": apx_isolation.build_snapshot_acquisition_plan().digest,
            "keyring_artifact": "archlinux-keyring-20250622-1-any.pkg.tar.zst",
            "keyring_sha256": "d" * 64,
            "trust_bootstrap_digest": "e" * 64,
            "verification_tool": "gpgv-fixture 1.0",
        }
        values = {
            "schema_version": 1,
            "snapshot_id": "apx-base-2026.07.11-v1",
            "source_kind": "arch-linux-archive",
            "source_uri": "https://archive.archlinux.org/repos/2026/07/11/$repo/os/$arch",
            "snapshot_date": "2026/07/11",
            "database_sha256": (("core", "b" * 64), ("extra", "c" * 64)),
            "seed_packages": apx_isolation.BASE_PACKAGES,
            "packages": selected,
            **provenance,
            "independent_validation_completed": True,
            "independent_validation_digest": apx_isolation.compute_independent_validation_digest(
                **provenance
            ),
        }
        values.update(changes)
        return apx_isolation.BaseSnapshotManifest(**values)

    def test_complete_signed_archive_manifest_is_verified(self) -> None:
        manifest = self.manifest()
        assessment = apx_isolation.assess_base_snapshot(manifest)
        self.assertEqual(assessment.classification, "verified")
        self.assertEqual(assessment.issues, ())
        self.assertEqual(len(assessment.digest), 64)

    def test_missing_signature_or_signer_is_incomplete(self) -> None:
        packages = [self.package(name) for name in apx_isolation.BASE_PACKAGES]
        packages[0] = self.package(
            packages[0].name, signature_verified=False, signer_fingerprint=None
        )
        manifest = self.manifest(packages)
        assessment = apx_isolation.assess_base_snapshot(manifest)
        self.assertEqual(assessment.classification, "verification-incomplete")
        self.assertIn("signature is not verified", " ".join(assessment.issues))

    def test_independent_validation_and_provenance_are_required(self) -> None:
        incomplete = self.manifest(independent_validation_completed=False)
        mismatched = self.manifest(independent_validation_digest="f" * 64)
        unsafe_keyring = self.manifest(keyring_artifact="../archlinux-keyring.pkg.tar.zst")
        self.assertEqual(
            apx_isolation.assess_base_snapshot(incomplete).classification,
            "verification-incomplete",
        )
        self.assertEqual(
            apx_isolation.assess_base_snapshot(mismatched).classification,
            "rejected",
        )
        self.assertEqual(
            apx_isolation.assess_base_snapshot(unsafe_keyring).classification,
            "rejected",
        )

    def test_moving_mirror_wrong_date_or_digest_is_rejected(self) -> None:
        manifest = self.manifest(
            source_kind="moving-mirror",
            source_uri="https://geo.mirror.pkgbuild.com/$repo/os/$arch",
            resolved_manifest_sha256="d" * 64,
        )
        assessment = apx_isolation.assess_base_snapshot(manifest)
        self.assertEqual(assessment.classification, "rejected")
        self.assertIn("immutable Arch Linux Archive", " ".join(assessment.issues))
        self.assertIn("does not match package evidence", " ".join(assessment.issues))

    def test_impossible_or_mismatched_date_and_database_order_are_rejected(self) -> None:
        impossible = self.manifest(
            snapshot_date="2026/99/11",
            source_uri="https://archive.archlinux.org/repos/2026/99/11/$repo/os/$arch",
            snapshot_id="apx-base-2026.99.11-v1",
        )
        mismatched = self.manifest(snapshot_id="apx-base-2026.07.12-v1")
        unordered = self.manifest(
            database_sha256=(("extra", "c" * 64), ("core", "b" * 64))
        )
        self.assertIn(
            "real calendar date",
            " ".join(apx_isolation.assess_base_snapshot(impossible).issues),
        )
        self.assertIn(
            "identity date does not match",
            " ".join(apx_isolation.assess_base_snapshot(mismatched).issues),
        )
        self.assertIn(
            "not canonically ordered",
            " ".join(apx_isolation.assess_base_snapshot(unordered).issues),
        )

    def test_signature_result_must_be_a_boolean(self) -> None:
        packages = [self.package(name) for name in apx_isolation.BASE_PACKAGES]
        packages[0] = self.package(packages[0].name, signature_verified=1)
        assessment = apx_isolation.assess_base_snapshot(self.manifest(packages))
        self.assertEqual(assessment.classification, "rejected")
        self.assertIn("not boolean", " ".join(assessment.issues))

    def test_duplicate_missing_unsorted_and_unsafe_packages_are_rejected(self) -> None:
        packages = (
            self.package("sudo"),
            self.package("base", filename="../base.pkg.tar.zst"),
            self.package("base"),
        )
        manifest = self.manifest(
            packages,
            resolved_manifest_sha256=apx_isolation.compute_resolved_manifest_sha256(packages),
        )
        assessment = apx_isolation.assess_base_snapshot(manifest)
        self.assertEqual(assessment.classification, "rejected")
        joined = " ".join(assessment.issues)
        self.assertIn("duplicated", joined)
        self.assertIn("omits fixed seed packages", joined)
        self.assertIn("not canonically ordered", joined)
        self.assertIn("unsafe filename", joined)

    def test_render_is_deterministic_and_explicitly_non_mutating(self) -> None:
        manifest = self.manifest()
        assessment = apx_isolation.assess_base_snapshot(manifest)
        output = apx_isolation.render_snapshot_assessment(manifest, assessment)
        self.assertEqual(
            output,
            apx_isolation.render_snapshot_assessment(manifest, assessment),
        )
        self.assertIn("repository evidence only; no downloads or host changes", output)
        self.assertIn("Stage 2 remains blocked", output)

    def test_canonical_serialization_round_trips(self) -> None:
        manifest = self.manifest()
        encoded = apx_isolation.serialize_base_snapshot_manifest(manifest)
        self.assertEqual(apx_isolation.parse_base_snapshot_manifest(encoded), manifest)
        self.assertTrue(encoded.endswith("\n"))
        self.assertNotIn('": ', encoded)
        self.assertNotIn('", ', encoded)

    def test_parser_rejects_duplicate_unknown_and_wrong_typed_fields(self) -> None:
        encoded = apx_isolation.serialize_base_snapshot_manifest(self.manifest())
        duplicate = encoded.replace(
            '"schema_version":1', '"schema_version":1,"schema_version":1'
        )
        unknown_payload = json.loads(encoded)
        unknown_payload["command"] = "pacman"
        wrong_type_payload = json.loads(encoded)
        wrong_type_payload["schema_version"] = True
        for candidate in (
            duplicate,
            json.dumps(unknown_payload),
            json.dumps(wrong_type_payload),
        ):
            with self.assertRaises(ValueError):
                apx_isolation.parse_base_snapshot_manifest(candidate)

    def test_parser_rejects_package_extensions_and_non_boolean_signature(self) -> None:
        payload = json.loads(
            apx_isolation.serialize_base_snapshot_manifest(self.manifest())
        )
        payload["packages"][0]["command"] = "ignored"
        with self.assertRaises(ValueError):
            apx_isolation.parse_base_snapshot_manifest(json.dumps(payload))
        del payload["packages"][0]["command"]
        payload["packages"][0]["signature_verified"] = 1
        with self.assertRaises(ValueError):
            apx_isolation.parse_base_snapshot_manifest(json.dumps(payload))

    def test_parser_enforces_text_and_package_count_bounds(self) -> None:
        with self.assertRaises(ValueError):
            apx_isolation.parse_base_snapshot_manifest(b"{}")
        with self.assertRaises(ValueError):
            apx_isolation.parse_base_snapshot_manifest("\ud800")
        payload = json.loads(
            apx_isolation.serialize_base_snapshot_manifest(self.manifest())
        )
        payload["packages"] = [
            payload["packages"][0]
            for _ in range(apx_isolation.SNAPSHOT_PACKAGE_MAX_COUNT + 1)
        ]
        with self.assertRaises(ValueError):
            apx_isolation.parse_base_snapshot_manifest(json.dumps(payload))
