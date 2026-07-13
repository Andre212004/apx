from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_database_acquisition as database


CONTENTS = {"core.db": b"core database", "extra.db": b"extra database"}


class Response:
    status = 200

    def __init__(self, uri):
        self.uri = uri
        self.content = CONTENTS[uri.rsplit("/", 1)[-1]]
        self.headers = HeaderLike(str(len(self.content)))
        self.offset = 0

    def geturl(self):
        return self.uri

    def read(self, amount):
        chunk = self.content[self.offset:self.offset + amount]
        self.offset += len(chunk)
        return chunk

    def close(self):
        pass


class HeaderLike:
    """Matches real HTTPMessage's get interface without being a Mapping."""

    def __init__(self, length):
        self.length = length

    def get(self, name):
        return self.length if name == "Content-Length" else None


class DatabaseAcquisitionTests(unittest.TestCase):
    def test_requests_are_exactly_two_fixed_dated_databases(self):
        requests = database.fixed_requests()
        self.assertEqual([item.filename for item in requests], ["core.db", "extra.db"])
        self.assertTrue(all(item.maximum_bytes == 64 * 1024**2 for item in requests))
        self.assertTrue(all(item.uri.startswith(database.BASE_URI + "/") for item in requests))

    def test_fake_acquisition_streams_both_and_reports_bounded_total(self):
        with tempfile.TemporaryDirectory() as parent:
            root = Path(parent) / "new-root"
            report = database.acquire_fixed_databases(
                root=root, opener=lambda uri, timeout: Response(uri)
            )
            self.assertEqual([item.staged.filename for item in report.files], ["core.db", "extra.db"])
            self.assertEqual(report.aggregate_bytes, sum(map(len, CONTENTS.values())))
            self.assertLessEqual(report.aggregate_bytes, database.AGGREGATE_MAX)
            output = database.render_report(report)
            self.assertIn("not installed or extracted", output)
            self.assertIn("requires separate approval", output)

    def test_existing_root_is_never_adopted(self):
        with tempfile.TemporaryDirectory() as parent:
            root = Path(parent) / "existing"
            root.mkdir()
            with self.assertRaisesRegex(RuntimeError, "refusing adoption"):
                database.acquire_fixed_databases(
                    root=root, opener=lambda uri, timeout: Response(uri)
                )

    def test_non_tmp_alternate_root_is_rejected(self):
        with self.assertRaises(ValueError):
            database.acquire_fixed_databases(
                root=Path("/var/lib/apx/not-authorized"),
                opener=lambda uri, timeout: Response(uri),
            )


if __name__ == "__main__":
    unittest.main()
