import importlib.machinery
import importlib.util
import json
from pathlib import Path
import tempfile
from unittest import mock
import unittest


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "config/environment-vm-v2/local/bin/apx-vm-runtime-v2"
WINDOWS = ROOT / "config/environment-vm-v2/profiles/windows11.json"
UBUNTU = ROOT / "config/environment-vm-v2/profiles/ubuntu.json"
HYPRLAND = ROOT / "config/environment-vm-v2/hypr/hyprland.lua"
PROVISIONER = ROOT / "scripts/physical-pilot/apx-system-environment-provision-v1.py"
ACCELERATOR = ROOT / "config/environment-vm-v2/APXTools/ATIVAR-ACELERACAO.cmd"
DISPLAY_TUNER = ROOT / "config/environment-vm-v2/APXTools/APX-CONFIGURAR-120HZ.ps1"
README = ROOT / "config/environment-vm-v2/APXTools/LEIA-ME.txt"
DEPLOY = ROOT / "scripts/physical-pilot/deploy-system-vm-v2.sh"
VFIO = ROOT / "config/environment-vm-v2/vfio-pci-v1.json"


def load_runtime():
    loader = importlib.machinery.SourceFileLoader("apx_vm_runtime_v2", str(RUNTIME))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


class Windows11VmLauncherTests(unittest.TestCase):
    def test_v2_is_one_runtime_without_host_readiness_protocol(self):
        source = RUNTIME.read_text()
        compile(source, str(RUNTIME), "exec")
        self.assertIn("Single-process owner for an APX KVM/VFIO system Environment", source)
        self.assertIn('qemu = subprocess.Popen(command', source)
        self.assertIn('client = subprocess.Popen(native_client', source)
        self.assertIn('stop(client); stop(qemu); stop(swtpm)', source)
        self.assertIn('"/usr/bin/hyprctl", "dispatch", "exit"', source)
        self.assertNotIn("query-status", source)
        self.assertNotIn("query-spice", source)
        self.assertNotIn("ready-v1", source)
        self.assertNotIn("presentation-ready", source)
        self.assertNotIn("deadline = time.monotonic() + 30", source)

    def test_resource_plan_uses_every_core_except_one_physical_host_core(self):
        runtime = load_runtime()
        topology = [[0, 1], [2, 3], [4, 5], [6, 7], [8, 9], [10, 11]]
        with mock.patch.object(runtime.os, "sched_getaffinity", return_value=set(range(12))), \
                mock.patch.object(runtime, "cpu_groups", return_value=topology), \
                mock.patch.object(runtime, "memory_limit_bytes", return_value=28 * runtime.GIB):
            plan = runtime.resource_plan()
        self.assertEqual(plan["cpus"], list(range(10)))
        self.assertEqual(plan["cpu_list"], "0-9")
        self.assertEqual(plan["reserved_cpus"], [10, 11])
        self.assertEqual((plan["vcpus"], plan["cores"], plan["threads"]), (10, 5, 2))
        self.assertEqual(plan["memory_gib"], 21)

    def test_resource_plan_respects_the_outer_memory_limit(self):
        runtime = load_runtime()
        with mock.patch.object(runtime.os, "sched_getaffinity", return_value={0, 1, 2, 3}), \
                mock.patch.object(runtime, "cpu_groups", return_value=[[0, 2], [1, 3]]), \
                mock.patch.object(runtime, "memory_limit_bytes", return_value=12 * runtime.GIB):
            plan = runtime.resource_plan()
        self.assertEqual(plan["memory_gib"], 7)
        self.assertEqual(plan["cpus"], [0, 2])

    def test_profiles_are_small_declarative_inputs_to_the_same_runtime(self):
        windows = json.loads(WINDOWS.read_text())
        ubuntu = json.loads(UBUNTU.read_text())
        self.assertEqual(windows["schema"], 2)
        self.assertEqual(ubuntu["schema"], 2)
        self.assertEqual(windows["disk"], "Windows11.raw")
        self.assertEqual(ubuntu["disk"], "Ubuntu.raw")
        self.assertEqual(windows["disk_gib"], 160)
        self.assertTrue(windows["native_capable"])
        self.assertFalse(ubuntu["native_capable"])
        self.assertEqual(windows["network"], "e1000e")
        self.assertEqual(ubuntu["network"], "virtio-net-pci")

    def test_near_native_path_is_explicit_and_has_direct_recovery(self):
        source = RUNTIME.read_text()
        for value in (
            '"-cpu", "host,topoext=on,hv_relaxed,hv_vapic,hv_spinlocks=0x1fff,hv_time"',
            '"-device", "vfio-pci,host=01:00.0,multifunction=on,x-vga=on"',
            '"-device", "vfio-pci,host=01:00.1"',
            '"cache=none", "aio=native"',
            '"-device", "ivshmem-plain,id=shmem0,memdev=looking-glass"',
            '"app:allowDMA=yes"',
            '"input:rawMouse=yes"',
            '"-display", "none"',
            '"-display", "gtk,zoom-to-fit=on,grab-on-hover=on,show-tabs=off"',
            'choices=(DIRECT, NATIVE)',
        ):
            self.assertIn(value, source)
        self.assertNotIn('"-overcommit", "mem-lock=on"', source)
        self.assertNotIn("grab-on-hover=off", source)
        self.assertNotIn("usb-tablet", source)

    def test_qemu_failure_surfaces_the_last_qemu_diagnostic(self):
        runtime = load_runtime()
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "launcher.log"
            log.write_text(
                "=== APX VM v2 old ===\nqemu-system-x86_64: old failure\n"
                "=== APX VM v2 current ===\n"
                "qemu-system-x86_64: mlockall: Operation not permitted\n"
                "qemu-system-x86_64: locking memory failed\n"
                "swtpm: unrelated shutdown line\n"
            )
            with mock.patch.object(runtime, "LOG", log):
                error = runtime.qemu_failure(1)
        self.assertEqual(str(error), "QEMU terminou com estado 1: locking memory failed")

    def test_existing_qcow2_is_preserved_as_a_compatibility_disk(self):
        runtime = load_runtime()
        with self.subTest("source contract"):
            source = RUNTIME.read_text()
            self.assertIn('if legacy.exists():', source)
            self.assertIn('return legacy, "qcow2", ["cache=writeback", "aio=threads"]', source)
            self.assertNotIn("qemu-img convert", source)
            self.assertNotIn("unlink()", source.split("def existing_disk", 1)[1].split("def qemu_command", 1)[0])

    def test_vm_surface_keeps_host_owned_recovery_shortcuts(self):
        source = HYPRLAND.read_text()
        self.assertIn('hl.exec_cmd("/home/apx/.local/bin/apx-system-vm")', source)
        self.assertIn('hl.bind("SUPER + E", hl.dsp.exit())', source)
        self.assertIn('hl.bind("SUPER + M", hl.dsp.exit())', source)
        self.assertIn('" --set-presentation-and-exit direct"', source)
        self.assertIn('" --set-presentation-and-exit native"', source)
        self.assertIn('no_shortcuts_inhibit = true', source)
        self.assertIn('animations = { enabled = false }', source)
        self.assertNotIn("quickshell", source.lower())

    def test_provisioner_installs_v2_once_and_prepares_raw_btrfs_storage(self):
        source = PROVISIONER.read_text()
        compile(source, str(PROVISIONER), "exec")
        self.assertIn('system-environment-template-v2', source)
        self.assertIn('home / ".local/bin/apx-system-vm"', source)
        self.assertIn('home / ".config/apx/system-vm-v2.json"', source)
        self.assertIn('"/usr/bin/chattr", "+C", str(vm_dir)', source)
        self.assertIn('def user_directory(path: Path, mode: int = 0o700)', source)
        self.assertIn('home / ".config/apx"', source)
        self.assertIn('os.chown(path, 1000, 1000)', source)
        self.assertIn('os.chmod(path, mode)', source)
        self.assertNotIn('home / f".config/autostart/', source)
        self.assertNotIn('home / ".local/bin/apx-vm-environment-menu-v1"', source)
        vfio = json.loads(VFIO.read_text())
        self.assertEqual(vfio["profile"], "apx-vfio-pci-v1")
        self.assertEqual(vfio["group"], 11)
        self.assertIn('config/environment-vm-v2/vfio-pci-v1.json', DEPLOY.read_text())

    def test_windows_guest_setup_explains_the_deterministic_mode_change(self):
        source = ACCELERATOR.read_text()
        self.assertIn("looking-glass-idd-setup.exe\" /S", source)
        self.assertIn("looking-glass-host-setup.exe\" /S", source)
        self.assertIn("SUPER+SHIFT+N", source)
        self.assertIn("SUPER+SHIFT+R", source)
        self.assertIn("choice /C RN /N", source)
        tuner = DISPLAY_TUNER.read_text()
        self.assertIn("[ApxDisplayMode]::Configure()", tuner)
        self.assertIn("dmDisplayFrequency == 120", tuner)
        self.assertIn("looking-glass-display.txt", tuner)
        readme = README.read_text()
        self.assertIn("não muda de fonte de vídeo durante uma sessão", readme)
        self.assertIn("KVMFR/RTX desde o arranque", readme)

    def test_physical_adapter_is_offline_target_bound_and_content_preserving(self):
        source = DEPLOY.read_text()
        for value in (
            "profile=apx-physical-headless-pilot-v1",
            "Lenovo identity differs",
            "the Hub is not the only active machine",
            "QEMU is active",
            "Looking Glass is active",
            "VFIO is active",
            "registration.get(\"state\") != \"stopped\"",
            "repository tests failed",
            "before.sha256",
            "after.sha256",
            "20260824-system-vm-v2-v20",
            "installation failed; exact previous files were restored",
            "installed without starting a VM",
        ):
            self.assertIn(value, source)
        self.assertNotIn("qemu-system-x86_64", source)
        self.assertNotIn("machinectl start", source)


if __name__ == "__main__":
    unittest.main()
