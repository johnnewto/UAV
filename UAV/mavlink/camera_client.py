


__all__ = ['NAN', 'CAMERA_INFORMATION', 'CAMERA_SETTINGS', 'STORAGE_INFORMATION', 'CAMERA_CAPTURE_STATUS',
           'CAMERA_IMAGE_CAPTURED',  'WaitMessage', 'CameraClient', 'Component']


import time, os, sys

from ..camera.fake_cam import GSTCamera, BaseCamera
from ..logging import logging
# from .mavcom import MAVCom, time_since_boot_ms, time_UTC_usec, boot_time_str, date_time_str
from .component import Component, mavutil, mavlink, MAVLink
import threading
import cv2
import numpy as np




# from pymavlink.dialects.v20 import ardupilotmega as mav
# from pymavlink.dialects.v20.ardupilotmega import MAVLink


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
CAMERA_INFORMATION = mavlink.MAVLINK_MSG_ID_CAMERA_INFORMATION # https://mavlink.io/en/messages/common.html#CAMERA_INFORMATION
CAMERA_SETTINGS = mavlink.MAVLINK_MSG_ID_CAMERA_SETTINGS # https://mavlink.io/en/messages/common.html#CAMERA_SETTINGS
STORAGE_INFORMATION = mavlink.MAVLINK_MSG_ID_STORAGE_INFORMATION # https://mavlink.io/en/messages/common.html#STORAGE_INFORMATION
CAMERA_CAPTURE_STATUS = mavlink.MAVLINK_MSG_ID_CAMERA_CAPTURE_STATUS # https://mavlink.io/en/messages/common.html#CAMERA_CAPTURE_STATUS
CAMERA_IMAGE_CAPTURED = mavlink.MAVLINK_MSG_ID_CAMERA_IMAGE_CAPTURED # https://mavlink.io/en/messages/common.html#CAMERA_IMAGE_CAPTURED



class WaitMessage:
    """Wait for a specific message from the server"""
    def __init__(self, target_system, target_component):
        # self.target_system = None
        # self.target_component = None
        self._condition = None
        self._event = threading.Event()
        self._object = None
        self._log = logging.getLogger("uav.{}".format(self.__class__.__name__))
        # self._msg_id = None

    @property
    def log(self) -> logging.Logger:
        return self._log

    def set_condition(self, msg_id, target_system, target_component):
        """Set the condition function to generate event for a specific message received from the server"""
        assert target_system is not None and target_component is not None, "call set_target(target_system, target_component) first"
        # self._msg_id = msg_id
        # self.target_system = target_system
        # self.target_component = target_component
        self._condition = (lambda msg: msg.get_msgId() == msg_id
                                   and msg.get_srcSystem() == target_system
                                   and msg.get_srcComponent() == target_component)
        self._event.clear()

    def on_condition(self, msg):
        """Event for a specific received from the server"""
        if self._condition is not None:
            # self.log.debug(f"!!!! on_condition : {msg.get_msgId() = } {self._msg_id = } ")
            # self.log.debug(f"!{msg.get_msgId() == self._msg_id} and {msg.get_srcSystem() = } {self.target_system} and {msg.get_srcComponent() == self.target_component } ")
            # self.log.debug(f"!!!!  {self._condition(msg) = } ")
            if self._condition(msg):
                # self.log.debug(f"!!!! on_condition meet : {msg = } ")
                self._object = msg
                self._event.set()
        # except:
        #     pass


    def set(self, value):
        """Set the object and set the event."""
        self._object = value
        self._event.set()

    def clear(self):
        """Clear the object and clear the event."""
        self._object = None
        self._event.clear()

    def get(self, timeout=1):
        """Get the object if the event is set or wait until it's set with an optional timeout.

        Returns:
            The object if the event is set, or None if it times out or the event isn't set.
        """
        is_set = self._event.wait(timeout)
        if is_set:
            return self._object
        return None

    def is_set(self):
        """Check if the event is set."""
        return self._event.is_set()

def check_target(obj, target_system, target_component):
    """Check if the target_system and target_component are set and return them"""
    target_system = obj.target_system if target_system is None else target_system
    target_component = obj.target_component if target_component is None else target_component
    assert target_system is not None and target_component is not None, "call set_target(target_system, target_component) first"
    return target_system, target_component


