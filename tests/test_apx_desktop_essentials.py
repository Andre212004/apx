from dataclasses import replace
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import apx_desktop_essentials as subject  # noqa: E402


def evidence(**changes):
    value = subject.DesktopEssentialsEvidence(
        subject.PROFILE,
        subject.CONFIGURATION_PROFILE,
        tuple(sorted(subject.LOCAL_PACKAGES)),
        True,
        True,
        True,
        True,
        True,
        True,
    )
    return replace(value, **changes)


class DesktopEssentialsTests(unittest.TestCase):
    def test_current_profile_is_ready_with_exclusive_bluetooth_power_mediator(self) -> None:
        result = subject.assess_desktop_essentials(evidence())
        self.assertEqual(result.classification, "ready")
        self.assertEqual(result.locked_controls, ())
        self.assertIn("audio", result.ready_controls)

    def test_profile_matches_versioned_json(self) -> None:
        value = json.loads((ROOT / "config/desktop-essential-v1/profile.json").read_text())
        self.assertEqual(value["profile"], subject.PROFILE)
        self.assertEqual(value["configuration_profile"], subject.CONFIGURATION_PROFILE)
        self.assertEqual(tuple(value["local_packages"]), subject.LOCAL_PACKAGES)
        self.assertEqual(
            tuple(value["optional_local_packages"]), subject.OPTIONAL_LOCAL_PACKAGES
        )
        self.assertEqual(
            tuple(value["services_not_enabled"]),
            subject.SERVICES_NOT_ENABLED,
        )

    def test_hardware_owners_are_not_disguised_as_local_packages(self) -> None:
        value = json.loads((ROOT / "config/desktop-essential-v1/profile.json").read_text())
        self.assertEqual(value["controls"]["audio"]["owner"], "environment")
        for control in subject.HOST_MEDIATED_CONTROLS:
            self.assertEqual(value["controls"][control]["owner"], "host")
        self.assertNotIn("networkmanager", subject.LOCAL_PACKAGES)
        self.assertNotIn("bluez", subject.LOCAL_PACKAGES)

    def test_missing_package_or_isolation_evidence_blocks(self) -> None:
        cases = (
            evidence(package_names=tuple(name for name in subject.LOCAL_PACKAGES if name != "pipewire-pulse")),
            evidence(environment_local_audio=False),
            evidence(host_hardware_services_disabled=False),
        )
        for case in cases:
            with self.subTest(case=case):
                self.assertEqual(subject.assess_desktop_essentials(case).classification, "blocked")

    def test_bluetooth_is_locked_without_the_exclusive_active_session_mediator(self) -> None:
        result = subject.assess_desktop_essentials(
            evidence(bluetooth_exclusive_mediator=False)
        )
        self.assertEqual(result.classification, "ready-with-locked-capability")
        self.assertEqual(result.locked_controls, ("bluetooth",))


if __name__ == "__main__":
    unittest.main()
