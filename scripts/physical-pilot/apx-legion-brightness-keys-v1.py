#!/usr/bin/env python3
"""Bridge the exact Lenovo ITE brightness keys into the running Hub shell."""

from __future__ import annotations

import fcntl
import os
from pathlib import Path
import select
import stat
import struct
import subprocess


ITE_NAME = "ITE Tech. Inc. ITE Device(8910) Keyboard"
AT_NAME = "AT Raw Set 2 keyboard"
EV_KEY = 1
KEY_F5 = 63
KEY_F6 = 64
KEY_BRIGHTNESSDOWN = 224
KEY_BRIGHTNESSUP = 225
EVENT = struct.Struct("llHHI")


def _ioc_read(kind: int, number: int, size: int) -> int:
    return (2 << 30) | (size << 16) | (kind << 8) | number


def _device_name(descriptor: int) -> str:
    data = bytearray(256)
    fcntl.ioctl(descriptor, _ioc_read(ord("E"), 0x06, len(data)), data, True)
    return bytes(data).split(b"\0", 1)[0].decode("utf-8", "strict")


def open_exact_keyboards() -> dict[int, str]:
    matches: dict[str, list[int]] = {ITE_NAME: [], AT_NAME: []}
    for node in sorted(Path("/dev/input").glob("event*")):
        metadata = node.stat(follow_symlinks=False)
        if not stat.S_ISCHR(metadata.st_mode) or os.major(metadata.st_rdev) != 13:
            continue
        descriptor = os.open(node, os.O_RDONLY | os.O_NONBLOCK | os.O_CLOEXEC)
        try:
            name = _device_name(descriptor)
            if name in matches:
                matches[name].append(descriptor)
            else:
                os.close(descriptor)
        except Exception:
            os.close(descriptor)
            raise
    if any(len(descriptors) != 1 for descriptors in matches.values()):
        for descriptors in matches.values():
            for descriptor in descriptors:
                os.close(descriptor)
        raise RuntimeError("exact Lenovo internal keyboards are absent or ambiguous")
    return {descriptors[0]: name for name, descriptors in matches.items()}


def call_shell(method: str) -> None:
    subprocess.run(
        ("/usr/bin/quickshell", "-c", "apx", "ipc", "call", "host", method),
        check=False,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=3,
    )


def main() -> int:
    keyboards = open_exact_keyboards()
    poller = select.poll()
    for descriptor in keyboards:
        poller.register(descriptor, select.POLLIN | select.POLLERR | select.POLLHUP)
    while True:
        for descriptor, flags in poller.poll():
            if flags & (select.POLLERR | select.POLLHUP):
                raise RuntimeError("Lenovo ITE brightness keyboard disconnected")
            data = os.read(descriptor, EVENT.size * 32)
            for offset in range(0, len(data) - EVENT.size + 1, EVENT.size):
                _, _, event_type, code, value = EVENT.unpack_from(data, offset)
                if event_type != EV_KEY or value != 1:
                    continue
                is_ite_brightness = keyboards[descriptor] == ITE_NAME \
                    and code in (KEY_BRIGHTNESSDOWN, KEY_BRIGHTNESSUP)
                is_at_function = keyboards[descriptor] == AT_NAME and code in (KEY_F5, KEY_F6)
                if not is_ite_brightness and not is_at_function:
                    continue
                if code in (KEY_BRIGHTNESSDOWN, KEY_F5):
                    call_shell("brightnessDown")
                elif code in (KEY_BRIGHTNESSUP, KEY_F6):
                    call_shell("brightnessUp")


if __name__ == "__main__":
    raise SystemExit(main())
