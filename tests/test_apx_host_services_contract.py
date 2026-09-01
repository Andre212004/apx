from dataclasses import replace
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import apx_host_services_contract as subject  # noqa: E402


def state(**changes):
    value = subject.HostServicesState(
        "iwd", "wlan0", True, "APX-WIFI", "America/Sao_Paulo",
        True, True, "bluez", True, False,
    )
    return replace(value, **changes)


class HostServicesContractTests(unittest.TestCase):
    def test_closed_request_and_state_round_trip(self) -> None:
        self.assertEqual(subject.parse_request(subject.request_bytes()), "status")
        self.assertEqual(
            subject.parse_request(subject.request_bytes("bluetooth-toggle")),
            "bluetooth-toggle",
        )
        self.assertEqual(subject.parse_response(subject.response_bytes(state())), state())

    def test_request_accepts_no_domains_actions_paths_or_arguments(self) -> None:
        for change in (
            {"operation": "set-wifi", "profile": subject.PROFILE, "schema": subject.SCHEMA},
            {"operation": "status", "profile": subject.PROFILE, "schema": subject.SCHEMA, "ssid": "injected"},
            {"operation": "status", "profile": subject.PROFILE, "schema": subject.SCHEMA, "path": "/tmp/injected"},
        ):
            with self.assertRaises(subject.HostServicesContractError):
                subject.parse_request((json.dumps(change) + "\n").encode())

    def test_unsafe_network_name_and_contradictory_states_are_rejected(self) -> None:
        cases = (
            state(network_name="bad\nname"),
            state(network_connected=False),
            state(ntp_enabled=False, time_synchronized=True),
            state(bluetooth_backend="unavailable", bluetooth_powered=True),
            state(bluetooth_controller_present=False, bluetooth_powered=True),
        )
        for value in cases:
            with self.subTest(value=value):
                with self.assertRaises(subject.HostServicesContractError):
                    subject.response_bytes(value)

    def test_locked_current_bluetooth_state_is_valid(self) -> None:
        value = state(
            ntp_enabled=False, time_synchronized=False,
            bluetooth_backend="unavailable", bluetooth_powered=False,
        )
        self.assertEqual(subject.parse_response(subject.response_bytes(value)), value)


if __name__ == "__main__":
    unittest.main()
