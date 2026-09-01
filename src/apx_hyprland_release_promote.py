"""Exact physical promotion adapter for the approved Hyprland H0 release."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess

from apx_hyprland_release_promotion import (
    FINAL_REPORT_DIGEST,
    MINIMUM_FREE_BYTES,
    PACKAGE_COUNT,
    RELEASE_ID,
    SOURCE_TREE_DIGEST,
)


SOURCE = Path("/tmp/apx-hyprland-build-v1/rootfs")
FINAL_REPORT = SOURCE.parent / "final-release-report.json"
APX_ROOT = Path("/var/lib/apx")
RELEASES = APX_ROOT / "releases"
DESTINATION = RELEASES / RELEASE_ID
TARGET_ROOT = DESTINATION / "root"
MANIFEST = DESTINATION / "manifest.json"
EXPECTED_HOSTNAME = "apx-host"
EXPECTED_MARKER_DIGEST = "73bedec12d8bfd3b91b5ed09fa97583a9cd517b08cb3c72619d1bb2ca3b20e14"
EXPECTED_HUB_GENERATION = "d68ee7a2-268a-4534-b033-8f5313943fcf"
EXPECTED_DEVELOPMENT_GENERATION = "b90155f6-ece2-44ae-91fc-42d91d6b35a5"
EXPECTED_HOLD_GENERATION = "1ec52013-e715-413a-bb48-b4691cf31ee9"
EXPECTED_ACCOUNT_PARTIAL_DIGEST = "b1bb42da33a9df56b39a28ec84bc11a0cbf14670e2c97efbb805dc294d997664"


class HyprlandReleasePromoteError(RuntimeError):
    """The approved physical promotion is unsafe, stale, or incomplete."""


@dataclass(frozen=True)
class HyprlandReleasePromotionResult:
    schema_version: int
    release_id: str
    source_tree_digest: str
    configured_tree_digest: str
    package_count: int
    logical_bytes: int
    allocated_bytes: int
    root_read_only: bool
    source_preserved: bool
    hub_generation_unchanged: bool
    development_generation_unchanged: bool
    disposable_hold_unchanged: bool
    no_uncertain_apx_operation: bool
    manifest_digest: str


def _run(arguments: tuple[str, ...], *, timeout: int = 300) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        arguments, shell=False, text=True, capture_output=True, timeout=timeout,
        env={"LC_ALL": "C", "PATH": "/usr/bin"}, check=False,
    )


def _hash_file(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _measure(root: Path) -> tuple[int, int, int, int, str]:
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
                with path.open("rb") as stream:
                    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                        digest.update(chunk)
            elif stat.S_ISLNK(info.st_mode):
                digest.update(os.readlink(path).encode())
            elif not stat.S_ISDIR(info.st_mode):
                special += 1
    return logical, allocated, development, special, digest.hexdigest()


def _atomic_replace(path: Path, content: str) -> None:
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or info.st_gid != 0:
        raise HyprlandReleasePromoteError("account file is not a root-owned regular file")
    temporary = path.with_name("." + path.name + ".apx-promote")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, stat.S_IMODE(info.st_mode))
    try:
        os.write(descriptor, content.encode("utf-8")); os.fsync(descriptor)
    finally:
        os.close(descriptor)
    os.replace(temporary, path)


def _append_unique(path: Path, prefix: str, line: str) -> None:
    content = path.read_text(encoding="utf-8")
    if any(existing.startswith(prefix) for existing in content.splitlines()):
        raise HyprlandReleasePromoteError("fixed Environment account already exists")
    _atomic_replace(path, content + ("" if content.endswith("\n") else "\n") + line + "\n")


def _write_new_regular(path: Path, content: bytes, mode: int) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode)
    try:
        os.write(descriptor, content); os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _configure_target() -> None:
    _append_unique(TARGET_ROOT / "etc/passwd", "apx:", "apx:x:1000:1000:APX graphical Environment:/home/apx:/usr/bin/bash")
    _append_unique(TARGET_ROOT / "etc/group", "apx:", "apx:x:1000:")
    _append_unique(TARGET_ROOT / "etc/shadow", "apx:", "apx:!:::::::")
    _append_unique(TARGET_ROOT / "etc/gshadow", "apx:", "apx:!::")
    home = TARGET_ROOT / "home/apx"
    home.mkdir(mode=0o700)
    os.chown(home, 1000, 1000)
    _write_new_regular(TARGET_ROOT / "etc/hostname", b"apx-hyprland-h0-release\n", 0o644)


def _registrations() -> dict[str, dict[str, object]]:
    result = {}
    for name in ("hub", "development", "codex-test-lifecycle-v1"):
        path = APX_ROOT / "environments" / name / "registration.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise HyprlandReleasePromoteError("APX registration is malformed")
        result[name] = value
    return result


def _check_preconditions(*, allow_exact_partial: bool = False) -> tuple[str, str]:
    if os.geteuid() != 0 or Path("/etc/hostname").read_text().strip() != EXPECTED_HOSTNAME:
        raise HyprlandReleasePromoteError("physical root Host identity is invalid")
    if _hash_file(Path("/etc/apx-physical-pilot")) != EXPECTED_MARKER_DIGEST:
        raise HyprlandReleasePromoteError("physical pilot marker changed")
    if os.path.lexists(DESTINATION) and not allow_exact_partial:
        raise HyprlandReleasePromoteError("target release already exists; refusing adoption")
    report = json.loads(FINAL_REPORT.read_text(encoding="utf-8"))
    if report.get("report_digest") != FINAL_REPORT_DIGEST or report.get("tree_digest") != SOURCE_TREE_DIGEST or report.get("package_count") != PACKAGE_COUNT:
        raise HyprlandReleasePromoteError("finalized release report changed")
    source_measure = _measure(SOURCE)
    if source_measure[2:] != (0, 0, SOURCE_TREE_DIGEST):
        raise HyprlandReleasePromoteError("finalized source tree changed")
    mount = _run(("/usr/bin/findmnt", "-n", "-o", "FSTYPE", str(APX_ROOT)))
    quota = _run(("/usr/bin/btrfs", "quota", "status", str(APX_ROOT)))
    available = _run(("/usr/bin/findmnt", "-b", "-n", "-o", "AVAIL", str(APX_ROOT)))
    if mount.returncode != 0 or mount.stdout.strip() != "btrfs":
        raise HyprlandReleasePromoteError("APX state parent is not Btrfs")
    required_quota = ("Enabled:                 yes", "Mode:                    qgroup (full accounting)", "Inconsistent:            no")
    if quota.returncode != 0 or any(item not in quota.stdout for item in required_quota):
        raise HyprlandReleasePromoteError("Btrfs quota state is not healthy")
    if available.returncode != 0 or not available.stdout.strip().isdigit() or int(available.stdout) < MINIMUM_FREE_BYTES:
        raise HyprlandReleasePromoteError("Host free-space reserve is insufficient")
    registrations = _registrations()
    if registrations["hub"].get("generation") != EXPECTED_HUB_GENERATION or registrations["hub"].get("state") != "running":
        raise HyprlandReleasePromoteError("Hub generation or state changed")
    if registrations["development"].get("generation") != EXPECTED_DEVELOPMENT_GENERATION or registrations["development"].get("state") != "running":
        raise HyprlandReleasePromoteError("Development generation or state changed")
    if registrations["codex-test-lifecycle-v1"].get("generation") != EXPECTED_HOLD_GENERATION or registrations["codex-test-lifecycle-v1"].get("state") != "stopped":
        raise HyprlandReleasePromoteError("disposable hold changed")
    recovery = _run(("/usr/bin/apx", "recovery-status"))
    if recovery.returncode != 0 or json.loads(recovery.stdout).get("uncertain_operations") != []:
        raise HyprlandReleasePromoteError("APX has an uncertain operation")
    return source_measure[4], hashlib.sha256(FINAL_REPORT.read_bytes()).hexdigest()


def _finish_release(source_digest: str) -> HyprlandReleasePromotionResult:
    logical, allocated, development, special, configured_digest = _measure(TARGET_ROOT)
    if development or special or _measure(SOURCE)[4] != source_digest:
        raise HyprlandReleasePromoteError("configured release or source preservation failed")
    manifest_value = {
        "backend": "systemd-nspawn-hyprland-h0-v1", "package_count": PACKAGE_COUNT,
        "release": RELEASE_ID, "role": "graphical-h0", "schema": 1,
        "source_tree_digest": SOURCE_TREE_DIGEST,
        "configured_tree_digest": configured_digest,
        "final_report_digest": FINAL_REPORT_DIGEST,
        "identity": "empty-until-environment-creation",
    }
    manifest_bytes = (json.dumps(manifest_value, sort_keys=True, separators=(",", ":")) + "\n").encode()
    _write_new_regular(MANIFEST, manifest_bytes, 0o400)
    readonly = _run(("/usr/bin/btrfs", "property", "set", "-ts", str(TARGET_ROOT), "ro", "true"))
    verify_ro = _run(("/usr/bin/btrfs", "property", "get", "-ts", str(TARGET_ROOT), "ro"))
    registrations = _registrations()
    recovery = _run(("/usr/bin/apx", "recovery-status"))
    result = HyprlandReleasePromotionResult(
        1, RELEASE_ID, source_digest, configured_digest, PACKAGE_COUNT, logical,
        allocated, readonly.returncode == 0 and "ro=true" in verify_ro.stdout,
        _measure(SOURCE)[4] == source_digest,
        registrations["hub"].get("generation") == EXPECTED_HUB_GENERATION,
        registrations["development"].get("generation") == EXPECTED_DEVELOPMENT_GENERATION,
        registrations["codex-test-lifecycle-v1"].get("generation") == EXPECTED_HOLD_GENERATION,
        recovery.returncode == 0 and json.loads(recovery.stdout).get("uncertain_operations") == [],
        hashlib.sha256(manifest_bytes).hexdigest(),
    )
    if not all((result.root_read_only, result.source_preserved, result.hub_generation_unchanged, result.development_generation_unchanged, result.disposable_hold_unchanged, result.no_uncertain_apx_operation)):
        raise HyprlandReleasePromoteError("final promotion verification failed; preserve release")
    return result


def promote_release() -> HyprlandReleasePromotionResult:
    source_digest, _ = _check_preconditions()
    DESTINATION.mkdir(mode=0o700)
    created = _run(("/usr/bin/btrfs", "subvolume", "create", str(TARGET_ROOT)))
    if created.returncode != 0:
        raise HyprlandReleasePromoteError("release root creation failed; preserve destination")
    copied = _run(("/usr/bin/cp", "-a", "--reflink=auto", str(SOURCE) + "/.", str(TARGET_ROOT)), timeout=1200)
    if copied.returncode != 0:
        raise HyprlandReleasePromoteError("release copy failed; preserve destination")
    _configure_target()
    return _finish_release(source_digest)


def resume_exact_account_partial() -> HyprlandReleasePromotionResult:
    source_digest, _ = _check_preconditions(allow_exact_partial=True)
    if not DESTINATION.is_dir() or DESTINATION.is_symlink() or MANIFEST.exists():
        raise HyprlandReleasePromoteError("partial release container is not exact")
    root_show = _run(("/usr/bin/btrfs", "subvolume", "show", str(TARGET_ROOT)))
    root_ro = _run(("/usr/bin/btrfs", "property", "get", "-ts", str(TARGET_ROOT), "ro"))
    if root_show.returncode != 0 or root_ro.returncode != 0 or "ro=false" not in root_ro.stdout:
        raise HyprlandReleasePromoteError("partial release root is not the expected writable subvolume")
    if _measure(TARGET_ROOT)[4] != EXPECTED_ACCOUNT_PARTIAL_DIGEST:
        raise HyprlandReleasePromoteError("partial release content is not the reviewed account boundary")
    if os.path.lexists(TARGET_ROOT / "etc/hostname"):
        raise HyprlandReleasePromoteError("partial release hostname outcome is not absent")
    home = (TARGET_ROOT / "home/apx").lstat()
    if not stat.S_ISDIR(home.st_mode) or stat.S_IMODE(home.st_mode) != 0o700 or (home.st_uid, home.st_gid) != (1000, 1000):
        raise HyprlandReleasePromoteError("partial Environment home identity changed")
    _write_new_regular(TARGET_ROOT / "etc/hostname", b"apx-hyprland-h0-release\n", 0o644)
    return _finish_release(source_digest)


if __name__ == "__main__":
    action = resume_exact_account_partial if os.path.lexists(DESTINATION) else promote_release
    print(json.dumps(asdict(action()), sort_keys=True, indent=2))
