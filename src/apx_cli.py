#!/usr/bin/env python3
"""Read-only APX Environment candidate inspection prototype."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import os
import pwd
import stat
import sys
from typing import Callable, Iterable, Sequence, TextIO


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


def render_inspect(candidate: Candidate) -> str:
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
    return "\n".join(lines)


def run(
    argv: Sequence[str] | None = None,
    *,
    accounts_provider: Callable[[], Iterable[object]] = pwd.getpwall,
    stat_func: Callable[[str], os.stat_result] = os.stat,
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

    if args.environment_command == "list":
        print(render_list(candidates), file=stdout)
        return 0

    candidate = next(
        (candidate for candidate in candidates if candidate.name == args.name), None
    )
    if candidate is None:
        print(f"Unknown Environment candidate: {args.name}", file=stderr)
        return 2
    print(render_inspect(candidate), file=stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
