import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
LAUNCH = ROOT / "scripts/physical-pilot/apx-graphical-test-launch-v1.py"
BROKER = ROOT / "scripts/physical-pilot/apx-graphical-broker-v1.py"
SESSION = ROOT / "scripts/physical-pilot/apx-graphical-session-v1.sh"
SPEC = importlib.util.spec_from_file_location("apx_graphical_test_launch", LAUNCH)
subject = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(subject)


class GraphicalInputResolutionTests(unittest.TestCase):
    def properties(self, node: str) -> str:
        values = {
            "event3": "DEVNAME=/dev/input/event3\nID_PATH=platform-i8042-serio-0\nID_INPUT_KEYBOARD=1\n",
            "event8": "DEVNAME=/dev/input/event8\nID_PATH=platform-AMDI0010:01\nID_INPUT_MOUSE=1\n",
            "event9": "DEVNAME=/dev/input/event9\nID_PATH=platform-AMDI0010:01\nID_INPUT_TOUCHPAD=1\n",
            "event10": "DEVNAME=/dev/input/event10\nID_PATH=platform-pcspkr\nID_INPUT=1\n",
        }
        return values[node]

    def test_resolves_physical_properties_and_ignores_unstable_event_numbers(self) -> None:
        nodes = [Path(f"/dev/input/{name}") for name in ("event10", "event9", "event3", "event8")]

        def fake_run(arguments, check=False):
            node = arguments[-1].split("=", 1)[1].rsplit("/", 1)[1]
            return type("Result", (), {"returncode": 0, "stdout": self.properties(node)})()

        with patch.object(subject.Path, "glob", return_value=nodes), patch.object(subject, "run", side_effect=fake_run):
            self.assertEqual(subject.resolve_input_devices(), {
                "keyboard": "/dev/input/event3",
                "elan_mouse": "/dev/input/event8",
                "elan_touchpad": "/dev/input/event9",
            })

    def test_missing_or_ambiguous_identity_fails_closed(self) -> None:
        node = Path("/dev/input/event3")
        result = type("Result", (), {"returncode": 0, "stdout": self.properties("event3")})()
        with patch.object(subject.Path, "glob", return_value=[node]), patch.object(subject, "run", return_value=result):
            with self.assertRaisesRegex(SystemExit, "absent or ambiguous"):
                subject.resolve_input_devices()

    def test_broker_and_session_use_resolved_nodes_not_fixed_event_numbers(self) -> None:
        broker = BROKER.read_text()
        session = SESSION.read_text()
        for required in ("ID_INPUT_KEYBOARD", "ID_INPUT_MOUSE", "ID_INPUT_TOUCHPAD", "resolve_input_devices"):
            self.assertIn(required, broker)
        self.assertNotIn("DeviceAllow=/dev/input/event3", broker)
        self.assertNotIn("DeviceAllow=/dev/input/event10", broker)
        for variable in ("APX_KEYBOARD_DEVICE", "APX_ELAN_MOUSE_DEVICE", "APX_ELAN_TOUCHPAD_DEVICE"):
            self.assertIn(variable, session)


if __name__ == "__main__":
    unittest.main()
