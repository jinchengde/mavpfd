import "EFIS/EADI"

import QtQuick 2.15
import QtQuick.Window 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls 2.15

Window {
    id: window
    visible: true
    minimumWidth: 310
    minimumHeight: 310
    //visibility: Window.Maximized
    title: "Primary Flight Display"
    color: "#ffffff"

    Item {
        id: container
        // property double scaleRatio: 3.05 * Math.min(height / 1080, width / 1920)

        anchors {
            fill: parent
            // margins: 16
        }

        Row {
            anchors.centerIn: parent
            // spacing: 8
            // scale: container.scaleRatio

            Rectangle {
                // width: 310
                // height: 310
                radius: 6
                color: "#000000"

                ElectronicAttitudeDirectionIndicator {
                    anchors.centerIn: parent
                    // scaleRatio: container.scaleRatio

                    adi.roll: pfd.roll
                    adi.fdRoll: pfd.nav_roll
                    adi.pitch: pfd.pitch
                    adi.fdPitch: pfd.nav_pitch
                    hsi.heading: pfd.yaw
                    hsi.bugValue: pfd.nav_yaw
                    asi.airspeed: pfd.airspeed
                    alt.altitude: pfd.alt
                    vsi.climbRate: pfd.climbrate
                    labels.flightMode: pfd.flightmode
                    labels.armstatus: pfd.arm_disarm
                    alt.bugValue: pfd.target_alt
                    labels.altitudeBugVisible: pfd.target_alt_visible
                    labels.altitudeBug: pfd.target_alt
                    asi.bugValue: pfd.target_aspd
                    labels.ekfstatus : pfd.ekf_healthy
                    labels.gpsFixed: pfd.gps_lock_type
                    adi.dotH: pfd.xtrack_error
                    adi.dotV: pfd.alt_error
                    adi.dotHVisible: pfd.ils_visible
                    adi.dotVVisible: pfd.ils_visible
                    labels.vibrationLevel: pfd.vibration_level
                }
            }
        }
    }
}