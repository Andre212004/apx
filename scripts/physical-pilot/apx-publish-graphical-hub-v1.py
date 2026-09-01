#!/usr/bin/env python3
"""Exact rollback-preserving publication of the first graphical APX Hub."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess


PLAN = "e6f99a38aecc88088949770c3213b2690aadcdefcad75c62c06de86b0776abee"
OLD_GENERATION = "d68ee7a2-268a-4534-b033-8f5313943fcf"
NEW_GENERATION = "2c3dbacc-106f-4053-8603-f649552f5513"
CURRENT = Path("/var/lib/apx/environments/hub")
CANDIDATE = Path("/var/lib/apx/quarantine/hub-graphical-v1-candidate-20260718")
RETAINED = Path("/var/lib/apx/quarantine/retained-hub-headless-v3-d68ee7a2")


def atomic_json(path: Path, value: dict[str, object]) -> None:
    temporary = path.with_name(".registration.json.apx-publish")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write((json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode())
        stream.flush(); os.fsync(stream.fileno())
    os.replace(temporary, path)


def main() -> int:
    if os.geteuid() != 0 or RETAINED.exists():
        raise SystemExit("graphical Hub publication refused: identity or retained destination differs")
    old = json.loads((CURRENT / "registration.json").read_text())
    if (old.get("generation"), old.get("release"), old.get("role"), old.get("state")) != (
        OLD_GENERATION, "hub-headless-v3", "hub", "stopped"
    ):
        raise SystemExit("graphical Hub publication refused: current Hub changed")
    if any((CURRENT / "home").iterdir()):
        raise SystemExit("graphical Hub publication refused: current Hub home is not empty")
    required = (
        CANDIDATE / "root/usr/bin/Hyprland", CANDIDATE / "root/usr/bin/waybar",
        CANDIDATE / "root/usr/bin/apx-hub", CANDIDATE / "root/usr/bin/dbus-launch",
        CANDIDATE / "home/apx/.config/hyprland/hyprland.conf",
        CANDIDATE / "home/apx/.config/waybar/config.json",
    )
    if not all(path.is_file() for path in required):
        raise SystemExit("graphical Hub publication refused: candidate is incomplete")
    machine_id = (CANDIDATE / "root/etc/machine-id").read_text().strip()
    if len(machine_id) != 32 or any(character not in "0123456789abcdef" for character in machine_id):
        raise SystemExit("graphical Hub publication refused: candidate identity is invalid")
    if subprocess.run(("machinectl", "list", "--no-legend"), text=True, capture_output=True).stdout.strip():
        raise SystemExit("graphical Hub publication refused: an Environment is active")
    moved_old = moved_new = False
    try:
        os.rename(CURRENT, RETAINED); moved_old = True
        os.rename(CANDIDATE, CURRENT); moved_new = True
        atomic_json(CURRENT / "registration.json", {
            "schema": 1, "name": "hub", "role": "hub-graphical",
            "generation": NEW_GENERATION, "release": "hyprland-base-v1",
            "state": "stopped", "created_at": "2026-07-19T00:35:00+00:00",
            "replaces_generation": OLD_GENERATION, "rollback_retained": str(RETAINED),
        })
    except BaseException:
        if moved_new and CURRENT.exists():
            os.rename(CURRENT, CANDIDATE)
        if moved_old and RETAINED.exists():
            os.rename(RETAINED, CURRENT)
        raise
    print(f"graphical-hub-published generation={NEW_GENERATION} plan={PLAN}")
    print(f"headless-hub-retained={RETAINED}")
    print("graphical_activation=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
