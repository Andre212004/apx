pragma ComponentBehavior: Bound

import QtQuick
import Quickshell
import Quickshell.Io

ShellRoot {
    id: root
    property color accent: "#ff4d5f"
    property color accentDim: "#742933"
    property color panel: "#ee17090c"
    property color textMain: "#fff1f2"
    property string clockText: ""
    property string volumeText: "--"
    property string batteryText: "--"
    property var environmentIdentity: ({ display_name: "ENVIRONMENT", name: "unknown", category: "general" })

    function updateClock() {
        var now = new Date()
        function two(value) { return value < 10 ? "0" + value : "" + value }
        clockText = two(now.getDate()) + "/" + two(now.getMonth() + 1) + "/" + now.getFullYear()
                    + " | " + two(now.getHours()) + ":" + two(now.getMinutes())
    }

    // Returning is deliberately local: the workload exits only its own
    // compositor and the Host-owned supervisor performs the recovery.
    Process { id: returnProcess; command: ["/usr/bin/hyprctl", "dispatch", "exit"] }
    Process {
        id: identityProcess
        command: ["/run/apx/environment-switch-client-v1.py", "identity"]
        stdout: StdioCollector {
            onStreamFinished: {
                try { root.environmentIdentity = JSON.parse(text) }
                catch (error) { root.environmentIdentity = ({ display_name: "ENVIRONMENT", name: "unknown", category: "general" }) }
            }
        }
    }
    Process {
        id: volumeProcess
        command: ["/usr/bin/wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"]
        stdout: StdioCollector {
            onStreamFinished: {
                var match = text.match(/Volume:\s+([0-9.]+)/)
                root.volumeText = match ? Math.round(parseFloat(match[1]) * 100) + "%" : "--"
            }
        }
    }
    Process {
        id: batteryProcess
        command: ["/usr/bin/bash", "-lc", "for f in /sys/class/power_supply/BAT*/capacity; do test -r \"$f\" && { tr -d '\\n' < \"$f\"; printf '%%'; exit; }; done; printf -- '--'"]
        stdout: StdioCollector { onStreamFinished: root.batteryText = text.trim() }
    }
    Timer {
        interval: 1000; running: true; repeat: true; triggeredOnStart: true
        onTriggered: root.updateClock()
    }
    Component.onCompleted: identityProcess.running = true
    Timer {
        interval: 10000; running: true; repeat: true; triggeredOnStart: true
        onTriggered: {
            if (!volumeProcess.running) volumeProcess.running = true
            if (!batteryProcess.running) batteryProcess.running = true
        }
    }

    component BarButton: Rectangle {
        id: button
        property string label: ""
        signal activated()
        implicitWidth: labelItem.implicitWidth + 22; implicitHeight: 32; radius: 7
        color: mouse.containsMouse ? root.accentDim : "transparent"
        border.width: mouse.containsMouse ? 1 : 0; border.color: root.accent
        Text {
            id: labelItem; anchors.centerIn: parent; text: button.label
            color: mouse.containsMouse ? root.accent : root.textMain
            font.family: "monospace"; font.pixelSize: 13; font.bold: true
        }
        MouseArea {
            id: mouse; anchors.fill: parent; hoverEnabled: true
            cursorShape: Qt.PointingHandCursor; onClicked: button.activated()
        }
    }

    PanelWindow {
        anchors { top: true; left: true; right: true }
        implicitHeight: 46; exclusiveZone: 46; color: "transparent"
        Rectangle {
            anchors.fill: parent; anchors.margins: 5; radius: 9
            color: root.panel; border.width: 1; border.color: root.accentDim
            BarButton {
                anchors.left: parent.left; anchors.leftMargin: 8; anchors.verticalCenter: parent.verticalCenter
                label: "[ " + root.clockText + " ]"
            }
            BarButton {
                anchors.centerIn: parent
                label: "[ APX :: " + String(root.environmentIdentity.display_name).toUpperCase() + " ]"
                onActivated: if (!returnProcess.running) returnProcess.running = true
            }
            Row {
                anchors.right: parent.right; anchors.rightMargin: 8; anchors.verticalCenter: parent.verticalCenter
                spacing: 2
                BarButton { label: "[ VOL " + root.volumeText + " ]" }
                BarButton { label: "[ BAT " + root.batteryText + " ]" }
            }
        }
    }

    PanelWindow {
        anchors { bottom: true; left: true; right: true }
        implicitHeight: 28; exclusiveZone: 0; color: "transparent"
        Rectangle {
            anchors.centerIn: parent; width: warning.implicitWidth + 28; height: 24; radius: 6
            color: "#dd4a0d16"; border.width: 1; border.color: root.accent
            Text {
                id: warning; anchors.centerIn: parent
                text: "WORKLOAD SEM PRIVILEGIOS DO HUB  •  clique APX ENVIRONMENTS para voltar"
                color: root.accent; font.family: "monospace"; font.pixelSize: 12; font.bold: true
            }
        }
    }
}
