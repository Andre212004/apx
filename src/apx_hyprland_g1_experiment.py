"""Run the authorized visible Hyprland G1 test in a disposable nested session."""

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
import traceback

from apx_first_boot_experiment import _descendants, _tree_content_digest
from apx_hyprland_g1_preview import (
    BUILD_REPORT_DIGEST, BUILD_ROOT, HOST_WAYLAND, INTERNAL_WAYLAND,
    HOST_RENDER, INTERNAL_RENDER, MACHINE, MAX_BYTES, RUNTIME_PARENT, RUNTIME_ROOT, SOURCE_ROOT,
    TIMEOUT_SECONDS, fixed_nspawn_command, validate_host_wayland,
)


from apx_hyprland_g0_experiment import resolve_amd_render_device


EVIDENCE_ROOT = Path("/tmp/apx-hyprland-g1-evidence-v5")
OUTPUT_LIMIT = 1024**2
DEVELOPMENT_GID = 1002


class HyprlandG1Error(RuntimeError):
    """The bounded G1 experiment is unsafe, incomplete, or left residue."""


@dataclass(frozen=True)
class HyprlandG1Report:
    schema_version: int
    build_report_digest: str
    host_wayland_socket: str
    container_systemd_pid1: bool
    private_namespaces: bool
    internal_package_count: int
    direct_drm_nodes_visible: int
    host_home_visible: bool
    temporary_socket_acl_applied: bool
    host_wayland_acl_restored: bool
    hyprland_started: bool
    nested_monitor_observed: bool
    monitor_evidence: tuple[str, ...]
    internal_screenshot_created: bool
    internal_screenshot_bytes: int
    hyprland_exit_code: int | None
    output_sha256: str
    output_bytes: int
    source_unchanged: bool
    processes_after: int
    mounts_after: int
    runtime_copy_removed: bool
    report_digest: str


def _container_pid(parent: int) -> int | None:
    for pid in _descendants(parent):
        try:
            executable = os.readlink(Path("/proc") / str(pid) / "exe")
            status = (Path("/proc") / str(pid) / "status").read_text(encoding="ascii")
        except OSError:
            continue
        if executable.endswith("/systemd") and any(
            line.startswith("NSpid:") and line.split()[-1] == "1"
            for line in status.splitlines()
        ):
            return pid
    return None


def _residue() -> tuple[int, int]:
    processes = 0
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            command = (entry / "cmdline").read_bytes()
        except OSError:
            continue
        if MACHINE.encode() in command and b"apx_hyprland_g1_experiment" not in command:
            processes += 1
    mounts = sum(
        MACHINE in line or str(RUNTIME_PARENT) in line
        for line in Path("/proc/self/mountinfo").read_text().splitlines()
    )
    return processes, mounts


def _cleanup(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=20)
        except subprocess.TimeoutExpired:
            process.kill()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                return
    deadline = time.monotonic() + 10
    while _residue() != (0, 0) and time.monotonic() < deadline:
        time.sleep(0.25)
    if _residue() == (0, 0) and RUNTIME_PARENT.exists():
        shutil.rmtree(RUNTIME_PARENT)


def _restore_wayland_acl(snapshot: Path) -> None:
    result = subprocess.run(
        ("/usr/bin/setfacl", "--restore=" + str(snapshot)),
        shell=False, stdin=subprocess.DEVNULL, capture_output=True, timeout=10,
        env={"LC_ALL": "C", "PATH": "/usr/bin"}, check=False,
    )
    if result.returncode != 0:
        return


def _mapped_host_uid(pid: int, internal_uid: int) -> int:
    for line in (Path("/proc") / str(pid) / "uid_map").read_text(encoding="ascii").splitlines():
        inside, outside, length = (int(value) for value in line.split())
        if inside <= internal_uid < inside + length:
            return outside + internal_uid - inside
    raise HyprlandG1Error("internal UID is absent from the private-user mapping")


