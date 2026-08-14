"""Pure active-Environment audio state handoff contract."""

from __future__ import annotations

from dataclasses import dataclass
import re


SCHEMA = 1
PROFILE = "apx-active-audio-handoff-v1"
_NAME = re.compile(r"[a-z](?:[a-z0-9]|-(?=[a-z0-9])){0,26}")


class AudioHandoffError(ValueError):
    pass


@dataclass(frozen=True)
class AudioState:
    schema: int
    profile: str
    output_volume: int
    output_muted: bool
    input_volume: int
    input_muted: bool
    output_name: str | None
    input_name: str | None


@dataclass(frozen=True)
class AudioHandoffPlan:
    outgoing_environment: str | None
    incoming_environment: str
    state: AudioState
    effects: tuple[str, ...]
    capture_access: str


def validate_state(state: AudioState) -> AudioState:
    if type(state) is not AudioState or state.schema != SCHEMA or state.profile != PROFILE:
        raise AudioHandoffError("audio state schema differs")
    for field in ("output_volume", "input_volume"):
        value = getattr(state, field)
        if type(value) is not int or not 0 <= value <= 100: raise AudioHandoffError("audio volume is outside bounds")
    if type(state.output_muted) is not bool or type(state.input_muted) is not bool:
        raise AudioHandoffError("audio mute state differs")
    for field in ("output_name", "input_name"):
        value = getattr(state, field)
        if value is not None and (type(value) is not str or not 1 <= len(value) <= 128 \
                                  or any(ord(character) < 32 for character in value)):
            raise AudioHandoffError("audio device label is unsafe")
    return state


def build_handoff(outgoing_environment: str | None, incoming_environment: str,
                  state: AudioState) -> AudioHandoffPlan:
    validate_state(state)
    if outgoing_environment is not None and _NAME.fullmatch(outgoing_environment) is None \
            or _NAME.fullmatch(incoming_environment) is None or outgoing_environment == incoming_environment:
        raise AudioHandoffError("audio handoff Environment identity differs")
    effects = (
        "capture-output-and-input-state-from-authoritative-active-environment",
        "persist-root-owned-state-without-stream-or-application-metadata",
        "stop-local-pipewire-and-revoke-playback-and-capture-device-leases",
        "prove-outgoing-environment-cannot-open-audio-devices",
        "lease-exact-playback-and-capture-devices-only-to-incoming-environment",
        "start-incoming-environment-local-pipewire",
        "apply-output-volume-mute-and-selected-output",
        "apply-input-volume-mute-and-selected-input",
        "publish-incoming-audio-authority-after-verification",
    )
    return AudioHandoffPlan(outgoing_environment, incoming_environment, state, effects, "active-environment-only")
