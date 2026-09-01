from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/physical-pilot/apx-official-hub-autostart-v1.py"
UNIT = ROOT / "config/systemd/apx-official-hub-autostart-v1.service"
LOADER = ROOT / "config/systemd-boot/loader.conf"
INSTALLER = ROOT / "scripts/physical-pilot/install-arch-headless-pilot.sh"


def load_subject():
    spec = importlib.util.spec_from_file_location("hub_autostart", SCRIPT)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


class OfficialHubAutostartV1Tests(unittest.TestCase):
    def test_unit_keeps_tty1_and_has_bounded_failure_restarts(self) -> None:
        source = UNIT.read_text()
        self.assertIn("Wants=getty@tty1.service", source)
        self.assertIn("Restart=on-failure", source)
        self.assertIn("StartLimitBurst=3", source)
        self.assertNotIn("User=apx", source)

    def test_boot_menu_is_hidden_but_entry_and_editor_are_fixed(self) -> None:
        source = LOADER.read_text()
        self.assertIn("default apx-secure-boot-v1.conf", source)
        self.assertIn("timeout 0", source)
        self.assertIn("editor no", source)

    def test_physical_install_uses_graphical_luks_prompt(self) -> None:
        source = INSTALLER.read_text()
        self.assertIn("cryptsetup plymouth iwd", source)
        self.assertIn("base systemd plymouth autodetect", source)
        self.assertIn("rootflags=subvol=@ rw splash", source)

    def test_every_interrupted_graphical_workload_is_recovered_before_hub(self) -> None:
        subject = load_subject()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in ("work", "study"):
                directory = root / name; directory.mkdir()
                (directory / "registration.json").write_text(json.dumps({
                    "name": name, "role": "graphical-base", "release": "hyprland-base-v2",
                    "state": "running",
                }))
            with mock.patch.object(subject, "ENVIRONMENTS", root), \
                    mock.patch.object(subject, "run", side_effect=[
                        SimpleNamespace(stdout="", returncode=0),
                        SimpleNamespace(stdout="", returncode=0),
                        SimpleNamespace(stdout="", returncode=0),
                    ]) as run:
                subject.reconcile_interrupted_workloads()
        self.assertEqual([call.args[0] for call in run.call_args_list[1:]], [
            (subject.GENERAL, "--environment", "study", "--recover"),
            (subject.GENERAL, "--environment", "work", "--recover"),
        ])

    def test_existing_machine_blocks_reconciliation(self) -> None:
        subject = load_subject()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); directory = root / "work"; directory.mkdir()
            (directory / "registration.json").write_text(json.dumps({
                "name": "work", "role": "graphical-base", "release": "hyprland-base-v2",
                "state": "running",
            }))
            with mock.patch.object(subject, "ENVIRONMENTS", root), \
                    mock.patch.object(subject, "run", return_value=SimpleNamespace(
                        stdout="apx-unknown\n", returncode=0,
                    )):
                with self.assertRaises(RuntimeError):
                    subject.reconcile_interrupted_workloads()

    def test_stopped_and_non_graphical_environments_are_not_recovered(self) -> None:
        subject = load_subject()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name, role, state in (("work", "graphical-base", "stopped"),
                                      ("development", "development", "running")):
                directory = root / name; directory.mkdir()
                (directory / "registration.json").write_text(json.dumps({
                    "name": name, "role": role, "release": "hyprland-base-v2", "state": state,
                }))
            with mock.patch.object(subject, "ENVIRONMENTS", root), \
                    mock.patch.object(subject, "run") as run:
                subject.reconcile_interrupted_workloads()
            run.assert_not_called()

    def test_boot_waits_for_every_hub_service_socket(self) -> None:
        subject = load_subject()
        self.assertEqual(len(subject.REQUIRED_SOCKETS), 7)
        self.assertTrue(all(str(path).startswith("/run/apx/") for path in subject.REQUIRED_SOCKETS))
        self.assertEqual(subject.OPTIONAL_SOCKETS, (Path("/run/apx/system-power-v1.sock"),))
        self.assertIn("wait_for_host_services()", SCRIPT.read_text())

    def test_boot_hides_raw_getty_without_removing_recovery(self) -> None:
        source = SCRIPT.read_text()
        self.assertIn('os.open("/dev/tty1", os.O_WRONLY | os.O_NOCTTY)', source)
        self.assertIn('b"\\033[2J\\033[H\\033[?25l"', source)
        self.assertLess(source.index("clear_recovery_console()\n    wait_for_host_services()"),
                        source.index('run((HUB, "--interactive")'))

    def test_authenticated_handoff_suppresses_competing_restart(self) -> None:
        source = SCRIPT.read_text()
        self.assertIn('HANDOFF_LOCK = Path("/run/apx/environment-handoff-v1.lock")', source)
        self.assertIn("def handoff_active() -> bool:", source)
        self.assertIn("if handoff_active():\n        return 0", source)
        self.assertIn("if result.returncode and handoff_active():", source)


if __name__ == "__main__":
    unittest.main()
