from __future__ import annotations

from dataclasses import fields, replace
from pathlib import Path
import json
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_environment as contract


UUID = "11111111-1111-4111-8111-111111111111"
PARENT_UUID = "22222222-2222-4222-8222-222222222222"


def registration(name: str = "work") -> contract.EnvironmentRegistration:
    identity = contract.derive_identity(name)
    return contract.EnvironmentRegistration(
        schema_version=contract.REGISTRATION_SCHEMA_VERSION,
        logical_name=name,
        role=identity.role,
        account_name=identity.account,
        home_path=identity.home,
        lifecycle_state="active",
        storage=contract.StorageIdentity("btrfs", 256, UUID, None),
    )


def postconditions(**changes: str) -> contract.CreationPostconditions:
    values = {
        field.name: "confirmed"
        for field in fields(contract.CreationPostconditions)
    }
    values.update(changes)
    return contract.CreationPostconditions(**values)


class RegistrationTests(unittest.TestCase):
    def test_valid_standard_hub_and_development(self) -> None:
        for name, role in (
            ("work", "standard"),
            ("hub", "hub"),
            ("development", "development"),
        ):
            with self.subTest(name=name):
                self.assertEqual(registration(name).role, role)

    def test_canonical_serialization_is_stable_and_round_trips(self) -> None:
        value = registration()
        first = contract.serialize_registration(value)
        second = contract.serialize_registration(value)
        self.assertEqual(first, second)
        self.assertEqual(contract.parse_registration_json(first), value)
        self.assertTrue(first.endswith("\n"))

    def test_malformed_json_is_rejected(self) -> None:
        with self.assertRaises(contract.ContractError):
            contract.parse_registration_json("{")

    def test_wrong_schema_version_is_rejected(self) -> None:
        data = contract.registration_to_data(registration())
        data["schema_version"] = 2
        with self.assertRaises(contract.ContractError):
            contract.parse_registration_json(json.dumps(data))

    def test_missing_and_unknown_fields_are_rejected(self) -> None:
        data = contract.registration_to_data(registration())
        del data["role"]
        with self.assertRaises(contract.ContractError):
            contract.parse_registration_json(json.dumps(data))

    def test_duplicate_fields_are_rejected(self) -> None:
        value = contract.serialize_registration(registration())
        duplicate = value.replace(
            '"schema_version": 1,',
            '"schema_version": 1, "schema_version": 1,',
        )
        with self.assertRaises(contract.ContractError):
            contract.parse_registration_json(duplicate)
        data = contract.registration_to_data(registration())
        data["password"] = "secret"
        with self.assertRaises(contract.ContractError):
            contract.parse_registration_json(json.dumps(data))

    def test_wrong_field_type_is_rejected(self) -> None:
        data = contract.registration_to_data(registration())
        data["logical_name"] = 7
        with self.assertRaises(contract.ContractError):
            contract.parse_registration_json(json.dumps(data))

    def test_identity_and_role_mismatches_are_rejected(self) -> None:
        for field_name, value in (
            ("account_name", "apx-other"),
            ("home_path", "/home/apx-other"),
            ("role", "hub"),
        ):
            with self.subTest(field=field_name):
                data = contract.registration_to_data(registration())
                data[field_name] = value
                with self.assertRaises(contract.ContractError):
                    contract.parse_registration_json(json.dumps(data))

    def test_unknown_and_archived_lifecycle_are_rejected_in_v1(self) -> None:
        for state in ("unknown", "archived"):
            data = contract.registration_to_data(registration())
            data["lifecycle_state"] = state
            with self.subTest(state=state), self.assertRaises(contract.ContractError):
                contract.parse_registration_json(json.dumps(data))

    def test_invalid_storage_identity_is_rejected(self) -> None:
        for field_name, value in (
            ("filesystem_type", "ext4"),
            ("subvolume_id", 0),
            ("subvolume_uuid", "invalid"),
            ("parent_uuid", "invalid"),
        ):
            with self.subTest(field=field_name):
                data = contract.registration_to_data(registration())
                data["storage"][field_name] = value
                with self.assertRaises(contract.ContractError):
                    contract.parse_registration_json(json.dumps(data))

    def test_pre_creation_record_cannot_omit_verified_storage(self) -> None:
        data = contract.registration_to_data(registration())
        data["storage"] = {
            "filesystem_type": "btrfs",
            "subvolume_id": None,
            "subvolume_uuid": None,
            "parent_uuid": None,
        }
        with self.assertRaises(contract.ContractError):
            contract.parse_registration_json(json.dumps(data))

    def test_schema_has_no_secret_or_arbitrary_fields(self) -> None:
        serialized = contract.serialize_registration(registration())
        for forbidden in ("password", "token", "command", "executable", "codex"):
            self.assertNotIn(forbidden, serialized.lower())


