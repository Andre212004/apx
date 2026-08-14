import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "scripts/virtual-lab/apx-lab-runtime.py"


def load_runtime():
    spec = importlib.util.spec_from_file_location("apx_lab_runtime_recovery_test", RUNTIME)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class RuntimeRecoveryTests(unittest.TestCase):
    def test_uncertain_unpublished_operation_can_close_after_proven_absence(self) -> None:
        runtime = load_runtime()
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory)
            runtime.STATE = state
            runtime.ENVIRONMENTS = state / "environments"
            runtime.JOURNAL = state / "journal/operations.jsonl"
            runtime.ENVIRONMENTS.mkdir()
            operation = "operation-absent-fixture"
            runtime.append_event(operation, "create", "operation", "started", name="codex-test-absent")
            runtime.append_event(operation, "create", "operation", "uncertain", name="codex-test-absent")

            with patch.object(runtime, "require_root"), patch.object(
                runtime, "machine_running", return_value=False
            ):
                runtime.recover_unpublished(
                    "codex-test-absent", "CLEAN UNPUBLISHED codex-test-absent"
                )

            last = json.loads(runtime.JOURNAL.read_text().splitlines()[-1])
            self.assertEqual(last["operation"], operation)
            self.assertEqual(last["status"], "complete")
            self.assertEqual(last["recovery"], "confirmed-already-absent")

    def test_absence_cannot_close_without_matching_uncertain_operation(self) -> None:
        runtime = load_runtime()
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory)
            runtime.STATE = state
            runtime.ENVIRONMENTS = state / "environments"
            runtime.JOURNAL = state / "journal/operations.jsonl"
            runtime.ENVIRONMENTS.mkdir()
            with patch.object(runtime, "require_root"), patch.object(
                runtime, "machine_running", return_value=False
            ):
                with self.assertRaises(runtime.Refusal):
                    runtime.recover_unpublished(
                        "codex-test-absent", "CLEAN UNPUBLISHED codex-test-absent"
                    )


if __name__ == "__main__":
    unittest.main()
