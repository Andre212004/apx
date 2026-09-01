from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/physical-pilot/apx-build-hub-headless-v4.py"


class BuildHubHeadlessV4Tests(unittest.TestCase):
    def test_builder_uses_two_fixed_fresh_builds_and_preserves_partials(self) -> None:
        source = SCRIPT.read_text()
        compile(source, str(SCRIPT), "exec")
        for required in (
            "hub-headless-v4-build-a", "hub-headless-v4-build-b",
            '"/usr/bin/pacstrap", "-c"', '"base", "sudo"',
            "two-fresh-pacstrap-builds", "INCOMPLETE",
            '"snapshot", "-r"', "PUBLISH HUB HEADLESS V4",
            'Path("/etc/hostname").read_text().strip()',
        ):
            self.assertIn(required, source)
        self.assertNotIn('"/usr/bin/hostname"', source)
        self.assertNotIn("shutil.rmtree(destination", source)

    def test_builder_excludes_graphical_install_and_normalizes_mutable_state(self) -> None:
        source = SCRIPT.read_text()
        for required in (
            "INSTALLDATE", "random-seed", "pacman.log",
            "SOURCE_DATE_EPOCH", "--faked-system-time", "--export-ownertrust",
            "--import-ownertrust", "trustdb.gpg", "S.*", "aux-cache",
            "owner_installs_hyprland=true", "owner_installs_terminal=true",
            "APX ENVIRONMENT: estás dentro do Hub, NÃO estás no Host",
            "Usa 'exit' ou Ctrl+D para regressar ao Host",
        ):
            self.assertIn(required, source)
        for forbidden in ('"hyprland"', '"kitty"', '"waybar"'):
            self.assertNotIn(forbidden, source.split("def publish", 1)[0])


if __name__ == "__main__":
    unittest.main()
