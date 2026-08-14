from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
DAEMON = ROOT / "scripts/physical-pilot/apx-host-services-v3.py"
CLIENT = ROOT / "scripts/physical-pilot/apx-host-services-client-v3.py"
UNIT = ROOT / "config/systemd/apx-host-services-v3.service"


class HostServicesV3PhysicalTests(unittest.TestCase):
    def test_daemon_uses_peer_auth_typed_operations_and_no_secret_argv_or_tempfile(self):
        source = DAEMON.read_text(); compile(source, str(DAEMON), "exec")
        for required in ('SOCKET = Path("/run/apx/host-services-v3.sock")', "authorize_shared_service_peer",
                         "SO_PEERCRED", "parse_request", "pty.openpty()", "~termios.ECHO",
                         '"events.subscribe"', '"network.connect"', '"network.connectivity-check"',
                         '"network.portal.open"', '"bluetooth.pair.begin"', '"bluetooth.pair.respond"',
                         '"KeyboardDisplay"', "perform_connectivity_check", "MAX_CLIENTS"):
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
        self.assertIn('"--accept"', source)
        self.assertIn("sys.stdin.readline()", source)
        self.assertNotIn('add_argument("--password"', source)
        self.assertNotIn('add_argument("--passphrase"', source)

    def test_unit_keeps_v3_at_host_boundary(self):
        source = UNIT.read_text()
        for required in ("ProtectSystem=strict", "ProtectHome=yes",
                         "RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6 AF_NETLINK",
                         "CapabilityBoundingSet=CAP_NET_RAW", "ReadWritePaths=/run/apx",
                         "MemoryDenyWriteExecute=yes"):
            self.assertIn(required, source)
        self.assertNotIn("/var/lib/iwd", source)


if __name__ == "__main__": unittest.main()
