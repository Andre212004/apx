#!/usr/bin/env python3
"""Read-only APX Environment candidate inspection prototype."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
import pwd
import re
import stat
import subprocess
import sys
from typing import Callable, Iterable, Sequence, TextIO


FINDMNT_TIMEOUT = 3.0
BTRFS_TIMEOUT = 5.0
LOGINCTL_TIMEOUT = 3.0
COMMAND_OUTPUT_LIMIT = 8192
SESSION_LIMIT = 100
SESSION_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}")


@dataclass(frozen=True)
class Candidate:
    name: str
    uid: int
    home: str
    role: str
    home_exists: bool | None
    home_is_directory: bool | None
    home_owner_uid: int | None
    ownership_matches: bool | None
    state: str
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class CommandResult:
    returncode: int | None
    stdout: str
    stderr: str
    failure: str | None = None


@dataclass(frozen=True)
class MountObservation:
    status: str
    filesystem_type: str | None
    target: str | None
    source: str | None
    options: str | None
    read_only: bool | None
    explanation: str


@dataclass(frozen=True)
class BtrfsObservation:
    filesystem: str
    subvolume: str
    explanation: str


@dataclass(frozen=True)
class SessionObservation:
    session_id: str
    username: str
    state: str
    active: str
    session_type: str
    session_class: str
    seat: str
    remote: str
    graphical: str
    status: str


@dataclass(frozen=True)
class SessionListObservation:
    sessions: tuple[SessionObservation, ...]
    status: str
    explanation: str | None
    truncated: bool


CommandRunner = Callable[[Sequence[str], float], CommandResult]


def sanitize_diagnostic(value: str) -> str:
    cleaned = "".join(
        character if character.isprintable() else " " for character in value
    )
    return " ".join(cleaned.split())[:COMMAND_OUTPUT_LIMIT]


def run_command(arguments: Sequence[str], timeout: float) -> CommandResult:
    if isinstance(arguments, (str, bytes)):
        raise TypeError("command arguments must be a sequence of strings")
    command = tuple(arguments)
    if not command or not all(isinstance(argument, str) for argument in command):
        raise TypeError("command arguments must be a non-empty sequence of strings")
    environment = os.environ.copy()
    environment["LC_ALL"] = "C"
    try:
        completed = subprocess.run(
            command,
            shell=False,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=environment,
        )
    except FileNotFoundError:
        return CommandResult(None, "", "", "missing executable")
    except subprocess.TimeoutExpired as error:
        return CommandResult(
            None,
            str(error.stdout or "")[:COMMAND_OUTPUT_LIMIT],
            str(error.stderr or "")[:COMMAND_OUTPUT_LIMIT],
            "timeout",
        )
    except OSError as error:
        return CommandResult(None, "", "", f"execution error: {error}")
    return CommandResult(
        completed.returncode,
        completed.stdout[:COMMAND_OUTPUT_LIMIT],
        completed.stderr[:COMMAND_OUTPUT_LIMIT],
    )


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="apx")
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("status", help="summarize read-only APX observations")

    environment = commands.add_parser(
        "environment", help="inspect candidate APX Environment accounts"
    )
    environment_commands = environment.add_subparsers(
        dest="environment_command", required=True
    )
    environment_commands.add_parser("list", help="list candidate accounts")
    inspect_parser = environment_commands.add_parser(
        "inspect", help="inspect one candidate account"
    )
    inspect_parser.add_argument("name", help="exact candidate account name")

    session = commands.add_parser("session", help="inspect read-only APX sessions")
    session_commands = session.add_subparsers(
        dest="session_command", required=True
    )
    session_commands.add_parser("list", help="list observable APX sessions")
    return parser


def candidate_role(name: str) -> str:
    if name == "apx-hub":
        return "hub"
    if name == "apx-development":
        return "development"
    return "candidate"


def candidate_sort_key(candidate: Candidate) -> tuple[int, str]:
    priority = {"apx-hub": 0, "apx-development": 1}
    return (priority.get(candidate.name, 2), candidate.name)


def observe_account(account: object, stat_func: Callable[[str], os.stat_result]) -> Candidate:
    name = account.pw_name
    uid = account.pw_uid
    home = account.pw_dir
    warnings: list[str] = []

    try:
        home_stat = stat_func(home)
    except FileNotFoundError:
        home_exists = False
        home_is_directory = None
        home_owner_uid = None
        ownership_matches = None
        state = "inconsistent"
        warnings.append("Home path does not exist.")
    except OSError as error:
        home_exists = None
        home_is_directory = None
        home_owner_uid = None
        ownership_matches = None
        state = "unavailable"
        warnings.append(f"Home path could not be observed: {error}.")
    else:
        home_exists = True
        home_is_directory = stat.S_ISDIR(home_stat.st_mode)
        home_owner_uid = home_stat.st_uid
        ownership_matches = home_owner_uid == uid

        if not home_is_directory:
            warnings.append("Home path is not a directory.")
        if not ownership_matches:
            warnings.append(
                f"Home ownership UID {home_owner_uid} does not match account UID {uid}."
            )
        state = "consistent" if not warnings else "inconsistent"

    return Candidate(
        name=name,
        uid=uid,
        home=home,
        role=candidate_role(name),
        home_exists=home_exists,
        home_is_directory=home_is_directory,
        home_owner_uid=home_owner_uid,
        ownership_matches=ownership_matches,
        state=state,
        warnings=tuple(warnings),
    )


def discover_candidates(
    accounts: Iterable[object], stat_func: Callable[[str], os.stat_result] = os.stat
) -> list[Candidate]:
    candidates = [
        observe_account(account, stat_func)
        for account in accounts
        if account.pw_name.startswith("apx-")
    ]
    return sorted(candidates, key=candidate_sort_key)


def observation(value: object) -> str:
    if value is None:
        return "unavailable"
    if isinstance(value, bool):
        return "yes" if value else "no"
    return str(value)


def unavailable_mount(explanation: str) -> MountObservation:
    return MountObservation(
        "unavailable", None, None, None, None, None, explanation
    )


def observe_mount(home: str, command_runner: CommandRunner) -> MountObservation:
    result = command_runner(("findmnt", "--json", "--target", home), FINDMNT_TIMEOUT)
    if result.failure:
        return unavailable_mount(f"findmnt {result.failure}.")
    if result.returncode != 0:
        diagnostic = sanitize_diagnostic(result.stderr or result.stdout)
        detail = f": {diagnostic}" if diagnostic else ""
        return unavailable_mount(f"findmnt failed with exit code {result.returncode}{detail}.")

    try:
        document = json.loads(result.stdout)
    except (json.JSONDecodeError, TypeError):
        return unavailable_mount("findmnt returned malformed JSON.")
    if not isinstance(document, dict) or set(document) != {"filesystems"}:
        return unavailable_mount("findmnt returned an unexpected JSON schema.")
    filesystems = document["filesystems"]
    if not isinstance(filesystems, list):
        return unavailable_mount("findmnt returned an unexpected JSON schema.")
    if not filesystems:
        return unavailable_mount("findmnt returned no filesystem for the home path.")
    if len(filesystems) != 1:
        return MountObservation(
            "ambiguous",
            None,
            None,
            None,
            None,
            None,
            "findmnt returned multiple filesystems for the home path.",
        )

    filesystem = filesystems[0]
    required = ("fstype", "target", "source", "options")
    if not isinstance(filesystem, dict) or any(
        not isinstance(filesystem.get(field), str) or not filesystem[field]
        for field in required
    ):
        return unavailable_mount("findmnt returned an unexpected JSON schema.")

    options = filesystem["options"]
    option_tokens = set(options.split(","))
    has_ro = "ro" in option_tokens
    has_rw = "rw" in option_tokens
    if has_ro == has_rw:
        mount_status = "ambiguous"
        read_only = None
        explanation = (
            "Mount options do not contain one unambiguous ro or rw token; "
            "values are observations from the current execution context."
        )
    else:
        mount_status = "confirmed"
        read_only = has_ro
        explanation = "Observed in the current execution context; host state is not implied."
    return MountObservation(
        mount_status,
        filesystem["fstype"],
        filesystem["target"],
        filesystem["source"],
        options,
        read_only,
        explanation,
    )


def result_diagnostic(result: CommandResult) -> str:
    return sanitize_diagnostic(result.stderr or result.stdout)


def observe_btrfs(
    home: str, mount: MountObservation, command_runner: CommandRunner
) -> BtrfsObservation:
    if mount.filesystem_type is None:
        return BtrfsObservation(
            "unavailable",
            "unavailable",
            "The containing filesystem could not be established.",
        )
    if mount.filesystem_type.lower() != "btrfs":
        return BtrfsObservation(
            "no",
            "not applicable",
            "The containing filesystem was confirmed as non-Btrfs in the current execution context.",
        )

    result = command_runner(
        ("btrfs", "subvolume", "show", home), BTRFS_TIMEOUT
    )
    if result.failure:
        return BtrfsObservation(
            "yes", "unavailable", f"btrfs inspection {result.failure}."
        )
    diagnostic = result_diagnostic(result)
    if result.returncode == 0:
        if not result.stdout.strip() or not re.search(
            r"(?m)^\s*[^:\n]+:\s*\S", result.stdout
        ):
            return BtrfsObservation(
                "yes",
                "ambiguous",
                "btrfs returned successful but malformed output.",
            )
        return BtrfsObservation(
            "yes",
            "yes",
            "Confirmed by btrfs subvolume show in the current execution context.",
        )

    if diagnostic == "ERROR: Not a Btrfs subvolume: Invalid argument":
        return BtrfsObservation(
            "yes",
            "no",
            "btrfs explicitly reported that the path is not a subvolume.",
        )
    lowered = diagnostic.lower()
    if "permission denied" in lowered or "operation not permitted" in lowered:
        reason = "Permission denied while inspecting the path"
    elif "no such file or directory" in lowered or "cannot access" in lowered:
        reason = "The path was inaccessible"
    else:
        reason = f"Unexpected btrfs failure with exit code {result.returncode}"
    detail = f": {diagnostic}" if diagnostic else ""
    return BtrfsObservation("yes", "unavailable", f"{reason}{detail}.")


def session_sort_key(session_id: str) -> tuple[int, int | str]:
    if session_id.isdigit():
        return (0, int(session_id))
    return (1, session_id)


def candidate_names_for_identity(
    uid_text: str | None,
    username: str | None,
    candidates_by_uid: dict[int, Candidate],
    candidates_by_name: dict[str, Candidate],
) -> set[str]:
    names: set[str] = set()
    if uid_text is not None and uid_text.isdigit():
        candidate = candidates_by_uid.get(int(uid_text))
        if candidate:
            names.add(candidate.name)
    if username in candidates_by_name:
        names.add(username)
    return names


def unavailable_session(
    session_id: str, username: str, status: str = "unavailable"
) -> SessionObservation:
    return SessionObservation(
        session_id,
        username,
        "unavailable",
        "unavailable",
        "unavailable",
        "unavailable",
        "unavailable",
        "unavailable",
        "unavailable",
        status,
    )


def observe_sessions(
    candidates: Sequence[Candidate], command_runner: CommandRunner
) -> SessionListObservation:
    list_arguments = (
        "loginctl",
        "list-sessions",
        "--no-legend",
        "--no-pager",
    )
    result = command_runner(list_arguments, LOGINCTL_TIMEOUT)
    if result.failure:
        return SessionListObservation(
            (), "unavailable", f"loginctl session enumeration {result.failure}.", False
        )
    if result.returncode != 0:
        diagnostic = result_diagnostic(result)
        detail = f": {diagnostic}" if diagnostic else ""
        return SessionListObservation(
            (),
            "unavailable",
            f"loginctl session enumeration failed with exit code "
            f"{result.returncode}{detail}.",
            False,
        )

    enumerated: list[tuple[str, str | None, str | None]] = []
    malformed_enumeration = False
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        fields = line.split()
        if len(fields) < 3 or not SESSION_ID_PATTERN.fullmatch(fields[0]):
            malformed_enumeration = True
            continue
        enumerated.append((fields[0], fields[1], fields[2]))
    enumerated.sort(key=lambda item: session_sort_key(item[0]))
    truncated = len(enumerated) > SESSION_LIMIT
    enumerated = enumerated[:SESSION_LIMIT]

    candidates_by_uid = {candidate.uid: candidate for candidate in candidates}
    candidates_by_name = {candidate.name: candidate for candidate in candidates}
    sessions: list[SessionObservation] = []
    properties = (
        "Id",
        "Name",
        "User",
        "State",
        "Active",
        "Type",
        "Class",
        "Seat",
        "Remote",
        "Service",
    )
    for session_id, listed_uid, listed_name in enumerated:
        show_arguments = (
            "loginctl",
            "show-session",
            session_id,
            "--no-pager",
            *(f"--property={name}" for name in properties),
        )
        detail_result = command_runner(show_arguments, LOGINCTL_TIMEOUT)
        listed_candidates = candidate_names_for_identity(
            listed_uid, listed_name, candidates_by_uid, candidates_by_name
        )
        if detail_result.failure or detail_result.returncode != 0:
            if listed_candidates:
                username = (
                    next(iter(listed_candidates))
                    if len(listed_candidates) == 1
                    else "ambiguous"
                )
                sessions.append(unavailable_session(session_id, username))
            continue

        known_properties = set(properties)
        values: dict[str, set[str]] = {}
        malformed_properties = False
        for line in detail_result.stdout.splitlines():
            if not line:
                continue
            if "=" not in line:
                malformed_properties = True
                continue
            key, value = line.split("=", 1)
            if key in known_properties:
                values.setdefault(key, set()).add(value)

        def single_value(key: str) -> str | None:
            observed = values.get(key, set())
            if len(observed) == 1:
                value = next(iter(observed))
                return value or None
            return None

        detailed_uid = single_value("User")
        detailed_name = single_value("Name")
        detailed_session_id = single_value("Id")
        detailed_candidates = candidate_names_for_identity(
            detailed_uid, detailed_name, candidates_by_uid, candidates_by_name
        )
        possible_candidates = listed_candidates | detailed_candidates
        if not possible_candidates:
            continue

        conflicting_properties = any(len(observed) > 1 for observed in values.values())
        identity_conflict = (
            len(possible_candidates) > 1
            or (
                listed_uid is not None
                and detailed_uid is not None
                and listed_uid != detailed_uid
            )
            or (
                listed_name is not None
                and detailed_name is not None
                and listed_name != detailed_name
            )
            or (
                detailed_session_id is not None
                and detailed_session_id != session_id
            )
        )
        ambiguous = malformed_properties or conflicting_properties or identity_conflict
        username = (
            next(iter(possible_candidates))
            if len(possible_candidates) == 1
            else "ambiguous"
        )

        def rendered_property(key: str) -> str:
            if len(values.get(key, set())) > 1:
                return "ambiguous"
            return single_value(key) or "unavailable"

        state = rendered_property("State")
        active = rendered_property("Active")
        session_type = rendered_property("Type")
        session_class = rendered_property("Class")
        seat = rendered_property("Seat")
        remote = rendered_property("Remote")
        if session_type == "ambiguous":
            graphical = "ambiguous"
        elif session_type == "unavailable":
            graphical = "unavailable"
        elif session_type in {"wayland", "x11"}:
            graphical = "yes"
        else:
            graphical = "no"
        required_values = (state, active, session_type, session_class, seat, remote)
        if ambiguous:
            status = "ambiguous"
        elif "unavailable" in required_values:
            status = "unavailable"
        else:
            status = "confirmed"
        sessions.append(
            SessionObservation(
                session_id,
                username,
                state,
                active,
                session_type,
                session_class,
                seat,
                remote,
                graphical,
                status,
            )
        )

    sessions.sort(key=lambda session: session_sort_key(session.session_id))
    conditions = []
    if malformed_enumeration:
        conditions.append("Malformed session enumeration rows were ignored")
    if truncated:
        conditions.append(f"Results were truncated to {SESSION_LIMIT} sessions")
    explanation = "; ".join(conditions) + "." if conditions else None
    overall_status = "ambiguous" if conditions else "confirmed"
    return SessionListObservation(tuple(sessions), overall_status, explanation, truncated)


def render_status(candidates: Sequence[Candidate]) -> str:
    consistent = sum(candidate.state == "consistent" for candidate in candidates)
    warning_count = sum(len(candidate.warnings) for candidate in candidates)
    return "\n".join(
        (
            "APX status",
            "Mode: read-only prototype",
            f"Candidate environments: {len(candidates)}",
            f"Consistent candidates: {consistent}",
            f"Warnings: {warning_count}",
        )
    )


def render_list(candidates: Sequence[Candidate]) -> str:
    headers = ("NAME", "UID", "HOME", "ROLE", "STATE")
    rows = [
        (candidate.name, str(candidate.uid), candidate.home, candidate.role, candidate.state)
        for candidate in candidates
    ]
    widths = [
        max(len(headers[index]), *(len(row[index]) for row in rows))
        if rows
        else len(headers[index])
        for index in range(len(headers))
    ]

    def format_row(row: tuple[str, ...]) -> str:
        return "  ".join(
            value.ljust(widths[index]) for index, value in enumerate(row)
        ).rstrip()

    return "\n".join((format_row(headers), *(format_row(row) for row in rows)))


def render_session_list(observation_result: SessionListObservation) -> str:
    if not observation_result.sessions:
        lines = [
            "APX sessions",
            f"Status: {observation_result.status}",
            "Sessions: none",
        ]
        if observation_result.explanation:
            lines.append(f"Explanation: {observation_result.explanation}")
        return "\n".join(lines)

    headers = (
        "SESSION",
        "USER",
        "STATE",
        "ACTIVE",
        "TYPE",
        "CLASS",
        "SEAT",
        "REMOTE",
        "GRAPHICAL",
        "STATUS",
    )
    rows = [
        (
            session.session_id,
            session.username,
            session.state,
            session.active,
            session.session_type,
            session.session_class,
            session.seat,
            session.remote,
            session.graphical,
            session.status,
        )
        for session in observation_result.sessions
    ]
    widths = [
        max(len(headers[index]), *(len(row[index]) for row in rows))
        for index in range(len(headers))
    ]

    def format_row(row: tuple[str, ...]) -> str:
        return "  ".join(
            value.ljust(widths[index]) for index, value in enumerate(row)
        ).rstrip()

    lines = [format_row(headers), *(format_row(row) for row in rows)]
    if observation_result.explanation:
        lines.append(f"Explanation: {observation_result.explanation}")
    return "\n".join(lines)


def render_inspect(
    candidate: Candidate,
    mount: MountObservation,
    btrfs: BtrfsObservation,
) -> str:
    lines = [
        f"Environment candidate: {candidate.name}",
        f"Role: {candidate.role}",
        f"State: {candidate.state}",
        f"Username: {candidate.name}",
        f"UID: {candidate.uid}",
        f"Home: {candidate.home}",
        f"Home exists: {observation(candidate.home_exists)}",
        f"Home is directory: {observation(candidate.home_is_directory)}",
        f"Home ownership UID: {observation(candidate.home_owner_uid)}",
        f"Ownership matches account UID: {observation(candidate.ownership_matches)}",
    ]
    if candidate.warnings:
        lines.append("Warnings:")
        lines.extend(f"- {warning}" for warning in candidate.warnings)
    else:
        lines.append("Warnings: none")
    lines.extend(
        (
            "Filesystem:",
            f"  Status: {mount.status}",
            f"  Type: {observation(mount.filesystem_type)}",
            f"  Mount target: {observation(mount.target)}",
            f"  Mount source: {observation(mount.source)}",
            f"  Mount options: {observation(mount.options)}",
            f"  Read-only: {observation(mount.read_only)}",
            f"  Explanation: {mount.explanation}",
            "Btrfs:",
            f"  Filesystem: {btrfs.filesystem}",
            f"  Subvolume: {btrfs.subvolume}",
            f"  Explanation: {btrfs.explanation}",
        )
    )
    return "\n".join(lines)


def run(
    argv: Sequence[str] | None = None,
    *,
    accounts_provider: Callable[[], Iterable[object]] = pwd.getpwall,
    stat_func: Callable[[str], os.stat_result] = os.stat,
    command_runner: CommandRunner = run_command,
    stdout: TextIO = sys.stdout,
    stderr: TextIO = sys.stderr,
) -> int:
    args = create_parser().parse_args(argv)
    try:
        candidates = discover_candidates(accounts_provider(), stat_func)
    except Exception as error:
        print(f"APX observation error: {error}", file=stderr)
        return 1

    if args.command == "status":
        print(render_status(candidates), file=stdout)
        return 0

    if args.command == "session":
        try:
            session_result = observe_sessions(candidates, command_runner)
        except Exception as error:
            print(f"APX observation error: {error}", file=stderr)
            return 1
        print(render_session_list(session_result), file=stdout)
        return 0

    if args.environment_command == "list":
        print(render_list(candidates), file=stdout)
        return 0

    candidate = next(
        (candidate for candidate in candidates if candidate.name == args.name), None
    )
    if candidate is None:
        print(f"Unknown Environment candidate: {args.name}", file=stderr)
        return 2
    try:
        mount = observe_mount(candidate.home, command_runner)
        btrfs = observe_btrfs(candidate.home, mount, command_runner)
    except Exception as error:
        print(f"APX observation error: {error}", file=stderr)
        return 1
    print(render_inspect(candidate, mount, btrfs), file=stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
