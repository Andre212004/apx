from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "scripts/physical-pilot/apx-graphical-environment-v1.py"


class GraphicalEnvironmentLauncherTests(unittest.TestCase):
    def test_launcher_reuses_proven_engine_without_merging_homes(self):
        source = LAUNCHER.read_text()
        compile(source, str(LAUNCHER), "exec")
        for value in (
            'record.get("role") != "graphical-base"',
            'record.get("release") != "hyprland-base-v2"',
            'engine.HOME = environment / "home"',
            'engine.CONFIG = engine.HOME / "apx/.config/hyprland/hyprland.conf"',
            "APX_HYPRLAND_CONFIG=/home/apx/.config/hypr/hyprland.lua",
            "APX_GPU_POLICY", "APX_DISPLAY_CARD", "APX_DISPLAY_RENDER",
            "APX_NVIDIA_CARD_DEVICE",
            "graphics['offload_render']",
            "apx-active-graphical-environment-v1",
            "engine.launch(args.test, args.authenticated_handoff)",
            'engine.HOME / "apx/.config/quickshell/apx/shell.qml"',
            '"desktop_shell": "virtual-machine" if',
            '"quickshell": not',
            '"/home/apx/.local/bin/apx-shell-v1"',
            'engine.compositor_state()',
            '"dispatch", "exec"',
            'KVM_CAPABILITY_NAME = "kvm-v1"',
            'engine.EXTRA_DEVICE_NODES = ("/dev/kvm",)',
            'stat.S_IMODE(metadata.st_mode) != 0o400',
            'VM_CAPABILITY_NAME = "virtual-machine-v1"',
            'VM_CAPABILITY_CONTENT = b"apx-virtual-machine-v1\\n"',
            'APX_SESSION_MODE=',
            'return "virtual-machine"',
            'deadline = time.monotonic() + 10',
            'VFIO_CAPABILITY_NAME = "vfio-pci-v1.json"',
            'engine.VFIO_GUEST_MODE = vfio_capability is not None',
            'activate_vfio(vfio_capability)',
            'restore_vfio()',
            '"/dev/vfio/vfio", "/dev/vfio/11"',
            'nodes.append("/dev/kvmfr0")',
            "Path(__file__).resolve() == GENERIC_INSTALLED",
            "engine.HOST_SERVICES_ENABLED = False",
            "engine.AUDIO_STATE_ENABLED = False",
            "engine.MODEL_STORE_ENABLED = False",
            "engine.LEASED_SERVICE_SOCKETS = (engine.ENVIRONMENT_SWITCH_SOCKET,)",
            "VM_FORBIDDEN_PROCESSES = (",
            'b"pipewire-pulse", b"xdg-desktop-por"',
            '"the minimal VM session started forbidden desktop services: "',
            'arguments.append(f"--property=LimitMEMLOCK={engine.VFIO_MEMLOCK_LIMIT}")',
            'engine.HUB_CPU_QUOTA = "1200%"',
            'engine.HUB_MEMORY_HIGH = "24G"',
            'engine.HUB_MEMORY_MAX = "26G"',
            'engine.VFIO_MEMLOCK_LIMIT = "24G"',
            'The v2 VM has no second readiness protocol',
            '"the VM owner compositor is not active"',
            'engine.before_publish_stopped = restore_vfio',
        ):
            self.assertIn(value, source)

    def test_launcher_does_not_claim_new_watchdog_or_recovery(self):
        source = LAUNCHER.read_text()
        self.assertIn("No new recovery/watchdog mechanism", source)
        self.assertNotIn('mode.add_argument("--watchdog"', source)

    def test_vm_presentation_uses_the_owner_session_without_marker_rediscovery(self):
        source = LAUNCHER.read_text()
        self.assertIn('return "virtual-machine"', source)
        self.assertIn('len(process_pids(b"Hyprland")) != 1', source)
        self.assertNotIn('VM_READY_RELATIVE', source)
        self.assertNotIn('VM_PRESENTATION_READY_RELATIVE', source)
        self.assertNotIn('executable_pids', source)

        vm_launcher = (
            ROOT / "config/environment-vm-v2/local/bin/apx-vm-runtime-v2"
        ).read_text()
        self.assertIn('client = subprocess.Popen(native_client', vm_launcher)
        self.assertIn('stop(client); stop(qemu); stop(swtpm)', vm_launcher)
        self.assertNotIn("query-spice", vm_launcher)
        self.assertNotIn("presentation-ready", vm_launcher)


if __name__ == "__main__":
    unittest.main()
