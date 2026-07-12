"""Repository-only protected acquisition staging fixture.

The state rules are intended for the future executor, but this store accepts
only a caller-provided disposable directory. It never chooses a host APX path.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import re
import stat
from typing import Iterable


MAX_FILES = 1028
MAX_AGGREGATE_BYTES = 4 * 1024**3
_OPERATION = re.compile(r"op-[0-9a-f]{32}")
_SHA256 = re.compile(r"[0-9a-f]{64}")
_FILENAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9@+_.:-]{0,254}")


class StagingError(RuntimeError):
    """The staging action is unsafe, conflicting, or outside policy."""


@dataclass(frozen=True)
class StagedFile:
    filename: str
    bytes_written: int
    sha256: str
    device: int
    inode: int
    mode: int


class FixtureAcquisitionStaging:
    """Safe disposable-directory fixture; not the authoritative host store."""

    def __init__(self, root: Path, operation_id: str, plan_digest: str) -> None:
        self.root = Path(root)
        self.operation_id = operation_id
        self.plan_digest = plan_digest
        if not _OPERATION.fullmatch(operation_id):
            raise StagingError("invalid operation identity")
        if not _SHA256.fullmatch(plan_digest):
            raise StagingError("invalid plan digest")

    def _open_parent(self) -> int:
        try:
            metadata = os.lstat(self.root)
        except OSError as error:
            raise StagingError("fixture parent is unavailable") from error
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            raise StagingError("fixture parent is not a real directory")
        if metadata.st_uid != os.getuid() or stat.S_IMODE(metadata.st_mode) != 0o700:
            raise StagingError("fixture parent ownership or mode is unsafe")
        try:
            return os.open(self.root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        except OSError as error:
            raise StagingError("fixture parent cannot be opened safely") from error

    def reserve(self) -> None:
        parent_fd = self._open_parent()
        try:
            try:
                os.mkdir(self.operation_id, 0o700, dir_fd=parent_fd)
            except FileExistsError as error:
                raise StagingError("operation staging already exists") from error
            operation_fd = os.open(
                self.operation_id,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                dir_fd=parent_fd,
            )
            try:
                marker_fd = os.open(
                    "plan.digest",
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                    0o600,
                    dir_fd=operation_fd,
                )
                try:
                    os.write(marker_fd, (self.plan_digest + "\n").encode("ascii"))
                    os.fsync(marker_fd)
                finally:
                    os.close(marker_fd)
                os.mkdir("files", 0o700, dir_fd=operation_fd)
                os.fsync(operation_fd)
            finally:
                os.close(operation_fd)
            os.fsync(parent_fd)
        except Exception:
            # Reservation is intentionally preserved on partial failure.
            raise
        finally:
            os.close(parent_fd)

    def _open_operation(self) -> tuple[int, int, int]:
        parent_fd = self._open_parent()
        try:
            operation_fd = os.open(
                self.operation_id,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                dir_fd=parent_fd,
            )
            files_fd = os.open(
                "files", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=operation_fd
            )
        except OSError as error:
            os.close(parent_fd)
            raise StagingError("reserved staging identity is unavailable") from error
        try:
            marker_fd = os.open("plan.digest", os.O_RDONLY | os.O_NOFOLLOW, dir_fd=operation_fd)
            try:
                marker = os.read(marker_fd, 66)
            finally:
                os.close(marker_fd)
            if marker != (self.plan_digest + "\n").encode("ascii"):
                raise StagingError("staging plan binding changed")
            operation_meta = os.fstat(operation_fd)
            files_meta = os.fstat(files_fd)
            if stat.S_IMODE(operation_meta.st_mode) != 0o700 or stat.S_IMODE(files_meta.st_mode) != 0o700:
                raise StagingError("staging directory mode changed")
            return parent_fd, operation_fd, files_fd
        except Exception:
            os.close(files_fd)
            os.close(operation_fd)
            os.close(parent_fd)
            raise

    def _current_usage(self, files_fd: int) -> tuple[int, int]:
        total = 0
        count = 0
        for name in os.listdir(files_fd):
            metadata = os.stat(name, dir_fd=files_fd, follow_symlinks=False)
            if not stat.S_ISREG(metadata.st_mode):
                raise StagingError("staging contains a non-regular entry")
            total += metadata.st_size
            count += 1
        return count, total

    def stage_bytes(
        self,
        *,
        filename: str,
        chunks: Iterable[bytes],
        expected_bytes: int,
        expected_sha256: str,
        per_file_max: int,
    ) -> StagedFile:
        if not isinstance(filename, str) or not _FILENAME.fullmatch(filename):
            raise StagingError("unsafe staging filename")
        numeric = (expected_bytes, per_file_max)
        if not all(type(value) is int and value >= 0 for value in numeric):
            raise StagingError("invalid staging size")
        if expected_bytes > per_file_max or not _SHA256.fullmatch(expected_sha256):
            raise StagingError("expected file evidence is outside policy")
        parent_fd, operation_fd, files_fd = self._open_operation()
        partial = filename + ".partial"
        file_fd: int | None = None
        try:
            count, current = self._current_usage(files_fd)
            if count >= MAX_FILES or current + expected_bytes > MAX_AGGREGATE_BYTES:
                raise StagingError("staging aggregate bound exceeded")
            file_fd = os.open(
                partial,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o600,
                dir_fd=files_fd,
            )
            digest = hashlib.sha256()
            written = 0
            for chunk in chunks:
                if not isinstance(chunk, bytes):
                    raise StagingError("download chunk has wrong type")
                written += len(chunk)
                if written > expected_bytes or written > per_file_max:
                    raise StagingError("download exceeded approved size")
                view = memoryview(chunk)
                while view:
                    consumed = os.write(file_fd, view)
                    if consumed <= 0:
                        raise StagingError("staging write made no progress")
                    view = view[consumed:]
                digest.update(chunk)
            os.fsync(file_fd)
            metadata = os.fstat(file_fd)
            os.close(file_fd)
            file_fd = None
            if written != expected_bytes or digest.hexdigest() != expected_sha256:
                raise StagingError("staged bytes do not match approved evidence")
            os.link(partial, filename, src_dir_fd=files_fd, dst_dir_fd=files_fd, follow_symlinks=False)
            os.unlink(partial, dir_fd=files_fd)
            os.fsync(files_fd)
            return StagedFile(
                filename, written, digest.hexdigest(), metadata.st_dev, metadata.st_ino,
                stat.S_IMODE(metadata.st_mode),
            )
        except FileExistsError as error:
            raise StagingError("staged filename already exists") from error
        finally:
            if file_fd is not None:
                os.close(file_fd)
            os.close(files_fd)
            os.close(operation_fd)
            os.close(parent_fd)
