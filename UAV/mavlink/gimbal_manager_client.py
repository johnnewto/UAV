from __future__ import annotations

__all__ = ['NAN', 'GimbalManagerClient']

import asyncio
# from pymavlink.dialects.v20.ardupilotmega
from pymavlink.dialects.v20.ardupilotmega import MAVLink_message
# , gimbal_manager_set_pitchyaw_send, gimbal_manager_set_manual_control_encode)

from .camera_client import check_target
from .client_component import ClientComponent, mavlink
from UAV.mavlink import CameraClient, CameraServer, MAVCom, mavlink

"""
https://mavlink.io/en/services/gimbal_v2.html
The gimbal protocol allows MAVLink control over the attitude/orientation of cameras (or other sensors) mounted on the drone. The orientation can be: controlled by the pilot in real time 
(e.g. using a joystick from a ground station), set as part of a mission, or moved based on cameras tracking.
The protocol also defines what status information is published for developers, configurators, as well as users of the drone. It additionally provides ways to assign control to different sources.
The protocol supports a number of hardware setups, and enables gimbals with varying capabilities
"""

import socket

from .component import Component, mavlink_command_to_string
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


class GimbalManagerClient(ClientComponent):
    """Create a mavlink gimbalmanager client component for send commands to a gimbal on a companion computer """

    def __init__(self,
                 source_component: int,  # used for component indication
                 mav_type: int,  # used for heartbeat MAV_TYPE indication
                 loglevel: LogLevels | int = LogLevels.INFO):  # logging level

        super().__init__(source_component=source_component, mav_type=mav_type, loglevel=loglevel)

    def cmd_pitch_yaw(self,
                      pitch,  # Pitch angle (positive to pitch up, relative to vehicle for FOLLOW mode, relative to world horizon for LOCK mode).
                      yaw,  # Yaw angle (positive to yaw to the right, relative to vehicle for FOLLOW mode, absolute to North for LOCK mode).
                      pitch_rate,  # Pitch rate (positive to pitch up).
                      yaw_rate,  # Yaw rate (positive to yaw to the right).
                      flags,  # Gimbal manager flags to use.
                      device_id=0,  # Component ID of gimbal device to address (or 1-6 for non-MAVLink gimbal),
                      # 0 for all gimbal device components. Send command multiple times for more than one gimbal (but not all gimbals).
                      target_system=None, target_component=None, ):
        """ [Command] Set gimbal manager pitch/yaw setpoints  for low-rate adjustments that require confirmation.
            MAV_CMD_DO_GIMBAL_MANAGER_PITCHYAW = 1000  # https://mavlink.io/en/messages/common.html#MAV_CMD_DO_GIMBAL_MANAGER_PITCHYAW
        """
        flags = 0

        target_system, target_component = check_target(self, target_system, target_component)
        params = [pitch, yaw, pitch_rate, yaw_rate, flags, 0, device_id]
        ret = self.send_command(target_system,
                                target_component,
                                mavlink.MAV_CMD_DO_GIMBAL_MANAGER_PITCHYAW,
                                params
                                )
        return ret

    def manual_pitch_yaw(self,
                         pitch,  # Pitch angle (positive to pitch up, relative to vehicle for FOLLOW mode, relative to world horizon for LOCK mode).
                         yaw,  # Yaw angle (positive to yaw to the right, relative to vehicle for FOLLOW mode, absolute to North for LOCK mode).
                         pitch_rate,  # Pitch rate (positive to pitch up).
                         yaw_rate,  # Yaw rate (positive to yaw to the right).
                         flags,  # Gimbal manager flags to use.
                         device_id=0,  # Component ID of gimbal device to address (or 1-6 for non-MAVLink gimbal),
                         # 0 for all gimbal device components. Send command multiple times for more than one gimbal (but not all gimbals).
                         target_system=None, target_component=None, ):
        """  High level message to control a gimbal manually.
            GIMBAL_MANAGER_SET_MANUAL_CONTROL = 288  # https://mavlink.io/en/messages/common.html#GIMBAL_MANAGER_SET_MANUAL_CONTROL
        """
        flags = 0

        target_system, target_component = check_target(self, target_system, target_component)
        # params = [pitch, yaw, pitch_rate, yaw_rate, flags, 0, device_id]

        # MAVLink_gimbal_manager_set_pitchyaw_message
        #
        # send message GIMBAL_MANAGER_SET_PITCHYAW
        self.log.debug(f"Sending: {target_system}/{target_component} : {mavlink_command_to_string(GIMBAL_MANAGER_SET_MANUAL_CONTROL)}:{GIMBAL_MANAGER_SET_MANUAL_CONTROL} ")
        if False:
            self.master.mav.gimbal_manager_set_manual_control_send(
                target_system, target_component,
                flags,
                device_id,
                pitch, yaw, pitch_rate, yaw_rate,
            )
        else:
            self.master.mav.gimbal_device_set_attitude_send(
                target_system, target_component, 0, [pitch, yaw, 0, 0], 0, 0, 0)

        return

    def _test_send_command(self, target_system: int,  # target system
                           target_component: int,  # target component
                           command_id: int,  # mavutil.mavlink.MAV_CMD....
                           params: list,  # list of parameters
                           timeout=0.5,  # seconds
                           ):
        self.log.debug(
            f"Sending: {target_system}/{target_component} : {mavlink_command_to_string(command_id)}:{command_id} ")

        return asyncio.sleep(0.1)

    def set_zoom(self, value):
        """ Set the cameras zoom"""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_SET_CAMERA_ZOOM
        return self.send_command(self.target_system, self.target_component,
                                 MAV_CMD_SET_CAMERA_ZOOM,
                                 [0,
                                  value, 0, 0, 0, 0, 0])

    def start_capture(self):
        """Start image capture sequence."""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_IMAGE_START_CAPTURE
        return self.send_command(self.target_system, self.target_component,
                                 MAV_CMD_IMAGE_START_CAPTURE,
                                 [0,
                                  0,  # interval
                                  1,  # number of  images to capture
                                  0,  # Sequence number starting from 1. This is only valid for single-capture (param3 == 1), otherwise set to 0.  Increment the capture ID for each capture command to prevent double captures when a command is re-transmitted.
                                  NAN,  # Reserved
                                  NAN,  # Reserved
                                  NAN])  # Reserved

    def stop_capture(self):
        """Stop image capture sequence"""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_IMAGE_STOP_CAPTURE
        return self.send_command(self.target_system, self.target_component,
                                 MAV_CMD_IMAGE_STOP_CAPTURE,
                                 [0, NAN, NAN, NAN, NAN, NAN, NAN])
