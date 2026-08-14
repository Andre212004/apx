import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import apx_host_services_v3_contract as subject  # noqa: E402


class HostServicesV3ContractTests(unittest.TestCase):
    def test_versioned_requests_and_structured_responses_round_trip(self):
        request_id, operation, payload = subject.parse_request(subject.request_bytes(
            "network.connect", {"ssid": "Rede", "credential": {"kind": "passphrase", "value": "valid-secret"}},
            request_id="env-a-7"))
        self.assertEqual((request_id, operation, payload["ssid"]), ("env-a-7", "network.connect", "Rede"))
        self.assertEqual(subject.parse_response(subject.response_bytes(request_id, {"ok": True}))["result"], {"ok": True})
        error = subject.parse_response(subject.error_bytes(request_id, "unsupported", "not available"))
        self.assertEqual(error["error"]["code"], "unsupported")

    def test_arbitrary_commands_extra_fields_and_bad_ssids_fail_closed(self):
        for operation, payload in (("exec", {}), ("network.connect", {"ssid": "bad\nssid", "credential": None}),
                                   ("network.scan", {"command": "id"}),
                                   ("network.connect", {"ssid": "ok", "credential": {"kind": "pin", "value": "12345678"}})):
            with self.assertRaises(subject.HostServicesV3ContractError):
                subject.request_bytes(operation, payload)
        forged = {"version": 3, "profile": subject.PROFILE, "request_id": "x", "operation": "snapshot.get",
                  "payload": {}, "password": "leak"}
        with self.assertRaises(subject.HostServicesV3ContractError):
            subject.parse_request((json.dumps(forged) + "\n").encode())

    def test_redaction_is_recursive_and_does_not_mutate_input(self):
        value = {"ssid": "Rede", "credential": {"kind": "passphrase", "value": "secret"},
                 "nested": [{"pin": "1234"}]}
        safe = subject.redacted(value)
        self.assertEqual(safe["credential"], "<redacted>")
        self.assertEqual(safe["nested"][0]["pin"], "<redacted>")
        self.assertEqual(value["credential"]["value"], "secret")

    def test_protected_wifi_secret_exists_only_in_socket_body(self):
        data = subject.request_bytes("network.connect", {"ssid": "Rede", "credential": {
            "kind": "passphrase", "value": "secret-123"}}, request_id="x")
        self.assertIn(b"secret-123", data)
        self.assertNotIn("secret-123", repr(subject.redacted(json.loads(data))))

    def test_connectivity_and_portal_operations_accept_no_caller_url(self):
        for operation in ("network.connectivity-check", "network.portal.open"):
            request_id, parsed, payload = subject.parse_request(
                subject.request_bytes(operation, {}, request_id="portal-test"))
            self.assertEqual((request_id, parsed, payload), ("portal-test", operation, {}))
            with self.assertRaises(subject.HostServicesV3ContractError):
                subject.request_bytes(operation, {"url": "https://attacker.invalid/"})

    def test_bluetooth_pairing_is_typed_and_pin_stays_in_the_socket_body(self):
        address = "AA:BB:CC:DD:EE:FF"
        for operation, payload in (
            ("bluetooth.status", {}), ("bluetooth.scan", {}),
            ("bluetooth.power", {"powered": True}),
            ("bluetooth.device.connect", {"address": address}),
            ("bluetooth.device.disconnect", {"address": address}),
            ("bluetooth.device.remove", {"address": address}),
            ("bluetooth.pair.begin", {"address": address}),
            ("bluetooth.pair.status", {"session_id": "a" * 32}),
        ):
            self.assertEqual(subject.parse_request(subject.request_bytes(operation, payload))[1], operation)
        request = subject.request_bytes("bluetooth.pair.respond", {
            "accept": True, "pin": "4931", "session_id": "a" * 32,
        })
        self.assertIn(b"4931", request)
        self.assertNotIn("4931", repr(subject.redacted(json.loads(request))))
        for operation, payload in (
            ("bluetooth.device.connect", {"address": "not-a-mac"}),
            ("bluetooth.power", {"powered": "yes"}),
            ("bluetooth.pair.status", {"session_id": "../bad"}),
            ("bluetooth.pair.respond", {"accept": True, "pin": "bad\n", "session_id": "a" * 32}),
        ):
            with self.assertRaises(subject.HostServicesV3ContractError):
                subject.request_bytes(operation, payload)


if __name__ == "__main__": unittest.main()
