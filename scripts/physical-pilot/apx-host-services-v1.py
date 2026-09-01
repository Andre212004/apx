#!/usr/bin/env python3
"""Read-only Host desktop-essential endpoint for the target-bound pilot."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import socket
import stat
import struct
import subprocess
import sys

sys.path.insert(0, "/usr/lib/apx")
from apx_host_services_contract import (  # noqa: E402
    HostServicesState, MAX_MESSAGE_BYTES, parse_request, response_bytes,
)
from apx_host_services_peer import (  # noqa: E402
    HostServicesPeer, authorize_shared_service_peer,
)


SOCKET = Path("/run/apx/host-services-v1.sock")
WIFI_INTERFACE = "wlan0"
ANSI = re.compile(r"\x1b\[[0-9;]*m")


class HostServicesError(RuntimeError):
    pass


def run(arguments: tuple[str, ...]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        arguments, text=True, capture_output=True, check=False, timeout=5,
        env={"PATH": "/usr/bin", "LC_ALL": "C", "TERM": "dumb", "SYSTEMD_COLORS": "0"},
    )


def key_values(text: str) -> dict[str, str]:
    return dict(line.split("=", 1) for line in text.splitlines() if "=" in line)


def wifi_state() -> tuple[str, bool, str | None]:
    if not Path("/usr/bin/iwctl").is_file():
        return "unavailable", False, None
    result = run(("/usr/bin/iwctl", "station", WIFI_INTERFACE, "show"))
    if result.returncode:
        return "iwd", False, None
    clean = ANSI.sub("", result.stdout)
    state_match = re.search(r"^\s*State\s+(\S+)\s*$", clean, re.MULTILINE)
    name_match = re.search(r"^\s*Connected network\s+(.+?)\s*$", clean, re.MULTILINE)
    connected = state_match is not None and state_match.group(1) == "connected" and name_match is not None
    return "iwd", connected, name_match.group(1) if connected else None


def time_state() -> tuple[str, bool, bool]:
    result = run((
        "/usr/bin/timedatectl", "show", "-p", "Timezone", "-p", "NTP", "-p", "NTPSynchronized",
    ))
    values = key_values(result.stdout) if result.returncode == 0 else {}
    timezone = values.get("Timezone", "Etc/UTC")
    return timezone, values.get("NTP") == "yes", values.get("NTPSynchronized") == "yes"


def bluetooth_state() -> tuple[str, bool, bool]:
    controller = Path("/sys/class/bluetooth/hci0").exists()
    service = run(("/usr/bin/systemctl", "is-active", "--quiet", "bluetooth.service"))
    backend = "bluez" if service.returncode == 0 else "unavailable"
    show = run(("/usr/bin/bluetoothctl", "show")) if backend == "bluez" else None
    powered = show is not None and show.returncode == 0 and re.search(
        r"^\s*Powered:\s+yes\s*$", show.stdout, re.MULTILINE,
    ) is not None
    return backend, controller, powered


def observe() -> HostServicesState:
    network_backend, connected, network_name = wifi_state()
    timezone, ntp, synchronized = time_state()
    bluetooth_backend, controller, powered = bluetooth_state()
    return HostServicesState(
        network_backend, WIFI_INTERFACE, connected, network_name,
        timezone, ntp, synchronized, bluetooth_backend, controller, powered,
    )


def apply(operation: str) -> HostServicesState:
    state = observe()
    if operation == "status":
        return state
    if operation != "bluetooth-toggle" or state.bluetooth_backend != "bluez" \
            or not state.bluetooth_controller_present:
        raise HostServicesError("Bluetooth toggle is unavailable")
    target = "off" if state.bluetooth_powered else "on"
    result = run(("/usr/bin/bluetoothctl", "power", target))
    updated = observe()
    if result.returncode or updated.bluetooth_powered != (target == "on"):
        raise HostServicesError("Bluetooth power transition did not complete")
    return updated


def receive(connection: socket.socket) -> bytes:
    data = bytearray()
    while b"\n" not in data and len(data) <= MAX_MESSAGE_BYTES:
        chunk = connection.recv(min(4096, MAX_MESSAGE_BYTES + 1 - len(data)))
        if not chunk:
            break
        data.extend(chunk)
    if not data or len(data) > MAX_MESSAGE_BYTES or not data.endswith(b"\n") or b"\n" in data[:-1]:
        raise HostServicesError("Host-services request framing differs")
    return bytes(data)


def peer(connection: socket.socket) -> HostServicesPeer:
    try:
        return HostServicesPeer(*struct.unpack(
            "3i", connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12)
        ))
    except (OSError, struct.error) as error:
        raise HostServicesError("Host-services peer credentials are unavailable") from error


def respond(connection: socket.socket) -> None:
    authorize_shared_service_peer(peer(connection))
    operation = parse_request(receive(connection))
    connection.sendall(response_bytes(apply(operation)))


def serve() -> None:
    if os.geteuid() != 0 or Path("/etc/hostname").read_text().strip() != "apx-host":
        raise HostServicesError("Host-services endpoint requires the APX Host root identity")
    SOCKET.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
    if SOCKET.exists() or SOCKET.is_symlink():
        metadata = SOCKET.lstat()
        if not stat.S_ISSOCK(metadata.st_mode) or metadata.st_uid != 0:
            raise HostServicesError("existing Host-services endpoint is unsafe")
        SOCKET.unlink()
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
        server.bind(str(SOCKET))
        os.chmod(SOCKET, 0o600)
        server.listen(8)
        while True:
            connection, _ = server.accept()
            with connection:
                try:
                    respond(connection)
                except Exception as error:
                    print(
                        f"APX Host services rejected {type(error).__name__}: {error}",
                        file=sys.stderr, flush=True,
                    )
                    continue


def main() -> int:
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--serve", action="store_true")
    modes.add_argument("--self-test", action="store_true")
    arguments = parser.parse_args()
    if arguments.self_test:
        sys.stdout.buffer.write(response_bytes(observe()))
        return 0
    serve()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (HostServicesError, OSError, subprocess.SubprocessError, ValueError) as error:
        print(f"APX Host services refused: {error}", file=sys.stderr)
        raise SystemExit(2)
