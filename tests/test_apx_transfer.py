from __future__ import annotations

import hashlib
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_downloader
import apx_staging
import apx_transfer


OPERATION = "op-" + "a" * 32
PLAN = "b" * 64
CONTENT = b"database bytes streamed directly"
HASH = hashlib.sha256(CONTENT).hexdigest()
URI = "https://archive.archlinux.org/repos/2026/07/11/core/os/x86_64/core.db"


class Response:
    status = 200
    headers = {"Content-Length": str(len(CONTENT))}

    def __init__(self, content=CONTENT):
        self.content = content
        self.offset = 0
        self.closed = False

    def geturl(self):
        return URI

    def read(self, amount):
        value = self.content[self.offset:self.offset + 5]
        self.offset += len(value)
        return value

    def close(self):
        self.closed = True


class TransferIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.root.chmod(0o700)
        self.staging = apx_staging.FixtureAcquisitionStaging(self.root, OPERATION, PLAN)
        self.staging.reserve()
        self.request = apx_downloader.DownloadRequest(
            URI, "core.db", 64 * 1024**2, None, None
        )

    def tearDown(self):
        self.temp.cleanup()

    def test_unknown_database_bytes_stream_and_publish_with_matching_evidence(self):
        response = Response()
        result = apx_transfer.acquire_to_fixture(
            request=self.request,
            staging=self.staging,
            opener=lambda uri, timeout: response,
            timeout_seconds=15,
        )
        target = self.root / OPERATION / "files" / "core.db"
        self.assertEqual(target.read_bytes(), CONTENT)
        self.assertEqual(result.transfer.sha256, HASH)
        self.assertEqual(result.staged.sha256, HASH)
        self.assertTrue(response.closed)

    def test_network_failure_preserves_partial_and_never_publishes(self):
        class Broken(Response):
            def read(self, amount):
                if self.offset >= 5:
                    raise TimeoutError
                return super().read(amount)

        with self.assertRaises(apx_downloader.DownloadError):
            apx_transfer.acquire_to_fixture(
                request=self.request,
                staging=self.staging,
                opener=lambda uri, timeout: Broken(),
                timeout_seconds=15,
            )
        files = self.root / OPERATION / "files"
        self.assertTrue((files / "core.db.partial").is_file())
        self.assertFalse((files / "core.db").exists())

    def test_existing_partial_refuses_retry_without_recovery_decision(self):
        writer = self.staging.begin_stream(filename="core.db", maximum_bytes=1024)
        writer.write(b"partial")
        writer.close()
        with self.assertRaises(apx_staging.StagingError):
            apx_transfer.acquire_to_fixture(
                request=self.request,
                staging=self.staging,
                opener=lambda uri, timeout: Response(),
                timeout_seconds=15,
            )


if __name__ == "__main__":
    unittest.main()
