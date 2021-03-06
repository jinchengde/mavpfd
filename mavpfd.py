#!/usr/bin/env python

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from __future__ import print_function

from functools import partial

from pymavlink import mavutil, mavwp
import sys
import time
import threading
import optparse
import math
import yaml
import json

from multiprocessing import Process, freeze_support, Pipe, Semaphore, Event, Lock, Queue

from vehicle import Status_Notify, EKF_STATUS, VIBRATION, GPS_RAW_INT, Attitude, VFR_HUD, Global_Position_INT, NAV_Controller_Output, CMD_Ack, MISSION_CURRENT, BatteryInfo, FlightState, WaypointInfo, FPS, Vehicle_Status

from PyQt5.QtGui import QGuiApplication
from PyQt5.QtCore import QUrl, QTimer
from PyQt5.QtQml import QQmlApplicationEngine

EKF_ATTITUDE = 1
EKF_VELOCITY_HORIZ = 2
EKF_VELOCITY_VERT = 4
EKF_POS_HORIZ_REL = 8
EKF_POS_HORIZ_ABS = 16
EKF_POS_VERT_ABS = 32
EKF_POS_VERT_AGL = 64
EKF_CONST_POS_MODE = 128
EKF_PRED_POS_HORIZ_REL = 256
EKF_PRED_POS_HORIZ_ABS = 512
EKF_UNINITIALIZED = 1024
class Connection(object):
    '''mavlink connection'''
    def __init__(self, addr):
        self._addr = addr
        self._active = False
        self._last_packet_received = 0
        self._last_attitude_received = 0
        self._last_vfr_hud_received = 0
        self._last_global_position_int = 0
        self._last_mav_controller_output = 0
        self._last_gps_raw_int = 0
        self._last_msg_send = 0
        self._last_connection_attempt = 0
        self._msglist = []
        self._wplist = False

    def clearMsgList(self):
        # clean the msg list in function, cant clear it directly
        self._msglist = []

    def open(self):
        try:
            '''open mavlink connection'''
            print("Opening connection to %s" % (self._addr,))
            self._mav = mavutil.mavlink_connection(self._addr, baud=115200)
            self._active = True
            self._last_packet_received = time.time()
            return
        except Exception as e:
            print("Connection to (%s) failed: %s" % (self._addr, str(e)))

    def close(self):
        '''close mavlink connection'''
        self._mav.close()
        self._active = False

    @property
    def active(self):
        '''active property'''
        return self._active
        
    @active.setter
    def active(self, value):
        if value == True or value == False:
            self._active = value     

    @property
    def wplist(self):
        '''active property'''
        return self._wplist
        
    @wplist.setter
    def wplist(self, value):
        if value == True or value == False:
            self._wplist = value   

