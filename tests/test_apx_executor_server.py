import socket
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import apx_executor_server as server
from apx_executor_endpoint import EndpointAuthorities
from apx_executor_peer import PeerCredentials


class ExecutorServerTests(unittest.TestCase):
    def test_one_framed_request_reaches_peer_bound_endpoint(self):
        left, right = socket.socketpair()
        authorities = EndpointAuthorities(*(Mock() for _ in range(5)))
        factory = Mock(return_value=authorities)
        with left, right, \
             patch.object(server, "_peer_credentials", return_value=PeerCredentials(12, 1000, 1000)), \
             patch.object(server, "handle_executor_request", return_value=b'{"ok":true}\n') as handle:
            right.sendall(b'{"request":"closed"}\n'); right.shutdown(socket.SHUT_WR)
            server.respond(left, factory)
            self.assertEqual(right.recv(1024), b'{"ok":true}\n')
        factory.assert_called_once_with(PeerCredentials(12, 1000, 1000))
        handle.assert_called_once_with(b'{"request":"closed"}\n', authorities)

    def test_missing_extra_and_oversized_frames_are_rejected(self):
        for payload in (b"", b"{}\n{}\n", b"x" * (server.MAX_REQUEST_BYTES + 1)):
            left, right = socket.socketpair()
            with left, right:
                right.sendall(payload); right.shutdown(socket.SHUT_WR)
                with self.assertRaises(server.ExecutorServerError):
                    server.receive_request(left)

    def test_factory_is_not_called_before_peer_credentials(self):
        left, right = socket.socketpair(); factory = Mock()
        with left, right, patch.object(server, "_peer_credentials", side_effect=server.ExecutorServerError("no peer")):
            with self.assertRaises(server.ExecutorServerError):
                server.respond(left, factory)
        factory.assert_not_called()


if __name__ == "__main__":
    unittest.main()
