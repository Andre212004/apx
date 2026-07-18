"""Pure non-extendable watchdog state machine for physical H0."""

from __future__ import annotations

from dataclasses import dataclass, replace
import re


GENERATION = "c4fc5c49-4106-4a56-b1f0-13bffa41a0c1"
PLAN_DIGEST = "3ef21d19a2518d4fcea9d51513cc1eee63f6ff593d4470bcc10955b06e3059cb"
TIMEOUT_SECONDS = 120
_SHA = re.compile(r"[0-9a-f]{64}")


class H0WatchdogError(ValueError):
    pass


@dataclass(frozen=True)
class H0WatchdogState:
    generation: str
    plan_digest: str
    phase: str
    armed_at: int
    deadline: int
    devices_granted: bool
    graphical_ready: bool
    teardown_requested: bool
    tty1_restored: bool
    processes_remaining: int
    mounts_remaining: int
    sockets_remaining: int
    leases_remaining: int


@dataclass(frozen=True)
class H0RecoveryDecision:
    expired: bool
    safe_complete: bool
    actions: tuple[str, ...]


def arm_watchdog(*, generation: str, plan_digest: str, monotonic_second: int) -> H0WatchdogState:
    if generation != GENERATION or plan_digest != PLAN_DIGEST:
        raise H0WatchdogError("watchdog identity is stale or outside H0")
    if type(monotonic_second) is not int or monotonic_second < 0:
        raise H0WatchdogError("watchdog time is invalid")
    return H0WatchdogState(generation, plan_digest, "armed", monotonic_second,
        monotonic_second + TIMEOUT_SECONDS, False, False, False, False, 0, 0, 0, 0)


def record_device_grant(state: H0WatchdogState, *, monotonic_second: int) -> H0WatchdogState:
    _validate(state)
    if state.phase != "armed" or monotonic_second >= state.deadline:
        raise H0WatchdogError("device grant is late, repeated, or unarmed")
    return replace(state, phase="devices-granted", devices_granted=True)


def record_graphical_ready(state: H0WatchdogState, *, monotonic_second: int) -> H0WatchdogState:
    _validate(state)
    if state.phase != "devices-granted" or monotonic_second >= state.deadline:
        raise H0WatchdogError("graphical readiness is late or out of order")
    return replace(state, phase="graphical-ready", graphical_ready=True)


def request_teardown(state: H0WatchdogState) -> H0WatchdogState:
    _validate(state)
    if state.phase == "complete":
        raise H0WatchdogError("completed watchdog cannot restart teardown")
    return replace(state, phase="teardown", teardown_requested=True, graphical_ready=False)


def observe_teardown(
    state: H0WatchdogState, *, tty1_restored: bool, processes: int,
    mounts: int, sockets: int, leases: int,
) -> H0WatchdogState:
    _validate(state)
    values = (processes, mounts, sockets, leases)
    if state.phase != "teardown" or type(tty1_restored) is not bool:
        raise H0WatchdogError("teardown observation is out of order")
    if any(type(value) is not int or value < 0 for value in values):
        raise H0WatchdogError("teardown residue count is invalid")
    candidate = replace(state, tty1_restored=tty1_restored,
        processes_remaining=processes, mounts_remaining=mounts,
        sockets_remaining=sockets, leases_remaining=leases)
    if tty1_restored and values == (0, 0, 0, 0):
        candidate = replace(candidate, phase="complete", devices_granted=False)
    return candidate


def recovery_decision(state: H0WatchdogState, *, monotonic_second: int) -> H0RecoveryDecision:
    _validate(state)
    if type(monotonic_second) is not int or monotonic_second < state.armed_at:
        raise H0WatchdogError("recovery time is invalid")
    expired = monotonic_second >= state.deadline
    safe = state.phase == "complete"
    if safe:
        actions = ("retain-evidence", "do-not-restart-graphics")
    elif expired or state.phase == "teardown":
        actions = ("terminate-generation-bound-unit", "revoke-five-devices",
            "activate-tty1", "observe-zero-residue", "do-not-restart-graphics")
    else:
        actions = ("keep-deadline-armed", "do-not-extend-deadline")
    return H0RecoveryDecision(expired, safe, actions)


def _validate(state: H0WatchdogState) -> None:
    if type(state) is not H0WatchdogState or state.generation != GENERATION:
        raise H0WatchdogError("watchdog state identity is invalid")
    if not _SHA.fullmatch(state.plan_digest) or state.plan_digest != PLAN_DIGEST:
        raise H0WatchdogError("watchdog plan identity is invalid")
    if state.deadline != state.armed_at + TIMEOUT_SECONDS:
        raise H0WatchdogError("watchdog deadline was extended or changed")
    if state.phase not in {"armed", "devices-granted", "graphical-ready", "teardown", "complete"}:
        raise H0WatchdogError("watchdog phase is invalid")
    for value in (state.devices_granted, state.graphical_ready, state.teardown_requested, state.tty1_restored):
        if type(value) is not bool:
            raise H0WatchdogError("watchdog flags are malformed")
    if state.phase == "complete" and (state.devices_granted or not state.tty1_restored or any((state.processes_remaining, state.mounts_remaining, state.sockets_remaining, state.leases_remaining))):
        raise H0WatchdogError("completed watchdog still has residue")
