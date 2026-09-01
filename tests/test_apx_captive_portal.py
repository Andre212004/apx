import socket
import unittest

from src import apx_captive_portal as subject


def response(status=200, body=b"", headers=None, url=subject.PROBE_URL):
    return subject.HttpResult(status, headers or {}, body, url)


class Transport:
    def __init__(self, *values):
        self.values = list(values)
        self.calls = []

    def __call__(self, url, interface, headers, timeout, **options):
        self.calls.append((url, interface, headers, timeout, options))
        value = self.values.pop(0)
        if isinstance(value, BaseException):
            raise value
        return value


class CaptivePortalTests(unittest.TestCase):
    def test_normal_network_is_full(self):
        transport = Transport(response(200, subject.PROBE_BODY, {"content-type": "text/plain"}))
        value = subject.check(connected=True, has_default_route=True, interface="wlan0", transport=transport)
        self.assertEqual(value["connectivity"], "full")
        self.assertFalse(value["portal"]["required"])

    def test_capport_portal_uses_validated_tls_user_url(self):
        body = b'{"captive":true,"user-portal-url":"https://login.example/session?token=x"}'
        transport = Transport(response(200, body, {"content-type": "application/captive+json; charset=utf-8"},
                                      "https://api.example/state"))
        value = subject.check(connected=True, has_default_route=True, interface="wlan0",
                              capport_uri="https://api.example/state", transport=transport)
        self.assertEqual(value["connectivity"], "portal")
        self.assertEqual(value["portal"]["source"], "capport")
        self.assertEqual(value["portal"]["url"], "https://login.example/session?token=x")

    def test_redirect_portal_does_not_follow_during_probe(self):
        transport = Transport(response(302, b"", {"location": "http://portal.local/login?token=x"}))
        value = subject.check(connected=True, has_default_route=True, interface="wlan0", transport=transport)
        self.assertEqual(value["connectivity"], "portal")
        self.assertEqual(value["portal"]["source"], "redirect")
        self.assertEqual(transport.calls[0][-1], {"redirects": 0})

    def test_html_interception_uses_safe_http_fallback(self):
        transport = Transport(response(200, b"<html>login</html>", {"content-type": "text/html"}))
        value = subject.check(connected=True, has_default_route=True, interface="wlan0", transport=transport)
        self.assertEqual(value["connectivity"], "portal")
        self.assertEqual(value["portal"]["url"], subject.PROBE_URL)
        self.assertEqual(value["portal"]["source"], "fallback")

    def test_timeout_is_limited_not_portal(self):
        value = subject.check(connected=True, has_default_route=True, interface="wlan0",
                              transport=Transport(socket.timeout("private detail")))
        self.assertEqual(value["connectivity"], "limited")
        self.assertFalse(value["portal"]["required"])

    def test_no_route_is_none_without_request(self):
        transport = Transport()
        value = subject.check(connected=True, has_default_route=False, interface="wlan0", transport=transport)
        self.assertEqual(value["connectivity"], "none")
        self.assertEqual(transport.calls, [])

    def test_false_positive_non_html_response_is_limited(self):
        transport = Transport(response(200, b"proxy diagnostic", {"content-type": "text/plain"}))
        value = subject.check(connected=True, has_default_route=True, interface="wlan0", transport=transport)
        self.assertEqual(value["connectivity"], "limited")

    def test_capport_false_is_confirmed_by_normal_probe_and_preserves_session_hint(self):
        api = response(200, b'{"captive":false,"user-portal-url":"https://portal.example/extend",'
                            b'"can-extend-session":true,"seconds-remaining":120}',
                       {"content-type": "application/captive+json"}, "https://api.example/state")
        transport = Transport(api, response(200, subject.PROBE_BODY, {"content-type": "text/plain"}))
        value = subject.check(connected=True, has_default_route=True, interface="wlan0",
                              capport_uri="https://api.example/state", transport=transport)
        self.assertEqual(value["connectivity"], "full")
        self.assertTrue(value["portal"]["can_extend_session"])
        self.assertEqual(value["portal"]["seconds_remaining"], 120)

    def test_invalid_capport_tls_or_user_url_falls_back_without_disabling_tls(self):
        self.assertIsNone(subject.capport_uri_from_networkctl({"DHCPv4Client": {"Lease": {"Message": {
            "options": [{"tag": 114, "data": "687474703a2f2f696e736563757265"}]
        }}}}))
        api = response(200, b'{"captive":true,"user-portal-url":"javascript:alert(1)"}',
                       {"content-type": "application/captive+json"})
        transport = Transport(api, response(200, subject.PROBE_BODY))
        value = subject.check(connected=True, has_default_route=True, interface="wlan0",
                              capport_uri="https://api.example/state", transport=transport)
        self.assertEqual(value["connectivity"], "full")

    def test_dhcp_option_114_is_decoded_only_as_https(self):
        encoded = "https://api.example/client-token".encode().hex()
        value = {"DHCPv4Client": {"Lease": {"Message": {"options": [{"tag": 114, "data": encoded}]}}}}
        self.assertEqual(subject.capport_uri_from_networkctl(value), "https://api.example/client-token")

    def test_networkctl_link_level_capport_covers_dhcpv6_or_ipv6_ra(self):
        value = {"CaptivePortal": "https://api.example/from-ra"}
        self.assertEqual(subject.capport_uri_from_networkctl(value), "https://api.example/from-ra")

    def test_userinfo_controls_and_unknown_schemes_are_rejected(self):
        for value in ("file:///tmp/x", "javascript:alert(1)", "data:text/plain,x",
                      "http://user:secret@example.test/", "https://example.test:99999/"):
            with self.assertRaises(subject.CaptivePortalError):
                subject.validated_url(value)


if __name__ == "__main__":
    unittest.main()