class Link(object):
    '''mavlink connect maintain'''
    def __init__(self, addrs, child_pipe_send):
        self._addrs = addrs
        self._child_pipe_send = child_pipe_send
        self._conns = []
        self._connection_maintenance_target_should_live = True
        self._inactivity_timeout = 10
        self._reconnect_interval = 5
        self._fps = 10.0
        self._sendDelay = (1.0/self._fps)*0.9
        self._wp_count = 0
        self._expected_count = 0
        self._wp_received = {}
        self._wp_requested = {}
        self._get_mission_item = False
        self._current_seq = 0
        self._get_system_info = False

    def maintain_connections(self):
        '''reconnect the mavlink'''
        now = time.time()
        for conn in self._conns:
            if not conn.active:
                continue
            if now - conn._last_packet_received > self._inactivity_timeout:
                print("Connection (%s) timed out" % (conn._addr))
                conn.close()
        for conn in self._conns:
            if not conn.active:
                if now - conn._last_connection_attempt > self._reconnect_interval:
                    conn._last_connection_attempt = now
                    conn.open()                    
        time.sleep(0.1)

    def create_connections(self):
        for addr in self._addrs:
            print("Creating connection (%s)" % addr)
            self._conns.append(Connection(addr))

    def send_messages(self):
        '''send msg to qml process''' 
        for conn in self._conns:
            if (time.time() - conn._last_msg_send) > self._sendDelay and len(conn._msglist) > 0:
                self._child_pipe_send.send(conn._msglist)
                conn.clearMsgList()
                conn._last_msg_send = time.time()
            else:
                continue

    def get_wp_list(self, conn):
        self._wp = mavwp.MAVWPLoader()
        conn._mav.waypoint_request_list_send()

    def missing_wps_to_request(self):
        ret = []
        tnow = time.time()
        next_seq = self._wp_count
        for i in range(self._expected_count):
            seq = next_seq+i
            if seq+1 > self._expected_count:
                continue
            if seq in self._wp_requested and tnow - self._wp_requested[seq] < 2:
                continue
            ret.append(seq)
        return ret

    def send_wp_requests(self, conn, wps=None):
        '''send waypoint item request'''
        if wps is None:
            self._wp_count = 0
            self._wp_received = {}
            self._wp_requested = {}
            wps = self.missing_wps_to_request()
        for seq in wps:
            conn._mav.waypoint_request_send(seq)

    def send_mission_ack(self, conn):
        '''send waypoint mission ack'''
        conn._mav.mav.mission_ack_send(conn._mav.target_system, conn._mav.target_component, mavutil.mavlink.MAV_CMD_ACK_OK) 

    def wp_from_mission_item_int(self, wp):
        '''convert a MISSION_ITEM_INT to a MISSION_ITEM'''
        wp2 = mavutil.mavlink.MAVLink_mission_item_message(wp.target_system,
                                                           wp.target_component,
                                                           wp.seq,
                                                           wp.frame,
                                                           wp.command,
                                                           wp.current,
                                                           wp.autocontinue,
                                                           wp.param1,
                                                           wp.param2,
                                                           wp.param3,
                                                           wp.param4,
                                                           wp.x*1.0e-7,
                                                           wp.y*1.0e-7,
                                                           wp.z)
        # preserve srcSystem as that is used for naming waypoint file
        wp2._header.srcSystem = wp.get_srcSystem()
        wp2._header.srcComponent = wp.get_srcComponent()
        return wp2

    def handle_messages(self):
        '''receive msg from mavlink''' 
        now = time.time()
        packet_received = False
        for conn in self._conns:
            if not conn.active:
                continue
            m = None
            try:
                m = conn._mav.recv_msg()
            except Exception as e:
                print("Exception receiving message on addr(%s): %s" % (str(conn.addr),str(e)))
                conn.close()

            if m is not None:
                conn._last_packet_received = now
                packet_received = True
                if m._type == 'ATTITUDE':
                    if now - conn._last_attitude_received > 0.1:
                        conn._last_attitude_received = now
                        conn._msglist.append(Attitude(m))
                elif m._type == 'VFR_HUD':
                    if now - conn._last_vfr_hud_received > 0.1:
                        conn._last_vfr_hud_received = now
                        conn._msglist.append(VFR_HUD(m))
                elif m._type == 'GLOBAL_POSITION_INT':
                    if now - conn._last_global_position_int > 0.1:
                        conn._last_global_position_int = now
                        conn._msglist.append(Global_Position_INT(m))
                elif m._type == 'NAV_CONTROLLER_OUTPUT':
                    if now - conn._last_mav_controller_output > 0.1:
                        conn._last_mav_controller_output = now
                        conn._msglist.append(NAV_Controller_Output(m))
                elif m._type == 'HEARTBEAT':
                    flightmode = mavutil.mode_string_v10(m)
                    if flightmode == 'AUTO':
                        if conn.wplist == False:
                            self.get_wp_list(conn)
                            conn.wplist = True
                    arm_disarm = conn._mav.motors_armed()
                    target_system = conn._mav.target_system
                    target_component = conn._mav.target_component
                    if self._get_system_info == False:
                        for i in range(0, 3):
                            conn._mav.mav.request_data_stream_send(target_system, target_component,
                                                               mavutil.mavlink.MAV_DATA_STREAM_ALL, 4, 1)
                    self._get_system_info = True
                    conn._msglist.append(FlightState(flightmode, arm_disarm, target_system, target_component))
                elif m._type == 'COMMAND_ACK':
                    conn._msglist.append(CMD_Ack(m))
                elif m._type in ['WAYPOINT_COUNT','MISSION_COUNT']:
                    self._expected_count = m.count
                    self.send_wp_requests(conn)
                elif m._type in ['WAYPOINT', 'MISSION_ITEM', 'MISSION_ITEM_INT']:
                    if m.get_type() == 'MISSION_ITEM_INT':
                        if getattr(m, 'mission_type', 0) != 0:
                            # this is not a mission item, likely fence
                            return
                        # our internal structure assumes MISSION_ITEM'''
                        m = self.wp_from_mission_item_int(m)
                    if m.seq < self._wp_count:
                        #print("DUPLICATE %u" % m.seq)
                        return
                    if m.seq+1 > self._expected_count:
                        return
                    if m.seq + 1 == self._expected_count:
                        self.send_mission_ack(conn)
                        self._get_mission_item = True
                    self._wp_received[m.seq] = m    
                    conn._msglist.append(WaypointInfo(m)) 
                    if self._get_mission_item == True:
                        conn._msglist.append(Status_Notify(Status_Notify.WAYPOINT_RECEIVED))
                elif m._type == 'MISSION_CURRENT':
                    # if m.seq == self._current_seq:
                    #     continue
                    if len(self._wp_received) != 0:
                        self._current_seq = m.seq
                        conn._msglist.append(MISSION_CURRENT(m.seq, self._wp_received[m.seq].x, self._wp_received[m.seq].y, self._wp_received[m.seq].z, self._wp_received[m.seq].command))
                elif m._type == 'EKF_STATUS_REPORT':
                    ekfhealthy = 0
                    ekfatitude = m.flags & 0x01 & EKF_ATTITUDE
                    ekfvelocity = m.flags & 0x06 & (EKF_VELOCITY_HORIZ + EKF_VELOCITY_VERT)
                    ekfposhorizon = ( m.flags & 0x08 & EKF_POS_HORIZ_REL ) or ( m.flags & 0x10 & EKF_POS_HORIZ_ABS)
                    ekfposvert = ( m.flags & 0x20 & EKF_POS_VERT_ABS ) or ( m.flags & 0x40 & EKF_POS_VERT_AGL)
                    ekfconst = m.flags & 0x80 & EKF_CONST_POS_MODE
                    # ekfpredpos = ( m.flags & 0x0100 & EKF_PRED_POS_HORIZ_REL ) or ( m.flags & 0x0200 & EKF_PRED_POS_HORIZ_ABS)
                    ekfunhealthy = m.flags & 0x0400 & EKF_UNINITIALIZED
                    if ekfunhealthy > 0:
                        ekfhealthy = 0
                    elif ekfconst > 0:
                        ekfhealthy = 1
                    elif ekfatitude > 0 and ekfposhorizon > 0 and ekfposvert > 0 and ekfvelocity > 0:
                        ekfhealthy = 2
                    conn._msglist.append(EKF_STATUS(ekfhealthy))
                elif m._type == 'GPS_RAW_INT':
                    if now - conn._last_gps_raw_int > 0.1:
                        conn._last_gps_raw_int = now
                        conn._msglist.append(GPS_RAW_INT(m))
                elif m._type == 'VIBRATION':
                    conn._msglist.append(VIBRATION(m))
                continue

        if not packet_received:
            time.sleep(0.01)

    def init(self):
        self.create_connections()
        self.create_connection_maintenance_thread()
        
    def loop(self):
        self.handle_messages()
        self.send_messages()

    def create_connection_maintenance_thread(self):
        '''create and start helper threads and the like'''
        def connection_maintenance_target():
            while self._connection_maintenance_target_should_live:
                self.maintain_connections()
                time.sleep(0.1)
        connection_maintenance_thread = threading.Thread(target=connection_maintenance_target)
        connection_maintenance_thread.start()

    def run(self):
        self.init()
        while True:
            self.loop()

