import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "scripts/virtual-lab/apx-lab-runtime.py"


def load_runtime():
    spec = importlib.util.spec_from_file_location("apx_update_policy_runtime", RUNTIME)
    module = importlib.util.module_from_spec(spec); assert spec.loader is not None; spec.loader.exec_module(module)
    return module


class CoordinatedUpdateCreationPolicyTests(unittest.TestCase):
    def test_new_environment_follows_host_by_default(self):
        runtime = load_runtime()
        with patch.object(runtime, "environment_dir") as directory, patch.object(runtime, "admitted_release"), \
                patch.object(runtime, "atomic_json"):
            directory.return_value.exists.return_value = False
            plan = runtime.make_plan("create", "work", "graphical-base")
        self.assertEqual(plan["update_policy"], "follow-host")

    def test_owner_can_exclude_environment_during_creation_plan(self):
        runtime = load_runtime()
        with patch.object(runtime, "environment_dir") as directory, patch.object(runtime, "admitted_release"), \
                patch.object(runtime, "atomic_json"):
            directory.return_value.exists.return_value = False
            plan = runtime.make_plan("create", "private", "graphical-base", "excluded")
        self.assertEqual(plan["update_policy"], "excluded")

    def test_unknown_policy_is_refused(self):
        runtime = load_runtime()
        with patch.object(runtime, "environment_dir") as directory:
            directory.return_value.exists.return_value = False
            with self.assertRaises(runtime.Refusal):
                runtime.make_plan("create", "work", "graphical-base", "sometimes")


if __name__ == "__main__": unittest.main()
