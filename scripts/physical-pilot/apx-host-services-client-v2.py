#!/usr/bin/env python3
"""Unprivileged typed client for APX Host desktop context menus."""

import argparse
import json
import socket
import sys

sys.path.insert(0, "/usr/lib/apx")
from apx_host_services_v2_contract import MAX_MESSAGE_BYTES, parse_response, request_bytes  # noqa: E402

SOCKET = "/run/apx/host-services-v2.sock"


def exchange(operation: str = "status", target: str | None = None):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
        connection.settimeout(25); connection.connect(SOCKET); connection.sendall(request_bytes(operation, target))
        data = bytearray()
        while b"\n" not in data and len(data) <= MAX_MESSAGE_BYTES:
            chunk = connection.recv(min(4096, MAX_MESSAGE_BYTES + 1 - len(data)))
            if not chunk: break
            data.extend(chunk)
    return parse_response(bytes(data))


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("operation"); parser.add_argument("target", nargs="?")
    arguments = parser.parse_args(); state = exchange(arguments.operation, arguments.target)
    print(json.dumps(state, default=lambda value: value.__dict__, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    try: raise SystemExit(main())
    except (OSError, ValueError) as error:
        print(f"APX Host services v2 unavailable: {error}", file=sys.stderr); raise SystemExit(3)
