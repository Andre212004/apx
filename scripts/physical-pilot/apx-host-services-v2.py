#!/usr/bin/env python3
"""Authenticated Host backend for APX desktop context menus."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import socket
import stat
import struct
import subprocess
import sys

sys.path.insert(0, "/usr/lib/apx")
from apx_host_services_peer import HostServicesPeer, authorize_shared_service_peer  # noqa: E402
from apx_host_services_v2_contract import (  # noqa: E402
    BluetoothDevice, HostServicesV2State, MAX_MESSAGE_BYTES, parse_request, response_bytes,
)


SOCKET = Path("/run/apx/host-services-v2.sock")
WIFI_INTERFACE = "wlan0"
ANSI = re.compile(r"\x1b\[[0-9;]*m")
MAC_LINE = re.compile(r"^Device\s+((?:[0-9A-F]{2}:){5}[0-9A-F]{2})\s+(.+)$")


class HostServicesV2Error(RuntimeError):
    pass


def run(arguments: tuple[str, ...], timeout: int = 8) -> subprocess.CompletedProcess[str]:
    return subprocess.run(arguments, text=True, capture_output=True, check=False, timeout=timeout,
                          env={"PATH": "/usr/bin", "LC_ALL": "C", "TERM": "dumb", "SYSTEMD_COLORS": "0"})


def wifi_current() -> tuple[bool, str | None]:
    result = run(("/usr/bin/iwctl", "station", WIFI_INTERFACE, "show"))
    clean = ANSI.sub("", result.stdout)
    state = re.search(r"^\s*State\s+(\S+)\s*$", clean, re.MULTILINE)
    name = re.search(r"^\s*Connected network\s+(.+?)\s*$", clean, re.MULTILINE)
    connected = result.returncode == 0 and state is not None and state.group(1) == "connected" and name is not None
    return connected, name.group(1) if connected and name else None


def table_names(arguments: tuple[str, ...], header: str) -> tuple[str, ...]:
    result = run(arguments)
    clean = ANSI.sub("", result.stdout)
    names: set[str] = set()
    in_table = False
    for line in clean.splitlines():
        if header in line:
            in_table = True
            continue
        if not in_table or not line.strip() or set(line.strip()) == {"-"} or "Security" in line:
            continue
        text = line.strip().removeprefix(">").strip()
        match = re.match(r"(.+?)\s{2,}(?:psk|open|8021x)\b", text)
        if match:
            names.add(match.group(1).strip())
    return tuple(sorted(names))


def known_networks() -> tuple[str, ...]:
    return table_names(("/usr/bin/iwctl", "known-networks", "list"), "Known Networks")


def available_networks() -> tuple[str, ...]:
    return table_names(("/usr/bin/iwctl", "station", WIFI_INTERFACE, "get-networks"), "Available networks")


def bluetooth_devices() -> tuple[BluetoothDevice, ...]:
    paired = run(("/usr/bin/bluetoothctl", "devices", "Paired"))
    connected = run(("/usr/bin/bluetoothctl", "devices", "Connected"))
    connected_addresses = {match.group(1) for line in connected.stdout.splitlines() if (match := MAC_LINE.match(line))}
    devices = []
    for line in paired.stdout.splitlines():
        match = MAC_LINE.match(line)
        if match:
            devices.append(BluetoothDevice(match.group(1), match.group(2), match.group(1) in connected_addresses))
    return tuple(sorted(set(devices), key=lambda item: item.address))


def observe() -> HostServicesV2State:
    iwd = Path("/usr/bin/iwctl").is_file()
    connected, name = wifi_current() if iwd else (False, None)
    timedate = run(("/usr/bin/timedatectl", "show", "-p", "Timezone", "-p", "NTP", "-p", "NTPSynchronized"))
    values = dict(line.split("=", 1) for line in timedate.stdout.splitlines() if "=" in line)
    bluez = run(("/usr/bin/systemctl", "is-active", "--quiet", "bluetooth.service")).returncode == 0
    show = run(("/usr/bin/bluetoothctl", "show")) if bluez else None
    powered = show is not None and re.search(r"^\s*Powered:\s+yes\s*$", show.stdout, re.MULTILINE) is not None
    return HostServicesV2State(
        "iwd" if iwd else "unavailable", WIFI_INTERFACE, connected, name,
        known_networks() if iwd else (), available_networks() if iwd else (),
        values.get("Timezone", "Etc/UTC"), values.get("NTP") == "yes", values.get("NTPSynchronized") == "yes",
        "bluez" if bluez else "unavailable", Path("/sys/class/bluetooth/hci0").exists(), powered,
        bluetooth_devices() if bluez else (),
    )


def apply(operation: str, target: str | None) -> HostServicesV2State:
    before = observe()
    if operation == "status":
        return before
    if operation == "wifi-scan":
        result = run(("/usr/bin/iwctl", "station", WIFI_INTERFACE, "scan"))
    elif operation == "wifi-disconnect":
        result = run(("/usr/bin/iwctl", "station", WIFI_INTERFACE, "disconnect"))
    elif operation == "wifi-connect":
        if target not in before.known_networks:
            raise HostServicesV2Error("Wi-Fi target is not a Host-known network")
        result = run(("/usr/bin/iwctl", "station", WIFI_INTERFACE, "connect", target), 20)
    elif operation == "bluetooth-power":
        result = run(("/usr/bin/bluetoothctl", "power", target))
    else:
        paired = {device.address for device in before.bluetooth_devices}
        if target not in paired:
            raise HostServicesV2Error("Bluetooth target is not a paired device")
        verb = "connect" if operation == "bluetooth-connect" else "disconnect"
        result = run(("/usr/bin/bluetoothctl", verb, target), 20)
    if result.returncode:
        raise HostServicesV2Error("Host desktop-service transition failed")
    return observe()


def receive(connection: socket.socket) -> bytes:
    data = bytearray()
    while b"\n" not in data and len(data) <= MAX_MESSAGE_BYTES:
        chunk = connection.recv(min(4096, MAX_MESSAGE_BYTES + 1 - len(data)))
        if not chunk:
            break
        data.extend(chunk)
    if not data or len(data) > MAX_MESSAGE_BYTES or not data.endswith(b"\n") or b"\n" in data[:-1]:
        raise HostServicesV2Error("desktop-service framing differs")
    return bytes(data)


def respond(connection: socket.socket) -> None:
    credentials = struct.unpack("3i", connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
    authorize_shared_service_peer(HostServicesPeer(*credentials))
    operation, target = parse_request(receive(connection))
    connection.sendall(response_bytes(apply(operation, target)))


def serve() -> None:
    if os.geteuid() != 0 or Path("/etc/hostname").read_text().strip() != "apx-host":
        raise HostServicesV2Error("desktop-service endpoint requires APX Host root")
    SOCKET.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
    if SOCKET.exists() or SOCKET.is_symlink():
        metadata = SOCKET.lstat()
        if not stat.S_ISSOCK(metadata.st_mode) or metadata.st_uid != 0:
            raise HostServicesV2Error("existing desktop-service endpoint is unsafe")
        SOCKET.unlink()
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
        server.bind(str(SOCKET)); os.chmod(SOCKET, 0o600); server.listen(8)
        while True:
            connection, _ = server.accept()
            with connection:
                try:
                    respond(connection)
                except Exception as error:
                    print(f"APX Host services v2 rejected {type(error).__name__}: {error}", file=sys.stderr, flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(); modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--serve", action="store_true"); modes.add_argument("--self-test", action="store_true")
    arguments = parser.parse_args()
    if arguments.self_test:
        sys.stdout.buffer.write(response_bytes(observe())); return 0
    serve(); return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (HostServicesV2Error, OSError, subprocess.SubprocessError, ValueError) as error:
        print(f"APX Host services v2 refused: {error}", file=sys.stderr); raise SystemExit(2)
