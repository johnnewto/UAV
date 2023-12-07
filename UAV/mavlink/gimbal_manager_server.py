from __future__ import annotations

from mavcom.mavlink.component import Component, mavutil, mavlink, MAVLink
from ..gimbals.gimbal import Gimbal

"""
Viewsheen Gimbal Component
https://mavlink.io/en/services/gimbal_v2.html
The gimbal protocol allows MAVLink control over the attitude/orientation of cameras (or other sensors) mounted on the drone. The orientation can be: controlled by the pilot in real time 
(e.g. using a joystick from a ground station), set as part of a mission, or moved based on cameras tracking.
The protocol also defines what status information is published for developers, configurators, as well as users of the drone. It additionally provides ways to assign control to different sources.
The protocol supports a number of hardware setups, and enables gimbals with varying capabilities
"""

__all__ = ['NAN', 'GIMBAL_DEVICE_SET_ATTITUDE', 'GIMBAL_MANAGER_SET_MANUAL_CONTROL', 'MAV_CMD_SET_CAMERA_ZOOM',
           'MAV_CMD_IMAGE_START_CAPTURE', 'MAV_CMD_IMAGE_STOP_CAPTURE', 'GimbalServer']

import socket

from mavcom.mavlink.component import Component, mavlink_command_to_string
# from viewsheen_sdk.gimbal_cntrl import pan_tilt, snapshot,  zoom, VS_IP_ADDRESS, VS_PORT, KeyReleaseThread
from ..camera_sdks.viewsheen.gimbal_cntrl import pan_tilt, snapshot, zoom, VS_IP_ADDRESS, VS_PORT
from ..logging import LogLevels

# from UAV.imports import *   # TODO why is this relative import on nbdev_export?


# from pymavlink.dialects.v20 import ardupilotmega as mav

NAN = float("nan")
GIMBAL_MANAGER_INFORMATION = 280  # https://mavlink.io/en/messages/common.html#GIMBAL_MANAGER_INFORMATION
GIMBAL_MANAGER_STATUS = 281  # https://mavlink.io/en/messages/common.html#GIMBAL_MANAGER_STATUS
GIMBAL_DEVICE_INFORMATION = 283  # https://mavlink.io/en/messages/common.html#GIMBAL_DEVICE_INFORMATION
GIMBAL_DEVICE_SET_ATTITUDE = 284  # https://mavlink.io/en/messages/common
GIMBAL_DEVICE_ATTITUDE_STATUS = 285  # https://mavlink.io/en/messages/common.html#GIMBAL_DEVICE_ATTITUDE_STATUS

AUTOPILOT_STATE_FOR_GIMBAL_DEVICE = 286  # https://mavlink.io/en/messages/common.html#AUTOPILOT_STATE_FOR_GIMBAL_DEVICE

GIMBAL_MANAGER_SET_PITCHYAW = 287  # https://mavlink.io/en/messages/common.html#GIMBAL_MANAGER_SET_PITCHYAW
GIMBAL_MANAGER_SET_MANUAL_CONTROL = 288  # https://mavlink.io/en/messages/common.html#GIMBAL_MANAGER_SET_MANUAL_CONTROL
MAV_CMD_DO_GIMBAL_MANAGER_PITCHYAW = 1000  # https://mavlink.io/en/messages/common.html#MAV_CMD_DO_GIMBAL_MANAGER_PITCHYAW
MAV_CMD_DO_GIMBAL_MANAGER_CONFIGURE = 1001  # https://mavlink.io/en/messages/common.html#MAV_CMD_DO_GIMBAL_MANAGER_CONFIGURE

MAV_CMD_SET_CAMERA_ZOOM = 531  # https://mavlink.io/en/messages/common.html#MAV_CMD_SET_CAMERA_ZOOM
MAV_CMD_IMAGE_START_CAPTURE = 2000  # https://mavlink.io/en/messages/common.html#MAV_CMD_IMAGE_START_CAPTURE
MAV_CMD_IMAGE_STOP_CAPTURE = 2001  # https://mavlink.io/en/messages/common.html#MAV_CMD_IMAGE_STOP_CAPTURE


