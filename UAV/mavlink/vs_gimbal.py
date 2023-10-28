from __future__ import annotations
"""
Viewsheen Gimbal Component
https://mavlink.io/en/services/gimbal_v2.html
The gimbal protocol allows MAVLink control over the attitude/orientation of cameras (or other sensors) mounted on the drone. The orientation can be: controlled by the pilot in real time 
(e.g. using a joystick from a ground station), set as part of a mission, or moved based on camera tracking.
The protocol also defines what status information is published for developers, configurators, as well as users of the drone. It additionally provides ways to assign control to different sources.
The protocol supports a number of hardware setups, and enables gimbals with varying capabilities
"""

__all__ = ['NAN', 'GIMBAL_DEVICE_SET_ATTITUDE', 'GIMBAL_MANAGER_SET_MANUAL_CONTROL', 'MAV_CMD_SET_CAMERA_ZOOM',
           'MAV_CMD_IMAGE_START_CAPTURE', 'MAV_CMD_IMAGE_STOP_CAPTURE', 'GimbalClient', 'GimbalServer']

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
class GimbalClient(Component):
    """Create a Viewsheen mavlink gimbal client component for send commands to a gimbal on a companion computer or GCS """

    def __init__(self,
                 source_component: int,  # used for component indication
                 mav_type: int,  # used for heartbeat MAV_TYPE indication
                 loglevel: LogLevels | int = LogLevels.INFO):  # logging level
        
        super().__init__(source_component=source_component, mav_type=mav_type, loglevel=loglevel)
        # self.gimbal_target_component = None
        # self.camera_target_component = None
        
    # def send_message(self, msg):
    #     """Send a message to the gimbal"""
    #     self.master.mav.send(msg)
    #     self.log.debug(f"Sent {msg}")
    #
    # # def set_target(self, target_system, gimbal_comp = None,  camera_comp = None):
    # #     """Set the target system and component for the gimbal / camera"""
    # #     self.target_system = target_system
    # #     self.gimbal_target_component = gimbal_comp
    # #     self.camera_target_component = camera_comp
    #

    async def set_attitude(self, pitch, yaw, pitchspeed, yawspeed):
        """Set the attitude of the gimbal"""
        # https://mavlink.io/en/messages/common.html#GIMBAL_DEVICE_SET_ATTITUDE
        # https://mavlink.io/en/messages/common.html#GIMBAL_DEVICE_FLAGS
        flags = 0

        q = [1, 0, pitch, yaw]
        angular_velocity_x, angular_velocity_y, angular_velocity_z = 0, pitchspeed, yawspeed

        self.mav.gimbal_device_set_attitude_send(
            self.target_system, self.target_component,
            flags,
            q,
            angular_velocity_x, angular_velocity_y, angular_velocity_z,
        )
        command_id = None
        return True
        # ret = await self.wait_ack(self.target_system, self.target_component, command_id=command_id, timeout=1)
        # if ret:
        #     # if self.wait_ack(target_system, target_component, command_id=command_id, timeout=timeout):
        #     self.log.debug(
        #         f"Rcvd ACK: {self.target_system}/{self.target_component} {mavlink_command_to_string(command_id)}:{command_id}")
        #     self.num_acks_rcvd += 1
        #     return True
        # else:
        #     self.log.warning(
        #         f"**No ACK: {self.target_system}/{self.target_component} {mavlink_command_to_string(command_id)}:{command_id}")
        #     self.num_acks_drop += 1
        #     return False
    
    def set_zoom(self, value):
        """ Set the camera zoom"""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_SET_CAMERA_ZOOM
        return self.send_command(self.target_system, self.target_component,
        MAV_CMD_SET_CAMERA_ZOOM,
        [0,
         value, 0,0,0,0,0])
    
    def start_capture(self):
        """Start image capture sequence."""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_IMAGE_START_CAPTURE
        return self.send_command(self.target_system, self.target_component,
        MAV_CMD_IMAGE_START_CAPTURE,
        [0,
         0, # interval
         1, # number of  images to capture
         0, # Sequence number starting from 1. This is only valid for single-capture (param3 == 1), otherwise set to 0.  Increment the capture ID for each capture command to prevent double captures when a command is re-transmitted.
         NAN, # Reserved
         NAN, # Reserved
         NAN]) # Reserved
    
    def stop_capture(self):
        """Stop image capture sequence"""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_IMAGE_STOP_CAPTURE
        return self.send_command(self.target_system, self.target_component,
        MAV_CMD_IMAGE_STOP_CAPTURE,
        [0, NAN, NAN, NAN, NAN, NAN, NAN])



class GimbalServer(Component):
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
            self.log.error(f"Timeout connecting to gimbal")
            return False
        self.log.debug(f"Connected to gimbal")
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
        """ Set the viewsheen camera zoom """
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

