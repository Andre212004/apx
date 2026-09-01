"""Bounded Unix transport for the typed APX executor endpoint."""

from __future__ import annotations

import os
from pathlib import Path
import socket
import stat
import struct
from typing import Callable

from apx_executor_contract import MAX_REQUEST_BYTES
from apx_executor_endpoint import EndpointAuthorities, handle_executor_request
from apx_executor_peer import PeerCredentials


SOCKET_PATH = Path("/run/apx/executor-v1.sock")
BACKLOG = 8


class ExecutorServerError(RuntimeError):
    pass


AuthorityFactory = Callable[[PeerCredentials], EndpointAuthorities]


def _peer_credentials(connection: socket.socket) -> PeerCredentials:
    try:
        pid, uid, gid = struct.unpack(
            "3i", connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12)
        )
    except (OSError, struct.error) as error:
        raise ExecutorServerError("Unix peer credentials are unavailable") from error
    return PeerCredentials(pid, uid, gid)


def receive_request(connection: socket.socket) -> bytes:
    data = bytearray()
    while b"\n" not in data and len(data) <= MAX_REQUEST_BYTES:
        chunk = connection.recv(min(4096, MAX_REQUEST_BYTES + 1 - len(data)))
        if not chunk:
            break
        data.extend(chunk)
    if not data or len(data) > MAX_REQUEST_BYTES or not data.endswith(b"\n") or b"\n" in data[:-1]:
        raise ExecutorServerError("executor request framing is invalid")
    return bytes(data)


def respond(connection: socket.socket, factory: AuthorityFactory) -> None:
    if not callable(factory):
        raise ExecutorServerError("executor authority factory is unavailable")
    credentials = _peer_credentials(connection)
    authorities = factory(credentials)
    if type(authorities) is not EndpointAuthorities:
        raise ExecutorServerError("executor authority factory returned wrong type")
    response = handle_executor_request(receive_request(connection), authorities)
    connection.sendall(response)


def serve(factory: AuthorityFactory) -> None:
    if os.geteuid() != 0:
        raise ExecutorServerError("executor server requires Host root")
    SOCKET_PATH.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
    if SOCKET_PATH.exists() or SOCKET_PATH.is_symlink():
        metadata = SOCKET_PATH.lstat()
        if not stat.S_ISSOCK(metadata.st_mode) or metadata.st_uid != 0:
            raise ExecutorServerError("existing executor endpoint is unsafe")
        SOCKET_PATH.unlink()
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
        server.bind(str(SOCKET_PATH))
        os.chmod(SOCKET_PATH, 0o666)
        server.listen(BACKLOG)
        while True:
            connection, _ = server.accept()
            with connection:
                try:
                    respond(connection, factory)
                except Exception:
                    # Malformed or unauthenticated peers receive no oracle.
                    continue
