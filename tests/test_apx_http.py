from __future__ import annotations

from pathlib import Path
import ssl
import sys
import unittest
from unittest.mock import Mock, patch
import urllib.error
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_http


URI = "https://archive.archlinux.org/repos/2026/07/11/core/os/x86_64/core.db"


class Response:
    def __init__(self, uri=URI):
        self.uri = uri
        self.closed = False

    def geturl(self):
        return self.uri

    def close(self):
        self.closed = True


class ArchiveHTTPTests(unittest.TestCase):
    def test_fixed_request_has_identity_encoding_and_no_secrets(self):
        response = Response()
        opener = Mock()
        opener.open.return_value = response
        self.assertIs(apx_http.open_archive_response(URI, 15, opener=opener), response)
        request = opener.open.call_args.args[0]
        headers = {name.lower(): value for name, value in request.header_items()}
        self.assertEqual(request.get_method(), "GET")
        self.assertEqual(headers["accept-encoding"], "identity")
        self.assertEqual(headers["connection"], "close")
        self.assertEqual(headers["user-agent"], apx_http.USER_AGENT)
        self.assertNotIn("authorization", headers)
        self.assertNotIn("cookie", headers)

    def test_opener_disables_proxy_and_redirect_support(self):
        with patch("urllib.request.getproxies", return_value={"https": "http://proxy.invalid"}):
            opener = apx_http.build_archive_opener()
        self.assertFalse(any(isinstance(handler, urllib.request.ProxyHandler) for handler in opener.handlers))
        redirect = next(handler for handler in opener.handlers if isinstance(handler, apx_http._NoRedirect))
        https = next(handler for handler in opener.handlers if isinstance(handler, urllib.request.HTTPSHandler))
        self.assertIsNone(redirect.redirect_request(None, None, 302, "", {}, "https://example.invalid"))
        self.assertIsNotNone(https)

    def test_default_tls_context_is_required_and_hostname_checked(self):
        contexts = []

        def context():
            value = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            value.check_hostname = True
            value.verify_mode = ssl.CERT_REQUIRED
            contexts.append(value)
            return value

        with patch("apx_http.ssl.create_default_context", side_effect=context):
            apx_http.build_archive_opener()
        self.assertEqual(contexts[0].minimum_version, ssl.TLSVersion.TLSv1_2)
        self.assertTrue(contexts[0].check_hostname)
        self.assertEqual(contexts[0].verify_mode, ssl.CERT_REQUIRED)

    def test_alternate_scheme_host_credentials_port_and_suffixes_block(self):
        variants = (
            URI.replace("https://", "http://"),
            URI.replace("archive.archlinux.org", "example.invalid"),
            URI.replace("archive.archlinux.org", "user@archive.archlinux.org"),
            URI.replace("archive.archlinux.org", "archive.archlinux.org:443"),
            URI + "?x=1",
            URI + "#x",
        )
        for uri in variants:
            with self.subTest(uri=uri):
                with self.assertRaises(apx_http.ArchiveHTTPError):
                    apx_http.open_archive_response(uri, 15, opener=Mock())

    def test_redirected_response_is_closed_and_rejected(self):
        response = Response("https://example.invalid/core.db")
        opener = Mock()
        opener.open.return_value = response
        with self.assertRaisesRegex(apx_http.ArchiveHTTPError, "redirected"):
            apx_http.open_archive_response(URI, 15, opener=opener)
        self.assertTrue(response.closed)

    def test_http_and_network_failures_are_sanitized(self):
        opener = Mock()
        error = urllib.error.HTTPError(URI, 404, "secret server detail", {}, None)
        opener.open.side_effect = error
        with self.assertRaisesRegex(apx_http.ArchiveHTTPError, "status 404"):
            apx_http.open_archive_response(URI, 15, opener=opener)

        opener.open.side_effect = urllib.error.URLError("secret network detail")
        with self.assertRaisesRegex(apx_http.ArchiveHTTPError, "connection failed"):
            apx_http.open_archive_response(URI, 15, opener=opener)

    def test_timeout_is_bounded_and_boolean_is_rejected(self):
        for timeout in (0, -1, 301, True):
            with self.assertRaises(apx_http.ArchiveHTTPError):
                apx_http.open_archive_response(URI, timeout, opener=Mock())


if __name__ == "__main__":
    unittest.main()
