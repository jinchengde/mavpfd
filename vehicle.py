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

class Attitude():
    '''The current Attitude Data'''
    def __init__(self, attitudeMsg):
        self.pitch = attitudeMsg.pitch
        self.roll = attitudeMsg.roll
        self.yaw = attitudeMsg.yaw

class VFR_HUD():
    '''HUD Information.'''
    def __init__(self, hudMsg):
        self.airspeed = hudMsg.airspeed
        self.groundspeed = hudMsg.groundspeed
        self.heading = hudMsg.heading
        self.throttle = hudMsg.throttle
        self.climbRate = hudMsg.climb
        self.alt = hudMsg.alt

class NAV_Controller_Output():
    '''fixed wing navigation and position controller'''
    def __init__(self, controller_output):
        self.nav_roll = controller_output.nav_roll
        self.nav_pitch = controller_output.nav_pitch
        self.nav_yaw = controller_output.target_bearing
        self.alt_error = controller_output.alt_error
        self.aspd_error = controller_output.aspd_error
        self.xtrack_error = controller_output.xtrack_error
        
class Global_Position_INT():
    '''Altitude relative to ground (GPS).'''
    def __init__(self,gpsINT):
        self.relAlt = gpsINT.relative_alt/1000.0
        # self.curTime = curTime
        
class BatteryInfo():
    '''Voltage, current and remaning battery.'''
    def __init__(self,batMsg):
        self.voltage = batMsg.voltage_battery/1000.0 # Volts
        self.current = batMsg.current_battery/100.0 # Amps
        self.batRemain = batMsg.battery_remaining # %

class MISSION_CURRENT():
    '''mission status'''
    MAV_CMD_NAV_WAYPOINT = 16
    MAV_CMD_NAV_LOITER_UNLIM = 17
    MAV_CMD_NAV_LOITER_TURNS = 18
    MAV_CMD_NAV_LOITER_TIME = 19
    MAV_CMD_NAV_RETURN_TO_LAUNCH = 20
    MAV_CMD_NAV_LAND = 21
    MAV_CMD_NAV_TAKEOFF = 22
    MAV_CMD_NAV_LAND_LOCAL = 23
    MAV_CMD_NAV_TAKEOFF_LOCAL =  24
    MAV_CMD_NAV_FOLLOW = 25
    def __init__(self, seq, x, y, z, cmd):
        self.seq = seq
        self.x = x
        self.y = y
        self.z = z
        self.cmd = cmd
        
class FlightState():
    '''Mode and arm state.'''
    def __init__(self,mode,arm_disarm,target_system, target_component):
        self.mode = mode
        self.arm_disarm = arm_disarm
        self.target_system = target_system
        self.target_component = target_component
        
class WaypointInfo():
    '''Current and final waypoint numbers, and the distance
    to the current waypoint.'''
    def __init__(self,current,final,currentDist,nextWPTime,wpBearing):
        self.current = current
        self.final = final
        self.currentDist = currentDist
        self.nextWPTime = nextWPTime
        self.wpBearing = wpBearing
        
class FPS():
    '''Stores intended frame rate information.'''
    def __init__(self,fps):
        self.fps = fps # if fps is zero, then the frame rate is unrestricted

class CMD_Ack():
    '''command ack message'''
    def __init__(self,ack):
        self.cmd = ack.command
        self.result = ack.result

class EKF_STATUS():
    '''ekf status'''
    def __init__(self, healthy):
        self.healthy = healthy

class GPS_RAW_INT():
    '''gps raw int'''
    GPS_FIX_TYPE_NO_GPS = 0
    GPS_FIX_TYPE_NO_FIX	= 1 
    GPS_FIX_TYPE_2D_FIX	= 2
    GPS_FIX_TYPE_3D_FIX	= 3
    GPS_FIX_TYPE_DGPS = 4
    GPS_FIX_TYPE_RTK_FLOAT = 5	
    GPS_FIX_TYPE_RTK_FIXED = 6	
    GPS_FIX_TYPE_STATIC = 7	
    GPS_FIX_TYPE_PPP = 8 

    def __init__(self, gps_raw_int):
        self.fix_type = gps_raw_int.fix_type
        self.eph = gps_raw_int.eph
        self.epv = gps_raw_int.epv
        self.vel = gps_raw_int.vel
        self.satellites_visible = gps_raw_int.satellites_visible
        
from multiprocessing.sharedctypes import Value
from PyQt5 import QtCore
import math

