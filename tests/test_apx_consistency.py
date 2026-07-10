from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import os
import stat
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_cli
import apx_consistency
import apx_environment as contract
import apx_registration


UUID = "11111111-1111-4111-8111-111111111111"


def metadata(*, uid: int = 1001, gid: int = 1001, mode: int = 0o700, kind: int = stat.S_IFDIR) -> os.stat_result:
    return os.stat_result([kind | mode, 0, 0, 0, uid, gid, 0, 0, 0, 0])


def registration(name: str = "work") -> contract.EnvironmentRegistration:
    identity = contract.derive_identity(name)
    return contract.EnvironmentRegistration(
        1, name, identity.role, identity.account, identity.home, "active",
        contract.StorageIdentity("btrfs", 256, UUID, None),
    )


def verification(**changes: object) -> apx_consistency.ConsistencyVerification:
    identity = contract.derive_identity("work")
    registered = registration()
    registration_observation = apx_registration.RegistrationObservation(
        "/test/work.json",
        apx_registration.RegistrationObservationState.VALID,
        registered,
        metadata=apx_registration.FileMetadata(0, 0, "root", "root", 0o644),
    )
    values: dict[str, object] = {
        "identity": identity,
        "registration_observation": registration_observation,
        "account": SimpleNamespace(
            pw_name="apx-work", pw_uid=1001, pw_gid=1001,
            pw_dir="/home/apx-work",
        ),
        "home": apx_consistency.HomeMetadataObservation(
            "confirmed", "confirmed", 1001, 1001,
            "apx-work", "apx-work", 0o700, "confirmed",
        ),
        "filesystem_type": "btrfs",
        "filesystem_status": "confirmed",
        "btrfs": apx_cli.BtrfsObservation(
            "yes", "yes", "observed", 256, UUID, None, True, "confirmed",
            "confirmed", "confirmed", "confirmed",
        ),
        "uuid_uniqueness": apx_registration.UUIDUniquenessObservation("confirmed"),
        "incomplete_operation": apx_consistency.IncompleteOperationObservation(
            "/test/work.json", "confirmed"
        ),
    }
    values.update(changes)
    return apx_consistency.verify_consistency(**values)


class HomeMetadataTests(unittest.TestCase):
    def observe(self, value: os.stat_result, writable: bool = True) -> apx_consistency.HomeMetadataObservation:
        return apx_consistency.observe_home_metadata(
            "/home/apx-work",
            lstat_func=lambda _path: value,
            access_func=lambda _path, _mode, **_kwargs: writable,
            uid_resolver=lambda uid: SimpleNamespace(pw_name=f"u{uid}"),
            gid_resolver=lambda gid: SimpleNamespace(gr_name=f"g{gid}"),
        )

    def test_correct_owner_group_mode_and_names(self) -> None:
        result = self.observe(metadata())
        self.assertEqual((result.uid, result.gid, result.mode), (1001, 1001, 0o700))
        self.assertEqual((result.owner_name, result.group_name), ("u1001", "g1001"))
        self.assertEqual(result.writable, "confirmed")

    def test_incorrect_values_are_preserved(self) -> None:
        result = self.observe(metadata(uid=9, gid=8, mode=0o755), writable=False)
        self.assertEqual((result.uid, result.gid, result.mode), (9, 8, 0o755))
        self.assertEqual(result.writable, "not-satisfied")

    def test_missing_permission_denied_symlink_and_non_directory(self) -> None:
        for error, expected in ((FileNotFoundError(), "not-satisfied"), (PermissionError(), "unavailable")):
            with self.subTest(expected=expected):
                result = apx_consistency.observe_home_metadata(
                    "/x", lstat_func=lambda _path, error=error: (_ for _ in ()).throw(error)
                )
                self.assertEqual(result.exists, expected)
        self.assertEqual(self.observe(metadata(kind=stat.S_IFLNK)).directory, "not-satisfied")
        self.assertEqual(self.observe(metadata(kind=stat.S_IFREG)).directory, "not-satisfied")

    def test_unresolved_uid_and_gid_preserve_numeric_values(self) -> None:
        def missing(_identifier: int) -> object:
            raise KeyError
        result = apx_consistency.observe_home_metadata(
            "/x", lstat_func=lambda _path: metadata(),
            uid_resolver=missing, gid_resolver=missing,
        )
        self.assertEqual((result.uid, result.gid), (1001, 1001))
        self.assertIsNone(result.owner_name)
        self.assertIsNone(result.group_name)


