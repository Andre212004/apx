"""Bounded Unix-socket client for the production typed APX executor protocol."""

from __future__ import annotations

from dataclasses import dataclass
import json
import socket
import stat
from pathlib import Path
from typing import Callable

from apx_executor_contract import ExecutorRequest, request_to_json


SOCKET_PATH = "/run/apx/executor-v1.sock"
TIMEOUT_SECONDS = 5.0
MAX_RESPONSE_BYTES = 64 * 1024
RESPONSE_FIELDS = {
    "classification", "issues", "operation_id", "protocol_version",
    "request_digest", "schema_version",
}
CLASSIFICATIONS = ("accepted", "rejected", "incomplete")


class ExecutorClientError(RuntimeError):
    pass


@dataclass(frozen=True)
class ExecutorResponse:
    schema_version: int
    protocol_version: str
    operation_id: str
    classification: str
    issues: tuple[str, ...]
    request_digest: str


Connector = Callable[[str, bytes, float], bytes]


def parse_executor_response(data: bytes, request: ExecutorRequest) -> ExecutorResponse:
    if type(data) is not bytes or not data or len(data) > MAX_RESPONSE_BYTES:
        raise ExecutorClientError("executor response is absent, oversized, or has wrong type")
    if not data.endswith(b"\n") or b"\n" in data[:-1]:
        raise ExecutorClientError("executor response framing is invalid")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ExecutorClientError("executor response is not UTF-8") from error

    def unique_fields(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ExecutorClientError(f"duplicate executor response field: {key}")
            result[key] = value
        return result

    try:
        value = json.loads(text, object_pairs_hook=unique_fields)
    except (json.JSONDecodeError, UnicodeError) as error:
        raise ExecutorClientError("executor response is not valid JSON") from error
    if not isinstance(value, dict) or set(value) != RESPONSE_FIELDS:
        raise ExecutorClientError("executor response fields are missing or unknown")
    if type(value["schema_version"]) is not int or type(value["protocol_version"]) is not str:
        raise ExecutorClientError("executor response version has wrong type")
    if value["schema_version"] != request.schema_version or value["protocol_version"] != request.protocol_version:
        raise ExecutorClientError("executor response protocol differs from request")
    if type(value["operation_id"]) is not str or value["operation_id"] != request.operation_id:
        raise ExecutorClientError("executor response operation does not match request")
    if type(value["classification"]) is not str or value["classification"] not in CLASSIFICATIONS:
        raise ExecutorClientError("executor response classification is unsupported")
    issues = value["issues"]
    if (
        type(issues) is not list or len(issues) > 32
        or any(type(issue) is not str or not issue or len(issue) > 240 or not issue.isprintable() for issue in issues)
    ):
        raise ExecutorClientError("executor response issues are malformed")
    digest = value["request_digest"]
    if type(digest) is not str or len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        raise ExecutorClientError("executor response request digest is malformed")
    if value["classification"] == "accepted" and issues:
        raise ExecutorClientError("accepted executor response cannot contain issues")
    return ExecutorResponse(
        value["schema_version"], value["protocol_version"], value["operation_id"],
        value["classification"], tuple(issues), digest,
    )


def unix_connector(path: str, payload: bytes, timeout: float) -> bytes:
    if path != SOCKET_PATH or timeout != TIMEOUT_SECONDS:
        raise ExecutorClientError("executor transport boundary differs")
    try:
        metadata = Path(path).lstat()
    except OSError as error:
        raise ExecutorClientError("typed executor endpoint is unavailable") from error
    if not stat.S_ISSOCK(metadata.st_mode):
        raise ExecutorClientError("typed executor endpoint is not a Unix socket")
    data = bytearray()
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
            connection.settimeout(timeout)
            connection.connect(path)
            connection.sendall(payload)
            connection.shutdown(socket.SHUT_WR)
            while b"\n" not in data and len(data) <= MAX_RESPONSE_BYTES:
                chunk = connection.recv(4096)
                if not chunk:
                    break
                data.extend(chunk)
    except (OSError, TimeoutError) as error:
        raise ExecutorClientError("typed executor transport failed") from error
    if len(data) > MAX_RESPONSE_BYTES:
        raise ExecutorClientError("executor response exceeds size limit")
    return bytes(data)


def exchange_executor_request(request: ExecutorRequest,
                              connector: Connector = unix_connector) -> ExecutorResponse:
    if type(request) is not ExecutorRequest:
        raise ExecutorClientError("executor request has wrong type")
    payload = request_to_json(request).encode("utf-8")
    response = connector(SOCKET_PATH, payload, TIMEOUT_SECONDS)
    return parse_executor_response(response, request)
