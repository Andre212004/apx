from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import apx_audio_handoff as subject  # noqa: E402


class AudioHandoffTests(unittest.TestCase):
    def state(self, **changes):
        values = {"schema": 1, "profile": subject.PROFILE, "output_volume": 80, "output_muted": False,
                  "input_volume": 65, "input_muted": True, "output_name": "Speakers", "input_name": "Microphone"}
        values.update(changes); return subject.AudioState(**values)

    def test_state_moves_to_only_the_incoming_environment(self):
        plan = subject.build_handoff("work", "games", self.state())
        self.assertEqual(plan.capture_access, "active-environment-only")
        self.assertIn("stop-local-pipewire-and-revoke-playback-and-capture-device-leases", plan.effects)
        self.assertIn("apply-input-volume-mute-and-selected-input", plan.effects)

    def test_invalid_volumes_and_same_environment_fail_closed(self):
        with self.assertRaises(subject.AudioHandoffError): subject.validate_state(self.state(output_volume=101))
        with self.assertRaises(subject.AudioHandoffError): subject.build_handoff("work", "work", self.state())


if __name__ == "__main__": unittest.main()
