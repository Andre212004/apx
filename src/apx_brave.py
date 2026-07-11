"""Read-only Brave isolation planning for APX Development."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class IsolationOption:
    name: str
    availability: str
    assessment: str


@dataclass(frozen=True)
class BraveIsolationReport:
    brave: object
    global_visibility: str
    options: tuple[IsolationOption, ...]
    recommendation: str
    backup: tuple[str, ...]
    rollback: tuple[str, ...]
    approvals: tuple[str, ...]
    overall: str


def build_brave_isolation_report(
    brave: object, which_func: Callable[[str], str | None]
) -> BraveIsolationReport:
    executable = str(getattr(brave, "executable", "not found"))
    desktop_entries = tuple(getattr(brave, "desktop_entries", ()))
    if executable.startswith(("/usr/", "/bin/", "/opt/")):
        visibility = (
            "system-wide executable"
            + (" and system desktop entry" if desktop_entries else "")
            + "; visible to APX users unless a separate access policy intervenes"
        )
    elif executable == "not found":
        visibility = "no globally resolved Brave executable detected"
    else:
        visibility = "unknown; executable is outside recognized system paths"

    flatpak_available = which_func("flatpak") is not None
    container_tools = tuple(
        name for name in ("distrobox", "podman", "docker") if which_func(name)
    )
    options = (
        IsolationOption(
            "Per-user Flatpak",
            "available" if flatpak_available else "requires Flatpak installation",
            "Best daily-use fit: per-user application scope, routine updates, desktop integration, and straightforward removal; adds a runtime and requires repository trust review.",
        ),
        IsolationOption(
            "User-local AppImage or extracted bundle",
            "possible in principle",
            "No system package exposure, but updates, authenticity checks, sandboxing, and desktop integration become manual and upstream artifact availability must be verified.",
        ),
        IsolationOption(
            "Distrobox or container",
            "available via " + ", ".join(container_tools) if container_tools else "requires a container tool",
            "Strong packaging separation but more browser integration, GPU, portal, update, and maintenance complexity than this first experiment needs.",
        ),
        IsolationOption(
            "Keep the Arch package and hide launchers",
            "current mechanism",
            "Low effort but not application isolation: the executable remains globally installed and callable by every Environment.",
        ),
    )
    recommendation = (
        "First experiment: preserve the apx-development profile, then test Brave as a per-user Flatpak owned by apx-development. "
        + ("Flatpak is already available." if flatpak_available else "Flatpak is not installed, so installing it requires separate explicit approval.")
        + " Do not remove the global Arch package until the isolated instance, profile migration, compositor-independent launch integration, and updates are validated."
    )
    backup = (
        "Back up /home/apx-development/.config/BraveSoftware before profile migration.",
        "Optionally preserve /home/apx-development/.cache/BraveSoftware only for diagnostic continuity; cache is not authoritative profile data.",
        "Record the current brave-bin package version, executable ownership, and desktop entry before changing installation scope.",
    )
    rollback = (
        "Keep brave-bin installed during the experiment so the current launcher remains recoverable.",
        "Remove only the experimental per-user installation and restore the backed-up development profile if validation fails.",
        "Profile formats may migrate forward; rollback is not guaranteed without a pre-experiment backup.",
    )
    approvals = (
        "Separate approval is required to install Flatpak or any other runtime.",
        "Separate approval is required to download or install Brave for apx-development.",
        "Separate approval is required to remove the global brave-bin package or its system desktop entry.",
        "No installation, removal, download, profile migration, or configuration change is performed by this report.",
    )
    user_data = dict(getattr(brave, "user_data", ()))
    unknown = sorted(name for name, state in user_data.items() if state == "unavailable")
    overall = (
        "ready for a separately approved per-user isolation experiment"
        if user_data.get("apx-development") == "present"
        else "incomplete because apx-development Brave data is unavailable"
    )
    if unknown:
        overall += "; other-user data unavailable: " + ", ".join(unknown)
    return BraveIsolationReport(
        brave, visibility, options, recommendation, backup, rollback, approvals, overall
    )


def render_brave_isolation(report: BraveIsolationReport) -> str:
    brave = report.brave
    lines = [
        "APX Brave isolation readiness",
        "Mode: read-only; no changes executed",
        "Target: apx-development",
        "",
        "Current installation:",
        f"- Mechanism: {getattr(brave, 'mechanism', 'unknown')}",
        f"- Executable: {getattr(brave, 'executable', 'unavailable')}",
        f"- Package ownership: {getattr(brave, 'package', 'unavailable')}",
        f"- Arch packages: {', '.join(getattr(brave, 'arch_packages', ())) or 'none detected'}",
        f"- Desktop entries: {', '.join(getattr(brave, 'desktop_entries', ())) or 'none detected'}",
        f"- Flatpak Brave: {getattr(brave, 'flatpak', 'unavailable')}",
        f"- Global visibility: {report.global_visibility}",
        "- Per-user data: " + "; ".join(
            f"{name}={state}" for name, state in getattr(brave, "user_data", ())
        ),
        "",
        "Isolation options:",
    ]
    lines.extend(
        f"- {option.name}: {option.availability} — {option.assessment}"
        for option in report.options
    )
    lines.extend(("", "Recommended first experiment:", f"- {report.recommendation}"))
    for heading, items in (
        ("Backup requirements:", report.backup),
        ("Rollback:", report.rollback),
        ("Approval requirements:", report.approvals),
    ):
        lines.extend(("", heading))
        lines.extend(f"- {item}" for item in items)
    lines.extend(("", f"Overall result: {report.overall}"))
    return "\n".join(lines)
