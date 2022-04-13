#!/usr/bin/env python

from __future__ import print_function

from functools import partial

from pymavlink import mavutil
import sys
import time
import threading
import optparse
import math

from multiprocessing import Process, freeze_support, Pipe, Semaphore, Event, Lock, Queue

from vehicle import Attitude, VFR_HUD, Global_Position_INT, BatteryInfo, FlightState, WaypointInfo, FPS, Vehicle_Status

from PyQt5.QtGui import QGuiApplication
from PyQt5.QtQuick import QQuickView
from PyQt5.QtCore import QUrl, QTimer

class Connection(object):
    '''mavlink connection'''
    def __init__(self, addr):
        self._addr = addr
        self._active = False
        self._last_packet_received = 0
        self._last_msg_send = 0
        self._last_connection_attempt = 0
        self._msglist = []

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
                    conn._msglist.append(Attitude(m))
                    # print("Snd %f"%m.pitch)
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
    if parent_pipe_recv.poll(0.001):
            objList = parent_pipe_recv.recv()
            for obj in objList:
                if isinstance(obj,Attitude):
                    vehicle_status.pitch = obj.pitch
                    # print("Rcv %f"%obj.pitch)

def childProcessRun(parm, p):
    parent_pipe_recv,child_pipe_send = p
    parent_pipe_recv.close()
    hub = Link(parm, child_pipe_send)
    if len(parm) == 0:
        print("Insufficient arguments")
        sys.exit(1)
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
    view = QQuickView()
    view.setResizeMode(QQuickView.SizeRootObjectToView)
    ctxt = view.rootContext()
    ctxt.setContextProperty('vehicle_status', vehicle_status)
    view.setSource(QUrl('view.qml'))
    view.show()

    timer = QTimer(interval=500)
    timer.timeout.connect(partial(update_mav, parent_pipe_recv))
    timer.start()

    sys.exit(app.exec_())



