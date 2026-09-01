"""Closed read-only contract for Host-owned desktop essentials."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import re


PROFILE = "apx-host-services-v1"
SCHEMA = 1
MAX_MESSAGE_BYTES = 4096
OPERATIONS = ("bluetooth-toggle", "status")
_INTERFACE = re.compile(r"[a-zA-Z0-9_.-]{1,32}")
_TIMEZONE = re.compile(r"[A-Za-z0-9_+.-]+(?:/[A-Za-z0-9_+.-]+)+")


class HostServicesContractError(ValueError):
    pass


@dataclass(frozen=True)
class HostServicesState:
    network_backend: str
    network_interface: str
    network_connected: bool
    network_name: str | None
    timezone: str
    ntp_enabled: bool
    time_synchronized: bool
    bluetooth_backend: str
    bluetooth_controller_present: bool
    bluetooth_powered: bool


def request_bytes(operation: str = "status") -> bytes:
    if operation not in OPERATIONS:
        raise HostServicesContractError("Host-services operation is unsupported")
    value = {"operation": operation, "profile": PROFILE, "schema": SCHEMA}
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def parse_request(data: bytes) -> str:
    if type(data) is not bytes or not data or len(data) > MAX_MESSAGE_BYTES:
        raise HostServicesContractError("Host-services request is absent or oversized")
    try:
        value = json.loads(data)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise HostServicesContractError("Host-services request is malformed") from error
    if type(value) is not dict or set(value) != {"operation", "profile", "schema"} or (
        value.get("profile"), value.get("schema")
    ) != (PROFILE, SCHEMA) or value.get("operation") not in OPERATIONS:
        raise HostServicesContractError("Host-services request differs from the closed operations")
    return str(value["operation"])


def validate_state(state: HostServicesState) -> HostServicesState:
    if type(state) is not HostServicesState:
        raise HostServicesContractError("Host-services state has wrong type")
    if state.network_backend not in {"iwd", "unavailable"}:
        raise HostServicesContractError("network backend is unsupported")
    if not _INTERFACE.fullmatch(state.network_interface):
        raise HostServicesContractError("network interface is malformed")
    if type(state.network_connected) is not bool:
        raise HostServicesContractError("network state has wrong type")
    if state.network_name is not None and (
        type(state.network_name) is not str
        or not 1 <= len(state.network_name) <= 64
        or any(ord(character) < 32 or ord(character) == 127 for character in state.network_name)
    ):
        raise HostServicesContractError("network display name is unsafe")
    if state.network_connected != (state.network_name is not None):
        raise HostServicesContractError("network connection and display name disagree")
    if not _TIMEZONE.fullmatch(state.timezone):
        raise HostServicesContractError("timezone is malformed")
    if type(state.ntp_enabled) is not bool or type(state.time_synchronized) is not bool:
        raise HostServicesContractError("time state has wrong type")
    if state.time_synchronized and not state.ntp_enabled:
        raise HostServicesContractError("time synchronization contradicts disabled NTP")
    if state.bluetooth_backend not in {"bluez", "unavailable"}:
        raise HostServicesContractError("Bluetooth backend is unsupported")
    if type(state.bluetooth_controller_present) is not bool or type(state.bluetooth_powered) is not bool:
        raise HostServicesContractError("Bluetooth state has wrong type")
    if state.bluetooth_powered and (
        not state.bluetooth_controller_present or state.bluetooth_backend != "bluez"
    ):
        raise HostServicesContractError("Bluetooth power state is contradictory")
    return state


def response_bytes(state: HostServicesState) -> bytes:
    validate_state(state)
    value = {"ok": True, "profile": PROFILE, "schema": SCHEMA, "state": asdict(state)}
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def parse_response(data: bytes) -> HostServicesState:
    if type(data) is not bytes or not data or len(data) > MAX_MESSAGE_BYTES:
        raise HostServicesContractError("Host-services response is absent or oversized")
    try:
        value = json.loads(data)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise HostServicesContractError("Host-services response is malformed") from error
    if type(value) is not dict or set(value) != {"ok", "profile", "schema", "state"} or (
        value["ok"], value["profile"], value["schema"]
    ) != (True, PROFILE, SCHEMA):
        raise HostServicesContractError("Host-services response envelope differs")
    raw = value["state"]
    if type(raw) is not dict or set(raw) != set(HostServicesState.__dataclass_fields__):
        raise HostServicesContractError("Host-services response state differs")
    try:
        return validate_state(HostServicesState(**raw))
    except TypeError as error:
        raise HostServicesContractError("Host-services response fields differ") from error
