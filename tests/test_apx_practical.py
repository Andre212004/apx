from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import os
import stat
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import apx_cli
import apx_practical


class Account:
    def __init__(self, name: str, uid: int) -> None:
        self.pw_name, self.pw_uid, self.pw_gid = name, uid, uid


def result(code: int = 0, output: str = "") -> apx_cli.CommandResult:
    return apx_cli.CommandResult(code, output, "")


class PracticalTests(unittest.TestCase):
    def observe(self, *, commands: dict[tuple[str, ...], apx_cli.CommandResult] | None = None, unavailable: bool = False):
        accounts = [Account(name, 1000 + index) for index, (_, name, _) in enumerate(apx_practical.ENVIRONMENTS, 1)]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            homes = {}
            for logical, name, home in apx_practical.ENVIRONMENTS:
                path = root / name
                path.mkdir(mode=0o700)
                homes[home] = path
            (homes["/home/apx-trial"] / "evidence.txt").write_text("x")
            (homes["/home/apx-development"] / ".config" / "BraveSoftware").mkdir(parents=True)
            dm = root / "display-manager.service"
            dm.symlink_to("/usr/lib/systemd/system/sddm.service")

            def lstat(path: str) -> os.stat_result:
                if path == "/etc/systemd/system/display-manager.service": return os.lstat(dm)
                for home, actual in homes.items():
                    if path == home: return os.lstat(actual)
                    if path.startswith(home + "/"): return os.lstat(str(actual) + path[len(home):])
                raise FileNotFoundError

            def scandir(path: str): return os.scandir(homes[path])
            calls = []
            mapping = commands or {}
            def runner(argv, timeout):
                calls.append(tuple(argv))
                if unavailable: return apx_cli.CommandResult(None, "", "", "missing executable")
                defaults = {
                    ("pacman", "-Qq"): result(0, "brave-bin\nother\n"),
                    ("pacman", "-Qo", "/usr/bin/brave"): result(0, "/usr/bin/brave is owned by brave-bin 1\n"),
                    ("flatpak", "list", "--app", "--columns=application"): result(0, ""),
                    ("loginctl", "list-seats", "--no-legend", "--no-pager"): result(0, "seat0\n"),
                }
                return mapping.get(tuple(argv), defaults.get(tuple(argv), result()))
            which = lambda name: "/usr/bin/brave" if name == "brave" else "/usr/bin/" + name
            sessions = SimpleNamespace(status="confirmed", sessions=())
            report = apx_practical.observe_practical(
                accounts=accounts, sessions=sessions,
                mount_observer=lambda path: SimpleNamespace(status="confirmed"),
                btrfs_observer=lambda path, mount: SimpleNamespace(subvolume="yes"),
                command_runner=runner, lstat_func=lstat, scandir_func=scandir,
                which_func=which, readlink_func=lambda path: "/usr/lib/systemd/system/sddm.service",
            )
            return report, calls

    def test_brave_arch_mechanism_and_user_data(self) -> None:
        report, _ = self.observe()
        self.assertEqual(report.brave.mechanism, "Arch package")
        self.assertEqual(report.brave.arch_packages, ("brave-bin",))
        self.assertEqual(dict(report.brave.user_data)["apx-development"], "present")
        self.assertEqual(dict(report.brave.user_data)["apx-hub"], "absent")

    def test_trial_nonempty_home_is_confirmed_blocker(self) -> None:
        report, _ = self.observe()
        trial = next(item for item in report.environments if item.logical_name == "trial")
        self.assertIn("confirmed blocker", trial.removal_evidence)
        self.assertIn("non-empty home", trial.removal_evidence)

    def test_unavailable_state_is_unknown(self) -> None:
        report, _ = self.observe(unavailable=True)
        trial = next(item for item in report.environments if item.logical_name == "trial")
        self.assertIn("unknown", trial.removal_evidence)
        self.assertEqual(trial.processes, "unavailable")

    def test_findmnt_empty_result_means_no_associated_mounts(self) -> None:
        commands = {
            ("findmnt", "--json", "--submounts", home): result(1)
            for _, _, home in apx_practical.ENVIRONMENTS
        }
        report, _ = self.observe(commands=commands)
        self.assertTrue(all(item.mounts == "none" for item in report.environments))

    def test_output_is_deterministic_and_concise(self) -> None:
        first, _ = self.observe()
        second, _ = self.observe()
        self.assertEqual(apx_practical.render_practical(first), apx_practical.render_practical(second))
        self.assertNotIn("evidence.txt: ", apx_practical.render_practical(first))

    def test_only_fixed_observational_commands(self) -> None:
        _, calls = self.observe()
        allowed = {"ps", "findmnt", "du", "pacman", "flatpak", "loginctl"}
        self.assertTrue(all(command[0] in allowed for command in calls))
        self.assertNotIn("sudo", repr(calls).lower())


if __name__ == "__main__":
    unittest.main()
