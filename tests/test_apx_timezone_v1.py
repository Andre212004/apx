import importlib.util
import json
from pathlib import Path
import stat
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/physical-pilot/apx-timezone-v1.py"
UNIT = ROOT / "config/systemd/apx-timezone-v1.service"


def load_subject():
    spec = importlib.util.spec_from_file_location("apx_timezone_v1", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class TimezoneV1Tests(unittest.TestCase):
    def test_source_and_unit_have_closed_host_only_shape(self):
        source = SCRIPT.read_text()
        unit = UNIT.read_text()

        compile(source, str(SCRIPT), "exec")

        for required in (
            'CONFIG = Path("/var/lib/apx/timezone-v1/networks.json")',
            '"/usr/bin/iwctl", "station", WIFI_INTERFACE, "show"',
            '"/usr/bin/timedatectl", "list-timezones"',
            '"/usr/bin/timedatectl", "set-timezone", target',
            '"already-correct"',
            '"network-unmapped"',
        ):
            self.assertIn(required, source)

        for forbidden in (
            "curl",
            "http://",
            "https://",
            "geoclue",
            "ConnectedBss",
            "shell=True",
        ):
            self.assertNotIn(forbidden, source)

        self.assertIn("ProtectSystem=strict", unit)
        self.assertIn("PrivateDevices=yes", unit)
        self.assertIn("CapabilityBoundingSet=", unit)
        self.assertNotIn("ReadWritePaths=/var/lib/apx", unit)

    def test_config_requires_exact_root_owned_0600_shape(self):
        subject = load_subject()

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "networks.json"
            path.write_text(json.dumps({
                "schema": 1,
                "profile": "apx-timezone-network-map-v1",
                "networks": {"Casa": "Europe/Lisbon"},
            }))
            path.chmod(0o600)

            result = subject.read_config(path)

            self.assertEqual(result, {"Casa": "Europe/Lisbon"})

    def test_config_rejects_symlink_and_wrong_permissions(self):
        subject = load_subject()

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            target = root / "target.json"
            target.write_text(json.dumps({
                "schema": 1,
                "profile": "apx-timezone-network-map-v1",
                "networks": {"Casa": "Europe/Lisbon"},
            }))
            target.chmod(0o600)

            link = root / "networks.json"
            link.symlink_to(target)

            with self.assertRaises(subject.TimezoneError):
                subject.read_config(link)

            regular = root / "regular.json"
            regular.write_text(target.read_text())
            regular.chmod(0o644)

            with self.assertRaises(subject.TimezoneError):
                subject.read_config(regular)

    def test_reconcile_changes_only_valid_mapped_timezone(self):
        subject = load_subject()

        responses = [
            mock.Mock(returncode=0, stdout="Europe/Lisbon\nAmerica/Sao_Paulo\n"),
            mock.Mock(returncode=0, stdout="America/Sao_Paulo\n"),
            mock.Mock(returncode=0, stdout=""),
            mock.Mock(returncode=0, stdout="Europe/Lisbon\n"),
        ]

        with mock.patch.object(subject, "read_config", return_value={"Casa": "Europe/Lisbon"}), \
                mock.patch.object(subject, "current_ssid", return_value="Casa"), \
                mock.patch.object(subject, "run", side_effect=responses) as run:
            self.assertEqual(subject.reconcile(), "updated")

        self.assertEqual(
            run.call_args_list[2].args[0],
            ("/usr/bin/timedatectl", "set-timezone", "Europe/Lisbon"),
        )

    def test_unmapped_network_never_changes_timezone(self):
        subject = load_subject()

        with mock.patch.object(subject, "read_config", return_value={"Casa": "Europe/Lisbon"}), \
                mock.patch.object(subject, "current_ssid", return_value="Universidade"), \
                mock.patch.object(subject, "run") as run:
            self.assertEqual(subject.reconcile(), "network-unmapped")
            run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
