#!/usr/bin/env python3
"""Recover the admitted external model stack after its device appears."""

from __future__ import annotations

import subprocess
import sys


STORE_UNIT = "apx-model-store-v1.service"
OLLAMA_UNIT = "apx-ollama-v1.service"


def run(*arguments: str, timeout: int = 360, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        arguments,
        check=check,
        timeout=timeout,
        env={"PATH": "/usr/bin", "LC_ALL": "C"},
    )


def main() -> int:
    # A power loss or abrupt USB removal can leave either unit failed even
    # though the device has subsequently returned. Clear only these two
    # admitted units, then recover them in strict storage-before-model order.
    # reset-failed also returns non-zero when an inactive unit was already
    # garbage-collected from systemd's memory. Starting it below remains safe.
    run(
        "/usr/bin/systemctl", "reset-failed", STORE_UNIT, OLLAMA_UNIT,
        timeout=15, check=False,
    )
    run("/usr/bin/systemctl", "start", STORE_UNIT, timeout=120)
    model = run("/usr/bin/systemctl", "start", OLLAMA_UNIT, timeout=300, check=False)
    active = run(
        "/usr/bin/systemctl", "is-active", "--quiet", OLLAMA_UNIT,
        timeout=15, check=False,
    )
    if model.returncode or active.returncode:
        # The verified read-only store remains usable when model startup is
        # delayed. Do not reset Ollama here: that would cancel the unit's own
        # bounded Restart=on-failure retry after a transient GPU resume race.
        print(
            "APX model store recovered; model service has not reached active state",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
        print(f"APX model recovery failed safely: {error}", file=sys.stderr)
        raise SystemExit(2)
