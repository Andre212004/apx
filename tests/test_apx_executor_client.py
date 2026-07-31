import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import apx_executor_client as client
import apx_executor_contract as contract


def request():
    plan = contract.build_operation_plan("activate", "development", 7)
    return contract.ExecutorRequest(
        contract.REQUEST_SCHEMA_VERSION, contract.PROTOCOL_VERSION,
        "op-" + "1" * 32, "activate", "development", 7,
        plan.plan_digest, "approval-" + "2" * 32, "3" * 64, 200,
    )


def response(**changes):
    value = {
        "schema_version": contract.REQUEST_SCHEMA_VERSION,
        "protocol_version": contract.PROTOCOL_VERSION,
        "operation_id": "op-" + "1" * 32,
        "classification": "accepted",
        "issues": [],
        "request_digest": "4" * 64,
    }
    value.update(changes)
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


class ExecutorClientTests(unittest.TestCase):
    def test_exact_request_uses_only_fixed_socket_timeout_and_canonical_payload(self) -> None:
        observed = []
        def connector(path, payload, timeout):
            observed.append((path, payload, timeout))
            return response()
        result = client.exchange_executor_request(request(), connector)
        self.assertEqual(result.classification, "accepted")
        self.assertEqual(observed[0][0], "/run/apx/executor-v1.sock")
        self.assertEqual(observed[0][2], 5.0)
        self.assertEqual(contract.parse_executor_request_json(observed[0][1].decode()), request())

    def test_rejection_issues_are_bounded_and_preserved(self) -> None:
        result = client.parse_executor_response(
            response(classification="rejected", issues=["Hub is not authoritative"]), request(),
        )
        self.assertEqual(result.issues, ("Hub is not authoritative",))

    def test_unknown_missing_duplicate_malformed_and_mismatched_fields_fail(self) -> None:
        values = json.loads(response())
        malformed = []
        extra = {**values, "command": "anything"}
        malformed.append((json.dumps(extra) + "\n").encode())
        missing = dict(values); del missing["issues"]
        malformed.append((json.dumps(missing) + "\n").encode())
        malformed.append(response().rstrip(b"\n"))
        malformed.append(response() + b"{}\n")
        malformed.append(b"\xff\n")
        malformed.append(response(operation_id="op-" + "9" * 32))
        malformed.append(response(protocol_version="caller-v9"))
        malformed.append(response(classification="success"))
        malformed.append(response(request_digest="bad"))
        malformed.append(response(classification="accepted", issues=["contradiction"]))
        duplicate = response().decode().strip()[:-1] + ',"issues":[]}\n'
        malformed.append(duplicate.encode())
        for value in malformed:
            with self.assertRaises(client.ExecutorClientError):
                client.parse_executor_response(value, request())

    def test_issue_count_text_and_response_size_are_bounded(self) -> None:
        invalid = (
            response(classification="rejected", issues=["x"] * 33),
            response(classification="rejected", issues=[""]),
            response(classification="rejected", issues=["x" * 241]),
            response(classification="rejected", issues=["line\nbreak"]),
            b"x" * (client.MAX_RESPONSE_BYTES + 1),
        )
        for value in invalid:
            with self.assertRaises(client.ExecutorClientError):
                client.parse_executor_response(value, request())

    def test_wrong_request_type_never_calls_connector(self) -> None:
        called = []
        with self.assertRaises(client.ExecutorClientError):
            client.exchange_executor_request("activate", lambda *args: called.append(args))
        self.assertEqual(called, [])
