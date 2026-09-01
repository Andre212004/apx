"""Closed result contract for the assisted physical graphical-input proof."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json


PROFILE = "apx-graphical-input-proof-v1"
DEVICE_LABELS = ("keyboard", "elan_mouse", "elan_touchpad")


class GraphicalInputProofError(ValueError):
    pass


@dataclass(frozen=True)
class GraphicalInputProofEvidence:
    resolved_devices: tuple[tuple[str, str], ...]
    keyboard_event_count: int
    pointer_event_count: int
    cursor_before: tuple[int, int]
    cursor_after: tuple[int, int]
    shortcut_marker_present: bool
    exact_nodes_visible_inside: bool
    closed_unit_device_policy: bool
    tty1_restored: bool
    registrations_stopped: bool
    no_machine_residue: bool
    no_unit_residue: bool
    no_failed_units: bool


@dataclass(frozen=True)
class GraphicalInputProofResult:
    profile: str
    classification: str
    blockers: tuple[str, ...]
    evidence_digest: str


def assess_graphical_input(evidence: GraphicalInputProofEvidence) -> GraphicalInputProofResult:
    if type(evidence) is not GraphicalInputProofEvidence:
        raise GraphicalInputProofError("input proof evidence has wrong type")
    if tuple(label for label, _node in evidence.resolved_devices) != DEVICE_LABELS:
        raise GraphicalInputProofError("resolved input labels are not exact or ordered")
    nodes = tuple(node for _label, node in evidence.resolved_devices)
    if len(set(nodes)) != 3 or any(not node.startswith("/dev/input/event") for node in nodes):
        raise GraphicalInputProofError("resolved input nodes are invalid or overlapping")
    for count in (evidence.keyboard_event_count, evidence.pointer_event_count):
        if type(count) is not int or count < 0 or count > 1_000_000:
            raise GraphicalInputProofError("event count is invalid")
    for point in (evidence.cursor_before, evidence.cursor_after):
        if len(point) != 2 or any(type(value) is not int or abs(value) > 1_000_000 for value in point):
            raise GraphicalInputProofError("cursor position is invalid")
    boolean_fields = (
        evidence.shortcut_marker_present, evidence.exact_nodes_visible_inside,
        evidence.closed_unit_device_policy, evidence.tty1_restored,
        evidence.registrations_stopped, evidence.no_machine_residue,
        evidence.no_unit_residue, evidence.no_failed_units,
    )
    if any(type(value) is not bool for value in boolean_fields):
        raise GraphicalInputProofError("input proof gate is not boolean")

    gates = (
        ("no keyboard event was observed", evidence.keyboard_event_count > 0),
        ("no pointer event was observed", evidence.pointer_event_count > 0),
        ("Hyprland cursor position did not change", evidence.cursor_before != evidence.cursor_after),
        ("Hyprland did not execute the temporary shortcut", evidence.shortcut_marker_present),
        ("exact resolved nodes were not visible inside", evidence.exact_nodes_visible_inside),
        ("graphical unit device policy was not closed", evidence.closed_unit_device_policy),
        ("tty1 was not restored", evidence.tty1_restored),
        ("graphical registrations were not stopped", evidence.registrations_stopped),
        ("machine residue remains", evidence.no_machine_residue),
        ("graphical unit residue remains", evidence.no_unit_residue),
        ("failed systemd units remain", evidence.no_failed_units),
    )
    blockers = tuple(label for label, passed in gates if not passed)
    payload = {
        "profile": PROFILE,
        "resolved_devices": evidence.resolved_devices,
        "keyboard_event_count": evidence.keyboard_event_count,
        "pointer_event_count": evidence.pointer_event_count,
        "cursor_before": evidence.cursor_before,
        "cursor_after": evidence.cursor_after,
        "shortcut_marker_present": evidence.shortcut_marker_present,
        "exact_nodes_visible_inside": evidence.exact_nodes_visible_inside,
        "closed_unit_device_policy": evidence.closed_unit_device_policy,
        "tty1_restored": evidence.tty1_restored,
        "registrations_stopped": evidence.registrations_stopped,
        "no_machine_residue": evidence.no_machine_residue,
        "no_unit_residue": evidence.no_unit_residue,
        "no_failed_units": evidence.no_failed_units,
    }
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return GraphicalInputProofResult(
        profile=PROFILE,
        classification="verified" if not blockers else "blocked",
        blockers=blockers,
        evidence_digest=digest,
    )
