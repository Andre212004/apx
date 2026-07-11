"""Read-only practical host validation for APX milestone 3A."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import stat
from typing import Callable, Iterable, Sequence

from apx_ownership import describe_numeric_owner, read_subordinate_ranges


ENVIRONMENTS = (
    ("hub", "apx-hub", "/home/apx-hub"),
    ("development", "apx-development", "/home/apx-development"),
    ("trial", "apx-trial", "/home/apx-trial"),
)
BRAVE_DATA_NAMES = (".config/BraveSoftware", ".cache/BraveSoftware")


@dataclass(frozen=True)
class PracticalEnvironment:
    logical_name: str
    account: str
    account_state: str
    uid: int | None
    primary_gid: int | None
    home: str
    home_state: str
    subvolume: str
    owner: str
    mode: str
    sessions: int | None
    processes: str
    mounts: str
    contents: str
    usage: str
    removal_evidence: str


@dataclass(frozen=True)
class BraveState:
    executable: str
    package: str
    arch_packages: tuple[str, ...]
    desktop_entries: tuple[str, ...]
    flatpak: str
    user_data: tuple[tuple[str, str], ...]
    mechanism: str


@dataclass(frozen=True)
class PracticalReport:
    environments: tuple[PracticalEnvironment, ...]
    brave: BraveState
    sessions: object
    display_manager: str
    tools: tuple[tuple[str, str], ...]
    seats: str


def _command(runner: Callable[[Sequence[str], float], object], argv: Sequence[str]) -> tuple[str, str]:
    result = runner(tuple(argv), 5.0)
    if getattr(result, "failure", None) or getattr(result, "returncode", None) is None:
        return "unavailable", ""
    return ("confirmed", getattr(result, "stdout", "").strip()) if result.returncode == 0 else ("unavailable", "")


def _submounts(runner: Callable[[Sequence[str], float], object], home: str) -> tuple[str, str]:
    result = runner(("findmnt", "--json", "--submounts", home), 5.0)
    if getattr(result, "failure", None) or getattr(result, "returncode", None) is None:
        return "unavailable", ""
    if result.returncode == 1 and not getattr(result, "stdout", "").strip():
        return "confirmed", ""
    return ("confirmed", result.stdout.strip()) if result.returncode == 0 else ("unavailable", "")


def _metadata(path: str, lstat_func: Callable[[str], os.stat_result]) -> tuple[str, os.stat_result | None]:
    try:
        return "present", lstat_func(path)
    except FileNotFoundError:
        return "absent", None
    except OSError:
        return "unavailable", None


def observe_practical(
    *, accounts: Sequence[object], sessions: object,
    mount_observer: Callable[[str], object], btrfs_observer: Callable[[str, object], object],
    command_runner: Callable[[Sequence[str], float], object],
    lstat_func: Callable[[str], os.stat_result] = os.lstat,
    scandir_func: Callable[[str], Iterable[object]] = os.scandir,
    which_func: Callable[[str], str | None], readlink_func: Callable[[str], str] = os.readlink,
    subordinate_uid_file: Path = Path("/etc/subuid"),
) -> PracticalReport:
    by_name = {getattr(account, "pw_name", ""): account for account in accounts}
    session_items = getattr(sessions, "sessions", ())
    subordinate_uids = read_subordinate_ranges(subordinate_uid_file)
    environments: list[PracticalEnvironment] = []
    for logical, name, home in ENVIRONMENTS:
        account = by_name.get(name)
        home_state, metadata = _metadata(home, lstat_func)
        mount = mount_observer(home)
        btrfs = btrfs_observer(home, mount) if home_state == "present" else None
        session_count = sum(1 for item in session_items if getattr(item, "username", None) == name) if getattr(sessions, "status", "unavailable") == "confirmed" else None
        process_state, process_output = _command(command_runner, ("ps", "-U", name, "-o", "pid=,comm=")) if account else ("confirmed", "")
        mount_state, mount_output = _submounts(command_runner, home) if home_state == "present" else ("confirmed", "")
        usage_state, usage_output = _command(command_runner, ("du", "-s", "-B1", home)) if home_state == "present" else ("confirmed", "")
        try:
            with scandir_func(home) as entries:
                names = sorted(entry.name for entry in entries)
            contents = "empty" if not names else f"non-empty ({len(names)} top-level entries: {', '.join(names[:8])}{'…' if len(names) > 8 else ''})"
        except FileNotFoundError:
            contents = "absent"
        except OSError:
            contents = "unavailable"
        owner = (
            describe_numeric_owner(metadata.st_uid, subordinate_uids, identifier="UID")
            if metadata else home_state
        )
        mode = f"{stat.S_IMODE(metadata.st_mode):04o}" if metadata else home_state
        blockers = []
        unknown = []
        if session_count is None: unknown.append("sessions")
        elif session_count: blockers.append("active sessions")
        if process_state != "confirmed": unknown.append("processes")
        elif process_output: blockers.append("running processes")
        if mount_state != "confirmed": unknown.append("mounts")
        elif mount_output: blockers.append("mounted paths")
        if contents == "unavailable": unknown.append("home contents")
        elif contents.startswith("non-empty"): blockers.append("non-empty home")
        if account and metadata and metadata.st_uid != account.pw_uid: blockers.append("unexpected ownership")
        if metadata and stat.S_IMODE(metadata.st_mode) != 0o700: blockers.append("unexpected permissions")
        if blockers:
            removal = "confirmed blocker: " + ", ".join(blockers)
            if unknown:
                removal += "; unknown: " + ", ".join(unknown)
        elif unknown:
            removal = "unknown: " + ", ".join(unknown)
        else:
            removal = "no blocker detected (not a deletion-safety claim)"
        environments.append(PracticalEnvironment(
            logical, name, "present" if account else "absent", getattr(account, "pw_uid", None),
            getattr(account, "pw_gid", None), home, home_state,
            getattr(btrfs, "subvolume", "unavailable"), owner, mode, session_count,
            "unavailable" if process_state != "confirmed" else ("none" if not process_output else f"present ({len(process_output.splitlines())})"),
            "unavailable" if mount_state != "confirmed" else ("none" if not mount_output else "present"), contents,
            "unavailable" if usage_state != "confirmed" else (usage_output.split()[0] + " bytes" if usage_output else "0 bytes"), removal,
        ))

    executable = which_func("brave") or which_func("brave-browser")
    pkg_state, pkg_output = _command(command_runner, ("pacman", "-Qq"))
    packages = tuple(sorted(line for line in pkg_output.splitlines() if "brave" in line.lower())) if pkg_state == "confirmed" else ()
    owner_state, owner_output = _command(command_runner, ("pacman", "-Qo", executable)) if executable else ("confirmed", "")
    package = owner_output if owner_state == "confirmed" and owner_output else "unavailable" if owner_state != "confirmed" else "not package-owned"
    desktop = tuple(str(path) for path in (Path("/usr/share/applications/brave-browser.desktop"), Path("/usr/local/share/applications/brave-browser.desktop")) if _metadata(str(path), lstat_func)[0] == "present")
    if which_func("flatpak"):
        flatpak_state, flatpak_output = _command(command_runner, ("flatpak", "list", "--app", "--columns=application"))
        flatpak = "present" if flatpak_state == "confirmed" and any("brave" in x.lower() for x in flatpak_output.splitlines()) else "absent" if flatpak_state == "confirmed" else "unavailable"
    else: flatpak = "not-installed"
    user_data = []
    for _, name, home in ENVIRONMENTS:
        states = [_metadata(str(Path(home) / relative), lstat_func)[0] for relative in BRAVE_DATA_NAMES]
        user_data.append((name, "present" if "present" in states else "unavailable" if "unavailable" in states else "absent"))
    mechanism = "Arch package" if packages or (executable and "owned by" in package) else "Flatpak" if flatpak == "present" else "unknown" if executable else "not detected"
    brave = BraveState(executable or "not found", package, packages, desktop, flatpak, tuple(user_data), mechanism)

    dm_state, dm_meta = _metadata("/etc/systemd/system/display-manager.service", lstat_func)
    display_manager = readlink_func("/etc/systemd/system/display-manager.service") if dm_state == "present" and dm_meta and stat.S_ISLNK(dm_meta.st_mode) else dm_state
    tools = tuple((name, "available" if which_func(name) else "unavailable") for name in ("loginctl", "systemctl", "Hyprland", "podman"))
    seat_state, seat_output = _command(command_runner, ("loginctl", "list-seats", "--no-legend", "--no-pager"))
    return PracticalReport(tuple(environments), brave, sessions, display_manager, tools, seat_output if seat_state == "confirmed" else "unavailable")


def render_practical(report: PracticalReport) -> str:
    lines = ["APX practical host validation", "Mode: read-only", "", "Environments:"]
    for item in report.environments:
        lines.extend((
            f"- {item.logical_name} ({item.account})", f"  Account: {item.account_state}; UID: {item.uid if item.uid is not None else 'unavailable'}; primary GID: {item.primary_gid if item.primary_gid is not None else 'unavailable'}",
            f"  Home: {item.home} ({item.home_state}); subvolume: {item.subvolume}; owner UID: {item.owner}; mode: {item.mode}",
            f"  Sessions: {item.sessions if item.sessions is not None else 'unavailable'}; processes: {item.processes}; mounts: {item.mounts}",
            f"  Contents: {item.contents}; approximate usage: {item.usage}", f"  Removal evidence: {item.removal_evidence}",
        ))
    brave = report.brave
    lines.extend(("", "Brave:", f"- Mechanism: {brave.mechanism}", f"- Executable: {brave.executable}", f"- Package ownership: {brave.package}", f"- Brave-related Arch packages: {', '.join(brave.arch_packages) or 'none detected'}", f"- Desktop entries: {', '.join(brave.desktop_entries) or 'none detected'}", f"- Flatpak: {brave.flatpak}", "- Per-user data: " + "; ".join(f"{name}={state}" for name, state in brave.user_data)))
    session_items = getattr(report.sessions, "sessions", ())
    graphical = sum(1 for item in session_items if getattr(item, "graphical", "no") == "yes")
    lines.extend(("", "Session switching:", f"- Display manager: {report.display_manager}", f"- Logind status: {getattr(report.sessions, 'status', 'unavailable')}; known sessions: {len(session_items)}; concurrent graphical sessions: {'yes' if graphical > 1 else 'no' if getattr(report.sessions, 'status', '') == 'confirmed' else 'unavailable'}", f"- Seats: {report.seats}", "- Tools: " + ", ".join(f"{name}={state}" for name, state in report.tools)))
    for item in session_items:
        lines.append(f"  Session {item.session_id}: user={item.username}; type={item.session_type}; class={item.session_class}; seat={item.seat}; state={item.state}; VT={getattr(item, 'vt', 'unavailable')}")
    return "\n".join(lines)