class IncompleteOperationTests(unittest.TestCase):
    def test_absent_directory_and_file_are_confirmed_absent(self) -> None:
        missing = apx_consistency.observe_incomplete_operation(
            "work", "/missing", lstat_func=lambda _path: (_ for _ in ()).throw(FileNotFoundError())
        )
        self.assertEqual(missing.absent, "confirmed")
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(
                apx_consistency.observe_incomplete_operation("work", directory).absent,
                "confirmed",
            )

    def test_record_exists_and_unsafe_paths(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "work.json"
            path.write_text("marker", encoding="utf-8")
            self.assertEqual(
                apx_consistency.observe_incomplete_operation("work", directory).absent,
                "not-satisfied",
            )
            path.unlink()
            path.symlink_to(Path(directory) / "other")
            self.assertEqual(
                apx_consistency.observe_incomplete_operation("work", directory).absent,
                "unavailable",
            )


class VerificationTests(unittest.TestCase):
    def test_complete_matching_postconditions_are_consistent(self) -> None:
        self.assertEqual(verification().classification, contract.EnvironmentClassification.CONSISTENT)

    def test_each_confirmed_mismatch_is_incomplete(self) -> None:
        bad_home = apx_consistency.HomeMetadataObservation(
            "confirmed", "confirmed", 9, 1001, None, None, 0o755, "confirmed"
        )
        self.assertEqual(
            verification(home=bad_home).classification,
            contract.EnvironmentClassification.INCOMPLETE,
        )
        self.assertEqual(
            verification(uuid_uniqueness=apx_registration.UUIDUniquenessObservation("not-satisfied", ("other",))).classification,
            contract.EnvironmentClassification.INCOMPLETE,
        )
        bad_registration = apx_registration.RegistrationObservation(
            "/test/work.json",
            apx_registration.RegistrationObservationState.VALID,
            registration(),
            metadata=apx_registration.FileMetadata(1, 2, "user", "group", 0o600),
        )
        result = verification(registration_observation=bad_registration)
        self.assertEqual(result.classification, contract.EnvironmentClassification.INCOMPLETE)
        self.assertEqual(result.postconditions.registration_owner_matches, "not-satisfied")
        self.assertEqual(result.postconditions.registration_group_matches, "not-satisfied")
        self.assertEqual(result.postconditions.registration_mode_matches, "not-satisfied")
        wrong_private_group = apx_consistency.HomeMetadataObservation(
            "confirmed", "confirmed", 1001, 1001,
            "apx-work", "shared-group", 0o700, "confirmed",
        )
        self.assertEqual(
            verification(home=wrong_private_group).postconditions.group_matches,
            "not-satisfied",
        )

    def test_unavailable_required_observation_is_unconfirmed(self) -> None:
        self.assertEqual(
            verification(uuid_uniqueness=apx_registration.UUIDUniquenessObservation("unavailable")).classification,
            contract.EnvironmentClassification.UNCONFIRMED,
        )

    def test_mismatch_precedes_unavailable_and_not_attempted_is_registered(self) -> None:
        bad_home = apx_consistency.HomeMetadataObservation(
            "confirmed", "confirmed", 9, 1001, None, None, 0o700, "confirmed"
        )
        self.assertEqual(
            verification(
                home=bad_home,
                uuid_uniqueness=apx_registration.UUIDUniquenessObservation("unavailable"),
            ).classification,
            contract.EnvironmentClassification.INCOMPLETE,
        )
        values = {
            field.name: "confirmed"
            for field in __import__("dataclasses").fields(contract.CreationPostconditions)
        }
        values["uuid_unique"] = "not-attempted"
        self.assertEqual(
            contract.CreationPostconditions(**values).classification(),
            contract.EnvironmentClassification.REGISTERED,
        )

    def test_unresolved_private_group_name_uses_canonical_primary_gid(self) -> None:
        unresolved = apx_consistency.HomeMetadataObservation(
            "confirmed", "confirmed", 1001, 1001,
            None, None, 0o700, "confirmed",
        )
        self.assertEqual(
            verification(home=unresolved).postconditions.group_matches,
            "confirmed",
        )

    def test_parent_uuid_requires_observed_field(self) -> None:
        incomplete_parent = apx_cli.BtrfsObservation(
            "yes", "yes", "observed", 256, UUID, None, False, "confirmed",
            "confirmed", "confirmed", "confirmed",
        )
        result = verification(btrfs=incomplete_parent)
        self.assertEqual(result.postconditions.parent_uuid_matches, "unavailable")
        self.assertEqual(
            result.classification, contract.EnvironmentClassification.UNCONFIRMED
        )

    def test_malformed_numeric_identity_evidence_is_unavailable(self) -> None:
        malformed = apx_consistency.HomeMetadataObservation(
            "confirmed", "confirmed", True, "1001",
            None, None, 0o700, "confirmed",
        )
        result = verification(home=malformed)
        self.assertEqual(result.postconditions.ownership_matches, "unavailable")
        self.assertEqual(result.postconditions.group_matches, "unavailable")

    def test_classification_is_deterministic(self) -> None:
        self.assertEqual(verification().classification, verification().classification)


if __name__ == "__main__":
    unittest.main()
