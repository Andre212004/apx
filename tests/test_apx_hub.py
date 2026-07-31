from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_hub


def environment(name: str, *, role: str = "standard", state: str = "inactive", cleanup_summary=None):
    return apx_hub.EnvironmentSummary(
        logical_name=name,
        display_name=name.replace("-", " ").title(),
        role=role,
        state=state,
        security_profile="Normal",
        template_name="Universidade 1.0",
        storage_summary="12 GB utilizados",
        cleanup_summary=cleanup_summary,
    )


def template(*, admitted: bool = True, compatibility: str = "compatible"):
    return apx_hub.TemplateSummary(
        template_id="university-1.0-" + "a" * 32,
        display_name="Universidade",
        description="Estudo, documentos e aulas.",
        security_profile="Normal",
        main_software=("Browser", "Office", "PDF"),
        storage_estimate="Aproximadamente 8 GB",
        admitted=admitted,
        compatibility=compatibility,
    )


def ready_view(*extra, templates=None):
    values = (environment("hub", role="hub", state="active"),) + extra
    return apx_hub.build_hub_view(values, templates or (template(),), system_state="ready")


def action(card, action_id):
    return next(item for item in card.actions if item.action_id == action_id)


class HubViewTests(unittest.TestCase):
    def test_graphical_hub_is_recognized_as_the_single_active_hub(self) -> None:
        graphical = environment("hub", role="hub-graphical", state="active")
        view = apx_hub.build_hub_view((graphical,), (template(),), system_state="ready")
        self.assertEqual(view.system_state, "ready")
        self.assertFalse(view.environment_cards[0].actions[0].enabled)

    def test_graphical_base_role_is_supported_as_a_workload(self) -> None:
        view = ready_view(environment("study", role="graphical-base", state="inactive"))
        study = next(card for card in view.environment_cards if card.logical_name == "study")
        self.assertTrue(next(action for action in study.actions if action.action_id == "open").enabled)

    def test_default_graphical_catalogue_maps_to_safe_hub_summaries(self) -> None:
        summaries = apx_hub.default_graphical_template_summaries()
        self.assertEqual({item.template_id for item in summaries}, {"hyprland-base-v1", "hub-hyprland-v1"})
        self.assertTrue(all(item.admitted and item.compatibility == "compatible" for item in summaries))
        self.assertTrue(all(item.security_profile == "Essencial privado" for item in summaries))

    def test_ready_inactive_environment_has_safe_fixed_actions(self) -> None:
        view = ready_view(environment("university"))
        card = next(item for item in view.environment_cards if item.logical_name == "university")
        self.assertTrue(action(card, "open").enabled)
        self.assertEqual(action(card, "open").request_kind, "activate")
        self.assertTrue(action(card, "capabilities").enabled)
        self.assertEqual(action(card, "capabilities").request_kind, "configure-capabilities")
        self.assertEqual(action(card, "capabilities").approval_class, "explicit-confirmation")
        self.assertTrue(action(card, "snapshot").enabled)
        self.assertTrue(action(card, "archive").enabled)
        self.assertTrue(action(card, "destroy").enabled)
        self.assertEqual(action(card, "destroy").approval_class, "strong-confirmation")
        self.assertIn("preservar as cópias", action(card, "destroy").explanation)
        for item in card.actions:
            self.assertFalse(hasattr(item, "command"))
            self.assertFalse(hasattr(item, "path"))

    def test_active_environment_cannot_be_snapshotted_archived_or_destroyed(self) -> None:
        view = apx_hub.build_hub_view(
            (environment("games", state="active"),),
            (template(),),
            system_state="ready",
        )
        card = view.environment_cards[0]
        for action_id in ("snapshot", "archive", "destroy"):
            self.assertFalse(action(card, action_id).enabled)
        self.assertEqual(view.system_state, "incomplete")
        self.assertTrue(view.warnings)

    def test_incomplete_environment_exposes_only_recovery_and_details(self) -> None:
        view = ready_view(environment("work", state="incomplete"))
        card = next(item for item in view.environment_cards if item.logical_name == "work")
        self.assertEqual({item.action_id for item in card.actions}, {"recover", "details"})
        self.assertTrue(action(card, "recover").enabled)

    def test_unconfirmed_environment_has_no_mutating_action(self) -> None:
        view = ready_view(environment("work", state="unconfirmed"))
        card = next(item for item in view.environment_cards if item.logical_name == "work")
        self.assertEqual({item.action_id for item in card.actions}, {"retry-check", "details"})
        self.assertTrue(all(item.request_kind is None for item in card.actions))

    def test_cleaning_environment_remains_visible_with_read_only_progress(self) -> None:
        view = ready_view(
            environment("games", state="cleaning", cleanup_summary="A limpar — 7/9 recursos")
        )
        card = next(item for item in view.environment_cards if item.logical_name == "games")
        self.assertEqual(card.state_label, "A limpar — 7/9 recursos")
        self.assertEqual({item.action_id for item in card.actions}, {"cleanup-status", "details"})
        self.assertTrue(all(item.enabled and item.request_kind is None for item in card.actions))

    def test_cleanup_progress_is_required_only_for_cleaning_state(self) -> None:
        with self.assertRaises(ValueError):
            ready_view(environment("games", state="cleaning"))
        with self.assertRaises(ValueError):
            ready_view(environment("games", cleanup_summary="unexpected"))

    def test_unavailable_or_busy_system_disables_all_mutating_actions(self) -> None:
        for state in ("busy", "incomplete", "unavailable"):
            view = apx_hub.build_hub_view(
                (environment("hub", role="hub", state="active"), environment("games")),
                (template(),),
                system_state=state,
            )
            for card in view.environment_cards:
                for item in card.actions:
                    if item.action_id not in {"details", "retry-check"}:
                        self.assertFalse(item.enabled)
            self.assertFalse(view.template_cards[0].action.enabled)
            self.assertFalse(next(item for item in view.global_actions if item.action_id == "restore").enabled)

    def test_multiple_active_environments_fail_closed(self) -> None:
        view = apx_hub.build_hub_view(
            (
                environment("hub", role="hub", state="active"),
                environment("games", state="active"),
            ),
            (template(),),
            system_state="ready",
        )
        self.assertEqual(view.system_state, "incomplete")
        self.assertIn("mais do que um Environment ativo", view.warnings[0])
        self.assertFalse(view.template_cards[0].action.enabled)

    def test_only_admitted_compatible_template_can_create(self) -> None:
        self.assertTrue(ready_view().template_cards[0].action.enabled)
        self.assertFalse(ready_view(templates=(template(admitted=False),)).template_cards[0].action.enabled)
        self.assertFalse(ready_view(templates=(template(compatibility="blocked"),)).template_cards[0].action.enabled)

    def test_template_create_action_never_contains_package_or_host_instructions(self) -> None:
        item = ready_view().template_cards[0].action
        self.assertEqual(item.request_kind, "create")
        self.assertFalse(hasattr(item, "packages"))
        self.assertFalse(hasattr(item, "command"))
        self.assertFalse(hasattr(item, "host_path"))

    def test_duplicate_invalid_or_unknown_input_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ready_view(environment("work"), environment("work"))
        with self.assertRaises(ValueError):
            ready_view(environment("../host"))
        with self.assertRaises(ValueError):
            ready_view(environment("work", state="invented"))
        with self.assertRaises(ValueError):
            apx_hub.build_hub_view((), (), system_state="invented")

    def test_text_render_is_plain_stable_and_explains_blocks(self) -> None:
        view = ready_view(environment("work", state="unconfirmed"))
        first = apx_hub.render_hub_text(view)
        second = apx_hub.render_hub_text(view)
        self.assertEqual(first, second)
        self.assertIn("Estado por confirmar", first)
        self.assertIn("Verificar novamente", first)
        self.assertIn("não altera dados", first)


if __name__ == "__main__":
    unittest.main()
