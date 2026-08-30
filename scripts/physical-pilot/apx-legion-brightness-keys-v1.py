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
AT_NAME = "AT Raw Set 2 keyboard"
EV_KEY = 1
KEY_F1 = 59
KEY_F2 = 60
KEY_F3 = 61
KEY_F5 = 63
KEY_F6 = 64
KEY_F4 = 62
KEY_F7 = 65
KEY_F8 = 66
KEY_F9 = 67
KEY_F10 = 68
KEY_F11 = 87
KEY_F12 = 88
KEY_PRINT = 99
KEY_MUTE = 113
KEY_VOLUMEDOWN = 114
KEY_VOLUMEUP = 115
KEY_BRIGHTNESSDOWN = 224
KEY_BRIGHTNESSUP = 225
KEY_MICMUTE = 248
EVENT = struct.Struct("llHHI")
LAPTOP_ACTION = "/home/apx/.local/bin/apx-laptop-action-v1"


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
                # The physical Fn row is mirrored as raw F4--F12 only by the
                # exact internal ITE interface. Plain F keys arrive through the
                # AT interface, so this does not consume application F4--F12.
                if name == ITE_NAME and code in (KEY_F1, KEY_MUTE):
                    call_shell("volumeMute")
                elif name == ITE_NAME and code in (KEY_F2, KEY_VOLUMEDOWN):
                    call_shell("volumeDown")
                elif name == ITE_NAME and code in (KEY_F3, KEY_VOLUMEUP):
                    call_shell("volumeUp")
                elif name == ITE_NAME and code in (KEY_F4, KEY_MICMUTE):
                    call_shell("microphoneMute")
                elif name == ITE_NAME and code == KEY_F5:
                    call_shell("brightnessDown")
                elif name == ITE_NAME and code == KEY_F6:
                    call_shell("brightnessUp")
                elif name == ITE_NAME and code == KEY_F7:
                    launch_action("display-cycle")
                elif name == ITE_NAME and code == KEY_F8:
                    launch_action("airplane-status")
                elif name == ITE_NAME and code == KEY_F9:
                    launch_action("apps")
                elif name == ITE_NAME and code == KEY_F10:
                    call_shell("hotkeyTouchpadToggled")
                elif name == ITE_NAME and code == KEY_F11:
                    launch_action("overview")
                elif name == ITE_NAME and code == KEY_F12:
                    launch_action("calculator")
                elif code == KEY_BRIGHTNESSDOWN:
                    call_shell("brightnessDown")
                elif code == KEY_BRIGHTNESSUP:
                    call_shell("brightnessUp")
                elif name == AT_NAME and code == KEY_PRINT:
                    launch_action("screenshot")


if __name__ == "__main__":
    raise SystemExit(main())
