from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_policy


class FixedPolicyTests(unittest.TestCase):
    def test_only_two_fixed_profiles_are_available(self) -> None:
        self.assertEqual(
            tuple(apx_policy.FIXED_POLICIES),
            ("normal-desktop", "high-security-headless"),
        )
        with self.assertRaisesRegex(ValueError, "unsupported APX isolation profile"):
            apx_policy.build_fixed_policy("caller-selected")

    def test_fixed_profiles_are_accepted_and_deterministic(self) -> None:
        for name in apx_policy.FIXED_POLICIES:
            policy = apx_policy.build_fixed_policy(name)
            first = apx_policy.assess_environment_policy(policy)
            second = apx_policy.assess_environment_policy(policy)
            self.assertEqual(first, second)
            self.assertEqual(first.classification, "accepted-contract")
            self.assertEqual(first.issues, ())
            self.assertEqual(len(first.digest), 64)

    def test_normal_profile_has_mediated_usability_not_direct_devices(self) -> None:
        policy = apx_policy.build_fixed_policy("normal-desktop")
        self.assertEqual(policy.direct_devices, ())
        self.assertIn("display-mediated", policy.integration_surfaces)
        self.assertIn("audio-mediated", policy.integration_surfaces)
        self.assertEqual(
            policy.local_administration,
            "owner-confirmed-environment-local-only",
        )
        self.assertEqual(policy.network_policy, "private-namespace-host-mediated-outbound")

    def test_high_security_profile_denies_optional_access(self) -> None:
        policy = apx_policy.build_fixed_policy("high-security-headless")
        self.assertEqual(policy.network_policy, "denied")
        self.assertEqual(policy.integration_surfaces, ())
        self.assertEqual(policy.direct_devices, ())
        self.assertEqual(policy.local_administration, "disabled")
        self.assertEqual(policy.privilege_escalation_policy, "denied")

    def test_cross_environment_and_host_surfaces_are_explicitly_denied(self) -> None:
        for policy in apx_policy.FIXED_POLICIES.values():
            denied = set(policy.forbidden_host_surfaces)
            self.assertIn("host-root", denied)
            self.assertIn("host-package-database", denied)
            self.assertIn("hub-home", denied)
            self.assertIn("sibling-environment-home", denied)
            self.assertIn("apx-control-plane", denied)
            self.assertFalse(policy.writable_host_binds)

    def test_privileged_host_root_linger_and_direct_devices_are_rejected(self) -> None:
        policy = apx_policy.build_fixed_policy("normal-desktop")
        variants = (
            replace(policy, privileged_mode=True),
            replace(policy, host_uid_zero_mapping=True),
            replace(policy, linger=True),
            replace(policy, direct_devices=("/dev",)),
            replace(policy, writable_host_binds=(("host", "environment"),)),
        )
        for variant in variants:
            assessment = apx_policy.assess_environment_policy(variant)
            self.assertEqual(assessment.classification, "rejected")
            self.assertTrue(assessment.issues)

    def test_missing_namespace_or_teardown_check_is_rejected(self) -> None:
        policy = apx_policy.build_fixed_policy("normal-desktop")
        variants = (
            replace(policy, namespaces=policy.namespaces[:-1]),
            replace(policy, teardown_requirements=policy.teardown_requirements[:-1]),
        )
        for variant in variants:
            self.assertEqual(
                apx_policy.assess_environment_policy(variant).classification,
                "rejected",
            )

    def test_policy_cannot_claim_vm_equivalence(self) -> None:
        policy = replace(
            apx_policy.build_fixed_policy("normal-desktop"),
            security_claim="vm-equivalent",
        )
        assessment = apx_policy.assess_environment_policy(policy)
        self.assertEqual(assessment.classification, "rejected")
        self.assertIn(
            "shared-kernel policy cannot claim VM equivalence",
            assessment.issues,
        )

    def test_any_change_to_fixed_policy_changes_digest_and_is_rejected(self) -> None:
        policy = apx_policy.build_fixed_policy("normal-desktop")
        changed = replace(policy, network_policy="host-network")
        original = apx_policy.assess_environment_policy(policy)
        modified = apx_policy.assess_environment_policy(changed)
        self.assertNotEqual(original.digest, modified.digest)
        self.assertEqual(modified.classification, "rejected")

    def test_summary_is_plain_deterministic_and_nonexecuting(self) -> None:
        policy = apx_policy.build_fixed_policy("high-security-headless")
        first = apx_policy.render_policy_summary(policy)
        second = apx_policy.render_policy_summary(policy)
        self.assertEqual(first, second)
        self.assertIn("no network", first)
        self.assertIn("local administration is disabled", first)
        self.assertIn("not VM-equivalent", first)
        self.assertNotIn("sudo", first)
        self.assertNotIn("/dev", first)


if __name__ == "__main__":
    unittest.main()
