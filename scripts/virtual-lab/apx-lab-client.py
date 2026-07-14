#!/usr/bin/env python3
"""Unprivileged APX management client installed in the headless Hub."""

from __future__ import annotations

import argparse
import json
import socket
import sys


SOCKET = "/run/apx/executor.sock"


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="apx")
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser("status")
    commands.add_parser("recovery-status")
    environment = commands.add_parser("environment")
    sub = environment.add_subparsers(dest="environment_command", required=True)
    sub.add_parser("list")
    create_plan = sub.add_parser("create-plan")
    create_plan.add_argument("name")
    create_plan.add_argument("--role", required=True, choices=("hub", "development", "minimal"))
    create = sub.add_parser("create")
    create.add_argument("--plan", required=True)
    create.add_argument("--approve", required=True)
    for command in ("start", "stop", "snapshot", "archive"):
        item = sub.add_parser(command)
        item.add_argument("name")
    destroy_plan = sub.add_parser("destroy-plan")
    destroy_plan.add_argument("name")
    destroy = sub.add_parser("destroy")
    destroy.add_argument("--plan", required=True)
    destroy.add_argument("--approve", required=True)
    restore = sub.add_parser("restore")
    restore.add_argument("--archive", required=True)
    restore.add_argument("--name", required=True)
    restore.add_argument("--approve", required=True)
    return root


def request(arguments: argparse.Namespace) -> dict[str, object]:
    operation = arguments.command if arguments.command != "environment" else arguments.environment_command
    result: dict[str, object] = {"schema": 1, "operation": operation}
    for field in ("name", "role", "plan", "approve", "archive"):
        if hasattr(arguments, field):
            result["approval" if field == "approve" else field] = getattr(arguments, field)
    return result


def main() -> int:
    payload = (json.dumps(request(parser().parse_args()), sort_keys=True, separators=(",", ":")) + "\n").encode()
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
            connection.settimeout(300)
            connection.connect(SOCKET)
            connection.sendall(payload)
            data = b""
            while b"\n" not in data:
                chunk = connection.recv(4096)
                if not chunk:
                    break
                data += chunk
        response = json.loads(data)
    except (OSError, json.JSONDecodeError) as error:
        print(f"APX unavailable: {error}", file=sys.stderr)
        return 3
    if response.get("ok") is True:
        sys.stdout.write(str(response.get("output", "")))
        return 0
    print(f"APX refused: {response.get('error', 'unknown executor error')}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
