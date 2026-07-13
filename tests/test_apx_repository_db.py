from __future__ import annotations

import hashlib
import io
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_repository_db as repository


SIGNATURE = "YWJj"


def description(**changes):
    values = {
        "FILENAME": "pkg-1-1-x86_64.pkg.tar.zst",
        "NAME": "pkg",
        "VERSION": "1-1",
        "CSIZE": "123",
        "ISIZE": "456",
        "SHA256SUM": "a" * 64,
        "PGPSIG": SIGNATURE,
        "ARCH": "x86_64",
        "DEPENDS": ("glibc", "bash>=5"),
    }
    values.update(changes)
    lines = []
    for name, raw in values.items():
        items = raw if isinstance(raw, tuple) else (raw,)
        lines.extend((f"%{name}%", *items, ""))
    return "\n".join(lines).encode()


def make_database(path: Path, records):
    with tarfile.open(path, "w:gz") as archive:
        for directory, content in records:
            info = tarfile.TarInfo(f"{directory}/desc")
            info.size = len(content)
            info.mode = 0o644
            archive.addfile(info, io.BytesIO(content))
    return hashlib.sha256(path.read_bytes()).hexdigest()


class RepositoryDatabaseTests(unittest.TestCase):
    def test_valid_database_returns_canonical_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "core.db"
            digest = make_database(path, (("pkg-1-1", description()),))
            result = repository.parse_repository_database(path, repository="core", expected_sha256=digest)
            self.assertEqual(result.file_sha256, digest)
            self.assertEqual(result.packages[0].name, "pkg")
            self.assertEqual(result.packages[0].dependencies, ("glibc", "bash>=5"))

    def test_digest_mismatch_and_symlink_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "core.db"
            digest = make_database(path, (("pkg-1-1", description()),))
            with self.assertRaises(repository.RepositoryDatabaseError):
                repository.parse_repository_database(path, repository="core", expected_sha256="b" * 64)
            link = Path(directory) / "link.db"
            link.symlink_to(path)
            with self.assertRaises(repository.RepositoryDatabaseError):
                repository.parse_repository_database(link, repository="core", expected_sha256=digest)

    def test_traversal_unexpected_member_and_duplicate_package_block(self):
        cases = (
            (("../pkg", description()),),
            (("pkg-1-1/extra", description()),),
            (("pkg-1-1", description()), ("pkg-2-1", description(VERSION="2-1"))),
        )
        for records in cases:
            with self.subTest(records=records), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "core.db"
                digest = make_database(path, records)
                with self.assertRaises(repository.RepositoryDatabaseError):
                    repository.parse_repository_database(path, repository="core", expected_sha256=digest)

    def test_missing_duplicate_malformed_and_binary_fields_block(self):
        malformed = (
            description(SHA256SUM="bad"),
            description(PGPSIG="not base64!"),
            description(CSIZE="-1"),
            description(ARCH="arm64"),
            description(NAME="../pkg"),
            description() + b"\n%NAME%\nother\n",
            description() + b"\x00",
        )
        for content in malformed:
            with self.subTest(content=content[:30]), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "core.db"
                digest = make_database(path, (("pkg-1-1", content),))
                with self.assertRaises(repository.RepositoryDatabaseError):
                    repository.parse_repository_database(path, repository="core", expected_sha256=digest)

    def test_wrong_repository_or_expected_digest_format_blocks(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "core.db"
            digest = make_database(path, (("pkg-1-1", description()),))
            for repo, expected in (("testing", digest), ("core", "bad")):
                with self.assertRaises(repository.RepositoryDatabaseError):
                    repository.parse_repository_database(path, repository=repo, expected_sha256=expected)


if __name__ == "__main__":
    unittest.main()
