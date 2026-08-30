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

    def test_detailed_winpe_failure_reaches_linux_diagnosis(self) -> None:
        subject = load(FINALIZER, "apx_windows_finalizer_detailed_failure")
        pending = {
            "action": "create", "created_at": 1, "explicit_attempts": 1,
            "generation": "12345678-1234-4234-9234-123456789abc",
            "name": "windows", "profile": "apx-native-windows-pending-v1",
            "requested_size_gib": 160, "resume_attempts": 11,
            "schema": 1, "stage": "installing",
        }
        status = {
            "profile": "apx-native-windows-install-status-v2",
            "generation": pending["generation"], "status": "failed",
            "error": "APX-PART-03", "step": "partition-identities",
            "detail": "windows-target", "command": "diskpart-partition-probe",
            "exit_code": "1",
            "diagnostic": "role=WINDOWS candidates=0 required_label=-",
        }
        with tempfile.TemporaryDirectory() as directory, \
                mock.patch.object(subject, "PENDING", Path(directory) / "pending.json"), \
                mock.patch.object(subject, "windows_complete", return_value=None), \
                mock.patch.object(subject, "installer_status", return_value=status), \
                mock.patch.object(subject, "ensure_linux_safe"), \
                mock.patch.object(subject, "archive_failure"), \
                mock.patch.object(subject, "write_state"):
            subject.finalize_create(pending)
            persisted = json.loads(subject.PENDING.read_text())
        self.assertEqual(persisted["stage"], "failed")
        self.assertIn("partition-identities/windows-target", persisted["failure_reason"])
        self.assertIn("comando=diskpart-partition-probe", persisted["failure_reason"])
        self.assertIn("exit=1", persisted["failure_reason"])
        self.assertIn("candidates=0", persisted["failure_reason"])

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
        self.assertIn(r"%APX_ESP%\EFI\APX\native-windows\install-log-v2.txt", text)
        self.assertIn("detail=!APX_DETAIL!", text)
        self.assertIn("command=!APX_LAST_COMMAND!", text)
        self.assertIn("exit_code=!APX_LAST_EXIT!", text)
        self.assertIn("diagnostic=!APX_DIAGNOSTIC!", text)
        self.assertIn("pause >nul", text)
        self.assertIn(r"/LogPath:%APX_MEDIA%\APX\dism-apply-v2.log /LogLevel:4", text)
        self.assertEqual((ROOT / ".gitattributes").read_text(), "*.cmd text eol=crlf\n")

    def test_windows_target_avoids_truncated_diskpart_label_but_keeps_full_checks(self) -> None:
        text = WINPE.read_text()
        probe = ('call :find_partition WINDOWS '
                 '"ebd0a0a2-b9e5-4433-87c0-68b6b72699c7" "-" '
                 '"!APX_WINDOWS_SIZE_TEXT!"')
        self.assertEqual(text.count(probe), 2)
        self.assertIn('call :mount_partition !APX_PART_WINDOWS! '
                      '!APX_LETTER_WINDOWS! WINDOWS "APXWINTARGET"', text)
        self.assertIn('call :validate_contract "%APX_TARGET%\\APX\\install-contract-v2.ini"', text)
        self.assertIn("FULL_VOLUME_LABEL role=!APX_MOUNT_ROLE!", text)
        self.assertLess(text.index("call :mount_partition !APX_PART_EFI!"), text.index(probe))
        self.assertIn("PARTITION_PROBE role=!APX_ROLE!", text)
        self.assertIn('>>"%APX_LOG%" type "%APX_DP_OUTPUT%"', text)

    def test_failure_archive_keeps_each_explicit_attempt(self) -> None:
        subject = load(FINALIZER, "apx_windows_finalizer_failure_history")
        pending = {
            "generation": "12345678-1234-4234-9234-123456789abc",
            "explicit_attempts": 1,
        }
        with tempfile.TemporaryDirectory() as directory, \
                mock.patch.object(subject, "FAILURES", Path(directory)), \
                mock.patch.object(subject.time, "time", side_effect=(100, 101)):
            subject.archive_failure(pending, {"error": "APX-PART-03"}, "first explicit failure")
            pending["explicit_attempts"] = 2
            subject.archive_failure(pending, {"error": "APX-APPLY-01"}, "second explicit failure")
            root = Path(directory) / pending["generation"]
            self.assertTrue((root / "failure.json").is_file())
            attempts = sorted(root.glob("failure-*-attempt-*.json"))
            self.assertEqual(len(attempts), 2)
            self.assertTrue(attempts[0].name.startswith("failure-100-attempt-1-"))
            self.assertTrue(attempts[1].name.startswith("failure-101-attempt-2-"))
            self.assertEqual(json.loads(attempts[0].read_text())["reason"], "first explicit failure")
            self.assertEqual(json.loads(attempts[1].read_text())["reason"], "second explicit failure")

    def test_preparation_never_arms_or_reboots(self) -> None:
        source = PREPARE.read_text()
        self.assertNotIn('efibootmgr -n "$setup_entry"', source)
        self.assertNotIn("systemctl reboot", source)
        self.assertIn("ready without reboot", source)
        self.assertIn("find.exe", source)

    def test_explicit_retry_is_bounded_to_two(self) -> None:
        subject = load(RECOVERY, "apx_windows_recovery_limit")
        self.assertEqual(subject.MAX_EXPLICIT_INSTALL_ATTEMPTS, 2)
        self.assertEqual(subject.MAX_EXPLICIT_BOOT_ATTEMPTS, 4)
        pending = {
            "action": "create", "stage": "recovery-required",
            "requested_size_gib": 160,
            "generation": "12345678-1234-4234-9234-123456789abc",
            "resume_attempts": 11,
            "explicit_attempts": 2,
        }
        with self.assertRaisesRegex(RuntimeError, "limite de duas"):
            subject.retry(pending, b"{}\n")

    def test_first_boot_continuation_has_its_own_bounded_counter(self) -> None:
        subject = load(RECOVERY, "apx_windows_first_boot_limit")
        pending = {
            "action": "create", "stage": "boot-prepared",
            "requested_size_gib": 160,
            "generation": "12345678-1234-4234-9234-123456789abc",
            "explicit_attempts": 1, "boot_attempts": 4,
        }
        with self.assertRaisesRegex(RuntimeError, "limite de continuações"):
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
