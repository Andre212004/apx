#!/usr/bin/env python3
"""Environment-side client and watcher for APX audio state handoff."""

from __future__ import annotations

import argparse
import json
import re
import socket
import subprocess
import sys
import time

sys.path.insert(0, "/usr/lib/apx")
from apx_audio_state_contract import MAX_MESSAGE_BYTES, parse_message, request_bytes  # noqa: E402

SOCKET = "/run/apx/audio-state-v1.sock"


def exchange(operation: str, payload: dict[str, object]) -> dict[str, object]:
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
        connection.settimeout(5); connection.connect(SOCKET); connection.sendall(request_bytes(operation, payload))
        data = bytearray()
        while b"\n" not in data and len(data) <= MAX_MESSAGE_BYTES:
            chunk = connection.recv(4096)
            if not chunk: break
            data.extend(chunk)
    response = parse_message(bytes(data))
    if not response.get("ok"): raise RuntimeError(str(response.get("error")))
    return response["result"]


def wpctl(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(("/usr/bin/wpctl", *arguments), text=True, capture_output=True, check=False)


def volume(target: str) -> tuple[int, bool]:
    result = wpctl("get-volume", target)
    match = re.search(r"Volume:\s+([0-9.]+)", result.stdout)
    if result.returncode or not match: raise RuntimeError("PipeWire audio endpoint unavailable")
    return min(100, round(float(match.group(1)) * 100)), "MUTED" in result.stdout


def apply(value: dict[str, object]) -> None:
    wpctl("set-volume", "@DEFAULT_AUDIO_SINK@", f"{int(value['output_volume'])}%")
    wpctl("set-mute", "@DEFAULT_AUDIO_SINK@", "1" if value["output_muted"] else "0")
    wpctl("set-volume", "@DEFAULT_AUDIO_SOURCE@", f"{int(value['input_volume'])}%")
    wpctl("set-mute", "@DEFAULT_AUDIO_SOURCE@", "1" if value["input_muted"] else "0")


def microphone_active() -> bool:
    result = wpctl("status")
    # WirePlumber marks nodes with an asterisk; RUNNING is exposed by pw-cli.
    probe = subprocess.run(("/usr/bin/pw-dump",), text=True, capture_output=True, check=False)
    if result.returncode or probe.returncode: return False
    try: values = json.loads(probe.stdout)
    except json.JSONDecodeError: return False
    return any(type(item) is dict and item.get("type") == "PipeWire:Interface:Node"
               and item.get("info", {}).get("state") == "running"
               and item.get("info", {}).get("props", {}).get("media.class") == "Audio/Source"
               for item in values)


def watch() -> None:
    deadline = time.monotonic() + 30
    while True:
        try:
            value = exchange("state.get", {}); break
        except (OSError, RuntimeError, ValueError):
            if time.monotonic() >= deadline: raise
            time.sleep(0.5)
    apply(value); last = None; last_activity = None
    while True:
        output, output_muted = volume("@DEFAULT_AUDIO_SINK@")
        input_level, input_muted = volume("@DEFAULT_AUDIO_SOURCE@")
        current = {"output_volume": output, "output_muted": output_muted,
                   "input_volume": input_level, "input_muted": input_muted,
                   "output_name": None, "input_name": None}
        if current != last: exchange("state.put", current); last = current
        activity = microphone_active()
        if activity != last_activity: exchange("activity.put", {"microphone_active": activity}); last_activity = activity
        time.sleep(1)


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("mode", choices=("get", "watch")); args = parser.parse_args()
    if args.mode == "get": print(json.dumps(exchange("state.get", {}), sort_keys=True)); return 0
    watch(); return 0


if __name__ == "__main__":
    try: raise SystemExit(main())
    except (OSError, RuntimeError, ValueError) as error:
        print(f"APX audio state unavailable: {error}", file=sys.stderr); raise SystemExit(3)
