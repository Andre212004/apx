from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
DAEMON = ROOT / "scripts/physical-pilot/apx-host-services-v1.py"
CLIENT = ROOT / "scripts/physical-pilot/apx-host-services-client-v1.py"
UNIT = ROOT / "config/systemd/apx-host-services-v1.service"


class HostServicesPhysicalTests(unittest.TestCase):
    def test_daemon_is_read_only_fixed_and_peer_authenticated(self) -> None:
        source = DAEMON.read_text()
        compile(source, str(DAEMON), "exec")
        for required in (
            'SOCKET = Path("/run/apx/host-services-v1.sock")',
            'WIFI_INTERFACE = "wlan0"', "authorize_shared_service_peer",
            '"/usr/bin/iwctl", "station", WIFI_INTERFACE, "show"',
            '"/usr/bin/timedatectl", "show"', '"bluetooth.service"',
            '"/usr/bin/bluetoothctl", "power", target',
            "SO_PEERCRED", "parse_request", "response_bytes(apply(operation))",
            "APX Host services rejected",
        ):
            self.assertIn(required, source)
        for forbidden in (
            "station connect", "station disconnect", "rfkill unblock", "rfkill block",
            "timedatectl set", "systemctl enable", "systemctl start", "shell=True",
        ):
            self.assertNotIn(forbidden, source)

    def test_client_has_only_fixed_status_modes_and_socket(self) -> None:
        source = CLIENT.read_text()
        compile(source, str(CLIENT), "exec")
        self.assertIn('SOCKET = "/run/apx/host-services-v1.sock"', source)
        for mode in ("json", "waybar-network", "waybar-bluetooth", "waybar-time", "bluetooth-toggle"):
            self.assertIn(mode, source)
        for forbidden in ("subprocess", "systemctl", "iwctl", "rfkill", "/sys/", "/var/lib/iwd"):
            self.assertNotIn(forbidden, source)

    def test_systemd_unit_is_host_read_only_and_unprivileged(self) -> None:
        source = UNIT.read_text()
        for required in (
            "ProtectSystem=strict", "ProtectHome=yes", "NoNewPrivileges=yes",
            "ReadWritePaths=/run/apx", "RestrictAddressFamilies=AF_UNIX",
            "CapabilityBoundingSet=", "MemoryDenyWriteExecute=yes",
        ):
            self.assertIn(required, source)
        self.assertNotIn("/var/lib/apx/environments", source)
        self.assertNotIn("CAP_NET_ADMIN", source)


if __name__ == "__main__":
    unittest.main()
