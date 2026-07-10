"""Bounded read-only observation of APX Environment registrations."""

from __future__ import annotations

from dataclasses import dataclass
import errno
from enum import Enum
import grp
import os
from pathlib import Path
import pwd
import stat
from typing import Callable

from apx_environment import (
    ContractError,
    EnvironmentRegistration,
    REGISTRATION_ROOT,
    RegistrationConflictError,
    UnsupportedRegistrationError,
    derive_identity,
    parse_registration_json,
)


DEFAULT_REGISTRATION_DIRECTORY = Path(REGISTRATION_ROOT)
MAX_REGISTRATION_BYTES = 64 * 1024
MAX_REGISTRATION_ENTRIES = 1024
REQUIRED_OPEN_FLAG_NAMES = ("O_NOFOLLOW", "O_DIRECTORY", "O_CLOEXEC")


class RegistrationObservationState(str, Enum):
    ABSENT = "absent"
    VALID = "valid"
    MALFORMED = "malformed"
    UNSUPPORTED = "unsupported"
    CONFLICTING = "conflicting"
    UNAVAILABLE = "unavailable"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class FileMetadata:
    uid: int
    gid: int
    owner_name: str | None
    group_name: str | None
    mode: int


@dataclass(frozen=True)
class RegistrationObservation:
    expected_path: str
    state: RegistrationObservationState
    registration: EnvironmentRegistration | None = None
    reason: str | None = None
    metadata: FileMetadata | None = None


@dataclass(frozen=True)
class UUIDUniquenessObservation:
    state: str
    duplicate_logical_names: tuple[str, ...] = ()
    reason: str | None = None


def expected_registration_path(
    logical_name: str,
    registration_directory: str | os.PathLike[str] = DEFAULT_REGISTRATION_DIRECTORY,
) -> Path:
    identity = derive_identity(logical_name)
    return Path(registration_directory) / f"{identity.logical_name}.json"


def _observation(
    path: Path, state: RegistrationObservationState, reason: str
) -> RegistrationObservation:
    return RegistrationObservation(str(path), state, reason=reason)


def _read_bounded(file_fd: int) -> bytes:
    chunks: list[bytes] = []
    remaining = MAX_REGISTRATION_BYTES + 1
    while remaining:
        chunk = os.read(file_fd, remaining)
        if not chunk:
            break
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def _safe_open_flags_supported() -> bool:
    return all(hasattr(os, name) for name in REQUIRED_OPEN_FLAG_NAMES)


def _observe_registration_at(
    logical_name: str,
    directory: Path,
    directory_fd: int,
    uid_resolver: Callable[[int], object] = pwd.getpwuid,
    gid_resolver: Callable[[int], object] = grp.getgrgid,
) -> RegistrationObservation:
    path = expected_registration_path(logical_name, directory)
    filename = path.name
    file_fd: int | None = None
    try:
        metadata = os.stat(filename, dir_fd=directory_fd, follow_symlinks=False)
        if stat.S_ISLNK(metadata.st_mode):
            return _observation(path, RegistrationObservationState.UNAVAILABLE, "registration file is a symbolic link")
        if not stat.S_ISREG(metadata.st_mode):
            return _observation(path, RegistrationObservationState.UNAVAILABLE, "registration path is not a regular file")
        if metadata.st_size > MAX_REGISTRATION_BYTES:
            return _observation(path, RegistrationObservationState.MALFORMED, "registration exceeds the maximum size")
        file_fd = os.open(
            filename, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC,
            dir_fd=directory_fd,
        )
        current = os.fstat(file_fd)
        if not stat.S_ISREG(current.st_mode):
            return _observation(path, RegistrationObservationState.UNAVAILABLE, "registration path is not a regular file")
        try:
            owner_name = uid_resolver(current.st_uid).pw_name
        except (KeyError, OSError, AttributeError):
            owner_name = None
        try:
            group_name = gid_resolver(current.st_gid).gr_name
        except (KeyError, OSError, AttributeError):
            group_name = None
        metadata_value = FileMetadata(
            current.st_uid, current.st_gid, owner_name, group_name,
            stat.S_IMODE(current.st_mode),
        )
        content = _read_bounded(file_fd)
        if len(content) > MAX_REGISTRATION_BYTES:
            return _observation(path, RegistrationObservationState.MALFORMED, "registration exceeds the maximum size")
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            return _observation(path, RegistrationObservationState.MALFORMED, "registration is not valid UTF-8")
        try:
            registration = parse_registration_json(text)
        except UnsupportedRegistrationError:
            return _observation(path, RegistrationObservationState.UNSUPPORTED, "registration schema version is unsupported")
        except RegistrationConflictError:
            return _observation(path, RegistrationObservationState.CONFLICTING, "registration conflicts with canonical identity")
        except (ContractError, ValueError):
            return _observation(path, RegistrationObservationState.MALFORMED, "registration JSON does not match schema version 1")
        if registration.logical_name != derive_identity(logical_name).logical_name:
            return _observation(path, RegistrationObservationState.CONFLICTING, "registration conflicts with canonical identity")
        return RegistrationObservation(
            str(path), RegistrationObservationState.VALID, registration,
            metadata=metadata_value,
        )
    except FileNotFoundError:
        return _observation(path, RegistrationObservationState.ABSENT, "registration file is absent")
    except OSError as error:
        reason = (
            "registration path contains a symbolic link"
            if error.errno == errno.ELOOP
            else "registration could not be read in the current context"
        )
        return _observation(path, RegistrationObservationState.UNAVAILABLE, reason)
    finally:
        if file_fd is not None:
            os.close(file_fd)


