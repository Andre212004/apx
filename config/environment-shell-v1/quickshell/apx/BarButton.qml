import QtQuick

Rectangle {
    id: button

    property string label: ""
    property string alternateLabel: ""
    property bool alternateActive: false
    property bool animateActivation: false
    property bool animateDeactivation: false
    property color activeSurface
    property color accentColor
    property color textColor
    readonly property bool visuallyActive: pointer.containsMouse || alternateActive

    signal activated()

    implicitWidth: Math.max(buttonText.implicitWidth, alternateButtonText.implicitWidth) + 22
    implicitHeight: 32
    scale: pointer.pressed ? 0.96 : 1
    radius: 7
    color: visuallyActive ? activeSurface : "transparent"
    border.width: visuallyActive ? 1 : 0
    border.color: accentColor

    Behavior on scale {
        NumberAnimation { duration: 120; easing.type: Easing.OutCubic }
    }

    Text {
        id: buttonText
        anchors.centerIn: parent
        text: button.label
        opacity: button.alternateActive ? 0 : 1
        scale: button.alternateActive ? 0.94 : 1
        color: button.visuallyActive ? button.accentColor : button.textColor
        font.family: "Adwaita Mono"
        font.pixelSize: 13
        font.bold: true

        Behavior on opacity {
            enabled: button.animateActivation || button.animateDeactivation
            NumberAnimation { duration: 110; easing.type: Easing.OutCubic }
        }
        Behavior on scale {
            enabled: button.animateActivation || button.animateDeactivation
            NumberAnimation { duration: 130; easing.type: Easing.OutCubic }
        }
    }

    Text {
        id: alternateButtonText
        anchors.centerIn: parent
        text: button.alternateLabel
        opacity: button.alternateActive ? 1 : 0
        scale: button.alternateActive ? 1 : 0.94
        color: button.visuallyActive ? button.accentColor : button.textColor
        font.family: "Adwaita Mono"
        font.pixelSize: 13
        font.bold: true

        Behavior on opacity {
            enabled: button.animateActivation || button.animateDeactivation
            NumberAnimation { duration: 110; easing.type: Easing.OutCubic }
        }
        Behavior on scale {
            enabled: button.animateActivation || button.animateDeactivation
            NumberAnimation { duration: 130; easing.type: Easing.OutCubic }
        }
    }

    MouseArea {
        id: pointer
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor

        // Finish the click on the permanently mapped bar before the menu
        // changes keyboard focus or layer-shell input regions.
        onClicked: button.activated()
    }
}
