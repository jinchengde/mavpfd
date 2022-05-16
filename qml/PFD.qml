import "EFIS/EADI"
import "EFIS/EHSI"

import QtQuick 2.15
import QtQuick.Window 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls 2.15

Window {
    id: window
    visible: true
    minimumWidth: 630
    minimumHeight: 320
    //visibility: Window.Maximized
    title: "Primary Flight Display"
    color: "#ffffff"

    Item {
        id: container
        property double scaleRatio: Math.min(height / 320, width / 630)

        anchors {
            fill: parent
            // margins: 4
        }

        Row {
            anchors.centerIn: parent
            spacing: 4
            scale: container.scaleRatio
            // layoutDirection: "RightToLeft"

            Rectangle {
                radius: 6
                color: "#000000"
                id: eadi
                width: 310
                height: 310
                // anchors.left: parent.left
                // anchors.top: parent.top
                // visible: false

                ElectronicAttitudeDirectionIndicator {
                    anchors.centerIn: parent
                    scaleRatio: container.scaleRatio                    

                    adi.roll: pfd.roll
                    adi.fdRoll: pfd.nav_roll
                    adi.pitch: pfd.pitch
                    adi.fdPitch: pfd.nav_pitch
                    adi.dotH: pfd.xtrack_error
                    adi.dotV: pfd.alt_error
                    adi.dotHVisible: pfd.ils_visible
                    adi.dotVVisible: pfd.ils_visible

                    hsi.heading: pfd.yaw
                    hsi.bugValue: pfd.nav_yaw

                    asi.airspeed: pfd.airspeed
                    asi.bugValue: pfd.target_aspd

                    vsi.climbRate: pfd.climbrate
                    
                    alt.bugValue: pfd.target_alt
                    alt.altitude: pfd.alt                    
                    
                    labels.ekfstatus : pfd.ekf_healthy
                    labels.gpsFixed: pfd.gps_lock_type
                    labels.vibrationLevel: pfd.vibration_level
                    labels.flightMode: pfd.flightmode
                    labels.armstatus: pfd.arm_disarm
                    labels.altitudeBugVisible: pfd.target_alt_visible
                    labels.altitudeBug: pfd.target_alt
                }
            }

            Rectangle {
                width: 310
                height: 310
                radius: 6
                color: "#000000"
                visible: true
                id: ehsi

                ElectronicHorizontalSituationIndicator {
                    anchors.centerIn: parent

                    heading: pfd.yaw
                    // course: pfd.course
                    // bearing: pfd.bearing
                    // deviation: pfd.vorDeviation
                    headingBug: pfd.nav_yaw
                    distance: pfd.wp_dist
                    wp_received_flag: pfd.wp_received_flag
                    labels.distanceVisible: pfd.target_alt_visible
                    // pfd: pfd
                    // cdiMode: pfd.courseDeviationIndicatorMode
                }
            }
        
        }
    }
}