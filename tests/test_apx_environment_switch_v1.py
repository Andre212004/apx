from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "src/apx_environment_switch_contract.py"
SERVICE = ROOT / "scripts/physical-pilot/apx-environment-switch-v1.py"
RUNNER = ROOT / "scripts/physical-pilot/apx-environment-switch-runner-v1.py"
MANAGEMENT_RUNNER = ROOT / "scripts/physical-pilot/apx-environment-management-runner-v1.py"
LAUNCHER = ROOT / "scripts/physical-pilot/apx-official-hub-graphical-v1.py"
GENERAL = ROOT / "scripts/physical-pilot/apx-graphical-environment-v1.py"
RED_SHELL = ROOT / "config/quickshell-workload-red-v1/shell.qml"
RED_HYPRLAND = ROOT / "config/quickshell-workload-red-v1/hyprland.conf"
SWITCH_UNIT = ROOT / "config/systemd/apx-environment-switch-v1.service"
EXECUTOR_UNIT = ROOT / "config/systemd/apx-executor-v1.service"
TMPFILES = ROOT / "config/tmpfiles.d/apx.conf"


def load_contract():
    spec = importlib.util.spec_from_file_location("switch_contract", CONTRACT)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def load_runner():
    spec = importlib.util.spec_from_file_location("switch_runner", RUNNER)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


