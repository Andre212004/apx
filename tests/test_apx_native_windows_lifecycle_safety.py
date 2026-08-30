from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
FINALIZER = ROOT / "scripts/physical-pilot/apx-native-windows-lifecycle-finalize-v1.py"
RECOVERY = ROOT / "scripts/physical-pilot/apx-native-windows-recovery-v1.py"
PREPARE = ROOT / "scripts/physical-pilot/prepare-native-windows-installer-v2.sh"
WINPE = ROOT / "config/system-images-v1/windows-internal-winpe/apx-media.cmd"
UNIT = ROOT / "config/systemd/apx-native-windows-lifecycle-finalize-v1.service"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class NativeWindowsLifecycleSafetyTests(unittest.TestCase):
    def test_incident_terminal_failure_never_arms_bootnext_or_reboots(self) -> None:
        subject = load(FINALIZER, "apx_windows_finalizer_incident")
        pending = {
            "action": "create",
            "created_at": 1787769090,
            "generation": "18fe09c4-ed14-40a3-96d2-544d3ba3e628",
            "name": "windows",
            "profile": "apx-native-windows-pending-v1",
            "requested_size_gib": 160,
            "resume_attempts": 11,
            "schema": 1,
            "stage": "installing",
        }
        status = {
            "profile": "apx-native-windows-install-status-v2",
            "generation": pending["generation"],
            "status": "failed",
            "error": "APX-FORMAT-04",
            "step": "formatted-target-label",
        }
        with tempfile.TemporaryDirectory() as directory:
            pending_path = Path(directory) / "windows-pending.json"
            with mock.patch.object(subject, "PENDING", pending_path), \
                    mock.patch.object(subject, "windows_complete", return_value=None), \
                    mock.patch.object(subject, "installer_status", return_value=status), \
                    mock.patch.object(subject, "ensure_linux_safe") as linux_safe, \
                    mock.patch.object(subject, "archive_failure") as archive, \
                    mock.patch.object(subject, "write_state"), \
                    mock.patch.object(subject, "run") as run:
                subject.finalize_create(pending)

            persisted = json.loads(pending_path.read_text())
            self.assertEqual(persisted["stage"], "failed")
            self.assertEqual(persisted["failure_code"], "APX-FORMAT-04")
            self.assertEqual(persisted["failure_step"], "formatted-target-label")
            self.assertEqual(persisted["resume_attempts"], 11)
            linux_safe.assert_called_once_with()
            archive.assert_called_once()
            run.assert_not_called()

    def test_missing_winpe_status_fails_closed_without_reboot(self) -> None:
        subject = load(FINALIZER, "apx_windows_finalizer_missing_status")
        pending = {
            "action": "create", "created_at": 1,
            "generation": "12345678-1234-4234-9234-123456789abc",
            "name": "windows", "profile": "apx-native-windows-pending-v1",
            "requested_size_gib": 160, "resume_attempts": 1,
            "schema": 1, "stage": "installing",
        }
        with tempfile.TemporaryDirectory() as directory:
            with mock.patch.object(subject, "PENDING", Path(directory) / "pending.json"), \
                    mock.patch.object(subject, "windows_complete", return_value=None), \
                    mock.patch.object(subject, "installer_status", return_value=None), \
                    mock.patch.object(subject, "ensure_linux_safe"), \
                    mock.patch.object(subject, "archive_failure"), \
                    mock.patch.object(subject, "write_state"), \
                    mock.patch.object(subject, "run") as run:
                subject.finalize_create(pending)
            self.assertEqual(pending["stage"], "recovery-required")
            self.assertEqual(pending["failure_code"], "APX-WINPE-NO-STATUS")
            run.assert_not_called()

    def test_finalizer_has_no_reboot_or_bootnext_arm_path(self) -> None:
        source = FINALIZER.read_text()
        self.assertNotIn('"/usr/bin/efibootmgr", "-n"', source)
        self.assertNotIn('"systemctl", "--no-block", "reboot"', source)
        self.assertIn('run(("/usr/bin/efibootmgr", "-N"))', source)
        self.assertIn('TERMINAL_STAGES = {"failed", "recovery-required"}', source)
        unit = UNIT.read_text()
        self.assertNotIn("Restart=", unit)
        self.assertIn("TimeoutStartSec=30min", unit)

    def test_winpe_uses_available_find_and_is_crlf(self) -> None:
        raw = WINPE.read_bytes()
        text = raw.decode("ascii")
        self.assertEqual(raw.count(b"\n"), raw.count(b"\r\n"))
        self.assertNotIn("file_contains", text)
        self.assertNotIn("findstr", text.lower())
        self.assertGreaterEqual(text.count(r"X:\Windows\System32\find.exe"), 9)
        self.assertIn("status=failed", text)
        self.assertIn(r"%APX_ESP%\EFI\APX\native-windows\install-status-v2.ini", text)
        self.assertEqual((ROOT / ".gitattributes").read_text(), "*.cmd text eol=crlf\n")

    def test_preparation_never_arms_or_reboots(self) -> None:
        source = PREPARE.read_text()
        self.assertNotIn('efibootmgr -n "$setup_entry"', source)
        self.assertNotIn("systemctl reboot", source)
        self.assertIn("ready without reboot", source)
        self.assertIn("find.exe", source)

    def test_explicit_retry_is_bounded_to_two(self) -> None:
        subject = load(RECOVERY, "apx_windows_recovery_limit")
        self.assertEqual(subject.MAX_EXPLICIT_ATTEMPTS, 2)
        pending = {
            "action": "create", "stage": "recovery-required",
            "requested_size_gib": 160,
            "generation": "12345678-1234-4234-9234-123456789abc",
            "resume_attempts": 11,
            "explicit_attempts": 2,
        }
        with self.assertRaisesRegex(RuntimeError, "limite de duas"):
            subject.retry(pending, b"{}\n")

    def test_no_existing_bootnext_is_already_safe(self) -> None:
        subject = load(FINALIZER, "apx_windows_finalizer_no_bootnext")
        firmware = (
            "BootCurrent: 0005\n"
            "BootOrder: 0005,0000\n"
            "Boot0005* Linux Boot Manager\tHD(1,GPT,9625f250-9acc-453a-ae63-0c863ade440f,0,0)"
            "/\\EFI\\systemd\\systemd-bootx64.efi\n"
        )
        with mock.patch.object(subject, "run", return_value=mock.Mock(returncode=1)), \
                mock.patch.object(subject, "checked", return_value=firmware):
            subject.ensure_linux_safe()


if __name__ == "__main__":
    unittest.main()
