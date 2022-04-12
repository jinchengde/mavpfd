import QtQuick 2.0

Rectangle {
    width: 300
    height: 300
    color: "cyan"
    Text {
        text: vehicle_status.pitch.toFixed(5)
        // text: "hello world"
        anchors.centerIn: parent
    }    
}