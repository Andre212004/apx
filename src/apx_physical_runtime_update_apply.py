"""Apply only the reviewed graphical-H0 Host runtime update."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import tarfile

from apx_physical_update import PhysicalUpdateCandidate
from apx_physical_update_artifact import inspect_artifact


UPDATE_ID = "update-a1b55982d14fb0bdf7afa8f1dd7991ca"
ARTIFACT = Path("/tmp/apx-hyprland-runtime-update-aa53683/candidate.tar")
TARGET = Path("/usr/lib/apx/apx-lab-runtime.py")
ALIAS = Path("/usr/bin/apx")
STATE = Path("/var/lib/apx")
STAGING = STATE / "updates/staging" / UPDATE_ID
ROLLBACK = STATE / "updates/rollback" / UPDATE_ID
RESULT = STATE / "updates/installed" / f"{UPDATE_ID}.json"
BEFORE_SHA256 = "5151b89ed53561c1e1f12b05b0b0c50dee483caa8e47f4c2ee397d767ded2b17"
AFTER_SHA256 = "0d7cc0c0c0631b65f68639f8b4994e3e3441a817604487256a30edd82f96da9f"
ARTIFACT_SHA256 = "a1b55982d14fb0bdf7afa8f1dd7991caf9d3a7ad5e24b321510763ad5b675a66"
MANIFEST_SHA256 = "62f5070ba016ac497f69dae6b6de78cbd2e07d033afd16306015cb3d8197f5fa"
GENERATIONS = {
    "development": "b90155f6-ece2-44ae-91fc-42d91d6b35a5",
    "hub": "d68ee7a2-268a-4534-b033-8f5313943fcf",
    "codex-test-lifecycle-v1": "1ec52013-e715-413a-bb48-b4691cf31ee9",
}
CANDIDATE = PhysicalUpdateCandidate(
    1, "apx-physical-headless-pilot-update-v1", UPDATE_ID,
    "aa5368315560341b4c6ab7d6736483bd80339134",
    "02fd4bafd7b851bce0bc0d9aa140bdca89240088", ARTIFACT_SHA256, 30720,
    MANIFEST_SHA256, 2, ("host-runtime",),
    "e71b5dba3bae19934b618a8f093970452b1e9a7603785d53ed1143cca6ae7951",
    682, 8, "a7fd48db155937036fb09d06eb5310cf67c9f9357d2004ad54d104b5027a048f",
    "60f149a106caf340b68bfec6b501ca5a35c1b65bfc9e7ae8c1f74289fdc8f0c0",
    "dc6547c863111b346a7de644a4d3643d129943ba52c6c2f498d3a618978f0550",
    True, True, True, True, True,
)


class RuntimeUpdateError(RuntimeError):
    pass


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _run(arguments: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(arguments, check=False, text=True, capture_output=True, env={**os.environ, "LC_ALL": "C"})


def _registration(name: str) -> dict[str, object]:
    path = STATE / "environments" / name / "registration.json"
    value = json.loads(path.read_text())
    if value.get("name") != name or value.get("generation") != GENERATIONS[name] or value.get("state") != "stopped":
        raise RuntimeUpdateError(f"{name} registration is not the approved stopped generation")
    return value


def _regular_root_file(path: Path, mode: int) -> bytes:
    information = path.lstat()
    if not stat.S_ISREG(information.st_mode) or information.st_uid != 0 or stat.S_IMODE(information.st_mode) != mode:
        raise RuntimeUpdateError(f"{path} is not the expected root-owned regular file")
    return path.read_bytes()


def preflight() -> bytes:
    if os.geteuid() != 0:
        raise RuntimeUpdateError("runtime update requires root")
    if STAGING.exists() or ROLLBACK.exists() or RESULT.exists():
        raise RuntimeUpdateError("update state already exists; preserve and inspect")
    artifact = _regular_root_file(ARTIFACT, 0o600)
    if len(artifact) != 30720 or _sha(artifact) != ARTIFACT_SHA256:
        raise RuntimeUpdateError("candidate artifact identity changed")
    inspect_artifact(artifact, CANDIDATE)
    installed = _regular_root_file(TARGET, 0o755)
    if _sha(installed) != BEFORE_SHA256:
        raise RuntimeUpdateError("installed runtime identity changed")
    if not ALIAS.is_symlink() or ALIAS.resolve() != TARGET:
        raise RuntimeUpdateError("runtime alias changed")
    for name in GENERATIONS:
        _registration(name)
        machine = _run(["machinectl", "show", f"apx-{name}", "--property=State", "--value"])
        if machine.returncode == 0 and machine.stdout.strip() in {"running", "degraded"}:
            raise RuntimeUpdateError(f"{name} is unexpectedly running")
    if _run(["systemctl", "--failed", "--no-legend"]).stdout.strip():
        raise RuntimeUpdateError("Host has failed systemd units")
    release = _run(["btrfs", "property", "get", "-ts", str(STATE / "releases/hyprland-h0-v1/root"), "ro"])
    if release.returncode != 0 or "ro=true" not in release.stdout:
        raise RuntimeUpdateError("Hyprland release is not immutable")
    return artifact


def _write_exact(path: Path, data: bytes, mode: int) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data); stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary, path)
        os.chmod(path, mode)
    finally:
        temporary.unlink(missing_ok=True)


def apply_update() -> dict[str, object]:
    artifact = preflight()
    STAGING.mkdir(parents=True, mode=0o700)
    _write_exact(STAGING / "candidate.tar", artifact, 0o600)
    ROLLBACK.mkdir(parents=True, mode=0o700)
    installed = TARGET.read_bytes()
    _write_exact(ROLLBACK / "host-runtime", installed, 0o500)
    with tarfile.open(ARTIFACT, mode="r:") as archive:
        stream = archive.extractfile("components/host-runtime")
        if stream is None:
            raise RuntimeUpdateError("candidate runtime is unreadable")
        candidate_runtime = stream.read()
    if _sha(candidate_runtime) != AFTER_SHA256:
        raise RuntimeUpdateError("candidate runtime identity changed after verification")
    _write_exact(TARGET, candidate_runtime, 0o755)
    if _sha(TARGET.read_bytes()) != AFTER_SHA256 or ALIAS.resolve() != TARGET:
        raise RuntimeUpdateError("installed runtime final verification failed; retain rollback")
    for name in GENERATIONS:
        _registration(name)
    result = {
        "schema": 1, "update_id": UPDATE_ID, "before_sha256": BEFORE_SHA256,
        "after_sha256": AFTER_SHA256, "artifact_sha256": ARTIFACT_SHA256,
        "rollback_retained": True, "hub_generation": GENERATIONS["hub"],
        "development_generation": GENERATIONS["development"],
    }
    RESULT.parent.mkdir(parents=True, mode=0o700)
    _write_exact(RESULT, (json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n").encode(), 0o400)
    return result


if __name__ == "__main__":
    print(json.dumps(apply_update(), sort_keys=True, indent=2))
