import importlib.util
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "scripts/physical-pilot/apx-official-hub-graphical-v1.py"
SESSION = ROOT / "scripts/physical-pilot/apx-official-hub-session-v1.sh"


def load_launcher():
    spec = importlib.util.spec_from_file_location("official_hub_graphical", LAUNCHER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class OfficialHubGraphicalTests(unittest.TestCase):
    def test_launcher_binds_current_hub_identity_and_recovers(self) -> None:
        source = LAUNCHER.read_text()
        compile(source, str(LAUNCHER), "exec")
        for required in (
            "6f63f9a9-daea-40d1-969f-e25ff0752f4d",
            'RELEASE = "hub-headless-v4"', "--recover", "finally:", "recover()",
            "apx-official-hub-graphical-expiry", 'run(("chvt", "1"), False)',
            "apx-official-hub-graphical-watchdog", "arm_health_watchdog",
            "health_watchdog", 'mode.add_argument("--watchdog"',
            '"--on-unit-active=30s"', '"classification": "healthy"',
            '"remove", "--environment", "hub"', "Super+Q", "Super+M",
            "open_and_verify_kitty", "Kitty did not create a Hyprland window",
            "verify_desktop_shell", 'process_pids(b"quickshell")',
            '"--private-users=pick"', '"--private-users-ownership=chown"',
            'f"--bind={HOME}:/home:idmap"', "resolve_user_namespace",
            "prepare_device_leases", "activate_device_leases", "cleanup_device_leases",
            "official-hub-recovery-v1.lock", "fcntl.flock(descriptor, fcntl.LOCK_EX)",
            "os.mknod", "start_host_seatd", '"--property=DevicePolicy=closed"',
            '"/usr/bin/seatd", "-u", "root"', "verify_local_admin",
            '"private_users": True', '"local_admin": True',
            "HOST_SERVICES_SOCKET", "HOST_SERVICES_CLIENT", "HOST_SERVICES_CONTRACT",
            "read-only Host-services bundle is unavailable",
            'f"--bind={HOST_SERVICES_SOCKET}:{HOST_SERVICES_SOCKET}"',
            "HOST_SERVICES_V2_SOCKET", "DESKTOP_MENU_V2", "verify_host_services_v2",
            'f"--bind={HOST_SERVICES_V2_SOCKET}:{HOST_SERVICES_V2_SOCKET}"',
            "publish_active_state", "host_services_call", "verify_host_services", '"--uid=apx"',
            '"host_services": True', '"network_backend"', '"ntp_enabled"',
            '"bluetooth_toggle": True', "Bluetooth Host state recovery failed",
            '"--property=TimeoutStopSec=3s"', 'process_pids(b"Hyprland")',
            'root/etc/apx/official-hub-base-v1',
            'kitty --directory /home/apx /usr/bin/nice -n 10',
            '/usr/bin/ionice -c 3 /usr/bin/bash',
            "if test_mode:\n            verify_update_and_audio_services()",
        ):
            self.assertIn(required, source)

    def test_interactive_launch_does_not_run_mutating_certification_proofs(self) -> None:
        source = LAUNCHER.read_text()
        proof_block = (
            "if test_mode:\n"
            "            verify_update_and_audio_services()\n"
            "            host_services = verify_host_services()\n"
            "            host_services_v2 = verify_host_services_v2()\n"
            "            host_services_v3 = verify_host_services_v3()\n"
            "            nvidia_device = verify_nvidia_render(pid)"
        )
        self.assertIn(proof_block, source)
        certification = source.index("if test_mode:\n            verify_update_and_audio_services")
        automatic_terminal = source.rindex("if test_mode:\n            open_and_verify_kitty(pid, signature)")
        self.assertLess(certification, automatic_terminal)
        self.assertEqual(source.count("open_and_verify_kitty(pid, signature)"), 1)

    def test_launcher_admits_only_fixed_internal_devices(self) -> None:
        source = LAUNCHER.read_text()
        for required in (
            "platform-i8042-serio-0", "pci-0000:05:00.3-usb-0:4:1.0",
            '"048d"', '"c101"', "platform-AMDI0010:01",
            "DevicePolicy=closed", 'AMD_PCI = "0000:05:00.0"', "/dev/tty2",
            'NVIDIA_PCI = "0000:01:00.0"', "resolve_drm_device", "effective_gpu_policy",
            "APX_NVIDIA_CARD_DEVICE", "APX_NVIDIA_RENDER_DEVICE",
            "offload_card", "verify_nvidia_render", '"DRI_PRIME=1!"',
            "resolve_nvidia_auxiliary_devices", '"/dev/nvidia0"',
            '"/dev/nvidiactl"', '"/dev/nvidia-modeset"',
            'HOST_SERVICES_UI_V3 = Path("/usr/lib/apx/apx-host-services-ui-v3.py")',
            'BRIGHTNESS_KEYS = Path("/usr/lib/apx/apx-legion-brightness-keys-v1.py")',
        ):
            self.assertIn(required, source)
        for fixed_event in ("/dev/input/event3", "/dev/input/event5", "/dev/input/event9"):
            self.assertNotIn(fixed_event, source)

    def test_hybrid_graphics_exposes_both_display_cards_with_amd_primary(self) -> None:
        subject = load_launcher()
        def resolved(pci: str, kind: str, _vendor: str, _device: str) -> str:
            card = "2" if pci == subject.AMD_PCI else "1"
            return f"/dev/dri/card{card}" if kind == "card" else f"/dev/dri/renderD{128 if card == '1' else 129}"
        with mock.patch.object(subject, "effective_gpu_policy", return_value="hybrid"), \
                mock.patch.object(subject, "resolve_drm_device", side_effect=resolved), \
                mock.patch.object(subject, "resolve_nvidia_auxiliary_devices", return_value={
                    "nvidia_device": "/dev/nvidia0",
                    "nvidia_control": "/dev/nvidiactl",
                    "nvidia_modeset": "/dev/nvidia-modeset",
                }):
            self.assertEqual(subject.resolve_graphics(), {
                "policy": "hybrid",
                "display_card": "/dev/dri/card2",
                "display_render": "/dev/dri/renderD129",
                "offload_card": "/dev/dri/card1",
                "offload_render": "/dev/dri/renderD128",
                "nvidia_device": "/dev/nvidia0",
                "nvidia_control": "/dev/nvidiactl",
                "nvidia_modeset": "/dev/nvidia-modeset",
            })

    def test_launcher_leases_only_internal_analog_playback_and_capture_audio(self) -> None:
        source = LAUNCHER.read_text()
        for required in (
            'AUDIO_ID_PATH = "pci-0000:05:00.6"', "resolve_audio_devices",
            '"audio_control"', '"audio_playback"', '"audio_capture"', '"audio_timer"',
            'r"/dev/snd/pcmC[0-9]+D0p"', 'r"/dev/snd/pcmC[0-9]+D0c"',
            "verify_audio_playback", '"wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"',
            '"wpctl", "get-volume", "@DEFAULT_AUDIO_SOURCE@"', 'glob("pcm*C*c")',
        ):
            self.assertIn(required, source)
        for forbidden in ('"--bind=/dev/snd"', '"--property=DeviceAllow=/dev/snd rw"'):
            self.assertNotIn(forbidden, source)

    def test_session_runs_owner_config_as_apx_not_root(self) -> None:
        source = SESSION.read_text()
        for required in (
            "/home/apx/.config/hypr/hyprland.lua", "/usr/bin/start-hyprland",
            "--reuid=1000", "--regid=1000", "--inh-caps=-all", "--ambient-caps=-all",
            "LIBSEAT_BACKEND=seatd", 'AQ_DRM_DEVICES="$drm_devices"',
            "RUNTIME=/run/apx/session-1000",
            "APX_GPU_POLICY", "APX_DISPLAY_CARD", "APX_DISPLAY_RENDER",
            'drm_devices="$DISPLAY_CARD:$NVIDIA_CARD"',
            "APX_KEYBOARD_I8042_DEVICE", "APX_KEYBOARD_ITE_DEVICE",
            "cd -- /home/apx", "--groups=5,983,987,992,995,998",
        ):
            self.assertIn(required, source)
        self.assertNotIn("sudo", source)
        self.assertNotIn("/usr/bin/seatd", source)
        self.assertNotIn("--bounding-set=-all", source)
        self.assertNotIn("--no-new-privs --inh-caps=-all", source)
        self.assertNotIn("LIBGL_DEBUG", source)
        self.assertNotIn("verify_render_device_access", source)

    def test_session_ipc_runtime_is_not_owned_by_transient_logind_sessions(self) -> None:
        launcher = LAUNCHER.read_text()
        session = SESSION.read_text()
        self.assertIn('SESSION_RUNTIME = "/run/apx/session-1000"', launcher)
        self.assertIn('readonly RUNTIME=/run/apx/session-1000', session)
        self.assertNotIn('readonly RUNTIME=/run/user/1000', session)

    def test_interactive_watchdog_is_health_based_not_wall_clock_expiry(self) -> None:
        source = LAUNCHER.read_text()
        self.assertNotIn("14400", source)
        self.assertIn("arm_test_expiry(75) if test_mode else arm_health_watchdog()", source)
        self.assertIn("A transient compositor/IPC observation must never end", source)
        self.assertNotIn('"classification": "recovered"', source)
        self.assertIn('"--property=ReadWritePaths=/run/seatd.sock"', source)
        self.assertIn("def unlink_if_present(path: Path)", source)
        self.assertIn("unlink_if_present(SEATD_SOCKET)", source)

    def test_health_watchdog_keeps_a_responsive_session(self) -> None:
        subject = load_launcher()
        with tempfile.TemporaryDirectory() as directory, \
                mock.patch.object(subject, "WATCHDOG_STATE", Path(directory) / "watchdog.json"), \
                mock.patch.object(subject, "ACTIVE", Path(directory) / "active.json"), \
                mock.patch.object(subject, "unit_active", return_value=True), \
                mock.patch.object(subject, "machine_running", return_value=True), \
                mock.patch.object(subject, "read_registration", return_value={"state": "running"}), \
                mock.patch.object(subject, "compositor_state", return_value=(42, "signature", True, ("kbd",))), \
                mock.patch.object(subject, "run", return_value=SimpleNamespace(returncode=0)):
            subject.ACTIVE.write_text(
                '{"profile":"apx-official-hub-graphical-v1",'
                f'"generation":"{subject.GENERATION}",'
                f'"unit":"{subject.OUTER_UNIT}.service","pid":42}}\n'
            )
            self.assertEqual(subject.health_watchdog(), {
                "classification": "healthy", "recovered": False,
            })

    def test_process_discovery_is_scoped_to_the_official_hub_unit(self) -> None:
        subject = load_launcher()
        with tempfile.TemporaryDirectory() as directory:
            proc = Path(directory)
            unit_path = f"/system.slice/{subject.OUTER_UNIT}.service"
            for pid, cgroup in (("41", unit_path + "/container"),
                                ("42", "/system.slice/systemd-nspawn@test.service")):
                entry = proc / pid
                (entry / "root/etc/apx").mkdir(parents=True)
                (entry / "root/etc/apx/official-hub-base-v1").write_text("\n")
                (entry / "comm").write_bytes(b"Hyprland\n")
                (entry / "cgroup").write_text(f"0::{cgroup}\n")
            self.assertEqual(subject.process_pids(b"Hyprland", proc), [41])

    def test_health_watchdog_reports_degradation_without_ending_session(self) -> None:
        subject = load_launcher()
        with tempfile.TemporaryDirectory() as directory, \
                mock.patch.object(subject, "WATCHDOG_STATE", Path(directory) / "watchdog.json"), \
                mock.patch.object(subject, "ACTIVE", Path(directory) / "absent-active.json"), \
                mock.patch.object(subject, "unit_active", return_value=True), \
                mock.patch.object(subject, "machine_running", return_value=True), \
                mock.patch.object(subject, "recover") as recover:
            self.assertEqual(subject.health_watchdog()["failures"], 1)
            self.assertEqual(subject.health_watchdog()["failures"], 2)
            self.assertEqual(subject.health_watchdog()["classification"], "degraded")
            self.assertEqual(subject.health_watchdog()["failures"], 2)
            recover.assert_not_called()

    def test_session_starts_environment_local_audio_stack_and_state_watcher(self) -> None:
        source = SESSION.read_text()
        for required in (
            "APX_AUDIO_CONTROL_DEVICE", "APX_AUDIO_PLAYBACK_DEVICE", "APX_AUDIO_CAPTURE_DEVICE",
            "APX_AUDIO_TIMER_DEVICE", "/usr/bin/pipewire",
            "/usr/bin/wireplumber", "/usr/bin/pipewire-pulse",
            "$RUNTIME/pulse/native", "--groups=5,983,987,992,995", "audio-state-client-v1.py watch",
        ):
            self.assertIn(required, source)


if __name__ == "__main__":
    unittest.main()
