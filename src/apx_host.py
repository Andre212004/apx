"""Read-only readiness inspection for the first APX Environment experiment."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import stat
from typing import Callable, Iterable, Sequence


TRIAL_LOGICAL_NAME = "trial"
TRIAL_ACCOUNT = "apx-trial"
TRIAL_HOME = "/home/apx-trial"
SESSION_DIRECTORIES = (
    Path("/usr/share/wayland-sessions"),
    Path("/usr/share/xsessions"),
)


@dataclass(frozen=True)
class ReadinessCheck:
    section: str
    name: str
    classification: str
    evidence: str


@dataclass(frozen=True)
class HostReadinessReport:
    checks: tuple[ReadinessCheck, ...]
    overall: str
    manual_plan: tuple[str, ...]


MANUAL_TRIAL_PLAN = (
    "Recheck every readiness precondition in an authoritative real-host context.",
    "Create the dedicated Btrfs subvolume at /home/apx-trial.",
    "Create apx-trial without creating or populating a normal home directory.",
    "Apply apx-trial ownership, its private primary group, and mode 0700.",
    "Publish the schema-v1 APX registration for trial from freshly observed storage identity as the late commit boundary.",
    "Verify the account, home, Btrfs identity, ownership, group, mode, registration, and marker absence.",
    "Test graphical login from Hub to apx-trial with the configured Wayland session, logout, and return to Hub.",
    "Inspect apx-trial with APX and retain the complete consistency evidence.",
    "Stop without automatic cleanup and preserve evidence on any unexpected state.",
)


def _positive(authoritative: bool) -> str:
    return "ready" if authoritative else "requires-host-confirmation"


def _conflict(authoritative: bool) -> str:
    # A visible conflict is sufficient reason to stop, even when the observer
    # cannot prove that positive evidence is authoritative. A false positive
    # only delays work; treating a real conflict as readiness could damage data.
    return "blocked"


def _check(
    section: str, name: str, classification: str, evidence: str
) -> ReadinessCheck:
    return ReadinessCheck(section, name, classification, evidence)


def classify_overall(checks: Sequence[ReadinessCheck]) -> str:
    states = {check.classification for check in checks}
    if "blocked" in states:
        return "blocked"
    if states & {"requires-host-confirmation", "unavailable"}:
        return "requires-host-confirmation"
    return "ready-for-manual-experiment"


def _command_state(result: object, *, active: bool = False) -> tuple[str, str]:
    failure = getattr(result, "failure", None)
    returncode = getattr(result, "returncode", None)
    stdout = getattr(result, "stdout", "").strip()
    if failure or returncode is None:
        return "unavailable", f"observation {failure or 'unavailable'}"
    if active:
        if returncode == 0 and stdout == "active":
            return "ready", "sddm.service reported active"
        if returncode in {0, 3} and stdout in {"inactive", "failed", "deactivating"}:
            return "blocked", f"sddm.service reported {stdout}"
    if returncode != 0:
        return "unavailable", f"observation failed with exit code {returncode}"
    return "ready", stdout or "command completed without output"


def observe_host_readiness(
    *,
    accounts: Sequence[object],
    mount: object,
    registration: object,
    incomplete_operation: object,
    sessions: object,
    lstat_func: Callable[[str | os.PathLike[str]], os.stat_result] = os.lstat,
    command_runner: Callable[[Sequence[str], float], object],
    which_func: Callable[[str], str | None],
    scandir_func: Callable[[str | os.PathLike[str]], Iterable[object]] = os.scandir,
    readlink_func: Callable[[str | os.PathLike[str]], str] = os.readlink,
    session_directories: Sequence[Path] = SESSION_DIRECTORIES,
    display_manager_link: Path = Path("/etc/systemd/system/display-manager.service"),
    authoritative_host: bool = False,
) -> HostReadinessReport:
    checks: list[ReadinessCheck] = []
    account_by_name = {getattr(account, "pw_name", ""): account for account in accounts}
    for name, home in (
        ("apx-hub", "/home/apx-hub"),
        ("apx-development", "/home/apx-development"),
    ):
        account = account_by_name.get(name)
        if account is None:
            checks.append(_check("APX identities", f"{name} account", _conflict(authoritative_host), "account is absent"))
        else:
            checks.append(_check("APX identities", f"{name} account", _positive(authoritative_host), "account exists"))
            observed_home = getattr(account, "pw_dir", None)
            state = _positive(authoritative_host) if observed_home == home else _conflict(authoritative_host)
            checks.append(_check("APX identities", f"{name} canonical home", state, f"observed {observed_home or 'unavailable'}; expected {home}"))

    trial_account = account_by_name.get(TRIAL_ACCOUNT)
    checks.append(_check(
        "APX identities", "apx-trial account absent",
        _conflict(authoritative_host) if trial_account is not None else _positive(authoritative_host),
        "account exists" if trial_account is not None else "account is absent",
    ))
    try:
        lstat_func(TRIAL_HOME)
    except FileNotFoundError:
        trial_home_state, trial_home_evidence = _positive(authoritative_host), "path is absent"
    except OSError:
        trial_home_state, trial_home_evidence = "unavailable", "path metadata unavailable"
    else:
        trial_home_state, trial_home_evidence = _conflict(authoritative_host), "path already exists"
    checks.append(_check("APX identities", "/home/apx-trial absent", trial_home_state, trial_home_evidence))

    registration_state = str(getattr(registration, "state", "unavailable"))
    if registration_state == "absent":
        reg_class = _positive(authoritative_host)
    elif registration_state == "unavailable":
        reg_class = "unavailable"
    else:
        reg_class = _conflict(authoritative_host)
    checks.append(_check("APX identities", "trial registration absent", reg_class, f"registration observation: {registration_state}"))
    marker_state = getattr(incomplete_operation, "absent", "unavailable")
    marker_class = (
        _positive(authoritative_host) if marker_state == "confirmed"
        else _conflict(authoritative_host) if marker_state == "not-satisfied"
        else "unavailable"
    )
    checks.append(_check("APX identities", "trial incomplete marker absent", marker_class, f"marker absence: {marker_state}"))

    mount_status = getattr(mount, "status", "unavailable")
    filesystem = getattr(mount, "filesystem_type", None)
    read_only = getattr(mount, "read_only", None)
    if mount_status != "confirmed":
        fs_class = "unavailable"
    elif filesystem != "btrfs":
        fs_class = _conflict(authoritative_host)
    elif read_only is True:
        fs_class = _conflict(authoritative_host)
    else:
        fs_class = _positive(authoritative_host)
    checks.append(_check("Storage", "filesystem containing /home", fs_class, f"filesystem: {filesystem or 'unavailable'}"))
    checks.append(_check(
        "Storage", "/home placement",
        "unavailable" if mount_status != "confirmed" else _positive(authoritative_host),
        "/home is the observed mount target" if getattr(mount, "target", None) == "/home" else f"/home is within mount {getattr(mount, 'target', None) or 'unavailable'}",
    ))
    checks.append(_check(
        "Storage", "mount options",
        "unavailable" if mount_status != "confirmed" else _conflict(authoritative_host) if read_only is True else _positive(authoritative_host),
        f"options: {getattr(mount, 'options', None) or 'unavailable'}; read-only: {read_only if read_only is not None else 'unavailable'}",
    ))
    try:
        parent_metadata = lstat_func("/home")
    except OSError:
        parent_class, parent_evidence = "unavailable", "parent metadata unavailable"
    else:
        if stat.S_ISLNK(parent_metadata.st_mode) or not stat.S_ISDIR(parent_metadata.st_mode):
            parent_class, parent_evidence = _conflict(authoritative_host), "parent is a symlink or not a directory"
        else:
            parent_class, parent_evidence = _positive(authoritative_host), "parent is a non-symlink directory"
    checks.append(_check("Storage", "safe target parent", parent_class, parent_evidence))
    principle_class = (
        "blocked" if "blocked" in {fs_class, parent_class}
        else "unavailable" if "unavailable" in {fs_class, parent_class}
        else "requires-host-confirmation" if "requires-host-confirmation" in {fs_class, parent_class}
        else _positive(authoritative_host)
    )
    checks.append(_check("Storage", "dedicated trial subvolume can be created in principle", principle_class, "requires a writable Btrfs context and safe /home parent"))

    hyprland_path = which_func("Hyprland")
    checks.append(_check(
        "Graphical session stack", "Hyprland availability",
        _positive(authoritative_host) if hyprland_path else _conflict(authoritative_host),
        "Hyprland executable found" if hyprland_path else "Hyprland executable not found",
    ))
    try:
        dm_metadata = lstat_func(display_manager_link)
        if stat.S_ISLNK(dm_metadata.st_mode):
            target = readlink_func(display_manager_link)
            dm_class = _positive(authoritative_host)
            dm_evidence = f"display-manager.service -> {target}"
        else:
            dm_class, dm_evidence = "requires-host-confirmation", "display-manager.service is not a symlink"
    except FileNotFoundError:
        dm_class, dm_evidence = "unavailable", "display-manager.service link is absent"
    except OSError:
        dm_class, dm_evidence = "unavailable", "display-manager configuration unavailable"
    checks.append(_check("Graphical session stack", "display-manager configuration", dm_class, dm_evidence))

    session_names: list[str] = []
    session_unavailable = False
    for directory in session_directories:
        try:
            with scandir_func(directory) as entries:
                session_names.extend(
                    entry.name for entry in entries
                    if entry.name.endswith(".desktop") and not entry.is_symlink()
                )
        except FileNotFoundError:
            continue
        except OSError:
            session_unavailable = True
    if session_names:
        definition_class = _positive(authoritative_host)
        definition_evidence = "definitions: " + ", ".join(sorted(set(session_names)))
    elif session_unavailable:
        definition_class, definition_evidence = "unavailable", "session definitions unavailable"
    else:
        definition_class, definition_evidence = _conflict(authoritative_host), "no graphical session definition found"
    checks.append(_check("Graphical session stack", "graphical session definitions", definition_class, definition_evidence))
    session_status = getattr(sessions, "status", "unavailable")
    checks.append(_check(
        "Graphical session stack", "current sessions",
        _positive(authoritative_host) if session_status == "confirmed" else "unavailable",
        f"loginctl observation: {session_status}",
    ))

    useradd = which_func("useradd")
    for name, evidence in (
        ("normal UID/GID allocation", "requires authoritative account-policy confirmation"),
        ("private primary group", "requires authoritative account-policy confirmation"),
        ("graphical login account", "requires authoritative display-manager and shell policy confirmation"),
        ("home mode 0700", "supported by the planned explicit permission policy"),
        ("account creation without automatic home", "useradd supports explicit no-create-home policy"),
    ):
        checks.append(_check(
            "Account policy readiness", name,
            _positive(authoritative_host) if useradd else _conflict(authoritative_host),
            evidence if useradd else "useradd executable not found",
        ))
    global_apps = tuple(filter(None, (
        which_func("brave"), which_func("foot"), which_func("alacritty"),
        which_func("kitty"),
    )))
    checks.append(_check(
        "Account policy readiness", "globally installed applications",
        _positive(authoritative_host) if global_apps else "requires-host-confirmation",
        "global application executables found" if global_apps else "application visibility requires host confirmation",
    ))

    checks_tuple = tuple(checks)
    return HostReadinessReport(
        checks_tuple, classify_overall(checks_tuple), MANUAL_TRIAL_PLAN
    )


def render_host_readiness(report: HostReadinessReport) -> str:
    lines = ["APX host readiness", "Target: trial (apx-trial, /home/apx-trial, standard)"]
    current_section = None
    for check in report.checks:
        if check.section != current_section:
            current_section = check.section
            lines.extend(("", f"{current_section}:"))
        lines.append(f"- {check.name}: {check.classification} — {check.evidence}")
    lines.extend(("", f"Overall readiness: {report.overall}", "", "Manual experiment plan (not executed):"))
    lines.extend(f"{index}. {step}" for index, step in enumerate(report.manual_plan, 1))
    return "\n".join(lines)
