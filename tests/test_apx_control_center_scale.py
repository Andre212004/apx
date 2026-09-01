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

    def test_every_keyboard_popup_animates_its_bar_button(self) -> None:
        source = SHELL.read_text()
        bar_button = source.split("component BarButton:", 1)[1].split(
            "component BounceMouseArea:", 1
        )[0]
        self.assertEqual(bar_button.count("scale: button.alternateActive ? 0.94 : 1"), 1)
        self.assertEqual(bar_button.count("scale: button.alternateActive ? 1 : 0.94"), 1)
        self.assertEqual(bar_button.count("duration: 110"), 2)
        self.assertEqual(bar_button.count("duration: 130"), 2)
        self.assertNotIn("Easing.OutBack", bar_button)
        self.assertIn("property bool animateActivation: false", bar_button)
        self.assertIn("property bool animateDeactivation: false", bar_button)
        self.assertIn(
            "readonly property bool visuallyActive: hover.hovered || alternateActive",
            bar_button,
        )
        self.assertIn("HoverHandler {", bar_button)
        self.assertIn("id: hover", bar_button)
        self.assertIn("TapHandler {", bar_button)
        self.assertIn("id: tap", bar_button)
        self.assertIn("acceptedButtons: Qt.LeftButton", bar_button)
        self.assertIn("onTapped: button.activated()", bar_button)
        self.assertIn("scale: tap.pressed ? 0.96 : 1", bar_button)
        self.assertNotIn("MouseArea {", bar_button)
        self.assertIn('color: visuallyActive ? root.cyanDim : "transparent"', bar_button)
        self.assertIn("border.width: visuallyActive ? 1 : 0", bar_button)
        self.assertIn("border.color: root.cyan", bar_button)
        self.assertNotIn("mouse.containsMouse", bar_button)
        self.assertEqual(
            bar_button.count("enabled: button.animateActivation || button.animateDeactivation"),
            4,
        )

        for button_id, kind in (
            ("calendarButton", "calendar"),
            ("environmentButton", "environments"),
            ("modelStoreButton", "model"),
            ("batteryButton", "battery"),
        ):
            block = source.split(f"id: {button_id}", 1)[1].split("onActivated:", 1)[0]
            self.assertIn(f"alternateLabel: {button_id}.label", block)
            self.assertIn(
                f'alternateActive: popup.visible && root.popupKind === "{kind}"',
                block,
            )
            self.assertIn(
                f'animateActivation: root.animatedBarOpenKind === "{kind}"',
                block,
            )
            self.assertIn(
                f'animateDeactivation: root.animatedBarCloseKind === "{kind}"',
                block,
            )

        # The Control Centre deliberately keeps its established | -> A cue.
        controls = source.split("id: controlCenterButton", 1)[1].split("onActivated:", 1)[0]
        self.assertIn('label: "[|]"', controls)
        self.assertIn('alternateLabel: "[A]"', controls)
        self.assertIn(
            'alternateActive: popup.visible && root.popupKind === "controls"',
            controls,
        )
        self.assertIn(
            'animateActivation: root.animatedBarOpenKind === "controls"',
            controls,
        )
        self.assertIn(
            'animateDeactivation: root.animatedBarCloseKind === "controls"',
            controls,
        )

        for unwanted in ('alternateLabel: "[D]"', 'alternateLabel: "[E]"',
                         'alternateLabel: "[I]"', 'alternateLabel: "[B]"'):
            self.assertNotIn(unwanted, source)

        close = source.split("function closePopup()", 1)[1].split(
            "function showPopup()", 1
        )[0]
        same_button = source.split("function togglePopup", 1)[1].split(
            "popupOpenAnimation.stop()", 1
        )[0]
        self.assertIn('animatedBarCloseKind = ""', close)
        self.assertIn("animatedBarCloseKind = kind", same_button)
        self.assertIn('animatedBarOpenKind = ""', same_button)
        self.assertIn("barAnimationReset.restart()", same_button)
        opening = source.split("function togglePopup", 1)[1].split(
            "function focusEnvironmentMenuAfterOpen", 1
        )[0]
        self.assertIn("animatedBarOpenKind = kind", opening)
        self.assertIn("popupKeyboardRequested = keyboardRequested === true", opening)

        popup = source.split("id: popup\n", 1)[1]
        self.assertIn("id: popupHover", popup)
        self.assertIn("focusable: visible", popup)
        self.assertIn("WlrLayershell.layer: WlrLayer.Overlay", popup)
        self.assertNotIn("popupKeyboardClaiming", source)
        self.assertNotIn("popupKeyboardClaimTimer", source)
        self.assertIn("visible && root.popupKeyboardRequested", popup)
        self.assertIn("? WlrKeyboardFocus.Exclusive", popup)
        self.assertNotIn("WlrKeyboardFocus.OnDemand", popup)
        self.assertIn("active: popup.visible", popup)

        dismiss = source.split("id: popupDismissLayer", 1)[1].split(
            "id: popup\n", 1
        )[0]
        self.assertIn("visible: popup.visible", dismiss)
        self.assertIn("WlrLayershell.layer: WlrLayer.Top", dismiss)
        self.assertIn("WlrLayershell.keyboardFocus: WlrKeyboardFocus.None", dismiss)
        self.assertIn("onClicked: root.closePopup()", dismiss)
        popup_frame = source.split("id: popupBackground", 1)[1].split(
            "HoverHandler {", 1
        )[0]
        self.assertIn("color: root.popupPanel", popup_frame)
        self.assertIn('property color popupPanel: "#ff0a1014"', source)
        self.assertIn('border.color: "#26343a"', popup_frame)
        self.assertNotIn("color: root.card", popup_frame)
        self.assertNotIn("border.color: root.cyanDim", popup_frame)

        # Mouse and IPC openings both request exclusive layer-shell keyboard focus. This
        # lets a user click a bar button and immediately continue with arrows,
        # Tab and Enter without first moving the pointer into the popup.
        bar = source.split("id: bar", 1)[1].split("id: hotkeyOsdWindow", 1)[0]
        for kind in ("calendar", "environments", "model", "battery", "controls"):
            self.assertIn(f'root.togglePopup("{kind}", this, true)', bar)
        ipc = source.split('target: "host"', 1)[1]
        for kind, button in (
            ("calendar", "calendarButton"),
            ("environments", "environmentButton"),
            ("model", "modelStoreButton"),
            ("battery", "batteryButton"),
            ("controls", "controlCenterButton"),
        ):
            self.assertIn(f'root.togglePopup("{kind}", {button}, true)', ipc)

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
        self.assertIn("height: visible ? 85 : 0", overview)
        # The compact 46px radio row recovered more space than the taller
        # 40px action cards and their 9px section gap consume.
        self.assertIn("height: visible ? 46 : 0", source)
        self.assertIn("width: parent.width; height: visible ? 9 : 0", overview)
        for label in ('root.isHub ? "Update" : "Apps"', 'text: "Bloquear"',
                      'root.isHub ? "Reiniciar" : "Ficheiros"',
                      'root.isHub ? "Desligar" : "Voltar"'):
            self.assertIn(label, overview)


if __name__ == "__main__":
    unittest.main()
