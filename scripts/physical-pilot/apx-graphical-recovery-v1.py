#!/usr/bin/env python3
"""Exact Host recovery adapter and harmless timer rehearsal for APX graphics."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import time


PROFILE = "apx-graphical-recovery-v1"
PLAN_DIGEST = "7603c8d17c787ed4122cff9520f49392c0865412967b5a53e9b595ff8dec43f3"
DUMMY_UNIT = "apx-graphical-recovery-dummy.service"
EXPIRY_UNIT = "apx-graphical-recovery-expiry"
TEST_UNIT = "apx-graphical-test-69b56acc.service"
TEST_MACHINE = "apx-test"
HUB_UNIT = "apx-graphical-hub-2c3dbacc.service"
HUB_MACHINE = "apx-hub"
INSTALLED_PATH = Path("/var/lib/apx/graphical-v1/apx-graphical-recovery-v1.py")
ACTIVE_SESSION = Path("/run/apx/active-session-v1.json")
HUB_REGISTRATION = Path("/var/lib/apx/environments/hub/registration.json")
TEST_REGISTRATION = Path("/var/lib/apx/environments/test/registration.json")


class RecoveryError(RuntimeError):
    pass


def run(arguments: tuple[str, ...], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(arguments, text=True, capture_output=True, check=check,
                          env={**os.environ, "LC_ALL": "C"})


def unit_active(unit: str) -> bool:
    return run(("/usr/bin/systemctl", "is-active", "--quiet", unit), check=False).returncode == 0


def require_clean_host() -> None:
    if os.geteuid() != 0 or Path("/sys/class/tty/tty0/active").read_text().strip() != "tty1":
        raise RecoveryError("rehearsal requires root with tty1 active")
    if run(("/usr/bin/systemctl", "--failed", "--no-legend"), check=False).stdout.strip():
        raise RecoveryError("rehearsal refuses failed systemd units")
    for unit in (DUMMY_UNIT, EXPIRY_UNIT + ".timer", EXPIRY_UNIT + ".service"):
        if unit_active(unit):
            raise RecoveryError("old graphical recovery rehearsal state is active")
    if run(("/usr/bin/machinectl", "list", "--no-legend"), check=False).stdout.strip():
        raise RecoveryError("rehearsal refuses while an Environment machine exists")


def recover_dummy() -> None:
    run(("/usr/bin/systemctl", "stop", DUMMY_UNIT), check=False)
    run(("/usr/bin/chvt", "1"), check=False)
    if unit_active(DUMMY_UNIT):
        raise RecoveryError("dummy graphical unit survived recovery")
    if Path("/sys/class/tty/tty0/active").read_text().strip() != "tty1":
        raise RecoveryError("tty1 was not restored")


def mark_stopped(path: Path) -> None:
    try:
        value = json.loads(path.read_text())
        value["state"] = "stopped"
        temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
        temporary.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    except (OSError, ValueError, TypeError) as error:
        raise RecoveryError("registration recovery failed") from error
    ACTIVE_SESSION.unlink(missing_ok=True)


def recover_test() -> None:
    run(("/usr/bin/systemctl", "stop", TEST_UNIT), check=False)
    run(("/usr/bin/chvt", "1"), check=False)
    if unit_active(TEST_UNIT):
        raise RecoveryError("test graphical unit survived recovery")
    if run(("/usr/bin/machinectl", "show", TEST_MACHINE), check=False).returncode == 0:
        raise RecoveryError("test machine survived recovery")
    if Path("/sys/class/tty/tty0/active").read_text().strip() != "tty1":
        raise RecoveryError("tty1 was not restored")
    mark_stopped(TEST_REGISTRATION)


def recover_hub() -> None:
    run(("/usr/bin/systemctl", "stop", HUB_UNIT), check=False)
    run(("/usr/bin/chvt", "1"), check=False)
    if unit_active(HUB_UNIT):
        raise RecoveryError("Hub graphical unit survived recovery")
    if run(("/usr/bin/machinectl", "show", HUB_MACHINE), check=False).returncode == 0:
        raise RecoveryError("Hub machine survived recovery")
    if Path("/sys/class/tty/tty0/active").read_text().strip() != "tty1":
        raise RecoveryError("tty1 was not restored")
    mark_stopped(HUB_REGISTRATION)


def rehearse_dummy() -> None:
    require_clean_host()
    if Path(__file__).resolve() != INSTALLED_PATH:
        raise RecoveryError("recovery rehearsal must use the fixed installed asset")
    run((
        "/usr/bin/systemd-run", f"--unit={EXPIRY_UNIT}", "--on-active=3s",
        "--timer-property=AccuracySec=1s", "--property=Type=oneshot",
        "--property=NoNewPrivileges=yes", "--property=ProtectSystem=strict",
        "--property=ProtectHome=yes", "--property=PrivateNetwork=yes",
        str(INSTALLED_PATH), "--recover-dummy",
    ))
    if not unit_active(EXPIRY_UNIT + ".timer"):
        raise RecoveryError("independent expiry timer did not arm")
    run((
        "/usr/bin/systemd-run", f"--unit={DUMMY_UNIT.removesuffix('.service')}",
        "--collect", "--property=Type=simple", "--property=NoNewPrivileges=yes",
        "--property=PrivateNetwork=yes", "--property=ProtectSystem=strict",
        "--property=ProtectHome=yes", "--", "/usr/bin/sleep", "60",
    ))
    if not unit_active(DUMMY_UNIT):
        raise RecoveryError("dummy graphical unit did not start")
    deadline = time.monotonic() + 10
    while unit_active(DUMMY_UNIT) and time.monotonic() < deadline:
        time.sleep(0.2)
    if unit_active(DUMMY_UNIT):
        recover_dummy()
        raise RecoveryError("independent expiry did not recover the dummy unit")
    recover_dummy()
    run(("/usr/bin/systemctl", "stop", EXPIRY_UNIT + ".timer"), check=False)
    if run(("/usr/bin/machinectl", "list", "--no-legend"), check=False).stdout.strip():
        raise RecoveryError("machine residue exists after dummy recovery")
    if run(("/usr/bin/systemctl", "--failed", "--no-legend"), check=False).stdout.strip():
        raise RecoveryError("failed unit exists after dummy recovery")
    print(f"{PROFILE}: independent-deadline-before-dummy; tty1-restored; zero-residue")
    print(f"plan={PLAN_DIGEST}")
    print("graphics=false devices=false environment=false")


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--rehearse-dummy", action="store_true")
    mode.add_argument("--recover-dummy", action="store_true")
    mode.add_argument("--recover-test", action="store_true")
    mode.add_argument("--recover-hub", action="store_true")
    args = parser.parse_args()
    if args.recover_hub:
        recover_hub()
    elif args.recover_test:
        recover_test()
    elif args.recover_dummy:
        recover_dummy()
    else:
        rehearse_dummy()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
