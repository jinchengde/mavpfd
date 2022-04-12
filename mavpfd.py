#!/usr/bin/env python

from __future__ import print_function

from pymavlink import mavutil
import sys
import time
import threading
import optparse
import math

from multiprocessing import Process, freeze_support, Pipe, Semaphore, Event, Lock, Queue

from vehicle import Attitude, VFR_HUD, Global_Position_INT, BatteryInfo, FlightState, WaypointInfo, FPS, Vehicle_Status

from PySide2.QtWidgets import QApplication
from PySide2.QtQuick import QQuickView
from PySide2.QtCore import QUrl
from PySide2.QtQml import QQmlApplicationEngine
from PySide2.QtGui import QGuiApplication
class Connection(object):
    def __init__(self, addr):
        self._addr = addr
        self._active = False
        self._last_packet_received = 0
        self._last_msg_send = 0
        self._last_connection_attempt = 0
        self._msglist = []

    def open(self):
        try:
            '''open mavlink connection'''
            print("Opening connection to %s" % (self._addr,))
            self._mav = mavutil.mavlink_connection(self._addr, baud=115200)
            self._active = True
            self._last_packet_received = time.time() # lie

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

class Link(object):
    def __init__(self, addrs):
        self._addrs = addrs
        self._conns = []
        self._connection_maintenance_target_should_live = True
        self._inactivity_timeout = 10
        self._reconnect_interval = 5
        self._fps = 10.0
        self._sendDelay = (1.0/self._fps)*0.9
        self._child_pipe_recv,self._parent_pipe_send = Pipe()
        self._close_event = Event()
        self._close_event.clear()
        # self._vehicle_status = Vehicle_Status()

        self._child = Process(target=self.update_mav)
        self._child.start()
        self._child_pipe_recv.close()
        

    def update_mav(self):
        '''sync data from Pipe'''
        self._parent_pipe_send.close()
        while self._child_pipe_recv.poll():
                objList = self._child_pipe_recv.recv()
                for obj in objList:
                    if isinstance(obj,Attitude):
                        # self._vehicle_status.set_pitch(obj.pitch)
                        print(obj.pitch*180/math.pi)
                time.sleep(0.1)                
        
    def maintain_connections(self):
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
        for conn in self._conns:
            if (time.time() - conn._last_msg_send) > self._sendDelay:
                self._parent_pipe_send.send(conn._msglist)
                conn._msgList = []
                conn._last_msg_send = time.time()
            else:
                continue

    def handle_messages(self):
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
                    conn._msglist.append(Attitude(m))
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

def childProcessRun(args):
    for x in args:
        print(x)
    hub = Link(args)
    if len(args) == 0:
        print("Insufficient arguments")
        sys.exit(1)
    hub.run()
    

if __name__ == '__main__':
    parser = optparse.OptionParser("mavpfd.py [options]")
    (opts, parm) = parser.parse_args()
    
    childProcess = Process(target=childProcessRun, args=(parm,))
    childProcess.start()
    
    vehicle_status = Vehicle_Status()
    app = QApplication([])
    view = QQuickView()
    context = view.rootContext()
    context.setContextProperty("vehicle_status", vehicle_status)
    url = QUrl("view.qml")

    view.setSource(url)
    view.show()
    app.exec_()

