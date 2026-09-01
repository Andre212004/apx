#!/usr/bin/env python3
"""Unprivileged client for the APX Host two-step system-power service."""

from __future__ import annotations

import argparse
import json
import socket
import sys

sys.path.insert(0, "/usr/lib/apx")
from apx_system_power_contract import MAX_MESSAGE_BYTES, parse_message, request_bytes  # noqa: E402

SOCKET = "/run/apx/system-power-v1.sock"


def exchange(operation: str, payload: dict[str, object]) -> dict[str, object]:
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
        connection.settimeout(10); connection.connect(SOCKET); connection.sendall(request_bytes(operation, payload))
        data = bytearray()
        while b"\n" not in data and len(data) <= MAX_MESSAGE_BYTES:
            chunk = connection.recv(4096)
            if not chunk: break
            data.extend(chunk)
    response = parse_message(bytes(data))
    if not response.get("ok"):
        error = response.get("error", {}); raise RuntimeError(f"{error.get('code')}: {error.get('message')}")
    return response["result"]


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("mode", choices=(
        "capabilities", "status", "prepare", "confirm", "cancel", "hardware-status",
        "platform-set", "gpu-prepare", "gpu-confirm", "gpu-cancel",
        "display-set", "keyboard-cycle",
    ))
    parser.add_argument("action", nargs="?"); parser.add_argument("--token-stdin", action="store_true")
    args = parser.parse_args()
    if args.mode == "capabilities": result = exchange("capabilities.get", {})
    elif args.mode == "status": result = exchange("system.action.status", {})
    elif args.mode == "hardware-status": result = exchange("hardware.profile.status", {})
    elif args.mode == "platform-set":
        if args.action not in {"low-power", "balanced", "performance"}:
            parser.error("platform-set requires low-power, balanced or performance")
        result = exchange("hardware.platform.set", {"profile": args.action})
    elif args.mode == "gpu-prepare":
        if args.action not in {"hybrid", "nvidia"}:
            parser.error("gpu-prepare requires hybrid or nvidia")
        result = exchange("hardware.gpu.prepare", {"profile": args.action})
    elif args.mode == "display-set":
        try: percent = int(args.action or "")
        except ValueError: parser.error("display-set requires an integer from 5 to 100")
        if not 5 <= percent <= 100: parser.error("display-set requires an integer from 5 to 100")
        result = exchange("hardware.display.set", {"percent": percent})
    elif args.mode == "keyboard-cycle":
        if args.action is not None: parser.error("keyboard-cycle takes no argument")
        result = exchange("hardware.keyboard.cycle", {})
    elif args.mode in {"gpu-confirm", "gpu-cancel"}:
        if not args.token_stdin: parser.error("gpu-confirm/gpu-cancel require --token-stdin")
        token = sys.stdin.readline().rstrip("\n")
        result = exchange("hardware.gpu.confirm" if args.mode == "gpu-confirm" else "hardware.gpu.cancel",
                          {"token": token})
    elif args.mode == "prepare":
        if args.action not in {"reboot", "poweroff", "suspend"}:
            parser.error("prepare requires reboot, poweroff or suspend")
        result = exchange(f"system.{args.action}.prepare", {})
    else:
        if not args.token_stdin: parser.error("confirm/cancel require --token-stdin")
        token = sys.stdin.readline().rstrip("\n")
        result = exchange("system.action.confirm" if args.mode == "confirm" else "system.action.cancel", {"token": token})
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":"))); return 0


if __name__ == "__main__":
    try: raise SystemExit(main())
    except (OSError, RuntimeError, ValueError) as error:
        print(f"APX system power unavailable: {error}", file=sys.stderr); raise SystemExit(3)