class LifecycleTests(unittest.TestCase):
    def test_candidate_without_registration(self) -> None:
        result = contract.classify_environment(
            candidate_present=True, registration=None,
            incomplete_operation=False, observations="confirmed",
            confirmed_mismatch=False,
        )
        self.assertEqual(result, contract.EnvironmentClassification.CANDIDATE)

    def test_registered_unavailable_is_unconfirmed(self) -> None:
        result = contract.classify_environment(
            candidate_present=True, registration=registration(),
            incomplete_operation=False, observations="unavailable",
            confirmed_mismatch=False,
        )
        self.assertEqual(result, contract.EnvironmentClassification.UNCONFIRMED)

    def test_registered_consistent_and_mismatch(self) -> None:
        consistent = contract.classify_environment(
            candidate_present=True, registration=registration(),
            incomplete_operation=False, observations="confirmed",
            confirmed_mismatch=False,
        )
        incomplete = contract.classify_environment(
            candidate_present=True, registration=registration(),
            incomplete_operation=False, observations="confirmed",
            confirmed_mismatch=True,
        )
        self.assertEqual(consistent, contract.EnvironmentClassification.CONSISTENT)
        self.assertEqual(incomplete, contract.EnvironmentClassification.INCOMPLETE)

    def test_incomplete_operation_is_incomplete(self) -> None:
        result = contract.classify_environment(
            candidate_present=False, registration=None,
            incomplete_operation=True, observations="unavailable",
            confirmed_mismatch=False,
        )
        self.assertEqual(result, contract.EnvironmentClassification.INCOMPLETE)

    def test_absence_and_inconsistency_are_distinct(self) -> None:
        absent = contract.classify_environment(
            candidate_present=False, registration=None,
            incomplete_operation=False, observations="confirmed",
            confirmed_mismatch=False,
        )
        self.assertEqual(absent, contract.EnvironmentClassification.ABSENT)
        self.assertNotEqual(absent, contract.EnvironmentClassification.INCOMPLETE)


class CreationStepTests(unittest.TestCase):
    def test_order_is_exact_stable_and_typed(self) -> None:
        self.assertEqual(contract.CREATION_STEPS, tuple(contract.CreationStep))
        self.assertEqual(
            contract.CREATION_STEPS[4],
            contract.CreationStep.CREATE_BTRFS_SUBVOLUME,
        )
        self.assertEqual(
            contract.CREATION_STEPS[5],
            contract.CreationStep.CREATE_LINUX_ACCOUNT,
        )
        self.assertTrue(
            all(isinstance(step, contract.CreationStep) for step in contract.CREATION_STEPS)
        )

    def test_steps_have_no_command_or_path_payload(self) -> None:
        self.assertTrue(all(isinstance(step.value, str) for step in contract.CREATION_STEPS))
        self.assertFalse(any("command" in step.value for step in contract.CREATION_STEPS))
        self.assertFalse(any("/" in step.value for step in contract.CREATION_STEPS))

    def test_all_roles_use_same_steps(self) -> None:
        for name in ("hub", "development", "work"):
            identity = contract.derive_identity(name)
            plan = contract.create_plan(identity, confirmed_preconditions())
            self.assertEqual(plan.steps, contract.CREATION_STEPS)


def confirmed_preconditions() -> contract.CreationPreconditions:
    return contract.CreationPreconditions(
        account_absent="confirmed",
        home_absent="confirmed",
        candidate_absent="confirmed",
        filesystem_type="btrfs",
        filesystem_status="confirmed",
        host_confirmation_required=True,
        registration_absent="confirmed",
        malformed_registration_absent="confirmed",
        registration_target_absent="confirmed",
        parent_paths_valid="confirmed",
        btrfs_context="confirmed",
        host_observation_authoritative="confirmed",
        helper_compatible="confirmed",
        approved_plan_current="confirmed",
        human_authorization_valid="confirmed",
    )


