from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / "scripts/physical-pilot/apx-environment-network-v1.py"
RUNTIME = ROOT / "scripts/virtual-lab/apx-lab-runtime.py"
NETWORK = ROOT / "config/hub-headless-v4/20-host0.network"


class EnvironmentNetworkV1Tests(unittest.TestCase):
    def test_policy_allows_dhcp_but_denies_host_private_and_siblings(self) -> None:
        source = ADAPTER.read_text()
        compile(source, str(ADAPTER), "exec")
        for required in (
            'INTERFACE = "ve-apx-hub"', "udp dport 67 accept",
            "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16",
            'oifname "ve-*" drop', "hook input", "hook forward",
        ):
            self.assertIn(required, source)
        self.assertNotIn("policy drop", source)

    def test_runtime_applies_before_start_and_removes_on_stop_or_failure(self) -> None:
        source = RUNTIME.read_text()
        apply_position = source.index('run([NETWORK_ADAPTER, "apply"')
        start_position = source.index("run(command, capture=True)", apply_position)
        self.assertLess(apply_position, start_position)
        self.assertGreaterEqual(source.count('[NETWORK_ADAPTER, "remove"'), 2)

    def test_container_uses_external_dns_and_disables_ipv6_ra(self) -> None:
        source = NETWORK.read_text()
        self.assertIn("UseDNS=no", source)
        self.assertIn("IPv6AcceptRA=no", source)
        self.assertIn("DNS=1.1.1.1", source)


if __name__ == "__main__":
    unittest.main()
