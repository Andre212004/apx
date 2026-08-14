pragma ComponentBehavior: Bound

import QtQuick
import Quickshell
import Quickshell.Io

ShellRoot {
    id: root

    property color cyan: "#55e6ff"
    property color cyanDim: "#246879"
    property color panel: "#e90a1014"
    property color card: "#f2162027"
    property color textMain: "#e8f7fa"
    property color textDim: "#8aa3aa"
    property string popupKind: ""
    property Item popupTarget: null
    property var hostState: ({})
    property string clockText: ""
    property string volumeText: "--"
    property string batteryText: "--"

    function togglePopup(kind, target) {
        if (popup.visible && popupKind === kind) {
            popup.visible = false
            popupKind = ""
            return
        }
        popup.visible = false
        popupKind = kind
        popupTarget = target
        popup.anchor.item = target
        popup.visible = true
    }

    function hostAction(operation, target) {
        if (hostActionProcess.running)
            return
        var args = ["/run/apx/host-services-ui-v3.py", operation]
        if (target !== undefined && target !== "")
            args.push(target)
        hostActionProcess.command = args
        hostActionProcess.running = true
    }

    function localAction(args) {
        if (!localActionProcess.running) {
            localActionProcess.command = args
            localActionProcess.running = true
        }
    }

    function updateClock() {
        var now = new Date()
        function two(value) { return value < 10 ? "0" + value : "" + value }
        clockText = two(now.getDate()) + "/" + two(now.getMonth() + 1) + "/" + now.getFullYear()
                    + " | " + two(now.getHours()) + ":" + two(now.getMinutes())
    }

    Process {
        id: hostStatusProcess
        command: ["/run/apx/host-services-ui-v3.py", "status"]
        stdout: StdioCollector {
            onStreamFinished: {
                try { root.hostState = JSON.parse(text) }
                catch (error) { root.hostState = ({ network_name: "host?", bluetooth_powered: false }) }
            }
        }
    }

    Process {
        id: hostActionProcess
        onExited: hostStatusProcess.running = true
    }

    Process {
        id: bluetoothManagerProcess
        command: ["/run/apx/desktop-menu-v2.py", "bluetooth"]
        onExited: hostStatusProcess.running = true
    }

    Process {
        id: localActionProcess
        onExited: {
            volumeProcess.running = true
            batteryProcess.running = true
        }
    }

    Process {
        id: volumeProcess
        command: ["/usr/bin/wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"]
        stdout: StdioCollector {
            onStreamFinished: {
                var match = text.match(/Volume:\s+([0-9.]+)/)
                root.volumeText = match ? Math.round(parseFloat(match[1]) * 100) + "%" : "--"
                if (text.indexOf("MUTED") >= 0) root.volumeText = "MUTE"
            }
        }
    }

    Process {
        id: batteryProcess
        command: ["/usr/bin/bash", "-lc", "for f in /sys/class/power_supply/BAT*/capacity; do test -r \"$f\" && { tr -d '\\n' < \"$f\"; printf '%%'; exit; }; done; printf -- '--'"]
        stdout: StdioCollector { onStreamFinished: root.batteryText = text.trim() }
    }

    Process { id: switcherProcess; command: ["/run/apx/environment-switch-client-v1.py", "hub-menu"] }

    Timer {
        interval: 1000
        running: true
        repeat: true
        triggeredOnStart: true
        onTriggered: root.updateClock()
    }

    Timer {
        interval: 10000
        running: true
        repeat: true
        triggeredOnStart: true
        onTriggered: {
            if (!hostStatusProcess.running) hostStatusProcess.running = true
            if (!volumeProcess.running) volumeProcess.running = true
            if (!batteryProcess.running) batteryProcess.running = true
        }
    }

    component BarButton: Rectangle {
        id: button
        property string label: ""
        signal activated()
        implicitWidth: buttonText.implicitWidth + 22
        implicitHeight: 32
        radius: 7
        color: mouse.containsMouse ? root.cyanDim : "transparent"
        border.width: mouse.containsMouse ? 1 : 0
        border.color: root.cyan
        Text {
            id: buttonText
            anchors.centerIn: parent
            text: button.label
            color: mouse.containsMouse ? root.cyan : root.textMain
            font.family: "monospace"
            font.pixelSize: 13
            font.bold: true
        }
        MouseArea {
            id: mouse
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: button.activated()
        }
    }

    component MenuButton: Rectangle {
        id: menuButton
        property string label: ""
        property bool accent: false
        signal activated()
        width: parent ? parent.width : 250
        height: 34
        radius: 6
        color: menuMouse.containsMouse ? root.cyanDim : (accent ? "#1c3941" : "#101920")
        border.width: accent ? 1 : 0
        border.color: root.cyan
        Text {
            anchors.left: parent.left
            anchors.leftMargin: 11
            anchors.verticalCenter: parent.verticalCenter
            text: menuButton.label
            color: menuButton.accent ? root.cyan : root.textMain
            font.family: "monospace"
            font.pixelSize: 12
        }
        MouseArea {
            id: menuMouse
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: menuButton.activated()
        }
    }

    PanelWindow {
        id: bar
        anchors { top: true; left: true; right: true }
        implicitHeight: 46
        exclusiveZone: 46
        color: "transparent"

        Rectangle {
            anchors.fill: parent
            anchors.margins: 5
            radius: 9
            color: root.panel
            border.width: 1
            border.color: "#26343a"

            Row {
                anchors.left: parent.left
                anchors.leftMargin: 8
                anchors.verticalCenter: parent.verticalCenter
                spacing: 4
                BarButton {
                    label: "[ " + root.clockText + " ]"
                    onActivated: root.togglePopup("battery", this)
                }
            }

            BarButton {
                id: environmentButton
                anchors.centerIn: parent
                label: "[ APX · HUB · ENVIRONMENTS ]"
                onActivated: {
                    popup.visible = false
                    switcherProcess.running = true
                }
            }

            Row {
                anchors.right: parent.right
                anchors.rightMargin: 8
                anchors.verticalCenter: parent.verticalCenter
                spacing: 2
                BarButton {
                    label: "[ WIFI " + (root.hostState.network_name || "OFF") + " ]"
                    onActivated: root.togglePopup("wifi", this)
                }
                BarButton {
                    label: "[ BT " + (root.hostState.bluetooth_powered ? "ON" : "OFF") + " ]"
                    onActivated: root.togglePopup("bluetooth", this)
                }
                BarButton {
                    label: "[ VOL " + root.volumeText + " ]"
                    onActivated: root.togglePopup("audio", this)
                }
                BarButton {
                    label: "[ BAT " + root.batteryText + " ]"
                    onActivated: root.togglePopup("battery", this)
                }
            }
        }
    }

    PopupWindow {
        id: popup
        implicitWidth: 300
        implicitHeight: 330
        visible: false
        color: "transparent"
        grabFocus: true
        anchor.edges: Edges.Bottom
        anchor.gravity: Edges.Bottom
        anchor.margins.top: 8

        Rectangle {
            anchors.fill: parent
            radius: 10
            color: root.card
            border.width: 1
            border.color: root.cyanDim

            Flickable {
                anchors.fill: parent
                anchors.margins: 12
                contentWidth: width
                contentHeight: menuContent.implicitHeight
                clip: true
                boundsBehavior: Flickable.StopAtBounds

                Column {
                    id: menuContent
                    width: parent.width
                    spacing: 7

                Text {
                    text: "[ " + root.popupKind.toUpperCase() + " CONTROL ]"
                    color: root.cyan
                    font.family: "monospace"
                    font.pixelSize: 14
                    font.bold: true
                }
                Rectangle { width: parent.width; height: 1; color: root.cyanDim }

                    Column {
                    width: parent.width
                    spacing: 6
                    visible: root.popupKind === "wifi"
                    Text {
                        text: "STATUS :: " + (root.hostState.network_name || "disconnected")
                        color: root.textDim; font.family: "monospace"; font.pixelSize: 12
                    }
                    MenuButton { label: "[ SCAN ] procurar redes"; accent: true; onActivated: root.hostAction("wifi-scan") }
                    MenuButton {
                        visible: !!root.hostState.network_name
                        label: "[ DISCONNECT ] rede atual"
                        onActivated: root.hostAction("wifi-disconnect")
                    }
                    Text { text: "KNOWN NETWORKS"; color: root.textDim; font.family: "monospace"; font.pixelSize: 11 }
                    Repeater {
                        model: root.hostState.known_networks || []
                        MenuButton {
                            required property string modelData
                            visible: modelData !== root.hostState.network_name
                            label: "[ CONNECT ] " + modelData
                            onActivated: root.hostAction("wifi-connect", modelData)
                        }
                    }
                }

                    Column {
                    width: parent.width
                    spacing: 6
                    visible: root.popupKind === "bluetooth"
                    MenuButton {
                        label: root.hostState.bluetooth_powered ? "[ POWER ] desligar" : "[ POWER ] ligar"
                        accent: true
                        onActivated: root.hostAction("bluetooth-power", root.hostState.bluetooth_powered ? "off" : "on")
                    }
                    MenuButton {
                        visible: root.hostState.bluetooth_powered
                        label: "[ MANAGE ] procurar, emparelhar ou remover"
                        onActivated: if (!bluetoothManagerProcess.running) bluetoothManagerProcess.running = true
                    }
                    Text { text: "PAIRED DEVICES"; color: root.textDim; font.family: "monospace"; font.pixelSize: 11 }
                    Repeater {
                        model: root.hostState.bluetooth_devices || []
                        MenuButton {
                            required property var modelData
                            label: "[ " + (modelData.connected ? "DISCONNECT" : "CONNECT") + " ] " + modelData.name
                            onActivated: root.hostAction(modelData.connected ? "bluetooth-disconnect" : "bluetooth-connect", modelData.address)
                        }
                    }
                    Text {
                        visible: !(root.hostState.bluetooth_devices || []).length
                        text: "-- nenhum dispositivo emparelhado --"
                        color: root.textDim; font.family: "monospace"; font.pixelSize: 11
                    }
                }

                    Column {
                    width: parent.width
                    spacing: 6
                    visible: root.popupKind === "audio"
                    Text { text: "OUTPUT :: " + root.volumeText; color: root.textDim; font.family: "monospace"; font.pixelSize: 12 }
                    MenuButton { label: "[ + 5% ] aumentar volume"; accent: true; onActivated: root.localAction(["/usr/bin/wpctl", "set-volume", "-l", "1", "@DEFAULT_AUDIO_SINK@", "5%+"]) }
                    MenuButton { label: "[ - 5% ] diminuir volume"; onActivated: root.localAction(["/usr/bin/wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", "5%-"]) }
                    MenuButton { label: "[ MUTE ] alternar som"; onActivated: root.localAction(["/usr/bin/wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "toggle"]) }
                    MenuButton { label: "[ MIXER ] controlo avançado"; onActivated: root.localAction(["/usr/bin/pavucontrol"]) }
                }

                    Column {
                    width: parent.width
                    spacing: 6
                    visible: root.popupKind === "battery"
                    Text { text: "BATTERY :: " + root.batteryText; color: root.textMain; font.family: "monospace"; font.pixelSize: 14 }
                    Rectangle { width: parent.width; height: 8; radius: 4; color: "#26343a"
                        Rectangle { height: parent.height; radius: 4; color: root.cyan; width: parent.width * Math.max(0, Math.min(100, parseInt(root.batteryText) || 0)) / 100 }
                    }
                    Text { text: "POWER PROFILE :: managed by Host"; color: root.textDim; font.family: "monospace"; font.pixelSize: 11 }
                    Text { text: "GPU PROFILE :: HYBRID"; color: root.cyan; font.family: "monospace"; font.pixelSize: 12 }
                    MenuButton { label: "[ HYBRID ] AMD display + NVIDIA on demand"; accent: true }
                    Text { text: "AMD / NVIDIA primary require a new admitted session profile"; color: root.textDim; wrapMode: Text.WordWrap; width: parent.width; font.family: "monospace"; font.pixelSize: 10 }
                    }
                }
            }
        }
    }
}
