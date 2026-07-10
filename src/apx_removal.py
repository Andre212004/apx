"""Non-executing APX Environment removal planning."""

from __future__ import annotations

from dataclasses import dataclass
import os
import stat
from typing import Callable, Iterable, Sequence

from apx_practical import _command, _metadata, _submounts


@dataclass(frozen=True)
class RemovalEvidence:
    logical_name: str
    account_name: str
    canonical_home: str
    account: object | None
    home_state: str
    home_metadata: os.stat_result | None
    subvolume: str
    sessions: int | None
    processes: str
    mounts: str
    contents: str
    usage: str
    registration: str


@dataclass(frozen=True)
class RemovalCheck:
    name: str
    classification: str
    evidence: str


@dataclass(frozen=True)
class RemovalReport:
    logical_name: str
    account_name: str
    home: str
    checks: tuple[RemovalCheck, ...]
    loss: tuple[str, ...]
    archive: tuple[str, ...]
    plan: tuple[str, ...]
    overall: str


REMOVAL_PLAN = (
    "Revalidate that no active sessions exist. [read-only]",
    "Revalidate that no processes are owned by the account. [read-only]",
    "Revalidate that no mounts are associated with the canonical home. [read-only]",
    "Inspect the home and create a separately approved archive when data must be retained. [archive write; may require privilege]",
    "Record UID, primary GID, canonical home, ownership, permissions, Btrfs identity, and APX metadata needed for reconstruction. [archive write]",
    "Remove the Linux account without implicit recursive home deletion or following unexpected paths. [privileged; irreversible identity removal]",
    "Deliberately archive or remove the canonical Btrfs home subvolume; handle a non-subvolume home explicitly. [privileged; irreversible without backup]",
    "Remove only canonical APX-owned registration and incomplete-operation metadata that exists. [privileged; irreversible metadata removal]",
    "Verify that the account, sessions, processes, mounts, canonical home, registration, and incomplete marker are absent. [read-only]",
)


def _processes(
    runner: Callable[[Sequence[str], float], object], account_name: str
) -> tuple[str, str]:
    result = runner(("ps", "-U", account_name, "-o", "pid=,comm="), 5.0)
    if getattr(result, "failure", None) or getattr(result, "returncode", None) is None:
        return "unavailable", ""
    output = getattr(result, "stdout", "").strip()
    if result.returncode == 0 or (result.returncode == 1 and not output):
        return "confirmed", output
    return "unavailable", ""


def observe_removal_evidence(
    *, logical_name: str, account_name: str, canonical_home: str,
    accounts: Sequence[object], sessions: object,
    mount_observer: Callable[[str], object],
    btrfs_observer: Callable[[str, object], object],
    command_runner: Callable[[Sequence[str], float], object],
    registration: object,
    lstat_func: Callable[[str], os.stat_result] = os.lstat,
    scandir_func: Callable[[str], Iterable[object]] = os.scandir,
) -> RemovalEvidence:
    account = next((item for item in accounts if getattr(item, "pw_name", None) == account_name), None)
    home_state, metadata = _metadata(canonical_home, lstat_func)
    if home_state == "present":
        mount = mount_observer(canonical_home)
        subvolume = getattr(btrfs_observer(canonical_home, mount), "subvolume", "unavailable")
        mount_state, mount_output = _submounts(command_runner, canonical_home)
        usage_state, usage_output = _command(command_runner, ("du", "-s", "-B1", canonical_home))
        try:
            with scandir_func(canonical_home) as entries:
                names = sorted(entry.name for entry in entries)
            contents = "empty" if not names else f"non-empty ({len(names)} top-level entries: {', '.join(names[:8])}{'…' if len(names) > 8 else ''})"
        except OSError:
            contents = "unavailable"
    else:
        subvolume, mount_state, mount_output = "not applicable", "confirmed", ""
        usage_state, usage_output, contents = "confirmed", "", home_state
    session_count = sum(1 for item in getattr(sessions, "sessions", ()) if getattr(item, "username", None) == account_name) if getattr(sessions, "status", "unavailable") == "confirmed" else None
    process_state, process_output = _processes(command_runner, account_name) if account else ("confirmed", "")
    return RemovalEvidence(
        logical_name, account_name, canonical_home, account, home_state, metadata,
        subvolume, session_count,
        "unavailable" if process_state != "confirmed" else ("none" if not process_output else f"present ({len(process_output.splitlines())})"),
        "unavailable" if mount_state != "confirmed" else ("none" if not mount_output else "present"),
        contents, "unavailable" if usage_state != "confirmed" else (usage_output.split()[0] + " bytes" if usage_output else "0 bytes"),
        str(getattr(registration, "state", "unavailable")),
    )


