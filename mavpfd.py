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

from multiprocessing import Process, freeze_support, Pipe, Semaphore, Event, Lock, Queue

from vehicle import Attitude, VFR_HUD, Global_Position_INT, NAV_Controller_Output, CMD_Ack, BatteryInfo, FlightState, WaypointInfo, FPS, Vehicle_Status

from PyQt5.QtGui import QGuiApplication
from PyQt5.QtQuick import QQuickView
from PyQt5.QtCore import QUrl, QTimer
from PyQt5.QtQml import QQmlApplicationEngine

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
        for i in range(5):
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
        tnow = time.time()
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
                    if conn.wplist == False and flightmode == 'AUTO':
                        self.get_wp_list(conn)
                        conn.wplist = True
                    arm_disarm = conn._mav.motors_armed()
                    target_system = conn._mav.target_system
                    target_component = conn._mav.target_component
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
                    self._wp_received[m.seq] = m
                
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
                elif isinstance(obj, NAV_Controller_Output):
                    vehicle_status.nav_pitch = obj.nav_pitch
                    vehicle_status.nav_roll = obj.nav_roll
                    vehicle_status.nav_yaw = obj.nav_yaw
                    vehicle_status.target_alt = obj.alt_error
                    vehicle_status.target_aspd = obj.aspd_error
                elif isinstance(obj, FlightState):
                    vehicle_status.flightmode = obj.mode
                    vehicle_status.arm_disarm = obj.arm_disarm
                    vehicle_status.target_system = obj.target_system
                    vehicle_status.target_component = obj.target_component

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
    parser = optparse.OptionParser("mavpfd.py [options]")
    (opts, parm) = parser.parse_args()

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
    timer.timeout.connect(partial(update_mav, parent_pipe_recv))
    timer.start()

    sys.exit(app.exec_())