def observe_registration(
    logical_name: str,
    registration_directory: str | os.PathLike[str] = DEFAULT_REGISTRATION_DIRECTORY,
    uid_resolver: Callable[[int], object] = pwd.getpwuid,
    gid_resolver: Callable[[int], object] = grp.getgrgid,
) -> RegistrationObservation:
    """Read exactly one canonical registration without following symlinks."""
    path = expected_registration_path(logical_name, registration_directory)
    directory = Path(registration_directory)
    directory_fd: int | None = None
    if not _safe_open_flags_supported():
        return _observation(path, RegistrationObservationState.UNAVAILABLE, "required safe read-only file flags are unavailable")
    try:
        directory_metadata = os.lstat(directory)
        if stat.S_ISLNK(directory_metadata.st_mode):
            return _observation(path, RegistrationObservationState.UNAVAILABLE, "registration directory is a symbolic link")
        if not stat.S_ISDIR(directory_metadata.st_mode):
            return _observation(path, RegistrationObservationState.UNAVAILABLE, "registration directory is not a directory")
        directory_fd = os.open(
            directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
        )
        return _observe_registration_at(
            logical_name, directory, directory_fd, uid_resolver, gid_resolver
        )
    except FileNotFoundError:
        return _observation(path, RegistrationObservationState.ABSENT, "registration directory is absent")
    except OSError:
        return _observation(path, RegistrationObservationState.UNAVAILABLE, "registration could not be read in the current context")
    finally:
        if directory_fd is not None:
            os.close(directory_fd)


def observe_uuid_uniqueness(
    registration: EnvironmentRegistration,
    registration_directory: str | os.PathLike[str] = DEFAULT_REGISTRATION_DIRECTORY,
) -> UUIDUniquenessObservation:
    """Compare one UUID with other bounded canonical valid registrations."""
    directory = Path(registration_directory)
    directory_fd: int | None = None
    if not _safe_open_flags_supported():
        return UUIDUniquenessObservation("unavailable", reason="safe directory access unavailable")
    try:
        metadata = os.lstat(directory)
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            return UUIDUniquenessObservation("unavailable", reason="registration directory unavailable")
        directory_fd = os.open(
            directory,
            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
        )
        entries: list[str] = []
        with os.scandir(directory_fd) as iterator:
            for entry in iterator:
                entries.append(entry.name)
                if len(entries) > MAX_REGISTRATION_ENTRIES:
                    return UUIDUniquenessObservation(
                        "unavailable", reason="registration scan limit exceeded"
                    )
        duplicates: list[str] = []
        uncertain = False
        for filename in sorted(entries):
            if not filename.endswith(".json"):
                continue
            logical_name = filename[:-5]
            try:
                identity = derive_identity(logical_name)
            except ValueError:
                continue
            if filename != f"{identity.logical_name}.json" or logical_name == registration.logical_name:
                continue
            observed = _observe_registration_at(
                logical_name, directory, directory_fd
            )
            if observed.state is RegistrationObservationState.VALID:
                if observed.registration.storage.subvolume_uuid == registration.storage.subvolume_uuid:
                    duplicates.append(logical_name)
            elif observed.state in {
                RegistrationObservationState.ABSENT,
                RegistrationObservationState.UNAVAILABLE,
                RegistrationObservationState.UNSUPPORTED,
            }:
                uncertain = True
        if duplicates:
            return UUIDUniquenessObservation("not-satisfied", tuple(duplicates))
        if uncertain:
            return UUIDUniquenessObservation("unavailable", reason="one or more registrations unavailable")
        with os.scandir(directory_fd) as iterator:
            final_entries = sorted(entry.name for entry in iterator)
        if final_entries != sorted(entries):
            return UUIDUniquenessObservation(
                "unavailable", reason="registration directory changed during scan"
            )
        return UUIDUniquenessObservation("confirmed")
    except OSError:
        return UUIDUniquenessObservation("unavailable", reason="registration directory unavailable")
    finally:
        if directory_fd is not None:
            os.close(directory_fd)
