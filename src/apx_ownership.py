"""Interpret numeric ownership allocated through Linux subordinate ID ranges."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class SubordinateIdRange:
    owner: str
    start: int
    count: int


def parse_subordinate_ranges(lines: Iterable[str]) -> tuple[SubordinateIdRange, ...]:
    ranges: list[SubordinateIdRange] = []
    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        fields = line.split(":")
        if len(fields) != 3 or not fields[0] or not fields[1].isdigit() or not fields[2].isdigit():
            continue
        start, count = int(fields[1]), int(fields[2])
        if start < 1 or count < 1:
            continue
        ranges.append(SubordinateIdRange(fields[0], start, count))
    return tuple(sorted(ranges, key=lambda item: (item.start, item.owner, item.count)))


def read_subordinate_ranges(path: Path) -> tuple[SubordinateIdRange, ...]:
    try:
        with path.open("r", encoding="utf-8") as source:
            return parse_subordinate_ranges(source)
    except (OSError, UnicodeError):
        return ()


def subordinate_namespace_id(
    host_id: int, ranges: Iterable[SubordinateIdRange]
) -> tuple[str, int] | None:
    for item in ranges:
        if item.start <= host_id < item.start + item.count:
            # Rootless Podman maps namespace ID 0 to the calling user's real ID.
            # The first subordinate ID therefore represents namespace ID 1.
            return item.owner, host_id - item.start + 1
    return None


def describe_numeric_owner(
    host_id: int, ranges: Iterable[SubordinateIdRange], *, identifier: str
) -> str:
    mapped = subordinate_namespace_id(host_id, ranges)
    if mapped is None:
        return str(host_id)
    owner, namespace_id = mapped
    return (
        f"{host_id} (allocated to {owner} rootless range; "
        f"namespace {identifier} {namespace_id})"
    )
