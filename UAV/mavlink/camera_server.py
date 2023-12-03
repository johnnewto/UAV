from __future__ import annotations

__all__ = ['NAN', 'CAMERA_INFORMATION', 'CAMERA_SETTINGS', 'STORAGE_INFORMATION', 'CAMERA_CAPTURE_STATUS',
           'CAMERA_IMAGE_CAPTURED', 'CameraServer', 'Component']

import time, os, sys

from ..cameras.gst_cam import GSTCamera, BaseCamera
from ..logging import logging, LogLevels
# from .mavcom import MAVCom, time_since_boot_ms, time_UTC_usec, boot_time_str, date_time_str
from .component import Component, mavutil, mavlink, MAVLink
import threading
import cv2
import numpy as np

# import toml


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
CAMERA_INFORMATION = mavlink.MAVLINK_MSG_ID_CAMERA_INFORMATION  # https://mavlink.io/en/messages/common.html#CAMERA_INFORMATION
CAMERA_SETTINGS = mavlink.MAVLINK_MSG_ID_CAMERA_SETTINGS  # https://mavlink.io/en/messages/common.html#CAMERA_SETTINGS
STORAGE_INFORMATION = mavlink.MAVLINK_MSG_ID_STORAGE_INFORMATION  # https://mavlink.io/en/messages/common.html#STORAGE_INFORMATION
CAMERA_CAPTURE_STATUS = mavlink.MAVLINK_MSG_ID_CAMERA_CAPTURE_STATUS  # https://mavlink.io/en/messages/common.html#CAMERA_CAPTURE_STATUS
CAMERA_IMAGE_CAPTURED = mavlink.MAVLINK_MSG_ID_CAMERA_IMAGE_CAPTURED  # https://mavlink.io/en/messages/common.html#CAMERA_IMAGE_CAPTURED


# def read_camera_info_from_toml(toml_file_path):
#     """Read MAVLink cameras info from a TOML file."""
#     with open(toml_file_path, 'rb') as file:
#         data = toml.load(file)
#
#     camera_info = data['camera_info']
#     camera_info['vendor_name'] = [int(b) for b in camera_info['vendor_name'].encode()]
#     camera_info['model_name'] = [int(b) for b in camera_info['model_name'].encode()]
#     # Extract camera_info
#     return data['camera_info']

# def try_log(func):  # decorator
#     """Decorator to log exceptions in functions, returns True if no exception"""
#     def wrapper(*args, **kwargs):
#         try:
#             func(*args, **kwargs)
#             return True
#         except Exception as err:
#             try:
#                 args[0].log.error(f"{err = }")   # args[0] is self for the class
#             except:
#                 logging.error(f"{err = }")
#             return False

#     return wrapper


