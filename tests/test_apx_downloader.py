from __future__ import annotations

import hashlib
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_downloader as downloader


CONTENT = b"signed archive package bytes"
HASH = hashlib.sha256(CONTENT).hexdigest()
URI = "https://archive.archlinux.org/repos/2026/07/11/core/os/x86_64/pkg.tar.zst"


class Response:
    def __init__(self, content=CONTENT, *, status=200, uri=URI, length=None, headers=None):
        self.content = content
        self.offset = 0
        self.status = status
        self.uri = uri
        self.headers = headers if headers is not None else {
            "Content-Length": str(len(content) if length is None else length)
        }
        self.closed = False

    def geturl(self):
        return self.uri

    def read(self, amount):
        chunk = self.content[self.offset:self.offset + amount]
        self.offset += len(chunk)
        return chunk

    def close(self):
        self.closed = True


class DownloaderTests(unittest.TestCase):
    def request(self, **changes):
        values = {
            "uri": URI,
            "filename": "pkg.tar.zst",
            "maximum_bytes": 1024,
            "expected_bytes": len(CONTENT),
            "expected_sha256": HASH,
        }
        values.update(changes)
        return downloader.DownloadRequest(**values)

    def transfer(self, response=None, request=None, **changes):
        response = response or Response()
        consumed = []
        values = {
            "request": request or self.request(),
            "opener": lambda uri, timeout: response,
            "consume": consumed.append,
            "timeout_seconds": 15,
        }
        values.update(changes)
        result = downloader.download_bounded(**values)
        return result, b"".join(consumed), response

    def test_exact_transfer_streams_and_closes(self):
        result, consumed, response = self.transfer()
        self.assertEqual(consumed, CONTENT)
        self.assertEqual(result.sha256, HASH)
        self.assertTrue(response.closed)

    def test_unknown_digest_and_size_can_be_observed_within_maximum(self):
        request = self.request(expected_bytes=None, expected_sha256=None)
        result, _, _ = self.transfer(request=request)
        self.assertEqual(result.bytes_received, len(CONTENT))

    def test_bad_status_redirect_missing_or_malformed_length_block(self):
        cases = (
            Response(status=404),
            Response(uri="https://example.invalid/pkg.tar.zst"),
            Response(headers={}),
            Response(headers={"Content-Length": "1, 2"}),
        )
        for response in cases:
            with self.subTest(response=response):
                with self.assertRaises(downloader.DownloadError):
                    self.transfer(response=response)
                self.assertTrue(response.closed)

    def test_declared_actual_and_policy_size_mismatches_block(self):
        for response, request in (
            (Response(length=len(CONTENT) + 1), self.request(expected_bytes=None)),
            (Response(), self.request(expected_bytes=len(CONTENT) + 1)),
            (Response(), self.request(maximum_bytes=1, expected_bytes=None)),
        ):
            with self.subTest(response=response, request=request):
                with self.assertRaises(downloader.DownloadError):
                    self.transfer(response=response, request=request)

    def test_digest_mismatch_blocks_after_streaming(self):
        with self.assertRaisesRegex(downloader.DownloadError, "digest mismatch"):
            self.transfer(request=self.request(expected_sha256="a" * 64))

    def test_opener_read_and_sink_failures_are_bounded(self):
        with self.assertRaisesRegex(downloader.DownloadError, "could not be opened"):
            self.transfer(opener=lambda uri, timeout: (_ for _ in ()).throw(OSError("network")))

        class Broken(Response):
            def read(self, amount):
                raise TimeoutError

        with self.assertRaisesRegex(downloader.DownloadError, "read failed"):
            self.transfer(response=Broken())
        with self.assertRaisesRegex(downloader.DownloadError, "staging rejected"):
            self.transfer(consume=lambda chunk: (_ for _ in ()).throw(OSError("disk")))

    def test_non_bytes_response_blocks(self):
        class TextResponse(Response):
            def read(self, amount):
                return "text"

        with self.assertRaises(downloader.DownloadError):
            self.transfer(response=TextResponse())

    def test_request_rejects_origin_path_suffix_credentials_and_unsafe_values(self):
        bad = (
            {"uri": URI.replace("https", "http")},
            {"uri": URI.replace("archive.archlinux.org", "example.invalid")},
            {"uri": URI.replace("archive.archlinux.org", "user@archive.archlinux.org")},
            {"uri": URI + "?x=1"},
            {"filename": "../pkg"},
            {"maximum_bytes": True},
            {"expected_bytes": -1},
            {"expected_sha256": "bad"},
        )
        for changes in bad:
            with self.subTest(changes=changes):
                with self.assertRaises(downloader.DownloadError):
                    downloader.validate_download_request(self.request(**changes))

    def test_timeout_and_callback_types_are_closed(self):
        for timeout in (0, -1, 301, True):
            with self.assertRaises(downloader.DownloadError):
                self.transfer(timeout_seconds=timeout)
        with self.assertRaises(downloader.DownloadError):
            downloader.download_bounded(
                self.request(), opener=None, consume=lambda chunk: None, timeout_seconds=15
            )


if __name__ == "__main__":
    unittest.main()
