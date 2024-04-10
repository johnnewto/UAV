from __future__ import annotations

__all__ = ['NAN', 'CAMERA_INFORMATION', 'CAMERA_SETTINGS', 'STORAGE_INFORMATION', 'CAMERA_CAPTURE_STATUS',
           'CAMERA_IMAGE_CAPTURED', 'CameraClient', 'Component']

import asyncio
import contextlib

from ..logging import logging, LogLevels
from .component import Component, mavutil, mavlink
import threading

NAN = float("nan")

"""
MAV_CMD_REQUEST_CAMERA_CAPTURE_STATUS = 527 # https://mavlink.io/en/messages/common.html#MAV_CMD_REQUEST_CAMERA_CAPTURE_STATUS
MAV_CMD_REQUEST_CAMERA_INFORMATION = 521 # https://mavlink.io/en/messages/common.html#MAV_CMD_REQUEST_CAMERA_INFORMATION
MAV_CMD_REQUEST_CAMERA_SETTINGS = 522 # https://mavlink.io/en/messages/common.html#MAV_CMD_REQUEST_CAMERA_SETTINGS
MAV_CMD_REQUEST_STORAGE_INFORMATION = 525 # https://mavlink.io/en/messages/common.html#MAV_CMD_REQUEST_STORAGE_INFORMATION
MAV_CMD_STORAGE_FORMAT = 526 # https://mavlink.io/en/messages/common.html#MAV_CMD_STORAGE_FORMAT
MAV_CMD_SET_CAMERA_ZOOM = 531 # https://mavlink.io/en/messages/common.html#MAV_CMD_SET_CAMERA_ZOOM
MAV_CMD_SET_CAMERA_FOCUS = 532 # https://mavlink.io/en/messages/common.html#MAV_CMD_SET_CAMERA_FOCUS
MAV_CMD_IMAGE_START_CAPTURE = 2000  # https://mavlink.io/en/messages/common.html#MAV_CMD_IMAGE_START_CAPTURE
MAV_CMD_IMAGE_STOP_CAPTURE = 2001  # https://mavlink.io/en/messages/common.html#MAV_CMD_IMAGE_STOP_CAPTURE
MAV_CMD_REQUEST_VIDEO_STREAM_INFORMATION = 2504 # https://mavlink.io/en/messages/common.html#MAV_CMD_REQUEST_VIDEO_STREAM_INFORMATION
MAV_CMD_REQUEST_VIDEO_STREAM_STATUS = 2505 # https://mavlink.io/en/messages/common.html#MAV_CMD_REQUEST_VIDEO_STREAM_STATUS
MAV_CMD_VIDEO_START_CAPTURE = 2500 # https://mavlink.io/en/messages/common.html#MAV_CMD_VIDEO_START_CAPTURE
MAV_CMD_VIDEO_STOP_CAPTURE = 2501 # https://mavlink.io/en/messages/common.html#MAV_CMD_VIDEO_STOP_CAPTURE
MAV_CMD_SET_CAMERA_MODE = 530 # https://mavlink.io/en/messages/common.html#MAV_CMD_SET_CAMERA_MODE

"""
CAMERA_INFORMATION = mavlink.MAVLINK_MSG_ID_CAMERA_INFORMATION  # https://mavlink.io/en/messages/common.html#CAMERA_INFORMATION
CAMERA_SETTINGS = mavlink.MAVLINK_MSG_ID_CAMERA_SETTINGS  # https://mavlink.io/en/messages/common.html#CAMERA_SETTINGS
STORAGE_INFORMATION = mavlink.MAVLINK_MSG_ID_STORAGE_INFORMATION  # https://mavlink.io/en/messages/common.html#STORAGE_INFORMATION
CAMERA_CAPTURE_STATUS = mavlink.MAVLINK_MSG_ID_CAMERA_CAPTURE_STATUS  # https://mavlink.io/en/messages/common.html#CAMERA_CAPTURE_STATUS
CAMERA_IMAGE_CAPTURED = mavlink.MAVLINK_MSG_ID_CAMERA_IMAGE_CAPTURED  # https://mavlink.io/en/messages/common.html#CAMERA_IMAGE_CAPTURED


