#!/usr/bin/env python3
"""Narrow unprivileged client for the APX external model-store controller."""

from __future__ import annotations

import argparse
import json
import socket
import stat
import sys
from pathlib import Path


PRIMARY_SOCKET = Path("/run/apx/model-store-control-v1.sock")
LIVE_SOCKET = Path("/home/.apx-host-bridge/model-store-control-v1.sock")
MAX_MESSAGE_BYTES = 4096


def connect() -> socket.socket:
    last_error: OSError | None = None
    for endpoint in (PRIMARY_SOCKET, LIVE_SOCKET):
        try:
            metadata = endpoint.stat()
            if not stat.S_ISSOCK(metadata.st_mode):
                continue
            connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            connection.settimeout(330)
            try:
                connection.connect(str(endpoint))
                return connection
            except OSError as error:
                last_error = error
                connection.close()
        except OSError as error:
            last_error = error
    if last_error is not None:
        raise last_error
    raise FileNotFoundError("no model-store control socket is available")


def exchange(operation: str, payload: dict[str, object]) -> dict[str, object]:
    request = (json.dumps({"operation": operation, "payload": payload}, separators=(",", ":")) + "\n").encode()
    with connect() as connection:
        connection.sendall(request)
        data = bytearray()
        while b"\n" not in data and len(data) <= MAX_MESSAGE_BYTES:
            chunk = connection.recv(1024)
            if not chunk:
                break
            data.extend(chunk)
    if not data.endswith(b"\n") or len(data) > MAX_MESSAGE_BYTES:
        raise RuntimeError("model-store response framing differs")
    response = json.loads(data)
    if not response.get("ok"):
        raise RuntimeError(str(response.get("error")))
    return response["result"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=(
        "status", "model-start", "model-stop", "model-select", "storage-activate", "safe-detach",
    ))
    parser.add_argument("target", nargs="?")
    args = parser.parse_args()
    payload: dict[str, object] = {}
    if args.mode == "model-start":
        payload = {"confirmation": "ATIVAR MODELO"}
    elif args.mode == "model-stop":
        payload = {"confirmation": "DESATIVAR MODELO"}
    elif args.mode == "storage-activate":
        payload = {"confirmation": "MONTAR SSD"}
    elif args.mode == "safe-detach":
        payload = {"confirmation": "REMOVER COM SEGURANÇA"}
    elif args.mode == "model-select":
        if args.target not in {"fast", "balanced", "quality"}:
            parser.error("model-select requires fast, balanced, or quality")
        payload = {"confirmation": "SELECIONAR MODELO", "profile": args.target}
    elif args.target is not None:
        parser.error("this mode does not accept a target")
    print(json.dumps(exchange(args.mode, payload), ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as error:
        print(f"APX model control unavailable: {error}", file=sys.stderr)
        raise SystemExit(3)
