"""Read-only APX Environment postcondition observations."""

from __future__ import annotations

from dataclasses import dataclass
import grp
import os
from pathlib import Path
import pwd
import stat
from typing import Callable

from apx_environment import (
    CreationPostconditions,
    EnvironmentClassification,
    EnvironmentIdentity,
    EnvironmentRegistration,
    INCOMPLETE_OPERATION_ROOT,
)
from apx_registration import FileMetadata, RegistrationObservation, UUIDUniquenessObservation


@dataclass(frozen=True)
class HomeMetadataObservation:
    exists: str
    directory: str
    uid: int | None
    gid: int | None
    owner_name: str | None
    group_name: str | None
    mode: int | None
    writable: str
    reason: str | None = None


@dataclass(frozen=True)
class IncompleteOperationObservation:
    expected_path: str
    absent: str
    reason: str | None = None


@dataclass(frozen=True)
class ConsistencyVerification:
    postconditions: CreationPostconditions
    classification: EnvironmentClassification
    home: HomeMetadataObservation
    registration_metadata: FileMetadata | None
    incomplete_operation: IncompleteOperationObservation
    uuid_uniqueness: UUIDUniquenessObservation


def _resolved_name(resolver: Callable[[int], object], identifier: int, field: str) -> str | None:
    try:
        return getattr(resolver(identifier), field)
    except (KeyError, OSError, AttributeError):
        return None


def observe_home_metadata(
    path: str,
    *,
    lstat_func: Callable[[str], os.stat_result] = os.lstat,
    access_func: Callable[..., bool] = os.access,
    uid_resolver: Callable[[int], object] = pwd.getpwuid,
    gid_resolver: Callable[[int], object] = grp.getgrgid,
) -> HomeMetadataObservation:
    try:
        metadata = lstat_func(path)
    except FileNotFoundError:
        return HomeMetadataObservation("not-satisfied", "not-satisfied", None, None, None, None, None, "not-satisfied", "home is absent")
    except OSError:
        return HomeMetadataObservation("unavailable", "unavailable", None, None, None, None, None, "unavailable", "home metadata unavailable")
    if stat.S_ISLNK(metadata.st_mode):
        return HomeMetadataObservation("confirmed", "not-satisfied", metadata.st_uid, metadata.st_gid, None, None, stat.S_IMODE(metadata.st_mode), "unavailable", "home path is a symbolic link")
    is_directory = stat.S_ISDIR(metadata.st_mode)
    try:
        writable = (
            "confirmed"
            if access_func(path, os.W_OK, follow_symlinks=False)
            else "not-satisfied"
        )
    except OSError:
        writable = "unavailable"
    return HomeMetadataObservation(
        "confirmed",
        "confirmed" if is_directory else "not-satisfied",
        metadata.st_uid,
        metadata.st_gid,
        _resolved_name(uid_resolver, metadata.st_uid, "pw_name"),
        _resolved_name(gid_resolver, metadata.st_gid, "gr_name"),
        stat.S_IMODE(metadata.st_mode),
        writable,
    )


def observe_incomplete_operation(
    logical_name: str,
    directory: str | os.PathLike[str] = INCOMPLETE_OPERATION_ROOT,
    *,
    lstat_func: Callable[[str | os.PathLike[str]], os.stat_result] = os.lstat,
) -> IncompleteOperationObservation:
    from apx_environment import derive_identity

    identity = derive_identity(logical_name)
    root = Path(directory)
    path = root / f"{identity.logical_name}.json"
    directory_fd: int | None = None
    try:
        root_metadata = lstat_func(root)
    except FileNotFoundError:
        return IncompleteOperationObservation(str(path), "confirmed", "incomplete-operation directory is absent")
    except OSError:
        return IncompleteOperationObservation(str(path), "unavailable", "incomplete-operation state unavailable")
    if stat.S_ISLNK(root_metadata.st_mode) or not stat.S_ISDIR(root_metadata.st_mode):
        return IncompleteOperationObservation(str(path), "unavailable", "incomplete-operation directory is unsafe")
    try:
        required = ("O_NOFOLLOW", "O_DIRECTORY", "O_CLOEXEC")
        if not all(hasattr(os, name) for name in required):
            return IncompleteOperationObservation(str(path), "unavailable", "safe incomplete-operation inspection unavailable")
        directory_fd = os.open(
            root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
        )
        marker = os.stat(path.name, dir_fd=directory_fd, follow_symlinks=False)
    except FileNotFoundError:
        return IncompleteOperationObservation(str(path), "confirmed")
    except OSError:
        return IncompleteOperationObservation(str(path), "unavailable", "incomplete-operation state unavailable")
    finally:
        if directory_fd is not None:
            os.close(directory_fd)
    if stat.S_ISLNK(marker.st_mode) or not stat.S_ISREG(marker.st_mode):
        return IncompleteOperationObservation(str(path), "unavailable", "incomplete-operation path is unsafe")
    return IncompleteOperationObservation(str(path), "not-satisfied", "incomplete-operation record exists")


def match_state(observed: object, expected: object) -> str:
    if observed is None:
        return "unavailable"
    return "confirmed" if observed == expected else "not-satisfied"


def numeric_identity_state(observed: object, expected: object) -> str:
    values = (observed, expected)
    if any(type(value) is not int or value < 0 for value in values):
        return "unavailable"
    return "confirmed" if observed == expected else "not-satisfied"


