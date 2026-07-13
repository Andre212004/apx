"""Render the fixed, non-executing Hyprland G1 nested-session preview."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
import stat

from apx_hyprland_offline_build import ROOT as BUILD_ROOT, ROOTFS as SOURCE_ROOT


HOST_RUNTIME = Path("/run/user/1002")
HOST_WAYLAND = HOST_RUNTIME / "wayland-0"
INTERNAL_WAYLAND = Path("/run/apx-host-wayland/wayland-0")
HOST_RENDER = Path("/dev/dri/renderD129")
INTERNAL_RENDER = Path("/dev/dri/renderD129")
RUNTIME_PARENT = Path("/tmp/apx-hyprland-runtime-g1-v5")
RUNTIME_ROOT = RUNTIME_PARENT / "rootfs"
MACHINE = "apx-hyprland-g1-v5"
TIMEOUT_SECONDS = 120
MAX_BYTES = 3 * 1024**3
BUILD_REPORT_DIGEST = "79aec029862f03c169afde83c97a1eb3fc67918b5826823f6c5b3e1f64831f56"


class HyprlandG1PreviewError(RuntimeError):
    """The fixed nested-session preview cannot be trusted."""


@dataclass(frozen=True)
class HyprlandG1Preview:
    schema_version: int
    build_report_digest: str
    host_wayland_socket: str
    host_wayland_uid: int
    host_wayland_mode: int
    internal_wayland_socket: str
    direct_drm_devices: tuple[str, ...]
    network_private: bool
    host_home_shared: bool
    host_dbus_shared: bool
    host_pipewire_shared: bool
    temporary_socket_acl: bool
    exact_acl_restoration_required: bool
    timeout_seconds: int
    maximum_runtime_bytes: int
    command: tuple[str, ...]
    preview_digest: str


def validate_host_wayland() -> os.stat_result:
    runtime = HOST_RUNTIME.lstat()
    socket = HOST_WAYLAND.lstat()
    if (
        not stat.S_ISDIR(runtime.st_mode)
        or runtime.st_uid != 1002
        or stat.S_IMODE(runtime.st_mode) != 0o700
        or not stat.S_ISSOCK(socket.st_mode)
        or socket.st_uid != 1002
        or stat.S_IMODE(socket.st_mode) != 0o755
    ):
        raise HyprlandG1PreviewError("KDE Wayland socket identity or permissions changed")
    return socket


def fixed_nspawn_command() -> tuple[str, ...]:
    return (
        "/usr/bin/timeout", "--signal=TERM", "--kill-after=15s", f"{TIMEOUT_SECONDS}s",
        "/usr/bin/systemd-nspawn", "--directory=" + str(RUNTIME_ROOT),
        "--machine=" + MACHINE, "--hostname=" + MACHINE, "--boot",
        "--settings=no", "--register=no", "--private-network",
        "--private-users=pick", "--private-users-ownership=chown", "--console=pipe",
        "--resolv-conf=off", "--timezone=off", "--link-journal=no", "--notify-ready=yes",
        "--kill-signal=SIGRTMIN+3", "--no-new-privileges=yes",
        "--property=MemoryMax=1536M", "--property=TasksMax=512", "--property=CPUQuota=100%",
        "--property=DevicePolicy=closed",
        "--property=DeviceAllow=" + str(HOST_RENDER) + " rw",
        "--bind-ro=" + str(HOST_WAYLAND) + ":" + str(INTERNAL_WAYLAND),
        "--drop-capability=CAP_SYS_MODULE,CAP_SYS_RAWIO,CAP_SYS_TIME,CAP_MKNOD,CAP_NET_ADMIN,CAP_NET_RAW",
        "--", "--unit=multi-user.target", "--log-target=console", "--log-level=info", "--show-status=yes",
    )


def build_preview() -> HyprlandG1Preview:
    validate_host_wayland()
    try:
        report = json.loads((BUILD_ROOT / "build-report.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise HyprlandG1PreviewError("graphical build report is unavailable") from error
    if report.get("report_digest") != BUILD_REPORT_DIGEST or not SOURCE_ROOT.is_dir():
        raise HyprlandG1PreviewError("graphical source identity changed")
    command = fixed_nspawn_command()
    draft = {
        "schema_version": 1,
        "build_report_digest": BUILD_REPORT_DIGEST,
        "host_wayland_socket": str(HOST_WAYLAND),
        "host_wayland_uid": 1002,
        "host_wayland_mode": 0o755,
        "internal_wayland_socket": str(INTERNAL_WAYLAND),
        "direct_drm_devices": (str(HOST_RENDER),),
        "network_private": True,
        "host_home_shared": False,
        "host_dbus_shared": False,
        "host_pipewire_shared": False,
        "temporary_socket_acl": True,
        "exact_acl_restoration_required": True,
        "timeout_seconds": TIMEOUT_SECONDS,
        "maximum_runtime_bytes": MAX_BYTES,
        "command": command,
    }
    digest = hashlib.sha256(json.dumps(draft, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return HyprlandG1Preview(**draft, preview_digest=digest)


def main() -> int:
    preview = build_preview()
    print("APX Hyprland G1 nested-session preview; no execution")
    print(f"Graphical root: {preview.build_report_digest}")
    print(f"Host Wayland: {preview.host_wayland_socket} -> {preview.internal_wayland_socket}")
    print(f"Direct DRM devices: {len(preview.direct_drm_devices)}")
    print(f"Private network: {preview.network_private}")
    print(f"Host home/D-Bus/PipeWire shared: {preview.host_home_shared}/{preview.host_dbus_shared}/{preview.host_pipewire_shared}")
    print(f"Temporary exact-UID socket ACL with restoration: {preview.temporary_socket_acl}/{preview.exact_acl_restoration_required}")
    print(f"Timeout: {preview.timeout_seconds}s; runtime ceiling: {preview.maximum_runtime_bytes}")
    print(f"Preview digest: {preview.preview_digest}")
    print("Container/window/GPU/input/audio/network/system effects: none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
