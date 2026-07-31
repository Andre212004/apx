"""Closed executor effect mapping for the first Hub/test graphical handoff."""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
import subprocess
from typing import Callable

from apx_executor_contract import OperationPlan, build_operation_plan
from apx_executor_endpoint import EffectResult


HUB_GENERATION = "2c3dbacc-106f-4053-8603-f649552f5513"
TEST_GENERATION = "69b56acc-fd4d-4499-8009-e1d0108466f4"
BROKER = "/var/lib/apx/graphical-v1/apx-graphical-broker-v1.py"
COMMANDS = {
    ("activate", "test", TEST_GENERATION): (
        BROKER, "--handoff", "hub-to-test", "--hub-generation", HUB_GENERATION,
        "--test-generation", TEST_GENERATION,
    ),
    ("stop", "test", TEST_GENERATION): (
        BROKER, "--handoff", "test-to-hub", "--hub-generation", HUB_GENERATION,
        "--test-generation", TEST_GENERATION,
    ),
}
_SHA = re.compile(r"[0-9a-f]{64}")


class GraphicalEffectError(RuntimeError):
    pass


Runner = Callable[[tuple[str, ...]], subprocess.CompletedProcess[str]]


def system_runner(command: tuple[str, ...]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, capture_output=True, timeout=45,
                          env={"PATH": "/usr/bin", "LC_ALL": "C"})


def apply_graphical_effect(plan: OperationPlan, request_digest: str,
                           runner: Runner = system_runner) -> EffectResult:
    if type(plan) is not OperationPlan or not isinstance(request_digest, str) or not _SHA.fullmatch(request_digest):
        raise GraphicalEffectError("graphical effect identity is malformed")
    expected = build_operation_plan(plan.operation_kind, plan.logical_name,
                                    plan.expected_generation,
                                    policy_version=plan.policy_version)
    if plan != expected:
        raise GraphicalEffectError("graphical effect plan differs from fixed policy")
    try:
        command = COMMANDS[(plan.operation_kind, plan.logical_name, plan.expected_generation)]
    except KeyError as error:
        raise GraphicalEffectError("operation is outside the first graphical handoff") from error
    completed = runner(command)
    if type(completed) is not subprocess.CompletedProcess:
        raise GraphicalEffectError("graphical broker returned wrong result type")
    if completed.returncode != 0:
        return EffectResult("incomplete", ("graphical broker failed; recovery state must be inspected",))
    try:
        result = json.loads(completed.stdout)
    except (TypeError, json.JSONDecodeError) as error:
        raise GraphicalEffectError("graphical broker result is malformed") from error
    required = {"classification", "direction", "incoming_generation", "outgoing_generation",
                "single_owner", "watchdog_active", "recovery_verified"}
    direction = "hub-to-test" if plan.operation_kind == "activate" else "test-to-hub"
    outgoing = HUB_GENERATION if direction == "hub-to-test" else TEST_GENERATION
    incoming = TEST_GENERATION if direction == "hub-to-test" else HUB_GENERATION
    if set(result) != required or (
        result.get("classification"), result.get("direction"),
        result.get("outgoing_generation"), result.get("incoming_generation"),
        result.get("single_owner"), result.get("watchdog_active"),
        result.get("recovery_verified"),
    ) != ("handoff-complete", direction, outgoing, incoming, True, True, True):
        return EffectResult("incomplete", ("graphical broker completion evidence differs",))
    return EffectResult("accepted", ())
