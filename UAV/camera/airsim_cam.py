

__all__ = [ 'AirsimCamera', 'videoCamera']


import time, os, sys
from pathlib import Path

from ..logging import logging, LogLevels
# # from ..mavlink.mavcom import MAVCom, time_since_boot_ms, time_UTC_usec, boot_time_str, date_time_str
# from ..utils.general import time_since_boot_ms, time_UTC_usec, boot_time_str, date_time_str
# from ..mavlink.component import Component, mavutil, mavlink, MAVLink
try:
    # allow import of gstreamer to fail if not installed (for github actions)
    from gstreamer import GstPipeline, GstVideoSource, GstVideoSave, GstJpegEnc, GstStreamUDP, GstVideoSink
    from gstreamer.utils import to_gst_string
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

WIDTH, HEIGHT = 800, 450
WIDTH, HEIGHT = 1920, 1080
class AirsimCamera(GSTCamera):

    """ run the airsim enviroment Create a airsim camera component for testing using GStreamer"""

    def __init__(self,
                 camera_dict=None,  # camera_info dict
                 udp_encoder='H264',  # encoder for video streaming
                 loglevel=LogLevels.INFO):  # log flag
        super().__init__(camera_dict=camera_dict, udp_encoder=udp_encoder, loglevel=loglevel)

        config_path = Path(__file__).parent.parent / "config"
        # self.rs = RunSim("AirSimNH", settings=config_path / "airsim_settings_high_res.json")
        # self.rs = RunSim("AirSimNH", settings=config_path / "airsim_settings.json")
        self.rs = RunSim("AirSimNH")
        self.asc = AirSimClient()
        print(
              f"{loglevel = } {self._loglevel = }")

    def open(self):
        """create and start the gstreamer pipeleine for the camera"""
        command = to_gst_string(self.camera_dict['gstreamer']['src_pipeline'])
        # command = to_gst_string( ['appsrc emit-signals=True is-live=True', 'queue', 'videoconvert', 'xvimagesink sync=false'])
        # command = to_gst_string( ['appsrc emit-signals=True is-live=True', 'queue', 'videoconvert',
        #                           'x264enc tune=zerolatency',
        #                           'rtph264pay ! udpsink host=127.0.0.1 port=5000'])
        self.fps = self.camera_dict['gstreamer']['fps']
        self.pipeline = GstVideoSink(command, width=WIDTH, height=HEIGHT, fps=self.fps, loglevel=self._loglevel)
        # print(f"{self._loglevel = }")

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
            state = self.asc.getMultirotorState()
            pos = state.kinematics_estimated.position
            img = self.asc.get_image(cams[cam_num], rgb2bgr=True)
            puttext(img, f"Frame: {framecounter} Pos: {pos.x_val:.2f}, {pos.y_val:.2f}, {pos.z_val:.2f}")

            # img = resize(img, width=WIDTH)
            self.pipeline.push(buffer=img)
            time.sleep(1/self.fps) # set fps to self.fps

        self.log.debug("Exiting AirsimCamera thread")

    def close(self):
        """Close the camera component."""
        self._running = False
        self.rs.exit()
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