def verify_consistency(
    *,
    identity: EnvironmentIdentity,
    registration_observation: RegistrationObservation,
    account: object | None,
    home: HomeMetadataObservation,
    filesystem_type: str | None,
    filesystem_status: str,
    btrfs: object,
    uuid_uniqueness: UUIDUniquenessObservation,
    incomplete_operation: IncompleteOperationObservation,
) -> ConsistencyVerification:
    registration = registration_observation.registration
    if registration is None:
        raise ValueError("consistency verification requires a valid registration")
    account_exists = "confirmed" if account is not None else "not-satisfied"
    account_name = getattr(account, "pw_name", None) if account else None
    account_home = getattr(account, "pw_dir", None) if account else None
    account_gid = getattr(account, "pw_gid", None) if account else None
    filesystem_state = (
        match_state(filesystem_type, "btrfs")
        if filesystem_status == "confirmed"
        else filesystem_status
    )
    dedicated = getattr(btrfs, "subvolume", "unavailable")
    dedicated_state = {"yes": "confirmed", "no": "not-satisfied"}.get(dedicated, dedicated if dedicated in {"unavailable", "ambiguous"} else "unavailable")
    subvolume_id_status = getattr(btrfs, "subvolume_id_status", "unavailable")
    subvolume_uuid_status = getattr(btrfs, "subvolume_uuid_status", "unavailable")
    parent_uuid_status = getattr(btrfs, "parent_uuid_status", "unavailable")
    subvolume_id_state = (
        match_state(getattr(btrfs, "subvolume_id", None), registration.storage.subvolume_id)
        if subvolume_id_status == "confirmed" else subvolume_id_status
    )
    subvolume_uuid_state = (
        match_state(getattr(btrfs, "subvolume_uuid", None), registration.storage.subvolume_uuid)
        if subvolume_uuid_status == "confirmed" else subvolume_uuid_status
    )
    parent_uuid_state = (
        "confirmed"
        if parent_uuid_status == "confirmed"
        and getattr(btrfs, "parent_uuid_observed", False)
        and getattr(btrfs, "parent_uuid", None) == registration.storage.parent_uuid
        else "not-satisfied"
        if parent_uuid_status == "confirmed"
        and getattr(btrfs, "parent_uuid_observed", False)
        else "unavailable"
        if parent_uuid_status == "confirmed"
        else parent_uuid_status
    )
    expected_account_uid = getattr(account, "pw_uid", None) if account else None
    owner_state = (
        numeric_identity_state(home.uid, expected_account_uid)
        if expected_account_uid is not None else "unavailable"
    )
    numeric_group_state = (
        numeric_identity_state(home.gid, account_gid)
        if account_gid is not None else "unavailable"
    )
    group_state = (
        numeric_group_state
        if numeric_group_state != "confirmed"
        else "not-satisfied"
        if home.group_name is not None and home.group_name != identity.account
        else "confirmed"
    )
    mode_state = match_state(home.mode, 0o700)
    registration_metadata = registration_observation.metadata
    reg_owner = match_state(registration_metadata.uid if registration_metadata else None, 0)
    reg_group = match_state(registration_metadata.gid if registration_metadata else None, 0)
    reg_mode = match_state(registration_metadata.mode if registration_metadata else None, 0o644)
    registration_host_owned = (
        "not-satisfied" if "not-satisfied" in {reg_owner, reg_group, reg_mode}
        else "unavailable" if "unavailable" in {reg_owner, reg_group, reg_mode}
        else "confirmed"
    )
    storage_identity = (
        "not-satisfied" if "not-satisfied" in {subvolume_id_state, subvolume_uuid_state, parent_uuid_state}
        else "unavailable" if "unavailable" in {subvolume_id_state, subvolume_uuid_state, parent_uuid_state}
        else "ambiguous" if "ambiguous" in {subvolume_id_state, subvolume_uuid_state, parent_uuid_state}
        else "confirmed"
    )
    postconditions = CreationPostconditions(
        registration_valid="confirmed",
        account_exists=account_exists,
        account_name_matches=match_state(account_name, identity.account),
        account_home_matches=match_state(account_home, identity.home),
        role_matches=match_state(registration.role, identity.role),
        home_directory_exists=("not-satisfied" if "not-satisfied" in {home.exists, home.directory} else "unavailable" if "unavailable" in {home.exists, home.directory} else "confirmed"),
        home_filesystem_btrfs=filesystem_state,
        dedicated_btrfs_subvolume=dedicated_state,
        storage_identity_matches=storage_identity,
        subvolume_id_matches=subvolume_id_state,
        subvolume_uuid_matches=subvolume_uuid_state,
        parent_uuid_matches=parent_uuid_state,
        uuid_unique=uuid_uniqueness.state,
        ownership_matches=owner_state,
        group_matches=group_state,
        mode_matches=mode_state,
        registration_host_owned=registration_host_owned,
        registration_owner_matches=reg_owner,
        registration_group_matches=reg_group,
        registration_mode_matches=reg_mode,
        incomplete_marker_absent=incomplete_operation.absent,
    )
    return ConsistencyVerification(postconditions, postconditions.classification(), home, registration_metadata, incomplete_operation, uuid_uniqueness)