class EnvironmentSwitchV1Tests(unittest.TestCase):
    def test_shared_runtime_directory_is_not_owned_by_one_service(self) -> None:
        self.assertIn("d /run/apx 0755 root root -", TMPFILES.read_text())
        for unit in (SWITCH_UNIT, EXECUTOR_UNIT):
            source = unit.read_text()
            self.assertNotIn("RuntimeDirectory=apx", source)
            self.assertIn("ReadWritePaths=/run/apx", source)

    def test_contract_accepts_catalog_identity_and_typed_target(self) -> None:
        subject = load_contract()
        for operation in ("catalog.get", "identity.get", "status.get", "management.status", "return.to-hub"):
            self.assertEqual(subject.parse_message(subject.request_bytes(operation))["operation"], operation)
        request = subject.request_bytes("switch.to-workload", "faculdade")
        self.assertEqual(subject.parse_message(request)["payload"], {"target": "faculdade"})
        creation = subject.request_bytes("environment.create", "faculdade", description="Estudo e aulas")
        creation_payload = subject.parse_message(creation)["payload"]
        self.assertEqual(creation_payload["description"], "Estudo e aulas")
        self.assertEqual(creation_payload["target"], "faculdade")
        self.assertEqual(creation_payload["preset"], "intermediate")
        self.assertEqual(len(creation_payload["modules"]), 15)
        generation = "12345678-1234-1234-1234-123456789abc"
        destruction = subject.request_bytes("environment.destroy", "faculdade", generation)
        self.assertEqual(subject.parse_message(destruction)["payload"]["generation"], generation)
        with self.assertRaises(ValueError):
            subject.request_bytes("run.command")
        with self.assertRaises(ValueError):
            subject.request_bytes("environment.create", "faculdade", description="linha\nnova")
        malformed = json.dumps({"schema": 1, "profile": subject.PROFILE,
                                "operation": "switch.to-workload", "payload": {"target": "../other"}}).encode() + b"\n"
        with self.assertRaises(ValueError):
            subject.parse_message(malformed)

    def test_service_catalogues_trusted_workloads_and_scopes_hub_to_quickshell(self) -> None:
        source = SERVICE.read_text()
        self.assertIn('ENVIRONMENTS = Path("/var/lib/apx/environments")', source)
        self.assertIn('LIVE_SOCKET = Path("/var/lib/apx/environments/hub/home/.apx-host-bridge/environment-switch-v1.sock")', source)
        self.assertIn("select.select(servers", source)
        self.assertIn('directory.name == "hub"', source)
        self.assertIn('"catalog.get"', source)
        self.assertIn('"identity.get"', source)
        self.assertIn('comm != "quickshell"', source)
        self.assertEqual(source.count("quickshell_parent(peer.pid"), 2)
        self.assertIn("authorize_official_hub_peer(peer)", source)
        self.assertIn("authorize_active_environment_peer(peer)", source)
        self.assertIn("environment-aware QuickShell", source)
        self.assertIn('name, "graphical-base", "hyprland-base-v2"', source)
        self.assertIn("def completed_destroy(", source)
        management_source = MANAGEMENT_RUNNER.read_text()
        self.assertIn("def recover_failed_create(", management_source)
        self.assertIn('"recovery-clean-unpublished", target', management_source)
        self.assertIn('write_state(action, target, "planning", 4', management_source)
        self.assertIn('"already_complete": True', source)
        self.assertNotIn("shell=True", source)

    def test_client_presents_contextual_hub_and_workload_actions(self) -> None:
        source = (ROOT / "scripts/physical-pilot/apx-environment-switch-client-v1.py").read_text()
        self.assertIn("[ APX · HUB · ENVIRONMENTS ]", source)
        self.assertIn("VOLTAR AO HUB", source)
        self.assertIn("Restauro de sessão:", source)
        self.assertIn('"return": "return.to-hub"', source)
        self.assertIn("for endpoint in (PRIMARY_SOCKET, LIVE_SOCKET)", source)
        self.assertIn('sys.path.insert(0, "/usr/lib/apx")', source)
        self.assertNotIn("Path(__file__).resolve().parent", source)
        self.assertNotIn('("/usr/bin/hyprctl", "dispatch", "exit")', source)

    def test_authenticated_return_is_host_driven_and_observable(self) -> None:
        source = SERVICE.read_text()
        self.assertIn("def request_environment_stop(name: str) -> str:", source)
        self.assertIn('("/usr/bin/systemctl", "--no-block", "stop", unit)', source)
        self.assertIn('unit = f"apx-graphical-{name}-{generation[:8]}.service"', source)
        self.assertIn("request_environment_stop(source)", source)
        self.assertIn("Environment switch accepted operation=", source)
        self.assertIn("Environment switch rejected operation=", source)

    def test_runner_has_validated_dynamic_round_trip_and_recovery_gate(self) -> None:
        source = RUNNER.read_text()
        self.assertIn('mode.add_argument("--environment")', source)
        self.assertIn('re.fullmatch(r"[a-z]', source)
        self.assertIn('mode.add_argument("--relaunch-hub", action="store_true")', source)
        self.assertIn("def release_handoff_lock(descriptor, device: int, inode: int)", source)
        self.assertIn("lock_metadata = os.fstat(descriptor.fileno())", source)
        self.assertIn("metadata.st_dev, metadata.st_ino", source)
        self.assertEqual(source.count("owns_transition = False"), 2)
        self.assertIn('run((HUB, "--recover")); wait_recovered()', source)
        self.assertIn('run_authenticated((GENERAL, "--environment", name, "--interactive"),', source)
        self.assertIn('run_authenticated((HUB, "--interactive"),', source)
        self.assertIn('HANDOFF_PROOF = Path("/run/apx/authenticated-handoff-v1")', source)
        self.assertIn('os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o444', source)
        self.assertIn('unlink_owned_handoff_proof(metadata.st_dev, metadata.st_ino)\n        if readiness is not None:', source)
        self.assertIn('stdout, stderr = process.communicate()', source)
        self.assertIn("metadata = os.fstat(descriptor)", source)
        self.assertIn("transition_screen", source)
        self.assertIn('transition_screen("A FECHAR O HUB", 8)', source)
        self.assertIn("hide_host_getty()", source)
        self.assertIn('"mask", "--runtime", "--now", "getty@tty1.service"', source)
        self.assertIn('"unmask", "--runtime", "getty@tty1.service"', source)
        self.assertIn("restore_host_getty()", source)
        self.assertIn('time.sleep(0.05)', source)
        self.assertIn("arm_failsafe(name)", source)
        self.assertIn("detail = (result.stderr.strip() or result.stdout.strip()", source)

    def test_runner_restores_hub_when_workload_shell_fails(self) -> None:
        runner = load_runner()
        calls: list[str] = []

        def authenticated(arguments, _message, _progress, **_options):
            calls.append(arguments[0])
            if arguments[0] == runner.GENERAL:
                raise RuntimeError("workload shell failed")
            return mock.Mock(returncode=0, stdout="", stderr="")

        with tempfile.TemporaryDirectory() as directory, \
                mock.patch.object(runner, "LOCK", Path(directory) / "handoff.lock"), \
                mock.patch.object(runner, "transition_screen"), \
                mock.patch.object(runner, "restore_console_cursor"), \
                mock.patch.object(runner, "run", return_value=mock.Mock(returncode=0, stdout="", stderr="")), \
                mock.patch.object(runner, "wait_recovered"), \
                mock.patch.object(runner, "arm_failsafe"), \
                mock.patch.object(runner, "disarm_failsafe"), \
                mock.patch.object(runner, "run_authenticated", side_effect=authenticated), \
                mock.patch.object(sys, "argv", ["runner", "--environment", "andre"]):
            with self.assertRaisesRegex(RuntimeError, "HUB foi restaurado"):
                runner.main()

        self.assertEqual(calls, [runner.GENERAL, runner.HUB])

    def test_runner_disarms_startup_failsafe_after_trusted_workload_readiness(self) -> None:
        runner = load_runner()
        source = RUNNER.read_text()
        self.assertIn('WORKLOAD_ACTIVE = Path("/run/apx/active-graphical-environment-v1.json")', source)
        self.assertIn('readiness=lambda: workload_ready(name)', source)
        self.assertIn('on_ready=disarm_failsafe', source)
        self.assertIn('record.get("state")) == (\n        name, "graphical-base", "hyprland-base-v2", "running"', source)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            registration = root / "environments/andre/registration.json"
            registration.parent.mkdir(parents=True)
            generation = "8b3b43de-097b-49e4-9264-f4a6bde86a05"
            registration.write_text(json.dumps({
                "name": "andre", "role": "graphical-base", "release": "hyprland-base-v2",
                "state": "running", "generation": generation,
            }))
            active = root / "active.json"
            active.write_text(json.dumps({
                "profile": "apx-active-graphical-environment-v1", "name": "andre",
                "role": "graphical-base", "generation": generation,
                "unit": "apx-graphical-andre-8b3b43de.service", "pid": 123,
            }))
            original_path = Path

            def routed_path(value):
                if value == "/var/lib/apx/environments":
                    return root / "environments"
                return original_path(value)

            with mock.patch.object(runner, "WORKLOAD_ACTIVE", active), \
                    mock.patch.object(runner, "Path", side_effect=routed_path):
                self.assertTrue(runner.workload_ready("andre"))
                registration.write_text(registration.read_text().replace('"running"', '"stopped"'))
                self.assertFalse(runner.workload_ready("andre"))

    def test_management_runner_uses_only_fixed_graphical_plan_and_bound_destroy(self) -> None:
        source = MANAGEMENT_RUNNER.read_text()
        self.assertIn('"--role", "graphical-base"', source)
        self.assertIn('f"CREATE {target} AS graphical-base"', source)
        self.assertIn('"--description", description', source)
        self.assertIn('"--desktop-preset", preset', source)
        self.assertIn('"--desktop-modules", modules', source)
        self.assertIn('f"DESTROY {target}"', source)
        self.assertIn('operation_plan.get("generation") != arguments.generation', source)
        self.assertIn('os.O_NOFOLLOW', source)
        self.assertNotIn("shell=True", source)

    def test_workload_does_not_receive_hub_only_services(self) -> None:
        general = GENERAL.read_text()
        self.assertIn("engine.UPDATE_ENABLED = False", general)
        self.assertIn("engine.POWER_ENABLED = False", general)
        self.assertIn("engine.HOST_CONSOLE_ENABLED = False", general)
        launcher = LAUNCHER.read_text()
        self.assertIn('ENVIRONMENT_FEATURES = Path("/usr/lib/apx/apx_environment_features.py")', launcher)
        self.assertIn(':/usr/lib/apx/apx_environment_features.py', launcher)
        self.assertIn('if (engine.HOME / "apx/.config/apx/red-shell-v1").is_file():', general)
        launcher = LAUNCHER.read_text()
        self.assertIn("ENVIRONMENT_SWITCH_SOCKET", launcher)

    def test_red_shell_has_only_return_control(self) -> None:
        source = RED_SHELL.read_text()
        self.assertIn("#ff4d5f", source)
        self.assertIn('command: ["/usr/bin/hyprctl", "dispatch", "exit"]', source)
        self.assertIn('["/run/apx/environment-switch-client-v1.py", "identity"]', source)
        self.assertIn("environmentIdentity.display_name", source)
        for forbidden in ("coordinated-update", "system-power", "host-console", "TERMINAL DO HOST"):
            self.assertNotIn(forbidden, source)
        hyprland = RED_HYPRLAND.read_text()
        self.assertIn("bind = SUPER, M, exit", hyprland)
        self.assertNotIn("bind = SUPER, E, exit", hyprland)
        self.assertIn("bind = SUPER SHIFT, M, exit", hyprland)
        self.assertNotIn("blur { enabled", hyprland)
        self.assertNotIn("shadow { enabled", hyprland)

    def test_workload_shell_surfaces_return_failure(self) -> None:
        source = (ROOT / "config/environment-shell-v1/quickshell/apx/shell.qml").read_text()
        self.assertIn('property string environmentSwitchError: ""', source)
        self.assertIn('property bool environmentSwitchPending: false', source)
        self.assertIn("stderr: StdioCollector", source)
        self.assertIn("O Host recusou a transição", source)
        self.assertNotIn('label: "ABRIR SELECIONADO"', source)
        self.assertIn('onDoubleClicked: { root.environmentFocusIndex = index; root.selectEnvironment(modelData); root.openSelectedEnvironment() }', source)
        self.assertIn('event.key === Qt.Key_Delete', source)
        self.assertIn('event.key === Qt.Key_Return || event.key === Qt.Key_Enter', source)
        self.assertIn('import Quickshell.Wayland', source)
        self.assertIn('import Quickshell.Hyprland', source)
        self.assertIn('PanelWindow {\n        id: popup', source)
        self.assertIn('sequence: "Escape"', source)
        self.assertIn('focusable: visible', source)
        self.assertIn('ScrollBar.vertical: ScrollBar', source)
        self.assertIn('menuContent.implicitHeight > popupBackground.height - 20', source)
        self.assertIn('WlrLayershell.keyboardFocus:', source)
        self.assertIn('HyprlandFocusGrab {', source)
        self.assertIn('windows: [bar, popup]', source)
        self.assertNotIn('id: popupDismissLayer', source)
        self.assertIn('environmentNameInput.forceActiveFocus()', source)
        self.assertIn('text: "‹  VOLTAR"', source)
        self.assertIn('root.cancelEnvironmentCreate()', source)
        self.assertIn('property bool environmentKeyboardFocus: false', source)
        self.assertIn('property int environmentFocusIndex: -1', source)
        self.assertIn('property int environmentCreateFocusIndex: -1', source)
        self.assertIn('property string environmentFeatureDrawer: ""', source)
        self.assertIn('property int environmentDeleteFocusIndex: 0', source)
        self.assertIn('function moveEnvironmentFocus(direction)', source)
        self.assertIn('function activateEnvironmentFocus()', source)
        self.assertIn('if (selectedEnvironmentName === item.name) openSelectedEnvironment()', source)
        self.assertIn('else selectEnvironment(item)', source)
        self.assertIn('root.moveEnvironmentFocus(-1)', source)
        self.assertIn('root.moveEnvironmentFocus(1)', source)
        self.assertIn('root.activateEnvironmentFocus()', source)
        self.assertIn('root.deleteFocusedEnvironment()', source)
        self.assertIn('root.environmentFocusIndex === root.environmentCatalog.length', source)
        self.assertIn('root.environmentFocusIndex === root.environmentCatalog.length + 1', source)
        self.assertIn('root.moveEnvironmentActionFocus(-1)', source)
        self.assertIn('root.moveEnvironmentActionFocus(1)', source)
        self.assertIn('root.environmentDeleteFocusIndex = 0', source)
        self.assertIn('root.environmentDeleteFocusIndex = 1', source)
        self.assertIn('if (root.environmentDeleteFocusIndex === 0) root.cancelEnvironmentDelete()', source)
        self.assertIn('else root.destroySelectedEnvironment()', source)
        self.assertIn('text: "Os teus Environments"', source)
        self.assertNotIn('↑↓ NAVEGAR', source)
        self.assertIn('id: environmentDescriptionInput', source)
        self.assertIn('function environmentCreateVisibleFocusIndices()', source)
        self.assertIn('function moveEnvironmentCreateFocus(direction)', source)
        self.assertIn('function moveEnvironmentCreateHorizontal(direction)', source)
        self.assertIn('function moveEnvironmentCreateVertical(direction)', source)
        self.assertIn('else if (event.key === Qt.Key_Up) moveEnvironmentCreateVertical(-1)', source)
        self.assertIn('else if (event.key === Qt.Key_Right) moveEnvironmentCreateHorizontal(1)', source)
        self.assertIn('function activateEnvironmentCreateFocus()', source)
        self.assertIn('function handleEnvironmentCreateKey(event)', source)
        self.assertIn('root.handleEnvironmentCreateKey(event)', source)
        self.assertIn('keyboardFocused: root.environmentCreateFocusIndex === root.environmentCreateModuleFocusBase + root.environmentModuleIndex(moduleInfo.key)', source)
        self.assertIn('environmentDescriptionInput.forceActiveFocus()', source)
        self.assertIn('environmentNameInput.forceActiveFocus()', source)
        self.assertIn('"--description", visibleDescription.trim()', source)
        self.assertIn('"--preset", environmentDesktopPreset', source)
        self.assertIn('"--modules", selectedEnvironmentModuleKeys().join(",")', source)
        self.assertIn('title: "BÁSICO · BASE APX"', source)
        self.assertIn('title: "INTERMÉDIO · DIA A DIA"', source)
        self.assertIn('title: "COMPLETO · TRABALHO"', source)
        self.assertIn('additions: "EXTRAS · NENHUM"', source)
        self.assertIn('+ BRAVE · PDF · MPV', source)
        self.assertIn('environmentCreateOpen = false', source)
        self.assertIn('+ LIBREOFFICE · DEV · IMPRESSÃO', source)
        self.assertIn('root.environmentSelectedModules[moduleInfo.key] === true', source)
        self.assertIn('property var environmentModuleGroups', source)
        self.assertIn('component FeatureCard: Rectangle', source)
        self.assertIn('programs: moduleInfo.programs', source)
        self.assertIn('acceptedButtons: Qt.RightButton', source)
        self.assertIn('root.environmentFeatureInfo = infoVisible ? "" : moduleInfo.key', source)
        self.assertNotIn('dialog-information-symbolic.svg', source)
        self.assertNotIn('text: modelData.description', source)
        self.assertIn('root.environmentFeatureDrawer === modelData.key ? "▴" : "▾"', source)
        self.assertIn('A palavra-passe de sudo será herdada do HUB.', source)
        self.assertIn('root.createEnvironment(environmentNameInput.text, environmentDescriptionInput.text)', source)
        self.assertIn('? "/home/.apx-host-bridge/environment-switch-client-v1.py"', source)
        self.assertIn(': "/run/apx/environment-switch-client-v1.py"', source)
        self.assertIn('environment_form_name: environmentNameInput.text', source)
        self.assertIn('name.normalize("NFD")', source)
        self.assertIn('name.replace(/[^a-z0-9]+/g, "-")', source)
        self.assertIn('if (/^[0-9]/.test(name)) name = "env-" + name', source)
        self.assertIn('Escreve um nome para o Environment.', source)
        self.assertIn('function focusEnvironmentMenuAfterOpen()', source)
        self.assertIn('focusEnvironmentMenuAfterOpen()', source)
        self.assertIn('root.selectedEnvironmentName = ""', source)
        self.assertIn('root.selectedEnvironmentGeneration = ""', source)
        self.assertIn('root.environmentKeyboardFocus = false', source)
        self.assertIn('label: root.environmentManagementBusy ? "A CRIAR…" : "CRIAR ENVIRONMENT"', source)
        self.assertNotIn("Escolha um Environment disponível", source)
        self.assertNotIn("ESC  FECHAR", source)
        self.assertNotIn("TRANSIÇÃO GERIDA PELO HOST", source)
        self.assertIn("function openEnvironments(): void", source)
        self.assertIn('root.togglePopup("environments", environmentButton)', source)
        self.assertIn("function toggleControls(): void", source)
        self.assertIn("function toggleCalendar(): void", source)
        self.assertIn("function toggleModel(): void", source)
        self.assertIn("function toggleBattery(): void", source)
        self.assertIn("id: batteryButton", source)
        self.assertIn('text: "SUPER+M"', source)
        self.assertIn('text: "Sair para o Host"', source)
        self.assertNotIn('text: root.isHub ? "Escolher Environment" : "Voltar ao Hub"', source)
        self.assertIn('command: ["/usr/bin/hyprctl", "dispatch", "hl.dsp.exit()"]', source)
        self.assertIn('text: root.isHub ? "Terminal do Host · sessão única"', source)
        self.assertIn('(root.isHub ? 440 : 394) * root.controlCenterScale', source)
        self.assertIn('key: "shortcuts"', source)
        self.assertIn('label: "Atalhos APX"', source)
        self.assertIn('SUPER+A/B/D/E', source)
        self.assertIn('command: ["/usr/bin/test", "-S", "/run/apx/host-console-v1.sock"]', source)
        self.assertIn('function returnToHub()', source)
        self.assertIn('["/usr/bin/hyprctl", "eval", "hl.dsp.exit()"]', source)
        self.assertIn('enabled: root.sessionKindReady && !root.environmentSwitchPending', source)
        self.assertIn('import Quickshell.Hyprland', source)
        self.assertIn('HyprlandFocusGrab {', source)
        self.assertIn('windows: [bar, popup]', source)
        self.assertNotIn('id: popupDismissLayer', source)
        self.assertIn('columns: 2', source)

    def test_work_shortcuts_use_super_e_for_menu_and_super_m_for_escape(self) -> None:
        lua = (ROOT / "config/environment-shell-v1/hypr/hyprland.lua").read_text()
        legacy = (ROOT / "config/environment-shell-v1/hyprland/hyprland.conf").read_text()
        self.assertIn('mainMod .. " + E"', lua)
        self.assertIn("openEnvironments", lua)
        self.assertIn('mainMod .. " + F"', lua)
        self.assertIn('mainMod .. " + M"', lua)
        self.assertIn('mainMod .. " + M", hl.dsp.exit()', lua)
        self.assertIn("bind = SUPER, M, exit", legacy)
        self.assertIn("bind = SUPER, F, exec, /usr/bin/thunar", legacy)
        self.assertIn("bind = SUPER, E, exec, quickshell -c apx ipc call host openEnvironments", legacy)
        shortcut_helper = (ROOT / "config/environment-shell-v1/local/bin/apx-shortcuts-v1").read_text()
        self.assertIn("hyprctl keyword unbind 'SUPER, E'", shortcut_helper)
        self.assertIn("hyprctl keyword bind \"SUPER, E, exec", shortcut_helper)
        for key, method in (("A", "toggleControls"), ("D", "toggleCalendar"),
                            ("I", "toggleModel"), ("B", "toggleBattery")):
            self.assertIn(f'mainMod .. " + {key}"', lua)
            self.assertIn(method, lua)
            self.assertIn(f"bind = SUPER, {key}, exec, quickshell -c apx ipc call host {method}", legacy)


if __name__ == "__main__":
    unittest.main()
