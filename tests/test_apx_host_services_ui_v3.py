from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / "scripts/physical-pilot/apx-host-services-ui-v3.py"


class HostServicesUiV3Tests(unittest.TestCase):
    def test_adapter_preserves_quickshell_shape_and_uses_secure_v3_credentials(self):
        source = ADAPTER.read_text(); compile(source, str(ADAPTER), "exec")
        for required in ('V2 = "/run/apx/host-services-client-v2.py"',
                         'V3 = "/run/apx/host-services-client-v3.py"', '"open_networks"',
                         '"network_details"', '"network_connectivity"', '"network_portal"',
                         '"wifi-portal-open"', '"--credential-stdin"', '"-password"'):
            self.assertIn(required, source)
        for forbidden in ("shell=True", '"--passphrase"', '"--password"', "NamedTemporaryFile", "mkstemp"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__": unittest.main()
