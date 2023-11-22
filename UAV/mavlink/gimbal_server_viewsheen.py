from __future__ import annotations
"""
Viewsheen Gimbal server Component
https://mavlink.io/en/services/gimbal_v2.html
The gimbal protocol allows MAVLink control over the attitude/orientation of cameras (or other sensors) mounted on the drone. The orientation can be: controlled by the pilot in real time 
(e.g. using a joystick from a ground station), set as part of a mission, or moved based on cameras tracking.
The protocol also defines what status information is published for developers, configurators, as well as users of the drone. It additionally provides ways to assign control to different sources.
The protocol supports a number of hardware setups, and enables gimbals with varying capabilities
"""

__all__ = ['NAN', 'GIMBAL_DEVICE_SET_ATTITUDE', 'GIMBAL_MANAGER_SET_MANUAL_CONTROL', 'MAV_CMD_SET_CAMERA_ZOOM',
           'MAV_CMD_IMAGE_START_CAPTURE', 'MAV_CMD_IMAGE_STOP_CAPTURE', 'GimbalServerViewsheen']

import socket

from .component import Component, mavlink_command_to_string
# from viewsheen_sdk.gimbal_cntrl import pan_tilt, snapshot,  zoom, VS_IP_ADDRESS, VS_PORT, KeyReleaseThread
from ..camera_sdks.viewsheen.gimbal_cntrl import pan_tilt, snapshot, zoom, VS_IP_ADDRESS, VS_PORT
from ..logging import LogLevels

# from UAV.imports import *   # TODO why is this relative import on nbdev_export?



# from pymavlink.dialects.v20 import ardupilotmega as mav

NAN = float("nan")
GIMBAL_DEVICE_SET_ATTITUDE = 284  # https://mavlink.io/en/messages/common
GIMBAL_MANAGER_SET_MANUAL_CONTROL = 288  # https://mavlink.io/en/messages/common.html#GIMBAL_MANAGER_SET_MANUAL_CONTROL
MAV_CMD_SET_CAMERA_ZOOM = 531  # https://mavlink.io/en/messages/common.html#MAV_CMD_SET_CAMERA_ZOOM
MAV_CMD_IMAGE_START_CAPTURE = 2000  # https://mavlink.io/en/messages/common.html#MAV_CMD_IMAGE_START_CAPTURE
MAV_CMD_IMAGE_STOP_CAPTURE = 2001  # https://mavlink.io/en/messages/common.html#MAV_CMD_IMAGE_STOP_CAPTURE
class GimbalServerViewsheen(Component):
    """Create a Viewsheen mavlink Camera Server Component for receiving commands from a gimbal on a companion computer or GCS"""

    def __init__(self,
                 source_component: int,  # used for component indication
                 mav_type: int,  # used for heartbeat MAV_TYPE indication
                 loglevel: LogLevels | int = LogLevels.INFO,  # logging level
                 ):
        
        super().__init__( source_component=source_component, mav_type=mav_type, loglevel=loglevel)
        
        self._set_message_callback(self.on_message)
        self.connect()
     
     
    def connect(self, timeout=2):
        """Connect to the viewsheen_sdk gimbal"""
        # # todo,  ping it first to see if gimbal present
        # self.log.error(f" Ping it first before , Connecting to gimbal, doesn't time out if not present")

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(timeout)  # Set a timeout
        try:
            self.sock.connect((VS_IP_ADDRESS, VS_PORT))
        except socket.timeout:
            self.log.error(f"Timeout connecting to gimbal socket")
            return False
        self.log.info(f"Connected to gimbal socket")
        return True
    
    def on_message(self, msg):
        """Callback for a command received from the gimbal"""
        # https://mavlink.io/en/messages/common.html#GIMBAL_DEVICE_SET_ATTITUDE
        # print(f" {msg = }")
        # print(f" {msg.get_type() = }")
        # return False
        if msg.get_type() == "GIMBAL_DEVICE_SET_ATTITUDE" or msg.get_type() == "GIMBAL_MANAGER_SET_ATTITUDE":
            self.set_attitude(msg)
            return False
        elif msg.get_type() == "COMMAND_LONG":
            # print(f"Command  {msg.command = } ")
            if msg.command == MAV_CMD_SET_CAMERA_ZOOM:
                # self.log.info(f"***** Zoom {msg}")
                # print(f"Zoom {msg.param2 = }")
                self.set_zoom(msg)
                return True
            elif msg.command == MAV_CMD_IMAGE_START_CAPTURE:
                self.start_capture()
                return True
            elif msg.command == MAV_CMD_IMAGE_STOP_CAPTURE:
                self.stop_capture()
                return True
            
        else:
            self.log.debug(f"Unknown command {msg.get_type()} received from {msg.get_srcSystem()}/{msg.get_srcComponent()}")
            return False
        
    def set_zoom(self, msg):
        """ Set the viewsheen cameras zoom """
        # print(msg.get_type())
        # print(f"Zoom {msg.param2 = }")
        data = zoom(int(msg.param2))
        self.sock.sendall(data)
        
        
    def start_capture(self):
        """Start image capture sequence."""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_IMAGE_START_CAPTURE
        data = snapshot(1, 0)
        self.sock.sendall(data)

        
    def set_attitude(self, msg):
        """Set the attitude of the gimbal"""
        # https://mavlink.io/en/messages/common.html#GIMBAL_DEVICE_SET_ATTITUDE
   
        pitch, yaw = msg.q[2], msg.q[3]
        pitchspeed, yawspeed = msg.angular_velocity_y, msg.angular_velocity_z
        pan = int(yawspeed * 100)
        tilt = int(pitchspeed * 100)
        data = pan_tilt(pan, tilt)
        print(f"pan tilt {pan = } {tilt = } {data = }")
        self.sock.sendall(data)
        
    def close(self):
        """Close the connection to the gimbal"""
        super().close()
        self.sock.close()
        self.log.debug(f"Closed connection to gimbal")
        return True

