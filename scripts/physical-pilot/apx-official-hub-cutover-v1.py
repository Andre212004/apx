#!/usr/bin/env python3
"""Prepare, publish, or recover the rollback-preserving official Hub cutover."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import uuid

sys.path.insert(0, "/usr/lib/apx")
from apx_official_hub_cutover import (
    NEW_RELEASE,
    OLD_GENERATION,
    OfficialHubCutoverEvidence,
    build_cutover_plan,
)


STATE = Path("/var/lib/apx")
CURRENT = STATE / "environments/hub"
TEST = STATE / "environments/hub-testes"
CANDIDATE = STATE / "quarantine/hub-official-v4-candidate"
RELEASE = STATE / "releases/hub-headless-v4"
JOURNAL = STATE / "journal/official-hub-cutover-v1.json"
OPERATIONS = STATE / "journal/operations.jsonl"


class CutoverError(RuntimeError):
    pass


def run(arguments: tuple[str, ...], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        arguments, check=check, text=True, capture_output=True,
        env={**os.environ, "LC_ALL": "C"},
    )


def atomic_json(path: Path, value: dict[str, object], mode: int = 0o600) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode)
    try:
        os.write(descriptor, (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode())
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    os.replace(temporary, path)


def read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text())
    if type(value) is not dict:
        raise CutoverError(f"JSON object is malformed: {path}")
    return value


def registration(path: Path) -> dict[str, object]:
    return read_json(path / "registration.json")


def require_host() -> None:
    if os.geteuid() != 0 or Path("/etc/hostname").read_text().strip() != "apx-host":
        raise CutoverError("cutover requires root on the exact APX Host")
    if Path("/sys/class/tty/tty0/active").read_text().strip() != "tty1":
        raise CutoverError("cutover requires tty1 recovery")
    if run(("/usr/bin/machinectl", "list", "--no-legend")).stdout.strip():
        raise CutoverError("cutover refuses a running Environment machine")


def no_uncertain_operations() -> bool:
    if not OPERATIONS.exists():
        return True
    terminal: dict[str, str] = {}
    for line in OPERATIONS.read_text().splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            return False
        if event.get("effect") == "operation" and type(event.get("operation")) is str:
            terminal[str(event["operation"])] = str(event.get("status", ""))
    return all(status not in {"started", "uncertain"} for status in terminal.values())


def prepare() -> None:
    require_host()
    if CANDIDATE.exists() or not (RELEASE / "root").is_dir():
        raise CutoverError("candidate already exists or clean release is absent")
    manifest = read_json(RELEASE / "manifest.json")
    if manifest.get("release") != NEW_RELEASE:
        raise CutoverError("clean release manifest identity differs")
    CANDIDATE.mkdir(mode=0o700)
    try:
        run(("/usr/bin/btrfs", "subvolume", "snapshot",
             str(RELEASE / "root"), str(CANDIDATE / "root")))
        run(("/usr/bin/btrfs", "property", "set", "-ts", str(CANDIDATE / "root"), "ro", "false"))
        run(("/usr/bin/btrfs", "subvolume", "create", str(CANDIDATE / "home")))
        home = CANDIDATE / "home/apx"
        home.mkdir(mode=0o700)
        os.chown(home, 1000, 1000)
        skeleton = CANDIDATE / "root/etc/skel"
        for source in sorted(skeleton.iterdir()):
            metadata = source.lstat()
            if not stat.S_ISREG(metadata.st_mode) or source.is_symlink():
                raise CutoverError("clean release skeleton is unsafe")
            target = home / source.name
            shutil.copy2(source, target, follow_symlinks=False)
            os.chown(target, 1000, 1000)
        (CANDIDATE / "root/etc/hostname").write_text("apx-hub\n")
        (CANDIDATE / "root/etc/machine-id").write_text("")
        record = {
            "schema": 1, "name": "hub", "role": "hub",
            "generation": str(uuid.uuid4()), "release": NEW_RELEASE,
            "state": "stopped", "created_at": "prepared-by-official-hub-cutover-v1",
        }
        atomic_json(CANDIDATE / "registration.json", record)
        atomic_json(CANDIDATE / "candidate.json", {
            "schema": 1, "profile": "apx-official-hub-candidate-v1",
            "release_manifest_digest": hashlib.sha256(
                (RELEASE / "manifest.json").read_bytes()
            ).hexdigest(),
            "root_source": str(RELEASE / "root"), "home_empty": True,
        }, 0o400)
    except BaseException:
        (CANDIDATE / "INCOMPLETE").write_text("preserved for recovery\n")
        raise
    print(json.dumps({
        "classification": "candidate-prepared",
        "generation": registration(CANDIDATE)["generation"],
        "path": str(CANDIDATE),
    }, sort_keys=True))


def cutover_evidence() -> OfficialHubCutoverEvidence:
    current = registration(CURRENT)
    candidate = read_json(CANDIDATE / "candidate.json")
    return OfficialHubCutoverEvidence(
        current_generation=str(current.get("generation", "")),
        current_release=str(current.get("release", "")),
        current_role=str(current.get("role", "")),
        current_stopped=current.get("state") == "stopped",
        hub_testes_absent=not TEST.exists(),
        official_candidate_ready=registration(CANDIDATE).get("release") == NEW_RELEASE
            and not (CANDIDATE / "INCOMPLETE").exists(),
        official_release_manifest_digest=str(candidate.get("release_manifest_digest", "")),
        tty1_active=Path("/sys/class/tty/tty0/active").read_text().strip() == "tty1",
        no_running_machines=not run(("/usr/bin/machinectl", "list", "--no-legend")).stdout.strip(),
        no_uncertain_operation=no_uncertain_operations(),
        rollback_paths_available=CURRENT.is_dir() and CANDIDATE.is_dir(),
    )


def rewrite_test_registration() -> None:
    value = registration(TEST)
    if value.get("generation") != OLD_GENERATION:
        raise CutoverError("preserved graphical Hub generation differs")
    value.update({"name": "hub-testes", "role": "graphical-base", "state": "stopped"})
    value["reclassified_from"] = "hub"
    value["hub_authority"] = False
    atomic_json(TEST / "registration.json", value)


def publish(approval: str) -> None:
    require_host()
    if JOURNAL.exists():
        raise CutoverError("cutover journal already exists; recover or reconcile it")
    plan = build_cutover_plan(cutover_evidence())
    if plan.classification != "ready-for-cutover":
        raise CutoverError("cutover blocked: " + ",".join(plan.blockers))
    expected = f"CUTOVER OFFICIAL HUB {plan.plan_digest}"
    if approval != expected:
        raise CutoverError("exact digest-bound cutover approval differs")
    journal = {
        "schema": 1, "profile": plan.profile, "plan_digest": plan.plan_digest,
        "stage": "prepared", "old_generation": OLD_GENERATION,
        "new_generation": registration(CANDIDATE)["generation"],
    }
    atomic_json(JOURNAL, journal)
    os.rename(CURRENT, TEST)
    journal["stage"] = "old-renamed"
    atomic_json(JOURNAL, journal)
    rewrite_test_registration()
    os.rename(CANDIDATE, CURRENT)
    journal["stage"] = "new-published"
    atomic_json(JOURNAL, journal)
    official = registration(CURRENT)
    if (official.get("name"), official.get("role"), official.get("release"), official.get("state")) != (
        "hub", "hub", NEW_RELEASE, "stopped"
    ):
        raise CutoverError("published official Hub registration differs")
    journal["stage"] = "complete"
    atomic_json(JOURNAL, journal)
    print(json.dumps({
        "classification": "cutover-complete", "plan_digest": plan.plan_digest,
        "official_generation": official["generation"],
        "preserved_test_generation": registration(TEST)["generation"],
    }, sort_keys=True))


def recover() -> None:
    require_host()
    value = read_json(JOURNAL)
    stage = value.get("stage")
    if stage == "prepared" and CURRENT.exists() and CANDIDATE.exists() and not TEST.exists():
        value["stage"] = "recovered-before-effects"
    elif stage == "old-renamed" and TEST.exists() and CANDIDATE.exists() and not CURRENT.exists():
        os.rename(TEST, CURRENT)
        old = registration(CURRENT)
        old.update({"name": "hub", "role": "hub-graphical", "state": "stopped"})
        old.pop("reclassified_from", None)
        old.pop("hub_authority", None)
        atomic_json(CURRENT / "registration.json", old)
        value["stage"] = "rolled-back-old-hub"
    elif stage in {"new-published", "complete"} and CURRENT.exists() and TEST.exists():
        rewrite_test_registration()
        value["stage"] = "complete"
    else:
        raise CutoverError("cutover state is ambiguous; state was preserved")
    atomic_json(JOURNAL, value)
    print(json.dumps({"classification": "cutover-reconciled", "stage": value["stage"]}, sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare", action="store_true")
    mode.add_argument("--plan", action="store_true")
    mode.add_argument("--publish", action="store_true")
    mode.add_argument("--recover", action="store_true")
    parser.add_argument("--approve", default="")
    arguments = parser.parse_args()
    if arguments.prepare:
        prepare()
    elif arguments.plan:
        plan = build_cutover_plan(cutover_evidence())
        print(json.dumps(plan.__dict__, sort_keys=True))
        return 0 if plan.classification == "ready-for-cutover" else 2
    elif arguments.publish:
        publish(arguments.approve)
    else:
        recover()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (CutoverError, subprocess.CalledProcessError, OSError, ValueError) as error:
        print(f"Official Hub cutover refused: {error}", file=sys.stderr)
        raise SystemExit(2)