def _progress(message: str) -> None:
    path = EVIDENCE_ROOT / "progress-v1.log"
    descriptor = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_NOFOLLOW)
    try:
        info = os.fstat(descriptor)
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_uid != 0
            or info.st_gid != DEVELOPMENT_GID
            or stat.S_IMODE(info.st_mode) != 0o640
        ):
            raise HyprlandG1Error("progress evidence identity changed")
        os.write(descriptor, (message + "\n").encode())
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _nsenter(pid: int, command: tuple[str, ...], *, timeout: int = 20) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        (
            "/usr/bin/nsenter", "--target", str(pid), "--mount", "--uts", "--ipc",
            "--net", "--pid", "--user", "--cgroup", "--root=/proc/" + str(pid) + "/root",
            "--wd=/", "--", *command,
        ),
        shell=False, stdin=subprocess.DEVNULL, capture_output=True, timeout=timeout,
        env={"LC_ALL": "C", "PATH": "/usr/bin"}, check=False,
    )


def execute_g1() -> HyprlandG1Report:
    if os.geteuid() != 0:
        raise HyprlandG1Error("G1 requires administrator execution for private namespaces")
    validate_host_wayland()
    device = resolve_amd_render_device()
    if device != HOST_RENDER:
        raise HyprlandG1Error("resolved AMD render identity changed")
    report = json.loads((BUILD_ROOT / "build-report.json").read_text(encoding="utf-8"))
    if report.get("report_digest") != BUILD_REPORT_DIGEST or _residue() != (0, 0):
        raise HyprlandG1Error("graphical source identity changed or old runtime state exists")
    try:
        os.mkdir(EVIDENCE_ROOT, 0o750)
    except FileExistsError as error:
        raise HyprlandG1Error("G1 evidence destination exists; refusing adoption") from error
    os.chown(EVIDENCE_ROOT, 0, DEVELOPMENT_GID)
    progress = os.open(
        EVIDENCE_ROOT / "progress-v1.log",
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
        0o640,
    )
    os.close(progress)
    os.chown(EVIDENCE_ROOT / "progress-v1.log", 0, DEVELOPMENT_GID)
    _progress("evidence-created")
    source_digest, _, _ = _tree_content_digest(SOURCE_ROOT)
    _progress("source-before-digested")
    try:
        os.mkdir(RUNTIME_PARENT, 0o700)
    except FileExistsError as error:
        raise HyprlandG1Error("G1 runtime destination exists; refusing adoption") from error
    copy = subprocess.run(
        ("/usr/bin/cp", "-a", "--reflink=auto", "--", str(SOURCE_ROOT) + "/.", str(RUNTIME_ROOT)),
        shell=False, stdin=subprocess.DEVNULL, capture_output=True, timeout=300, check=False,
    )
    if copy.returncode != 0:
        shutil.rmtree(RUNTIME_PARENT)
        raise HyprlandG1Error("runtime copy failed")
    runtime_digest, logical, allocated = _tree_content_digest(RUNTIME_ROOT)
    if runtime_digest != source_digest or logical > MAX_BYTES or allocated > MAX_BYTES:
        shutil.rmtree(RUNTIME_PARENT)
        raise HyprlandG1Error("runtime copy is different or oversized")
    _progress("runtime-copy-verified")

    home = RUNTIME_ROOT / "home/apx-g1"
    config = home / ".config/hypr/g1.conf"
    config.parent.mkdir(parents=True, mode=0o755, exist_ok=True)
    config.write_text(
        "monitor = ,1280x720@60,auto,1\n"
        "exec-once = foot --title 'APX G1 nested proof'\n"
        "debug {\n  disable_logs = false\n}\n"
        "misc {\n  disable_hyprland_logo = true\n  disable_splash_rendering = true\n}\n",
        encoding="utf-8",
    )
    with (RUNTIME_ROOT / "etc/passwd").open("a", encoding="utf-8") as stream:
        stream.write("apx-g1:x:1000:1000:APX disposable G1:/home/apx-g1:/usr/bin/nologin\n")
    with (RUNTIME_ROOT / "etc/group").open("a", encoding="utf-8") as stream:
        stream.write("apx-g1:x:1000:\n")
    cache = home / ".cache/hyprland"
    cache.mkdir(parents=True, mode=0o700)
    for path in (home, config.parent.parent, config.parent, config, cache.parent, cache):
        os.chown(path, 1000, 1000)

    nspawn = subprocess.Popen(
        fixed_nspawn_command(), stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, env={"LC_ALL": "C", "PATH": "/usr/bin"},
    )
    atexit.register(_cleanup, nspawn)
    pid = None
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline and nspawn.poll() is None:
        pid = _container_pid(nspawn.pid)
        if pid and (Path("/proc") / str(pid) / "root/run/systemd/system").is_dir():
            break
        time.sleep(0.25)
    if pid is None:
        _cleanup(nspawn)
        raise HyprlandG1Error("container systemd did not become observable")
    proc = Path("/proc") / str(pid)
    private = all(
        os.readlink(proc / "ns" / name) != os.readlink(Path("/proc/self/ns") / name)
        for name in ("pid", "mnt", "user", "net")
    )
    packages = sum(path.is_dir() for path in (proc / "root/var/lib/pacman/local").iterdir())
    internal_device = proc / "root" / str(INTERNAL_RENDER).lstrip("/")
    internal_device.parent.mkdir(mode=0o755, exist_ok=True)
    os.mknod(internal_device, stat.S_IFCHR | 0o666, device.stat().st_rdev)
    os.chmod(internal_device, 0o666)
    dri = proc / "root/dev/dri"
    direct_drm = sum(1 for _ in dri.iterdir()) if dri.is_dir() else 0
    host_home = (proc / "root/home/apx-development").exists()
    setup = _nsenter(pid, ("/usr/bin/install", "-d", "-m", "0700", "-o", "1000", "-g", "1000", "/run/user/1000"))
    if setup.returncode != 0:
        _cleanup(nspawn)
        raise HyprlandG1Error("temporary internal user runtime could not be prepared")

    acl_snapshot = EVIDENCE_ROOT / "wayland-acl-before-v5.txt"
    baseline = subprocess.run(
        ("/usr/bin/getfacl", "-p", str(HOST_WAYLAND)), shell=False,
        stdin=subprocess.DEVNULL, capture_output=True, timeout=10,
        env={"LC_ALL": "C", "PATH": "/usr/bin"}, check=False,
    )
    if baseline.returncode != 0 or len(baseline.stdout) > 4096:
        _cleanup(nspawn)
        raise HyprlandG1Error("host Wayland ACL could not be captured")
    descriptor = os.open(acl_snapshot, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o640)
    try:
        os.write(descriptor, baseline.stdout)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    os.chown(acl_snapshot, 0, DEVELOPMENT_GID)
    mapped_uid = _mapped_host_uid(pid, 1000)
    acl = subprocess.run(
        ("/usr/bin/setfacl", "-m", f"u:{mapped_uid}:w", str(HOST_WAYLAND)),
        shell=False, stdin=subprocess.DEVNULL, capture_output=True, timeout=10,
        env={"LC_ALL": "C", "PATH": "/usr/bin"}, check=False,
    )
    if acl.returncode != 0:
        _cleanup(nspawn)
        raise HyprlandG1Error("temporary exact-UID Wayland ACL could not be applied")
    atexit.register(_restore_wayland_acl, acl_snapshot)
    acl_applied = True
    _progress("temporary-wayland-acl-applied")

    hypr_cmd = (
        "/usr/bin/setpriv", "--reuid=1000", "--regid=1000", "--clear-groups", "--",
        "/usr/bin/env", "HOME=/home/apx-g1", "USER=apx-g1", "LOGNAME=apx-g1",
        "XDG_RUNTIME_DIR=/run/user/1000", "XDG_CACHE_HOME=/home/apx-g1/.cache",
        "XDG_SESSION_TYPE=wayland", "WAYLAND_DISPLAY=" + str(INTERNAL_WAYLAND),
        "AQ_DRM_DEVICES=" + str(INTERNAL_RENDER), "AQ_TRACE=1", "HYPRLAND_TRACE=1",
        "HYPRLAND_NO_RT=1", "HYPRLAND_NO_SD_NOTIFY=1", "HYPRLAND_NO_SD_VARS=1",
        "/usr/bin/Hyprland", "--config", "/home/apx-g1/.config/hypr/g1.conf",
    )
    hypr = subprocess.Popen(
        (
            "/usr/bin/nsenter", "--target", str(pid), "--mount", "--uts", "--ipc",
            "--net", "--pid", "--user", "--cgroup", "--root=/proc/" + str(pid) + "/root",
            "--wd=/", "--", *hypr_cmd,
        ),
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        env={"LC_ALL": "C", "PATH": "/usr/bin"},
    )
    hypr_pid = None
    signature = None
    monitor_lines: tuple[str, ...] = ()
    deadline = time.monotonic() + 45
    while time.monotonic() < deadline and hypr.poll() is None:
        for candidate in _descendants(hypr.pid):
            try:
                executable = os.readlink(Path("/proc") / str(candidate) / "exe")
            except OSError:
                continue
            if executable.endswith("/Hyprland"):
                hypr_pid = candidate
        hypr_root = proc / "root/run/user/1000/hypr"
        if hypr_root.is_dir():
            entries = tuple(path for path in hypr_root.iterdir() if path.is_dir())
            if entries:
                signature = entries[0].name
        if signature:
            query = _nsenter(
                pid,
                (
                    "/usr/bin/setpriv", "--reuid=1000", "--regid=1000", "--clear-groups", "--",
                    "/usr/bin/env", "XDG_RUNTIME_DIR=/run/user/1000",
                    "HYPRLAND_INSTANCE_SIGNATURE=" + signature,
                    "/usr/bin/hyprctl", "-j", "monitors",
                ),
            )
            text = query.stdout.decode("utf-8", "replace")
            if query.returncode == 0 and text.strip() not in ("", "[]"):
                monitor_lines = (text[:4096],)
                break
        time.sleep(0.25)
    nested = bool(monitor_lines)
    _progress("nested-monitor-observed=" + str(nested))
    screenshot = False
    screenshot_bytes = 0
    if nested and signature:
        internal_runtime = proc / "root/run/user/1000"
        wayland_sockets = tuple(
            path.name for path in internal_runtime.iterdir()
            if path.name.startswith("wayland-") and stat.S_ISSOCK(path.lstat().st_mode)
        )
        if len(wayland_sockets) == 1:
            try:
                shot = _nsenter(
                    pid,
                    (
                        "/usr/bin/setpriv", "--reuid=1000", "--regid=1000", "--clear-groups", "--",
                        "/usr/bin/env", "XDG_RUNTIME_DIR=/run/user/1000",
                        "WAYLAND_DISPLAY=" + wayland_sockets[0],
                        "HYPRLAND_INSTANCE_SIGNATURE=" + signature,
                        "/usr/bin/grim", "/tmp/apx-g1.png",
                    ),
                    timeout=10,
                )
            except subprocess.TimeoutExpired:
                shot = None
            shot_path = proc / "root/tmp/apx-g1.png"
            screenshot = shot is not None and shot.returncode == 0 and shot_path.is_file()
            if screenshot:
                screenshot_bytes = shot_path.stat().st_size

    if hypr.poll() is None:
        if hypr_pid is not None:
            try:
                os.kill(hypr_pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        else:
            hypr.send_signal(signal.SIGTERM)
        try:
            hypr_output, _ = hypr.communicate(timeout=15)
        except subprocess.TimeoutExpired as first_timeout:
            if hypr_pid is not None:
                try:
                    os.kill(hypr_pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            hypr.kill()
            try:
                hypr_output, _ = hypr.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                hypr_output = first_timeout.output or b""
    else:
        hypr_output, _ = hypr.communicate(timeout=5)
    crash_reports = sorted((proc / "root/home/apx-g1/.cache/hyprland").glob("hyprlandCrashReport*.txt"))
    if crash_reports:
        try:
            crash = crash_reports[-1].read_bytes()
        except OSError:
            crash = b""
        hypr_output += b"\n--- APX PRESERVED HYPRLAND CRASH REPORT ---\n" + crash
    hypr_output = hypr_output[-OUTPUT_LIMIT:]
    _progress("hyprland-stopped")
    _restore_wayland_acl(acl_snapshot)
    restored_acl = subprocess.run(
        ("/usr/bin/getfacl", "-p", str(HOST_WAYLAND)), shell=False,
        stdin=subprocess.DEVNULL, capture_output=True, timeout=10,
        env={"LC_ALL": "C", "PATH": "/usr/bin"}, check=False,
    )
    acl_restored = restored_acl.returncode == 0 and restored_acl.stdout == baseline.stdout
    if acl_restored:
        atexit.unregister(_restore_wayland_acl)
    _progress("host-wayland-acl-restored=" + str(acl_restored))
    _cleanup(nspawn)
    residue = _residue()
    _progress("container-stopped-residue=" + str(residue))
    after_digest, _, _ = _tree_content_digest(SOURCE_ROOT)
    unchanged = source_digest == after_digest
    removed = not RUNTIME_PARENT.exists()
    _progress("source-unchanged=" + str(unchanged))
    _progress("runtime-removed=" + str(removed))
    if removed:
        atexit.unregister(_cleanup)

    draft = {
        "schema_version": 1, "build_report_digest": BUILD_REPORT_DIGEST,
        "host_wayland_socket": str(HOST_WAYLAND), "container_systemd_pid1": pid is not None,
        "private_namespaces": private, "internal_package_count": packages,
        "direct_drm_nodes_visible": direct_drm, "host_home_visible": host_home,
        "temporary_socket_acl_applied": acl_applied, "host_wayland_acl_restored": acl_restored,
        "hyprland_started": hypr_pid is not None, "nested_monitor_observed": nested,
        "monitor_evidence": monitor_lines, "internal_screenshot_created": screenshot,
        "internal_screenshot_bytes": screenshot_bytes, "hyprland_exit_code": hypr.returncode,
        "output_sha256": hashlib.sha256(hypr_output).hexdigest(), "output_bytes": len(hypr_output),
        "source_unchanged": unchanged, "processes_after": residue[0], "mounts_after": residue[1],
        "runtime_copy_removed": removed,
    }
    digest = hashlib.sha256(json.dumps(draft, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    result = HyprlandG1Report(**draft, report_digest=digest)
    for path, payload in (
        (EVIDENCE_ROOT / "g1-report-v1.json", (json.dumps(asdict(result), sort_keys=True, indent=2) + "\n").encode()),
        (EVIDENCE_ROOT / "hyprland-output-v1.log", hypr_output),
    ):
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o640)
        try:
            os.write(descriptor, payload)
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        os.chown(path, 0, DEVELOPMENT_GID)
    _progress("evidence-complete")
    if residue != (0, 0) or not unchanged or not removed or not acl_restored:
        raise HyprlandG1Error("G1 ended with residue, source change, retained runtime copy, or changed host ACL")
    return result


def main() -> int:
    try:
        result = execute_g1()
    except Exception:
        path = Path("/tmp/apx-hyprland-g1-controller-v5.log")
        try:
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o640)
            try:
                os.write(descriptor, traceback.format_exc().encode()[-65536:])
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
            os.chown(path, 0, DEVELOPMENT_GID)
        except OSError:
            pass
        raise
    print("APX Hyprland visible nested G1 test")
    for label, value in (
        ("Systemd PID 1", result.container_systemd_pid1),
        ("Private namespaces", result.private_namespaces),
        ("Packages", result.internal_package_count),
        ("Direct DRM nodes", result.direct_drm_nodes_visible),
        ("Host home visible", result.host_home_visible),
        ("Temporary socket ACL", result.temporary_socket_acl_applied),
        ("Host socket ACL restored", result.host_wayland_acl_restored),
        ("Hyprland started", result.hyprland_started),
        ("Nested monitor", result.nested_monitor_observed),
        ("Internal screenshot", result.internal_screenshot_created),
        ("Processes after", result.processes_after),
        ("Mounts after", result.mounts_after),
        ("Source unchanged", result.source_unchanged),
        ("Runtime removed", result.runtime_copy_removed),
    ):
        print(f"{label}: {value}")
    print(f"Report digest: {result.report_digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