class GimbalServer(Component):
    """Create a Viewsheen mavlink Camera Server Component for receiving commands from a gimbal on a companion computer or GCS"""

    def __init__(self,
                 source_component: int = mavlink.MAV_COMP_ID_GIMBAL,  # used for component indication
                 mav_type: int = mavlink.MAV_TYPE_GIMBAL,  # used for heartbeat MAV_TYPE indication
                 gimbal=None,
                 loglevel: LogLevels | int = LogLevels.INFO,  # logging level
                 ):

        super().__init__(source_component=source_component, mav_type=mav_type, loglevel=loglevel)

        self._set_message_callback(self.on_message)
        self.gimbal: Gimbal = gimbal

    def on_mav_connection(self):
        """Start the mavlink connection"""
        super().on_mav_connection()
        assert self.mav is not None, "call set_mav first"
        if self.gimbal is None:
            self.log.warning(f"Component has no gimbal object")
        self.gimbal.mav = self.mav  # set the mavlink connection for mavlink messages
        self.gimbal.source_system = self.source_system
        self.gimbal.source_component = self.source_component

    def on_message(self, msg):
        """Callback for a command received from the gimbal"""
        # https://mavlink.io/en/messages/common.html#GIMBAL_DEVICE_SET_ATTITUDE
        # print(f" {msg = }")
        # print(f" {msg.get_type() = }")
        # return False
        if msg.get_type() == "GIMBAL_DEVICE_SET_ATTITUDE" or msg.get_type() == "GIMBAL_MANAGER_SET_ATTITUDE":
            """ not sure on use???  without confirmation"""
            self._set_attitude(msg)
            return False
        elif msg.get_type() == "GIMBAL_MANAGER_SET_PITCHYAW":
            """ high rate message without confirmation"""
            self.log.debug(f"***** PitchYaw {msg}")
            self._cmd_gimbal_pitch_yaw(msg)
            return False

        elif msg.get_type() == "GIMBAL_MANAGER_SET_MANUAL_CONTROL":
            """ high rate message without confirmation manual relative control"""
            self._manual_gimbal_pitch_yaw(msg)
            self.log.debug(f"***** Manual Control {msg}")
            return False
        # elif msg.get_type() == "MAVLINK_MSG_ID_GIMBAL_DEVICE_SET_ATTITUDE":


        elif msg.get_type() == "COMMAND_LONG":
            # print(f"Command  {msg.command = } ")
            if msg.command == MAV_CMD_DO_GIMBAL_MANAGER_PITCHYAW:
                self._cmd_gimbal_pitch_yaw(msg)
                return True
            elif msg.command == MAV_CMD_SET_CAMERA_ZOOM:
                # self.log.info(f"***** Zoom {msg}")
                # print(f"Zoom {msg.param2 = }")
                self._set_zoom(msg)
                return True
            elif msg.command == MAV_CMD_IMAGE_START_CAPTURE:
                self._start_capture()
                return True

        else:
            self.log.debug(f"Unknown command {msg.get_type()} received from {msg.get_srcSystem()}/{msg.get_srcComponent()}")
            return False

    def _cmd_gimbal_pitch_yaw(self, msg):
        """Set the attitude of the gimbal"""
        # self.log.warning (f"Not Implemented _cmd_gimbal_pitch_yaw")
        # return False
        # https://mavlink.io/en/messages/common.html#MAV_CMD_DO_GIMBAL_MANAGER_PITCHYAW
        pitch, yaw = msg.param1, msg.param2
        pitchspeed, yawspeed = msg.param3, msg.param4
        self.log.info(f"Pitch {pitch = } {yaw = } {pitchspeed = } {yawspeed = }")
        # self.gimbal.set_pitch_yaw(pitch, yaw)
        self.gimbal.set_pitch_yaw(pitch, yaw, pitchspeed, yawspeed)
        return True


    def _manual_gimbal_pitch_yaw(self, msg):
        """ High level message to control a gimbal manually The angles or angular rates are unitless (-1..1).
        the actual rates will depend on internal gimbal manager settings/configuration"""
        # https://mavlink.io/en/messages/common.html#GIMBAL_MANAGER_SET_MANUAL_CONTROL
        self.log.info(f"Pitch {msg.pitch = } {msg.yaw = } {msg.pitch_rate = } {msg.yaw_rate = }")
        self.gimbal.manual_pitch_yaw(msg.pitch, msg.yaw)
        # self._cmd_gimbal_pitch_yaw(msg)
        # self.gimbal.set_pitch_yaw(pitch, yaw, pitchspeed, yawspeed)
        return True


    def _set_attitude(self, msg):
        """Set the attitude of the gimbal"""
        # https://mavlink.io/en/messages/common.html#GIMBAL_DEVICE_SET_ATTITUDE
        pitch, yaw = msg.q[0], msg.q[1]
        self.log.info  (f"_set_attitude {pitch = } {yaw = }")
        self.gimbal.manual_pitch_yaw(pitch, yaw)
        # retur
        # #
        # # pitch, yaw = msg.q[2], msg.q[3]
        # # pitchspeed, yawspeed = msg.angular_velocity_y, msg.angular_velocity_z
        # # pan = int(yawspeed * 100)
        # # tilt = int(pitchspeed * 100)
        # # data = pan_tilt(pan, tilt)
        # # print(f"pan tilt {pan = } {tilt = } {data = }")
        # # # self.sock.sendall(data)

    def _set_zoom(self, msg):
        """ Set the viewsheen cameras zoom """
        # print(msg.get_type())
        # print(f"Zoom {msg.param2 = }")
        data = zoom(int(msg.param2))
        # self.sock.sendall(data)

    def _start_capture(self):
        """Start image capture sequence."""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_IMAGE_START_CAPTURE
        data = snapshot(1, 0)
        # self.sock.sendall(data)


    def close(self):
        """Close the connection to the gimbal"""
        super().close()
        # self.sock.close()
        self.log.debug(f"Closed connection to gimbal")
        return True
