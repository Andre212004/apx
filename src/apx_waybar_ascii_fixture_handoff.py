"""Pure exact-generation button catalogue for the Waybar ASCII physical fixture."""

from __future__ import annotations

from dataclasses import dataclass

from apx_executor_contract import OperationPlan, RequesterContext, build_operation_plan


PROFILE = "apx-waybar-ascii-fixture-handoff-v1"
HUB_GENERATION = "6f63f9a9-daea-40d1-969f-e25ff0752f4d"
TARGET_NAME = "codex-test-waybar-v1"
TARGET_GENERATION = "1df14250-c628-49d4-961e-44ad22fd67a4"


class WaybarAsciiFixtureHandoffError(ValueError):
    pass


@dataclass(frozen=True)
class FixtureButton:
    action_id: str
    label: str
    plan: OperationPlan


def build_fixture_buttons(requester: RequesterContext) -> tuple[FixtureButton, ...]:
    """Return only the action admitted for the exact active fixture identity."""
    if type(requester) is not RequesterContext or not (
        requester.authenticated and requester.active and requester.authoritative
    ):
        raise WaybarAsciiFixtureHandoffError("active requester evidence is incomplete")
    identity = (requester.logical_name, requester.role, requester.generation)
    if identity == ("hub", "hub", HUB_GENERATION):
        return (
            FixtureButton(
                "activate",
                "Abrir WAYBAR TEST",
                build_operation_plan("activate", TARGET_NAME, TARGET_GENERATION),
            ),
        )
    if identity == (TARGET_NAME, "graphical-base", TARGET_GENERATION):
        return (
            FixtureButton(
                "return-to-hub",
                "Voltar ao HUB",
                build_operation_plan("stop", TARGET_NAME, TARGET_GENERATION),
            ),
        )
    raise WaybarAsciiFixtureHandoffError("requester is outside the exact fixture handoff")
