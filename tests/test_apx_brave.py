from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_brave


def brave(**changes):
    values = dict(
        mechanism="Arch package", executable="/usr/bin/brave",
        package="/usr/bin/brave is owned by brave-bin 1", arch_packages=("brave-bin",),
        desktop_entries=("/usr/share/applications/brave-browser.desktop",),
        flatpak="not-installed",
        user_data=(("apx-hub", "absent"), ("apx-development", "present"), ("apx-trial", "absent")),
    )
    values.update(changes)
    return SimpleNamespace(**values)


class BraveIsolationTests(unittest.TestCase):
    def test_arch_package_is_classified_as_globally_visible(self) -> None:
        report = apx_brave.build_brave_isolation_report(brave(), lambda name: None)
        self.assertIn("system-wide executable", report.global_visibility)
        self.assertIn("system desktop entry", report.global_visibility)

    def test_flatpak_availability_and_recommendation(self) -> None:
        available = apx_brave.build_brave_isolation_report(
            brave(flatpak="absent"), lambda name: "/usr/bin/flatpak" if name == "flatpak" else None
        )
        option = next(item for item in available.options if item.name == "Per-user Flatpak")
        self.assertEqual(option.availability, "available")
        self.assertIn("per-user Flatpak", available.recommendation)

    def test_missing_flatpak_requires_separate_approval(self) -> None:
        report = apx_brave.build_brave_isolation_report(brave(), lambda name: None)
        option = next(item for item in report.options if item.name == "Per-user Flatpak")
        self.assertEqual(option.availability, "requires Flatpak installation")
        self.assertIn("separate explicit approval", report.recommendation)

    def test_container_option_reflects_local_tools_without_preference(self) -> None:
        report = apx_brave.build_brave_isolation_report(
            brave(), lambda name: "/usr/bin/podman" if name == "podman" else None
        )
        option = next(item for item in report.options if item.name == "Distrobox or container")
        self.assertEqual(option.availability, "available via podman")
        self.assertIn("complexity", option.assessment)

    def test_unavailable_development_data_is_incomplete(self) -> None:
        data = (("apx-hub", "unavailable"), ("apx-development", "unavailable"), ("apx-trial", "absent"))
        report = apx_brave.build_brave_isolation_report(brave(user_data=data), lambda name: None)
        self.assertTrue(report.overall.startswith("incomplete"))

    def test_output_is_deterministic_and_nonexecuting(self) -> None:
        first = apx_brave.build_brave_isolation_report(brave(), lambda name: None)
        second = apx_brave.build_brave_isolation_report(brave(), lambda name: None)
        self.assertEqual(apx_brave.render_brave_isolation(first), apx_brave.render_brave_isolation(second))
        rendered = apx_brave.render_brave_isolation(first)
        self.assertIn("no changes executed", rendered)
        self.assertEqual(rendered.splitlines()[-1], "Overall result: " + first.overall)


if __name__ == "__main__":
    unittest.main()
