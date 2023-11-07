__all__ = ['Gimbal']

import time, os, sys
from typing import List

from ..logging import logging, LogLevels
# from ..mavlink.mavcom import MAVCom, time_since_boot_ms, time_UTC_usec, boot_time_str, date_time_str
from ..utils.general import time_since_boot_ms, time_UTC_usec, boot_time_str, date_time_str
from ..mavlink.component import Component, mavutil, mavlink, MAVLink
import time


# cams = ["high_res", "front_center", "front_right", "front_left", "bottom_center", "back_center"]


class Gimbal:
    """ adjust the orientation of the airsim gimbal"""

    def __init__(self,
                 # camera_name="",
                 # settings_dict=None,  # settings dict
                 loglevel=LogLevels.INFO):  # log flag

        # self.camera_name = camera_name
        # self.settings_dict = settings_dict
        self._log = None
        self._loglevel = loglevel
        self._log = logging.getLogger("uav.{}".format(self.__class__.__name__))
        self._log.setLevel(int(loglevel))

        # self.log.info(f"***** Gimbal: {camera_name = } ******")
        # self.camera_info = self.get_camera_info(self.camera_dict)  # camera_info dict
        #
        # self.model_name = self.camera_dict['camera_info']['model_name']
        self.mav: MAVLink = None  # camera_server.on_mav_connection() callback sets this  (line 84)
        self.source_system = None  # camera_server.on_mav_connection() callback sets this  (line 84)
        self.source_component = None  # camera_server.on_mav_connection() callback sets this  (line 84)

    def __str__(self) -> str:
        return self.__class__.__name__

    def __repr__(self) -> str:
        return "<{}>".format(self)

    @property
    def log(self) -> logging.Logger:
        return self._log

    def set_source_compenent(self):
        """Set the source component for the self.mav """
        try:
            self.mav.srcSystem = self.source_system
            self.mav.srcComponent = self.source_component
        except AttributeError:
            self.log.debug("No mav connection")
            # raise AttributeError

    def manual_pitch_yaw(self, pitch, yaw):
        """manual position the camera by increments"""
        self.log.warning(f" (Not implmented) manual position camera by {pitch = } {yaw = }")

    def set_pitch_yaw(self, pitch, yaw, pitchspeed, yawspeed):
        """Set the attitude of the gimbal"""
        self.log.info(f"  (Not implmented)  Pitch {pitch = } {yaw = } {pitchspeed = } {yawspeed = }")

    def close(self):
        """Close the gimbal component."""
        self.log.info("Closing the gimbal")

    def __enter__(self):
        """ Context manager entry point for with statement."""
        return self  # This value is assigned to the variable after 'as' in the 'with' statement

    def __exit__(self, exc_type, exc_value, traceback):
        """Context manager exit point."""
        self.close()
        return False  # re-raise any exceptions