def patch_MAVLink_camera_information_message():
    """Override/patch format_attr to handle vender and model name list as a string rather than list of ints.
    See ardupilotmega.py line 143
    `def format_attr(self, field: str) -> Union[str, float, int]:`
    """
    # print("patch_MAVLink_camera_information_message.format_attr;   to handle vender and model name list")
    from typing import List, Union
    import sys
    def format_attr(msg, field: str) -> Union[str, float, int]:
        """override field getter"""
        raw_attr: Union[bytes, float, int] = getattr(msg, field)
        if isinstance(raw_attr, bytes):
            if sys.version_info[0] == 2:
                return raw_attr.rstrip(b"\x00")
            return raw_attr.decode(errors="backslashreplace").rstrip("\x00")
        elif isinstance(raw_attr, List):
            return str(''.join(chr(i) for i in raw_attr)).rstrip()
        return raw_attr

    mavlink.MAVLink_camera_information_message.format_attr = format_attr


patch_MAVLink_camera_information_message()


def check_target(obj, target_system, target_component):
    """Check if the target_system and target_component are set and return them"""
    target_system = obj.target_system if target_system is None else target_system
    target_component = obj.target_component if target_component is None else target_component
    assert target_system is not None and target_component is not None, "call set_target(target_system, target_component) first"
    return target_system, target_component


async def event_wait(evt, timeout):
    # suppress TimeoutError because we'll return False in case of timeout
    with contextlib.suppress(asyncio.TimeoutError):
        await asyncio.wait_for(evt.wait(), timeout)
    return evt.is_set()


