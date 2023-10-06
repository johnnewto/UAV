

__all__ = [ 'AirsimCamera', 'videoCamera']


import time, os, sys

from ..logging import logging, LogLevels
# from ..mavlink.mavcom import MAVCom, time_since_boot_ms, time_UTC_usec, boot_time_str, date_time_str
from ..utils.general import time_since_boot_ms, time_UTC_usec, boot_time_str, date_time_str
from ..mavlink.component import Component, mavutil, mavlink, MAVLink
try:
    from gstreamer import GstPipeline, GstVideoSource, GstVideoSave, GstJpegEnc, GstStreamUDP
    import gstreamer.utils as gst_utils
except:
    print("GStreamer is not installed")
    pass
from ..camera.gst_cam import GSTCamera
from ..utils.sim_linux import RunSim
from ..airsim.client import AirSimClient
import threading
import cv2
import numpy as np



class AirsimCamera(GSTCamera):

    """ run the airsim enviroment Create a airsim camera component for testing using GStreamer"""

    def __init__(self,
                 camera_dict=None,  # camera_info dict
                 udp_encoder='H264',  # encoder for video streaming
                 loglevel=LogLevels.INFO):  # log flag
        super().__init__( camera_dict, loglevel)

        # GstVideoSink(command, width=width, height=height, loglevel=10) as pipeline:


        self.rs = RunSim("AirSimNH", settings="config/settings_high_res.json")
        self.asc = AirSimClient()

    def close(self):
        """Close the camera component."""
        self.rs.exit()
        super().close()

    def __exit__(self, exc_type, exc_value, traceback):
        """Context manager exit point."""
        print("Exiting AirsimCamera")
        super().__exit__(exc_type, exc_value, traceback)
        self.close()
        return False  # re-raise any exceptions

def videoCamera(camera_name):
    """
    Set up streaming pipeline for Video camera
    """
    return True


