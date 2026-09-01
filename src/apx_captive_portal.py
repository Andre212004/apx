"""Bounded captive-portal detection for the APX Host network authority."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import http.client
import json
import socket
import ssl
from typing import Callable
from urllib.parse import urljoin, urlsplit


PROBE_URL = "http://ping.archlinux.org/nm-check.txt"
PROBE_BODY = b"NetworkManager is online\n"
MAX_BODY = 65536
MAX_URL = 2048
MAX_REDIRECTS = 3
TIMEOUT_SECONDS = 6


class CaptivePortalError(RuntimeError):
    pass


@dataclass(frozen=True)
class HttpResult:
    status: int
    headers: dict[str, str]
    body: bytes
    url: str


def checked_at() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def validated_url(value: object, *, https_only: bool = False) -> str:
    if type(value) is not str or not value or len(value) > MAX_URL or any(ord(c) < 32 for c in value):
        raise CaptivePortalError("portal URL is invalid")
    parsed = urlsplit(value)
    allowed = {"https"} if https_only else {"http", "https"}
    if parsed.scheme.lower() not in allowed or not parsed.hostname or parsed.username is not None \
            or parsed.password is not None:
        raise CaptivePortalError("portal URL is invalid")
    try:
        port = parsed.port
    except ValueError as error:
        raise CaptivePortalError("portal URL port is invalid") from error
    if port is not None and not 1 <= port <= 65535:
        raise CaptivePortalError("portal URL port is invalid")
    return value


def portal_state(*, required: bool = False, url: str | None = None, source: str | None = None,
                 can_extend_session: bool = False, seconds_remaining: int | None = None,
                 bytes_remaining: int | None = None) -> dict[str, object]:
    return {"required": required, "url": url, "source": source,
            "can_extend_session": can_extend_session,
            "seconds_remaining": seconds_remaining, "bytes_remaining": bytes_remaining}


def result(connectivity: str, *, portal: dict[str, object] | None = None) -> dict[str, object]:
    return {"connectivity": connectivity, "connectivity_checked_at": checked_at(),
            "portal": portal or portal_state()}


def unknown() -> dict[str, object]:
    return {"connectivity": "unknown", "connectivity_checked_at": None, "portal": portal_state()}


def _bound_socket(host: str, port: int, interface: str, timeout: int) -> socket.socket:
    last_error: OSError | None = None
    for family, socktype, protocol, _canonical, address in socket.getaddrinfo(host, port, type=socket.SOCK_STREAM):
        candidate = socket.socket(family, socktype, protocol)
        try:
            candidate.settimeout(timeout)
            candidate.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, interface.encode() + b"\0")
            candidate.connect(address)
            return candidate
        except OSError as error:
            last_error = error
            candidate.close()
    raise last_error or CaptivePortalError("connectivity endpoint is unavailable")


def request_once(url: str, interface: str, headers: dict[str, str], timeout: int = TIMEOUT_SECONDS) -> HttpResult:
    value = validated_url(url)
    parsed = urlsplit(value)
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    connection: http.client.HTTPConnection
    raw = _bound_socket(str(parsed.hostname), port, interface, timeout)
    if parsed.scheme == "https":
        context = ssl.create_default_context()
        wrapped = context.wrap_socket(raw, server_hostname=str(parsed.hostname))
        connection = http.client.HTTPSConnection(str(parsed.hostname), port, timeout=timeout, context=context)
        connection.sock = wrapped
    else:
        connection = http.client.HTTPConnection(str(parsed.hostname), port, timeout=timeout)
        connection.sock = raw
    path = parsed.path or "/"
    if parsed.query:
        path += "?" + parsed.query
    try:
        connection.request("GET", path, headers={**headers, "Connection": "close"})
        response = connection.getresponse()
        body = response.read(MAX_BODY + 1)
        if len(body) > MAX_BODY:
            raise CaptivePortalError("connectivity response is oversized")
        response_headers = {name.lower(): value for name, value in response.getheaders()}
        return HttpResult(response.status, response_headers, body, value)
    finally:
        connection.close()


def request(url: str, interface: str, headers: dict[str, str], timeout: int = TIMEOUT_SECONDS,
            *, redirects: int = MAX_REDIRECTS) -> HttpResult:
    current = validated_url(url)
    for attempt in range(redirects + 1):
        response = request_once(current, interface, headers, timeout)
        location = response.headers.get("location")
        if response.status not in {301, 302, 303, 307, 308} or location is None:
            return response
        if attempt == redirects:
            raise CaptivePortalError("too many connectivity redirects")
        current = validated_url(urljoin(current, location))
    raise CaptivePortalError("connectivity request failed")


def capport_uri_from_networkctl(value: object) -> str | None:
    if type(value) is not dict:
        return None
    # networkctl exposes DHCPv6/IPv6 Router Advertisement CAPPORT at link
    # level; the exact key varies between systemd-networkd releases.
    for key in ("CaptivePortal", "CaptivePortalURL", "CAPTIVE_PORTAL"):
        if key not in value:
            continue
        try:
            return validated_url(value[key], https_only=True)
        except CaptivePortalError:
            return None
    try:
        options = value["DHCPv4Client"]["Lease"]["Message"]["options"]
    except (KeyError, TypeError):
        return None
    if type(options) is not list:
        return None
    for option in options:
        if type(option) is not dict or option.get("tag") != 114 or type(option.get("data")) is not str:
            continue
        try:
            candidate = bytes.fromhex(option["data"]).decode("utf-8")
            return validated_url(candidate, https_only=True)
        except (UnicodeDecodeError, ValueError, CaptivePortalError):
            return None
    return None


def _nonnegative_integer(value: object) -> int | None:
    return value if type(value) is int and value >= 0 else None


def _capport(api_uri: str, interface: str, transport: Callable[..., HttpResult]) \
        -> tuple[bool, dict[str, object]] | None:
    response = transport(api_uri, interface, {"Accept": "application/captive+json",
                                              "User-Agent": "APX-CAPPORT/1"}, TIMEOUT_SECONDS)
    if response.status != 200 or response.headers.get("content-type", "").split(";", 1)[0].strip() \
            != "application/captive+json":
        return None
    value = json.loads(response.body)
    if type(value) is not dict or type(value.get("captive")) is not bool:
        return None
    portal_url = None
    if "user-portal-url" in value:
        try:
            portal_url = validated_url(value["user-portal-url"], https_only=True)
        except CaptivePortalError:
            return None
    state = portal_state(required=value["captive"], url=portal_url,
                         source="capport" if portal_url else None,
                         can_extend_session=value.get("can-extend-session") is True,
                         seconds_remaining=_nonnegative_integer(value.get("seconds-remaining")),
                         bytes_remaining=_nonnegative_integer(value.get("bytes-remaining")))
    return value["captive"], state


def check(*, connected: bool, has_default_route: bool, interface: str,
          capport_uri: str | None = None, transport: Callable[..., HttpResult] = request) -> dict[str, object]:
    if not connected or not has_default_route:
        return result("none")
    session = portal_state()
    if capport_uri is not None:
        try:
            api = _capport(validated_url(capport_uri, https_only=True), interface, transport)
            if api is not None:
                captive, session = api
                if captive:
                    if session["url"] is None:
                        session = portal_state(required=True, url=PROBE_URL, source="fallback")
                    return result("portal", portal=session)
        except (CaptivePortalError, json.JSONDecodeError, OSError, TimeoutError):
            pass
    try:
        response = transport(PROBE_URL, interface, {"Accept": "text/plain",
                                                    "User-Agent": "APX-Connectivity/1"}, TIMEOUT_SECONDS,
                             redirects=0)
        if response.status == 200 and response.body == PROBE_BODY:
            return result("full", portal=session)
        location = response.headers.get("location")
        if response.status in {301, 302, 303, 307, 308} and location:
            portal_url = validated_url(urljoin(PROBE_URL, location))
            return result("portal", portal=portal_state(required=True, url=portal_url, source="redirect"))
        content_type = response.headers.get("content-type", "").lower()
        looks_like_html = "text/html" in content_type or b"<html" in response.body[:1024].lower()
        if response.status == 511 or (response.status == 200 and looks_like_html):
            return result("portal", portal=portal_state(required=True, url=PROBE_URL, source="fallback"))
        return result("limited", portal=session)
    except (CaptivePortalError, OSError, TimeoutError, socket.timeout):
        return result("limited", portal=session)
