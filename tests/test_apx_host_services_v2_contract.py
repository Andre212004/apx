from dataclasses import replace
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import apx_host_services_v2_contract as subject  # noqa: E402


def state(**changes):
    value = subject.HostServicesV2State(
        "iwd", "wlan0", True, "APX", ("APX", "Known"), ("APX", "Other"),
        "America/Sao_Paulo", True, True, "bluez", True, True,
        (subject.BluetoothDevice("AA:BB:CC:DD:EE:FF", "Headphones", False),),
    )
    return replace(value, **changes)


class HostServicesV2ContractTests(unittest.TestCase):
    def test_typed_requests_and_state_round_trip(self):
        cases = (("status", None), ("wifi-scan", None), ("wifi-disconnect", None),
                 ("wifi-connect", "Known"), ("bluetooth-power", "on"),
                 ("bluetooth-connect", "AA:BB:CC:DD:EE:FF"))
        for operation, target in cases:
            self.assertEqual(subject.parse_request(subject.request_bytes(operation, target)), (operation, target))
        self.assertEqual(subject.parse_response(subject.response_bytes(state())), state())

    def test_arbitrary_commands_and_invalid_targets_fail_closed(self):
        for operation, target in (("exec", "id"), ("wifi-connect", "bad\nname"),
                                  ("bluetooth-connect", "not-a-mac"), ("status", "extra")):
            with self.assertRaises(subject.HostServicesV2ContractError):
                subject.request_bytes(operation, target)
        forged = {"operation": "wifi-connect", "profile": subject.PROFILE,
                  "schema": subject.SCHEMA, "target": "Known", "password": "secret"}
        with self.assertRaises(subject.HostServicesV2ContractError):
            subject.parse_request((json.dumps(forged) + "\n").encode())

    def test_catalogues_are_canonical_and_labels_safe(self):
        for invalid in (state(known_networks=("z", "a")),
                        state(bluetooth_devices=(subject.BluetoothDevice("bad", "x", False),)),
                        state(available_networks=("bad\nname",))):
            with self.assertRaises(subject.HostServicesV2ContractError):
                subject.response_bytes(invalid)


if __name__ == "__main__": unittest.main()
