"""Offline resolution of the first dated APX Hyprland role candidate."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

from apx_isolation import BASE_PACKAGES
from apx_repository_db import parse_repository_database
from apx_resolution import BASE_URI, DATABASE_DIGESTS, DATABASE_ROOT, RESOLUTION_ROOT, ResolvedPackage, parse_resolution_manifest


ROOT = Path("/tmp/apx-hyprland-resolution-20260711-v1")
BASE_MANIFEST = RESOLUTION_ROOT / "resolution-manifest.json"
GRAPHICAL_SEEDS = (
    "hyprland", "uwsm", "foot", "fuzzel", "mako",
    "xdg-desktop-portal-hyprland", "hyprpolkitagent",
    "pipewire-pulse", "wireplumber", "vulkan-radeon", "noto-fonts",
    "wl-clipboard", "grim", "slurp",
)
MAX_PACKAGES = 512
MAX_BYTES = 4 * 1024**3
MAX_OUTPUT = 4 * 1024**2


class GraphicalResolutionError(RuntimeError):
    """The fixed graphical role cannot be resolved from the dated databases."""


@dataclass(frozen=True)
class GraphicalResolutionManifest:
    schema_version: int
    base_manifest_digest: str
    database_digests: tuple[tuple[str, str], ...]
    graphical_seeds: tuple[str, ...]
    all_packages: tuple[ResolvedPackage, ...]
    role_packages: tuple[ResolvedPackage, ...]
    all_package_bytes: int
    role_package_bytes: int
    all_installed_bytes: int
    role_installed_bytes: int
    manifest_digest: str


def parse_graphical_manifest(text: str) -> GraphicalResolutionManifest:
    if not isinstance(text, str) or len(text.encode()) > MAX_OUTPUT:
        raise GraphicalResolutionError("graphical manifest is invalid or oversized")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as error:
        raise GraphicalResolutionError("graphical manifest JSON is invalid") from error
    expected = set(GraphicalResolutionManifest.__dataclass_fields__)
    if not isinstance(payload, dict) or set(payload) != expected:
        raise GraphicalResolutionError("graphical manifest fields do not match schema")
    package_fields = set(ResolvedPackage.__dataclass_fields__)
    def packages(name: str) -> tuple[ResolvedPackage, ...]:
        raw = payload[name]
        if not isinstance(raw, list) or any(not isinstance(item, dict) or set(item) != package_fields for item in raw):
            raise GraphicalResolutionError("graphical package fields do not match schema")
        return tuple(ResolvedPackage(**item) for item in raw)
    try:
        manifest = GraphicalResolutionManifest(
            payload["schema_version"], payload["base_manifest_digest"],
            tuple(tuple(item) for item in payload["database_digests"]),
            tuple(payload["graphical_seeds"]), packages("all_packages"),
            packages("role_packages"), payload["all_package_bytes"],
            payload["role_package_bytes"], payload["all_installed_bytes"],
            payload["role_installed_bytes"], payload["manifest_digest"],
        )
    except (TypeError, ValueError) as error:
        raise GraphicalResolutionError("graphical manifest values are malformed") from error
    unsigned = asdict(manifest); unsigned.pop("manifest_digest")
    digest = hashlib.sha256(json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    base = parse_resolution_manifest(BASE_MANIFEST.read_text(encoding="utf-8"))
    role_names = {item.name for item in manifest.role_packages}
    all_names = {item.name for item in manifest.all_packages}
    if (
        manifest.schema_version != 1 or manifest.base_manifest_digest != base.manifest_digest
        or manifest.database_digests != tuple(sorted(DATABASE_DIGESTS.items()))
        or manifest.graphical_seeds != GRAPHICAL_SEEDS
        or manifest.manifest_digest != digest
        or len(manifest.role_packages) != 194 or len(manifest.all_packages) != 332
        or len(role_names) != 194 or len(all_names) != 332
        or not role_names <= all_names or not set(GRAPHICAL_SEEDS) <= role_names
        or manifest.role_package_bytes != sum(item.compressed_size for item in manifest.role_packages)
        or manifest.all_package_bytes != sum(item.compressed_size for item in manifest.all_packages)
    ):
        raise GraphicalResolutionError("graphical manifest invariants do not match")
    return manifest


def fixed_command(root: Path, config: Path) -> tuple[str, ...]:
    return (
        "/usr/bin/pacman", "-Sp", "--print-format", "%r|%n|%v|%a|%f|%s|%l",
        "--config", str(config), "--dbpath", str(root / "db"),
        "--root", str(root / "root"), "--cachedir", str(root / "cache"),
        "--gpgdir", str(root / "gpg"), "--hookdir", str(root / "hooks"),
        "--logfile", str(root / "pacman.log"), "--", *BASE_PACKAGES, *GRAPHICAL_SEEDS,
    )


def _write(path: Path, content: str) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        os.write(descriptor, content.encode())
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def resolve_graphical_role() -> GraphicalResolutionManifest:
    base = parse_resolution_manifest(BASE_MANIFEST.read_text(encoding="utf-8"))
    databases = tuple(
        parse_repository_database(DATABASE_ROOT / f"{name}.db", repository=name, expected_sha256=digest)
        for name, digest in sorted(DATABASE_DIGESTS.items())
    )
    records = {(item.repository, item.name): item for database in databases for item in database.packages}
    if any(not any(item.name == seed for item in records.values()) for seed in GRAPHICAL_SEEDS):
        raise GraphicalResolutionError("one graphical seed is absent from the dated databases")
    try:
        os.mkdir(ROOT, 0o700)
    except FileExistsError as error:
        raise GraphicalResolutionError("graphical resolution root exists; refusing adoption") from error
    for relative in ("db/sync", "root/var/lib/pacman/local", "cache", "gpg", "hooks"):
        (ROOT / relative).mkdir(parents=True, mode=0o700)
    for name in ("core", "extra"):
        shutil.copyfile(DATABASE_ROOT / f"{name}.db", ROOT / "db/sync" / f"{name}.db")
    config = ROOT / "pacman.conf"
    _write(config, "[options]\nArchitecture = x86_64\nSigLevel = Required DatabaseOptional\n\n" +
           f"[core]\nServer = {BASE_URI}/core/os/x86_64\n\n" +
           f"[extra]\nServer = {BASE_URI}/extra/os/x86_64\n")
    outputs = []
    for _ in range(2):
        result = subprocess.run(fixed_command(ROOT, config), shell=False, capture_output=True, text=True,
                                timeout=60, env={"LC_ALL": "C", "PATH": "/usr/bin"}, check=False)
        if result.returncode != 0 or len(result.stdout.encode()) > MAX_OUTPUT:
            raise GraphicalResolutionError("offline graphical resolution failed")
        outputs.append(result.stdout)
    if outputs[0] != outputs[1]:
        raise GraphicalResolutionError("independent graphical resolver passes disagree")
    selected = []
    installed_sizes = {}
    for line in outputs[0].splitlines():
        fields = line.split("|")
        if len(fields) != 7:
            raise GraphicalResolutionError("graphical resolver row is malformed")
        repository, name, version, architecture, filename, size_text, uri = fields
        record = records.get((repository, name))
        if record is None or not size_text.isdigit():
            raise GraphicalResolutionError("graphical resolver selected unknown package")
        expected_uri = f"{BASE_URI}/{repository}/os/x86_64/{record.filename}"
        if (version, architecture, filename, int(size_text), uri) != (
            record.version, record.architecture, record.filename, record.compressed_size, expected_uri
        ):
            raise GraphicalResolutionError("graphical result disagrees with repository evidence")
        selected.append(ResolvedPackage(repository, name, version, architecture, filename,
                                        record.compressed_size, record.sha256, record.pgp_signature,
                                        uri, uri + ".sig"))
        installed_sizes[name] = record.installed_size
    selected.sort(key=lambda item: (item.repository, item.filename))
    if not selected or len(selected) > MAX_PACKAGES or len({item.name for item in selected}) != len(selected):
        raise GraphicalResolutionError("graphical package set is invalid")
    base_names = {item.name for item in base.packages}
    selected_names = {item.name for item in selected}
    if not base_names <= selected_names or not set(GRAPHICAL_SEEDS) <= selected_names:
        raise GraphicalResolutionError("graphical closure omits base or role seed")
    role = tuple(item for item in selected if item.name not in base_names)
    all_bytes = sum(item.compressed_size for item in selected)
    role_bytes = sum(item.compressed_size for item in role)
    all_installed = sum(installed_sizes[item.name] for item in selected)
    role_installed = sum(installed_sizes[item.name] for item in role)
    if all_bytes > MAX_BYTES or all_installed > MAX_BYTES:
        raise GraphicalResolutionError("graphical closure exceeds planning bound")
    draft = GraphicalResolutionManifest(
        1, base.manifest_digest, tuple(sorted(DATABASE_DIGESTS.items())), GRAPHICAL_SEEDS,
        tuple(selected), role, all_bytes, role_bytes, all_installed, role_installed, "0" * 64,
    )
    payload = asdict(draft); payload.pop("manifest_digest")
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    manifest = replace(draft, manifest_digest=digest)
    _write(ROOT / "graphical-resolution-manifest.json", json.dumps(asdict(manifest), sort_keys=True, indent=2) + "\n")
    return manifest


def main() -> int:
    result = resolve_graphical_role()
    print("APX Hyprland role offline resolution")
    print(f"Total packages with base: {len(result.all_packages)}")
    print(f"New role packages: {len(result.role_packages)}")
    print(f"New download bytes: {result.role_package_bytes}")
    print(f"New installed bytes: {result.role_installed_bytes}")
    print(f"Manifest digest: {result.manifest_digest}")
    print("Network/download/install/extract/execute effects: none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
