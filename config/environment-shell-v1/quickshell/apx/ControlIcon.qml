import QtQuick
import QtQuick.Controls

Item {
    property url source
    property color tint

    ToolButton {
        anchors.fill: parent
        padding: 0
        focusPolicy: Qt.NoFocus
        hoverEnabled: false
        display: AbstractButton.IconOnly
        icon.source: parent.source
        icon.color: parent.tint
        icon.width: Math.max(18, width)
        icon.height: Math.max(18, height)
        background: Item {}
    }
}
