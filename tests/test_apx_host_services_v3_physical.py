import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
DAEMON = ROOT / "scripts/physical-pilot/apx-host-services-v3.py"
CLIENT = ROOT / "scripts/physical-pilot/apx-host-services-client-v3.py"
UNIT = ROOT / "config/systemd/apx-host-services-v3.service"
DEPLOY = ROOT / "scripts/physical-pilot/deploy-host-connectivity-input-v1.sh"


def load_daemon():
    spec = importlib.util.spec_from_file_location("apx_host_services_v3_test", DAEMON)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class HostServicesV3PhysicalTests(unittest.TestCase):
    def test_daemon_uses_peer_auth_typed_operations_and_no_secret_argv_or_tempfile(self):
        source = DAEMON.read_text(); compile(source, str(DAEMON), "exec")
        for required in ('SOCKET = Path("/run/apx/host-services-v3.sock")', "authorize_shared_service_peer",
                         "SO_PEERCRED", "parse_request", "pty.openpty()", "~termios.ECHO",
                         '"events.subscribe"', '"network.connect"', '"network.connectivity-check"',
                         '"network.portal.open"', '"bluetooth.pair.begin"', '"bluetooth.pair.respond"',
                         '"radio.status"', 'RFKILL_ROOT = Path("/sys/class/rfkill")',
                         'RFKILL = "/usr/bin/rfkill"', '"airplane_mode"', '"KeyboardDisplay"',
                         "perform_connectivity_check", "bluetooth_soft_blocked", "set_bluetooth_power",
                         "wait_for_network", "MAX_CLIENTS"):
            self.assertIn(required, source)
        self.assertIn("if not stat.S_ISSOCK(metadata.st_mode)", source)
        self.assertNotIn("metadata.st_uid != 0", source)
        for forbidden in ("shell=True", "NamedTemporaryFile", "mkstemp", '"--passphrase"', "os.system"):
            self.assertNotIn(forbidden, source)
        self.assertGreaterEqual(source.count("~termios.ECHO"), 2)

    def test_client_reads_credentials_from_stdin_and_never_accepts_secret_argument(self):
        source = CLIENT.read_text(); compile(source, str(CLIENT), "exec")
        self.assertIn('SOCKET = "/run/apx/host-services-v3.sock"', source)
        self.assertIn('"--credential-stdin"', source)
        self.assertIn('"bluetooth-pair-respond"', source)
        self.assertIn('"radio-status"', source)
        self.assertIn('"--accept"', source)
        self.assertIn("sys.stdin.readline()", source)
        self.assertNotIn('add_argument("--password"', source)
        self.assertNotIn('add_argument("--passphrase"', source)

    def test_unit_keeps_v3_at_host_boundary(self):
        source = UNIT.read_text()
        for required in ("ProtectSystem=strict", "ProtectHome=yes",
                         "RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6 AF_NETLINK",
                         "CapabilityBoundingSet=CAP_NET_ADMIN CAP_NET_RAW", "ReadWritePaths=/run/apx",
                         "MemoryDenyWriteExecute=yes"):
            self.assertIn(required, source)
        self.assertNotIn("/var/lib/iwd", source)

    def test_bluetooth_power_unblocks_before_bluez_and_verifies_state(self):
        subject = load_daemon()
        calls = []

        def run(arguments, timeout=10):
            calls.append(arguments)
            return SimpleNamespace(returncode=0, stdout="PowerState: off\n")

        with mock.patch.object(subject, "run", side_effect=run), \
                mock.patch.object(subject, "bluetooth_soft_blocked", return_value=False), \
                mock.patch.object(subject, "bluetooth_state", return_value={"powered": True}):
            state = subject.set_bluetooth_power(True)
        self.assertEqual(state, {"powered": True})
        self.assertEqual(calls, [
            ("/usr/bin/rfkill", "unblock", "bluetooth"),
            ("/usr/bin/bluetoothctl", "show"),
            ("/usr/bin/bluetoothctl", "power", "on"),
        ])

    def test_wifi_connect_confirmation_requires_the_requested_ssid(self):
        subject = load_daemon()
        with mock.patch.object(subject, "network_state", side_effect=[
                {"connected": True, "network": "old"},
                {"connected": True, "network": "requested"},
        ]), mock.patch.object(subject.time, "sleep"):
            self.assertEqual(subject.wait_for_network("requested"), {
                "connected": True, "network": "requested",
            })

    def test_deployer_stages_without_restarting_the_inode_bound_service(self):
        source = DEPLOY.read_text()
        for required in ("rfkill unblock bluetooth", "bluetoothctl power on",
                         "pkill -x quickshell", "stop_fn_bridge", "exactly one Fn bridge did not remain running",
                         "daemon activation pending coordinated Hub relaunch"):
            self.assertIn(required, source)
        self.assertNotIn("systemctl restart apx-host-services-v3.service", source)


if __name__ == "__main__": unittest.main()
