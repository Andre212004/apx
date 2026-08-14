#!/usr/bin/env python3
"""Exact-Hub-button-only interactive Host root console."""

from __future__ import annotations

import argparse
import fcntl
import json
import os
from pathlib import Path
import pty
import select
import signal
import socket
import struct
import sys
import threading
import time
import termios

sys.path.insert(0, "/usr/lib/apx")
from apx_host_console_contract import MAX_MESSAGE_BYTES, PROFILE, parse_message  # noqa: E402
from apx_host_services_peer import HostServicesPeer, authorize_official_hub_peer  # noqa: E402

SOCKET = Path("/run/apx/host-console-v1.sock")
ACTIVE = Path("/run/apx/official-hub-graphical-v1.json")
STATE_DIR = Path("/var/lib/apx/host-console-v1")
AUDIT = STATE_DIR / "audit.jsonl"
OFFICIAL_UNIT = "/system.slice/apx-official-hub-graphical-6f63f9a9.service"
SESSION_LOCK = threading.Lock()
DETACHED_OUTPUT_LIMIT = 1024 * 1024
REPLAY_OUTPUT_LIMIT = 16 * 1024 * 1024
SESSION: "PersistentConsole | None" = None


def audit(event: str, result: str, uid: int | None = None) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    record = {"schema": 1, "profile": PROFILE, "time": int(time.time()),
              "event": event, "result": result, "environment": "hub", "peer_uid": uid}
    descriptor = os.open(AUDIT, os.O_WRONLY | os.O_APPEND | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        os.write(descriptor, (json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n").encode())
    finally:
        os.close(descriptor)


def quickshell_ancestor(peer_pid: int, proc: Path = Path("/proc")) -> int:
    current = peer_pid
    for _ in range(8):
        try:
            status = dict(line.split(":", 1) for line in (proc / str(current) / "status").read_text().splitlines() if ":" in line)
            parent = int(status["PPid"].strip())
            comm = (proc / str(parent) / "comm").read_text().strip()
            executable = os.readlink(proc / str(parent) / "exe")
            cgroups = (proc / str(parent) / "cgroup").read_text().splitlines()
        except (OSError, KeyError, ValueError) as error:
            raise PermissionError("Quickshell ancestry proof is unavailable") from error
        if comm == "quickshell" and executable == "/usr/bin/quickshell" and any(
            OFFICIAL_UNIT in line and line.split(":", 2)[-1].startswith(OFFICIAL_UNIT) for line in cgroups
        ):
            return parent
        if parent <= 1:
            break
        current = parent
    raise PermissionError("Host-console caller is not a Quickshell descendant")


def receive(connection: socket.socket) -> bytes:
    data = bytearray()
    while b"\n" not in data and len(data) <= MAX_MESSAGE_BYTES:
        chunk = connection.recv(min(4096, MAX_MESSAGE_BYTES + 1 - len(data)))
        if not chunk:
            break
        data.extend(chunk)
    return bytes(data)


def response(connection: socket.socket, ok: bool, result: object = None, error: str | None = None) -> None:
    connection.sendall((json.dumps({"schema": 1, "profile": PROFILE, "ok": ok,
                                    "result": result, "error": error}, sort_keys=True,
                                   separators=(",", ":")) + "\n").encode())


class PersistentConsole:
    """One Host-root PTY that may outlive and accept a replacement Hub client."""

    def __init__(self, rows: int, columns: int, peer_uid: int) -> None:
        self.peer_uid = peer_uid
        self.condition = threading.Condition()
        self.output = bytearray()
        # A replacement terminal starts with an empty renderer. Keep a bounded
        # copy of the PTY stream so it can reconstruct the current full-screen
        # TUI instead of receiving only the next few changed cells.
        self.replay = bytearray()
        self.attached = False
        self.alive = True
        self.child, self.master = pty.fork()
        if self.child == 0:
            os.chdir("/root")
            environment = {"HOME": "/root", "USER": "root", "LOGNAME": "root",
                           "SHELL": "/usr/bin/bash", "PATH": "/usr/local/sbin:/usr/local/bin:/usr/bin",
                           # The Host deliberately stays minimal and does not ship
                           # Kitty's terminfo entry.  Advertise the compatible,
                           # ubiquitous profile so clear/tput/full-screen TUIs work.
                           "LANG": "C.UTF-8", "TERM": "xterm-256color",
                           "PS1": "[APX HOST root \\W]# "}
            os.execve("/usr/bin/bash", ("bash", "--noprofile", "--norc", "-i"), environment)
        self.resize(rows, columns)
        threading.Thread(target=self._read_output, daemon=True).start()
        audit("console-open", "opened", peer_uid)

    def resize(self, rows: int, columns: int) -> None:
        fcntl.ioctl(self.master, termios.TIOCSWINSZ,
                    struct.pack("HHHH", rows, columns, 0, 0))
        try:
            foreground = os.tcgetpgrp(self.master)
            if foreground > 0:
                os.killpg(foreground, signal.SIGWINCH)
        except (OSError, ProcessLookupError):
            pass

    def _read_output(self) -> None:
        try:
            while True:
                readable, _, _ = select.select((self.master,), (), (), 1)
                if self.master not in readable:
                    with self.condition:
                        if not self.alive:
                            return
                    continue
                try:
                    data = os.read(self.master, 8192)
                except OSError:
                    break
                if not data:
                    break
                with self.condition:
                    self.output.extend(data)
                    self.replay.extend(data)
                    if len(self.output) > DETACHED_OUTPUT_LIMIT:
                        del self.output[:-DETACHED_OUTPUT_LIMIT]
                    if len(self.replay) > REPLAY_OUTPUT_LIMIT:
                        del self.replay[:-REPLAY_OUTPUT_LIMIT]
                    self.condition.notify_all()
        finally:
            with self.condition:
                self.alive = False
                self.condition.notify_all()
            try:
                os.waitpid(self.child, 0)
            except ChildProcessError:
                pass
            try:
                os.close(self.master)
            except OSError:
                pass
            audit("console-close", "closed", self.peer_uid)

    def claim(self, rows: int, columns: int, reattached: bool = False) -> bytes:
        with self.condition:
            if not self.alive:
                raise RuntimeError("the previous Host console has ended")
            if self.attached:
                raise RuntimeError("another Host console is active")
            self.attached = True
            snapshot = bytes(self.replay) if reattached else b""
            if reattached:
                # The snapshot contains every byte pending during detachment;
                # clear the delivery queue so those bytes are not sent twice.
                self.output.clear()
        self.resize(rows, columns)
        return snapshot

    def release(self, peer_uid: int) -> None:
        with self.condition:
            self.attached = False
            self.condition.notify_all()
        audit("console-detach", "detached", peer_uid)

    def take_output(self) -> bytes:
        with self.condition:
            if not self.output and self.alive:
                self.condition.wait(timeout=0.1)
            data = bytes(self.output)
            self.output.clear()
            return data

    def write_input(self, data: bytes) -> None:
        os.write(self.master, data)


def active_session(rows: int, columns: int, peer_uid: int) -> tuple[PersistentConsole, bool, bytes]:
    global SESSION
    with SESSION_LOCK:
        reattached = SESSION is not None and SESSION.alive
        if not reattached:
            SESSION = PersistentConsole(rows, columns, peer_uid)
        assert SESSION is not None
        snapshot = SESSION.claim(rows, columns, reattached)
        return SESSION, reattached, snapshot


def bridge_root_console(connection: socket.socket, peer: HostServicesPeer,
                        rows: int, columns: int) -> None:
    session, reattached, snapshot = active_session(rows, columns, peer.uid)
    try:
        response(connection, True, {"opened": True, "identity": "HOST root",
                                    "reattached": reattached, "persistent": True})
        if snapshot:
            # Reset the replacement emulator, replay the terminal state, then
            # resize once more so a full-screen foreground app redraws too.
            connection.sendall(b"\x1bc" + snapshot)
            session.resize(rows, columns)
        audit("console-attach", "reattached" if reattached else "opened", peer.uid)
        while True:
            readable, _, _ = select.select((connection,), (), (), 0.1)
            if connection in readable:
                data = connection.recv(8192)
                if not data:
                    break
                session.write_input(data)
            data = session.take_output()
            if data:
                connection.sendall(data)
            with session.condition:
                if not session.alive and not session.output:
                    break
    finally:
        session.release(peer.uid)


def handle(connection: socket.socket) -> None:
    pid, uid, gid = struct.unpack("3i", connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
    peer = HostServicesPeer(pid, uid, gid)
    authorize_official_hub_peer(peer)
    request = parse_message(receive(connection)); operation = request.get("operation"); payload = request.get("payload")
    if type(operation) is not str or type(payload) is not dict:
        raise ValueError("Host-console request differs")
    quickshell_ancestor(pid)
    if operation == "console.open":
        rows, columns = payload.get("rows"), payload.get("columns")
        if type(rows) is not int or type(columns) is not int \
                or not 10 <= rows <= 500 or not 20 <= columns <= 1000:
            raise ValueError("Host-console terminal dimensions differ")
        bridge_root_console(connection, peer, rows, columns)
        return
    if operation == "capabilities.get":
        result = {"root_console": True, "authorization": "official-hub-button",
                  "terminal_size_forwarding": True, "persistent_pty": True,
                  "reattach_on_open": True}
    else:
        raise ValueError("unsupported Host-console operation")
    response(connection, True, result)


def admit_existing_active_session() -> None:
    try:
        value = json.loads(ACTIVE.read_text()); pid = int(value["pid"])
        fields = Path(f"/proc/{pid}/uid_map").read_text().split()
        if len(fields) == 3 and fields[0] == "0" and int(fields[2]) == 65536:
            translated = int(fields[1]) + 1000
            os.chown(SOCKET, translated, translated); os.chmod(SOCKET, 0o660)
    except (OSError, ValueError, KeyError, json.JSONDecodeError):
        pass


def worker(connection: socket.socket) -> None:
    with connection:
        try:
            handle(connection)
        except Exception as error:
            try:
                response(connection, False, error=str(error)[:300])
            except OSError:
                pass
            audit("request", "rejected")


def serve() -> None:
    SOCKET.parent.mkdir(parents=True, exist_ok=True, mode=0o755); SOCKET.unlink(missing_ok=True)
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
        server.bind(str(SOCKET)); os.chmod(SOCKET, 0o600); admit_existing_active_session(); server.listen(8)
        while True:
            connection, _ = server.accept()
            threading.Thread(target=worker, args=(connection,), daemon=True).start()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--serve", action="store_true", required=True)
    serve()
