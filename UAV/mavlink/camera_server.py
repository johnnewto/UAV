


__all__ = ['NAN', 'CAMERA_INFORMATION', 'CAMERA_SETTINGS', 'STORAGE_INFORMATION', 'CAMERA_CAPTURE_STATUS',
           'CAMERA_IMAGE_CAPTURED', 'read_camera_info_from_toml', 'CameraServer', 'Component']


import time, os, sys

from ..camera.fake_cam import GSTCamera, BaseCamera
from ..logging import logging
# from .mavcom import MAVCom, time_since_boot_ms, time_UTC_usec, boot_time_str, date_time_str
from .component import Component, mavutil, mavlink, MAVLink
import threading
import cv2
import numpy as np
import toml



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



def read_camera_info_from_toml(toml_file_path):
    """Read MAVLink camera info from a TOML file."""
    with open(toml_file_path, 'rb') as file:
        data = toml.load(file)

    camera_info = data['camera_info']
    camera_info['vendor_name'] = [int(b) for b in camera_info['vendor_name'].encode()]
    camera_info['model_name'] = [int(b) for b in camera_info['model_name'].encode()]
    # Extract camera_info
    return data['camera_info']





class CameraServer(Component):
    """Create a mavlink Camera server Component using a test GSTREAMER pipeline"""

    def __init__(self,
                 source_component,  # used for component indication
                 mav_type,  # used for heartbeat MAV_TYPE indication
                 camera, # camera  (or FakeCamera for testing)
                 debug,  # logging level
                ):
        super().__init__( source_component=source_component, mav_type=mav_type, debug=debug)
        self.set_message_callback(self.on_message)


        self.camera:GSTCamera = camera


    def on_mav_connection(self):
        """Start the mavlink connection"""
        super().on_mav_connection()
        assert self.mav is not None, "call set_mav first"
        if self.camera is None:
            self.log.warning(f"Component has no camera object")
            self.camera = BaseCamera()
        self.camera.mav = self.mav  # set the mavlink connection for mavlink messages


    def on_message(self, msg # type: Message
                   ) -> bool: # return True to indicate that the message has been handled
        """Callback for a command received from the client
        """

        if msg.get_type() == "COMMAND_LONG":
            # print(f"Command  {msg.command = } ")
            if msg.command == mavlink.MAV_CMD_REQUEST_CAMERA_CAPTURE_STATUS:
                self.camera_capture_status_send()
                return True # return True to indicate that the message has been handled

            elif msg.command == mavlink.MAV_CMD_REQUEST_CAMERA_INFORMATION:
                self.camera_information_send()
                return True # return True to indicate that the message has been handled

            elif msg.command == mavlink.MAV_CMD_REQUEST_CAMERA_SETTINGS:
                # self.send_ack(msg)
                self.camera_settings_send()
                return True

            elif msg.command == mavlink.MAV_CMD_REQUEST_STORAGE_INFORMATION:
                self.storage_information_send()
                return True

            elif msg.command == mavlink.MAV_CMD_STORAGE_FORMAT:
                self.storage_format(msg)
                return True

            elif msg.command == mavlink.MAV_CMD_SET_CAMERA_ZOOM:
                # self.log.info(f"***** Zoom {msg}")
                # print(f"Zoom {msg.param2 = }")
                self.set_camera_zoom(msg)
                return True

            elif msg.command == mavlink.MAV_CMD_IMAGE_START_CAPTURE:
                self.image_start_capture(msg)
                return True # return True to indicate that the message has been handled

            elif msg.command == mavlink.MAV_CMD_IMAGE_STOP_CAPTURE:
                self.image_stop_capture(msg)
                return True

            elif msg.command == mavlink.MAV_CMD_VIDEO_START_CAPTURE:
                self.video_start_capture(msg)
                return True

            elif msg.command == mavlink.MAV_CMD_VIDEO_STOP_CAPTURE:
                self.video_stop_capture(msg)
                return True

            elif msg.command == mavlink.MAV_CMD_SET_CAMERA_MODE:
                self.set_camera_mode(msg)
                return True # return True to indicate that the message has been handled

            elif msg.command == mavlink.MAV_CMD_VIDEO_START_STREAMING:
                self.video_start_streaming(msg)
                return True # return True to indicate that the message has been handled

            elif msg.command == mavlink.MAV_CMD_VIDEO_STOP_STREAMING:
                self.video_stop_streaming(msg)
                return True # return True to indicate that the message has been handled


            
        else:
            self.log.debug(f"Unknown command {msg.get_type()} received from {msg.get_srcSystem()}/{msg.get_srcComponent()}")
            return False # return False to indicate that the message has not been handled

        
    def camera_capture_status_send(self):
        """ Information about the status of a capture. Can be requested with a
            MAV_CMD_REQUEST_MESSAGE command."""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_REQUEST_CAMERA_CAPTURE_STATUS
        try:
            self.camera.camera_capture_status_send()
        except AttributeError as err:
            self.log.error(f"{err = }")

        # if self.camera is None:
        #     self.log.warning(f"Component has no camera object")
        #     return
        # self.mav.camera_capture_status_send(time_since_boot_ms(), # time_boot_ms
        #                                     0, # image status
        #                                     0, # video status
        #                                     0, # image interval
        #                                     0, # recording time ms
        #                                     0, # available capacity
        #                                     0, # image count
        #                                     )

    def camera_information_send(self):
        """ Information about a camera. Can be requested with a
            MAV_CMD_REQUEST_MESSAGE command."""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_REQUEST_CAMERA_INFORMATION
        try:
            self.camera.camera_information_send()
        except AttributeError as err:
            self.log.error(f"{err = }")


    def camera_settings_send(self):
        """ Settings of a camera. Can be requested with a
            MAV_CMD_REQUEST_MESSAGE command."""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_REQUEST_CAMERA_SETTINGS
        try:
            self.camera.camera_settings_send()
        except AttributeError as err:
            self.log.error(f"{err = }")

        # if self.camera is None:
        #     self.log.warning(f"Component has no camera object")
        #     return
        # nan = float("nan")
        # self.mav.camera_settings_send(time_since_boot_ms(), # time_boot_ms
        #                               0, # https://mavlink.io/en/messages/common.html#CAMERA_MODE
        #                               NAN, # Current zoom level as a percentage of the full range (0.0 to 100.0, NaN if not known)
        #                               NAN, # Current focus level as a percentage of the full range (0.0 to 100.0, NaN if not known)
        #                               )

    def storage_information_send(self):
        """ Information about a storage medium. This message is sent in response to
            MAV_CMD_REQUEST_MESSAGE."""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_REQUEST_STORAGE_INFORMATION
        try:
            self.camera.storage_information_send()
        except AttributeError as err:
            self.log.error(f"{err = }")



    def storage_format(self, msg):
        """ A message containing the result of the format attempt (asynchronous)."""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_STORAGE_FORMAT
        self.log.error(f"storage_format_send not implemented")
        # do format storage
        storage_id = msg.param1
        format =    msg.param2
        reset_image_log = msg.param3
        self.storage_information_send()
 



    def set_camera_zoom(self, msg):
        """ Set the camera zoom """
        # https://mavlink.io/en/messages/common.html#MAV_CMD_SET_CAMERA_ZOOM
        try:
            self.camera.set_camera_zoom(msg.param2)
        except AttributeError as err:
            self.log.error(f"{err = }")
        
        
    def image_start_capture(self, msg):
        """Start image capture sequence."""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_IMAGE_START_CAPTURE
        try:
            interval = msg.param2
            count = msg.param3
            self.camera.image_start_capture(interval, count)
        except AttributeError as err:
            self.log.error(f"{err = }")


    def image_stop_capture(self, msg):
        """Stop image capture sequence"""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_IMAGE_STOP_CAPTURE
        try:

            self.camera.image_stop_capture()
        except AttributeError as err:
            self.log.error(f"{err = }")


    def video_start_capture(self, msg):
        """Start video capture"""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_VIDEO_START_CAPTURE
        try:
            stream_id = msg.param1
            frequency = msg.param2  # Frequency CAMERA_CAPTURE_STATUS messages should be sent while recording (0 for no messages, otherwise frequency in Hz)

            self.camera.video_start_capture(stream_id, frequency)
        except AttributeError as err:
            self.log.error(f"{err = }")



    def video_stop_capture(self, msg):
        """Stop video capture"""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_VIDEO_STOP_CAPTURE
        try:
            self.camera.video_stop_capture()
        except AttributeError as err:
            self.log.error(f"{err = }")


    def video_start_streaming(self, msg):
        """Start video streaming"""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_VIDEO_START_STREAMING
        # todo get parameters from message
        print("todo get parameters from message")
        try:
            self.camera.video_start_streaming(0)
        except AttributeError as err:
            self.log.error(f"{err = }")


    def video_stop_streaming(self, msg):
        """Stop video streaming"""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_VIDEO_STOP_STREAMING
        # todo get parameters from message
        print("todo get parameters from message")
        try:
            self.camera.video_stop_streaming(0)
        except AttributeError as err:
            self.log.error(f"{err = }")


    def set_camera_mode(self, msg):
        """ Set the camera mode"""
        # https://mavlink.io/en/messages/common.html#MAV_CMD_SET_CAMERA_MODE
        try:
            self.camera.set_camera_mode(msg.param2)
        except AttributeError as err:
            self.log.error(f"{err = }")





    def close(self):
        """Close the connection to the camera"""
        if self.camera is not None:
            self.camera.close()
        super().close()
        self.log.debug(f"Closed connection to camera")
        return True
    

