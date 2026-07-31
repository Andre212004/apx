#!/usr/bin/env python3
"""Exact bounded visual launch of the published graphical Hub."""

from __future__ import annotations

import importlib.util
from pathlib import Path


SOURCE = Path("/var/lib/apx/graphical-v1/apx-graphical-test-launch-v1.py")
spec = importlib.util.spec_from_file_location("apx_graphical_launch", SOURCE)
if spec is None or spec.loader is None:
    raise SystemExit("graphical Hub launch source is unavailable")
launch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launch)

launch.GENERATION = "2c3dbacc-106f-4053-8603-f649552f5513"
launch.PLAN = "2def2bb58aeb6aa3b15cfd7764421c94e94cbd1c092fccddefcf7eeb3787c64f"
launch.UNIT = "apx-graphical-hub-2c3dbacc"
launch.EXPIRY = "apx-graphical-hub-expiry"
launch.MACHINE = "apx-hub"
launch.ROOT = "/var/lib/apx/environments/hub/root"
launch.HOME = "/var/lib/apx/environments/hub/home"
launch.RECOVERY_MODE = "--recover-hub"
launch.REGISTRATION = "/var/lib/apx/environments/hub/registration.json"

if __name__ == "__main__":
    raise SystemExit(launch.main())
