"""Run the authorized invisible Hyprland G0 test in a disposable copy."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import atexit
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import stat
import subprocess
import time

from apx_first_boot_experiment import _descendants, _tree_content_digest
from apx_hyprland_offline_build import ROOT as BUILD_ROOT, ROOTFS as SOURCE_ROOT


MACHINE = "apx-hyprland-g0-v13"
RUNTIME_PARENT = Path("/tmp/apx-hyprland-runtime-g0-v13")
RUNTIME_ROOT = RUNTIME_PARENT / "rootfs"
EVIDENCE_ROOT = Path("/tmp/apx-hyprland-g0-evidence-v13")
INTERNAL_RENDER = Path("/dev/dri/renderD129")
AMD_PCI = Path("/sys/bus/pci/devices/0000:05:00.0")
EXPECTED_VENDOR = "0x1002"
MAX_BYTES = 3 * 1024**3
TIMEOUT_SECONDS = 120
OUTPUT_LIMIT = 1024**2
DEVELOPMENT_GID = 1002
BUILD_REPORT_DIGEST = "79aec029862f03c169afde83c97a1eb3fc67918b5826823f6c5b3e1f64831f56"


class HyprlandG0Error(RuntimeError):
    """The bounded G0 experiment is unsafe, incomplete, or left residue."""


@dataclass(frozen=True)
class HyprlandG0Report:
    schema_version: int
    build_report_digest: str
    amd_pci_identity: str
    render_device: str
    container_systemd_pid1: bool
    private_namespaces: bool
    internal_package_count: int
    transient_seatd_started: bool
    hyprland_started: bool
    headless_monitor_observed: bool
    monitor_evidence: tuple[str, ...]
    amd_render_fd_observed: bool
    forbidden_dri_nodes_visible: int
    screenshot_created_inside_copy: bool
    screenshot_bytes: int
    hyprland_exit_code: int | None
    output_sha256: str
    output_bytes: int
    source_unchanged: bool
    processes_after: int
    mounts_after: int
    runtime_copy_removed: bool
    report_digest: str


def resolve_amd_render_device() -> Path:
    try:
        if (AMD_PCI / "vendor").read_text(encoding="ascii").strip() != EXPECTED_VENDOR:
            raise HyprlandG0Error("authorized PCI identity is not AMD")
        candidates = tuple((AMD_PCI / "drm").glob("renderD*"))
    except OSError as error:
        raise HyprlandG0Error("authorized AMD render identity is unavailable") from error
    if len(candidates) != 1:
        raise HyprlandG0Error("authorized PCI identity does not resolve to exactly one render node")
    device = Path("/dev/dri") / candidates[0].name
    info = device.stat()
    sysdev = (candidates[0] / "dev").read_text(encoding="ascii").strip()
    if not stat.S_ISCHR(info.st_mode) or f"{os.major(info.st_rdev)}:{os.minor(info.st_rdev)}" != sysdev:
        raise HyprlandG0Error("AMD render node identity disagrees with sysfs")
    return device


def fixed_nspawn_command(device: Path) -> tuple[str, ...]:
    return (
        "/usr/bin/timeout", "--signal=TERM", "--kill-after=15s", f"{TIMEOUT_SECONDS}s",
        "/usr/bin/systemd-nspawn", "--directory=" + str(RUNTIME_ROOT),
        "--machine=" + MACHINE, "--hostname=" + MACHINE, "--boot",
        "--settings=no", "--register=no", "--private-network",
        "--private-users=pick", "--private-users-ownership=chown", "--console=pipe",
        "--resolv-conf=off", "--timezone=off", "--link-journal=no", "--notify-ready=yes",
        "--kill-signal=SIGRTMIN+3", "--no-new-privileges=yes",
        "--property=MemoryMax=1536M", "--property=TasksMax=512", "--property=CPUQuota=100%",
        "--property=DevicePolicy=closed", "--property=DeviceAllow=" + str(device) + " rw",
        "--drop-capability=CAP_SYS_MODULE,CAP_SYS_RAWIO,CAP_SYS_TIME,CAP_MKNOD,CAP_NET_ADMIN,CAP_NET_RAW",
        "--", "--unit=multi-user.target", "--log-target=console", "--log-level=info", "--show-status=yes",
    )


def _container_pid(parent: int) -> int | None:
    for pid in _descendants(parent):
        try:
            executable = os.readlink(Path("/proc") / str(pid) / "exe")
            status = (Path("/proc") / str(pid) / "status").read_text(encoding="ascii")
        except OSError:
            continue
        if executable.endswith("/systemd") and any(line.startswith("NSpid:") and line.split()[-1] == "1" for line in status.splitlines()):
            return pid
    return None


def _executable_descendant(parent: int, suffix: str) -> int | None:
    for pid in _descendants(parent):
        try: executable = os.readlink(Path("/proc") / str(pid) / "exe")
        except OSError: continue
        if executable.endswith(suffix):
            return pid
    return None


def _emergency_cleanup(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is None:
        process.terminate()
        try: process.wait(timeout=20)
        except subprocess.TimeoutExpired:
            process.kill()
            try: process.wait(timeout=5)
            except subprocess.TimeoutExpired: return
    deadline = time.monotonic() + 10
    while _residue() != (0, 0) and time.monotonic() < deadline:
        time.sleep(0.25)
    if _residue() == (0, 0) and RUNTIME_PARENT.exists():
        shutil.rmtree(RUNTIME_PARENT)


def _progress(message: str) -> None:
    path = EVIDENCE_ROOT / "progress-v13.log"
    descriptor = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_NOFOLLOW)
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or info.st_gid != DEVELOPMENT_GID:
            raise HyprlandG0Error("progress evidence identity changed")
        if stat.S_IMODE(info.st_mode) != 0o640:
            raise HyprlandG0Error("progress evidence permissions changed")
        os.write(descriptor, (message + "\n").encode())
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _nsenter(pid: int, command: tuple[str, ...], *, timeout: int = 20) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ("/usr/bin/nsenter", "--target", str(pid), "--mount", "--uts", "--ipc", "--net", "--pid", "--user", "--cgroup",
         "--root=/proc/" + str(pid) + "/root", "--wd=/", "--", *command),
        shell=False, stdin=subprocess.DEVNULL, capture_output=True, timeout=timeout,
        env={"LC_ALL": "C", "PATH": "/usr/bin"}, check=False,
    )


def _residue() -> tuple[int, int]:
    processes = 0
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try: command = (entry / "cmdline").read_bytes()
        except OSError: continue
        if MACHINE.encode() in command and b"apx_hyprland_g0_experiment" not in command:
            processes += 1
    mounts = sum(MACHINE in line or str(RUNTIME_PARENT) in line for line in Path("/proc/self/mountinfo").read_text().splitlines())
    return processes, mounts


def execute_g0() -> HyprlandG0Report:
    if os.geteuid() != 0:
        raise HyprlandG0Error("G0 requires administrator execution for private namespaces and the exact device")
    device = resolve_amd_render_device()
    report = json.loads((BUILD_ROOT / "build-report.json").read_text(encoding="utf-8"))
    if report.get("report_digest") != BUILD_REPORT_DIGEST or _residue() != (0, 0):
        raise HyprlandG0Error("graphical source identity changed or old runtime state exists")
    try: os.mkdir(EVIDENCE_ROOT, 0o750)
    except FileExistsError as error: raise HyprlandG0Error("G0 v13 evidence destination exists; refusing adoption") from error
    os.chown(EVIDENCE_ROOT, 0, DEVELOPMENT_GID)
    progress = os.open(
        EVIDENCE_ROOT / "progress-v13.log",
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
        0o640,
    )
    os.close(progress)
    os.chown(EVIDENCE_ROOT / "progress-v13.log", 0, DEVELOPMENT_GID)
    _progress("evidence-created")
    source_digest, _, _ = _tree_content_digest(SOURCE_ROOT)
    _progress("source-before-digested")
    try: os.mkdir(RUNTIME_PARENT, 0o700)
    except FileExistsError as error: raise HyprlandG0Error("runtime destination exists; refusing adoption") from error
    copy = subprocess.run(("/usr/bin/cp", "-a", "--reflink=auto", "--", str(SOURCE_ROOT) + "/.", str(RUNTIME_ROOT)),
                          shell=False, stdin=subprocess.DEVNULL, capture_output=True, timeout=300, check=False)
    if copy.returncode != 0:
        shutil.rmtree(RUNTIME_PARENT); raise HyprlandG0Error("runtime copy failed")
    runtime_digest, logical, allocated = _tree_content_digest(RUNTIME_ROOT)
    if runtime_digest != source_digest or logical > MAX_BYTES or allocated > MAX_BYTES:
        shutil.rmtree(RUNTIME_PARENT); raise HyprlandG0Error("runtime copy is different or oversized")
    _progress("runtime-copy-verified")
    config = RUNTIME_ROOT / "home/apx-g0/.config/hypr/g0.conf"
    config.parent.mkdir(parents=True, mode=0o755, exist_ok=True)
    config.write_text("monitor = HEADLESS-0,1920x1080@60,0x0,1\ndebug {\n  disable_logs = false\n}\nmisc {\n  disable_hyprland_logo = true\n  disable_splash_rendering = true\n}\n", encoding="utf-8")
    with (RUNTIME_ROOT / "etc/passwd").open("a", encoding="utf-8") as stream:
        stream.write("apx-g0:x:1000:1000:APX disposable G0:/home/apx-g0:/usr/bin/nologin\n")
    with (RUNTIME_ROOT / "etc/group").open("a", encoding="utf-8") as stream:
        stream.write("apx-g0:x:1000:\n")
    cache = RUNTIME_ROOT / "home/apx-g0/.cache/hyprland"
    cache.mkdir(parents=True, mode=0o700)
    for path in (RUNTIME_ROOT / "home/apx-g0", config.parent, config, cache.parent, cache):
        os.chown(path, 1000, 1000)
    nspawn = subprocess.Popen(fixed_nspawn_command(device), stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, env={"LC_ALL": "C", "PATH": "/usr/bin"})
    atexit.register(_emergency_cleanup, nspawn)
    pid = None; deadline = time.monotonic() + 30
    while time.monotonic() < deadline and nspawn.poll() is None:
        pid = _container_pid(nspawn.pid)
        if pid and (Path("/proc") / str(pid) / "root/run/systemd/system").is_dir(): break
        time.sleep(0.25)
    if pid is None:
        nspawn.terminate(); nspawn.communicate(timeout=20); shutil.rmtree(RUNTIME_PARENT)
        raise HyprlandG0Error("container systemd did not become observable")
    proc = Path("/proc") / str(pid)
    private = all(os.readlink(proc / "ns" / n) != os.readlink(Path("/proc/self/ns") / n) for n in ("pid", "mnt", "user", "net"))
    packages = sum(x.is_dir() for x in (proc / "root/var/lib/pacman/local").iterdir())
    internal_device = proc / "root" / str(INTERNAL_RENDER).lstrip("/")
    internal_device.parent.mkdir(mode=0o755, exist_ok=True)
    os.mknod(internal_device, stat.S_IFCHR | 0o666, device.stat().st_rdev)
    os.chmod(internal_device, 0o666)
    device_probe = _nsenter(
        pid,
        ("/usr/bin/setpriv", "--reuid=1000", "--regid=1000", "--clear-groups", "--",
         "/usr/bin/stat", "-Lc", "%F %a %t:%T %n", str(INTERNAL_RENDER)),
    )
    visible = tuple((proc / "root/dev/dri").iterdir())
    forbidden = sum(path.name != INTERNAL_RENDER.name for path in visible)
    setup = _nsenter(pid, ("/usr/bin/install", "-d", "-m", "0700", "-o", "1000", "-g", "1000", "/run/user/1000"))
    if setup.returncode != 0:
        raise HyprlandG0Error("temporary internal user runtime could not be prepared")
    seatd = subprocess.Popen(
        ("/usr/bin/nsenter", "--target", str(pid), "--mount", "--uts", "--ipc", "--net", "--pid", "--user", "--cgroup",
         "--root=/proc/" + str(pid) + "/root", "--wd=/", "--", "/usr/bin/env",
         "SEATD_LOGLEVEL=debug", "SEATD_VTBOUND=0",
         "/usr/bin/seatd", "-u", "apx-g0"),
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        env={"LC_ALL": "C", "PATH": "/usr/bin"},
    )
    seatd_socket = proc / "root/run/seatd.sock"
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline and seatd.poll() is None and not seatd_socket.exists():
        time.sleep(0.1)
    seatd_started = seatd.poll() is None and seatd_socket.is_socket()
    seatd_pid = _executable_descendant(seatd.pid, "/seatd") if seatd_started else None
    seatd_started = seatd_started and seatd_pid is not None
    _progress("seatd-observed=" + str(seatd_started))
    seatd_output = b""
    if not seatd_started:
        seatd_output, _ = seatd.communicate(timeout=5)
    hypr_cmd = (
        "/usr/bin/setpriv", "--reuid=1000", "--regid=1000", "--clear-groups", "--",
        "/usr/bin/env", "HOME=/home/apx-g0", "USER=apx-g0", "LOGNAME=apx-g0",
        "XDG_RUNTIME_DIR=/run/user/1000", "XDG_CACHE_HOME=/home/apx-g0/.cache", "XDG_SESSION_TYPE=wayland",
        "AQ_NO_KMS_REQUIREMENT=1", "AQ_DRM_DEVICES=" + str(INTERNAL_RENDER), "AQ_TRACE=1",
        "HYPRLAND_TRACE=1", "HYPRLAND_NO_RT=1", "HYPRLAND_NO_SD_NOTIFY=1",
        "/usr/bin/Hyprland", "--config", "/home/apx-g0/.config/hypr/g0.conf",
    )
    hypr = subprocess.Popen(("/usr/bin/nsenter", "--target", str(pid), "--mount", "--uts", "--ipc", "--net", "--pid", "--user", "--cgroup",
                             "--root=/proc/" + str(pid) + "/root", "--wd=/", "--", *hypr_cmd),
                            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            env={"LC_ALL": "C", "PATH": "/usr/bin"})
    hypr_pid = None; signature = None; monitor_lines: tuple[str, ...] = (); render_fd = False; screenshot = False; screenshot_bytes = 0
    deadline = time.monotonic() + 45
    while time.monotonic() < deadline and hypr.poll() is None:
        for candidate in _descendants(hypr.pid):
            try: executable = os.readlink(Path("/proc") / str(candidate) / "exe")
            except OSError: continue
            if executable.endswith("/Hyprland"): hypr_pid = candidate
        if hypr_pid:
            try:
                render_fd = render_fd or any(
                    os.readlink(path) == str(INTERNAL_RENDER)
                    for path in (Path("/proc") / str(hypr_pid) / "fd").iterdir()
                )
            except OSError: pass
        hypr_root = proc / "root/run/user/1000/hypr"
        if hypr_root.is_dir():
            entries = tuple(path for path in hypr_root.iterdir() if path.is_dir())
            if entries: signature = entries[0].name
        if signature:
            query = _nsenter(pid, ("/usr/bin/setpriv", "--reuid=1000", "--regid=1000", "--clear-groups", "--",
                                   "/usr/bin/env", "XDG_RUNTIME_DIR=/run/user/1000", "HYPRLAND_INSTANCE_SIGNATURE=" + signature,
                                   "/usr/bin/hyprctl", "-j", "monitors"))
            text = query.stdout.decode("utf-8", "replace")
            if query.returncode == 0 and "HEADLESS-0" in text:
                monitor_lines = (text[:4096],); break
        time.sleep(0.25)
    headless = any("HEADLESS-0" in line for line in monitor_lines)
    _progress("headless-observed=" + str(headless))
    if headless and signature:
        shot = _nsenter(pid, ("/usr/bin/setpriv", "--reuid=1000", "--regid=1000", "--clear-groups", "--",
                              "/usr/bin/env", "XDG_RUNTIME_DIR=/run/user/1000", "WAYLAND_DISPLAY=wayland-1",
                              "/usr/bin/grim", "/tmp/apx-g0.png"))
        shot_path = proc / "root/tmp/apx-g0.png"
        screenshot = shot.returncode == 0 and shot_path.is_file()
        if screenshot: screenshot_bytes = shot_path.stat().st_size
    hypr_output = b""
    if hypr.poll() is None:
        hypr.send_signal(signal.SIGTERM)
        try: hypr_output, _ = hypr.communicate(timeout=15)
        except subprocess.TimeoutExpired: hypr.kill(); hypr_output, _ = hypr.communicate(timeout=5)
    else:
        hypr_output, _ = hypr.communicate(timeout=5)
    crash_reports = sorted((proc / "root/home/apx-g0/.cache/hyprland").glob("hyprlandCrashReport*.txt"))
    if crash_reports:
        try:
            crash = crash_reports[-1].read_bytes()
        except OSError:
            crash = b""
        hypr_output += b"\n--- APX PRESERVED HYPRLAND CRASH REPORT ---\n" + crash
    if len(hypr_output) > OUTPUT_LIMIT:
        hypr_output = hypr_output[-OUTPUT_LIMIT:]
    _progress("hyprland-stopped")
    hypr_output += b"\n--- APX INTERNAL DEVICE PROBE ---\n" + device_probe.stdout + device_probe.stderr
    if seatd.poll() is None:
        if seatd_pid is not None:
            os.kill(seatd_pid, signal.SIGTERM)
        else:
            seatd.terminate()
        try: seatd_output, _ = seatd.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            if seatd_pid is not None:
                try: os.kill(seatd_pid, signal.SIGKILL)
                except ProcessLookupError: pass
            seatd.kill(); seatd_output, _ = seatd.communicate(timeout=5)
    else:
        if not seatd_output:
            seatd_output, _ = seatd.communicate(timeout=5)
    hypr_output += b"\n--- APX TRANSIENT SEATD OUTPUT ---\n" + seatd_output[-65536:]
    if len(hypr_output) > OUTPUT_LIMIT:
        hypr_output = hypr_output[-OUTPUT_LIMIT:]
    for candidate in _descendants(nspawn.pid):
        try:
            if b"systemd-nspawn" in (Path("/proc") / str(candidate) / "cmdline").read_bytes(): os.kill(candidate, signal.SIGTERM)
        except OSError: pass
    try: nspawn.communicate(timeout=30)
    except subprocess.TimeoutExpired: nspawn.kill(); nspawn.communicate(timeout=5)
    deadline = time.monotonic() + 15
    residue = _residue()
    while residue != (0, 0) and time.monotonic() < deadline:
        time.sleep(0.25); residue = _residue()
    _progress("container-stopped-residue=" + str(residue))
    after_digest, _, _ = _tree_content_digest(SOURCE_ROOT)
    _progress("source-after-digested")
    unchanged = source_digest == after_digest
    if residue == (0, 0): shutil.rmtree(RUNTIME_PARENT)
    removed = not RUNTIME_PARENT.exists()
    _progress("runtime-removed=" + str(removed))
    if removed:
        atexit.unregister(_emergency_cleanup)
    draft = {"schema_version": 1, "build_report_digest": BUILD_REPORT_DIGEST,
             "amd_pci_identity": str(AMD_PCI), "render_device": str(device),
             "container_systemd_pid1": pid is not None, "private_namespaces": private,
             "internal_package_count": packages, "transient_seatd_started": seatd_started,
             "hyprland_started": hypr_pid is not None,
             "headless_monitor_observed": headless, "monitor_evidence": monitor_lines,
             "amd_render_fd_observed": render_fd, "forbidden_dri_nodes_visible": forbidden,
             "screenshot_created_inside_copy": screenshot, "screenshot_bytes": screenshot_bytes,
             "hyprland_exit_code": hypr.returncode,
             "output_sha256": hashlib.sha256(hypr_output).hexdigest(), "output_bytes": len(hypr_output),
             "source_unchanged": unchanged, "processes_after": residue[0], "mounts_after": residue[1],
             "runtime_copy_removed": removed}
    digest = hashlib.sha256(json.dumps(draft, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    result = HyprlandG0Report(**draft, report_digest=digest)
    output = EVIDENCE_ROOT / "g0-report-v13.json"
    fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o640)
    try: os.write(fd, (json.dumps(asdict(result), sort_keys=True, indent=2) + "\n").encode()); os.fsync(fd)
    finally: os.close(fd)
    fd = os.open(EVIDENCE_ROOT / "hyprland-output-v13.log", os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o640)
    try: os.write(fd, hypr_output); os.fsync(fd)
    finally: os.close(fd)
    os.chown(output, 0, DEVELOPMENT_GID)
    os.chown(EVIDENCE_ROOT / "hyprland-output-v13.log", 0, DEVELOPMENT_GID)
    _progress("evidence-complete")
    if residue != (0, 0) or not unchanged or not removed:
        raise HyprlandG0Error("G0 ended with residue, source change, or retained runtime copy")
    return result


def main() -> int:
    result = execute_g0()
    print("APX Hyprland invisible G0 test")
    for label, value in (("Systemd PID 1", result.container_systemd_pid1), ("Private namespaces", result.private_namespaces),
                         ("Packages", result.internal_package_count), ("Transient seatd", result.transient_seatd_started),
                         ("Hyprland started", result.hyprland_started),
                         ("HEADLESS-0", result.headless_monitor_observed), ("AMD render used", result.amd_render_fd_observed),
                         ("Other DRM nodes visible", result.forbidden_dri_nodes_visible), ("Internal screenshot", result.screenshot_created_inside_copy),
                         ("Processes after", result.processes_after), ("Mounts after", result.mounts_after),
                         ("Source unchanged", result.source_unchanged), ("Runtime removed", result.runtime_copy_removed)):
        print(f"{label}: {value}")
    print(f"Report digest: {result.report_digest}")
    return 0


if __name__ == "__main__": raise SystemExit(main())