def update_mav(parent_pipe_recv):
    '''sync data from Pipe'''
    if parent_pipe_recv.poll():
            objList = parent_pipe_recv.recv()
            for obj in objList:
                if isinstance(obj, Attitude):
                    vehicle_status.pitch = obj.pitch
                    vehicle_status.roll = obj.roll
                elif isinstance(obj, VFR_HUD):
                    vehicle_status.airspeed = obj.airspeed
                    vehicle_status.yaw = obj.heading
                    vehicle_status.climbrate = obj.climbRate
                elif isinstance(obj, Global_Position_INT):
                    vehicle_status.alt = obj.relAlt
                    vehicle_status.lat = obj.lat
                    vehicle_status.lon = obj.lon
                elif isinstance(obj, NAV_Controller_Output):
                    vehicle_status.nav_pitch = obj.nav_pitch
                    vehicle_status.nav_roll = obj.nav_roll
                    vehicle_status.nav_yaw = obj.nav_yaw
                    vehicle_status.target_aspd = obj.aspd_error
                    vehicle_status.xtrack_error = obj.xtrack_error
                    vehicle_status.alt_error = obj.alt_error                    
                    if vehicle_status.flightmode != 'AUTO':                        
                        vehicle_status.target_alt_visible = False  
                        vehicle_status.target_alt = obj.alt_error                      
                    else: 
                        vehicle_status.wp_dist = obj.wp_dist
                        if vehicle_status.mission_cmd == MISSION_CURRENT.MAV_CMD_NAV_LAND:
                            vehicle_status.ils_visible = True
                        else:
                            vehicle_status.ils_visible = False     
                elif isinstance(obj, FlightState):
                    vehicle_status.flightmode = obj.mode
                    vehicle_status.arm_disarm = obj.arm_disarm
                    vehicle_status.target_system = obj.target_system
                    vehicle_status.target_component = obj.target_component
                elif isinstance(obj, MISSION_CURRENT):
                    if vehicle_status.flightmode == 'AUTO':
                        vehicle_status.target_alt = obj.z
                        vehicle_status.target_alt_visible = True
                        vehicle_status.mission_cmd = obj.cmd
                        vehicle_status.mission_seq = obj.seq
                elif isinstance(obj, EKF_STATUS):
                    vehicle_status.ekf_healthy = obj.healthy
                elif isinstance(obj, GPS_RAW_INT):
                    vehicle_status.gps_visible = obj.satellites_visible
                    vehicle_status.gps_lock_type = obj.fix_type
                elif isinstance(obj, VIBRATION):
                    if obj.x > 0.6 or obj.y > 0.6 or obj.z > 0.6:
                        vehicle_status.vibration_level = 2
                    elif obj.x > 0.3 or obj.y > 0.3 or obj.z > 0.3:
                        vehicle_status.vibration_level = 1
                    else:
                        vehicle_status.vibration_level = 0
                elif isinstance(obj, WaypointInfo):
                    if vehicle_status.wp_received_flag != True:
                        vehicle_status._wp_received[obj.seq] = obj
                elif isinstance(obj, Status_Notify):
                    vehicle_status.wp_received_flag = True

                # elif isinstance(obj, CMD_Ack):
                #     if obj.cmd == MAV_CMD_COMPONENT_ARM_DISARM:
                #         vehicle_status._arm_disarm = obj.result
                #         print(obj.result)

