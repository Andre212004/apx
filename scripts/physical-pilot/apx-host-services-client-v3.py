#!/usr/bin/env python3
"""Unprivileged APX Host shared-services v3 client."""

import argparse
import getpass
import json
import socket
import sys

sys.path.insert(0, "/usr/lib/apx")
from apx_host_services_v3_contract import MAX_MESSAGE_BYTES, parse_response, request_bytes  # noqa: E402

SOCKET = "/run/apx/host-services-v3.sock"


def exchange(operation: str, payload: dict[str, object]) -> dict[str, object]:
    request = request_bytes(operation, payload)
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
        connection.settimeout(35); connection.connect(SOCKET); connection.sendall(request)
        data = bytearray()
        while b"\n" not in data and len(data) <= MAX_MESSAGE_BYTES:
            chunk = connection.recv(min(4096, MAX_MESSAGE_BYTES + 1 - len(data)))
            if not chunk: break
            data.extend(chunk)
    response = parse_response(bytes(data))
    if response["error"] is not None:
        raise RuntimeError(f"{response['error']['code']}: {response['error']['message']}")
    return response["result"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=("bluetooth-connect", "bluetooth-disconnect", "bluetooth-pair",
                                               "bluetooth-pair-respond", "bluetooth-pair-status", "bluetooth-power",
                                               "bluetooth-remove", "bluetooth-scan", "bluetooth-status",
                                               "capabilities", "events", "snapshot", "wifi-connect",
                                               "wifi-connectivity-check", "wifi-disconnect", "wifi-forget",
                                               "wifi-portal-open", "wifi-scan", "wifi-status"))
    parser.add_argument("target", nargs="?")
    parser.add_argument("--credential-stdin", action="store_true",
                        help="read one passphrase from stdin; never pass it as an argument")
    parser.add_argument("--accept", choices=("yes", "no"))
    arguments = parser.parse_args()
    mapping = {"bluetooth-connect": "bluetooth.device.connect",
               "bluetooth-disconnect": "bluetooth.device.disconnect", "bluetooth-pair": "bluetooth.pair.begin",
               "bluetooth-pair-respond": "bluetooth.pair.respond", "bluetooth-pair-status": "bluetooth.pair.status",
               "bluetooth-power": "bluetooth.power", "bluetooth-remove": "bluetooth.device.remove",
               "bluetooth-scan": "bluetooth.scan", "bluetooth-status": "bluetooth.status",
               "capabilities": "capabilities.get", "events": "events.subscribe", "snapshot": "snapshot.get",
               "wifi-connect": "network.connect", "wifi-disconnect": "network.disconnect",
               "wifi-connectivity-check": "network.connectivity-check", "wifi-forget": "network.forget",
               "wifi-portal-open": "network.portal.open", "wifi-scan": "network.scan",
               "wifi-status": "network.status"}
    payload: dict[str, object] = {}
    if arguments.operation in {"bluetooth-connect", "bluetooth-disconnect", "bluetooth-pair", "bluetooth-remove"}:
        if arguments.target is None: parser.error("this operation requires a Bluetooth address")
        payload["address"] = arguments.target
    if arguments.operation == "bluetooth-power":
        if arguments.target not in {"on", "off"}: parser.error("Bluetooth power requires on or off")
        payload["powered"] = arguments.target == "on"
    if arguments.operation == "bluetooth-pair-status":
        if arguments.target is None: parser.error("pair status requires a session id")
        payload["session_id"] = arguments.target
    if arguments.operation == "bluetooth-pair-respond":
        if arguments.target is None or arguments.accept is None:
            parser.error("pair response requires a session id and --accept")
        pin = None
        if arguments.credential_stdin:
            pin = sys.stdin.readline().rstrip("\n") if not sys.stdin.isatty() else getpass.getpass("")
        payload = {"accept": arguments.accept == "yes", "pin": pin, "session_id": arguments.target}
    if arguments.operation in {"wifi-connect", "wifi-forget"}:
        if arguments.target is None: parser.error("this operation requires an SSID")
        payload["ssid"] = arguments.target
    if arguments.operation == "wifi-connect":
        credential = None
        if arguments.credential_stdin:
            secret = sys.stdin.readline().rstrip("\n") if not sys.stdin.isatty() else getpass.getpass("")
            credential = {"kind": "passphrase", "value": secret}
        payload["credential"] = credential
    if arguments.operation == "events": payload = {"after": 0, "timeout_ms": 25000}
    print(json.dumps(exchange(mapping[arguments.operation], payload), ensure_ascii=False,
                     sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    try: raise SystemExit(main())
    except (OSError, RuntimeError, ValueError) as error:
        print(f"APX Host services v3 unavailable: {error}", file=sys.stderr); raise SystemExit(3)
