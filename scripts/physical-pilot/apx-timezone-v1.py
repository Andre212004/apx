#!/usr/bin/env python3
"""Host-owned APX timezone selection from explicitly mapped Wi-Fi SSIDs."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import time


CONFIG = Path("/var/lib/apx/timezone-v1/networks.json")
WIFI_INTERFACE = "wlan0"

PROFILE = "apx-timezone-network-map-v1"
SCHEMA = 1

SSID = re.compile(r"^[^\x00-\x1f\x7f]{1,32}$")
TIMEZONE = re.compile(r"^[A-Za-z0-9_+.-]+(?:/[A-Za-z0-9_+.-]+)+$")


class TimezoneError(RuntimeError):
    pass


def run(arguments: tuple[str, ...], timeout: int = 10) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        arguments,
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout,
        env={
            "PATH": "/usr/bin",
            "LC_ALL": "C",
            "TERM": "dumb",
            "SYSTEMD_COLORS": "0",
        },
    )


def read_config(path: Path = CONFIG) -> dict[str, str]:
    flags = os.O_RDONLY | os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW

    try:
        descriptor = os.open(path, flags)
    except OSError as error:
        raise TimezoneError("timezone policy is unavailable") from error

    try:
        metadata = os.fstat(descriptor)

        if not stat.S_ISREG(metadata.st_mode):
            raise TimezoneError("timezone policy is not a regular file")

        if metadata.st_uid != 0 or metadata.st_gid != 0:
            raise TimezoneError("timezone policy ownership differs")

        if stat.S_IMODE(metadata.st_mode) != 0o600:
            raise TimezoneError("timezone policy permissions differ")

        data = os.read(descriptor, 65537)
    finally:
        os.close(descriptor)

    if not data or len(data) > 65536:
        raise TimezoneError("timezone policy size differs")

    try:
        value = json.loads(data)
    except json.JSONDecodeError as error:
        raise TimezoneError("timezone policy is malformed") from error

    if (
        type(value) is not dict
        or value.get("schema") != SCHEMA
        or value.get("profile") != PROFILE
        or type(value.get("networks")) is not dict
    ):
        raise TimezoneError("timezone policy schema differs")

    result: dict[str, str] = {}

    for raw_ssid, raw_timezone in value["networks"].items():
        if (
            type(raw_ssid) is not str
            or SSID.fullmatch(raw_ssid) is None
            or type(raw_timezone) is not str
            or TIMEZONE.fullmatch(raw_timezone) is None
        ):
            raise TimezoneError("timezone policy entry differs")

        result[raw_ssid] = raw_timezone

    return result


def current_ssid() -> str | None:
    result = run(("/usr/bin/iwctl", "station", WIFI_INTERFACE, "show"))

    if result.returncode:
        return None

    for line in result.stdout.splitlines():
        match = re.match(r"^\s*Connected network\s{2,}(.+?)\s*$", line)
        if match:
            value = match.group(1).strip()
            return value if SSID.fullmatch(value) else None

    return None


def available_timezones() -> set[str]:
    result = run(("/usr/bin/timedatectl", "list-timezones"))

    if result.returncode:
        raise TimezoneError("Host timezone catalogue is unavailable")

    return {line.strip() for line in result.stdout.splitlines() if line.strip()}


def current_timezone() -> str:
    result = run(("/usr/bin/timedatectl", "show", "-p", "Timezone", "--value"))

    if result.returncode:
        raise TimezoneError("Host timezone state is unavailable")

    value = result.stdout.strip()

    if TIMEZONE.fullmatch(value) is None:
        raise TimezoneError("Host timezone state differs")

    return value


def reconcile() -> str:
    try:
        policy = read_config()
    except (FileNotFoundError, OSError, TimezoneError):
        return "policy-unavailable"

    ssid = current_ssid()
    if ssid is None:
        return "network-unavailable"

    target = policy.get(ssid)
    if target is None:
        return "network-unmapped"

    try:
        catalogue = available_timezones()
        current = current_timezone()
    except (OSError, subprocess.SubprocessError, TimezoneError):
        return "timezone-state-unavailable"

    if target not in catalogue:
        return "target-invalid"

    if target == current:
        return "already-correct"

    result = run(("/usr/bin/timedatectl", "set-timezone", target))

    if result.returncode:
        return "set-failed"

    try:
        if current_timezone() != target:
            return "verification-failed"
    except (OSError, subprocess.SubprocessError, TimezoneError):
        return "verification-failed"

    return "updated"


def serve(interval: int = 30) -> None:
    previous: str | None = None

    while True:
        try:
            result = reconcile()
        except Exception:
            # Timezone automation must never terminate APX networking or
            # graphical sessions because of malformed or unavailable evidence.
            result = "internal-error"

        if result != previous:
            print(f"APX timezone v1 result={result}", flush=True)
            previous = result

        time.sleep(interval)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--serve", action="store_true")
    args = parser.parse_args()

    if args.once == args.serve:
        parser.error("choose exactly one mode")

    if args.once:
        print(reconcile())
        return 0

    serve()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