class PreconditionAndDigestTests(unittest.TestCase):
    def test_conflicts_block_and_unavailable_requires_confirmation(self) -> None:
        for field_name in (
            "account_absent", "home_absent", "registration_absent",
            "malformed_registration_absent", "candidate_absent",
        ):
            plan = contract.create_plan(
                contract.derive_identity("work"),
                replace(confirmed_preconditions(), **{field_name: "not-satisfied"}),
            )
            self.assertEqual(plan.architectural_eligibility, "blocked")
        for status in ("unavailable", "ambiguous"):
            plan = contract.create_plan(
                contract.derive_identity("work"),
                replace(confirmed_preconditions(), filesystem_status=status),
            )
            self.assertEqual(
                plan.architectural_eligibility, "requires-host-confirmation"
            )

    def test_non_btrfs_blocks_and_btrfs_can_be_eligible(self) -> None:
        valid = contract.create_plan(
            contract.derive_identity("work"), confirmed_preconditions()
        )
        invalid = contract.create_plan(
            contract.derive_identity("work"),
            replace(confirmed_preconditions(), filesystem_type="ext4"),
        )
        self.assertEqual(valid.architectural_eligibility, "eligible-for-future-apply")
        self.assertEqual(invalid.architectural_eligibility, "blocked")

    def test_relevant_change_changes_digest(self) -> None:
        base = contract.create_plan(
            contract.derive_identity("work"), confirmed_preconditions()
        )
        for field in fields(contract.CreationPreconditions):
            replacement = (
                False
                if field.name == "host_confirmation_required"
                else "not-satisfied"
            )
            with self.subTest(field=field.name):
                stale = contract.create_plan(
                    contract.derive_identity("work"),
                    replace(confirmed_preconditions(), **{field.name: replacement}),
                )
                self.assertNotEqual(
                    contract.plan_digest(base), contract.plan_digest(stale)
                )

    def test_diagnostic_reason_does_not_affect_digest(self) -> None:
        plan = contract.create_plan(
            contract.derive_identity("work"), confirmed_preconditions()
        )
        self.assertEqual(
            contract.plan_digest(plan),
            contract.plan_digest(replace(plan, reason="different diagnostic text")),
        )

    def test_digest_has_no_diagnostics_timestamp_or_randomness(self) -> None:
        plan = contract.create_plan(
            contract.derive_identity("work"), confirmed_preconditions()
        )
        data = json.dumps(contract.asdict(plan), default=str)
        for forbidden in ("diagnostic", "stderr", "timestamp", "random"):
            self.assertNotIn(forbidden, data.lower())
        self.assertEqual(contract.plan_digest(plan), contract.plan_digest(plan))

    def test_plan_schema_and_protocol_compatibility_boundary(self) -> None:
        self.assertEqual(contract.PLAN_SCHEMA_VERSION, 2)
        self.assertIsNone(contract.PRIVILEGED_REQUEST_PROTOCOL_VERSION)


class PostconditionTests(unittest.TestCase):
    def test_complete_state_passes(self) -> None:
        self.assertEqual(
            postconditions().classification(),
            contract.EnvironmentClassification.CONSISTENT,
        )

    def test_each_confirmed_mismatch_is_incomplete(self) -> None:
        for field_name in (
            "account_exists", "account_home_matches",
            "dedicated_btrfs_subvolume", "storage_identity_matches",
            "ownership_matches", "group_matches", "mode_matches",
            "registration_valid",
        ):
            with self.subTest(field=field_name):
                self.assertEqual(
                    postconditions(**{field_name: "not-satisfied"}).classification(),
                    contract.EnvironmentClassification.INCOMPLETE,
                )

    def test_unavailable_is_unconfirmed_not_failed(self) -> None:
        result = postconditions(account_exists="unavailable").classification()
        self.assertEqual(result, contract.EnvironmentClassification.UNCONFIRMED)


class RollbackTests(unittest.TestCase):
    def classify(self, **changes: bool) -> contract.RollbackClassification:
        values = {
            "resource_created_by_operation": True,
            "resource_empty": True,
            "externally_modified": False,
            "user_used": False,
            "registration_published": False,
        }
        values.update(changes)
        return contract.classify_rollback(**values)

    def test_uncreated_resource_needs_no_rollback(self) -> None:
        self.assertEqual(
            self.classify(resource_created_by_operation=False),
            contract.RollbackClassification.NONE_REQUIRED,
        )

    def test_owned_empty_resource_can_be_eligible(self) -> None:
        self.assertEqual(
            self.classify(),
            contract.RollbackClassification.AUTOMATICALLY_ELIGIBLE,
        )

    def test_uncertain_modified_used_or_published_resource_is_preserved(self) -> None:
        for changes in (
            {"resource_empty": False},
            {"externally_modified": True},
            {"user_used": True},
            {"registration_published": True},
        ):
            with self.subTest(changes=changes):
                self.assertEqual(
                    self.classify(**changes),
                    contract.RollbackClassification.PRESERVE_INCOMPLETE,
                )

    def test_classification_is_deterministic(self) -> None:
        self.assertEqual(self.classify(), self.classify())


if __name__ == "__main__":
    unittest.main()
