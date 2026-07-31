"""Pure readiness gate for an owner-driven physical Hub button round trip."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json


PROFILE = "apx-manual-hub-workload-round-trip-v1"
TARGET = "test"
MAX_VISIBLE_SECONDS = 30


@dataclass(frozen=True)
class ManualGraphicalTestEvidence:
    profile: str
    target_logical_name: str
    effect_free_integration_passed: bool
    typed_executor_installed_and_verified: bool
    graphical_base_release_admitted: bool
    production_hub_client_admitted: bool
    graphical_hub_installed: bool
    graphical_workload_installed: bool
    trusted_launcher_installed: bool
    exclusive_broker_installed: bool
    mediated_device_adapter_verified: bool
    independent_graphical_watchdog_verified: bool
    tty1_recovery_verified_after_current_boot: bool
    physical_h0_execution_unlocked: bool
    no_failed_units_or_uncertain_operation: bool


@dataclass(frozen=True)
class ManualGraphicalTestAssessment:
    classification: str
    blockers: tuple[str, ...]
    target_logical_name: str
    max_visible_seconds: int
    required_owner_actions: tuple[str, ...]
    forbidden_actions: tuple[str, ...]
    evidence_digest: str


CURRENT_OBSERVED_EVIDENCE = ManualGraphicalTestEvidence(
    PROFILE, TARGET,
    True,   # repository effect-free integration
    True,   # active physical pilot typed executor
    True,   # immutable reproduced hyprland-base-v1 physical release
    False,  # current GTK program is demo-only
    False,  # current Hub is headless
    True,   # stopped apx-test graphical-base workload is installed
    False,  # trusted launcher is a pure contract only
    False,  # broker is a pure contract only
    False,  # physical mediated device adapter is absent
    False,  # only non-graphical recovery-v2 rehearsal passed
    True,   # post-battery tty1/read-only recovery observation
    False,  # H0 remains code-locked
    True,   # post-battery zero failed units and no uncertain observed runtime
)


def assess_manual_test(evidence: ManualGraphicalTestEvidence) -> ManualGraphicalTestAssessment:
    if type(evidence) is not ManualGraphicalTestEvidence:
        raise ValueError("manual graphical evidence has wrong type")
    if (evidence.profile, evidence.target_logical_name) != (PROFILE, TARGET):
        raise ValueError("manual graphical test subject differs")
    gates = {
        "effect-free button integration is incomplete": evidence.effect_free_integration_passed,
        "typed executor is not installed and verified": evidence.typed_executor_installed_and_verified,
        "graphical base release is not admitted": evidence.graphical_base_release_admitted,
        "production Hub client is not admitted": evidence.production_hub_client_admitted,
        "graphical Hub is not installed": evidence.graphical_hub_installed,
        "graphical workload is not installed": evidence.graphical_workload_installed,
        "trusted UI launcher is not installed": evidence.trusted_launcher_installed,
        "exclusive session broker is not installed": evidence.exclusive_broker_installed,
        "mediated physical device adapter is unverified": evidence.mediated_device_adapter_verified,
        "independent graphical watchdog is unverified": evidence.independent_graphical_watchdog_verified,
        "tty1 recovery is unverified for the current boot": evidence.tty1_recovery_verified_after_current_boot,
        "physical H0 execution remains locked": evidence.physical_h0_execution_unlocked,
        "failed units or an uncertain operation remain": evidence.no_failed_units_or_uncertain_operation,
    }
    if any(type(value) is not bool for value in gates.values()):
        raise ValueError("manual graphical gate has wrong type")
    blockers = tuple(message for message, passed in gates.items() if not passed)
    digest = hashlib.sha256(
        json.dumps(asdict(evidence), sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return ManualGraphicalTestAssessment(
        "ready-for-separate-owner-approval" if not blockers else "blocked",
        blockers, TARGET, MAX_VISIBLE_SECONDS,
        (
            "click-Development-in-Hub", "wait-for-verified-workload-screen",
            "click-return-to-Hub", "confirm-Hub-restored",
        ),
        (
            "run-from-ssh-only-recovery", "disable-watchdog", "force-stop",
            "poweroff-as-normal-return", "test-with-two-graphical-owners",
        ),
        digest,
    )
