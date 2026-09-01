"""Versioned, secret-aware contract for APX Host shared services v3."""

from __future__ import annotations

import json
import re
import uuid


PROFILE = "apx-host-shared-services"
VERSION = 3
MAX_MESSAGE_BYTES = 65536
MAX_SSID_BYTES = 32
OPERATIONS = (
    "bluetooth.device.connect", "bluetooth.device.disconnect", "bluetooth.device.remove",
    "bluetooth.pair.begin", "bluetooth.pair.respond", "bluetooth.pair.status",
    "bluetooth.power", "bluetooth.scan", "bluetooth.status",
    "capabilities.get", "events.subscribe", "network.connect",
    "network.connectivity-check", "network.disconnect", "network.forget",
    "network.portal.open", "network.scan", "network.status", "radio.status",
    "snapshot.get",
)
SECRET_FIELDS = frozenset({"credential", "passphrase", "password", "pin", "secret"})
_REQUEST_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,95}")
_BLUETOOTH_ADDRESS = re.compile(r"(?:[0-9A-F]{2}:){5}[0-9A-F]{2}")
_PAIR_SESSION = re.compile(r"[a-f0-9]{32}")


class HostServicesV3ContractError(ValueError):
    pass


def _request_id(value: object) -> str:
    if type(value) is not str or _REQUEST_ID.fullmatch(value) is None:
        raise HostServicesV3ContractError("request_id is invalid")
    return value


def validate_ssid(value: object) -> str:
    if type(value) is not str or not value or len(value.encode("utf-8")) > MAX_SSID_BYTES \
            or "\x00" in value or "\n" in value or "\r" in value:
        raise HostServicesV3ContractError("SSID is invalid")
    return value


def _credential(value: object) -> dict[str, str] | None:
    if value is None:
        return None
    if type(value) is not dict or set(value) != {"kind", "value"} \
            or value.get("kind") != "passphrase" or type(value.get("value")) is not str:
        raise HostServicesV3ContractError("credential is invalid")
    secret = value["value"]
    if not 8 <= len(secret) <= 63 or any(ord(character) < 32 or ord(character) == 127 for character in secret):
        raise HostServicesV3ContractError("passphrase is invalid")
    return {"kind": "passphrase", "value": secret}


def validate_payload(operation: str, payload: object) -> dict[str, object]:
    if operation not in OPERATIONS or type(payload) is not dict:
        raise HostServicesV3ContractError("operation or payload is unsupported")
    if operation in {"bluetooth.scan", "bluetooth.status", "capabilities.get",
                     "network.connectivity-check", "network.disconnect",
                     "network.portal.open", "network.scan", "network.status", "radio.status", "snapshot.get"}:
        if payload:
            raise HostServicesV3ContractError("operation takes no payload")
        return {}
    if operation == "bluetooth.power":
        if set(payload) != {"powered"} or type(payload.get("powered")) is not bool:
            raise HostServicesV3ContractError("Bluetooth power payload differs")
        return {"powered": payload["powered"]}
    if operation in {"bluetooth.device.connect", "bluetooth.device.disconnect",
                     "bluetooth.device.remove", "bluetooth.pair.begin"}:
        address = payload.get("address")
        if set(payload) != {"address"} or type(address) is not str \
                or _BLUETOOTH_ADDRESS.fullmatch(address) is None:
            raise HostServicesV3ContractError("Bluetooth device payload differs")
        return {"address": address}
    if operation == "bluetooth.pair.status":
        session_id = payload.get("session_id")
        if set(payload) != {"session_id"} or type(session_id) is not str \
                or _PAIR_SESSION.fullmatch(session_id) is None:
            raise HostServicesV3ContractError("Bluetooth pairing session differs")
        return {"session_id": session_id}
    if operation == "bluetooth.pair.respond":
        if set(payload) != {"accept", "pin", "session_id"}:
            raise HostServicesV3ContractError("Bluetooth pairing response differs")
        session_id, accept, pin = payload["session_id"], payload["accept"], payload["pin"]
        if type(session_id) is not str or _PAIR_SESSION.fullmatch(session_id) is None \
                or type(accept) is not bool or pin is not None and (
                    type(pin) is not str or not 1 <= len(pin) <= 16
                    or any(ord(character) < 32 or ord(character) == 127 for character in pin)
                ):
            raise HostServicesV3ContractError("Bluetooth pairing response is invalid")
        return {"accept": accept, "pin": pin, "session_id": session_id}
    if operation == "events.subscribe":
        if set(payload) - {"after", "timeout_ms"}:
            raise HostServicesV3ContractError("event subscription payload differs")
        after = payload.get("after", 0); timeout = payload.get("timeout_ms", 25000)
        if type(after) is not int or after < 0 or type(timeout) is not int or not 1000 <= timeout <= 30000:
            raise HostServicesV3ContractError("event subscription bounds differ")
        return {"after": after, "timeout_ms": timeout}
    if operation == "network.forget":
        if set(payload) != {"ssid"}:
            raise HostServicesV3ContractError("network forget payload differs")
        return {"ssid": validate_ssid(payload["ssid"])}
    if set(payload) != {"credential", "ssid"}:
        raise HostServicesV3ContractError("network connect payload differs")
    return {"ssid": validate_ssid(payload["ssid"]), "credential": _credential(payload["credential"])}


