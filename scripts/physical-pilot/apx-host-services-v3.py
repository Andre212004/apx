#!/usr/bin/env python3
"""Authenticated Host backend for APX shared services v3."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import pty
import re
import select
import socket
import stat
import struct
import subprocess
import sys
import termios
import threading
import time
import uuid

sys.path.insert(0, "/usr/lib/apx")
from apx_host_services_peer import HostServicesPeer, authorize_shared_service_peer  # noqa: E402
from apx_host_services_v3_contract import (  # noqa: E402
    MAX_MESSAGE_BYTES, error_bytes, parse_request, response_bytes,
)
from apx_captive_portal import (  # noqa: E402
    capport_uri_from_networkctl, check as check_connectivity, result as connectivity_result,
    unknown as unknown_connectivity,
)

SOCKET = Path("/run/apx/host-services-v3.sock")
RFKILL_ROOT = Path("/sys/class/rfkill")
RFKILL = "/usr/bin/rfkill"
WIFI_INTERFACE = "wlan0"
ANSI = re.compile(r"\x1b\[[0-9;]*m")
MAX_CLIENTS = 16
CAPABILITIES = {
    "events": ["bluetooth.changed", "bluetooth.scan_completed", "network.changed", "network.scan_completed", "network.connectivity_changed",
               "host.service_restarted"],
    "operations": ["bluetooth.device.connect", "bluetooth.device.disconnect", "bluetooth.device.remove",
                   "bluetooth.pair.begin", "bluetooth.pair.respond", "bluetooth.pair.status",
                   "bluetooth.power", "bluetooth.scan", "bluetooth.status",
                   "capabilities.get", "events.subscribe", "network.connect", "network.disconnect",
                   "network.connectivity-check", "network.forget", "network.portal.open",
                   "network.scan", "network.status", "radio.status", "snapshot.get"],
    "security": {"bluetooth_pairing_agent": "KeyboardDisplay", "enterprise_wifi": False,
                 "secret_transport": "unix-socket-body", "shell": False},
}
_LOCK = threading.Lock()
_MUTATION_LOCK = threading.Lock()
_CONNECTIVITY_CHECK_LOCK = threading.Lock()
_CONNECTIVITY_LOCK = threading.Lock()
_CLIENTS = threading.BoundedSemaphore(MAX_CLIENTS)
_SEQUENCE = 1
_LAST_DIGEST = ""
_LAST_EVENT = "host.service_restarted"
_CONNECTIVITY_IDENTITY: str | None = None
_CONNECTIVITY = unknown_connectivity()
_PAIR_LOCK = threading.Lock()
_PAIR_SESSION: dict[str, object] | None = None


class HostServicesV3Error(RuntimeError):
    code = "operation_failed"


class UnsupportedError(HostServicesV3Error):
    code = "unsupported"


class ConflictError(HostServicesV3Error):
    code = "conflict"


def run(arguments: tuple[str, ...], timeout: int = 10) -> subprocess.CompletedProcess[str]:
    return subprocess.run(arguments, text=True, capture_output=True, check=False, timeout=timeout,
                          env={"PATH": "/usr/bin", "LC_ALL": "C", "TERM": "dumb", "SYSTEMD_COLORS": "0"})


def clean(text: str) -> str:
    return ANSI.sub("", text)


def _properties(arguments: tuple[str, ...]) -> dict[str, str]:
    result = run(arguments)
    if result.returncode:
        return {}
    values = {}
    for line in clean(result.stdout).splitlines():
        match = re.match(r"^\s*(?:\*\s*)?([A-Za-z][A-Za-z0-9 ]*?)\s{2,}(.+?)\s*$", line)
        if match:
            values[match.group(1).strip()] = match.group(2).strip()
    return values


def known_networks() -> dict[str, str]:
    result = run(("/usr/bin/iwctl", "known-networks", "list")); values = {}
    for line in clean(result.stdout).splitlines():
        match = re.match(r"^\s*(.+?)\s{2,}(psk|open|8021x)\s{2,}", line)
        if match: values[match.group(1).strip()] = match.group(2)
    return values


def available_networks() -> list[dict[str, object]]:
    result = run(("/usr/bin/iwctl", "station", WIFI_INTERFACE, "get-networks", "rssi-dbms")); values = {}
    for line in clean(result.stdout).splitlines():
        selected = line.lstrip().startswith(">")
        text = line.strip().removeprefix(">").strip()
        match = re.match(r"(.+?)\s{2,}(psk|open|8021x)\s{2,}(-?[0-9]+)\s*$", text)
        if not match: continue
        ssid, security, centi_dbm = match.groups()
        values[(ssid.strip(), security)] = {
            "connected": selected, "known": False, "security": "enterprise" if security == "8021x" else security,
            "signal": max(0, min(100, round(2 * (int(centi_dbm) / 100 + 100)))), "ssid": ssid.strip(),
        }
    known = known_networks()
    for value in values.values(): value["known"] = value["ssid"] in known
    return sorted(values.values(), key=lambda item: (-int(item["connected"]), -int(item["signal"]), str(item["ssid"])))


def _network_state() -> tuple[dict[str, object], str | None]:
    station = _properties(("/usr/bin/iwctl", "station", WIFI_INTERFACE, "show"))
    device = _properties(("/usr/bin/iwctl", "device", WIFI_INTERFACE, "show"))
    connected = station.get("State") == "connected"
    current = station.get("Connected network") if connected else None
    networks = available_networks()
    if current and not any(item["ssid"] == current for item in networks):
        networks.insert(0, {"connected": True, "known": current in known_networks(), "security": "unknown",
                            "signal": 0, "ssid": current})
    identity = f"{WIFI_INTERFACE}\0{current}\0{station.get('ConnectedBss', '')}" if connected and current else None
    return ({"backend": "iwd" if Path("/usr/bin/iwctl").is_file() else "unavailable",
             "connected": connected, "interface": WIFI_INTERFACE, "network": current,
             "powered": device.get("Powered") == "on", "networks": networks}, identity)


def _cached_connectivity(identity: str | None, connected: bool) -> dict[str, object]:
    global _CONNECTIVITY_IDENTITY, _CONNECTIVITY
    with _CONNECTIVITY_LOCK:
        if identity != _CONNECTIVITY_IDENTITY:
            _CONNECTIVITY_IDENTITY = identity
            _CONNECTIVITY = unknown_connectivity() if connected else connectivity_result("none")
        return json.loads(json.dumps(_CONNECTIVITY))


def network_state() -> dict[str, object]:
    state, identity = _network_state()
    state.update(_cached_connectivity(identity, bool(state["connected"])))
    return state


def radio_state() -> dict[str, object]:
    radios: dict[str, list[bool]] = {"wlan": [], "bluetooth": []}
    for directory in sorted(RFKILL_ROOT.glob("rfkill*")):
        try:
            kind = (directory / "type").read_text(encoding="ascii").strip()
            blocked = (directory / "soft").read_text(encoding="ascii").strip() == "1"
        except OSError:
            continue
        if kind in radios:
            radios[kind].append(blocked)
    present = bool(radios["wlan"]) and bool(radios["bluetooth"])
    return {
        "airplane_mode": present and all(radios["wlan"] + radios["bluetooth"]),
        "bluetooth_soft_blocked": bool(radios["bluetooth"]) and all(radios["bluetooth"]),
        "radios_present": present,
        "wlan_soft_blocked": bool(radios["wlan"]) and all(radios["wlan"]),
    }


def _default_route() -> bool:
    value = run(("/usr/bin/ip", "-j", "route", "show", "default", "dev", WIFI_INTERFACE))
    try:
        return value.returncode == 0 and bool(json.loads(value.stdout))
    except json.JSONDecodeError:
        return False


def _capport_uri() -> str | None:
    value = run(("/usr/bin/networkctl", "status", WIFI_INTERFACE, "--json=short"))
    if value.returncode:
        return None
    try:
        return capport_uri_from_networkctl(json.loads(value.stdout))
    except json.JSONDecodeError:
        return None


def perform_connectivity_check() -> dict[str, object]:
    global _CONNECTIVITY_IDENTITY, _CONNECTIVITY
    if not _CONNECTIVITY_CHECK_LOCK.acquire(blocking=False):
        raise ConflictError("another connectivity check is active")
    try:
        state, identity = _network_state()
        checked = check_connectivity(connected=bool(state["connected"]), has_default_route=_default_route(),
                                     interface=WIFI_INTERFACE, capport_uri=_capport_uri())
        changed = False
        with _CONNECTIVITY_LOCK:
            if identity == _CONNECTIVITY_IDENTITY or _CONNECTIVITY_IDENTITY is None:
                changed = (_CONNECTIVITY.get("connectivity"), _CONNECTIVITY.get("portal")) != \
                          (checked.get("connectivity"), checked.get("portal"))
                _CONNECTIVITY_IDENTITY = identity
                _CONNECTIVITY = checked
            else:
                checked = unknown_connectivity() if state["connected"] else connectivity_result("none")
        if changed:
            emit("network.connectivity_changed")
        return json.loads(json.dumps(checked))
    finally:
        _CONNECTIVITY_CHECK_LOCK.release()


def portal_open() -> dict[str, object]:
    state = network_state()
    if state.get("connectivity") == "unknown":
        perform_connectivity_check()
        state = network_state()
    portal = state.get("portal")
    if state.get("connectivity") != "portal" or type(portal) is not dict or portal.get("required") is not True:
        raise ConflictError("portal_not_detected")
    url = portal.get("url")
    if type(url) is not str:
        raise ConflictError("portal_url_invalid")
    return {"handler": "environment-browser", "url": url}


def _bluetooth_addresses(kind: str) -> set[str]:
    result = run(("/usr/bin/bluetoothctl", "devices", kind))
    return {match.group(1) for line in result.stdout.splitlines()
            if (match := re.match(r"^Device\s+((?:[0-9A-F]{2}:){5}[0-9A-F]{2})(?:\s|$)", line))}


def bluetooth_state() -> dict[str, object]:
    active = run(("/usr/bin/systemctl", "is-active", "--quiet", "bluetooth.service")).returncode == 0
    show = run(("/usr/bin/bluetoothctl", "show")) if active else None
    text = show.stdout if show else ""
    paired = _bluetooth_addresses("Paired") if active else set()
    connected = _bluetooth_addresses("Connected") if active else set()
    trusted = _bluetooth_addresses("Trusted") if active else set()
    devices = []
    catalogue = run(("/usr/bin/bluetoothctl", "devices")).stdout if active else ""
    for line in catalogue.splitlines():
        match = re.match(r"^Device\s+((?:[0-9A-F]{2}:){5}[0-9A-F]{2})\s+(.+)$", line)
        if match:
            devices.append({"address": match.group(1), "connected": match.group(1) in connected,
                            "name": match.group(2)[:128], "paired": match.group(1) in paired,
                            "trusted": match.group(1) in trusted})
    return {"backend": "bluez" if active else "unavailable",
            "controller_present": Path("/sys/class/bluetooth/hci0").exists(),
            "discovering": bool(re.search(r"^\s*Discovering:\s+yes\s*$", text, re.MULTILINE)),
            "pairable": bool(re.search(r"^\s*Pairable:\s+yes\s*$", text, re.MULTILINE)),
            "powered": bool(re.search(r"^\s*Powered:\s+yes\s*$", text, re.MULTILINE)),
            "devices": sorted(devices, key=lambda item: (not item["paired"], item["name"], item["address"]))}


def bluetooth_soft_blocked() -> bool:
    values = []
    for directory in sorted(RFKILL_ROOT.glob("rfkill*")):
        try:
            if (directory / "type").read_text(encoding="ascii").strip() == "bluetooth":
                values.append((directory / "soft").read_text(encoding="ascii").strip() == "1")
        except OSError:
            continue
    return not values or any(values)


def set_bluetooth_power(powered: bool) -> dict[str, object]:
    """Apply one complete BlueZ/rfkill transition and verify the real result."""
    if powered:
        # BlueZ reports `off-blocked` and refuses `power on` while its hci
        # rfkill entry is soft-blocked. Clear only the Bluetooth class first;
        # Wi-Fi and the laptop's separate airplane-mode control are untouched.
        unblocked = run((RFKILL, "unblock", "bluetooth"))
        if unblocked.returncode:
            raise HostServicesV3Error("Não foi possível desbloquear o rádio Bluetooth")
        # rfkill returns before BlueZ necessarily leaves its `off-blocked`
        # transition. Wait for both kernel and daemon views before asking for
        # power; an immediate command is reproducibly acknowledged but ignored.
        deadline = time.monotonic() + 5
        ready = False
        while time.monotonic() < deadline:
            show = run(("/usr/bin/bluetoothctl", "show"))
            ready = not bluetooth_soft_blocked() and "PowerState: off-blocked" not in show.stdout
            if ready:
                break
            time.sleep(0.1)
        if not ready:
            raise HostServicesV3Error("O rádio Bluetooth não concluiu o desbloqueio")
    result = run(("/usr/bin/bluetoothctl", "power", "on" if powered else "off"))
    if result.returncode:
        raise HostServicesV3Error("Não foi possível alterar o estado do Bluetooth")
    deadline = time.monotonic() + 5
    state = bluetooth_state()
    while state["powered"] is not powered and time.monotonic() < deadline:
        time.sleep(0.1)
        state = bluetooth_state()
    if state["powered"] is not powered:
        raise HostServicesV3Error("O controlador Bluetooth não confirmou o novo estado")
    return state


def _pair_cleanup(session: dict[str, object], *, terminate: bool = False) -> None:
    process = session["process"]
    if terminate and process.poll() is None:
        process.terminate()
        try: process.wait(timeout=2)
        except subprocess.TimeoutExpired: process.kill(); process.wait(timeout=2)
    master = session.get("master")
    if type(master) is int:
        try: os.close(master)
        except OSError: pass
        session["master"] = None


def _pair_view(session: dict[str, object]) -> dict[str, object]:
    process = session["process"]
    master = session.get("master")
    if type(master) is int:
        while True:
            readable, _, _ = select.select([master], [], [], 0)
            if not readable: break
            try: chunk = os.read(master, 4096)
            except OSError: break
            if not chunk: break
            session["output"] = (bytes(session["output"]) + chunk)[-16384:]
    output = clean(bytes(session["output"]).decode("utf-8", "replace"))
    phase, challenge, passkey, message = "working", None, None, "A emparelhar"
    confirm = re.search(r"Confirm passkey\s+([0-9]{6})", output, re.IGNORECASE)
    displayed = re.findall(r"Passkey:\s*([0-9]{6})", output, re.IGNORECASE)
    if re.search(r"Enter PIN code", output, re.IGNORECASE):
        phase, challenge, message = "needs-response", "pin", "Introduza o PIN do dispositivo"
    elif confirm:
        phase, challenge, passkey, message = "needs-response", "confirm", confirm.group(1), "Confirme o código nos dois dispositivos"
    elif displayed and process.poll() is None:
        phase, challenge, passkey, message = "waiting-device", "display-passkey", displayed[-1], "Escreva este código no dispositivo Bluetooth"
    if process.poll() is not None:
        if "Pairing successful" in output:
            run(("/usr/bin/bluetoothctl", "trust", str(session["address"])))
            phase, challenge, message = "completed", None, "Dispositivo emparelhado e confiável"
        else:
            phase, challenge, message = "failed", None, "O emparelhamento não foi concluído"
        _pair_cleanup(session)
    elif time.monotonic() >= float(session["deadline"]):
        _pair_cleanup(session, terminate=True)
        phase, challenge, message = "failed", None, "O emparelhamento expirou"
    session["phase"] = phase
    return {"address": session["address"], "challenge": challenge, "message": message,
            "passkey": passkey, "phase": phase, "session_id": session["id"]}


def pair_begin(address: str) -> dict[str, object]:
    global _PAIR_SESSION
    with _PAIR_LOCK:
        if _PAIR_SESSION is not None:
            current = _pair_view(_PAIR_SESSION)
            if current["phase"] not in {"completed", "failed"}:
                raise ConflictError("another Bluetooth pairing session is active")
        state = bluetooth_state()
        device = next((item for item in state["devices"] if item["address"] == address), None)
        if device is None: raise ConflictError("Bluetooth device is not present in the current scan")
        if device["paired"]: raise ConflictError("Bluetooth device is already paired")
        master, slave = pty.openpty()
        settings = termios.tcgetattr(slave); settings[3] &= ~termios.ECHO
        termios.tcsetattr(slave, termios.TCSANOW, settings)
        process = subprocess.Popen(("/usr/bin/bluetoothctl", "--agent", "KeyboardDisplay", "pair", address),
                                   stdin=slave, stdout=slave, stderr=slave, close_fds=True,
                                   env={"PATH": "/usr/bin", "LC_ALL": "C", "TERM": "dumb"})
        os.close(slave)
        _PAIR_SESSION = {"address": address, "deadline": time.monotonic() + 120,
                         "id": uuid.uuid4().hex, "master": master, "output": b"", "process": process}
        time.sleep(0.3)
        return _pair_view(_PAIR_SESSION)


def pair_status(session_id: str) -> dict[str, object]:
    with _PAIR_LOCK:
        if _PAIR_SESSION is None or _PAIR_SESSION["id"] != session_id:
            raise ConflictError("Bluetooth pairing session is absent")
        return _pair_view(_PAIR_SESSION)


def pair_respond(session_id: str, accept: bool, pin: str | None) -> dict[str, object]:
    with _PAIR_LOCK:
        if _PAIR_SESSION is None or _PAIR_SESSION["id"] != session_id:
            raise ConflictError("Bluetooth pairing session is absent")
        current = _pair_view(_PAIR_SESSION)
        if current["phase"] != "needs-response": raise ConflictError("Bluetooth pairing is not awaiting a response")
        if current["challenge"] == "pin" and (not accept or pin is None): answer = "no" if not accept else ""
        elif current["challenge"] == "pin": answer = pin
        elif pin is not None: raise ConflictError("PIN supplied for a confirmation challenge")
        else: answer = "yes" if accept else "no"
        master = _PAIR_SESSION.get("master")
        if type(master) is not int: raise ConflictError("Bluetooth pairing process ended")
        os.write(master, (answer + "\n").encode())
        time.sleep(0.2)
        return _pair_view(_PAIR_SESSION)


def power_state() -> dict[str, object]:
    batteries = []
    for directory in sorted(Path("/sys/class/power_supply").glob("BAT*")):
        def read(name: str) -> str | None:
            try: return (directory / name).read_text().strip()
            except OSError: return None
        capacity = read("capacity")
        batteries.append({"capacity": int(capacity) if capacity and capacity.isdecimal() else None,
                          "name": directory.name, "status": read("status")})
    return {"batteries": batteries, "brightness": "pending", "power_profile": "unavailable"}


def snapshot() -> dict[str, object]:
    timedate = run(("/usr/bin/timedatectl", "show", "-p", "Timezone", "-p", "NTP", "-p", "NTPSynchronized"))
    values = dict(line.split("=", 1) for line in timedate.stdout.splitlines() if "=" in line)
    return {"bluetooth": bluetooth_state(), "capabilities": CAPABILITIES, "health": "ok",
            "network": network_state(), "power": power_state(), "radio": radio_state(),
            "time": {"ntp_enabled": values.get("NTP") == "yes", "synchronized": values.get("NTPSynchronized") == "yes",
                     "timezone": values.get("Timezone", "Etc/UTC")}, "version": 3}


def secret_connect(ssid: str, secret: str) -> None:
    """Feed iwd through a no-echo PTY; the secret is never argv, output, journal or a temporary file."""
    master, slave = pty.openpty()
    settings = termios.tcgetattr(slave); settings[3] &= ~termios.ECHO; termios.tcsetattr(slave, termios.TCSANOW, settings)
    process = subprocess.Popen(("/usr/bin/iwctl", "station", WIFI_INTERFACE, "connect", ssid), stdin=slave,
                               stdout=slave, stderr=slave, close_fds=True,
                               env={"PATH": "/usr/bin", "LC_ALL": "C", "TERM": "dumb"})
    os.close(slave)
    output = bytearray(); sent = False; deadline = time.monotonic() + 25
    try:
        while process.poll() is None and time.monotonic() < deadline:
            readable, _, _ = select.select([master], [], [], 0.25)
            if readable:
                try: chunk = os.read(master, 4096)
                except OSError: break
                output.extend(chunk)
                if len(output) > 16384:
                    del output[:-16384]
                if not sent and (b"passphrase" in output.lower() or b"psk" in output.lower()):
                    os.write(master, secret.encode() + b"\n"); sent = True
        if process.poll() is None: process.kill()
        process.wait(timeout=2)
    finally:
        os.close(master)
    if not sent:
        raise HostServicesV3Error("O serviço Wi-Fi não pediu a palavra-passe")
    if process.returncode != 0:
        raise HostServicesV3Error("A palavra-passe foi recusada ou a ligação Wi-Fi falhou")


def wait_for_network(ssid: str, timeout: float = 10) -> dict[str, object]:
    """Return only after iwd confirms the requested network as connected."""
    deadline = time.monotonic() + timeout
    state = network_state()
    while (not state["connected"] or state["network"] != ssid) and time.monotonic() < deadline:
        time.sleep(0.2)
        state = network_state()
    if not state["connected"] or state["network"] != ssid:
        raise HostServicesV3Error("A ligação Wi-Fi não foi confirmada pelo Host")
    return state


def apply(operation: str, payload: dict[str, object]) -> object:
    if operation == "capabilities.get": return CAPABILITIES
    if operation == "snapshot.get": return snapshot()
    if operation == "bluetooth.status": return bluetooth_state()
    if operation == "bluetooth.pair.begin": return pair_begin(str(payload["address"]))
    if operation == "bluetooth.pair.status": return pair_status(str(payload["session_id"]))
    if operation == "bluetooth.pair.respond":
        return pair_respond(str(payload["session_id"]), bool(payload["accept"]),
                            str(payload["pin"]) if payload["pin"] is not None else None)
    if operation.startswith("bluetooth."):
        before_bluetooth = bluetooth_state()
        if before_bluetooth["backend"] != "bluez" or not before_bluetooth["controller_present"]:
            raise UnsupportedError("Host Bluetooth controller is unavailable")
        if operation == "bluetooth.power":
            state = set_bluetooth_power(bool(payload["powered"]))
            result = None
        elif operation == "bluetooth.scan":
            if not before_bluetooth["powered"]: raise ConflictError("Bluetooth controller is powered off")
            result = run(("/usr/bin/bluetoothctl", "--timeout", "8", "scan", "on"), 12)
            run(("/usr/bin/bluetoothctl", "scan", "off"))
        else:
            address = str(payload["address"])
            device = next((item for item in before_bluetooth["devices"] if item["address"] == address), None)
            if device is None or not device["paired"]:
                raise ConflictError("Bluetooth device is not paired")
            verb = {"bluetooth.device.connect": "connect", "bluetooth.device.disconnect": "disconnect",
                    "bluetooth.device.remove": "remove"}.get(operation)
            if verb is None: raise UnsupportedError("Bluetooth operation is unsupported")
            result = run(("/usr/bin/bluetoothctl", verb, address), 25)
        if result is not None and result.returncode: raise HostServicesV3Error("Host Bluetooth transition failed")
        emit("bluetooth.scan_completed" if operation == "bluetooth.scan" else "bluetooth.changed")
        return state if operation == "bluetooth.power" else bluetooth_state()
    if operation == "network.status": return network_state()
    if operation == "radio.status": return radio_state()
    if operation == "network.connectivity-check": return perform_connectivity_check()
    if operation == "network.portal.open": return portal_open()
    before = network_state()
    if operation == "network.scan":
        result = run(("/usr/bin/iwctl", "station", WIFI_INTERFACE, "scan"))
    elif operation == "network.disconnect":
        result = run(("/usr/bin/iwctl", "station", WIFI_INTERFACE, "disconnect"), 20)
    elif operation == "network.forget":
        if payload["ssid"] not in {item["ssid"] for item in before["networks"] if item["known"]}:
            raise ConflictError("network is not known by the Host")
        result = run(("/usr/bin/iwctl", "known-networks", str(payload["ssid"]), "forget"), 20)
    elif operation == "network.connect":
        target = next((item for item in before["networks"] if item["ssid"] == payload["ssid"]), None)
        if target is None: raise ConflictError("network is not present in the current Host scan")
        if target["security"] == "enterprise": raise UnsupportedError("enterprise Wi-Fi is not supported by v3")
        credential = payload["credential"]
        if target["known"] or target["security"] == "open":
            if credential is not None: raise ConflictError("credential was supplied for a known or open network")
            result = run(("/usr/bin/iwctl", "station", WIFI_INTERFACE, "connect", str(payload["ssid"])), 25)
        else:
            if credential is None: raise ConflictError("this protected network requires a passphrase")
            secret_connect(str(payload["ssid"]), str(credential["value"])); result = None
    else:
        raise UnsupportedError("operation is unsupported")
    if result is not None and result.returncode: raise HostServicesV3Error("Host network transition failed")
    if operation == "network.scan": emit("network.scan_completed")
    if operation == "network.connect":
        wait_for_network(str(payload["ssid"]))
        perform_connectivity_check()
    return network_state()


def emit(event_type: str) -> None:
    global _LAST_EVENT, _SEQUENCE
    if event_type not in CAPABILITIES["events"]: raise HostServicesV3Error("event type differs")
    with _LOCK: _SEQUENCE += 1; _LAST_EVENT = event_type


def receive(connection: socket.socket) -> bytes:
    data = bytearray()
    while b"\n" not in data and len(data) <= MAX_MESSAGE_BYTES:
        chunk = connection.recv(min(4096, MAX_MESSAGE_BYTES + 1 - len(data)))
        if not chunk: break
        data.extend(chunk)
    if not data or len(data) > MAX_MESSAGE_BYTES or not data.endswith(b"\n") or b"\n" in data[:-1]:
        raise HostServicesV3Error("request framing differs")
    return bytes(data)


def event_result(after: int, timeout_ms: int) -> dict[str, object]:
    global _LAST_DIGEST, _LAST_EVENT, _SEQUENCE
    deadline = time.monotonic() + timeout_ms / 1000
    while True:
        state = network_state(); digest = hashlib.sha256(json.dumps(state, sort_keys=True).encode()).hexdigest()
        with _LOCK:
            if not _LAST_DIGEST: _LAST_DIGEST = digest
            elif digest != _LAST_DIGEST:
                _LAST_DIGEST = digest; _SEQUENCE += 1; _LAST_EVENT = "network.changed"
            sequence = _SEQUENCE; event_type = _LAST_EVENT
        if sequence > after or time.monotonic() >= deadline:
            return {"events": ([{"sequence": sequence, "type": event_type}] if sequence > after else []),
                    "next": sequence, "snapshot": state if sequence > after else None}
        time.sleep(0.5)


def respond(connection: socket.socket) -> None:
    request_id = "rejected"
    try:
        credentials = struct.unpack("3i", connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
        authorize_shared_service_peer(HostServicesPeer(*credentials))
        request_id, operation, payload = parse_request(receive(connection))
        if operation in {"bluetooth.device.connect", "bluetooth.device.disconnect", "bluetooth.device.remove",
                         "bluetooth.pair.begin", "bluetooth.pair.respond", "bluetooth.power", "bluetooth.scan",
                         "network.connect", "network.disconnect", "network.forget", "network.scan"}:
            if not _MUTATION_LOCK.acquire(blocking=False): raise ConflictError("another Host network transition is active")
            try: result = apply(operation, payload)
            finally: _MUTATION_LOCK.release()
        else:
            result = event_result(int(payload["after"]), int(payload["timeout_ms"])) \
                if operation == "events.subscribe" else apply(operation, payload)
        connection.sendall(response_bytes(request_id, result))
        print(f"APX Host services v3 accepted operation={operation} request_id={request_id} peer_pid={credentials[0]}",
              file=sys.stderr, flush=True)
    except Exception as error:
        code = getattr(error, "code", "request_rejected")
        try: connection.sendall(error_bytes(request_id, code, str(error)[:256] or "request rejected"))
        except (BrokenPipeError, ValueError): pass
        print(f"APX Host services v3 rejected {type(error).__name__} code={code}", file=sys.stderr, flush=True)


def worker(connection: socket.socket) -> None:
    try:
        connection.settimeout(35)
        with connection: respond(connection)
    finally: _CLIENTS.release()


def connectivity_monitor() -> None:
    while True:
        try:
            current = network_state()
            interval = 60 if current.get("connectivity") == "portal" else 300
            if current.get("connected"):
                perform_connectivity_check()
        except (HostServicesV3Error, OSError, subprocess.SubprocessError, ValueError):
            interval = 60
        time.sleep(interval)


def serve() -> None:
    if os.geteuid() != 0 or Path("/etc/hostname").read_text().strip() != "apx-host":
        raise HostServicesV3Error("endpoint requires APX Host root")
    SOCKET.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
    if SOCKET.exists() or SOCKET.is_symlink():
        metadata = SOCKET.lstat()
        # The exact active-Environment launcher leases this root-directory
        # socket by changing its owner. Only root can replace entries in
        # /run/apx, so a real socket is safe to retire on daemon restart;
        # symlinks and every other file type remain rejected.
        if not stat.S_ISSOCK(metadata.st_mode): raise HostServicesV3Error("existing endpoint is unsafe")
        SOCKET.unlink()
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
        server.bind(str(SOCKET)); os.chmod(SOCKET, 0o600); server.listen(MAX_CLIENTS)
        threading.Thread(target=connectivity_monitor, daemon=True).start()
        while True:
            connection, _ = server.accept()
            if not _CLIENTS.acquire(blocking=False): connection.close(); continue
            threading.Thread(target=worker, args=(connection,), daemon=True).start()


def main() -> int:
    parser = argparse.ArgumentParser(); modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--serve", action="store_true"); modes.add_argument("--self-test", action="store_true")
    arguments = parser.parse_args()
    if arguments.self_test: print(json.dumps(snapshot(), ensure_ascii=False, sort_keys=True)); return 0
    serve(); return 0


if __name__ == "__main__":
    try: raise SystemExit(main())
    except (HostServicesV3Error, OSError, subprocess.SubprocessError, ValueError) as error:
        print(f"APX Host services v3 refused: {error}", file=sys.stderr); raise SystemExit(2)
