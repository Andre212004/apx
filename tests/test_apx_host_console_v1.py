import importlib.util
import json
import os
from pathlib import Path
import signal
import tempfile
import time
import unittest

import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import apx_host_console_contract as contract  # noqa: E402


DAEMON = ROOT / "scripts/physical-pilot/apx-host-console-v1.py"
CLIENT = ROOT / "scripts/physical-pilot/apx-host-console-client-v1.py"
LAUNCHER = ROOT / "scripts/physical-pilot/apx-official-hub-graphical-v1.py"
OPEN = ROOT / "config/environment-shell-v1/local/bin/apx-host-console-open"
TERMINAL = ROOT / "config/environment-shell-v1/local/bin/apx-host-console-terminal"
QML = ROOT / "config/environment-shell-v1/quickshell/apx/shell.qml"


class HostConsoleV1Tests(unittest.TestCase):
    @staticmethod
    def load_daemon():
        specification = importlib.util.spec_from_file_location("apx_host_console_daemon", DAEMON)
        assert specification is not None and specification.loader is not None
        module = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(module)
        module.audit = lambda *_args, **_kwargs: None
        return module

    def test_contract_is_closed_and_round_trips(self):
        for operation in contract.OPERATIONS:
            value = contract.parse_message(contract.request_bytes(operation, {}))
            self.assertEqual(value["operation"], operation)
        with self.assertRaises(ValueError):
            contract.request_bytes("exec", {"command": "id"})

    def test_daemon_uses_exact_hub_confirmation_and_fixed_shell(self):
        source = DAEMON.read_text(); compile(source, str(DAEMON), "exec")
        for required in (
            "authorize_official_hub_peer", "quickshell_ancestor", "console.open",
            "pty.fork()", 'os.execve("/usr/bin/bash"', "TIOCSWINSZ",
            "SIGWINCH", "RootConsole", "console-detach", "console.ticket",
            "DETACHED_OUTPUT_LIMIT", "TICKET_TTL_SECONDS", '"TERM": "xterm-256color"',
            "secrets.token_urlsafe", "consume_ticket",
        ):
            self.assertIn(required, source)
        self.assertIn('"persistent_pty": False', source)
        self.assertIn("os.killpg(self.child, signal.SIGHUP)", source)
        self.assertNotIn("SESSION:", source)
        self.assertNotIn("ConsoleReplaced", source)
        self.assertNotIn('"TERM": "xterm-kitty"', source)
        self.assertNotIn('payload.get("command")', source)
        self.assertNotIn("host.tty.activate", source)
        self.assertNotIn("shell=True", source)

    def test_client_keeps_token_and_commands_out_of_arguments(self):
        source = CLIENT.read_text(); compile(source, str(CLIENT), "exec")
        self.assertIn("os.get_terminal_size", source)
        self.assertIn('"rows": size.lines', source)
        self.assertIn('os.environ.pop("APX_HOST_CONSOLE_TICKET"', source)
        self.assertIn("fechar a janela termina esta consola", source)
        self.assertNotIn('add_argument("--token"', source)
        self.assertNotIn("input(", source)
        self.assertNotIn("subprocess", source)

    def test_exact_launcher_mounts_console_but_generic_disables_it(self):
        exact = LAUNCHER.read_text()
        generic = (ROOT / "scripts/physical-pilot/apx-graphical-environment-v1.py").read_text()
        self.assertIn("HOST_CONSOLE_ENABLED = True", exact)
        self.assertIn("HOST_CONSOLE_SOCKET", exact)
        self.assertIn("engine.HOST_CONSOLE_ENABLED = False", generic)

    def test_hub_console_shortcut_focuses_or_opens_one_fresh_pty(self):
        source = OPEN.read_text(); compile(source, str(OPEN), "exec"); compile(CLIENT.read_text(), str(CLIENT), "exec")
        self.assertIn('request_bytes("console.ticket", {})', source)
        self.assertIn("hyprctl\", \"clients", source)
        self.assertIn("hl.get_window", source)
        self.assertIn("hl.dsp.focus", source)
        self.assertIn("APX HOST ROOT", source)
        self.assertIn('f"class: {WINDOW_CLASS}"', source)
        self.assertIn('"--class", WINDOW_CLASS', source)
        self.assertIn("apx-host-console-terminal", source)
        self.assertIn("APX_HOST_CONSOLE_TICKET", source)
        self.assertIn("start_new_session=True", source)
        self.assertIn("for _ in range(60)", source)
        self.assertNotIn("Já existe uma consola", TERMINAL.read_text())
        self.assertIn('command: ["/home/apx/.local/bin/apx-host-console-open"]', QML.read_text())
        hyprland = (ROOT / "config/environment-shell-v1/hypr/hyprland.lua").read_text()
        self.assertIn('mainMod .. " + H", hl.dsp.exec_cmd("quickshell -c apx ipc call host openTerminal")', hyprland)

    def test_pty_is_new_and_ends_with_its_window(self):
        daemon = self.load_daemon()
        session = daemon.RootConsole(24, 80, 0)

        def output_until(marker: bytes) -> bytes:
            deadline = time.monotonic() + 3
            output = bytearray()
            while marker not in output and time.monotonic() < deadline:
                output.extend(session.take_output())
            return bytes(output)

        try:
            session.claim(24, 80)
            session.write_input(b"printf 'APX-FIRST\\n'\n")
            self.assertIn(b"APX-FIRST", output_until(b"APX-FIRST"))
            session.release(0)
            session.terminate()
            deadline = time.monotonic() + 3
            while session.alive and time.monotonic() < deadline:
                time.sleep(0.02)
            self.assertFalse(session.alive)
        finally:
            if session.alive:
                try:
                    os.kill(session.child, signal.SIGHUP)
                except ProcessLookupError:
                    pass

    def test_ticket_is_short_lived_and_single_use(self):
        daemon = self.load_daemon()
        daemon.quickshell_ancestor = lambda _pid: 123
        peer = daemon.HostServicesPeer(200, 5000, 5000)
        token = daemon.issue_ticket(peer)
        daemon.consume_ticket(token, peer)
        with self.assertRaises(PermissionError):
            daemon.consume_ticket(token, peer)
        token = daemon.issue_ticket(peer)
        with self.assertRaises(PermissionError):
            daemon.consume_ticket(token, daemon.HostServicesPeer(201, 5001, 5001))


if __name__ == "__main__":
    unittest.main()
