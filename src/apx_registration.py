"""Bounded read-only observation of APX Environment registrations."""

from __future__ import annotations

from dataclasses import dataclass
import errno
from enum import Enum
import os
from pathlib import Path
import stat

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
class RegistrationObservation:
    expected_path: str
    state: RegistrationObservationState
    registration: EnvironmentRegistration | None = None
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


def observe_registration(
    logical_name: str,
    registration_directory: str | os.PathLike[str] = DEFAULT_REGISTRATION_DIRECTORY,
) -> RegistrationObservation:
    """Read exactly one canonical registration without following symlinks."""
    path = expected_registration_path(logical_name, registration_directory)
    directory = Path(registration_directory)
    directory_fd: int | None = None
    file_fd: int | None = None
    if not _safe_open_flags_supported():
        return _observation(
            path,
            RegistrationObservationState.UNAVAILABLE,
            "required safe read-only file flags are unavailable",
        )
    try:
        directory_metadata = os.lstat(directory)
        if stat.S_ISLNK(directory_metadata.st_mode):
            return _observation(
                path, RegistrationObservationState.UNAVAILABLE,
                "registration directory is a symbolic link"
            )
        if not stat.S_ISDIR(directory_metadata.st_mode):
            return _observation(
                path, RegistrationObservationState.UNAVAILABLE,
                "registration directory is not a directory"
            )
        directory_fd = os.open(
            directory,
            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
        )
        filename = path.name
        try:
            metadata = os.stat(filename, dir_fd=directory_fd, follow_symlinks=False)
        except FileNotFoundError:
            return _observation(
                path, RegistrationObservationState.ABSENT,
                "registration file is absent"
            )
        if stat.S_ISLNK(metadata.st_mode):
            return _observation(
                path, RegistrationObservationState.UNAVAILABLE,
                "registration file is a symbolic link"
            )
        if not stat.S_ISREG(metadata.st_mode):
            return _observation(
                path, RegistrationObservationState.UNAVAILABLE,
                "registration path is not a regular file"
            )
        if metadata.st_size > MAX_REGISTRATION_BYTES:
            return _observation(
                path, RegistrationObservationState.MALFORMED,
                "registration exceeds the maximum size"
            )
        file_fd = os.open(
            filename,
            os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC,
            dir_fd=directory_fd,
        )
        current = os.fstat(file_fd)
        if not stat.S_ISREG(current.st_mode):
            return _observation(
                path, RegistrationObservationState.UNAVAILABLE,
                "registration path is not a regular file"
            )
        content = _read_bounded(file_fd)
        if len(content) > MAX_REGISTRATION_BYTES:
            return _observation(
                path, RegistrationObservationState.MALFORMED,
                "registration exceeds the maximum size"
            )
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            return _observation(
                path, RegistrationObservationState.MALFORMED,
                "registration is not valid UTF-8"
            )
        try:
            registration = parse_registration_json(text)
        except UnsupportedRegistrationError:
            return _observation(
                path, RegistrationObservationState.UNSUPPORTED,
                "registration schema version is unsupported"
            )
        except RegistrationConflictError:
            return _observation(
                path, RegistrationObservationState.CONFLICTING,
                "registration conflicts with canonical identity"
            )
        except (ContractError, ValueError):
            return _observation(
                path, RegistrationObservationState.MALFORMED,
                "registration JSON does not match schema version 1"
            )
        expected = derive_identity(logical_name)
        if registration.logical_name != expected.logical_name:
            return _observation(
                path, RegistrationObservationState.CONFLICTING,
                "registration conflicts with canonical identity"
            )
        return RegistrationObservation(
            str(path), RegistrationObservationState.VALID, registration
        )
    except FileNotFoundError:
        return _observation(
            path, RegistrationObservationState.ABSENT,
            "registration directory is absent"
        )
    except OSError as error:
        if error.errno == errno.ELOOP:
            reason = "registration path contains a symbolic link"
        else:
            reason = "registration could not be read in the current context"
        return _observation(path, RegistrationObservationState.UNAVAILABLE, reason)
    finally:
        if file_fd is not None:
            os.close(file_fd)
        if directory_fd is not None:
            os.close(directory_fd)
