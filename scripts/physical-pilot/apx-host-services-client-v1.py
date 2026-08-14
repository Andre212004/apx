#!/usr/bin/env python3
"""Unprivileged fixed client for the APX Host desktop-essential endpoint."""

from __future__ import annotations

import argparse
import json
import socket
import sys

sys.path.insert(0, "/usr/lib/apx")
from apx_host_services_contract import (  # noqa: E402
    MAX_MESSAGE_BYTES, parse_response, request_bytes,
)


SOCKET = "/run/apx/host-services-v1.sock"


def exchange(operation: str = "status"):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
        connection.settimeout(3)
        connection.connect(SOCKET)
        connection.sendall(request_bytes(operation))
        data = bytearray()
        while b"\n" not in data and len(data) <= MAX_MESSAGE_BYTES:
            chunk = connection.recv(min(4096, MAX_MESSAGE_BYTES + 1 - len(data)))
            if not chunk:
                break
            data.extend(chunk)
    return parse_response(bytes(data))


def waybar(text: str, tooltip: str, css_class: str) -> str:
    return json.dumps(
        {"text": text, "tooltip": tooltip, "class": css_class},
        sort_keys=True, separators=(",", ":"),
    ) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "mode", choices=(
            "json", "waybar-network", "waybar-bluetooth", "waybar-time", "bluetooth-toggle",
        ),
    )
    mode = parser.parse_args().mode
    state = exchange("bluetooth-toggle" if mode == "bluetooth-toggle" else "status")
    if mode == "json":
        print(json.dumps(state.__dict__, sort_keys=True, separators=(",", ":")))
    elif mode == "bluetooth-toggle":
        print(json.dumps(state.__dict__, sort_keys=True, separators=(",", ":")))
    elif mode == "waybar-network":
        label = f"[ WIFI {state.network_name} ]" if state.network_connected else "[ WIFI DOWN ]"
        sys.stdout.write(waybar(label, f"Host {state.network_backend} · {state.network_interface}",
                               "connected" if state.network_connected else "disconnected"))
    elif mode == "waybar-bluetooth":
        if state.bluetooth_backend == "bluez":
            label, css = ("[ BT ON ]", "on") if state.bluetooth_powered else ("[ BT OFF ]", "off")
        else:
            label, css = "[ BT LOCKED ]", "locked"
        sys.stdout.write(waybar(label, "Bluetooth gerido pelo Host APX", css))
    else:
        sync = "SYNC" if state.time_synchronized else "UNSYNC"
        sys.stdout.write(waybar(f"[ TIME {sync} ]", state.timezone,
                               "synchronized" if state.time_synchronized else "unsynchronized"))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as error:
        print(f"APX Host services unavailable: {error}", file=sys.stderr)
        raise SystemExit(3)
