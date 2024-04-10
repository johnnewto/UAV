__all__ = ['AirsimGimbal']

import time

import numpy as np

from .gimbal import Gimbal
from ..logging import LogLevels
from ..utils import config_dir

from ..airsim.client import AirSimClient
import threading


# cams = ["high_res", "front_center", "front_right", "front_left", "bottom_center", "back_center"]
# quaternion reotate 90 degrees around z axis

# def rotate_camera_pitch_yaw(self, camera_name,
#                             pitch,
#                             yaw,
#                             ):
#     pose = super(AirSimClient, self).simGetCameraInfo(camera_name).pose
#     existing_orientation = pose.orientation
#     # get the vector of the existing orientation
#     existing_angles = airsim.to_eularian_angles(existing_orientation)
#     print(f"{existing_angles = }")
#

class AirsimGimbal(Gimbal):
    """ adjust the orientation of the airsim gimbal"""

    def __init__(self,
                 camera_name="center",
                 settings_dict=None,  # settings dict
                 loglevel=LogLevels.INFO):  # log flag

        # _dict = settings_dict['gstreamer_video_src']
        self.camera_name = camera_name
        self.settings_dict = settings_dict
        self._dont_wait = threading.Event()  # used to pause or resume the thread

        config_file = config_dir() / "airsim_settings_high_res.json"

        self._dont_wait = threading.Event()  # used to pause or resume the thread
        super().__init__(loglevel=loglevel)
        self.log.info(f"***** AirsimGimbal: {camera_name = } ******")
        try:
            self.asc = AirSimClient()
            self.camera_angle = self.asc.get_cam_angle(camera_name)
        except:
            self.asc = None
            self.log.error("Airsim not running")
            assert False

    def manual_pitch_yaw(self, pitch, yaw):
        """ manual position the camera by increments """
        self.log.info(f"manual position camera by {pitch = } {yaw = }")
        self.camera_angle[0] += pitch
        self.camera_angle[2] += yaw
        # Convert angles to radians
        pitch = np.deg2rad(self.camera_angle[0])
        yaw = np.deg2rad(self.camera_angle[2])
        self.asc.set_camera_orientation(camera_name=self.camera_name, roll=0, pitch=pitch, yaw=yaw)

    def set_pitch_yaw(self, pitch, yaw, pitchspeed, yawspeed):
        """Set the attitude of the gimbal"""
        self.camera_angle[0] = pitch
        self.camera_angle[2] = yaw
        try:
            pitch = np.deg2rad(self.camera_angle[0])
            yaw = np.deg2rad(self.camera_angle[2])
            self.asc.set_camera_orientation(camera_name=self.camera_name, roll=0, pitch=pitch, yaw=yaw)
            self.log.info(f"Airsim Gimbal {self.camera_name}: {pitch = } {yaw = } {pitchspeed = } {yawspeed = }")
        except Exception as e:
            self.log.error(f"Airsim not running {e}")

    def close(self):
        """Close the gimbal."""
        self.log.info("Closing  AirsimGimbal")