class CameraServer(Component):
    """Create a mavlink Camera server Component, cameras argument will normally be a  gstreamer pipeline"""
    mav_cmd_list = [mavlink.MAV_CMD_REQUEST_MESSAGE,
                    mavlink.MAV_CMD_STORAGE_FORMAT,
                    mavlink.MAV_CMD_SET_CAMERA_ZOOM,
                    mavlink.MAV_CMD_IMAGE_START_CAPTURE,
                    mavlink.MAV_CMD_IMAGE_STOP_CAPTURE,
                    mavlink.MAV_CMD_VIDEO_START_CAPTURE,
                    mavlink.MAV_CMD_VIDEO_STOP_CAPTURE,
                    mavlink.MAV_CMD_SET_CAMERA_MODE,
                    mavlink.MAV_CMD_VIDEO_START_STREAMING,
                    mavlink.MAV_CMD_VIDEO_STOP_STREAMING,
                    ]
    mav_msg_id_list = [("MAVLINK_MSG_ID_CAMERA_INFORMATION", mavlink.MAVLINK_MSG_ID_CAMERA_INFORMATION),
                       ("MAVLINK_MSG_ID_CAMERA_SETTINGS", mavlink.MAVLINK_MSG_ID_CAMERA_SETTINGS),
                       ("MAVLINK_MSG_ID_STORAGE_INFORMATION", mavlink.MAVLINK_MSG_ID_STORAGE_INFORMATION),
                       ("MAVLINK_MSG_ID_CAMERA_CAPTURE_STATUS", mavlink.MAVLINK_MSG_ID_CAMERA_CAPTURE_STATUS),
                       ("MAVLINK_MSG_ID_CAMERA_IMAGE_CAPTURED", mavlink.MAVLINK_MSG_ID_CAMERA_IMAGE_CAPTURED),
                       ("MAVLINK_MSG_ID_VIDEO_STREAM_INFORMATION", mavlink.MAVLINK_MSG_ID_VIDEO_STREAM_INFORMATION),
                       ("MAVLINK_MSG_ID_VIDEO_STREAM_STATUS", mavlink.MAVLINK_MSG_ID_VIDEO_STREAM_STATUS),
                       ]

    def __init__(self,
                 source_component=mavlink.MAV_COMP_ID_CAMERA,  # used for component indication
                 mav_type=mavlink.MAV_TYPE_CAMERA,  # used for heartbeat MAV_TYPE indication
                 camera=None,  # cameras  (or FakeCamera for testing)
                 loglevel: LogLevels | int = LogLevels.INFO,  # logging level
                 ):

        super().__init__(source_component=source_component, mav_type=mav_type, loglevel=loglevel)
        # self.set_log(loglevel)
        self._set_message_callback(self.on_message)

        self.camera: GSTCamera = camera

    def on_mav_connection(self):
        """Start the mavlink connection"""
        super().on_mav_connection()
        assert self.mav is not None, "call set_mav first"
        if self.camera is None:
            self.log.warning(f"Component has no cameras object")
            self.camera = BaseCamera()
        self.camera.mav = self.mav  # set the mavlink connection for mavlink messages
        self.camera.source_system = self.source_system
        self.camera.source_component = self.source_component
        # self.set_source_compenent()
        # self.cameras.mav.srcComponent = self.source_component

    def list_commands(self):
        """List the commands supported by the cameras server
        https://mavlink.io/en/messages/common.html
        https://mavlink.io/en/messages/common.html#MAV_CMD_REQUEST_CAMERA_INFORMATION
        https://mavlink.io/en/messages/common.html#MAV_CMD_REQUEST_CAMERA_SETTINGS
        https://mavlink.io/en/messages/common.html#MAV_CMD_REQUEST_STORAGE_INFORMATION
        https://mavlink.io/en/messages/common.html#MAV_CMD_STORAGE_FORMAT
        https://mavlink.io/en/messages/common.html#MAV_CMD_SET_CAMERA_ZOOM
        etc

        """
        print("Supported Commands: https://mavlink.io/en/messages/common.html#mav_commands")
        for cmd in self.mav_cmd_list:
            detail = mavlink.enums['MAV_CMD'][cmd]
            print(f" Cmd = {detail.name}: {cmd} ")  #: '{detail.description}'")

        print("Supported Message Requests:  https://mavlink.io/en/messages/common.html#messages")
        print()
        for msg in self.mav_msg_id_list:
            print(f"{msg[0]}:  {msg[1]}")

    def on_message(self, msg: mavlink.MAVLink_command_long_message  # : mavlink  Message
                   ) -> bool:  # return True to indicate that the message has been handled
        """Callback for a command received from the client
        This will respond to the mavlink cameras and storage focused commands:
        """
        self.set_source_compenent()  # set the source component for the reply

        if msg.get_type() == "COMMAND_LONG":

            if msg.command == mavlink.MAV_CMD_REQUEST_MESSAGE:
                if msg.param1 == mavlink.MAVLINK_MSG_ID_CAMERA_INFORMATION:
                    return self._camera_information_send()

                elif msg.param1 == mavlink.MAVLINK_MSG_ID_CAMERA_SETTINGS:
                    return self._camera_settings_send()

                elif msg.param1 == mavlink.MAVLINK_MSG_ID_STORAGE_INFORMATION:
                    return self._storage_information_send()

                elif msg.param1 == mavlink.MAVLINK_MSG_ID_CAMERA_CAPTURE_STATUS:
                    return self._camera_capture_status_send()

                else:
                    self.log.warning(f"Unknown message type {msg.param1}")
                    return False

            # if msg.command == mavlink.MAV_CMD_REQUEST_CAMERA_CAPTURE_STATUS:
            #     self._camera_capture_status_send()
            #     return True # return True to indicate that the message has been handled
            #
            # elif msg.command == mavlink.MAV_CMD_REQUEST_CAMERA_INFORMATION:
            #     self._camera_information_send()
            #     return True # return True to indicate that the message has been handled
            #
            # elif msg.command == mavlink.MAV_CMD_REQUEST_CAMERA_SETTINGS:
            #     # self.send_ack(msg)
            #     self._camera_settings_send()
            #     return True
            #
            # elif msg.command == mavlink.MAV_CMD_REQUEST_STORAGE_INFORMATION:
            #     self._storage_information_send()
            #     return True

            elif msg.command == mavlink.MAV_CMD_STORAGE_FORMAT:
                return self._storage_format(msg)

            elif msg.command == mavlink.MAV_CMD_SET_CAMERA_ZOOM:
                # self.log.info(f"***** Zoom {msg}")
                # print(f"Zoom {msg.param2 = }")
                return self._set_camera_zoom(msg)

            elif msg.command == mavlink.MAV_CMD_IMAGE_START_CAPTURE:
                return self._image_start_capture(msg)

            elif msg.command == mavlink.MAV_CMD_IMAGE_STOP_CAPTURE:
                return self._image_stop_capture(msg)

            elif msg.command == mavlink.MAV_CMD_VIDEO_START_CAPTURE:
                return self._video_start_capture(msg)

            elif msg.command == mavlink.MAV_CMD_VIDEO_STOP_CAPTURE:
                return self._video_stop_capture(msg)

            elif msg.command == mavlink.MAV_CMD_SET_CAMERA_MODE:
                return self._set_camera_mode(msg)

            elif msg.command == mavlink.MAV_CMD_VIDEO_START_STREAMING:
                return self._video_start_streaming(msg)  # return True to indicate that the message has been handled

            elif msg.command == mavlink.MAV_CMD_VIDEO_STOP_STREAMING:
                return self._video_stop_streaming(msg)  # return True to indicate that the message has been handled

        else:
            self.log.debug(
                f"Unknown command {msg.get_type()} received from {msg.get_srcSystem()}/{msg.get_srcComponent()}")
            return False  # return False to indicate that the message has not been handled

    def _camera_capture_status_send(self):
        """ Information about the status of a capture. Can be requested with a
            MAV_CMD_REQUEST_MESSAGE command.
            https://mavlink.io/en/messages/common.html#MAV_CMD_REQUEST_CAMERA_CAPTURE_STATUS """
        try:
            self.camera.camera_capture_status_send()
            return True
        except Exception as err:
            self.log.error(f"{err = }")
            return False

    def _camera_information_send(self):
        """ Information about a cameras. Can be requested with a
            MAV_CMD_REQUEST_MESSAGE command
            https://mavlink.io/en/messages/common.html#MAV_CMD_REQUEST_CAMERA_INFORMATION
        """
        try:
            self.camera.camera_information_send()
            return True
        except Exception as err:
            self.log.error(f"{err = }")
            return False

    def _camera_settings_send(self):
        """ Settings of a cameras. Can be requested with a
            MAV_CMD_REQUEST_MESSAGE command.
            https://mavlink.io/en/messages/common.html#MAV_CMD_REQUEST_CAMERA_SETTINGS
        """
        try:
            self.camera.camera_settings_send()
            return True
        except Exception as err:
            self.log.error(f"{err = }")
            return False
        # if self.cameras is None:
        #     self.log.warning(f"Component has no cameras object")
        #     return
        # nan = float("nan")
        # self.mav.camera_settings_send(time_since_boot_ms(), # time_boot_ms
        #                               0, # https://mavlink.io/en/messages/common.html#CAMERA_MODE
        #                               NAN, # Current zoom level as a percentage of the full range (0.0 to 100.0, NaN if not known)
        #                               NAN, # Current focus level as a percentage of the full range (0.0 to 100.0, NaN if not known)
        #                               )

    def _storage_information_send(self):
        """ Information about a storage medium. This message is sent in response to
            MAV_CMD_REQUEST_MESSAGE.
            https://mavlink.io/en/messages/common.html#MAV_CMD_REQUEST_STORAGE_INFORMATION """
        try:
            self.camera.storage_information_send()
            return True
        except Exception as err:
            self.log.error(f"{err = }")
            return False
        
    def _storage_format(self, msg):
        """ A message containing the result of the format attempt (asynchronous).
            https://mavlink.io/en/messages/common.html#MAV_CMD_STORAGE_FORMAT """
        self.log.error(f"storage_format_send not implemented")
        # do format storage
        storage_id = msg.param1
        format = msg.param2
        reset_image_log = msg.param3
        try:
            self._storage_information_send()
            return True
        except Exception as err:
            self.log.error(f"{err = }")
            return False

    def _set_camera_zoom(self, msg):
        """ Set the cameras zoom
            https://mavlink.io/en/messages/common.html#MAV_CMD_SET_CAMERA_ZOOM  """
        try:
            self.camera.set_camera_zoom(msg.param2)
            return True
        except Exception as err:
            self.log.error(f"{err = }")
            return False

    def __image_start_capture(self, msg):
        """ Start image capture sequence.
            https://mavlink.io/en/messages/common.html#MAV_CMD_IMAGE_START_CAPTURE
        """
        interval = msg.param2
        count = msg.param3
        try:
            self.camera.image_start_capture(interval, count)
            return True
        except Exception as err:
            self.log.error(f"{err = }")
            return False

    def _image_start_capture(self, msg):
        """ Start image capture sequence.
            https://mavlink.io/en/messages/common.html#MAV_CMD_IMAGE_START_CAPTURE
        """
        interval = msg.param2
        count = msg.param3
        try:
            self.camera.image_start_capture(interval, count)
            return True
        except Exception as err:
            self.log.error(f"{err = }")
            return False

    def _image_stop_capture(self, msg):
        """ Stop image capture sequence
            https://mavlink.io/en/messages/common.html#MAV_CMD_IMAGE_STOP_CAPTURE """
        try:
            self.camera.image_stop_capture()
            return True
        except Exception as err:
            self.log.error(f"{err = }")
            return False

    def _video_start_capture(self, msg):
        """ Start video capture
            https://mavlink.io/en/messages/common.html#MAV_CMD_VIDEO_START_CAPTURE
        """
        stream_id = msg.param1
        frequency = msg.param2  # Frequency CAMERA_CAPTURE_STATUS messages should be sent while recording (0 for no messages, otherwise frequency in Hz)
        try:
            self.camera.video_start_capture(stream_id, frequency)
            return True
        except Exception as err:
            self.log.error(f"{err = }")
            return False
        
    def _video_stop_capture(self, msg):
        """ top video capture
            https://mavlink.io/en/messages/common.html#MAV_CMD_VIDEO_STOP_CAPTURE """
        try:
            self.camera.video_stop_capture()
            return True
        except Exception as err:
            self.log.error(f"{err = }")
            return False
        
    def _video_start_streaming(self, msg):
        """ Start video streaming
            https://mavlink.io/en/messages/common.html#MAV_CMD_VIDEO_START_STREAMING """
        streamId = msg.param1
        try:
            self.camera.video_start_streaming(streamId)
            self.log.info(f"Started video streaming: {streamId = }")
            return True
        except Exception as err:
            self.log.error(f"{err = }")
            return False
        
    def _video_stop_streaming(self, msg):
        """ Stop video streaming
            https://mavlink.io/en/messages/common.html#MAV_CMD_VIDEO_STOP_STREAMING """
        # print("todo get parameters from message")
        try:
            self.camera.video_stop_streaming()
            return True
        except Exception as err:
            self.log.error(f"{err = }")
            return False
        
    def _set_camera_mode(self, msg):
        """ Set the cameras mode
            https://mavlink.io/en/messages/common.html#MAV_CMD_SET_CAMERA_MODE """
        try:
            self.camera.set_camera_mode(msg.param2)
            return True
        except Exception as err:
            self.log.error(f"{err = }")
            return False
        
    def close(self):
        """Close the connection to the cameras"""
        if self.camera is not None:
            self.camera.close()
        super().close()
        self.log.debug(f"Closed connection to cameras")
        return True
