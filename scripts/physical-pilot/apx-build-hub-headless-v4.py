#!/usr/bin/env python3
"""Build and publish two matching minimal Arch roots for the official Hub."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys

sys.path.insert(0, "/usr/lib/apx")
from apx_hub_clean_release import HubCleanReleaseEvidence, assess_hub_clean_release


STATE = Path("/var/lib/apx")
QUARANTINE = STATE / "quarantine"
BUILD_A = QUARANTINE / "hub-headless-v4-build-a"
BUILD_B = QUARANTINE / "hub-headless-v4-build-b"
RELEASE = STATE / "releases/hub-headless-v4"
CLIENT = Path("/usr/lib/apx/apx-lab-client.py")
NETWORK = Path("/root/apx-host-development-mode-v1/apx/config/hub-headless-v4/20-host0.network")
APPROVAL = "PUBLISH HUB HEADLESS V4"
REPRODUCIBLE_TIME = "1800000000"


class HubBuildError(RuntimeError):
    pass


def run(arguments: tuple[str, ...], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        arguments, check=check, text=True, capture_output=True,
        env={**os.environ, "LC_ALL": "C"},
    )


def require_clean_builder_host() -> None:
    if os.geteuid() != 0 or Path("/etc/hostname").read_text().strip() != "apx-host":
        raise HubBuildError("builder requires root on the exact APX Host")
    if Path("/sys/class/tty/tty0/active").read_text().strip() != "tty1":
        raise HubBuildError("builder requires the recovery console on tty1")
    if run(("/usr/bin/machinectl", "list", "--no-legend")).stdout.strip():
        raise HubBuildError("builder refuses while an Environment is running")
    if not CLIENT.is_file() or not NETWORK.is_file():
        raise HubBuildError("fixed Hub client or network source is absent")


def normalize(root: Path) -> None:
    trust_home = root / "etc/pacman.d/gnupg"
    ownertrust = run((
        "/usr/bin/gpg", "--homedir", str(trust_home), "--batch", "--export-ownertrust",
    )).stdout
    ownertrust_lines = sorted(
        line for line in ownertrust.splitlines() if line and not line.startswith("#")
    )
    if not ownertrust_lines:
        raise HubBuildError("pacman ownertrust export is unexpectedly empty")
    ownertrust_path = root / "run/apx-ownertrust-normalize"
    ownertrust_path.parent.mkdir(parents=True, exist_ok=True)
    ownertrust_path.write_text("\n".join(ownertrust_lines) + "\n")
    for socket in trust_home.glob("S.*"):
        if stat.S_ISSOCK(socket.lstat().st_mode):
            socket.unlink()
    (trust_home / "trustdb.gpg").unlink(missing_ok=True)
    run((
        "/usr/bin/gpg", "--homedir", str(trust_home), "--batch",
        "--faked-system-time", REPRODUCIBLE_TIME,
        "--import-ownertrust", str(ownertrust_path),
    ))
    ownertrust_path.unlink()
    for socket in trust_home.glob("S.*"):
        if stat.S_ISSOCK(socket.lstat().st_mode):
            socket.unlink()
    run((
        "/usr/bin/systemd-nspawn", "-q", "-D", str(root), "/usr/bin/env",
        f"SOURCE_DATE_EPOCH={REPRODUCIBLE_TIME}", "/usr/bin/update-ca-trust", "extract",
    ))
    (root / "etc/machine-id").write_text("")
    (root / "var/lib/systemd/random-seed").unlink(missing_ok=True)
    (root / "var/log/pacman.log").unlink(missing_ok=True)
    (root / "var/cache/ldconfig/aux-cache").unlink(missing_ok=True)
    package_cache = root / "var/cache/pacman/pkg"
    if package_cache.exists():
        for child in package_cache.iterdir():
            if child.is_file() or child.is_symlink():
                child.unlink()
            elif child.is_dir():
                shutil.rmtree(child)
    for description in (root / "var/lib/pacman/local").glob("*/desc"):
        lines = description.read_text().splitlines()
        for index, line in enumerate(lines[:-1]):
            if line == "%INSTALLDATE%":
                lines[index + 1] = "0"
        description.write_text("\n".join(lines) + "\n")


def configure(root: Path) -> None:
    (root / "etc/locale.conf").write_text("LANG=en_US.UTF-8\n")
    (root / "etc/hostname").write_text("apx-hub-release\n")
    (root / "etc/systemd/network").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(NETWORK, root / "etc/systemd/network/20-host0.network")
    resolv = root / "etc/resolv.conf"
    resolv.unlink(missing_ok=True)
    resolv.symlink_to("/run/systemd/resolve/stub-resolv.conf")
    run(("/usr/bin/systemd-nspawn", "-q", "-D", str(root), "/usr/bin/systemctl",
         "enable", "systemd-networkd.service", "systemd-resolved.service"))
    run(("/usr/bin/systemd-nspawn", "-q", "-D", str(root), "/usr/bin/systemctl",
         "set-default", "multi-user.target"))
    run(("/usr/bin/systemd-nspawn", "-q", "-D", str(root), "/usr/bin/useradd",
         "--create-home", "--uid", "1000", "--user-group", "--shell", "/bin/bash", "apx"))
    run(("/usr/bin/passwd", "-R", str(root), "-l", "root"))
    run(("/usr/bin/passwd", "-R", str(root), "-l", "apx"))
    target = root / "usr/bin/apx"
    shutil.copyfile(CLIENT, target)
    target.chmod(0o755)
    (root / "etc/apx").mkdir(mode=0o755, exist_ok=True)
    (root / "etc/apx/official-hub-base-v1").write_text(
        "headless=true\nowner_installs_hyprland=true\nowner_installs_terminal=true\n"
    )
    (root / "etc/motd").write_text(
        "\n"
        "========================================================================\n"
        " APX ENVIRONMENT: estás dentro do Hub, NÃO estás no Host.\n"
        " Pacotes, ficheiros e sudo pertencem somente a este Environment.\n"
        " Usa 'exit' ou Ctrl+D para regressar ao Host; lê o aviso de saída.\n"
        "========================================================================\n"
    )
    normalize(root)


def build_one(destination: Path) -> None:
    if destination.exists():
        raise HubBuildError(f"preserved build destination already exists: {destination}")
    destination.mkdir(mode=0o700)
    root = destination / "root"
    run(("/usr/bin/btrfs", "subvolume", "create", str(root)))
    try:
        run(("/usr/bin/pacstrap", "-c", str(root), "base", "sudo"))
        configure(root)
    except BaseException:
        (destination / "INCOMPLETE").write_text("preserved for inspection\n")
        raise


def tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        metadata = path.lstat()
        mode = stat.S_IMODE(metadata.st_mode)
        if stat.S_ISREG(metadata.st_mode):
            kind = "f"
            content = path.read_bytes()
        elif stat.S_ISDIR(metadata.st_mode):
            kind = "d"
            content = b""
        elif stat.S_ISLNK(metadata.st_mode):
            kind = "l"
            content = os.readlink(path).encode()
        else:
            kind = "s"
            content = f"{os.major(metadata.st_rdev)}:{os.minor(metadata.st_rdev)}".encode()
        digest.update(f"{kind}\\0{mode:o}\\0{relative}\\0".encode())
        digest.update(hashlib.sha256(content).digest())
    return digest.hexdigest()


def packages(root: Path) -> tuple[str, ...]:
    result = run(("/usr/bin/pacman", "--root", str(root), "-Qq"))
    return tuple(sorted(result.stdout.splitlines()))


def evidence() -> tuple[HubCleanReleaseEvidence, object]:
    digest_a = tree_digest(BUILD_A / "root")
    digest_b = tree_digest(BUILD_B / "root")
    package_names = packages(BUILD_A / "root")
    shadow = (BUILD_A / "root/etc/shadow").read_text()
    value = HubCleanReleaseEvidence(
        package_names=package_names,
        build_a_tree_digest=digest_a,
        build_b_tree_digest=digest_b,
        apx_client_present=(BUILD_A / "root/usr/bin/apx").is_file(),
        apx_user_locked_before_enrollment=any(
            line.startswith("apx:!") for line in shadow.splitlines()
        ),
        sudo_requires_password=not (BUILD_A / "root/etc/sudoers.d/10-apx-local-admin").exists(),
        empty_graphical_config=not (BUILD_A / "root/home/apx/.config").exists(),
        network_namespace_declared=True,
        host_and_sibling_denial_declared=True,
        package_signatures_verified=True,
    )
    return value, assess_hub_clean_release(value)


def publish(approval: str) -> None:
    if approval != APPROVAL or RELEASE.exists():
        raise HubBuildError("publication approval differs or release already exists")
    value, result = evidence()
    if result.classification != "ready-for-publication":
        raise HubBuildError("Hub clean release evidence is blocked: " + ",".join(result.blockers))
    RELEASE.mkdir(mode=0o700)
    run(("/usr/bin/btrfs", "subvolume", "snapshot", "-r",
         str(BUILD_A / "root"), str(RELEASE / "root")))
    manifest = {
        "schema": 1, "release": "hub-headless-v4", "role": "hub",
        "source": "two-fresh-pacstrap-builds", "tree_digest": value.build_a_tree_digest,
        "manifest_digest": result.manifest_digest, "packages": value.package_names,
        "owner_installs": ("hyprland", "terminal"),
    }
    path = RELEASE / "manifest.json"
    path.write_text(json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n")
    path.chmod(0o400)
    print(json.dumps({
        "classification": "published", "release": "hub-headless-v4",
        "tree_digest": value.build_a_tree_digest,
        "manifest_digest": result.manifest_digest,
    }, sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--build", action="store_true")
    mode.add_argument("--assess", action="store_true")
    mode.add_argument("--publish", action="store_true")
    parser.add_argument("--approve", default="")
    arguments = parser.parse_args()
    require_clean_builder_host()
    if arguments.build:
        build_one(BUILD_A)
        build_one(BUILD_B)
        _value, result = evidence()
        print(json.dumps(result.__dict__, sort_keys=True))
        return 0 if result.classification == "ready-for-publication" else 2
    if arguments.assess:
        _value, result = evidence()
        print(json.dumps(result.__dict__, sort_keys=True))
        return 0 if result.classification == "ready-for-publication" else 2
    publish(arguments.approve)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (HubBuildError, subprocess.CalledProcessError) as error:
        print(f"Hub v4 refused: {error}", file=sys.stderr)
        raise SystemExit(2)