class CameraClient(Component):
    """Create a Viewsheen mavlink gimbal client component for send commands to a gimbal on a companion computer or GCS """

    def __init__(self,
                 source_component,  # used for component indication
                 mav_type,  # used for heartbeat MAV_TYPE indication
                 debug):  # logging level
        
        super().__init__(source_component=source_component, mav_type=mav_type, debug=debug)
        self.set_message_callback(self.on_message)
        self.wait_for_message = WaitMessage(self.target_system, self.target_component)

    def on_mav_connection(self):
        super().on_mav_connection()


    def on_message(self, msg):
        """Callback for a command received from the server"""
        print(f"CAMERA_Client  {msg} ")
        self.wait_for_message.on_condition(msg)
        # if msg.get_type() == "CAMERA_IMAGE_CAPTURED":
        #     # print(f"Camera Capture Status {msg = }")
        #     print(msg)
        #         # f"{msg.image_count = }  {msg.image_interval = } {msg.recording_time_ms = } {msg.available_capacity = } {msg.image_status = } {msg.video_status = } {msg.image_interval = } ")
        #
        #     return True
            # print(f"Camera Image Captured {msg = }")


    def send_message(self, msg):
        """Send a message to the camera"""
        self.master.mav.send(msg)
        self.log.debug(f"Sent {msg}")

    def request_camera_capture_status(self, target_system=None, target_component=None):
        """Request camera capture status"""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_REQUEST_CAMERA_CAPTURE_STATUS
        # see https://github.com/PX4/PX4-SITL_gazebo-classic/blob/main/src/gazebo_camera_manager_plugin.cpp#L543
        target_system, target_component = check_target(self, target_system, target_component)

        self.wait_for_message.set_condition(CAMERA_CAPTURE_STATUS, target_system, target_component)
        t = self.send_command(  target_system,
                                target_component,
                                mavlink.MAV_CMD_REQUEST_CAMERA_CAPTURE_STATUS,
                                [1,0,0,0,0,0,0]
                              )
        return self.wait_for_message.get()


    def request_camera_information(self, target_system=None, target_component=None):
        """Request camera information"""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_REQUEST_CAMERA_INFORMATION
        target_system, target_component = check_target(self, target_system, target_component)

        self.wait_for_message.set_condition(CAMERA_INFORMATION, target_system, target_component)
        self.send_command(target_system, target_component,
                                command_id=mavlink.MAV_CMD_REQUEST_CAMERA_INFORMATION,
                                params=[1,0,0,0,0,0,0]
                              )
        return self.wait_for_message.get()

    def request_camera_settings(self, target_system=None, target_component=None):
        """Request camera settings"""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_REQUEST_CAMERA_SETTINGS
        target_system, target_component = check_target(self, target_system, target_component)
        self.wait_for_message.set_condition(CAMERA_SETTINGS, target_system, target_component)
        t = self.send_command(  target_system,
                                target_component,
                                mavlink.MAV_CMD_REQUEST_CAMERA_SETTINGS,
                                [0,0,0,0,0,0,0]
                              )

        return self.wait_for_message.get()

    def request_storage_information(self, target_system=None, target_component=None):
        """Request storage information (for cases where camera has storage)"""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_REQUEST_STORAGE_INFORMATION
        target_system, target_component = check_target(self, target_system, target_component)
        self.wait_for_message.set_condition(STORAGE_INFORMATION, target_system, target_component)
        t = self.send_command(  target_system,
                                target_component,
                                mavlink.MAV_CMD_REQUEST_STORAGE_INFORMATION,
                                [0,0,0,0,0,0,0]
                              )

        return self.wait_for_message.get()

    def storage_format(self, target_system=None, target_component=None):
        """Format storage (for cases where camera has storage)"""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_STORAGE_FORMAT
        target_system, target_component = check_target(self, target_system, target_component)
        self.wait_for_message.set_condition(STORAGE_INFORMATION, target_system, target_component)
        t = self.send_command(  target_system,
                                target_component,
                                mavlink.MAV_CMD_STORAGE_FORMAT,
                                [0,0,0,0,0,0,0]
                              )
        return self.wait_for_message.get()


    def set_camera_mode(self, target_system=None, target_component=None, mode_id=0): # https://mavlink.io/en/messages/common.html#CAMERA_MODE
        """ Set the camera mode"""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_SET_CAMERA_MODE
        # https://mavlink.io/en/messages/common.html#CAMERA_MODE
        target_system, target_component = check_target(self, target_system, target_component)
        # self.wait_for_message.set_condition(????, target_system, target_component)
        t = self.send_command(target_system, target_component,
                                mavlink.MAV_CMD_SET_CAMERA_MODE,
                                [0,
                                 mode_id, # https://mavlink.io/en/messages/common.html#CAMERA_MODE
                                 0,0,0,0,0]
                              )


    def set_camera_zoom(self, target_system=None, target_component=None, zoom_type= 0, zoom_value=1): # 0 to 100 zoom value
        """ Set the camera zoom"""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_SET_CAMERA_ZOOM
        target_system, target_component = check_target(self, target_system, target_component)
        self.wait_for_message.set_condition(CAMERA_SETTINGS, target_system, target_component)
        t = self.send_command(target_system, target_component,
                                mavlink.MAV_CMD_SET_CAMERA_ZOOM,
                                [zoom_type,  # https://mavlink.io/en/messages/common.html#CAMERA_ZOOM_TYPE
                                 zoom_value, 0,0,0,0,0]
                              )

        return self.wait_for_message.get()


    def image_start_capture(self, target_system=None, target_component=None, interval=0, # Image capture interval
                            count=1, # Number of images to capture (0 for unlimited)
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
        self.wait_for_message.set_condition(CAMERA_IMAGE_CAPTURED, target_system, target_component)
        t = self.send_command(target_system, target_component,
                                mavlink.MAV_CMD_IMAGE_START_CAPTURE,
                                [0,
                                 interval, # interval
                                 count, # number of  images to capture
                                 self.image_capture_sequence_number, # Sequence number starting from 1. This is only valid for single-capture (param3 == 1), otherwise set to 0.  Increment the capture ID for each capture command to prevent double captures when a command is re-transmitted.
                                 NAN, # Reserved
                                 NAN, # Reserved
                                 NAN]
                              ) # Reserved
        return self.wait_for_message.get()


    def image_stop_capture(self, target_system=None, target_component=None):
        """Stop image capture sequence"""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_IMAGE_STOP_CAPTURE
        target_system, target_component = check_target(self, target_system, target_component)
        t = self.send_command(target_system, target_component,
                                mavlink.MAV_CMD_IMAGE_STOP_CAPTURE,
                                [0, NAN, NAN, NAN, NAN, NAN, NAN]
                              )

    def video_start_capture(self, target_system=None, target_component=None, video_stream_id=0, # Video stream id (0 for all streams)
                            frequency=1): # Frequency CAMERA_CAPTURE_STATUS messages should be sent while recording (0 for no messages, otherwise frequency in Hz)
        """Start video capture"""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_VIDEO_START_CAPTURE
        target_system, target_component = check_target(self, target_system, target_component)
        t = self.send_command(target_system, target_component,
                                mavlink.MAV_CMD_VIDEO_START_CAPTURE,
                                [video_stream_id, # Video stream id (0 for all streams)
                                 frequency, # Frequency CAMERA_CAPTURE_STATUS messages should be sent while recording (0 for no messages, otherwise frequency in Hz)
                                 NAN, NAN, 0, 0, NAN]
                              )

    def video_stop_capture(self, target_system=None, target_component=None, video_stream_id=0): # Video stream id (0 for all streams)
        """Stop video capture"""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_VIDEO_STOP_CAPTURE
        target_system, target_component = check_target(self, target_system, target_component)
        t = self.send_command(target_system, target_component,
                                mavlink.MAV_CMD_VIDEO_STOP_CAPTURE,
                                [video_stream_id, NAN, NAN, NAN, NAN, NAN, NAN]
                              )

    def video_start_streaming(self, target_system=None, target_component=None, video_stream_id=0, # Video Stream ID (0 for all streams)
                                ):
        """Start video streaming"""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_VIDEO_START_STREAMING
        target_system, target_component = check_target(self, target_system, target_component)
        t = self.send_command(target_system, target_component,
                                mavlink.MAV_CMD_VIDEO_START_STREAMING,
                                [video_stream_id, NAN, NAN, NAN, NAN, NAN, NAN]
                                )

    def video_stop_streaming(self, target_system=None, target_component=None, video_stream_id=0): # Video Stream ID (0 for all streams)
        """Stop the video stream"""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_VIDEO_STOP_STREAMING
        target_system, target_component = check_target(self, target_system, target_component)
        t = self.send_command(target_system, target_component,
                                mavlink.MAV_CMD_VIDEO_STOP_STREAMING,
                                [video_stream_id, NAN, NAN, NAN, NAN, NAN, NAN]
                              )






