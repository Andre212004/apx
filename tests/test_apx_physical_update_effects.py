from dataclasses import replace
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_physical_update as update
import apx_physical_update_artifact as artifact
import apx_physical_update_effects as effects
from tests.test_apx_physical_update import candidate as generic_candidate, installed
from tests.test_apx_physical_update_artifact import candidate_for, tar_bytes


def inputs():
    raw = tar_bytes()
    candidate = candidate_for(raw)
    current = replace(installed(), installed_source_revision=candidate.parent_revision)
    preview = update.build_update_preview(candidate, current)
    inspected = artifact.inspect_artifact(raw, candidate)
    return candidate, current, preview, inspected


class PhysicalUpdateEffectsTests(unittest.TestCase):
    def test_ready_runtime_candidate_maps_only_to_fixed_target(self) -> None:
        candidate, current, preview, inspected = inputs()
        plan = effects.build_import_plan(
            candidate, current, preview, inspected,
            import_approval_digest="a" * 64,
        )
        effects.validate_import_plan(plan)
        self.assertEqual(plan.staging_root, "/var/lib/apx/updates/staging")
        self.assertEqual(plan.artifact_name, "candidate.tar")
        self.assertEqual(plan.targets[0].destination, "/usr/lib/apx/apx-lab-runtime.py")
        self.assertEqual(plan.targets[0].required_alias, "/usr/bin/apx")
        self.assertEqual(plan.targets[0].required_alias_target, plan.targets[0].destination)
        self.assertEqual(plan.targets[0].before_sha256, current.installed_runtime_sha256)
        self.assertEqual(plan.targets[0].rollback_sha256, current.installed_runtime_sha256)

    def test_blocked_stale_or_mismatched_preview_refuses(self) -> None:
        candidate, current, preview, inspected = inputs()
        variants = (
            replace(preview, classification="blocked", blockers=("recovery-console-not-verified",)),
            replace(preview, update_id="update-" + "f" * 32),
            replace(preview, candidate_digest="0" * 64),
            replace(preview, installed_evidence_digest="0" * 64),
            replace(preview, plan_digest="0" * 64),
        )
        for changed in variants:
            with self.subTest(changed=changed):
                with self.assertRaises(effects.PhysicalUpdateEffectError):
                    effects.build_import_plan(
                        candidate, current, changed, inspected,
                        import_approval_digest="a" * 64,
                    )

    def test_artifact_identity_size_manifest_count_and_components_are_bound(self) -> None:
        candidate, current, preview, inspected = inputs()
        variants = (
            replace(inspected, artifact_sha256="0" * 64),
            replace(inspected, artifact_bytes=inspected.artifact_bytes + 1),
            replace(inspected, manifest_digest="0" * 64),
            replace(inspected, member_count=3),
            replace(inspected, component_digests=(("hub-client", "0" * 64),)),
        )
        for changed in variants:
            with self.subTest(changed=changed):
                with self.assertRaises(effects.PhysicalUpdateEffectError):
                    effects.build_import_plan(
                        candidate, current, preview, changed,
                        import_approval_digest="a" * 64,
                    )

    def test_unmapped_executor_and_hub_client_fail_closed(self) -> None:
        candidate = generic_candidate()
        current = installed()
        preview = update.build_update_preview(candidate, current)
        supplied = artifact.PhysicalUpdateArtifactEvidence(
            candidate.artifact_sha256,
            candidate.artifact_bytes,
            candidate.member_manifest_digest,
            candidate.member_count,
            tuple((name, "f" * 64) for name in candidate.components),
        )
        with self.assertRaisesRegex(effects.PhysicalUpdateEffectError, "no reviewed"):
            effects.build_import_plan(
                candidate, current, preview, supplied,
                import_approval_digest="a" * 64,
            )

    def test_plan_rejects_path_alias_mode_rollback_and_digest_tampering(self) -> None:
        candidate, current, preview, inspected = inputs()
        plan = effects.build_import_plan(
            candidate, current, preview, inspected,
            import_approval_digest="a" * 64,
        )
        target = plan.targets[0]
        variants = (
            replace(plan, staging_root="/tmp"),
            replace(plan, operation_directory="/var/lib/apx/updates/staging/other"),
            replace(plan, artifact_name="../candidate.tar"),
            replace(plan, targets=(replace(target, destination="/usr/bin/apx"),)),
            replace(plan, targets=(replace(target, mode=0o4755),)),
            replace(plan, targets=(replace(target, required_alias_target="/tmp/runtime"),)),
            replace(plan, targets=(replace(target, rollback_sha256="f" * 64),)),
            replace(plan, effects_absent=()),
            replace(plan, plan_digest="0" * 64),
        )
        for changed in variants:
            with self.subTest(changed=changed):
                with self.assertRaises(effects.PhysicalUpdateEffectError):
                    effects.validate_import_plan(changed)

    def test_invalid_approval_and_wrong_types_refuse(self) -> None:
        candidate, current, preview, inspected = inputs()
        for approval in ("short", "A" * 64, None):
            with self.subTest(approval=approval):
                with self.assertRaises(effects.PhysicalUpdateEffectError):
                    effects.build_import_plan(
                        candidate, current, preview, inspected,
                        import_approval_digest=approval,
                    )


if __name__ == "__main__":
    unittest.main()
