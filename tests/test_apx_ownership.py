from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_ownership


class OwnershipTests(unittest.TestCase):
    def test_rootless_host_id_is_rendered_with_namespace_mapping(self) -> None:
        ranges = apx_ownership.parse_subordinate_ranges(
            ["apx-development:231072:65536\n"]
        )
        self.assertEqual(
            apx_ownership.describe_numeric_owner(232073, ranges, identifier="UID"),
            "232073 (allocated to apx-development rootless range; namespace UID 1002)",
        )

    def test_first_subordinate_id_maps_to_namespace_id_one(self) -> None:
        ranges = apx_ownership.parse_subordinate_ranges(["user:100000:65536"])
        self.assertEqual(
            apx_ownership.subordinate_namespace_id(100000, ranges), ("user", 1)
        )

    def test_unmapped_id_remains_numeric(self) -> None:
        ranges = apx_ownership.parse_subordinate_ranges(["user:100000:65536"])
        self.assertEqual(
            apx_ownership.describe_numeric_owner(1002, ranges, identifier="UID"),
            "1002",
        )

    def test_malformed_and_nonpositive_ranges_are_ignored(self) -> None:
        self.assertEqual(
            apx_ownership.parse_subordinate_ranges(
                ["bad", "user:x:2", "user:1:0", ":1:2", "# comment"]
            ),
            (),
        )

    def test_unreadable_file_is_unavailable_without_guessing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing"
            self.assertEqual(apx_ownership.read_subordinate_ranges(missing), ())


if __name__ == "__main__":
    unittest.main()
