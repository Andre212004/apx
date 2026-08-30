#!/usr/bin/env python3
"""Hub-side client for the direct Host root console button."""

from __future__ import annotations

import argparse
import json
import os
import select
import socket
import sys
import termios
import tty

sys.path.insert(0, "/usr/lib/apx")
from apx_host_console_contract import MAX_MESSAGE_BYTES, parse_message, request_bytes  # noqa: E402

SOCKET = "/run/apx/host-console-v1.sock"


def exchange(operation: str, payload: dict[str, object]) -> dict[str, object]:
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
        connection.connect(SOCKET); connection.sendall(request_bytes(operation, payload))
        data = bytearray()
        while b"\n" not in data and len(data) <= MAX_MESSAGE_BYTES:
            chunk = connection.recv(4096)
            if not chunk: break
            data.extend(chunk)
    value = parse_message(bytes(data))
    if not value.get("ok"):
        raise RuntimeError(str(value.get("error")))
    return value["result"]


def open_console() -> None:
    size = os.get_terminal_size(sys.stdin.fileno())
    ticket = os.environ.pop("APX_HOST_CONSOLE_TICKET", "")
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
        connection.connect(SOCKET)
        connection.sendall(request_bytes("console.open", {
            "rows": size.lines, "columns": size.columns, "ticket": ticket,
        }))
        header = bytearray()
        while b"\n" not in header:
            header.extend(connection.recv(4096))
        line, remainder = bytes(header).split(b"\n", 1)
        value = parse_message(line + b"\n")
        if not value.get("ok"):
            raise RuntimeError(str(value.get("error")))
        result = value["result"]
        print("\n=== APX HOST ROOT :: NOVA SESSÃO ===")
        print("=== Ctrl-D, 'exit' ou fechar a janela termina esta consola ===\n")
        if remainder:
            os.write(sys.stdout.fileno(), remainder)
        old = termios.tcgetattr(sys.stdin.fileno())
        try:
            tty.setraw(sys.stdin.fileno())
            while True:
                readable, _, _ = select.select((sys.stdin, connection), (), ())
                if sys.stdin in readable:
                    data = os.read(sys.stdin.fileno(), 8192)
                    if not data: break
                    connection.sendall(data)
                if connection in readable:
                    data = connection.recv(8192)
                    if not data: break
                    os.write(sys.stdout.fileno(), data)
        finally:
            termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, old)


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("mode", choices=("capabilities", "console")); args = parser.parse_args()
    if args.mode == "console": open_console(); return 0
    print(json.dumps(exchange("capabilities.get", {}), ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    try: raise SystemExit(main())
    except (OSError, RuntimeError, ValueError) as error:
        print(f"APX Host console unavailable: {error}", file=sys.stderr); raise SystemExit(3)
