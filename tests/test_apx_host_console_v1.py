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
            "SIGWINCH", "PersistentConsole", "SESSION_LOCK", "console-detach",
            "DETACHED_OUTPUT_LIMIT", "REPLAY_OUTPUT_LIMIT", '"TERM": "xterm-256color"',
            'connection.sendall(b"\\x1bc" + snapshot)',
        ):
            self.assertIn(required, source)
        self.assertIn('"reattach_on_open": True', source)
        self.assertNotIn("os.kill(child, signal.SIGHUP)", source)
        self.assertNotIn('"TERM": "xterm-kitty"', source)
        self.assertNotIn('payload.get("command")', source)
        self.assertNotIn("host.tty.activate", source)
        self.assertNotIn("shell=True", source)

    def test_client_keeps_token_and_commands_out_of_arguments(self):
        source = CLIENT.read_text(); compile(source, str(CLIENT), "exec")
        self.assertIn("os.get_terminal_size", source)
        self.assertIn('"rows": size.lines', source)
        self.assertIn("SESSÃO ANTERIOR REANEXADA", source)
        self.assertIn("fechar a janela apenas desanexa", source)
        self.assertNotIn('add_argument("--token"', source)
        self.assertNotIn("input(", source)
        self.assertNotIn("subprocess", source)

    def test_exact_launcher_mounts_console_but_generic_disables_it(self):
        exact = LAUNCHER.read_text()
        generic = (ROOT / "scripts/physical-pilot/apx-graphical-environment-v1.py").read_text()
        self.assertIn("HOST_CONSOLE_ENABLED = True", exact)
        self.assertIn("HOST_CONSOLE_SOCKET", exact)
        self.assertIn("engine.HOST_CONSOLE_ENABLED = False", generic)

    def test_hub_console_shortcut_focuses_or_reattaches_the_single_pty(self):
        source = OPEN.read_text(); compile(CLIENT.read_text(), str(CLIENT), "exec")
        self.assertIn("hyprctl clients", source)
        self.assertIn("hl.get_window", source)
        self.assertIn("hl.dsp.focus", source)
        self.assertIn("APX HOST ROOT", source)
        self.assertIn("apx-host-console-terminal", source)
        self.assertIn('command: ["/home/apx/.local/bin/apx-host-console-open"]', QML.read_text())

    def test_pty_survives_detach_and_accepts_a_second_attachment(self):
        daemon = self.load_daemon()
        session = daemon.PersistentConsole(24, 80, 0)

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
            self.assertTrue(session.alive)

            snapshot = session.claim(31, 100, reattached=True)
            self.assertIn(b"APX-FIRST", snapshot)
            session.write_input(b"printf 'APX-REATTACHED\\n'\n")
            self.assertIn(b"APX-REATTACHED", output_until(b"APX-REATTACHED"))
            session.release(0)
            session.write_input(b"exit\n")
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


if __name__ == "__main__":
    unittest.main()