def request_bytes(operation: str, payload: dict[str, object] | None = None, *, request_id: str | None = None) -> bytes:
    request_id = _request_id(request_id or uuid.uuid4().hex)
    value = {"operation": operation, "payload": validate_payload(operation, payload or {}),
             "profile": PROFILE, "request_id": request_id, "version": VERSION}
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def parse_request(data: bytes) -> tuple[str, str, dict[str, object]]:
    if type(data) is not bytes or not data or len(data) > MAX_MESSAGE_BYTES:
        raise HostServicesV3ContractError("request is absent or oversized")
    try:
        value = json.loads(data)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise HostServicesV3ContractError("request is malformed") from error
    if type(value) is not dict or set(value) != {"operation", "payload", "profile", "request_id", "version"} \
            or value.get("profile") != PROFILE or value.get("version") != VERSION:
        raise HostServicesV3ContractError("request envelope differs")
    operation = value.get("operation")
    if type(operation) is not str:
        raise HostServicesV3ContractError("operation differs")
    return _request_id(value.get("request_id")), operation, validate_payload(operation, value.get("payload"))


def response_bytes(request_id: str, result: object) -> bytes:
    value = {"error": None, "profile": PROFILE, "request_id": _request_id(request_id),
             "result": result, "version": VERSION}
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def error_bytes(request_id: str, code: str, message: str) -> bytes:
    if type(code) is not str or not re.fullmatch(r"[a-z][a-z0-9_]{1,47}", code) \
            or type(message) is not str or not 1 <= len(message) <= 256:
        raise HostServicesV3ContractError("error differs")
    value = {"error": {"code": code, "message": message}, "profile": PROFILE,
             "request_id": _request_id(request_id), "result": None, "version": VERSION}
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def parse_response(data: bytes) -> dict[str, object]:
    if type(data) is not bytes or not data or len(data) > MAX_MESSAGE_BYTES:
        raise HostServicesV3ContractError("response is absent or oversized")
    try:
        value = json.loads(data)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise HostServicesV3ContractError("response is malformed") from error
    if type(value) is not dict or set(value) != {"error", "profile", "request_id", "result", "version"} \
            or value.get("profile") != PROFILE or value.get("version") != VERSION:
        raise HostServicesV3ContractError("response envelope differs")
    _request_id(value.get("request_id"))
    if value["error"] is not None:
        error = value["error"]
        if type(error) is not dict or set(error) != {"code", "message"}:
            raise HostServicesV3ContractError("response error differs")
    return value


def redacted(value: object) -> object:
    """Return an audit-safe deep copy; never log the unredacted request."""
    if type(value) is dict:
        return {key: "<redacted>" if key.lower() in SECRET_FIELDS else redacted(item)
                for key, item in value.items()}
    if type(value) is list:
        return [redacted(item) for item in value]
    return value
