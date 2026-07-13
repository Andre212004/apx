"""Build the first correct offline APX root from the closed verified package set."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
import subprocess

from apx_package_acquisition import AUTHORIZED_MANIFEST, MANIFEST_PATH
from apx_package_metadata import AUTHORIZED_SIGNATURE_EVIDENCE
from apx_resolution import parse_resolution_manifest
from apx_signature_verification import PACKAGE_ROOT


ROOT = Path("/tmp/apx-first-console-build-v1")
ROOTFS = ROOT / "rootfs"
GPGDIR = ROOTFS / "etc/pacman.d/gnupg"
PACMAN_DB = ROOTFS / "var/lib/pacman"
MAX_BYTES = 1024**3
EXPECTED_PACKAGES = 138


class OfflineBaseBuildError(RuntimeError):
    """The fixed offline base build is unsafe or incomplete."""


@dataclass(frozen=True)
class OfflineBaseBuildReport:
    schema_version: int
    manifest_digest: str
    signature_evidence_digest: str
    package_count: int
    local_database_count: int
    logical_bytes: int
    allocated_bytes: int
    development_uid_entries: int
    machine_identity_present: bool
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


def _run(command: tuple[str, ...], *, timeout: int = 600) -> None:
    result = subprocess.run(
        command, shell=False, stdin=subprocess.DEVNULL, capture_output=True,
        timeout=timeout, env={"LC_ALL": "C", "PATH": "/usr/bin"}, check=False,
    )
    if result.returncode != 0:
        tail = result.stderr.decode("utf-8", "replace")[-2000:]
        raise OfflineBaseBuildError("offline base tool failed: " + tail) from None


def _measure(root: Path) -> tuple[int, int, int]:
    logical = allocated = development_uid = 0
    seen = set()
    for directory, names, files in os.walk(root, followlinks=False):
        for name in names + files:
            info = (Path(directory) / name).lstat()
            if info.st_uid == 1002:
                development_uid += 1
            if not os.path.islink(Path(directory) / name) and os.path.isfile(Path(directory) / name):
                identity = (info.st_dev, info.st_ino)
                if identity not in seen:
                    seen.add(identity); logical += info.st_size; allocated += info.st_blocks * 512
    return logical, allocated, development_uid


def build_offline_base() -> OfflineBaseBuildReport:
    if os.geteuid() != 0:
        raise OfflineBaseBuildError("this disposable ownership experiment requires administrator execution")
    manifest = parse_resolution_manifest(MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest.manifest_digest != AUTHORIZED_MANIFEST or len(manifest.packages) != EXPECTED_PACKAGES:
        raise OfflineBaseBuildError("closed package manifest identity changed")
    packages = tuple(PACKAGE_ROOT / item.filename for item in manifest.packages)
    for item, path in zip(manifest.packages, packages):
        if not path.is_file() or path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() != item.sha256:
            raise OfflineBaseBuildError("one verified package changed before the build")
    try:
        os.mkdir(ROOT, 0o700)
    except FileExistsError as error:
        raise OfflineBaseBuildError("build root exists; refusing adoption") from error
    ROOTFS.mkdir(mode=0o755)
    for relative in ("etc/pacman.d/gnupg", "etc/pacman.d/hooks", "var/lib/pacman", "var/log"):
        (ROOTFS / relative).mkdir(parents=True, mode=0o755, exist_ok=True)
    config = "[options]\nArchitecture = x86_64\nSigLevel = Required DatabaseOptional\nLocalFileSigLevel = Required\nParallelDownloads = 1\n"
    (ROOT / "pacman.conf").write_text(config, encoding="utf-8")
    os.chmod(ROOT / "pacman.conf", 0o600)
    key_base = ("/usr/bin/unshare", "--net", "--", "/usr/bin/pacman-key", "--gpgdir", str(GPGDIR), "--populate-from", "/usr/share/pacman/keyrings")
    _run(key_base + ("--init",), timeout=120)
    _run(key_base + ("--populate", "archlinux"), timeout=180)
    _run(fixed_pacman_command(packages), timeout=900)
    _run(("/usr/bin/gpgconf", "--homedir", str(GPGDIR), "--kill", "all"), timeout=30)
    local_entries = tuple(path for path in (PACMAN_DB / "local").iterdir() if path.is_dir())
    logical, allocated, development_uid = _measure(ROOTFS)
    if len(local_entries) != EXPECTED_PACKAGES:
        raise OfflineBaseBuildError("pacman internal package count is incomplete")
    if logical > MAX_BYTES or allocated > MAX_BYTES:
        raise OfflineBaseBuildError("built root exceeded the authorized 1 GiB")
    machine_identity = any((ROOTFS / path).exists() for path in ("etc/machine-id", "var/lib/dbus/machine-id", "var/lib/systemd/random-seed"))
    draft = {
        "schema_version": 1, "manifest_digest": manifest.manifest_digest,
        "signature_evidence_digest": AUTHORIZED_SIGNATURE_EVIDENCE,
        "package_count": len(packages), "local_database_count": len(local_entries),
        "logical_bytes": logical, "allocated_bytes": allocated,
        "development_uid_entries": development_uid,
        "machine_identity_present": machine_identity,
    }
    digest = hashlib.sha256(json.dumps(draft, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    report = OfflineBaseBuildReport(**draft, report_digest=digest)
    descriptor = os.open(ROOT / "build-report.json", os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        os.write(descriptor, (json.dumps(asdict(report), sort_keys=True, indent=2) + "\n").encode())
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return report


def main() -> int:
    report = build_offline_base()
    print("APX correct offline disposable base")
    print(f"Packages recorded internally: {report.local_database_count}")
    print(f"Logical bytes: {report.logical_bytes}")
    print(f"Allocated bytes: {report.allocated_bytes}")
    print(f"Development-owner entries: {report.development_uid_entries}")
    print(f"Machine identity present: {report.machine_identity_present}")
    print(f"Report digest: {report.report_digest}")
    print("Boot/network/download/host-account/service/Btrfs/cleanup effects: none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
