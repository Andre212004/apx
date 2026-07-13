from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_contracts_package as package


def entries():
    values = []
    for index, source in enumerate(
        sorted(package.SOURCE_TARGETS, key=lambda path: package.SOURCE_TARGETS[path])
    ):
        values.append(
            package.PackageEntry(
                source,
                package.SOURCE_TARGETS[source],
                index + 1,
                0o644,
                f"{index + 1:064x}",
            )
        )
    return tuple(values)


def definition():
    return package.build_definition(
        package_version="0.1.0.dev1",
        source_revision="a" * 40,
        source_tree_sha256="b" * 64,
        source_date_epoch=1_800_000_000,
        entries=entries(),
    )


def evidence(**changes):
    subject = package.PackageBuildEvidence(
        1,
        definition().definition_digest,
        "c" * 64,
        1024,
        "d" * 64,
        "e" * 64,
        "f" * 64,
        "unsigned-development-only",
    )
    return replace(subject, **changes)


class ContractsPackageTests(unittest.TestCase):
    def test_closed_definition_is_canonical_and_valid(self) -> None:
        subject = definition()
        package.validate_definition(subject)
        self.assertEqual(subject.package_name, "apx-contracts-development")
        self.assertEqual(subject.runtime_dependencies, ("python",))
        self.assertEqual(subject.license_id, "Apache-2.0")
        self.assertEqual(len(subject.entries), 8)

    def test_missing_extra_duplicate_and_reordered_entries_fail(self) -> None:
        for changed in (
            entries()[:-1],
            entries() + (entries()[0],),
            tuple(reversed(entries())),
        ):
            with self.subTest(count=len(changed)):
                with self.assertRaises(package.ContractsPackageError):
                    package.build_definition(
                        package_version="0.1.0.dev1",
                        source_revision="a" * 40,
                        source_tree_sha256="b" * 64,
                        source_date_epoch=1_800_000_000,
                        entries=changed,
                    )

    def test_mapping_mode_size_and_digest_are_closed(self) -> None:
        variants = (
            replace(entries()[0], target_path="usr/bin/apx"),
            replace(entries()[0], mode=0o755),
            replace(entries()[0], size=0),
            replace(entries()[0], sha256="bad"),
        )
        for changed in variants:
            with self.subTest(changed=changed):
                with self.assertRaises(package.ContractsPackageError):
                    package._validate_entry(changed)

    def test_identity_source_epoch_dependencies_and_features_are_closed(self) -> None:
        subject = definition()
        variants = (
            replace(subject, package_name="apx"),
            replace(subject, architecture="x86_64"),
            replace(subject, license_id="custom"),
            replace(subject, source_revision="dirty"),
            replace(subject, source_date_epoch=True),
            replace(subject, runtime_dependencies=("python", "bash")),
            replace(subject, forbidden_features=()),
        )
        for changed in variants:
            with self.subTest(changed=changed):
                with self.assertRaises(package.ContractsPackageError):
                    package.validate_definition(changed)

    def test_definition_digest_detects_direct_object_tampering(self) -> None:
        with self.assertRaisesRegex(package.ContractsPackageError, "digest disagrees"):
            package.validate_definition(replace(definition(), package_release=2))

    def test_build_evidence_is_bounded_and_never_trusted(self) -> None:
        package.validate_build_evidence(evidence())
        for changed in (
            evidence(classification="trusted"),
            evidence(package_size=0),
            evidence(pkginfo_sha256="bad"),
        ):
            with self.assertRaises(package.ContractsPackageError):
                package.validate_build_evidence(changed)

    def test_two_identical_rebuilds_are_exact_match(self) -> None:
        result = package.compare_rebuilds(definition(), evidence(), evidence())
        self.assertEqual(result.classification, "exact-match")
        self.assertEqual(result.issues, ())

    def test_any_output_or_definition_difference_breaks_match(self) -> None:
        changed_output = evidence(package_sha256="1" * 64, mtree_sha256="2" * 64)
        result = package.compare_rebuilds(definition(), evidence(), changed_output)
        self.assertEqual(result.classification, "mismatch")
        self.assertIn("rebuild-package_sha256-mismatch", result.issues)
        self.assertIn("rebuild-mtree_sha256-mismatch", result.issues)
        wrong_definition = evidence(definition_digest="3" * 64)
        result = package.compare_rebuilds(definition(), evidence(), wrong_definition)
        self.assertIn("definition-identity-mismatch", result.issues)


if __name__ == "__main__":
    unittest.main()
