"""Deterministic, non-executing preview for the first APX console boot."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path

from apx_offline_base_build import ROOTFS


MACHINE = "apx-first-console-v1"
FINAL_REPORT_DIGEST = "741fe1c332c334f9f0667b295ae98e7de686c752c3f415e169e0e48912535b68"
TIMEOUT_SECONDS = 120
MEMORY_MAX = "512M"
TASKS_MAX = "256"
CPU_QUOTA = "50%"
RUNTIME_ROOT = Path("/tmp/apx-first-console-runtime-v4/rootfs")
RUNTIME_MAX_BYTES = 1024**3


@dataclass(frozen=True)
class FirstBootPreview:
    schema_version: int
    machine: str
    source_root: str
    final_report_digest: str
    command: tuple[str, ...]
    allowed_effects: tuple[str, ...]
    forbidden_effects: tuple[str, ...]
    pass_conditions: tuple[str, ...]
    preview_digest: str


def fixed_command() -> tuple[str, ...]:
    return (
        "/usr/bin/timeout", "--signal=TERM", "--kill-after=15s", f"{TIMEOUT_SECONDS}s",
        "/usr/bin/systemd-nspawn", "--directory=" + str(RUNTIME_ROOT),
        "--machine=" + MACHINE, "--hostname=" + MACHINE, "--boot",
        "--settings=no", "--register=no",
        "--private-network", "--private-users=pick",
        "--private-users-ownership=chown", "--console=pipe",
        "--resolv-conf=off", "--timezone=off", "--link-journal=no",
        "--notify-ready=yes", "--kill-signal=SIGRTMIN+3",
        "--no-new-privileges=yes", "--rlimit=CORE=0",
        "--property=MemoryMax=" + MEMORY_MAX,
        "--property=TasksMax=" + TASKS_MAX,
        "--property=CPUQuota=" + CPU_QUOTA,
        "--property=DevicePolicy=closed",
        "--drop-capability=CAP_SYS_MODULE,CAP_SYS_RAWIO,CAP_SYS_TIME,CAP_MKNOD,CAP_NET_ADMIN,CAP_NET_RAW",
        "--", "--unit=multi-user.target",
    )


def build_preview() -> FirstBootPreview:
    command = fixed_command()
    if any(value.startswith(("--bind=", "--bind-ro=", "--network-veth", "--port=")) for value in command):
        raise ValueError("first boot command exposes a forbidden host resource")
    draft = {
        "schema_version": 1, "machine": MACHINE, "source_root": str(ROOTFS),
        "final_report_digest": FINAL_REPORT_DIGEST, "command": command,
        "allowed_effects": (
            "start one temporary systemd-nspawn process tree for at most 120 seconds",
            "create one exact temporary runtime copy below /tmp, capped at 1 GiB",
            "shift ownership only in the temporary copy for private user isolation",
            "create transient mount, namespace, and cgroup runtime state",
            "write only to the disposable runtime copy and bounded process output",
        ),
        "forbidden_effects": (
            "change the verified source root or any host package/configuration",
            "use external networking or expose a host port",
            "share host home, GPU, audio, removable devices, or credentials",
            "create a persistent machine registration, service, user, or Btrfs resource",
            "download, install, or clean up previous experiment areas",
            "retain the temporary runtime copy after verified shutdown",
        ),
        "pass_conditions": (
            "container systemd reports ready before the timeout",
            "the internal Arch identity and 138-package database are visible",
            "the host Development home and host package database are not visible",
            "shutdown leaves no matching process, mount, cgroup, namespace, or registration",
            "the verified source root and final report digest remain unchanged",
        ),
    }
    digest = hashlib.sha256(json.dumps(draft, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return FirstBootPreview(**draft, preview_digest=digest)


def main() -> int:
    preview = build_preview()
    print(json.dumps(asdict(preview), sort_keys=True, indent=2))
    print("EXECUTION: no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
