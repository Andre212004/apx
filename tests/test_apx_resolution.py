from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_isolation
import apx_repository_db
import apx_resolution


def package(name, repo="core", size=10):
    filename = f"{name}-1-1-x86_64.pkg.tar.zst"
    return apx_repository_db.RepositoryPackage(
        repo, name, "1-1", "x86_64", filename, size, size * 2,
        "a" * 64, "YWJj", (),
    )


class ResolutionTests(unittest.TestCase):
    def databases(self):
        seeds = tuple(package(name) for name in apx_isolation.BASE_PACKAGES)
        return (
            apx_repository_db.RepositoryDatabase("core", 1, "b" * 64, 1, 2, seeds),
            apx_repository_db.RepositoryDatabase("extra", 1, "c" * 64, 1, 3, ()),
        )

    def output(self):
        return "\n".join(
            f"core|{item.name}|{item.version}|{item.architecture}|{item.filename}|{item.compressed_size}|"
            f"{apx_resolution.BASE_URI}/core/os/x86_64/{item.filename}"
            for item in self.databases()[0].packages
        ) + "\n"

    def build(self, output=None, databases=None):
        return apx_resolution.build_resolution_manifest(
            self.output() if output is None else output,
            databases=self.databases() if databases is None else databases,
            plan_digest="d" * 64,
        )

    def test_valid_closure_is_canonical_bounded_and_digest_bound(self):
        result = self.build()
        self.assertEqual(len(result.packages), len(apx_isolation.BASE_PACKAGES))
        self.assertEqual(result.aggregate_package_bytes, 60)
        self.assertEqual(len(result.manifest_digest), 64)
        self.assertEqual(tuple(item.name for item in result.packages), tuple(sorted(apx_isolation.BASE_PACKAGES)))

    def test_missing_seed_duplicate_unknown_and_malformed_rows_block(self):
        lines = self.output().splitlines()
        cases = (
            "\n".join(lines[:-1]),
            self.output() + lines[0] + "\n",
            self.output().replace("core|base|", "core|unknown|", 1),
            self.output() + "wrong|fields\n",
        )
        for output in cases:
            with self.subTest(output=output[-50:]):
                with self.assertRaises(apx_resolution.ResolutionError):
                    self.build(output)

    def test_every_database_bound_field_must_match(self):
        original = self.output()
        variants = (
            original.replace("|1-1|", "|2-1|", 1),
            original.replace("|x86_64|", "|any|", 1),
            original.replace("|10|", "|11|", 1),
            original.replace("/core/os/", "/extra/os/", 1),
        )
        for output in variants:
            with self.assertRaises(apx_resolution.ResolutionError):
                self.build(output)

    def test_requires_exactly_core_and_extra_evidence(self):
        with self.assertRaises(apx_resolution.ResolutionError):
            self.build(databases=self.databases()[:1])
        duplicate = self.databases() + (self.databases()[0],)
        with self.assertRaises(apx_resolution.ResolutionError):
            self.build(databases=duplicate)

    def test_package_count_bytes_output_and_plan_digest_bounds(self):
        with self.assertRaises(apx_resolution.ResolutionError):
            self.build(output="x" * (apx_resolution.OUTPUT_MAX + 1))
        with self.assertRaises(apx_resolution.ResolutionError):
            apx_resolution.build_resolution_manifest(
                self.output(), databases=self.databases(), plan_digest="bad"
            )
        large = replace(self.databases()[0].packages[0], compressed_size=apx_resolution.MAX_AGGREGATE_BYTES)
        core = replace(self.databases()[0], packages=(large,) + self.databases()[0].packages[1:])
        with self.assertRaises(apx_resolution.ResolutionError):
            self.build(databases=(core, self.databases()[1]))

if __name__ == "__main__":
    unittest.main()
