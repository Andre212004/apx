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
        self.assertIn("property int volumeInFlight: -1", source)
        self.assertIn("property int volumeLastSent: -1", source)

        self.assertIn("function previewVolume(value)", source)
        self.assertIn("function dispatchVolume()", source)
        # Both the compact overview slider and the expanded audio slider must
        # update the visible percentage and real PipeWire volume during drag.
        self.assertEqual(source.count("onMoved: root.previewVolume(value)"), 2)

        preview = source.split(
            "function previewVolume(value)", 1
        )[1].split(
            "function dispatchVolume()", 1
        )[0]

        self.assertIn(
            "volumeValue = Math.max(0, Math.min(100, Math.round(value)))",
            preview,
        )
        self.assertIn("volumePending = volumeValue", preview)
        self.assertIn(
            "if (!volumeSetProcess.running)",
            preview,
        )
        self.assertIn("dispatchVolume()", preview)

        dispatch = source.split(
            "function dispatchVolume()", 1
        )[1].split(
            "function commitVolume(value)", 1
        )[0]

        self.assertIn("var nextVolume = volumePending", dispatch)
        self.assertIn("volumePending = -1", dispatch)
        self.assertIn("volumeInFlight = nextVolume", dispatch)
        self.assertIn("volumeLastSent = nextVolume", dispatch)
        self.assertIn("volumeSetProcess.running = true", dispatch)
        self.assertIn('"@DEFAULT_AUDIO_SINK@"', dispatch)

        process = source.split(
            "id: volumeSetProcess", 1
        )[1].split(
            "id: volumeProcess", 1
        )[0]

        self.assertIn("if (root.volumePending >= 0)", process)
        self.assertIn("root.dispatchVolume()", process)

        # Audio dragging must not depend on a debounce/pump timer. A timer can
        # defer the real write until movement stops or the pointer is released.
        self.assertNotIn("id: volumeSetDebounce", source)
        self.assertNotIn("id: volumeSetPump", source)

    def test_calendar_is_fully_reachable_from_the_keyboard(self) -> None:
        source = SHELL.read_text()

        self.assertIn('property var calendarFocusAction:', source)
        self.assertIn("function calendarKeyboardActions()", source)
        self.assertIn("function moveCalendarKeyboardFocus(step)", source)
        self.assertIn("function activateCalendarKeyboardFocus()", source)
        self.assertIn("function handleCalendarKey(event)", source)
        self.assertIn("id: calendarMenu", source)
        self.assertIn("Keys.onPressed: function(event) { root.handleCalendarKey(event) }", source)
        self.assertIn("calendarMenu.forceActiveFocus()", source)

        handler = source.split(
            "function handleCalendarKey(event)", 1
        )[1].split(
            "function focusCalendarMenuAfterOpen()", 1
        )[0]
        for key in (
            "Qt.Key_Left", "Qt.Key_Right", "Qt.Key_Up", "Qt.Key_Down",
            "Qt.Key_Tab", "Qt.Key_Backtab", "Qt.Key_Return", "Qt.Key_Enter",
            "Qt.Key_Space", "Qt.Key_PageUp", "Qt.Key_PageDown", "Qt.Key_Home",
        ):
            self.assertIn(key, handler)

        # Enter can reach every action class in the calendar overview.
        activation = source.split(
            "function activateCalendarKeyboardFocus()", 1
        )[1].split(
            "function handleCalendarKey(event)", 1
        )[0]
        for kind in (
            '"previous"', '"next"', '"view"', '"date"', '"month"',
            '"today"', '"new"', '"edit"', '"delete"',
        ):
            self.assertIn(kind, activation)

        # The editor starts in its first text field and exposes the remaining
        # text and action controls through the normal Tab focus chain.
        self.assertIn("calendarTitleField.focusInput()", source)
        self.assertIn("activeFocusOnTab: true", source)
        self.assertIn("function cancelCalendarEditor()", source)

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
