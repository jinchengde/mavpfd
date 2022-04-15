class Attitude():
    '''The current Attitude Data'''
    def __init__(self, attitudeMsg):
        self.pitch = attitudeMsg.pitch
        self.roll = attitudeMsg.roll
        self.yaw = attitudeMsg.yaw

class VFR_HUD():
    '''HUD Information.'''
    def __init__(self,hudMsg):
        self.airspeed = hudMsg.airspeed
        self.groundspeed = hudMsg.groundspeed
        self.heading = hudMsg.heading
        self.throttle = hudMsg.throttle
        self.climbRate = hudMsg.climb
        self.alt = hudMsg.alt
        
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
        
class FlightState():
    '''Mode and arm state.'''
    def __init__(self,mode,armState):
        self.mode = mode
        self.armState = armState
        
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

    def __init__(self, parent=None):
        super(Vehicle_Status, self).__init__(parent)
        self._pitch = 0.0
        self._roll = 0.0
        self._yaw = 0
        self._alt = 0.0
        self._climbrate = 0.0
        self._airspeed = 0.0

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
        self._alt = value
        self.alt_changed.emit(self._alt)

    @QtCore.pyqtProperty(float, notify=climbrate_changed)
    def climbrate(self):
        return self._climbrate

    @climbrate.setter
    def climbrate(self, value):
        self._climbrate = value
        self.climbrate_changed.emit(self._climbrate)

    @QtCore.pyqtProperty(float, notify=airspeed_changed)
    def airspeed(self):
        return self._airspeed
    
    @airspeed.setter
    def airspeed(self, value):
        self._airspeed = value
        self.airspeed_changed.emit(self._airspeed)

    