class Vehicle_Status(QtCore.QObject):
    pitch_changed = QtCore.pyqtSignal(float)
    roll_changed = QtCore.pyqtSignal(float)
    yaw_changed = QtCore.pyqtSignal(int)
    altitude_changed = QtCore.pyqtSignal(float)
    altitude_bug_changed = QtCore.pyqtSignal(float)
    alt_changed = QtCore.pyqtSignal(float)
    climbrate_changed = QtCore.pyqtSignal(float)
    airspeed_changed = QtCore.pyqtSignal(float)
    nav_pitch_changed = QtCore.pyqtSignal(float)
    nav_roll_changed = QtCore.pyqtSignal(float)
    nav_yaw_changed = QtCore.pyqtSignal(int)
    flightmode_changed = QtCore.pyqtSignal(str)
    arm_disarm_changed = QtCore.pyqtSignal(int)
    target_alt_changed = QtCore.pyqtSignal(float)
    target_aspd_changed = QtCore.pyqtSignal(float)
    target_alt_visible_changed = QtCore.pyqtSignal(bool)
    ekf_healthy_changed = QtCore.pyqtSignal(int)
    gps_visible_changed = QtCore.pyqtSignal(int)
    gps_lock_type_changed = QtCore.pyqtSignal(int)
    ils_visible_changed = QtCore.pyqtSignal(bool)
    xtrack_error_changed = QtCore.pyqtSignal(int)
    alt_error_changed = QtCore.pyqtSignal(int)
    mission_cmd_changed = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        super(Vehicle_Status, self).__init__(parent)
        self._pitch = 0.0
        self._roll = 0.0
        self._yaw = 0
        self._alt = 0.0
        self._climbrate = 0.0
        self._airspeed = 0.0
        self._nav_pitch = 0.0
        self._nav_roll = 0.0
        self._nav_yaw = 0
        self._flightmode = ''
        self._arm_disarm = 0
        self._target_alt = 0.0
        self._target_aspd = 0.0
        self._target_system = 0.0
        self._target_component = 0.0
        self._target_alt_visible = False
        self._ekf_healthy = 2
        self._gps_visible = 0
        self._gps_lock_type = 0
        self._gps_lock_type_str = ''
        self._ils_visible = False
        self._alt_error = 0
        self._xtrack_error = 0
        self._mission_cmd = 0

    @QtCore.pyqtProperty(float, notify=pitch_changed)
    def pitch(self):
        return self._pitch
    
    @pitch.setter
    def pitch(self, value):
        self._pitch = value * 180 / math.pi
        self.pitch_changed.emit(self._pitch)

    @QtCore.pyqtProperty(float, notify=pitch_changed)
    def roll(self):
        return self._roll
    
    @roll.setter
    def roll(self, value):
        self._roll = value * 180 / math.pi
        self.roll_changed.emit(self._roll)

    @QtCore.pyqtProperty(int, notify=yaw_changed)
    def yaw(self):
        return self._yaw
    
    @yaw.setter
    def yaw(self, value):
        self._yaw = value
        self.yaw_changed.emit(self._yaw)

    @QtCore.pyqtProperty(float, notify=alt_changed)
    def alt(self):
        return self._alt
    
    @alt.setter
    def alt(self, value):
        if value == -0:
            value = 0
        self._alt = value
        self.alt_changed.emit(self._alt)

    @QtCore.pyqtProperty(float, notify=climbrate_changed)
    def climbrate(self):
        return self._climbrate

    @climbrate.setter
    def climbrate(self, value):
        if value > 6.8:
            self._climbrate = 6.8
        elif value < -6.8:
            self._climbrate = -6.8
        else:
            self._climbrate = value
        self.climbrate_changed.emit(self._climbrate)

    @QtCore.pyqtProperty(float, notify=airspeed_changed)
    def airspeed(self):
        return self._airspeed
    
    @airspeed.setter
    def airspeed(self, value):
        self._airspeed = value
        self.airspeed_changed.emit(self._airspeed)

    @QtCore.pyqtProperty(float, notify=nav_pitch_changed)
    def nav_pitch(self):
        return self._nav_pitch

    @nav_pitch.setter
    def nav_pitch(self, value):
        self._nav_pitch = value
        self.nav_pitch_changed.emit(self._nav_pitch)

    @QtCore.pyqtProperty(float, notify=nav_roll_changed)
    def nav_roll(self):
        return self._nav_roll

    @nav_roll.setter
    def nav_roll(self, value):
        self._nav_roll = value
        self.nav_roll_changed.emit(self._nav_roll)

    @QtCore.pyqtProperty(int, notify=nav_yaw_changed)
    def nav_yaw(self):
        return self._nav_yaw

    @nav_yaw.setter
    def nav_yaw(self, value):
        self._nav_yaw = value
        self.nav_yaw_changed.emit(self._nav_yaw)

    @QtCore.pyqtProperty(str, notify=flightmode_changed)
    def flightmode(self):
        return self._flightmode

    @flightmode.setter
    def flightmode(self, value):
        if self._flightmode == value:
            return
        self._flightmode = value
        self.flightmode_changed.emit(self._flightmode)

    @QtCore.pyqtProperty(int, notify=arm_disarm_changed)
    def arm_disarm(self):
        return self._arm_disarm

    @arm_disarm.setter
    def arm_disarm(self, value):
        if self._arm_disarm == value:
            return
        if value > 0:
            value = 1
        self._arm_disarm = value
        self.arm_disarm_changed.emit(self._arm_disarm)
    
    @QtCore.pyqtProperty(float, notify=target_alt_changed)
    def target_alt(self):
        return self._target_alt

    @target_alt.setter
    def target_alt(self, value):
        if self._flightmode == 'AUTO':
            self._target_alt = value
        else:
            self._target_alt = self._alt + value
        self.target_alt_changed.emit(self._target_alt)

    @QtCore.pyqtProperty(float, notify=target_aspd_changed)
    def target_aspd(self):
        return self._target_aspd

    @target_aspd.setter
    def target_aspd(self, value):
        self._target_aspd = self._airspeed + (value / 100)
        self.target_aspd_changed.emit(self._target_aspd)

    @QtCore.pyqtProperty(int)
    def target_system(self):
        return self._target_system

    @target_system.setter
    def target_system(self, value):
        if self._target_system == value:
            return
        self._target_system = value

    @QtCore.pyqtProperty(int)
    def target_component(self):
        return self._target_component

    @target_component.setter
    def target_component(self, value):
        if self._target_component == value:
            return
        self._target_component = value
    
    @QtCore.pyqtProperty(float, notify=target_alt_visible_changed)
    def target_alt_visible(self):
        return self._target_alt_visible

    @target_alt_visible.setter
    def target_alt_visible(self, value):
        if self._target_alt_visible == value:
            return
        self._target_alt_visible = value
        self.target_alt_visible_changed.emit(self._target_alt_visible)

    @QtCore.pyqtProperty(int, notify=ekf_healthy_changed)
    def ekf_healthy(self):
        return self._ekf_healthy

    @ekf_healthy.setter
    def ekf_healthy(self, value):
        if self._ekf_healthy == value:
            return
        self._ekf_healthy = value
        self.ekf_healthy_changed.emit(self._ekf_healthy)

    @QtCore.pyqtProperty(int, notify=gps_visible_changed)
    def gps_visible(self):
        return self._gps_visible

    @gps_visible.setter
    def gps_visible(self, value):
        if self._gps_visible == value:
            return
        self._gps_visible = value
        self.gps_visible_changed.emit(self._gps_visible)

    @QtCore.pyqtProperty(int, notify=gps_lock_type_changed)
    def gps_lock_type(self):
        return self._gps_lock_type

    @gps_lock_type.setter
    def gps_lock_type(self, value):
        if self._gps_lock_type == value:
            return
        self._gps_lock_type = value
        self.gps_lock_type_changed.emit(self._gps_lock_type)

    @QtCore.pyqtProperty(bool, notify=ils_visible_changed)
    def ils_visible(self):
        return self._ils_visible

    @ils_visible.setter
    def ils_visible(self, value): 
        self._ils_visible = value       
        self.ils_visible_changed.emit(self._ils_visible)

    @QtCore.pyqtProperty(int, notify=xtrack_error_changed)
    def xtrack_error(self):
        return self._xtrack_error

    @xtrack_error.setter
    def xtrack_error(self, value):
        if self._ils_visible == True: 
            self._xtrack_error = value       
            self.xtrack_error_changed.emit(self._xtrack_error)

    @QtCore.pyqtProperty(int, notify=alt_error_changed)
    def alt_error(self):
        return self._alt_error

    @alt_error.setter
    def alt_error(self, value):
        if self._ils_visible == True: 
            self._alt_error = value       
            self.alt_error_changed.emit(self._alt_error)

    @QtCore.pyqtProperty(int, notify=mission_cmd_changed)
    def mission_cmd(self):
        return self._mission_cmd

    @mission_cmd.setter
    def mission_cmd(self, value):
        self._mission_cmd = value       
        self.mission_cmd_changed.emit(self._mission_cmd)

    
    
