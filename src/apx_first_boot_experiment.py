"""Execute and attest the exact authorized first APX console boot preview."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import stat
import subprocess
import time

from apx_first_boot_preview import FINAL_REPORT_DIGEST, MACHINE, OBSERVATION_SECONDS, RUNTIME_MAX_BYTES, RUNTIME_ROOT, build_preview, fixed_command
from apx_offline_base_build import ROOT, ROOTFS


AUTHORIZED_PREVIEW = "0f59742d68e041b7bc2147dce7a2a901dd575ed0c99929875f1ac844dbcc883b"
FINAL_REPORT = ROOT / "final-report.json"
OUTPUT_LIMIT = 4 * 1024**2


class FirstBootExperimentError(RuntimeError):
    """The authorized boot could not start or left uncertain runtime state."""


@dataclass(frozen=True)
class FirstBootReport:
    schema_version: int
    preview_digest: str
    machine: str
    process_exit_code: int
    timed_out_as_planned: bool
    systemd_started: bool
    multi_user_reached: bool
    clean_shutdown_observed: bool
    container_pid: int | None
    pid1_systemd_observed: bool
    private_namespaces_observed: bool
    systemd_runtime_observed: bool
    internal_package_count: int
    host_development_home_hidden: bool
    observation_seconds: float
    source_report_unchanged: bool
    matching_processes_after: int
    matching_mounts_after: int
    output_sha256: str
    output_bytes: int
    runtime_copy_digest: str
    runtime_copy_removed: bool
    report_digest: str


def _final_report_bytes() -> bytes:
    content = FINAL_REPORT.read_bytes()
    payload = json.loads(content)
    if payload.get("final_report_digest") != FINAL_REPORT_DIGEST:
        raise FirstBootExperimentError("final root report identity changed")
    return content


def _runtime_residue() -> tuple[int, int]:
    processes = 0
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            command = (entry / "cmdline").read_bytes().replace(b"\0", b" ")
        except (OSError, PermissionError):
            continue
        if MACHINE.encode() in command and b"apx_first_boot_experiment" not in command:
            processes += 1
    mounts = 0
    for line in Path("/proc/self/mountinfo").read_text(encoding="utf-8").splitlines():
        if str(ROOTFS) in line or str(RUNTIME_ROOT) in line or MACHINE in line:
            mounts += 1
    return processes, mounts


def _descendants(parent: int) -> tuple[int, ...]:
    parents: dict[int, int] = {}
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            text = (entry / "stat").read_text(encoding="ascii")
            remainder = text[text.rfind(")") + 2:].split()
            parents[int(entry.name)] = int(remainder[1])
        except (OSError, ValueError, IndexError):
            continue
    found = set(); frontier = {parent}
    while frontier:
        children = {pid for pid, ppid in parents.items() if ppid in frontier and pid not in found}
        found.update(children); frontier = children
    return tuple(sorted(found))


def _observe_container(outer_pid: int) -> tuple[int | None, int | None, bool, bool, int, bool, bool, bool]:
    nspawn_pid = container_pid = None
    for pid in _descendants(outer_pid):
        try:
            command = (Path("/proc") / str(pid) / "cmdline").read_bytes().replace(b"\0", b" ")
            executable = os.readlink(Path("/proc") / str(pid) / "exe")
        except OSError:
            continue
        if b"systemd-nspawn" in command:
            nspawn_pid = pid
        if executable.endswith("/systemd"):
            try:
                status = (Path("/proc") / str(pid) / "status").read_text(encoding="ascii")
                nspid = next(line for line in status.splitlines() if line.startswith("NSpid:"))
                if nspid.split()[-1] == "1":
                    container_pid = pid
            except (OSError, StopIteration):
                pass
    if container_pid is None:
        return nspawn_pid, None, False, False, 0, False, False, False
    proc = Path("/proc") / str(container_pid)
    namespaces = True
    for name in ("pid", "mnt", "user", "net"):
        try:
            namespaces = namespaces and os.readlink(proc / "ns" / name) != os.readlink(Path("/proc/self/ns") / name)
        except OSError:
            namespaces = False
    root = proc / "root"
    runtime = (root / "run/systemd/system").is_dir()
    multi_user = (
        (root / "run/systemd/units/invocation:systemd-user-sessions.service").exists()
        and not (root / "run/nologin").exists()
    )
    try:
        packages = sum(1 for item in (root / "var/lib/pacman/local").iterdir() if item.is_dir())
    except OSError:
        packages = 0
    host_hidden = not (root / "home/apx-development").exists()
    return nspawn_pid, container_pid, True, namespaces, packages, runtime, host_hidden, multi_user


def _tree_content_digest(root: Path) -> tuple[str, int, int]:
    digest = hashlib.sha256(); logical = allocated = 0; seen = set()
    for directory, names, files in os.walk(root, followlinks=False):
        names.sort(); files.sort()
        for name in names + files:
            path = Path(directory) / name
            info = path.lstat(); relative = path.relative_to(root).as_posix()
            if stat.S_ISDIR(info.st_mode):
                kind = b"d"; extra = b""
            elif stat.S_ISLNK(info.st_mode):
                kind = b"l"; extra = os.readlink(path).encode("utf-8")
            elif stat.S_ISREG(info.st_mode):
                kind = b"f"; extra = b""
                identity = (info.st_dev, info.st_ino)
                if identity not in seen:
                    seen.add(identity); logical += info.st_size; allocated += info.st_blocks * 512
                with path.open("rb") as stream:
                    for block in iter(lambda: stream.read(1024 * 1024), b""):
                        digest.update(block)
            else:
                raise FirstBootExperimentError("source or runtime copy contains a special entry")
            digest.update(kind + b"\0" + relative.encode() + b"\0" + extra + b"\n")
    return digest.hexdigest(), logical, allocated


def execute_first_boot() -> FirstBootReport:
    if os.geteuid() != 0:
        raise FirstBootExperimentError("the bounded namespace experiment requires administrator execution")
    preview = build_preview()
    if preview.preview_digest != AUTHORIZED_PREVIEW or preview.command != fixed_command():
        raise FirstBootExperimentError("authorized preview identity changed")
    before = _final_report_bytes()
    if _runtime_residue() != (0, 0):
        raise FirstBootExperimentError("matching runtime state exists before boot")
    source_digest, _, _ = _tree_content_digest(ROOTFS)
    runtime_parent = RUNTIME_ROOT.parent
    try:
        os.mkdir(runtime_parent, 0o700)
    except FileExistsError as error:
        raise FirstBootExperimentError("runtime copy destination exists; refusing adoption") from error
    RUNTIME_ROOT.mkdir(mode=0o755)
    copy = subprocess.run(
        ("/usr/bin/cp", "-a", "--reflink=auto", "--", str(ROOTFS) + "/.", str(RUNTIME_ROOT)),
        shell=False, stdin=subprocess.DEVNULL, capture_output=True, timeout=120,
        env={"LC_ALL": "C", "PATH": "/usr/bin"}, check=False,
    )
    if copy.returncode != 0:
        shutil.rmtree(runtime_parent)
        raise FirstBootExperimentError("exact runtime copy failed")
    runtime_digest, runtime_logical, runtime_allocated = _tree_content_digest(RUNTIME_ROOT)
    if runtime_digest != source_digest or runtime_logical > RUNTIME_MAX_BYTES or runtime_allocated > RUNTIME_MAX_BYTES:
        shutil.rmtree(runtime_parent)
        raise FirstBootExperimentError("runtime copy identity or size is outside authorization")
    coredump_directory = RUNTIME_ROOT / "etc/systemd/coredump.conf.d"
    coredump_directory.mkdir(parents=True, mode=0o755, exist_ok=True)
    coredump_policy = coredump_directory / "apx-first-console.conf"
    descriptor = os.open(coredump_policy, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
    try:
        os.write(descriptor, b"[Coredump]\nStorage=none\nProcessSizeMax=0\n")
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    process = subprocess.Popen(
        preview.command, shell=False, stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        env={"LC_ALL": "C", "PATH": "/usr/bin"},
    )
    observed_at = time.monotonic(); observation_deadline = observed_at + OBSERVATION_SECONDS
    nspawn_pid = container_pid = None
    pid1 = namespaces = runtime_observed = host_hidden = multi_user_observed = False
    packages = 0
    while time.monotonic() < observation_deadline and process.poll() is None:
        seen = _observe_container(process.pid)
        nspawn_pid = seen[0] or nspawn_pid; container_pid = seen[1] or container_pid
        pid1 = pid1 or seen[2]; namespaces = namespaces or seen[3]
        packages = max(packages, seen[4]); runtime_observed = runtime_observed or seen[5]
        host_hidden = host_hidden or seen[6]; multi_user_observed = multi_user_observed or seen[7]
        if pid1 and namespaces and packages == 138 and runtime_observed and host_hidden and multi_user_observed:
            break
        time.sleep(0.25)
    observation_elapsed = time.monotonic() - observed_at
    if nspawn_pid is not None:
        os.kill(nspawn_pid, signal.SIGTERM)
    try:
        output, _ = process.communicate(timeout=30)
    except subprocess.TimeoutExpired:
        if nspawn_pid is not None:
            try: os.kill(nspawn_pid, signal.SIGTERM)
            except ProcessLookupError: pass
        try:
            output, _ = process.communicate(timeout=15)
        except subprocess.TimeoutExpired:
            process.kill(); output, _ = process.communicate(timeout=5)
    if len(output) > OUTPUT_LIMIT:
        raise FirstBootExperimentError("bounded boot output exceeded policy")
    deadline = time.monotonic() + 15
    residue = _runtime_residue()
    while residue != (0, 0) and time.monotonic() < deadline:
        time.sleep(0.25)
        residue = _runtime_residue()
    after = _final_report_bytes()
    after_source_digest, _, _ = _tree_content_digest(ROOTFS)
    text = output.decode("utf-8", "replace")
    systemd_started = pid1 or any(marker in text for marker in ("systemd 261", "Welcome to Arch Linux", "systemd[1]"))
    multi_user = multi_user_observed or any(marker in text for marker in ("Reached target Multi-User System", "Reached target multi-user.target"))
    clean = any(marker in text for marker in ("Reached target System Power Off", "Powering off", "Shutting down"))
    draft = {
        "schema_version": 1, "preview_digest": preview.preview_digest,
        "machine": MACHINE, "process_exit_code": process.returncode,
        "timed_out_as_planned": process.returncode == 124,
        "systemd_started": systemd_started, "multi_user_reached": multi_user,
        "clean_shutdown_observed": clean or process.returncode == 0,
        "container_pid": container_pid, "pid1_systemd_observed": pid1,
        "private_namespaces_observed": namespaces,
        "systemd_runtime_observed": runtime_observed,
        "internal_package_count": packages,
        "host_development_home_hidden": host_hidden,
        "observation_seconds": round(observation_elapsed, 3),
        "source_report_unchanged": before == after and source_digest == after_source_digest,
        "matching_processes_after": residue[0], "matching_mounts_after": residue[1],
        "output_sha256": hashlib.sha256(output).hexdigest(), "output_bytes": len(output),
        "runtime_copy_digest": runtime_digest, "runtime_copy_removed": False,
    }
    digest = hashlib.sha256(json.dumps(draft, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    if residue == (0, 0):
        shutil.rmtree(runtime_parent)
    runtime_removed = not runtime_parent.exists()
    draft["runtime_copy_removed"] = runtime_removed
    digest = hashlib.sha256(json.dumps(draft, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    report = FirstBootReport(**draft, report_digest=digest)
    descriptor = os.open(ROOT / "first-boot-report-v7.json", os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        os.write(descriptor, (json.dumps(asdict(report), sort_keys=True, indent=2) + "\n").encode())
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    output_path = ROOT / "first-boot-output-v7.log"
    descriptor = os.open(output_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        os.write(descriptor, output)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    if residue != (0, 0) or before != after or source_digest != after_source_digest or not runtime_removed:
        raise FirstBootExperimentError("boot ended with runtime residue or source change")
    return report


def main() -> int:
    report = execute_first_boot()
    print("APX first bounded console boot")
    print(f"Exit code: {report.process_exit_code}")
    print(f"Systemd started: {report.systemd_started}")
    print(f"Multi-user reached: {report.multi_user_reached}")
    print(f"Clean shutdown observed: {report.clean_shutdown_observed}")
    print(f"PID 1 systemd observed: {report.pid1_systemd_observed}")
    print(f"Private namespaces observed: {report.private_namespaces_observed}")
    print(f"Internal packages observed: {report.internal_package_count}")
    print(f"Host Development home hidden: {report.host_development_home_hidden}")
    print(f"Processes after: {report.matching_processes_after}")
    print(f"Mounts after: {report.matching_mounts_after}")
    print(f"Source unchanged: {report.source_report_unchanged}")
    print(f"Report digest: {report.report_digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
