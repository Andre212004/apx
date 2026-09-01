"""Stage only the three reviewed H0 assets into fixed private Host state."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat

from apx_hyprland_h0_launch_plan import ASSETS, EXPERIMENT, GENERATION, STATE


REPOSITORY = Path("/root/apx-host-development-mode-v1/apx")
SOURCES = {
    "hyprland.conf": REPOSITORY / "config/hyprland-h0.conf",
    "session": REPOSITORY / "scripts/physical-pilot/hyprland-h0-session-v1.sh",
    "watchdog": REPOSITORY / "scripts/physical-pilot/hyprland-h0-watchdog-v1.sh",
}
DESTINATION = Path(STATE)
REGISTRATION = Path("/var/lib/apx/environments/codex-test-hyprland-h0-v1/registration.json")
RESULT = DESTINATION / "staging-result.json"


class H0StageError(RuntimeError):
    pass


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _source(name: str, expected: str) -> bytes:
    path = SOURCES[name]
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid != 0:
        raise H0StageError("H0 source asset is not a root-owned regular file")
    data = path.read_bytes()
    if _sha(data) != expected:
        raise H0StageError("H0 source asset identity changed")
    return data


def _write(path: Path, data: bytes, mode: int) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(data); stream.flush(); os.fsync(stream.fileno())
    os.chmod(path, mode)


def stage_assets() -> dict[str, object]:
    if os.geteuid() != 0 or DESTINATION.exists():
        raise H0StageError("H0 staging requires root and an absent exact destination")
    registration = json.loads(REGISTRATION.read_text())
    if registration.get("generation") != GENERATION or registration.get("state") != "stopped" or registration.get("role") != "graphical-h0":
        raise H0StageError("H0 Environment is not the exact stopped generation")
    content = {name: _source(name, digest) for name, digest, _ in ASSETS}
    DESTINATION.mkdir(parents=True, mode=0o700)
    try:
        for name, digest, mode in ASSETS:
            _write(DESTINATION / name, content[name], mode)
            if _sha((DESTINATION / name).read_bytes()) != digest:
                raise H0StageError("staged H0 asset failed final verification")
        result = {"schema": 1, "experiment": EXPERIMENT, "generation": GENERATION,
            "assets": [[name, digest, mode] for name, digest, mode in ASSETS],
            "graphical_activation": False}
        _write(RESULT, (json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n").encode(), 0o400)
        return result
    except BaseException:
        # Preserve any partial exact destination for inspection; never adopt or delete it.
        raise


if __name__ == "__main__":
    print(json.dumps(stage_assets(), sort_keys=True, indent=2))