def childProcessRun(parm, p):
    parent_pipe_recv,child_pipe_send = p
    parent_pipe_recv.close()
    if len(parm) == 0:
        print("Insufficient arguments")
        sys.exit(1)
    hub = Link(parm, child_pipe_send)    
    hub.run()    

if __name__ == '__main__':
    # parser = optparse.OptionParser("mavpfd.py [options]")
    # (opts, parm) = parser.parse_args()
    file = open('config.yaml')
    data = file.read()
    yaml_reader = yaml.full_load(data)
    parm = []
    if yaml_reader.__contains__('udp'):
        str_conn = 'udp:' + str(yaml_reader['udp']['host']) + ":" + str(yaml_reader['udp']['port'])
        parm.append(str_conn)
    elif yaml_reader.__contains__('serial'):
        str_conn = str(yaml_reader['serial']['com'])
        parm.append(str_conn)

    parent_pipe_recv,child_pipe_send = Pipe()
    childProcess = Process(target=childProcessRun, args=((parm, (parent_pipe_recv,child_pipe_send))))
    childProcess.start()
    child_pipe_send.close()

    vehicle_status = Vehicle_Status()

    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine(parent=app)
    context = engine.rootContext()
    context.setContextProperty("pfd", vehicle_status)
    engine.load(QUrl('qml/PFD.qml'))

    timer = QTimer(interval=100)
    while parent_pipe_recv.poll(): #flush pipe data
        objList = parent_pipe_recv.recv()
    timer.timeout.connect(partial(update_mav, parent_pipe_recv))
    timer.start()

    sys.exit(app.exec_())



