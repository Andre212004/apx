"""Closed typed contract for APX Host-owned desktop service menus."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import re


PROFILE = "apx-host-services-v2"
SCHEMA = 2
MAX_MESSAGE_BYTES = 16384
OPERATIONS = (
    "bluetooth-connect", "bluetooth-disconnect", "bluetooth-power",
    "status", "wifi-connect", "wifi-disconnect", "wifi-scan",
)
_NO_TARGET = {"status", "wifi-disconnect", "wifi-scan"}
_MAC = re.compile(r"(?:[0-9A-F]{2}:){5}[0-9A-F]{2}")
_INTERFACE = re.compile(r"[a-zA-Z0-9_.-]{1,32}")
_TIMEZONE = re.compile(r"[A-Za-z0-9_+.-]+(?:/[A-Za-z0-9_+.-]+)+")


class HostServicesV2ContractError(ValueError):
    pass


def _label(value: object, *, maximum: int = 64) -> str:
    if type(value) is not str or not 1 <= len(value) <= maximum or any(
        ord(character) < 32 or ord(character) == 127 for character in value
    ):
        raise HostServicesV2ContractError("desktop-service label is unsafe")
    return value


@dataclass(frozen=True)
class BluetoothDevice:
    address: str
    name: str
    connected: bool


@dataclass(frozen=True)
class HostServicesV2State:
    network_backend: str
    network_interface: str
    network_connected: bool
    network_name: str | None
    known_networks: tuple[str, ...]
    available_networks: tuple[str, ...]
    timezone: str
    ntp_enabled: bool
    time_synchronized: bool
    bluetooth_backend: str
    bluetooth_controller_present: bool
    bluetooth_powered: bool
    bluetooth_devices: tuple[BluetoothDevice, ...]


def request_bytes(operation: str = "status", target: str | None = None) -> bytes:
    validate_request(operation, target)
    value = {"operation": operation, "profile": PROFILE, "schema": SCHEMA, "target": target}
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def validate_request(operation: object, target: object) -> tuple[str, str | None]:
    if operation not in OPERATIONS:
        raise HostServicesV2ContractError("desktop-service operation is unsupported")
    if operation in _NO_TARGET:
        if target is not None:
            raise HostServicesV2ContractError("desktop-service operation takes no target")
    elif operation == "bluetooth-power":
        if target not in {"on", "off"}:
            raise HostServicesV2ContractError("Bluetooth power target differs")
    elif operation in {"bluetooth-connect", "bluetooth-disconnect"}:
        if type(target) is not str or _MAC.fullmatch(target) is None:
            raise HostServicesV2ContractError("Bluetooth device target differs")
    else:
        _label(target)
    return str(operation), target if type(target) is str else None


def parse_request(data: bytes) -> tuple[str, str | None]:
    if type(data) is not bytes or not data or len(data) > MAX_MESSAGE_BYTES:
        raise HostServicesV2ContractError("desktop-service request is absent or oversized")
    try:
        value = json.loads(data)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise HostServicesV2ContractError("desktop-service request is malformed") from error
    if type(value) is not dict or set(value) != {"operation", "profile", "schema", "target"} or (
        value.get("profile"), value.get("schema")
    ) != (PROFILE, SCHEMA):
        raise HostServicesV2ContractError("desktop-service request envelope differs")
    return validate_request(value.get("operation"), value.get("target"))


def validate_state(state: HostServicesV2State) -> HostServicesV2State:
    if type(state) is not HostServicesV2State:
        raise HostServicesV2ContractError("desktop-service state has wrong type")
    if state.network_backend not in {"iwd", "unavailable"} or not _INTERFACE.fullmatch(state.network_interface):
        raise HostServicesV2ContractError("network state differs")
    if type(state.network_connected) is not bool or state.network_connected != (state.network_name is not None):
        raise HostServicesV2ContractError("network connection state contradicts its name")
    if state.network_name is not None:
        _label(state.network_name)
    for catalogue in (state.known_networks, state.available_networks):
        if type(catalogue) is not tuple or catalogue != tuple(sorted(set(catalogue))):
            raise HostServicesV2ContractError("network catalogue is not canonical")
        for name in catalogue:
            _label(name)
    if not _TIMEZONE.fullmatch(state.timezone) or type(state.ntp_enabled) is not bool \
            or type(state.time_synchronized) is not bool or state.time_synchronized and not state.ntp_enabled:
        raise HostServicesV2ContractError("time state differs")
    if state.bluetooth_backend not in {"bluez", "unavailable"} \
            or type(state.bluetooth_controller_present) is not bool \
            or type(state.bluetooth_powered) is not bool:
        raise HostServicesV2ContractError("Bluetooth state differs")
    if state.bluetooth_powered and (state.bluetooth_backend != "bluez" or not state.bluetooth_controller_present):
        raise HostServicesV2ContractError("Bluetooth power state contradicts its backend")
    if type(state.bluetooth_devices) is not tuple or state.bluetooth_devices != tuple(
        sorted(set(state.bluetooth_devices), key=lambda item: item.address)
    ):
        raise HostServicesV2ContractError("Bluetooth device catalogue is not canonical")
    for device in state.bluetooth_devices:
        if type(device) is not BluetoothDevice or _MAC.fullmatch(device.address) is None \
                or type(device.connected) is not bool:
            raise HostServicesV2ContractError("Bluetooth device differs")
        _label(device.name, maximum=128)
    return state


def response_bytes(state: HostServicesV2State) -> bytes:
    validate_state(state)
    value = {"ok": True, "profile": PROFILE, "schema": SCHEMA, "state": asdict(state)}
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def parse_response(data: bytes) -> HostServicesV2State:
    if type(data) is not bytes or not data or len(data) > MAX_MESSAGE_BYTES:
        raise HostServicesV2ContractError("desktop-service response is absent or oversized")
    try:
        value = json.loads(data)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise HostServicesV2ContractError("desktop-service response is malformed") from error
    if type(value) is not dict or set(value) != {"ok", "profile", "schema", "state"} or (
        value.get("ok"), value.get("profile"), value.get("schema")
    ) != (True, PROFILE, SCHEMA):
        raise HostServicesV2ContractError("desktop-service response envelope differs")
    raw = value["state"]
    if type(raw) is not dict or set(raw) != set(HostServicesV2State.__dataclass_fields__):
        raise HostServicesV2ContractError("desktop-service response fields differ")
    try:
        raw["known_networks"] = tuple(raw["known_networks"])
        raw["available_networks"] = tuple(raw["available_networks"])
        raw["bluetooth_devices"] = tuple(BluetoothDevice(**item) for item in raw["bluetooth_devices"])
        return validate_state(HostServicesV2State(**raw))
    except (TypeError, KeyError) as error:
        raise HostServicesV2ContractError("desktop-service response values differ") from error
