"""Closed desktop-feature catalogue for APX Environment creation."""

from __future__ import annotations

MODULES = (
    "system", "cli-aur", "graphical", "desktop-integration", "locale-input",
    "network", "bluetooth", "audio", "graphics", "power", "devices-storage",
    "files", "web-documents", "multimedia", "office", "communication",
    "printing-scanning", "development", "shortcuts",
)

DEPENDENCIES = {
    "system": (), "cli-aur": ("system",), "graphical": ("system",),
    "desktop-integration": ("graphical",), "locale-input": ("system",),
    "network": ("system",), "bluetooth": ("system",), "audio": ("system",),
    "graphics": ("graphical",), "power": ("graphical",),
    "devices-storage": ("system",),
    "files": ("desktop-integration", "devices-storage"),
    "web-documents": ("desktop-integration", "network"),
    "multimedia": ("desktop-integration", "audio", "graphics"),
    "office": ("desktop-integration", "locale-input"),
    "communication": ("desktop-integration", "network", "audio", "graphics"),
    "printing-scanning": ("desktop-integration", "network", "devices-storage"),
    "development": ("cli-aur",), "shortcuts": ("graphical",),
}

PRESETS = {
    "basic": ("system", "cli-aur"),
    "intermediate": MODULES[:14] + ("shortcuts",),
    "complete": MODULES,
}

# The admitted graphical release already owns its GPU stack. Reinstalling that
# stack into every snapshot wastes space and can create a partial-upgrade
# conflict when the Host repositories move ahead of the immutable release.
# Modules therefore add only applications absent from that release.
PACKAGES = {
    "web-documents": ("evince",),
    "multimedia": ("ffmpeg", "gst-libav", "gst-plugins-good", "mpv"),
    "office": ("hunspell-en_gb", "libreoffice-fresh"),
    "communication": ("v4l-utils",),
    "printing-scanning": ("cups", "sane", "simple-scan", "system-config-printer"),
    "development": ("cmake", "ninja", "nodejs", "npm", "podman", "python-pip", "rust"),
}

# Reviewed native packages that are not available from the official Arch
# repositories. The runtime resolves these names through the Host-owned,
# digest-pinned artifact manifest before invoking pacman -U.
LOCAL_PACKAGES = {
    "web-documents": ("brave-bin",),
}

ESTIMATED_MIB = {
    "system": 420, "cli-aur": 260, "graphical": 520,
    "desktop-integration": 170, "locale-input": 190, "network": 70,
    "bluetooth": 35, "audio": 125, "graphics": 390, "power": 30,
    "devices-storage": 120, "files": 115, "web-documents": 360,
    "multimedia": 240, "office": 620, "communication": 55,
    "printing-scanning": 145, "development": 1150, "shortcuts": 8,
}


def normalize_modules(values: object) -> tuple[str, ...]:
    if type(values) not in {list, tuple} or not values:
        raise ValueError("Environment modules must be a non-empty list")
    if any(type(value) is not str or value not in MODULES for value in values):
        raise ValueError("Environment module is unsupported")
    selected = set(values)
    changed = True
    while changed:
        changed = False
        for module in tuple(selected):
            for dependency in DEPENDENCIES[module]:
                if dependency not in selected:
                    selected.add(dependency); changed = True
    return tuple(module for module in MODULES if module in selected)


def validate_selection(preset: object, values: object) -> tuple[str, tuple[str, ...]]:
    if type(preset) is not str or preset not in PRESETS:
        raise ValueError("Environment preset is unsupported")
    modules = normalize_modules(values)
    return preset, modules


def packages_for(values: object) -> tuple[str, ...]:
    modules = normalize_modules(values)
    return tuple(sorted({package for module in modules for package in PACKAGES.get(module, ())}))


def local_packages_for(values: object) -> tuple[str, ...]:
    modules = normalize_modules(values)
    return tuple(sorted({package for module in modules for package in LOCAL_PACKAGES.get(module, ())}))


def estimated_mib(values: object) -> int:
    return sum(ESTIMATED_MIB[module] for module in normalize_modules(values))
