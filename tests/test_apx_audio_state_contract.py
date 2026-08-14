import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from apx_audio_state_contract import parse_message, request_bytes


class AudioStateContractTests(unittest.TestCase):
    def test_round_trip(self):
        value = parse_message(request_bytes("activity.put", {"microphone_active": True}))
        self.assertEqual(value["operation"], "activity.put")
        self.assertTrue(value["payload"]["microphone_active"])

    def test_rejects_unknown_operation_and_extra_frame(self):
        with self.assertRaises(ValueError): request_bytes("shell", {})
        with self.assertRaises(ValueError): parse_message(b"{}\n{}\n")
