import QtQuick 2.15

Item {
    id: root
    width: 300
    height: 300
    clip: true

    property double heading: 0
    property double course: 0
    property double bearing: 0
    property double deviation: 0
    property double distance: 0
    property double headingBug: 0
    property bool distanceVisible: false
    property bool wp_received_flag: false
    property int cdiMode: 0 // 0->OFF, 1->TO, 2->FROM
    property int sequence: 0



    // property var pfd

    property alias labels: labels

    readonly property double pixelPerDeviation: 52.5

    onHeadingChanged: update()
    onDistanceChanged: update()

    function update() {
        canvas.requestPaint()
    }

    FontLoader {
        source: "../../Resources/Fonts/Courier Std Bold.otf"
    }

    Canvas {
        id: canvas
        x: 0
        y: 0
        width: 300
        height: 300
        antialiasing: true
        clip: true

        onPaint: {
            if(wp_received_flag == true) {
                var data = pfd.wp_received()
                var ctx = getContext('2d')
                ctx.reset()
                ctx.lineWidth = 2
                ctx.strokeStyle = "green"
                ctx.beginPath()
                var value=0
                var pointx= 0
                var pointy=0
                var pointx_pre=0
                var pointy_pre=0
                var radius=5
                var startangle=-180
                var endangle=180
                ctx.translate(150, 150)
                ctx.rotate((-heading)*Math.PI/180)
                for(var key in data){                    
                    value = data[key]
                    const point = value.split(':')
                    pointx = parseInt(point[0])
                    pointy = parseInt(point[1])
                    ctx.moveTo(pointx, pointy)
                    ctx.arc(pointx, pointy, radius, (startangle)*(Math.PI/180), (endangle)*(Math.PI/180), false) //x, y, radius, startAngle, endAngle, anticlockwise
                    ctx.fillStyle = "green"
                    ctx.fill()
                    if(key == 0)
                    {
                        pointx_pre = pointx
                        pointy_pre = pointy
                        continue
                    }
                    ctx.moveTo(pointx_pre, pointy_pre)
                    ctx.lineTo(pointx, pointy)
                    pointx_pre = pointx
                    pointy_pre = pointy                    
                }
                
                ctx.stroke()   
            }             
        }
    }

    CustomImage {
        id: back
        source: "../../Resources/ehsi/ehsi_back.svg"
        width: 300
        height: 300
    }

    // // CustomImage {
    // //     id: devScale
    // //     rotation: -heading + course
    // //     source: "../../Resources/ehsi/ehsi_dev_scale.svg"
    // //     width: 300
    // //     height: 300
    // //     visible: cdiMode === 1 || cdiMode === 2
    // // }

    // // CustomImage {
    // //     id: devBar
    // //     rotation: -heading + course
    // //     transform: Translate {
    // //         x: pixelPerDeviation * deviation * Math.cos((-heading + course)* Math.PI / 180.0)
    // //         y: pixelPerDeviation * deviation * Math.sin((-heading + course)* Math.PI / 180.0)
    // //     }
    // //     source: "../../Resources/ehsi/ehsi_dev_bar.svg"
    // //     width: 300
    // //     height: 300
    // //     visible: cdiMode === 1 || cdiMode === 2
    // // }

    // // CustomImage {
    // //     id: brgArrow
    // //     rotation: -heading + bearing
    // //     source: "../../Resources/ehsi/ehsi_brg_arrow.svg"
    // //     width: 300
    // //     height: 300
    // // }

    // // CustomImage {
    // //     id: crsArrow
    // //     rotation: -heading + course
    // //     source: "../../Resources/ehsi/ehsi_crs_arrow.svg"
    // //     width: 300
    // //     height: 300
    // // }

    // // CustomImage {
    // //     id: cdiTo
    // //     rotation: -heading + course
    // //     transform: Translate {
    // //         x: pixelPerDeviation * deviation * Math.cos((-heading + course)* Math.PI / 180.0)
    // //         y: pixelPerDeviation * deviation * Math.sin((-heading + course)* Math.PI / 180.0)
    // //     }
    // //     source: "../../Resources/ehsi/ehsi_cdi_to.svg"
    // //     width: 300
    // //     height: 300
    // //     visible: cdiMode === 1
    // // }

    // // CustomImage {
    // //     id: cdiFrom
    // //     rotation: -heading + course
    // //     transform: Translate {
    // //         x: pixelPerDeviation * deviation * Math.cos((-heading + course)* Math.PI / 180.0)
    // //         y: pixelPerDeviation * deviation * Math.sin((-heading + course)* Math.PI / 180.0)
    // //     }
    // //     source: "../../Resources/ehsi/ehsi_cdi_from.svg"
    // //     width: 300
    // //     height: 300
    // //     visible: cdiMode === 2
    // // }

    // // CustomImage {
    // //     id: mask
    // //     source: "../../Resources/ehsi/ehsi_mask.svg"
    // //     width: 300
    // //     height: 300
    // // }

    CustomImage {
        id: hdgScale
        source: "../../Resources/ehsi/ehsi_hdg_scale.svg"
        rotation: -heading
        width: 300
        height: 300
    }

    CustomImage {
        id: hdgBug
        rotation: -heading + headingBug
        source: "../../Resources/ehsi/ehsi_hdg_bug.svg"
        width: 300
        height: 300
    }

    CustomImage {
        id: mark
        source: "../../Resources/ehsi/ehsi_mark.svg"
        width: 300
        height: 300
    }

    Labels {
       id: labels
       headingBug: root.headingBug
       course: root.course
       distance: root.distance
       sequence: root.sequence
       distanceVisible: root.distanceVisible
    }

}
