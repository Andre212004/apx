"""Fixed HTTPS opener for the APX Arch Linux Archive acquisition."""

from __future__ import annotations

import ssl
import urllib.error
import urllib.request
from urllib.parse import urlsplit


ARCHIVE_HOST = "archive.archlinux.org"
USER_AGENT = "APX-base-acquisition/1"


class ArchiveHTTPError(RuntimeError):
    """The fixed archive transport could not be opened safely."""


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def build_archive_opener() -> urllib.request.OpenerDirector:
    """Build a direct TLS opener with no proxies, cookies, or redirects."""
    context = ssl.create_default_context()
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.check_hostname = True
    context.verify_mode = ssl.CERT_REQUIRED
    return urllib.request.build_opener(
        urllib.request.ProxyHandler({}),
        urllib.request.HTTPSHandler(context=context),
        _NoRedirect(),
    )


def open_archive_response(
    uri: str,
    timeout: float,
    *,
    opener: urllib.request.OpenerDirector | None = None,
) -> object:
    parsed = urlsplit(uri)
    if (
        parsed.scheme != "https"
        or parsed.hostname != ARCHIVE_HOST
        or parsed.netloc != ARCHIVE_HOST
        or parsed.username
        or parsed.password
        or parsed.port
        or parsed.query
        or parsed.fragment
    ):
        raise ArchiveHTTPError("archive URI is outside direct HTTPS policy")
    if type(timeout) not in {int, float} or not 0 < timeout <= 300:
        raise ArchiveHTTPError("archive timeout is outside policy")
    request = urllib.request.Request(
        uri,
        headers={
            "Accept": "application/octet-stream",
            "Accept-Encoding": "identity",
            "Connection": "close",
            "User-Agent": USER_AGENT,
        },
        method="GET",
    )
    director = opener or build_archive_opener()
    try:
        response = director.open(request, timeout=float(timeout))
    except urllib.error.HTTPError as error:
        error.close()
        raise ArchiveHTTPError(f"archive returned HTTP status {error.code}") from error
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise ArchiveHTTPError("archive connection failed") from error
    final_uri = getattr(response, "geturl", lambda: None)()
    if final_uri != uri:
        response.close()
        raise ArchiveHTTPError("archive response redirected")
    return response
