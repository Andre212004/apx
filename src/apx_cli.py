#!/usr/bin/env python3
"""Read-only APX Environment candidate inspection prototype."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import grp
import json
import os
import pwd
import re
import shutil
import stat
import subprocess
import sys
from typing import Callable, Iterable, Sequence, TextIO
import uuid

from apx_environment import (
    CreationPreconditions,
    EnvironmentClassification,
    EnvironmentIdentity,
    INCOMPLETE_OPERATION_ROOT,
    classify_observed_environment,
    create_plan,
    derive_identity,
    render_creation_plan,
    validate_logical_name,
)
from apx_consistency import (
    ConsistencyVerification,
    observe_home_metadata,
    observe_incomplete_operation,
    verify_consistency,
)
from apx_registration import (
    DEFAULT_REGISTRATION_DIRECTORY,
    RegistrationObservation,
    RegistrationObservationState,
    observe_registration,
    observe_uuid_uniqueness,
)
from apx_host import observe_host_readiness, render_host_readiness
from apx_practical import observe_practical, render_practical


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
    subvolume_id: int | None = None
    subvolume_uuid: str | None = None
    parent_uuid: str | None = None
    parent_uuid_observed: bool = False
    identity_status: str = "unavailable"
    subvolume_id_status: str = "unavailable"
    subvolume_uuid_status: str = "unavailable"
    parent_uuid_status: str = "unavailable"


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
    vt: str = "unavailable"


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

    host = commands.add_parser("host", help="inspect host readiness")
    host_commands = host.add_subparsers(dest="host_command", required=True)
    host_commands.add_parser("check", help="check readiness for the trial experiment")
    host_commands.add_parser("validate", help="inspect practical host state for milestone 3A")

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
    create_environment = environment_commands.add_parser(
        "create", help="plan creation of an APX Environment"
    )
    create_environment.add_argument("logical_name", help="canonical logical name")
    create_environment.add_argument(
        "--dry-run",
        action="store_true",
        required=True,
        help="produce a plan without applying changes",
    )

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
        fields: dict[str, list[str]] = {}
        for line in result.stdout.splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            fields.setdefault(key.strip(), []).append(value.strip())
        subvolume_id: int | None = None
        subvolume_uuid: str | None = None
        parent_uuid: str | None = None
        parent_observed = False
        id_values = fields.get("Subvolume ID", [])
        uuid_values = fields.get("UUID", [])
        parent_values = fields.get("Parent UUID", [])
        id_status = "confirmed"
        uuid_status = "confirmed"
        parent_status = "confirmed"
        if len(id_values) == 1 and id_values[0].isdigit() and int(id_values[0]) > 0:
            subvolume_id = int(id_values[0])
        else:
            id_status = "unavailable" if not id_values else "ambiguous"
        if len(uuid_values) == 1:
            try:
                canonical = str(uuid.UUID(uuid_values[0]))
                if canonical == uuid_values[0]:
                    subvolume_uuid = canonical
                else:
                    uuid_status = "ambiguous"
            except ValueError:
                uuid_status = "ambiguous"
        else:
            uuid_status = "unavailable" if not uuid_values else "ambiguous"
        if len(parent_values) == 1:
            if parent_values[0] in {"-", "none", "None"}:
                parent_uuid = None
                parent_observed = True
            else:
                try:
                    canonical_parent = str(uuid.UUID(parent_values[0]))
                    if canonical_parent == parent_values[0]:
                        parent_uuid = canonical_parent
                        parent_observed = True
                    else:
                        parent_status = "ambiguous"
                except ValueError:
                    parent_status = "ambiguous"
        else:
            parent_status = "unavailable" if not parent_values else "ambiguous"
        statuses = {id_status, uuid_status, parent_status}
        identity_status = (
            "ambiguous" if "ambiguous" in statuses
            else "unavailable" if "unavailable" in statuses
            else "confirmed"
        )
        return BtrfsObservation(
            "yes", "yes",
            "Confirmed by btrfs subvolume show in the current execution context.",
            subvolume_id, subvolume_uuid, parent_uuid, parent_observed,
            identity_status, id_status, uuid_status, parent_status,
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
        "VTNr",
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
        vt = rendered_property("VTNr")
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
                vt,
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


def observe_creation_preconditions(
    identity: EnvironmentIdentity,
    accounts: Sequence[object],
    candidates: Sequence[Candidate],
    stat_func: Callable[[str], os.stat_result],
    command_runner: CommandRunner,
) -> CreationPreconditions:
    account_exists = any(
        account.pw_name == identity.account for account in accounts
    )
    candidate_exists = any(
        candidate.name == identity.account for candidate in candidates
    )
    try:
        stat_func(identity.home)
    except FileNotFoundError:
        home_absent = "confirmed"
    except OSError:
        home_absent = "unavailable"
    else:
        home_absent = "not-satisfied"

    mount = observe_mount("/home", command_runner)
    if mount.status == "confirmed" and mount.filesystem_type == "btrfs":
        btrfs_context = "confirmed"
    elif mount.status == "confirmed":
        btrfs_context = "not-satisfied"
    else:
        btrfs_context = mount.status
    return CreationPreconditions(
        account_absent="not-satisfied" if account_exists else "confirmed",
        home_absent=home_absent,
        candidate_absent="not-satisfied" if candidate_exists else "confirmed",
        filesystem_type=mount.filesystem_type or "unavailable",
        filesystem_status=mount.status,
        host_confirmation_required=True,
        btrfs_context=btrfs_context,
    )


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
    registration: RegistrationObservation,
    classification: EnvironmentClassification,
    consistency: ConsistencyVerification | None = None,
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
            "Registration:",
            f"  Expected path: {registration.expected_path}",
            f"  Observation: {registration.state}",
        )
    )
    if registration.registration is not None:
        lines.extend(
            (
                f"  Schema version: {registration.registration.schema_version}",
                f"  Logical name: {registration.registration.logical_name}",
                f"  Lifecycle state: {registration.registration.lifecycle_state}",
            )
        )
    elif registration.reason:
        lines.append(f"  Reason: {registration.reason}")
    lines.append("Consistency:")
    if consistency is None:
        lines.append("  Verification: unavailable (valid registration required)")
    else:
        post = consistency.postconditions
        lines.extend(
            (
                f"  Registration ownership: {post.registration_host_owned}",
                f"  Registration mode: {post.registration_mode_matches}",
                f"  Home ownership: {post.ownership_matches}",
                f"  Home group: {post.group_matches}",
                f"  Home mode: {post.mode_matches}",
                f"  Home writable in current context: {consistency.home.writable}",
                f"  Home filesystem Btrfs: {post.home_filesystem_btrfs}",
                f"  Dedicated Btrfs subvolume: {post.dedicated_btrfs_subvolume}",
                f"  Subvolume ID match: {post.subvolume_id_matches}",
                f"  Subvolume UUID match: {post.subvolume_uuid_matches}",
                f"  Parent UUID match: {post.parent_uuid_matches}",
                f"  UUID uniqueness: {post.uuid_unique}",
                f"  Incomplete operation absent: {post.incomplete_marker_absent}",
            )
        )
        if post.mode_matches == "not-satisfied" and consistency.home.mode is not None:
            lines.extend(("    Expected: 0700", f"    Observed: {consistency.home.mode:04o}"))
        if post.ownership_matches == "not-satisfied" and consistency.home.uid is not None:
            lines.extend((f"    Expected owner UID: {candidate.uid}", f"    Observed owner UID: {consistency.home.uid}"))
        if post.group_matches == "not-satisfied" and consistency.home.gid is not None:
            lines.append(f"    Observed home GID: {consistency.home.gid}")
        if post.registration_mode_matches == "not-satisfied" and consistency.registration_metadata is not None:
            lines.extend(("    Registration expected: 0644", f"    Registration observed: {consistency.registration_metadata.mode:04o}"))
        if consistency.registration_metadata is not None:
            if post.registration_owner_matches == "not-satisfied":
                lines.extend(("    Registration expected owner UID: 0", f"    Registration observed owner UID: {consistency.registration_metadata.uid}"))
            if post.registration_group_matches == "not-satisfied":
                lines.extend(("    Registration expected group GID: 0", f"    Registration observed group GID: {consistency.registration_metadata.gid}"))
        storage = registration.registration.storage if registration.registration else None
        if storage is not None and post.subvolume_id_matches == "not-satisfied":
            lines.extend((f"    Expected subvolume ID: {storage.subvolume_id}", f"    Observed subvolume ID: {btrfs.subvolume_id}"))
        if storage is not None and post.subvolume_uuid_matches == "not-satisfied":
            lines.extend((f"    Expected subvolume UUID: {storage.subvolume_uuid}", f"    Observed subvolume UUID: {btrfs.subvolume_uuid}"))
        if storage is not None and post.parent_uuid_matches == "not-satisfied":
            lines.extend((f"    Expected parent UUID: {storage.parent_uuid}", f"    Observed parent UUID: {btrfs.parent_uuid}"))
    lines.append(
        f"Formal classification: {render_environment_classification(classification)}"
    )
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


def render_environment_classification(
    classification: EnvironmentClassification,
) -> str:
    if classification is EnvironmentClassification.UNCONFIRMED:
        return "unconfirmed"
    return classification.value


def run(
    argv: Sequence[str] | None = None,
    *,
    accounts_provider: Callable[[], Iterable[object]] = pwd.getpwall,
    stat_func: Callable[[str], os.stat_result] = os.stat,
    command_runner: CommandRunner = run_command,
    registration_directory: str | os.PathLike[str] = DEFAULT_REGISTRATION_DIRECTORY,
    incomplete_operation_directory: str | os.PathLike[str] = INCOMPLETE_OPERATION_ROOT,
    lstat_func: Callable[[str], os.stat_result] = os.lstat,
    access_func: Callable[..., bool] = os.access,
    uid_resolver: Callable[[int], object] = pwd.getpwuid,
    gid_resolver: Callable[[int], object] = grp.getgrgid,
    which_func: Callable[[str], str | None] = shutil.which,
    scandir_func: Callable[..., object] = os.scandir,
    readlink_func: Callable[[str | os.PathLike[str]], str] = os.readlink,
    host_authoritative: bool = False,
    stdout: TextIO = sys.stdout,
    stderr: TextIO = sys.stderr,
) -> int:
    args = create_parser().parse_args(argv)
    if (
        args.command == "environment"
        and args.environment_command == "create"
    ):
        name_error = validate_logical_name(args.logical_name)
        if name_error:
            print(
                f"Invalid Environment logical name '{args.logical_name}': {name_error}.",
                file=stderr,
            )
            return 2
    try:
        accounts = list(accounts_provider())
        candidates = discover_candidates(accounts, stat_func)
    except Exception as error:
        print(f"APX observation error: {error}", file=stderr)
        return 1

    if args.command == "status":
        print(render_status(candidates), file=stdout)
        return 0

    if args.command == "host":
        try:
            if args.host_command == "validate":
                current_sessions = observe_sessions(candidates, command_runner)
                report = observe_practical(
                    accounts=accounts, sessions=current_sessions,
                    mount_observer=lambda path: observe_mount(path, command_runner),
                    btrfs_observer=lambda path, mount: observe_btrfs(path, mount, command_runner),
                    command_runner=command_runner, lstat_func=lstat_func,
                    scandir_func=scandir_func, which_func=which_func,
                    readlink_func=readlink_func,
                )
                print(render_practical(report), file=stdout)
                return 0
            trial_registration = observe_registration(
                "trial", registration_directory, uid_resolver, gid_resolver
            )
            trial_marker = observe_incomplete_operation(
                "trial", incomplete_operation_directory, lstat_func=lstat_func
            )
            home_mount = observe_mount("/home", command_runner)
            current_sessions = observe_sessions(candidates, command_runner)
            report = observe_host_readiness(
                accounts=accounts,
                mount=home_mount,
                registration=trial_registration,
                incomplete_operation=trial_marker,
                sessions=current_sessions,
                lstat_func=lstat_func,
                command_runner=command_runner,
                which_func=which_func,
                scandir_func=scandir_func,
                readlink_func=readlink_func,
                authoritative_host=host_authoritative,
            )
        except Exception as error:
            print(f"APX observation error: {error}", file=stderr)
            return 1
        print(render_host_readiness(report), file=stdout)
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

    if args.environment_command == "create":
        try:
            identity = derive_identity(args.logical_name)
            preconditions = observe_creation_preconditions(
                identity, accounts, candidates, stat_func, command_runner
            )
            plan = create_plan(identity, preconditions)
        except Exception as error:
            print(f"APX observation error: {error}", file=stderr)
            return 1
        print(render_creation_plan(plan), file=stdout)
        return 0

    candidate = next(
        (candidate for candidate in candidates if candidate.name == args.name), None
    )
    if candidate is None:
        print(f"Unknown Environment candidate: {args.name}", file=stderr)
        return 2
    logical_name = candidate.name.removeprefix("apx-")
    try:
        identity = derive_identity(logical_name)
        if identity.account != candidate.name:
            raise ValueError("candidate account is not canonical")
        registration = observe_registration(
            logical_name, registration_directory, uid_resolver, gid_resolver
        )
    except ValueError:
        registration = RegistrationObservation(
            str(registration_directory),
            RegistrationObservationState.CONFLICTING,
            reason="candidate account does not map to a canonical APX identity",
        )
    try:
        mount = observe_mount(candidate.home, command_runner)
        btrfs = observe_btrfs(candidate.home, mount, command_runner)
    except Exception as error:
        print(f"APX observation error: {error}", file=stderr)
        return 1
    consistency = None
    if registration.state is RegistrationObservationState.VALID:
        account = next((item for item in accounts if item.pw_name == candidate.name), None)
        home = observe_home_metadata(
            candidate.home, lstat_func=lstat_func, access_func=access_func,
            uid_resolver=uid_resolver, gid_resolver=gid_resolver,
        )
        uniqueness = observe_uuid_uniqueness(
            registration.registration, registration_directory
        )
        incomplete = observe_incomplete_operation(
            logical_name, incomplete_operation_directory, lstat_func=lstat_func
        )
        consistency = verify_consistency(
            identity=identity,
            registration_observation=registration,
            account=account,
            home=home,
            filesystem_type=mount.filesystem_type,
            filesystem_status=mount.status,
            btrfs=btrfs,
            uuid_uniqueness=uniqueness,
            incomplete_operation=incomplete,
        )
        classification = consistency.classification
    else:
        classification = classify_observed_environment(
            registration_state=registration.state,
            candidate_present=True,
            incomplete_operation=False,
            host_observations="unavailable",
            confirmed_mismatch=candidate.state == "inconsistent",
        )
    print(
        render_inspect(
            candidate, mount, btrfs, registration, classification, consistency
        ),
        file=stdout,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
