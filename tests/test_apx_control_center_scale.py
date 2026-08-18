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
        self.assertIn('property real popupReveal: 1', source)
        self.assertIn('* (0.96 + 0.04 * root.popupReveal)', source)
        self.assertIn('opacity: root.popupReveal', source)
        self.assertIn('id: popupOpenAnimation', source)
        self.assertIn('property: "popupReveal"', source)
        self.assertIn('duration: 160', source)
        self.assertNotIn('id: popupOpenTimer', source)
        self.assertNotIn('property bool popupOpening', source)
        self.assertIn("transformOrigin: Item.TopLeft", source)
        self.assertIn("function popupStatus(): string", source)

    def test_popup_opening_uses_one_explicit_forward_animation(self) -> None:
        source = SHELL.read_text()

        show = source.split("function showPopup()", 1)[1].split("function togglePopup", 1)[0]
        toggle = source.split("function togglePopup", 1)[1].split("function focusEnvironmentMenuAfterOpen", 1)[0]

        self.assertIn("popupReveal = 0", show)
        self.assertIn("popup.visible = true", show)
        self.assertIn("popupOpenAnimation.restart()", show)

        # Switching from one APX menu to another must not destroy/hide the
        # layer surface for a frame before revealing the next menu.
        switch_path = toggle.split('if (popupKind === kind && popup.visible)', 1)[1]
        self.assertEqual(switch_path.count("popup.visible = false"), 1)

    def test_audio_slider_updates_volume_while_dragging(self) -> None:
        source = SHELL.read_text()

        self.assertIn("property int volumePending: -1", source)
        self.assertIn("function previewVolume(value)", source)
        self.assertIn("function dispatchPendingVolume()", source)
        self.assertIn("onMoved: root.previewVolume(value)", source)
        self.assertIn("id: volumeSetPump", source)
        self.assertIn("interval: 40", source)
        self.assertIn("repeat: true", source)
        self.assertIn("id: volumeSetProcess", source)
        self.assertIn('"@DEFAULT_AUDIO_SINK@"', source)

        preview = source.split(
            "function previewVolume(value)", 1
        )[1].split(
            "function dispatchPendingVolume()", 1
        )[0]
        self.assertIn("volumeValue = nextVolume", preview)
        self.assertIn('volumeText = nextVolume + "%"', preview)
        self.assertIn("volumePending = nextVolume", preview)

        dispatch = source.split(
            "function dispatchPendingVolume()", 1
        )[1].split(
            "function commitVolume(value)", 1
        )[0]
        self.assertIn("volumeSetProcess.command", dispatch)
        self.assertIn("volumeSetProcess.running = true", dispatch)

        # The old behaviour explicitly waited for release before reflecting
        # the selected position. That contract must not return.
        self.assertNotIn(
            "Keep the UI at the released position while wpctl confirms it.",
            source,
        )

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
