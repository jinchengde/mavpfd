import QtQuick 2.0

Item {
    width: 300
    height: 300

    property double airspeedBug: 0
    property double machNumber: 0
    property double altitudeBug: 0
    property bool altitudeBugVisible: false
    property double pressure: 0

    property int ekfstatus: 2
    property int armstatus: 0 //0->disarm, 1->arm
    property int pressureMode: 0 // 0->STD, 1->MB, 2->IN
    property string flightMode: '' // 0->OFF, 1->FD, 2->CMD
    property int speedMode: 0 // 0->OFF, 1->FMC SPD
    property int lnav: 0 // 0->OFF, 1->HDG, 2->NAV, 3->NAV ARM, 4->NAV APR, 5->NAV APR ARM, 6->BC, 7->BC ARM
    property int vnav: 0 // 0->OFF, 1->ALT, 2->IAS, 3->VS, 4->ALT SEL, 5->GS, 6-> GS ARM
    property int gpsFixed: 0

    Text {
        id: altitudeBugText
        x: 228
        y: 21
        width: 36
        height: 18
        font.family: "Courier Std"
        font.pixelSize: altitudeBug.toFixed(0).length < 4 ?  16  :
                        altitudeBug.toFixed(0).length === 4 ? 14  :
                        altitudeBug.toFixed(0).length === 5  ? 12  : 12
        horizontalAlignment: Text.AlignRight
        verticalAlignment: Text.AlignVCenter
        color: "#ff00ff"
        visible: altitudeBugVisible

        antialiasing: true
        text: altitudeBug.toFixed(0)
    }

    // Flight Mode
    Text {
        y: 213
        font.family: "Courier Std"
        font.pixelSize: 16
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        anchors.horizontalCenter: altitudeBugText.horizontalCenter
        color: "#00ff00"
        antialiasing: true
        text: flightMode
    }

    // Arm or Disarm Status
    Text {
        y: 33
        width: 128
        height: 18
        font.family: "Courier Std"
        font.pixelSize: 16
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        anchors.horizontalCenter: parent.horizontalCenter
        color: armstatus === 0 ? "#00ff00" :
                                armstatus === 1? "#FF0000" : ""
        antialiasing: true
        text: armstatus === 0 ? "DISARM" :
                                 armstatus === 1 ? "ARM" : ""

    }

    // Speed Mode
    Text {
        x: 80
        y: 5
        font.family: "Courier Std"
        font.pixelSize: 9
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        color: "#00ff00"
        antialiasing: true
        text: speedMode === 1 ? "FMC SPD" : ""
    }

    // EKF Status
    Text {
        x: 132
        y: 12
        width: 38
        height: 10
        color: ekfstatus === 2 ? "#00FF00" :
                ekfstatus === 1 ? "#FFFF00" :
                ekfstatus === 0 ? "#FF0000" : ""
        font.pixelSize: 16
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        font.family: "Courier Std"
        antialiasing: true
        text: "EKF"
    }

    // GPS Fixed
    Text {
        x: 80
        y: 12
        width: 38
        height: 10
        color: gpsFixed === 0 ? "#FF0000" :
                gpsFixed === 1 ? "#FF0000" :
                gpsFixed === 2 ? "#FFFF00" :
                gpsFixed === 3 ? "#00FF00" :
                gpsFixed === 4 ? "#00FF00" :
                gpsFixed === 5 ? "#00FF00" :
                gpsFixed === 6 ? "#00FF00" :
                gpsFixed === 7 ? "#00FF00" : 
                gpsFixed === 8 ? "#00FF00" : "#FF0000"
        font.pixelSize: gpsFixed === 0 ?  12  :
                        gpsFixed === 1 ?  12  :
                        gpsFixed === 2 ?  12  :
                        gpsFixed === 3 ?  12  :
                        gpsFixed === 4 ?  16  :
                        gpsFixed === 5 ?  12  :
                        gpsFixed === 6 ?  12  :
                        gpsFixed === 7 ?  14  :
                        gpsFixed === 8 ?  16  : 16
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        font.family: "Courier Std"
        antialiasing: true
        text: gpsFixed === 0 ? "NO GPS" :
              gpsFixed === 1 ? "NO FIX" :
              gpsFixed === 2 ? "2D FIX" :
              gpsFixed === 3 ? "3D FIX" :
              gpsFixed === 4 ? "DGPS" :
              gpsFixed === 5 ? "RTK\nFLOAT" :
              gpsFixed === 6 ? "RTK\nFIXED" :
              gpsFixed === 7 ? "STATIC" :
              gpsFixed === 8 ? "PPP" : "NO GPS"
    }

}
