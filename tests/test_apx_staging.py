from __future__ import annotations

import hashlib
import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_staging as staging


OPERATION = "op-" + "a" * 32
PLAN = "b" * 64
CONTENT = b"verified package bytes"
CONTENT_HASH = hashlib.sha256(CONTENT).hexdigest()


class StagingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.root.chmod(0o700)
        self.store = staging.FixtureAcquisitionStaging(self.root, OPERATION, PLAN)

    def tearDown(self):
        self.temp.cleanup()

    def reserve(self):
        self.store.reserve()

    def stage(self, **changes):
        values = {
            "filename": "package.pkg.tar.zst",
            "chunks": (CONTENT[:5], CONTENT[5:]),
            "expected_bytes": len(CONTENT),
            "expected_sha256": CONTENT_HASH,
            "per_file_max": 1024,
        }
        values.update(changes)
        return self.store.stage_bytes(**values)

    def test_reserve_binds_plan_and_restricts_modes(self):
        self.reserve()
        operation = self.root / OPERATION
        self.assertEqual(stat.S_IMODE(operation.stat().st_mode), 0o700)
        self.assertEqual(stat.S_IMODE((operation / "plan.digest").stat().st_mode), 0o600)
        self.assertEqual((operation / "plan.digest").read_text(), PLAN + "\n")

    def test_reservation_never_adopts_existing_state(self):
        self.reserve()
        with self.assertRaisesRegex(staging.StagingError, "already exists"):
            self.reserve()

    def test_success_publishes_exact_regular_file(self):
        self.reserve()
        result = self.stage()
        target = self.root / OPERATION / "files" / result.filename
        self.assertEqual(target.read_bytes(), CONTENT)
        self.assertEqual(result.mode, 0o600)
        self.assertFalse((target.parent / (target.name + ".partial")).exists())

    def test_wrong_hash_short_and_oversized_content_remain_unpublished(self):
        cases = (
            {"expected_sha256": "c" * 64},
            {"chunks": (CONTENT[:-1],)},
            {"chunks": (CONTENT + b"x",)},
        )
        for index, changes in enumerate(cases):
            with self.subTest(changes=changes):
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    root.chmod(0o700)
                    store = staging.FixtureAcquisitionStaging(root, OPERATION, PLAN)
                    store.reserve()
                    values = {
                        "filename": f"package{index}.pkg.tar.zst",
                        "chunks": (CONTENT,),
                        "expected_bytes": len(CONTENT),
                        "expected_sha256": CONTENT_HASH,
                        "per_file_max": 1024,
                    }
                    values.update(changes)
                    with self.assertRaises(staging.StagingError):
                        store.stage_bytes(**values)
                    self.assertFalse((root / OPERATION / "files" / values["filename"]).exists())

    def test_partial_is_preserved_after_failure(self):
        self.reserve()
        with self.assertRaises(staging.StagingError):
            self.stage(expected_sha256="c" * 64)
        partial = self.root / OPERATION / "files" / "package.pkg.tar.zst.partial"
        self.assertTrue(partial.is_file())
        self.assertEqual(partial.read_bytes(), CONTENT)

    def test_symlink_parent_and_entries_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            real = parent / "real"
            real.mkdir(mode=0o700)
            link = parent / "link"
            link.symlink_to(real, target_is_directory=True)
            store = staging.FixtureAcquisitionStaging(link, OPERATION, PLAN)
            with self.assertRaises(staging.StagingError):
                store.reserve()
        self.reserve()
        files = self.root / OPERATION / "files"
        (files / "foreign").symlink_to("/dev/null")
        with self.assertRaisesRegex(staging.StagingError, "non-regular"):
            self.stage()

    def test_changed_plan_marker_or_directory_mode_blocks(self):
        self.reserve()
        marker = self.root / OPERATION / "plan.digest"
        marker.write_text("c" * 64 + "\n")
        with self.assertRaisesRegex(staging.StagingError, "binding changed"):
            self.stage()
        marker.write_text(PLAN + "\n")
        (self.root / OPERATION / "files").chmod(0o755)
        with self.assertRaisesRegex(staging.StagingError, "mode changed"):
            self.stage()

    def test_unsafe_root_ownership_mode_operation_and_filename_block(self):
        self.root.chmod(0o755)
        with self.assertRaises(staging.StagingError):
            self.store.reserve()
        with self.assertRaises(staging.StagingError):
            staging.FixtureAcquisitionStaging(self.root, "bad", PLAN)
        self.root.chmod(0o700)
        self.reserve()
        for filename in ("../x", "x/y", ".hidden"):
            with self.assertRaises(staging.StagingError):
                self.stage(filename=filename)

    def test_no_overwrite_and_partial_collision(self):
        self.reserve()
        self.stage()
        with self.assertRaises(staging.StagingError):
            self.stage()

    def test_invalid_types_and_policy_bounds_block(self):
        self.reserve()
        for changes in (
            {"expected_bytes": True},
            {"expected_bytes": -1},
            {"expected_sha256": "bad"},
            {"per_file_max": 1},
            {"chunks": ("not bytes",)},
        ):
            with self.subTest(changes=changes):
                with self.assertRaises(staging.StagingError):
                    self.stage(filename="x" + str(len(str(changes))) + ".pkg", **changes)


if __name__ == "__main__":
    unittest.main()
