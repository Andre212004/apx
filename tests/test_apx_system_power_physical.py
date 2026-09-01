import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load_runner():
    path = ROOT / "scripts/physical-pilot/apx-system-power-runner-v1.py"
    spec = importlib.util.spec_from_file_location("apx_system_power_runner_test", path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


class SystemPowerPhysicalSourceTests(unittest.TestCase):
    def test_runner_finds_only_exact_root_interactive_hub_supervisor(self):
        subject = load_runner()
        with tempfile.TemporaryDirectory() as directory:
            proc = Path(directory)
            for pid, uid, argument in (("42", "0", "--interactive"), ("43", "1000", "--interactive"),
                                       ("44", "0", "--recover")):
                process = proc / pid; process.mkdir()
                process.joinpath("cmdline").write_bytes(
                    b"python3\0" + subject.HUB_RECOVERY.encode() + b"\0" + argument.encode() + b"\0"
                )
                process.joinpath("status").write_text(f"Name:\tpython3\nUid:\t{uid}\t{uid}\t{uid}\t{uid}\n")
                process.joinpath("cgroup").write_text("0::/session.scope\n")
            self.assertEqual(subject.hub_launcher_supervisors(proc), ((42, "0::/session.scope\n"),))

    def test_runner_uses_logind_after_exact_recovery(self):
        source = (ROOT / "scripts/physical-pilot/apx-system-power-runner-v1.py").read_text()
        launcher = (ROOT / "scripts/physical-pilot/apx-official-hub-graphical-v1.py").read_text()
        self.assertLess(source.index('(HUB_RECOVERY, "--recover")'), source.index('("/usr/bin/systemctl", "--no-block", args.action)'))
        self.assertIn('run(("/usr/bin/systemctl", "--no-block", args.action))', source)
        self.assertIn("machine-transition-v1.lock", source)
        self.assertIn("quiesce_hub_launcher()", source)
        self.assertIn("multiple official Hub launch supervisors exist", source)
        self.assertIn("official-hub-recovery-v1.lock", launcher)
        self.assertIn("fcntl.LOCK_EX", launcher)

    def test_daemon_has_no_arbitrary_command_surface(self):
        source = (ROOT / "scripts/physical-pilot/apx-system-power-v1.py").read_text()
        self.assertIn("quickshell_parent(pid)", source)
        self.assertIn("secrets.compare_digest", source)
        self.assertIn("systemd-inhibit", source)
        self.assertIn("select.select(servers, [], [], 1)", source)
        self.assertNotIn('payload.get("command")', source)
        self.assertIn('def display_backlight()', source)
        self.assertIn('"/0000:05:00.0/drm/"', source)
        self.assertNotIn('amdgpu_bl2', source)

    def test_exact_launcher_leases_and_revokes_private_socket(self):
        source = (ROOT / "scripts/physical-pilot/apx-official-hub-graphical-v1.py").read_text()
        for required in ("POWER_SOCKET", "activate_service_sockets(uid_base)", "deactivate_service_sockets()",
                         "apx-system-power-client-v1.py", "LEASED_SERVICE_SOCKETS", "0o660", "0o600"):
            self.assertIn(required, source)

    def test_suspend_preserves_active_environment_and_uses_logind(self):
        source = (ROOT / "scripts/physical-pilot/apx-system-power-runner-v1.py").read_text()
        suspend = source.index('if args.action == "suspend"')
        recovery = source.index('(HUB_RECOVERY, "--recover")')
        self.assertLess(suspend, recovery)
        self.assertIn('run(("/usr/bin/loginctl", "suspend"))', source)
        self.assertNotIn('run(("/usr/bin/systemctl", "suspend"))', source)

    def test_update_runner_honors_power_reservation(self):
        source = (ROOT / "scripts/physical-pilot/apx-coordinated-update-runner-v1.py").read_text()
        self.assertIn("system-power-v1.reserved", source)
        self.assertIn("machine-transition-v1.lock", source)
