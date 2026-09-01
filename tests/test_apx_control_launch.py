from dataclasses import replace
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import apx_control_launch as launch


def evidence(**changes):
    value = launch.ControlLaunchEvidence(
        session_id="session-7",
        session_authenticated=True,
        session_active=True,
        session_graphical=True,
        observed_logical_name="hub",
        observed_role="hub-graphical",
        observed_generation=4,
        registration_logical_name="hub",
        registration_role="hub-graphical",
        registration_generation=4,
        registration_verified=True,
        observation_authoritative=True,
    )
    return replace(value, **changes)


class ControlLaunchTests(unittest.TestCase):
    def test_verified_hub_gets_fixed_switcher_and_management_commands(self) -> None:
        for mode in launch.MODES:
            decision = launch.decide_control_launch(mode, evidence())
            self.assertEqual(decision.classification, "launch-approved")
            self.assertEqual(
                decision.argv,
                ("/usr/bin/apx-hub-ui", f"--{mode}", "--role", "hub-graphical"),
            )

    def test_verified_workload_gets_switcher_but_never_management(self) -> None:
        workload = evidence(
            observed_logical_name="university",
            registration_logical_name="university",
            observed_role="graphical-base",
            registration_role="graphical-base",
        )
        self.assertEqual(
            launch.decide_control_launch("switcher", workload).classification,
            "launch-approved",
        )
        management = launch.decide_control_launch("management", workload)
        self.assertEqual(management.classification, "rejected")
        self.assertEqual(management.argv, ())

    def test_every_trust_or_binding_failure_blocks_without_command(self) -> None:
        variants = (
            evidence(session_authenticated=False),
            evidence(session_active=False),
            evidence(session_graphical=False),
            evidence(registration_verified=False),
            evidence(observation_authoritative=False),
            evidence(registration_logical_name="games"),
            evidence(registration_role="standard"),
            evidence(registration_generation=5),
            evidence(observed_role="caller-claims-hub", registration_role="caller-claims-hub"),
            evidence(
                observed_logical_name="university",
                registration_logical_name="university",
                observed_role="hub-graphical",
                registration_role="hub-graphical",
            ),
        )
        for variant in variants:
            decision = launch.decide_control_launch("switcher", variant)
            self.assertEqual(decision.classification, "rejected")
            self.assertEqual(decision.argv, ())

    def test_unknown_mode_cannot_become_an_argument(self) -> None:
        decision = launch.decide_control_launch("--execute-anything", evidence())
        self.assertEqual(decision.classification, "rejected")
        self.assertEqual(decision.argv, ())
