import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from apx_system_power_contract import parse_message, request_bytes
from apx_host_services_peer import HostServicesPeer


def load_daemon():
    path = ROOT / "scripts/physical-pilot/apx-system-power-v1.py"
    spec = importlib.util.spec_from_file_location("apx_system_power_test", path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


class SystemPowerContractTests(unittest.TestCase):
    def test_contract_has_no_shell_operation(self):
        value = parse_message(request_bytes("system.reboot.prepare", {}))
        self.assertEqual(value["operation"], "system.reboot.prepare")
        with self.assertRaises(ValueError): request_bytes("exec", {"command": "reboot"})

    def test_contract_exposes_only_typed_hardware_profile_operations(self):
        self.assertEqual(
            parse_message(request_bytes("hardware.platform.set", {"profile": "balanced"}))["operation"],
            "hardware.platform.set",
        )
        self.assertEqual(
            parse_message(request_bytes("hardware.gpu.prepare", {"profile": "nvidia"}))["operation"],
            "hardware.gpu.prepare",
        )
        self.assertEqual(
            parse_message(request_bytes("hardware.display.set", {"percent": 50}))["operation"],
            "hardware.display.set",
        )
        self.assertEqual(
            parse_message(request_bytes("hardware.keyboard.cycle", {}))["operation"],
            "hardware.keyboard.cycle",
        )
        with self.assertRaises(ValueError):
            request_bytes("hardware.write", {"path": "/sys/anything", "value": "1"})

    def test_hardware_status_matches_target_bound_lenovo_interfaces(self):
        subject = load_daemon()
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory); bridge = base / "bridge"; bridge.mkdir()
            (bridge / "hybrid_supported").write_text("2\n")
            (bridge / "igpu_supported").write_text("0\n")
            (bridge / "hybrid_mode").write_text("1\n")
            platform = base / "platform_profile"; platform.write_text("balanced\n")
            choices = base / "platform_profile_choices"
            choices.write_text("low-power balanced performance custom\n")
            boot_id = base / "boot_id"; boot_id.write_text("boot-one\n")
            display = base / "display"; display.mkdir()
            (display / "type").write_text("raw\n")
            (display / "max_brightness").write_text("65535\n")
            (display / "brightness").write_text("32768\n")
            keyboard = base / "keyboard"; keyboard.mkdir()
            (keyboard / "max_brightness").write_text("2\n")
            (keyboard / "brightness").write_text("2\n")
            with mock.patch.object(subject, "GPU_BRIDGE", bridge), \
                    mock.patch.object(subject, "PLATFORM_PROFILE", platform), \
                    mock.patch.object(subject, "PLATFORM_CHOICES", choices), \
                    mock.patch.object(subject, "BOOT_ID", boot_id), \
                    mock.patch.object(subject, "display_backlight", return_value=display), \
                    mock.patch.object(subject, "KEYBOARD_BACKLIGHT", keyboard), \
                    mock.patch.object(subject, "HARDWARE_STATUS", base / "hardware.json"):
                status = subject.hardware_profile_status()
                self.assertEqual(status["gpu_profiles"], ["hybrid", "nvidia"])
                self.assertFalse(status["igpu_firmware_supported"])
                self.assertEqual(status["display_brightness"], 50)
                self.assertEqual(status["keyboard_brightness"], 2)
                self.assertEqual(subject.set_display_brightness(40)["display_brightness"], 40)
                self.assertEqual(subject.cycle_keyboard_brightness()["keyboard_brightness"], 0)
                self.assertEqual(subject.set_platform_profile("performance")["platform_profile"], "performance")
                staged = subject.set_gpu_profile("nvidia")
                self.assertTrue(staged["reboot_required"])
                self.assertEqual((bridge / "hybrid_mode").read_text(), "0\n")

    def test_quickshell_parent_is_exact(self):
        subject = load_daemon()
        with tempfile.TemporaryDirectory() as directory:
            proc = Path(directory); (proc / "20").mkdir(); (proc / "10").mkdir()
            (proc / "20/status").write_text("Name:\tpython3\nPPid:\t10\n")
            (proc / "10/comm").write_text("quickshell\n")
            (proc / "10/cgroup").write_text("0::/system.slice/apx-official-hub-graphical-6f63f9a9.service/session\n")
            (proc / "10/exe").symlink_to("/usr/bin/quickshell")
            self.assertEqual(subject.quickshell_parent(20, proc), 10)
            (proc / "10/comm").write_text("kitty\n")
            with self.assertRaises(PermissionError): subject.quickshell_parent(20, proc)

    def test_prepare_confirm_is_two_step_and_replay_is_refused(self):
        subject = load_daemon(); peer = HostServicesPeer(22, 1000, 1000)
        with tempfile.TemporaryDirectory() as directory, \
                mock.patch.object(subject, "STATE_DIR", Path(directory)), \
                mock.patch.object(subject, "STATUS", Path(directory) / "status.json"), \
                mock.patch.object(subject, "AUDIT", Path(directory) / "audit.jsonl"), \
                mock.patch.object(subject, "RESERVATION", Path(directory) / "reserved"), \
                mock.patch.object(subject, "blockers", return_value=[]), \
                mock.patch.object(subject, "update_state", return_value={"state": "idle", "reboot_required": False}), \
                mock.patch.object(subject.subprocess, "run", return_value=mock.Mock(returncode=0, stdout="", stderr="")):
            subject.PENDING = None; subject.LAST_PREPARE = 0
            prepared = subject.apply("system.reboot.prepare", {}, peer, 10)
            self.assertTrue(prepared["prepared"]); self.assertFalse(prepared["blockers"])
            confirmed = subject.apply("system.action.confirm", {"token": prepared["token"]}, peer, 10)
            self.assertTrue(confirmed["accepted"])
            launched = subject.subprocess.run.call_args.args[0]
            self.assertIn("--no-block", launched)
            self.assertIn(subject.RUNNER, launched)
            with self.assertRaises(ValueError):
                subject.apply("system.action.confirm", {"token": prepared["token"]}, peer, 10)
            self.assertNotIn(prepared["token"], (Path(directory) / "audit.jsonl").read_text())

    def test_gpu_profile_requires_bound_single_use_confirmation(self):
        subject = load_daemon(); peer = HostServicesPeer(22, 1000, 1000)
        with tempfile.TemporaryDirectory() as directory, \
                mock.patch.object(subject, "STATE_DIR", Path(directory)), \
                mock.patch.object(subject, "STATUS", Path(directory) / "status.json"), \
                mock.patch.object(subject, "AUDIT", Path(directory) / "audit.jsonl"), \
                mock.patch.object(subject, "RESERVATION", Path(directory) / "reserved"), \
                mock.patch.object(subject, "set_gpu_profile", return_value={
                    "requested_gpu_profile": "hybrid", "reboot_required": True,
                }) as setter:
            subject.PENDING = None; subject.LAST_PREPARE = 0
            prepared = subject.apply("hardware.gpu.prepare", {"profile": "hybrid"}, peer, 10)
            self.assertTrue(prepared["prepared"]); setter.assert_not_called()
            with self.assertRaises(PermissionError):
                subject.apply("hardware.gpu.confirm", {"token": prepared["token"]}, peer, 11)
            result = subject.apply("hardware.gpu.confirm", {"token": prepared["token"]}, peer, 10)
            self.assertTrue(result["reboot_required"]); setter.assert_called_once_with("hybrid")
            with self.assertRaises(ValueError):
                subject.apply("hardware.gpu.confirm", {"token": prepared["token"]}, peer, 10)

    def test_response_tolerates_client_disappearing_after_accept(self):
        subject = load_daemon()
        connection = mock.Mock()
        connection.getsockopt.return_value = __import__("struct").pack("3i", 20, 1000, 1000)
        connection.recv.side_effect = [b'{"schema":1,"profile":"apx-system-power-v1","operation":"capabilities.get","payload":{}}\n']
        connection.sendall.side_effect = BrokenPipeError()
        with mock.patch.object(subject, "authorize_official_hub_peer"):
            subject.respond(connection)

    def test_wrong_shell_and_expired_token_are_refused(self):
        subject = load_daemon(); peer = HostServicesPeer(22, 1000, 1000)
        with tempfile.TemporaryDirectory() as directory, \
                mock.patch.object(subject, "STATE_DIR", Path(directory)), \
                mock.patch.object(subject, "STATUS", Path(directory) / "status.json"), \
                mock.patch.object(subject, "AUDIT", Path(directory) / "audit.jsonl"), \
                mock.patch.object(subject, "RESERVATION", Path(directory) / "reserved"), \
                mock.patch.object(subject, "blockers", return_value=[]), \
                mock.patch.object(subject, "update_state", return_value={"state": "idle", "reboot_required": False}):
            subject.PENDING = None; subject.LAST_PREPARE = 0
            prepared = subject.apply("system.poweroff.prepare", {}, peer, 10)
            with self.assertRaises(PermissionError):
                subject.apply("system.action.cancel", {"token": prepared["token"]}, peer, 11)
            cancelled = subject.apply("system.action.cancel", {"token": prepared["token"]}, peer, 10)
            self.assertTrue(cancelled["cancelled"])
            subject.LAST_PREPARE = 0
            prepared = subject.apply("system.poweroff.prepare", {}, peer, 10)
            subject.PENDING["expires_monotonic"] = 0
            status = subject.apply("system.action.status", {}, peer, None)
            self.assertFalse(status["pending"])
            self.assertFalse((Path(directory) / "reserved").exists())


if __name__ == "__main__": unittest.main()
