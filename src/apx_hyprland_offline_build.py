"""Build the verified Hyprland role into one disposable copy, offline."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import threading
import time

from apx_graphical_acquisition import AUTHORIZED_MANIFEST, MANIFEST_PATH
from apx_graphical_metadata import AUTHORIZED_SIGNATURE_EVIDENCE
from apx_graphical_resolution import parse_graphical_manifest
from apx_graphical_signature_verification import PACKAGE_ROOT
from apx_offline_base_build import ROOTFS as BASE_ROOTFS


ROOT = Path("/tmp/apx-hyprland-build-v1")
ROOTFS = ROOT / "rootfs"
PACMAN_DB = ROOTFS / "var/lib/pacman"
GPGDIR = ROOTFS / "etc/pacman.d/gnupg"
MAX_BYTES = 3 * 1024**3
EXPECTED_BASE_PACKAGES = 138
EXPECTED_ROLE_PACKAGES = 194
EXPECTED_TOTAL_PACKAGES = 332
AUTHORIZED_METADATA = "89ed0ab7623a93972bb403af33bbda4ee1ebb2717d285455fa4a240adea455df"
POLL_SECONDS = 0.25


class HyprlandOfflineBuildError(RuntimeError):
    """The fixed graphical-role build is unsafe or incomplete."""


@dataclass(frozen=True)
class HyprlandOfflineBuildReport:
    schema_version: int
    manifest_digest: str
    signature_evidence_digest: str
    metadata_digest: str
    base_package_count: int
    role_package_count: int
    final_package_count: int
    logical_bytes: int
    allocated_bytes: int
    source_before_digest: str
    source_after_digest: str
    development_uid_entries: int
    special_file_count: int
    report_digest: str


def fixed_pacman_command(packages: tuple[Path, ...]) -> tuple[str, ...]:
    return (
        "/usr/bin/unshare", "--net", "--", "/usr/bin/pacman", "-U",
        "--noconfirm", "--noprogressbar", "--root", str(ROOTFS),
        "--dbpath", str(PACMAN_DB), "--cachedir", str(PACKAGE_ROOT),
        "--gpgdir", str(GPGDIR), "--hookdir", str(ROOTFS / "etc/pacman.d/hooks"),
        "--logfile", str(ROOTFS / "var/log/pacman.log"),
        "--config", str(ROOT / "pacman.conf"), "--", *(str(path) for path in packages),
    )


def _tree_measure(root: Path, *, content_digest: bool = False) -> tuple[int, int, int, int, str]:
    logical = allocated = development = special = 0
    digest = hashlib.sha256()
    for directory, names, files in os.walk(root, topdown=True, followlinks=False):
        names.sort(); files.sort()
        for name in names + files:
            path = Path(directory) / name
            info = path.lstat()
            relative = path.relative_to(root).as_posix()
            kind = stat.S_IFMT(info.st_mode)
            digest.update(f"{relative}\0{kind:o}\0{stat.S_IMODE(info.st_mode):o}\0{info.st_uid}\0{info.st_gid}\0{info.st_size}\0".encode())
            if info.st_uid == 1002:
                development += 1
            if stat.S_ISREG(info.st_mode):
                logical += info.st_size; allocated += info.st_blocks * 512
                if content_digest:
                    with path.open("rb") as stream:
                        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                            digest.update(chunk)
            elif stat.S_ISLNK(info.st_mode):
                digest.update(os.readlink(path).encode())
            elif not stat.S_ISDIR(info.st_mode):
                special += 1
    return logical, allocated, development, special, digest.hexdigest()


def _package_count(root: Path) -> int:
    local = root / "var/lib/pacman/local"
    return sum(path.is_dir() and not path.is_symlink() for path in local.iterdir())


def _verify_inputs() -> tuple[Path, ...]:
    manifest = parse_graphical_manifest(MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest.manifest_digest != AUTHORIZED_MANIFEST or len(manifest.role_packages) != EXPECTED_ROLE_PACKAGES:
        raise HyprlandOfflineBuildError("closed graphical manifest identity changed")
    metadata_path = Path("/tmp/apx-hyprland-metadata-20260711-v1/graphical-package-metadata.json")
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise HyprlandOfflineBuildError("verified graphical metadata is unavailable") from error
    if metadata.get("metadata_digest") != AUTHORIZED_METADATA or metadata.get("signature_evidence_digest") != AUTHORIZED_SIGNATURE_EVIDENCE:
        raise HyprlandOfflineBuildError("graphical evidence identity changed")
    packages = tuple(PACKAGE_ROOT / item.filename for item in manifest.role_packages)
    for item, path in zip(manifest.role_packages, packages):
        if not path.is_file() or path.is_symlink():
            raise HyprlandOfflineBuildError("one verified graphical package is unavailable")
        with path.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        if path.stat().st_size != item.compressed_size or digest != item.sha256:
            raise HyprlandOfflineBuildError("one verified graphical package changed before the build")
    return packages


def _run_bounded(command: tuple[str, ...]) -> None:
    process = subprocess.Popen(
        command, shell=False, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, env={"LC_ALL": "C", "PATH": "/usr/bin"},
        start_new_session=True,
    )
    exceeded = threading.Event()

    def monitor() -> None:
        while process.poll() is None:
            try:
                logical, allocated, *_ = _tree_measure(ROOTFS)
                if logical > MAX_BYTES or allocated > MAX_BYTES:
                    exceeded.set(); os.killpg(process.pid, 9); return
            except FileNotFoundError:
                pass
            time.sleep(POLL_SECONDS)

    watcher = threading.Thread(target=monitor, daemon=True)
    watcher.start()
    try:
        stdout, stderr = process.communicate(timeout=1200)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, 9); process.communicate()
        raise HyprlandOfflineBuildError("offline graphical build exceeded 20 minutes") from None
    watcher.join(timeout=2)
    if exceeded.is_set():
        raise HyprlandOfflineBuildError("disposable graphical root exceeded 3 GiB")
    if process.returncode != 0:
        tail = (stdout + stderr).decode("utf-8", "replace")[-3000:]
        raise HyprlandOfflineBuildError("offline graphical package installation failed: " + tail)


def build_hyprland_role() -> HyprlandOfflineBuildReport:
    if os.geteuid() != 0:
        raise HyprlandOfflineBuildError("this disposable ownership-preserving build requires administrator execution")
    if not BASE_ROOTFS.is_dir() or BASE_ROOTFS.is_symlink() or _package_count(BASE_ROOTFS) != EXPECTED_BASE_PACKAGES:
        raise HyprlandOfflineBuildError("verified console base is unavailable or changed")
    packages = _verify_inputs()
    _, _, _, source_special, source_before = _tree_measure(BASE_ROOTFS, content_digest=True)
    if source_special:
        raise HyprlandOfflineBuildError("console base contains an unexpected special file")
    try:
        os.mkdir(ROOT, 0o700)
    except FileExistsError as error:
        raise HyprlandOfflineBuildError("graphical build root exists; refusing adoption") from error
    subprocess.run(
        ("/usr/bin/cp", "-a", "--reflink=auto", str(BASE_ROOTFS), str(ROOTFS)),
        shell=False, stdin=subprocess.DEVNULL, capture_output=True, timeout=300,
        env={"LC_ALL": "C", "PATH": "/usr/bin"}, check=True,
    )
    config = "[options]\nArchitecture = x86_64\nSigLevel = Required DatabaseOptional\nLocalFileSigLevel = Required\nParallelDownloads = 1\n"
    (ROOT / "pacman.conf").write_text(config, encoding="utf-8")
    os.chmod(ROOT / "pacman.conf", 0o600)
    _run_bounded(fixed_pacman_command(packages))
    subprocess.run(
        ("/usr/bin/gpgconf", "--homedir", str(GPGDIR), "--kill", "all"),
        shell=False, stdin=subprocess.DEVNULL, capture_output=True, timeout=30,
        env={"LC_ALL": "C", "PATH": "/usr/bin"}, check=False,
    )
    for path in GPGDIR.glob("S.gpg-agent*"):
        if stat.S_ISSOCK(path.lstat().st_mode):
            path.unlink()
        else:
            raise HyprlandOfflineBuildError("unexpected GPG runtime entry type")
    logical, allocated, development, special, _ = _tree_measure(ROOTFS)
    final_packages = _package_count(ROOTFS)
    _, _, _, _, source_after = _tree_measure(BASE_ROOTFS, content_digest=True)
    if final_packages != EXPECTED_TOTAL_PACKAGES or logical > MAX_BYTES or allocated > MAX_BYTES:
        raise HyprlandOfflineBuildError("built graphical root is incomplete or oversized")
    if development or special or source_before != source_after:
        raise HyprlandOfflineBuildError("ownership, file type, or source-preservation check failed")
    draft = {
        "schema_version": 1, "manifest_digest": AUTHORIZED_MANIFEST,
        "signature_evidence_digest": AUTHORIZED_SIGNATURE_EVIDENCE,
        "metadata_digest": AUTHORIZED_METADATA,
        "base_package_count": EXPECTED_BASE_PACKAGES,
        "role_package_count": EXPECTED_ROLE_PACKAGES,
        "final_package_count": final_packages,
        "logical_bytes": logical, "allocated_bytes": allocated,
        "source_before_digest": source_before, "source_after_digest": source_after,
        "development_uid_entries": development, "special_file_count": special,
    }
    report_digest = hashlib.sha256(json.dumps(draft, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    report = HyprlandOfflineBuildReport(**draft, report_digest=report_digest)
    descriptor = os.open(ROOT / "build-report.json", os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        os.write(descriptor, (json.dumps(asdict(report), sort_keys=True, indent=2) + "\n").encode())
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return report


def main() -> int:
    report = build_hyprland_role()
    print("APX disposable Hyprland role build")
    print(f"Packages recorded internally: {report.final_package_count}")
    print(f"Logical bytes: {report.logical_bytes}")
    print(f"Allocated bytes: {report.allocated_bytes}")
    print(f"Source preserved: {report.source_before_digest == report.source_after_digest}")
    print(f"Development-owner entries: {report.development_uid_entries}")
    print(f"Special runtime entries: {report.special_file_count}")
    print(f"Report digest: {report.report_digest}")
    print("Hyprland/GPU/display/input/audio/network/host/Btrfs/cleanup effects: none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
