__all__ = ['AirsimCamera', 'videoCamera']

import json
import time, os, sys
from pathlib import Path

from ..logging import logging, LogLevels
from ..utils import find_config_dir

# # from ..mavlink.mavcom import MAVCom, time_since_boot_ms, time_UTC_usec, boot_time_str, date_time_str
# from ..utils.general import time_since_boot_ms, time_UTC_usec, boot_time_str, date_time_str
# from ..mavlink.component import Component, mavutil, mavlink, MAVLink
try:
    # allow import of gstreamer to fail if not installed (for github actions)
    from gstreamer import GstPipeline, GstVideoSource, GstVideoSave, GstJpegEnc, GstStreamUDP, GstVideoSink
    import gstreamer.utils as gst_utils
except:
    print("GStreamer is not installed")
    pass
from ..camera.gst_cam import GSTCamera
from ..utils.sim_linux import RunSim
from ..airsim.client import AirSimClient
import threading
from UAV.utils.display import puttext
from imutils import resize
import cv2
import numpy as np

cams = ["high_res", "front_center", "front_right", "front_left", "bottom_center", "back_center"]

# WIDTH, HEIGHT = 800, 450
WIDTH, HEIGHT = 1920, 1080


class AirsimCamera(GSTCamera):
    """ run the airsim enviroment Create a airsim camera component for testing using GStreamer"""

    def __init__(self,
                 camera_name="high_res",
                 camera_dict=None,  # camera_info dict
                 udp_encoder='H264',  # encoder for video streaming
                 loglevel=LogLevels.INFO):  # log flag
        super().__init__(camera_dict=camera_dict, udp_encoder=udp_encoder, loglevel=loglevel)

        config_file = find_config_dir() / "airsim_settings_high_res.json"
        _dict = camera_dict['gstreamer_src_intervideosink']
        self.check_airsm_camera_resolution(config_file, camera_name, _dict['width'], _dict['height'])
        self.rs = RunSim("AirSimNH", settings=config_file)

        # self.rs = RunSim("AirSimNH", settings=find_config_dir() / "airsim_settings.json")
        self.asc = AirSimClient()

        print(
            f"{loglevel = } {self._loglevel = }")

    def check_airsm_camera_resolution(self, settings_file_path, camera_name, desired_width, desired_height):
        """check the airsim camera resolution and update if necessary"""
        import json

        # Read the existing settings.json file
        with open(settings_file_path, 'r') as json_file:
            settings = json.load(json_file)

        # Find the camera section you want to modify
        try:
            camera_settings = settings['Vehicles']['Drone1']['Cameras'].get(camera_name)
            if camera_settings:
                # Get the current width and height
                current_width = camera_settings['CaptureSettings'][0]['Width']
                current_height = camera_settings['CaptureSettings'][0]['Height']

                # Check if the current resolution is different from the desired resolution
                if current_width != desired_width or current_height != desired_height:
                    # Update the width and height settings
                    camera_settings['CaptureSettings'][0]['Width'] = desired_width
                    camera_settings['CaptureSettings'][0]['Height'] = desired_height

                    # Write the updated settings back to the file
                    with open(settings_file_path, 'w') as json_file:
                        json.dump(settings, json_file, indent=4)
                        self.log.info(f"Updated {camera_name} width and height settings in {settings_file_path}")

        except Exception as e:
            self.log.error(f"Error updating {camera_name} width and height settings in {settings_file_path}: {e}")

    def open(self):
        """create and start the gstreamer pipeleine for the camera"""
        _dict = self.camera_dict['gstreamer_src_intervideosink']
        self.width, self.height, self.fps = _dict['width'], _dict['height'], _dict['fps']
        pipeline = gst_utils.format_pipeline(**_dict)
        self.pipeline = GstVideoSink(pipeline, width=self.width, height=self.height, fps=self.fps, loglevel=self._loglevel)

        self.pipeline.startup()
        self._thread = threading.Thread(target=self.run_pipe, daemon=True)
        self._thread.start()

        return self

    def run_pipe(self):
        """run the camera pipeline in a thread"""
        cam_num = 0
        # width, height = 800, 450
        framecounter = 1
        self._running = True

        while self._running:
            # print(framecounter)
            framecounter += 1
            # state = self.asc.getMultirotorState()
            # pos = state.kinematics_estimated.position
            img = self.asc.get_image(cams[cam_num], rgb2bgr=True)
            # puttext(img, f"Frame: {framecounter} Pos: {pos.x_val:.2f}, {pos.y_val:.2f}, {pos.z_val:.2f}")
            # create a blank image
            # img = np.zeros((HEIGHT, WIDTH, 3), np.uint8)
            # img = resize(img, width=WIDTH)
            self.pipeline.push(buffer=img)
            if img.shape != (self.height, self.width,  3):   # numpy array are rows by columns = height by width
                self.log.error(f"Airsim img.shape = {img.shape} != {(self.height, self.width, 3)}")

            time.sleep(1 / self.fps)  # set fps to self.fps


        self.log.debug("Exiting AirsimCamera thread")

    def close(self):
        """Close the camera component."""
        self._running = False
        try:
            self.rs.exit()
        except:
            pass
        super().close()

    def __exit__(self, exc_type, exc_value, traceback):
        """Context manager exit point."""
        self.log.info("Exiting AirsimCamera")
        super().__exit__(exc_type, exc_value, traceback)
        self.close()
        return False  # re-raise any exceptions


def videoCamera(camera_name):
    """
    Set up streaming pipeline for Video camera
    """
    return True