class CameraClient(Component):
    """Create a client component to send commands to a companion computer or GCS that will control a cameras via a CameraServer instance """

    def __init__(self,
                 source_component: int,  # used for component indication
                 mav_type: int,  # used for heartbeat MAV_TYPE indication
                 loglevel: LogLevels | int = LogLevels.INFO,  # logging level
                 ):

        super().__init__(source_component=source_component, mav_type=mav_type, loglevel=loglevel)

        self._set_message_callback(self.on_message)
        self._message_callback_conds = []

    def set_message_callback_cond(self, msg_id, target_system, target_component):
        """Register a callback condition for a message received from the server"""
        evt = asyncio.Event()
        cond = {'msg_id': msg_id, 'target_system': target_system, 'target_component': target_component, 'event': evt,
                'msg': None}
        self._message_callback_conds.append(cond)
        self.log.debug(f"{len( self._message_callback_conds) = } ")
        return cond

    async def wait_message_callback(self, cond, timeout=1):
        """Wait for the callback for a message received from the server"""
        ret = await event_wait(cond['event'], timeout)
        try:
            self._message_callback_conds.remove(cond)
        except ValueError:
            self.log.error(f"Failed to remove callback condition {cond}")
        return ret

    async def message_callback_cond(self, msg_id, target_system, target_component, timeout=1):
        """Register a callback for a message received from the server
           Returns the message """
        evt = asyncio.Event()
        cond = {'msg_id': msg_id, 'target_system': target_system, 'target_component': target_component, 'event': evt,
                'msg': None}
        self._message_callback_conds.append(cond)
        self.log.debug(f"{len( self._message_callback_conds) = } ")
        # await asyncio.sleep(0.1)
        ret = await event_wait(evt, timeout)
        try:
            self._message_callback_conds.remove(cond)
        except ValueError:
            self.log.error(
                f"Failed to remove callback condition {msg_id = } {target_system = } {target_component = } {timeout = } {evt = }")
        return cond['msg']

    def on_mav_connection(self):
        super().on_mav_connection()

    def on_message(self, msg: mavlink.MAVLink_message):
        """Callback for a command received from the server"""
        self.log.debug(f"RCVD: {msg.get_srcSystem()}/{msg.get_srcComponent()}: CAMERA_Client  {msg} ")
        for cond in self._message_callback_conds:
            if msg.get_msgId() == cond['msg_id'] and msg.get_srcSystem() == cond[
                'target_system'] and msg.get_srcComponent() == cond['target_component']:
                # self.log.debug(f"RCVD: {msg.get_srcSystem()}/{msg.get_srcComponent()}: CAMERA_Client  {msg} ")
                cond['event'].set()
                cond['msg'] = msg  # add the message to the condition, so it can be returned

    def send_message(self, msg):
        """Send a message to the cameras"""
        self.master.mav.send(msg)
        self.log.debug(f"Sent {msg}")

    # https://mavlink.io/en/messages/common.html#MAV_CMD_REQUEST_MESSAGE
    async def request_message(self, msg_id, params=None, target_system=None, target_component=None):
        """Request a message from the cameras"""
        if params is None:
            params = [0, 0, 0, 0, 0, 0]
        tgt_sys, tgt_comp = check_target(self, target_system, target_component)

        cond = self.set_message_callback_cond(msg_id, tgt_sys, tgt_comp)
        await self.send_command(tgt_sys, tgt_comp,
                                mavlink.MAV_CMD_REQUEST_MESSAGE,
                                [msg_id] + params
                                )

        await self.wait_message_callback(cond)
        return cond['msg']

    # async def request_camera_information(self, target_system=None, target_component=None):
    #     """Request cameras information"""
    #     # https://mavlink.io/en/messages/common.html#MAV_CMD_REQUEST_CAMERA_INFORMATION
    #
    #     # todo change this to  requested with a MAV_CMD_REQUEST_MESSAGE command.
    #     #  todo see https://mavlink.io/en/messages/common.html#CAMERA_INFORMATION
    #     tgt_sys, tgt_comp = check_target(self, target_system, target_component)
    #
    #     cond = self.set_message_callback_cond(mavlink.MAVLINK_MSG_ID_CAMERA_INFORMATION, tgt_sys, tgt_comp)
    #     await self.send_command(target_system, target_component,
    #                             command_id=mavlink.MAV_CMD_REQUEST_CAMERA_INFORMATION,
    #                             params=[1,0,0,0,0,0,0]
    #                           )
    #     await self.wait_message_callback(cond)
    #     return cond['msg']
    #     # return await self._wait_for_message.async_get()
    #
    #
    #
    # async def request_camera_capture_status(self, target_system=None, target_component=None):
    #     """Request cameras capture status"""
    #     # https://mavlink.io/en/messages/common.html#MAV_CMD_REQUEST_CAMERA_CAPTURE_STATUS
    #     # see https://github.com/PX4/PX4-SITL_gazebo-classic/blob/main/src/gazebo_camera_manager_plugin.cpp#L543
    #     target_system, target_component = check_target(self, target_system, target_component)
    #     # self._wait_for_message.set_condition( mavlink.MAVLINK_MSG_ID_CAMERA_CAPTURE_STATUS, target_system, target_component)
    #     await self.send_command(  target_system,
    #                             target_component,
    #                             mavlink.MAV_CMD_REQUEST_CAMERA_CAPTURE_STATUS,
    #                             [1,0,0,0,0,0,0]
    #                           )
    #     ret = await self.wait_message_callback()
    #     # return self._wait_for_message.get()
    #
    #
    #
    #
    #
    # def request_camera_settings(self, target_system=None, target_component=None):
    #     """Request cameras settings"""
    #     # https://mavlink.io/en/messages/common.html#MAV_CMD_REQUEST_CAMERA_SETTINGS
    #     target_system, target_component = check_target(self, target_system, target_component)
    #     self._wait_for_message.set_condition(CAMERA_SETTINGS, target_system, target_component)
    #     t = self.send_command(  target_system,
    #                             target_component,
    #                             mavlink.MAV_CMD_REQUEST_CAMERA_SETTINGS,
    #                             [0,0,0,0,0,0,0]
    #                           )
    #
    #     return self._wait_for_message.get()
    #
    # def request_storage_information(self, target_system=None, target_component=None):
    #     """Request storage information (for cases where cameras has storage)"""
    #     # https://mavlink.io/en/messages/common.html#MAV_CMD_REQUEST_STORAGE_INFORMATION
    #     target_system, target_component = check_target(self, target_system, target_component)
    #     self._wait_for_message.set_condition(STORAGE_INFORMATION, target_system, target_component)
    #     t = self.send_command(  target_system,
    #                             target_component,
    #                             mavlink.MAV_CMD_REQUEST_STORAGE_INFORMATION,
    #                             [0,0,0,0,0,0,0]
    #                           )
    #
    #     return self._wait_for_message.get()

    def storage_format(self, target_system=None, target_component=None):
        """Format storage (for cases where cameras has storage)"""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_STORAGE_FORMAT
        target_system, target_component = check_target(self, target_system, target_component)
        self._wait_for_message.set_condition(STORAGE_INFORMATION, target_system, target_component)
        t = self.send_command(target_system,
                              target_component,
                              mavlink.MAV_CMD_STORAGE_FORMAT,
                              [0, 0, 0, 0, 0, 0, 0]
                              )
        return self._wait_for_message.get()

    def set_camera_mode(self, target_system=None, target_component=None,
                        mode_id=0):  # https://mavlink.io/en/messages/common.html#CAMERA_MODE
        """ Set the cameras mode"""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_SET_CAMERA_MODE
        # https://mavlink.io/en/messages/common.html#CAMERA_MODE
        target_system, target_component = check_target(self, target_system, target_component)
        # self.wait_for_message.set_condition(????, target_system, target_component)
        t = self.send_command(target_system, target_component,
                              mavlink.MAV_CMD_SET_CAMERA_MODE,
                              [0,
                               mode_id,  # https://mavlink.io/en/messages/common.html#CAMERA_MODE
                               0, 0, 0, 0, 0]
                              )

    def set_camera_zoom(self, target_system=None, target_component=None, zoom_type=0,
                        zoom_value=1):  # 0 to 100 zoom value
        """ Set the cameras zoom"""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_SET_CAMERA_ZOOM
        target_system, target_component = check_target(self, target_system, target_component)
        self._wait_for_message.set_condition(CAMERA_SETTINGS, target_system, target_component)
        t = self.send_command(target_system, target_component,
                              mavlink.MAV_CMD_SET_CAMERA_ZOOM,
                              [zoom_type,  # https://mavlink.io/en/messages/common.html#CAMERA_ZOOM_TYPE
                               zoom_value, 0, 0, 0, 0, 0]
                              )

        return self._wait_for_message.get()

    def image_start_capture(self, target_system=None, target_component=None, interval=0,  # Image capture interval
                            count=1,  # Number of images to capture (0 for unlimited)
                            ):
        """Start image capture sequence."""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_IMAGE_START_CAPTURE
        try:
            self.image_capture_sequence_number += 1
            if count != 1:
                self.image_capture_sequence_number = 0
        except:
            self.image_capture_sequence_number = 1
        target_system, target_component = check_target(self, target_system, target_component)
        # self.wait_for_message.set_condition(CAMERA_IMAGE_CAPTURED, target_system, target_component)
        return self.send_command(target_system, target_component,
                                 mavlink.MAV_CMD_IMAGE_START_CAPTURE,
                                 [0,
                                  interval,  # interval
                                  count,  # number of  images to capture
                                  self.image_capture_sequence_number,
                                  # Sequence number starting from 1. This is only valid for single-capture (param3 == 1), otherwise set to 0.  Increment the capture ID for each capture command to prevent double captures when a command is re-transmitted.
                                  NAN,  # Reserved
                                  NAN,  # Reserved
                                  NAN]
                                 )  # Reserved

        # return self.wait_for_message.get()

    def image_stop_capture(self, target_system=None, target_component=None):
        """Stop image capture sequence"""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_IMAGE_STOP_CAPTURE
        target_system, target_component = check_target(self, target_system, target_component)
        return self.send_command(target_system, target_component,
                                 mavlink.MAV_CMD_IMAGE_STOP_CAPTURE,
                                 [0, NAN, NAN, NAN, NAN, NAN, NAN]
                                 )

    def video_start_capture(self, target_system=None, target_component=None, video_stream_id=0,
                            # Video stream id (0 for all streams)
                            frequency=1):  # Frequency CAMERA_CAPTURE_STATUS messages should be sent while recording (0 for no messages, otherwise frequency in Hz)
        """Start video capture"""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_VIDEO_START_CAPTURE
        target_system, target_component = check_target(self, target_system, target_component)
        return self.send_command(target_system, target_component,
                                 mavlink.MAV_CMD_VIDEO_START_CAPTURE,
                                 [video_stream_id,  # Video stream id (0 for all streams)
                                  frequency,
                                  # Frequency CAMERA_CAPTURE_STATUS messages should be sent while recording (0 for no messages, otherwise frequency in Hz)
                                  NAN, NAN, 0, 0, NAN]
                                 )

    def video_stop_capture(self, target_system=None, target_component=None,
                           video_stream_id=0):  # Video stream id (0 for all streams)
        """Stop video capture"""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_VIDEO_STOP_CAPTURE
        target_system, target_component = check_target(self, target_system, target_component)
        return self.send_command(target_system, target_component,
                                 mavlink.MAV_CMD_VIDEO_STOP_CAPTURE,
                                 [video_stream_id, NAN, NAN, NAN, NAN, NAN, NAN]
                                 )

    def video_start_streaming(self, target_system=None, target_component=None, video_stream_id=0,
                              # Video Stream ID (0 for all streams)
                              ):
        """Start video streaming"""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_VIDEO_START_STREAMING
        target_system, target_component = check_target(self, target_system, target_component)
        return self.send_command(target_system, target_component,
                                 mavlink.MAV_CMD_VIDEO_START_STREAMING,
                                 [video_stream_id, NAN, NAN, NAN, NAN, NAN, NAN]
                                 )

    def video_stop_streaming(self, target_system=None, target_component=None,
                             video_stream_id=0):  # Video Stream ID (0 for all streams)
        """Stop the video stream"""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_VIDEO_STOP_STREAMING
        target_system, target_component = check_target(self, target_system, target_component)
        return self.send_command(target_system, target_component,
                                 mavlink.MAV_CMD_VIDEO_STOP_STREAMING,
                                 [video_stream_id, NAN, NAN, NAN, NAN, NAN, NAN]
                                 )
