import hashlib
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "scripts/virtual-lab/apx-lab-runtime.py"
PROFILE = ROOT / "config/waybar-ascii-v1"
SHELL_PROFILE = ROOT / "config/environment-shell-v1"


def load_runtime():
    spec = importlib.util.spec_from_file_location("apx_lab_runtime_desktop_seed", RUNTIME)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class RuntimeDesktopSeedTests(unittest.TestCase):
    def fixture(self, directory: str):
        runtime = load_runtime()
        seed = Path(directory) / "seed"
        seed.mkdir()
        for name in runtime.DESKTOP_CONFIG_ASSETS:
            (seed / name).write_bytes((PROFILE / name).read_bytes())
        destination = Path(directory) / "home/.config"
        (destination / "waybar").mkdir(parents=True)
        (destination / "waybar/config.json").write_text("old\n")
        (destination / "waybar/style.css").write_text("old\n")
        return runtime, seed, destination

    def apply(self, runtime, seed, destination, role):
        runtime.copy_desktop_config_seed(
            seed, destination, role, uid=os.getuid(), gid=os.getgid(),
        )

    def test_normal_environment_gets_workspace_profile_and_independent_copy(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runtime, seed, destination = self.fixture(directory)
            self.apply(runtime, seed, destination, "graphical-base")
            target = destination / "waybar/config.json"
            self.assertEqual(target.read_bytes(), (PROFILE / "environment-config.json").read_bytes())
            self.assertEqual(target.stat().st_mode & 0o777, 0o600)
            self.assertNotEqual(target.stat().st_ino, (seed / "environment-config.json").stat().st_ino)

    def test_graphical_hub_gets_profile_without_workspace_selector(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runtime, seed, destination = self.fixture(directory)
            self.apply(runtime, seed, destination, "hub-graphical")
            self.assertEqual(
                (destination / "waybar/config.json").read_bytes(),
                (PROFILE / "hub-config.json").read_bytes(),
            )

    def test_changed_extra_or_linked_seed_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runtime, seed, destination = self.fixture(directory)
            (seed / "style.css").write_text("changed\n")
            with self.assertRaises(runtime.Refusal):
                self.apply(runtime, seed, destination, "graphical-base")
        with tempfile.TemporaryDirectory() as directory:
            runtime, seed, destination = self.fixture(directory)
            (seed / "extra").write_text("unexpected\n")
            with self.assertRaises(runtime.Refusal):
                self.apply(runtime, seed, destination, "graphical-base")
        with tempfile.TemporaryDirectory() as directory:
            runtime, seed, destination = self.fixture(directory)
            (seed / "style.css").unlink()
            (seed / "style.css").symlink_to(PROFILE / "style.css")
            with self.assertRaises((runtime.Refusal, OSError)):
                self.apply(runtime, seed, destination, "graphical-base")

    def test_runtime_hashes_match_reviewed_profile(self) -> None:
        runtime = load_runtime()
        for name, expected in runtime.DESKTOP_CONFIG_ASSETS.items():
            self.assertEqual(hashlib.sha256((PROFILE / name).read_bytes()).hexdigest(), expected)

    def test_environment_shell_is_an_independent_exact_copy(self) -> None:
        runtime = load_runtime()
        with tempfile.TemporaryDirectory() as directory:
            seed = Path(directory) / "seed"
            home = Path(directory) / "home"
            home.mkdir()
            for relative in runtime.ENVIRONMENT_SHELL_ASSETS:
                target = seed / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((SHELL_PROFILE / relative).read_bytes())
            runtime.copy_environment_shell_seed(
                seed, home, uid=os.getuid(), gid=os.getgid(),
            )
            # Fresh nested paths must not leave root-owned/mode-0755
            # ancestors that prevent the Environment user from creating
            # ~/.local/state during shell startup.
            for directory_name in (".local", ".local/bin", ".config"):
                target_directory = home / directory_name
                self.assertEqual(target_directory.stat().st_mode & 0o777, 0o700)
                self.assertEqual(target_directory.stat().st_uid, os.getuid())
                self.assertEqual(target_directory.stat().st_gid, os.getgid())
            for relative in runtime.ENVIRONMENT_SHELL_ASSETS:
                parts = Path(relative).parts
                target = (
                    home / ".local" / Path(*parts[1:])
                    if parts[0] == "local"
                    else home / ".config" / relative
                )
                self.assertEqual(target.read_bytes(), (SHELL_PROFILE / relative).read_bytes())
                self.assertNotEqual(target.stat().st_ino, (seed / relative).stat().st_ino)
                expected_mode = 0o755 if relative.startswith("local/bin/") else 0o600
                self.assertEqual(target.stat().st_mode & 0o777, expected_mode)

    def test_changed_or_extra_environment_shell_asset_is_refused(self) -> None:
        runtime = load_runtime()
        for mutation in ("changed", "extra"):
            with tempfile.TemporaryDirectory() as directory:
                seed = Path(directory) / "seed"
                home = Path(directory) / "home"
                home.mkdir()
                for relative in runtime.ENVIRONMENT_SHELL_ASSETS:
                    target = seed / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes((SHELL_PROFILE / relative).read_bytes())
                if mutation == "changed":
                    (seed / "quickshell/apx/shell.qml").write_text("changed\n")
                else:
                    (seed / "unexpected").write_text("unexpected\n")
                with self.assertRaises(runtime.Refusal):
                    runtime.copy_environment_shell_seed(
                        seed, home, uid=os.getuid(), gid=os.getgid(),
                    )

    def test_environment_shell_hashes_match_reviewed_profile(self) -> None:
        runtime = load_runtime()
        for name, expected in runtime.ENVIRONMENT_SHELL_ASSETS.items():
            self.assertEqual(
                hashlib.sha256((SHELL_PROFILE / name).read_bytes()).hexdigest(), expected,
            )


if __name__ == "__main__":
    unittest.main()
