#!/usr/bin/env python3
"""Bridge the exact Lenovo ITE function row into the running Hub shell."""

from __future__ import annotations

import fcntl
import os
from pathlib import Path
import select
import stat
import struct
import subprocess


ITE_NAME = "ITE Tech. Inc. ITE Device(8910) Keyboard"
# This is the stable evdev name exposed by the physical i8042 keyboard.  The
# earlier "AT Raw" value came from an intermediate diagnostic path and makes
# the exact-device bridge fail closed during a normal Hub launch.
AT_NAME = "AT Translated Set 2 keyboard"
EV_KEY = 1
KEY_PRINT = 99
KEY_BRIGHTNESSDOWN = 224
KEY_BRIGHTNESSUP = 225
EVENT = struct.Struct("llHHI")
LAPTOP_ACTION = "/home/apx/.local/bin/apx-laptop-action-v1"
LOCK = "/run/apx/session-1000/apx-legion-brightness-keys-v1.lock"


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
    try:
        subprocess.run(
            ("/usr/bin/quickshell", "-c", "apx", "ipc", "call", "host", method),
            check=False,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=3,
        )
    except (OSError, subprocess.SubprocessError):
        # A transient shell restart must not terminate the keyboard bridge.
        return


def launch_action(action: str) -> None:
    try:
        subprocess.Popen(
            (LAPTOP_ACTION, action),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError:
        call_shell("hotkeyFailed")


def main() -> int:
    lock = os.open(LOCK, os.O_RDWR | os.O_CREAT | os.O_CLOEXEC, 0o600)
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        os.close(lock)
        return 0
    keyboards = open_exact_keyboards()
    # Observe the exact ITE interface without grabbing it exclusively. The
    # physical follow-up after enabling an exclusive grab reported a non-responsive
    # keyboard and repeated clean compositor exits, so exclusivity remains
    # disabled until the complete key/modifier stream is proved safe.
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
                name = keyboards[descriptor]
                # ITE is the complete keyboard, not an Fn-only interface. Its
                # raw F1--F12 codes are therefore ordinary application keys.
                # Act only on semantic firmware events that cannot be emitted
                # by a plain F key while fn_lock is off.
                if name == ITE_NAME and code == KEY_BRIGHTNESSDOWN:
                    call_shell("brightnessDown")
                elif name == ITE_NAME and code == KEY_BRIGHTNESSUP:
                    call_shell("brightnessUp")
                elif name == AT_NAME and code == KEY_PRINT:
                    launch_action("screenshot")


if __name__ == "__main__":
    raise SystemExit(main())
