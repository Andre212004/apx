from dataclasses import replace
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import apx_graphical_template as subject


class GraphicalTemplateTests(unittest.TestCase):
    def test_catalogue_contains_only_base_and_hub(self) -> None:
        catalogue = subject.template_catalogue()
        self.assertEqual([item.template_id for item in catalogue], ["hub-hyprland-v1", "hyprland-base-v1"])
        self.assertTrue(all(item.waybar_apx_control for item in catalogue))
        self.assertTrue(all(item.config_inheritance == "copy-on-create-independent" for item in catalogue))
        self.assertTrue(all(item.storage_policy == subject.STORAGE_POLICY for item in catalogue))

    def test_default_capabilities_are_essential_and_private(self) -> None:
        template = subject.TEMPLATES["hyprland-base-v1"]
        self.assertEqual(template.default_optional_capabilities, ())
        for capability in ("camera-mediated", "microphone-mediated", "controller-mediated", "removable-storage-mediated"):
            self.assertNotIn(capability, template.essential_capabilities)
        self.assertIn("host-mediated-outbound-network", template.essential_capabilities)

    def test_creation_plan_is_independent_and_never_activates(self) -> None:
        plan = subject.build_creation_plan("university", "hyprland-base-v1")
        self.assertNotEqual(plan.root_storage, plan.home_storage)
        self.assertEqual(plan.config_destination, "/var/lib/apx/environments/university/home/apx/.config")
        self.assertIn("activate-graphical-session", plan.forbidden_effects)
        self.assertIn("modify-host-package-state", plan.forbidden_effects)
        self.assertEqual(len(plan.plan_digest), 64)

    def test_hub_template_is_reserved_and_fixed(self) -> None:
        self.assertEqual(subject.build_creation_plan("hub", "hub-hyprland-v1").role, "hub-graphical")
        for name, template in (("hub", "hyprland-base-v1"), ("work", "hub-hyprland-v1")):
            with self.assertRaises(subject.GraphicalTemplateError):
                subject.build_creation_plan(name, template)

    def test_caller_cannot_supply_packages_paths_or_capabilities(self) -> None:
        with self.assertRaises(TypeError):
            subject.build_creation_plan("work", "hyprland-base-v1", packages=("steam",))
        changed = replace(subject.TEMPLATES["hyprland-base-v1"], storage_policy="per-environment-cap")
        with self.assertRaises(subject.GraphicalTemplateError):
            subject.canonical_template_json(changed)

    def test_invalid_names_and_templates_fail_closed(self) -> None:
        for name, template in (("../host", "hyprland-base-v1"), ("work", "unknown")):
            with self.assertRaises(subject.GraphicalTemplateError):
                subject.build_creation_plan(name, template)


if __name__ == "__main__":
    unittest.main()
