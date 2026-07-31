from dataclasses import replace
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import apx_hyprland_base_release as subject


def evidence():
    return subject.HyprlandBaseEvidence(
        subject.PROFILE, subject.RELEASE, subject.CONFIG_SEED,
        tuple(sorted(subject.PACKAGE_SEEDS)), "1" * 64, True, True,
        "2" * 64, "2" * 64, subject.CONFIG_ASSETS, subject.HUB_ASSETS,
        True, True, True, True,
    )


class HyprlandBaseReleaseTests(unittest.TestCase):
    def test_complete_reproducible_signed_release_is_verified(self) -> None:
        result = subject.assess_release(evidence())
        self.assertEqual(result.classification, "verified")
        self.assertEqual(result.issues, ())
        self.assertEqual(len(result.evidence_digest), 64)

    def test_seed_covers_minimal_desktop_and_hub_runtime(self) -> None:
        for package in (
            "hyprland", "waybar", "foot", "fuzzel", "pipewire", "wireplumber",
            "xdg-desktop-portal-hyprland", "mesa", "vulkan-radeon", "gtk4",
            "libadwaita", "python-gobject", "sudo",
        ):
            self.assertIn(package, subject.PACKAGE_SEEDS)

    def test_demo_hub_application_is_not_an_admitted_release_asset(self) -> None:
        self.assertEqual(subject.HUB_ASSETS, ())
        self.assertEqual(subject.HUB_APPLICATION_STATUS, "future-production-artifact-required")
        prototype = ROOT / "prototypes/hub-gtk/apx_hub_app.py"
        self.assertTrue(prototype.is_file())
        self.assertNotIn("prototypes", repr(subject.CONFIG_ASSETS) + repr(subject.HUB_ASSETS))

    def test_repository_config_seed_matches_the_closed_asset_digests(self) -> None:
        import hashlib

        seed_root = ROOT / "config/hyprland-base"
        for relative, expected_digest in subject.CONFIG_ASSETS:
            mapped = seed_root / relative
            if relative == "hyprland/hyprland.conf":
                mapped = seed_root / "hyprland.conf"
            self.assertEqual(hashlib.sha256(mapped.read_bytes()).hexdigest(), expected_digest)

    def test_missing_signature_reproducibility_or_seed_blocks(self) -> None:
        cases = (
            replace(evidence(), all_package_signatures_verified=False),
            replace(evidence(), second_root_digest="3" * 64),
            replace(evidence(), package_names=tuple(name for name in evidence().package_names if name != "waybar")),
            replace(evidence(), config_assets=()),
        )
        for case in cases:
            with self.subTest(case=case):
                self.assertEqual(subject.assess_release(case).classification, "blocked")

    def test_duplicate_unsorted_and_malformed_evidence_blocks(self) -> None:
        for case in (
            replace(evidence(), package_names=("waybar", "waybar")),
            replace(evidence(), package_manifest_digest="bad"),
            replace(evidence(), private_keys_absent=False),
        ):
            self.assertEqual(subject.assess_release(case).classification, "blocked")


if __name__ == "__main__":
    unittest.main()
