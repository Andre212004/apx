from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/physical-pilot/apx-graphical-input-proof-v1.py"


class GraphicalInputProofAdapterTests(unittest.TestCase):
    def test_adapter_is_bounded_identity_resolved_and_always_recovers(self) -> None:
        source = SCRIPT.read_text()
        compile(source, str(SCRIPT), "exec")
        for required in (
            "resolve_input_devices", "--on-active=30s", "finally:",
            "recover()", "DevicePolicy=closed", "Super+F12",
            "keyboard_event_count", "pointer_event_count",
            "--host-keyboard-only", "apx-host-keyboard-candidate-count-v2",
            "candidate_event_counts", "platform-i8042-serio-0",
            "pci-0000:05:00.3-usb-0:4:1.0", "ID_INTEGRATION",
        ):
            self.assertIn(required, source)
        for fixed in ("/dev/input/event3", "/dev/input/event8", "/dev/input/event9"):
            self.assertNotIn(fixed, source)

    def test_adapter_does_not_store_key_codes_values_or_raw_events(self) -> None:
        source = SCRIPT.read_text()
        self.assertIn("_code, _value", source)
        for forbidden in ("print(_code", "print(_value", "write(chunk", "open(\"/var/log"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
