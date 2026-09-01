import json
import stat
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ApxModelStorePhysicalTests(unittest.TestCase):
    def test_installed_entrypoint_sources_are_executable(self):
        for relative in (
            "scripts/physical-pilot/apx-model-store-v1.py",
            "scripts/physical-pilot/apx-model-store-recover-v1.py",
            "scripts/physical-pilot/apx-model-store-control-v1.py",
            "scripts/physical-pilot/apx-model-store-client-v1.py",
            "scripts/physical-pilot/apx-ollama-warmup-v1.py",
            "scripts/physical-pilot/apx-local-code-v1.sh",
        ):
            mode = stat.S_IMODE((ROOT / relative).stat().st_mode)
            self.assertEqual(mode, 0o755, relative)

    def test_adapter_is_bound_to_every_storage_identity(self):
        source = (ROOT / "scripts/physical-pilot/apx-model-store-v1.py").read_text()
        for value in (
            "Samsung_SSD_870_QVO_1TB",
            "S5SVNF0R241427A",
            "c8806268-9695-4d52-9136-6f278b95c2e4",
            "f0ca74a0-90d1-408c-8f01-0668ce554a17",
            "b94ab3ad-f41f-4eae-b663-78789ce3ba52",
        ):
            self.assertIn(value, source)
        self.assertIn('"type": "crypto_LUKS"', source)
        self.assertIn('"TYPE") != "btrfs"', source)

    def test_udev_rule_and_service_use_the_exact_device(self):
        rule = (ROOT / "config/udev/99-apx-model-store-v1.rules").read_text()
        unit = (ROOT / "config/systemd/apx-model-store-v1.service").read_text()
        self.assertIn('ENV{ID_SERIAL_SHORT}=="S5SVNF0R241427A"', rule)
        self.assertIn('ENV{ID_PART_ENTRY_UUID}=="c8806268-9695-4d52-9136-6f278b95c2e4"', rule)
        self.assertIn("BindsTo=dev-disk-by\\x2did-ata", unit)
        self.assertNotIn("Wants=apx-ollama-v1.service", unit)
        self.assertIn("apx-model-store-recover-v1.service", rule)
        self.assertNotIn('SYSTEMD_WANTS}+="apx-model-store-v1.service', rule)

    def test_attachment_recovery_clears_failed_units_and_orders_startup(self):
        recovery = (ROOT / "scripts/physical-pilot/apx-model-store-recover-v1.py").read_text()
        unit = (ROOT / "config/systemd/apx-model-store-recover-v1.service").read_text()
        self.assertIn('"reset-failed", STORE_UNIT, OLLAMA_UNIT', recovery)
        self.assertIn("timeout=15, check=False", recovery)
        self.assertLess(
            recovery.index('"start", STORE_UNIT'),
            recovery.index('"start", OLLAMA_UNIT'),
        )
        self.assertIn('"start", OLLAMA_UNIT, timeout=300, check=False', recovery)
        self.assertIn('"is-active", "--quiet", OLLAMA_UNIT', recovery)
        self.assertIn("Do not reset Ollama here", recovery)
        self.assertIn("BindsTo=dev-disk-by\\x2did-ata", unit)
        self.assertIn("TimeoutStartSec=360", unit)

    def test_model_server_is_loopback_only_and_part_of_storage_lifecycle(self):
        unit = (ROOT / "config/systemd/apx-ollama-v1.service").read_text()
        self.assertIn('OLLAMA_HOST=127.0.0.1:11434', unit)
        self.assertIn('OLLAMA_MODELS=/var/lib/apx/model-store/ollama', unit)
        self.assertIn('OLLAMA_NO_CLOUD=true', unit)
        self.assertIn('OLLAMA_GPU_OVERHEAD=1073741824', unit)
        self.assertIn("After=apx-model-store-v1.service network.target systemd-modules-load.service", unit)
        self.assertIn("ExecStartPre=-+/usr/bin/nvidia-modprobe -c0 -u", unit)
        self.assertIn("ExecStartPre=-/usr/bin/nvidia-smi --query-gpu=name --format=csv,noheader", unit)
        self.assertNotIn("ExecCondition=", unit)
        self.assertIn("RestartPreventExitStatus=1\n", unit)
        self.assertIn("PartOf=apx-model-store-v1.service", unit)
        self.assertIn("NoNewPrivileges=yes", unit)
        self.assertIn("ReadOnlyPaths=/var/lib/apx/model-store/ollama", unit)
        self.assertNotIn('OLLAMA_VULKAN=false', unit)

    def test_nvidia_cuda_boot_path_is_signed_and_excludes_nouveau(self):
        dkms = (ROOT / "config/dkms/apx-secure-boot-v1.conf").read_text()
        modprobe = (ROOT / "config/modprobe.d/apx-nvidia-v1.conf").read_text()
        mkinitcpio = (ROOT / "config/mkinitcpio/apx-nvidia-v1.conf").read_text()
        self.assertIn('try_sign_modules="true"', dkms)
        self.assertIn("/etc/kernel/secure-boot-private-key.pem", dkms)
        self.assertIn("blacklist nouveau", modprobe)
        self.assertIn("options nvidia_drm modeset=1 fbdev=1", modprobe)
        self.assertIn("MODULES=(amdgpu nvidia nvidia_modeset nvidia_uvm nvidia_drm)", mkinitcpio)
        self.assertNotIn(" kms ", mkinitcpio)

    def test_model_selection_state_is_created_with_root_only_write_access(self):
        tmpfiles = (ROOT / "config/tmpfiles.d/apx.conf").read_text()
        controller_unit = (ROOT / "config/systemd/apx-model-store-control-v1.service").read_text()
        self.assertIn("d /var/lib/apx/model-selection-v1 0755 root root -", tmpfiles)
        self.assertIn("f /var/lib/apx/model-selection-v1/selected 0644 root root - fast", tmpfiles)
        self.assertIn("ReadWritePaths=/var/lib/apx/model-selection-v1", controller_unit)

    def test_normal_model_store_mount_is_read_only_and_hidden_when_absent(self):
        source = (ROOT / "scripts/physical-pilot/apx-model-store-v1.py").read_text()
        self.assertIn('"-o", "ro,nosuid,nodev,noexec,noatime', source)
        self.assertIn('os.chmod(MOUNTPOINT, 0o000)', source)
        self.assertIn('"read_only": "ro" in mount_options()', source)

    def test_hub_controller_is_narrow_authenticated_and_requires_confirmation(self):
        server = (ROOT / "scripts/physical-pilot/apx-model-store-control-v1.py").read_text()
        client = (ROOT / "scripts/physical-pilot/apx-model-store-client-v1.py").read_text()
        launcher = (ROOT / "scripts/physical-pilot/apx-official-hub-graphical-v1.py").read_text()
        self.assertIn("authorize_official_hub_peer", server)
        self.assertIn('HOST_MOUNT_NS = ("/usr/bin/nsenter", "--target", "1", "--mount", "--")', server)
        self.assertIn("run(*HOST_MOUNT_NS, ADAPTER, \"status\"", server)
        self.assertIn("reset_failed(STORE_UNIT, OLLAMA_UNIT)", server)
        self.assertIn("reset_failed(OLLAMA_UNIT)", server)
        self.assertIn("timeout=300", server)
        self.assertIn("connection.settimeout(330)", client)
        self.assertIn("for endpoint in (PRIMARY_SOCKET, LIVE_SOCKET)", client)
        self.assertIn("except OSError as error", client)
        self.assertIn("LIVE_SOCKET", server)
        self.assertIn(".apx-host-bridge/model-store-control-v1.sock", client)
        self.assertIn('payload != {"confirmation": "REMOVER COM SEGURANÇA"}', server)
        for operation in ("model-start", "model-stop", "model-select", "storage-activate", "safe-detach"):
            self.assertIn(operation, client)
        self.assertIn('"fast": {', server)
        self.assertIn('"balanced": {', server)
        self.assertIn('"quality": {', server)
        self.assertIn('payload["confirmation"] != "SELECIONAR MODELO"', server)
        self.assertIn("MODEL_STORE_SOCKET", launcher)
        self.assertIn("model-store-client-v1.py", launcher)

    def test_hub_exposes_confirmed_safe_detach_control(self):
        qml = (ROOT / ".apx-live-shell-bluetooth-v1.qml").read_text()
        for required in (
            "modelStoreButton", "[ IA ON ]", "[ SSD OK ]",
            "DESATIVAR MODELO", "DESMONTAR SSD", "CONFIRMAR DESMONTAR",
            "SELECIONAR MODELO", 'root.modelStoreAction("model-select", modelData.profile)',
            'root.modelStoreAction("safe-detach")',
        ):
            self.assertIn(required, qml)

    def test_model_switch_reports_progress_without_moving_the_selector(self):
        controller = (ROOT / "scripts/physical-pilot/apx-model-store-control-v1.py").read_text()
        qml = (ROOT / ".apx-live-shell-bluetooth-v1.qml").read_text()
        for required in (
            '"model_transition": True',
            '"transition_progress": progress',
            'set_transition(requested, "loading")',
            "threading.Thread(",
        ):
            self.assertIn(required, controller)
        for required in (
            "A LIGAR AO NOVO MODELO",
            "modelSwitchProgress",
            "modelSelectorRow.cellWidth",
            "root.modelStoreBusy ? 500 : 5000",
        ):
            self.assertIn(required, qml)

    def test_qwen_code_defaults_select_the_local_model(self):
        settings = json.loads(
            (ROOT / "config/qwen-code/apx-local-coder-v1.json").read_text()
        )
        provider = settings["modelProviders"]["openai"][0]
        self.assertEqual(settings["model"]["name"], "qwen2.5-coder:3b")
        self.assertEqual(provider["baseUrl"], "http://127.0.0.1:11434/v1")
        self.assertEqual(provider["generationConfig"]["contextWindowSize"], 8192)
        self.assertFalse(settings["privacy"]["usageStatisticsEnabled"])

    def test_local_agent_wrapper_never_enables_unrestricted_mode(self):
        wrapper = (ROOT / "scripts/physical-pilot/apx-local-code-v1.sh").read_text()
        self.assertIn("apx-ollama-v1.service", wrapper)
        self.assertIn("-y|--yolo", wrapper)
        self.assertIn("--approval-mode default", wrapper)
        self.assertIn("OPENAI_BASE_URL=http://127.0.0.1:11434/v1", wrapper)
        self.assertIn("QWEN_CODE_API_TIMEOUT_MS=600000", wrapper)
        self.assertIn("--auth-type openai", wrapper)
        self.assertIn("cd /root", wrapper)
        self.assertIn("--bare", wrapper)
        self.assertIn("agente local de programação APX", wrapper)
        self.assertIn('model="qwen2.5-coder:3b"', wrapper)
        self.assertIn('model="qwen3-coder:30b"', wrapper)
        self.assertIn('[[ ${1:-} == "--quality" ]]', wrapper)
        self.assertIn("Não leias ficheiros extensos por inteiro", wrapper)

    def test_model_is_preloaded_and_retained_only_while_service_is_active(self):
        unit = (ROOT / "config/systemd/apx-ollama-v1.service").read_text()
        warmup = (ROOT / "scripts/physical-pilot/apx-ollama-warmup-v1.py").read_text()
        self.assertIn("ExecStartPost=/usr/lib/apx/apx-ollama-warmup-v1.py", unit)
        self.assertIn('OLLAMA_KEEP_ALIVE=-1', unit)
        self.assertIn('"fast": "qwen2.5-coder:3b"', warmup)
        self.assertIn('"balanced": "qwen2.5-coder:7b"', warmup)
        self.assertIn('"quality": "qwen3-coder:30b"', warmup)
        self.assertIn("selected_model()", warmup)
        self.assertIn('"keep_alive": -1', warmup)
        self.assertIn('"num_ctx": 8192', warmup)


if __name__ == "__main__":
    unittest.main()
