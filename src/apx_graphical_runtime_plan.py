"""Pure physical plan for the first recovery-bounded Hub/test round trip."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json


PROFILE = "apx-hub-test-round-trip-v1"
HUB_GENERATION = "2c3dbacc-106f-4053-8603-f649552f5513"
TEST_GENERATION = "69b56acc-fd4d-4499-8009-e1d0108466f4"
RELEASE_MANIFEST_DIGEST = "1b4f1bfc0fc697f9097bbd3e3588b4314e2cb6ff70ec5536520dc936735490ba"
DEADLINE_SECONDS = 15
DEVICES = (
    ("amd-kms", "/dev/dri/card2", 226, 2, "rw"),
    ("amd-render", "/dev/dri/renderD129", 226, 129, "rw"),
    ("keyboard", "/dev/input/event3", 13, 67, "rw"),
    ("touchpad", "/dev/input/event10", 13, 74, "rw"),
    ("transition-vt", "/dev/tty2", 4, 2, "rw"),
)


class GraphicalRuntimePlanError(ValueError):
    pass


@dataclass(frozen=True)
class GraphicalRuntimeObservation:
    test_generation: str
    release_manifest_digest: str
    connector: str
    connector_connected: bool
    tty1_active: bool
    tty2_inactive: bool
    no_graphical_owner: bool
    no_display_manager: bool
    no_failed_units: bool
    no_uncertain_operation: bool
    hub_candidate_present: bool
    test_stopped: bool
    devices: tuple[tuple[str, str, int, int, str], ...]


@dataclass(frozen=True)
class GraphicalRuntimePlan:
    profile: str
    test_generation: str
    release_manifest_digest: str
    deadline_seconds: int
    recovery_vt: str
    transition_vt: str
    devices: tuple[tuple[str, str, int, int, str], ...]
    session_subjects: tuple[tuple[str, str, str, str], ...]
    ordered_effects: tuple[str, ...]
    recovery_effects: tuple[str, ...]
    forbidden_effects: tuple[str, ...]
    observation_digest: str
    plan_digest: str


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def build_graphical_runtime_plan(observation: GraphicalRuntimeObservation) -> GraphicalRuntimePlan:
    if type(observation) is not GraphicalRuntimeObservation:
        raise GraphicalRuntimePlanError("graphical runtime observation has wrong type")
    if observation.test_generation != TEST_GENERATION or observation.release_manifest_digest != RELEASE_MANIFEST_DIGEST:
        raise GraphicalRuntimePlanError("graphical Environment or release identity changed")
    if observation.connector != "card2-eDP-2" or observation.devices != DEVICES:
        raise GraphicalRuntimePlanError("physical display or device identity changed")
    gates = (
        observation.connector_connected, observation.tty1_active,
        observation.tty2_inactive, observation.no_graphical_owner,
        observation.no_display_manager, observation.no_failed_units,
        observation.no_uncertain_operation, observation.hub_candidate_present,
        observation.test_stopped,
    )
    if any(type(value) is not bool for value in gates) or not all(gates):
        raise GraphicalRuntimePlanError("clean Host, recovery, or candidate gate failed")
    subjects = (
        ("hub", HUB_GENERATION, "/var/lib/apx/environments/hub/root",
         "/var/lib/apx/environments/hub/home"),
        ("test", TEST_GENERATION, "/var/lib/apx/environments/test/root",
         "/var/lib/apx/environments/test/home"),
    )
    ordered = (
        "revalidate-plan-and-zero-residue",
        "write-read-only-host-issued-session-descriptor",
        "arm-independent-15-second-host-deadline",
        "verify-deadline-active-before-granting-devices",
        "start-one-generation-bound-private-nspawn-session",
        "verify-wayland-monitor-client-and-single-seat-owner",
        "permit-only-typed-generation-bound-handoff",
    )
    recovery = (
        "stop-only-current-generation-bound-graphical-unit",
        "revoke-five-device-grants", "remove-session-descriptor",
        "activate-tty1", "verify-no-machine-mount-socket-process-or-lease-residue",
        "never-automatically-restart-graphics",
    )
    forbidden = (
        "grant-tty1", "grant-nvidia", "grant-unlisted-input",
        "run-two-graphical-environments", "extend-deadline",
        "accept-command-or-path-from-ui", "delete-headless-hub",
        "report-success-before-zero-residue",
    )
    draft = {
        "profile": PROFILE, "test_generation": TEST_GENERATION,
        "release_manifest_digest": RELEASE_MANIFEST_DIGEST,
        "deadline_seconds": DEADLINE_SECONDS, "recovery_vt": "/dev/tty1",
        "transition_vt": "/dev/tty2", "devices": DEVICES,
        "session_subjects": subjects, "ordered_effects": ordered,
        "recovery_effects": recovery, "forbidden_effects": forbidden,
        "observation_digest": _digest(asdict(observation)),
    }
    return GraphicalRuntimePlan(**draft, plan_digest=_digest(draft))
