from dataclasses import replace
import unittest

from src.apx_graphical_input_proof import (
    GraphicalInputProofError,
    GraphicalInputProofEvidence,
    assess_graphical_input,
)


class GraphicalInputProofTests(unittest.TestCase):
    def evidence(self) -> GraphicalInputProofEvidence:
        return GraphicalInputProofEvidence(
            resolved_devices=(
                ("keyboard", "/dev/input/event3"),
                ("elan_mouse", "/dev/input/event8"),
                ("elan_touchpad", "/dev/input/event9"),
            ),
            keyboard_event_count=4,
            pointer_event_count=12,
            cursor_before=(100, 100),
            cursor_after=(140, 120),
            shortcut_marker_present=True,
            exact_nodes_visible_inside=True,
            closed_unit_device_policy=True,
            tty1_restored=True,
            registrations_stopped=True,
            no_machine_residue=True,
            no_unit_residue=True,
            no_failed_units=True,
        )

    def test_complete_hardware_delivery_and_recovery_are_verified(self) -> None:
        result = assess_graphical_input(self.evidence())
        self.assertEqual(result.classification, "verified")
        self.assertEqual(result.blockers, ())
        self.assertEqual(len(result.evidence_digest), 64)

    def test_each_delivery_and_recovery_gate_blocks(self) -> None:
        changes = {
            "keyboard_event_count": 0,
            "pointer_event_count": 0,
            "cursor_after": (100, 100),
            "shortcut_marker_present": False,
            "exact_nodes_visible_inside": False,
            "closed_unit_device_policy": False,
            "tty1_restored": False,
            "registrations_stopped": False,
            "no_machine_residue": False,
            "no_unit_residue": False,
            "no_failed_units": False,
        }
        for field, value in changes.items():
            with self.subTest(field=field):
                result = assess_graphical_input(replace(self.evidence(), **{field: value}))
                self.assertEqual(result.classification, "blocked")
                self.assertTrue(result.blockers)

    def test_nodes_counts_positions_and_types_fail_closed(self) -> None:
        with self.assertRaises(GraphicalInputProofError):
            assess_graphical_input(replace(
                self.evidence(),
                resolved_devices=(("keyboard", "/dev/input/event3"),),
            ))
        with self.assertRaises(GraphicalInputProofError):
            assess_graphical_input(replace(self.evidence(), keyboard_event_count=-1))
        with self.assertRaises(GraphicalInputProofError):
            assess_graphical_input(replace(self.evidence(), shortcut_marker_present=1))


if __name__ == "__main__":
    unittest.main()
