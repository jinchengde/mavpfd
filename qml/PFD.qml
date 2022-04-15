import "EFIS/EADI"

import QtQuick 2.15
import QtQuick.Window 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls 2.15

Window {
    id: window
    visible: true
    minimumWidth: 600
    minimumHeight: 400
    //visibility: Window.Maximized
    title: "Primary Flight Display"
    color: "#ffffff"

    Item {
        id: container
        property double scaleRatio: 3.05 * Math.min(height / 1080, width / 1920)

        anchors {
            fill: parent
            margins: 16
        }

        Row {
            anchors.centerIn: parent
            spacing: 8
            scale: container.scaleRatio

            Rectangle {
                width: 310
                height: 310
                radius: 6
                color: "#000000"

                ElectronicAttitudeDirectionIndicator {
                    anchors.centerIn: parent
                    scaleRatio: container.scaleRatio

                    adi.roll: pfd.roll
                    adi.pitch: pfd.pitch
                    hsi.heading: pfd.yaw
                    asi.airspeed: pfd.airspeed
                    alt.altitude: pfd.alt
                    vsi.climbRate: pfd.climbrate
                }
            }
        }
    }
}