def build_removal_report(evidence: RemovalEvidence) -> RemovalReport:
    checks: list[RemovalCheck] = []
    def add(name: str, classification: str, detail: str) -> None:
        checks.append(RemovalCheck(name, classification, detail))
    if evidence.logical_name == "hub":
        add("Hub protection", "blocked", "the Hub is a protected Environment")
        return RemovalReport(evidence.logical_name, evidence.account_name, evidence.canonical_home, tuple(checks), (), (), (), "protected Environment")
    account = evidence.account
    if account is None and evidence.home_state == "absent":
        add("Environment existence", "not applicable", "canonical account and home are absent")
        return RemovalReport(evidence.logical_name, evidence.account_name, evidence.canonical_home, tuple(checks), (), (), (), "Environment does not exist")
    add("Account exists", "ready" if account else "blocked", "account exists" if account else "canonical account is absent while other state exists")
    if account:
        configured = getattr(account, "pw_dir", None)
        add("Canonical account home", "ready" if configured == evidence.canonical_home else "blocked", f"configured {configured or 'unavailable'}; expected {evidence.canonical_home}")
    add("Canonical home exists", "ready" if evidence.home_state == "present" else "blocked" if evidence.home_state == "absent" else "unknown", evidence.home_state)
    metadata = evidence.home_metadata
    if account and metadata:
        add("Home ownership", "ready" if metadata.st_uid == getattr(account, "pw_uid", None) else "blocked", f"owner UID {metadata.st_uid}; account UID {getattr(account, 'pw_uid', None)}")
        mode = stat.S_IMODE(metadata.st_mode)
        add("Home permissions", "ready" if mode == 0o700 else "blocked", f"mode {mode:04o}; expected 0700")
    else:
        add("Home ownership", "unknown", "home or account metadata unavailable")
        add("Home permissions", "unknown", "home metadata unavailable")
    add("Active sessions", "unknown" if evidence.sessions is None else "blocked" if evidence.sessions else "ready", "unavailable" if evidence.sessions is None else str(evidence.sessions))
    add("Running processes", "unknown" if evidence.processes == "unavailable" else "blocked" if evidence.processes != "none" else "ready", evidence.processes)
    add("Associated mounts", "unknown" if evidence.mounts == "unavailable" else "blocked" if evidence.mounts != "none" else "ready", evidence.mounts)
    add("Home contents", "unknown" if evidence.contents == "unavailable" else "ready", evidence.contents)
    add("Home usage", "unknown" if evidence.usage == "unavailable" else "ready", evidence.usage)
    add("Btrfs home type", "unknown" if evidence.subvolume in {"unavailable", "ambiguous"} else "ready", evidence.subvolume)
    registration_class = "unknown" if evidence.registration == "unavailable" else "not applicable" if evidence.registration == "absent" else "ready"
    add("APX registration", registration_class, evidence.registration)
    states = {check.classification for check in checks}
    overall = "blocked" if "blocked" in states else "incomplete because evidence is unavailable" if "unknown" in states else "ready for a separately approved removal operation"
    loss = (f"Linux account identity {evidence.account_name}", f"Canonical home data at {evidence.canonical_home} ({evidence.contents}; {evidence.usage})", "APX-owned metadata, if present")
    archive = ("Archive any home data that must be retained.", "Record account UID/GID, home metadata, Btrfs identity, and APX registration before removal.")
    return RemovalReport(evidence.logical_name, evidence.account_name, evidence.canonical_home, tuple(checks), loss, archive, REMOVAL_PLAN, overall)


def render_removal_report(report: RemovalReport) -> str:
    lines = ["APX Environment removal plan", "Mode: non-executing", f"Environment: {report.logical_name} ({report.account_name}, {report.home})", "", "Preconditions:"]
    lines.extend(f"- {check.name}: {check.classification} — {check.evidence}" for check in report.checks)
    if report.plan:
        lines.extend(("", "What would be lost:"))
        lines.extend(f"- {item}" for item in report.loss)
        lines.extend(("", "Archive or record first:"))
        lines.extend(f"- {item}" for item in report.archive)
        lines.extend(("", "Ordered plan (not executed):"))
        lines.extend(f"{index}. {step}" for index, step in enumerate(report.plan, 1))
        lines.extend(("", "Rollback limitation: account identity, metadata, and unarchived home removal cannot be assumed reversible."))
    lines.extend(("", f"Overall result: {report.overall}"))
    return "\n".join(lines)
