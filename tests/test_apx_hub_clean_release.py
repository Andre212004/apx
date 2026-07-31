from dataclasses import replace
import unittest

from src.apx_hub_clean_release import (
    HubCleanReleaseError,
    HubCleanReleaseEvidence,
    assess_hub_clean_release,
)


class HubCleanReleaseTests(unittest.TestCase):
    def evidence(self) -> HubCleanReleaseEvidence:
        return HubCleanReleaseEvidence(
            package_names=("base", "ca-certificates", "pacman", "sudo", "systemd"),
            build_a_tree_digest="a" * 64,
            build_b_tree_digest="a" * 64,
            apx_client_present=True,
            apx_user_locked_before_enrollment=True,
            sudo_requires_password=True,
            empty_graphical_config=True,
            network_namespace_declared=True,
            host_and_sibling_denial_declared=True,
            package_signatures_verified=True,
        )

    def test_exact_minimal_reproducible_release_is_ready(self) -> None:
        result = assess_hub_clean_release(self.evidence())
        self.assertEqual(result.classification, "ready-for-publication")
        self.assertEqual(result.blockers, ())

    def test_graphical_package_or_build_difference_blocks(self) -> None:
        with_graphics = replace(
            self.evidence(),
            package_names=("base", "ca-certificates", "hyprland", "pacman", "sudo", "systemd"),
        )
        self.assertIn("graphical packages", " ".join(assess_hub_clean_release(with_graphics).blockers))
        different = replace(self.evidence(), build_b_tree_digest="b" * 64)
        self.assertIn("independent builds differ", assess_hub_clean_release(different).blockers)

    def test_missing_base_and_wrong_types_fail_closed(self) -> None:
        missing = replace(self.evidence(), package_names=("base",))
        self.assertEqual(assess_hub_clean_release(missing).classification, "blocked")
        with self.assertRaises(HubCleanReleaseError):
            assess_hub_clean_release(replace(self.evidence(), sudo_requires_password=1))


if __name__ == "__main__":
    unittest.main()
