from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_environment as contract
import apx_registration


UUID = "11111111-1111-4111-8111-111111111111"


def registration_text(name: str = "work", subvolume_uuid: str = UUID) -> str:
    identity = contract.derive_identity(name)
    registration = contract.EnvironmentRegistration(
        schema_version=1,
        logical_name=name,
        role=identity.role,
        account_name=identity.account,
        home_path=identity.home,
        lifecycle_state="active",
        storage=contract.StorageIdentity("btrfs", 256, subvolume_uuid, None),
    )
    return contract.serialize_registration(registration)


class RegistrationObservationTests(unittest.TestCase):
    def observe_with(self, content: str | bytes | None) -> apx_registration.RegistrationObservation:
        with tempfile.TemporaryDirectory() as directory:
            if content is not None:
                path = Path(directory) / "work.json"
                if isinstance(content, bytes):
                    path.write_bytes(content)
                else:
                    path.write_text(content, encoding="utf-8")
                path.chmod(0o644)
            return apx_registration.observe_registration("work", directory)

    def test_valid_schema_v1(self) -> None:
        result = self.observe_with(registration_text())
        self.assertEqual(result.state, "valid")
        self.assertEqual(result.registration.logical_name, "work")
        self.assertIsNone(result.reason)
        self.assertIsNotNone(result.metadata)
        self.assertEqual(result.metadata.mode, 0o644)

    def test_registration_owner_and_group_names_resolve_independently(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "work.json").write_text(
                registration_text(), encoding="utf-8"
            )
            result = apx_registration.observe_registration(
                "work", directory,
                lambda uid: type("User", (), {"pw_name": f"user-{uid}"})(),
                lambda gid: type("Group", (), {"gr_name": f"group-{gid}"})(),
            )
        self.assertEqual(result.metadata.owner_name, f"user-{result.metadata.uid}")
        self.assertEqual(result.metadata.group_name, f"group-{result.metadata.gid}")

    def test_absent_file(self) -> None:
        result = self.observe_with(None)
        self.assertEqual(result.state, "absent")

    def test_absent_directory(self) -> None:
        with tempfile.TemporaryDirectory() as parent:
            result = apx_registration.observe_registration(
                "work", Path(parent) / "missing"
            )
        self.assertEqual(result.state, "absent")

    def test_malformed_json_and_duplicate_fields(self) -> None:
        malformed = self.observe_with("{")
        duplicate = self.observe_with(
            registration_text().replace(
                '"schema_version": 1,',
                '"schema_version": 1, "schema_version": 1,',
            )
        )
        self.assertEqual(malformed.state, "malformed")
        self.assertEqual(duplicate.state, "malformed")

    def test_unsupported_schema(self) -> None:
        data = json.loads(registration_text())
        data["schema_version"] = 2
        result = self.observe_with(json.dumps(data))
        self.assertEqual(result.state, "unsupported")

    def test_identity_conflict(self) -> None:
        result = self.observe_with(registration_text("other"))
        self.assertEqual(result.state, "conflicting")

    def test_invalid_utf8(self) -> None:
        result = self.observe_with(b"\xff\xfe")
        self.assertEqual(result.state, "malformed")
        self.assertEqual(result.reason, "registration is not valid UTF-8")

    def test_oversized_file(self) -> None:
        result = self.observe_with(b"x" * (apx_registration.MAX_REGISTRATION_BYTES + 1))
        self.assertEqual(result.state, "malformed")
        self.assertIn("maximum size", result.reason or "")

    def test_exactly_maximum_size_is_parsed(self) -> None:
        base = registration_text().rstrip("\n")
        padding = apx_registration.MAX_REGISTRATION_BYTES - len(base.encode()) - 1
        content = f"{base}{' ' * padding}\n"
        self.assertEqual(len(content.encode()), apx_registration.MAX_REGISTRATION_BYTES)
        result = self.observe_with(content)
        self.assertEqual(result.state, "valid")

    def test_configured_directory_is_regular_file(self) -> None:
        with tempfile.TemporaryDirectory() as parent:
            path = Path(parent) / "registrations"
            path.write_text("not a directory", encoding="utf-8")
            result = apx_registration.observe_registration("work", path)
        self.assertEqual(result.state, "unavailable")
        self.assertEqual(result.reason, "registration directory is not a directory")

    def test_registration_path_is_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / "work.json").mkdir()
            result = apx_registration.observe_registration("work", directory)
        self.assertEqual(result.state, "unavailable")
        self.assertEqual(result.reason, "registration path is not a regular file")

    def test_symlink_file_is_not_followed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "target.json"
            target.write_text(registration_text(), encoding="utf-8")
            (Path(directory) / "work.json").symlink_to(target)
            result = apx_registration.observe_registration("work", directory)
        self.assertEqual(result.state, "unavailable")
        self.assertIn("symbolic link", result.reason or "")

    def test_symlink_directory_is_not_followed(self) -> None:
        with tempfile.TemporaryDirectory() as parent:
            target = Path(parent) / "target"
            target.mkdir()
            (target / "work.json").write_text(registration_text(), encoding="utf-8")
            link = Path(parent) / "registrations"
            link.symlink_to(target, target_is_directory=True)
            result = apx_registration.observe_registration("work", link)
        self.assertEqual(result.state, "unavailable")
        self.assertEqual(result.reason, "registration directory is a symbolic link")

    def test_permission_denied_is_unavailable_and_sanitized(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / "work.json").write_text(
                registration_text(), encoding="utf-8"
            )
            real_open = os.open

            def denied(path: object, flags: int, *args: object, **kwargs: object) -> int:
                if kwargs.get("dir_fd") is not None:
                    raise PermissionError("secret host path and contents")
                return real_open(path, flags, *args, **kwargs)

            with patch("apx_registration.os.open", side_effect=denied):
                result = apx_registration.observe_registration("work", directory)
        self.assertEqual(result.state, "unavailable")
        self.assertEqual(
            result.reason, "registration could not be read in the current context"
        )
        self.assertNotIn("secret", result.reason)

    def test_invalid_logical_name_cannot_traverse(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                apx_registration.observe_registration("../escape", directory)

    def test_reader_uses_no_write_or_create_flags(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / "work.json").write_text(
                registration_text(), encoding="utf-8"
            )
            real_open = os.open
            calls: list[int] = []

            def recording_open(
                path: object, flags: int, *args: object, **kwargs: object
            ) -> int:
                calls.append(flags)
                return real_open(path, flags, *args, **kwargs)

            with patch("apx_registration.os.open", side_effect=recording_open):
                result = apx_registration.observe_registration("work", directory)
        self.assertEqual(result.state, "valid")
        self.assertTrue(calls)
        for flags in calls:
            self.assertEqual(flags & os.O_ACCMODE, os.O_RDONLY)
            self.assertFalse(flags & os.O_CREAT)
            self.assertFalse(flags & os.O_TRUNC)

    def test_file_descriptors_are_closed_after_success(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / "work.json").write_text(
                registration_text(), encoding="utf-8"
            )
            real_close = os.close
            closed: list[int] = []

            def recording_close(file_fd: int) -> None:
                closed.append(file_fd)
                real_close(file_fd)

            with patch("apx_registration.os.close", side_effect=recording_close):
                result = apx_registration.observe_registration("work", directory)
        self.assertEqual(result.state, "valid")
        self.assertEqual(len(closed), 2)
        self.assertEqual(len(set(closed)), 2)

    def test_missing_safe_open_flags_is_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with patch(
                "apx_registration._safe_open_flags_supported", return_value=False
            ):
                result = apx_registration.observe_registration("work", directory)
        self.assertEqual(result.state, "unavailable")
        self.assertEqual(
            result.reason, "required safe read-only file flags are unavailable"
        )


class UUIDUniquenessTests(unittest.TestCase):
    OTHER_UUID = "22222222-2222-4222-8222-222222222222"

    def write(self, directory: str, name: str, content: str) -> None:
        Path(directory, f"{name}.json").write_text(content, encoding="utf-8")

    def observe(self, directory: str, name: str = "work") -> apx_registration.UUIDUniquenessObservation:
        current = apx_registration.observe_registration(name, directory)
        self.assertEqual(current.state, "valid")
        return apx_registration.observe_uuid_uniqueness(current.registration, directory)

    def test_one_registration_and_two_different_uuids_are_unique(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            self.write(directory, "work", registration_text())
            self.assertEqual(self.observe(directory).state, "confirmed")
            self.write(directory, "other", registration_text("other", self.OTHER_UUID))
            self.assertEqual(self.observe(directory).state, "confirmed")

    def test_duplicate_uuid_is_not_satisfied_and_self_is_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            self.write(directory, "work", registration_text())
            self.write(directory, "other", registration_text("other"))
            result = self.observe(directory)
        self.assertEqual(result.state, "not-satisfied")
        self.assertEqual(result.duplicate_logical_names, ("other",))

    def test_malformed_and_oversized_unrelated_files_are_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            self.write(directory, "work", registration_text())
            self.write(directory, "broken", "{")
            Path(directory, "large.json").write_bytes(
                b"x" * (apx_registration.MAX_REGISTRATION_BYTES + 1)
            )
            self.assertEqual(self.observe(directory).state, "confirmed")

    def test_symlink_or_unsupported_registration_prevents_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            self.write(directory, "work", registration_text())
            Path(directory, "other.json").symlink_to(Path(directory, "work.json"))
            self.assertEqual(self.observe(directory).state, "unavailable")
            Path(directory, "other.json").unlink()
            data = json.loads(registration_text("other", self.OTHER_UUID))
            data["schema_version"] = 2
            self.write(directory, "other", json.dumps(data))
            self.assertEqual(self.observe(directory).state, "unavailable")

    def test_enumerated_registration_that_disappears_is_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            self.write(directory, "work", registration_text())
            self.write(directory, "other", registration_text("other", self.OTHER_UUID))
            current = apx_registration.observe_registration("work", directory)
            vanished = apx_registration.RegistrationObservation(
                str(Path(directory, "other.json")),
                apx_registration.RegistrationObservationState.ABSENT,
            )
            with patch("apx_registration._observe_registration_at", return_value=vanished):
                result = apx_registration.observe_uuid_uniqueness(
                    current.registration, directory
                )
        self.assertEqual(result.state, "unavailable")

    def test_directory_change_during_scan_is_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            self.write(directory, "work", registration_text())
            current = apx_registration.observe_registration("work", directory)
            real_scandir = os.scandir
            calls = 0

            def changing_scandir(path: object):
                nonlocal calls
                calls += 1
                if calls == 2:
                    self.write(directory, "other", registration_text("other", self.OTHER_UUID))
                return real_scandir(path)

            with patch("apx_registration.os.scandir", side_effect=changing_scandir):
                result = apx_registration.observe_uuid_uniqueness(
                    current.registration, directory
                )
        self.assertEqual(result.state, "unavailable")
        self.assertIn("changed", result.reason or "")

    def test_hub_development_and_standard_use_same_rules(self) -> None:
        for name in ("hub", "development", "work"):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                self.write(directory, name, registration_text(name))
                self.assertEqual(self.observe(directory, name).state, "confirmed")

    def test_scan_entry_limit_is_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            self.write(directory, "work", registration_text())
            for number in range(apx_registration.MAX_REGISTRATION_ENTRIES):
                Path(directory, f"ignored-{number}").touch()
            result = self.observe(directory)
        self.assertEqual(result.state, "unavailable")
        self.assertIn("scan limit", result.reason or "")


if __name__ == "__main__":
    unittest.main()
