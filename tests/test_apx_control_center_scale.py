from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SHELL = ROOT / "config/environment-shell-v1/quickshell/apx/shell.qml"


class ControlCenterScaleTests(unittest.TestCase):
    def test_control_center_matches_desktop_scale_without_fractional_resampling(self) -> None:
        source = SHELL.read_text()
        self.assertIn("readonly property real controlCenterScale: 1", source)
        self.assertIn("forced SVG icons through an intermediate texture", source)
        self.assertIn("340 * root.controlCenterScale", source)
        self.assertIn("(root.isHub ? 440 : 394) * root.controlCenterScale", source)
        self.assertIn("parent.width / root.controlCenterScale", source)
        self.assertIn("parent.height / root.controlCenterScale", source)
        self.assertIn('scale: root.popupKind === "controls" ? root.controlCenterScale : 1', source)
        self.assertIn("transformOrigin: Item.TopLeft", source)
        self.assertIn("function popupStatus(): string", source)

    def test_control_icons_use_qt_icon_rendering_without_post_effect(self) -> None:
        source = SHELL.read_text()
        component = source.split("component ControlIcon: Item", 1)[1].split("PanelWindow", 1)[0]
        self.assertIn("ToolButton", component)
        self.assertIn("icon.source: parent.source", component)
        self.assertIn("icon.color: parent.tint", component)
        self.assertNotIn("MultiEffect", component)
        self.assertNotIn("import QtQuick.Effects", source)

    def test_workload_overview_has_room_for_all_actions(self) -> None:
        source = SHELL.read_text()
        overview = source.split('visible: root.controlsAllClosed() && !root.powerConfirmOpen', 5)[-1]
        self.assertIn("columns: 2", overview)
        self.assertIn("height: visible ? 69 : 0", overview)
        for label in ('root.isHub ? "Update" : "Apps"', 'text: "Bloquear"',
                      'root.isHub ? "Reiniciar" : "Ficheiros"',
                      'root.isHub ? "Desligar" : "Voltar"'):
            self.assertIn(label, overview)


if __name__ == "__main__":
    unittest.main()
