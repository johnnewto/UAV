from UAV.logging import LogLevels

from UAV.mavlink import CameraClient, CameraServer,  MAVCom, GimbalClient, GimbalServer, mavutil, mavlink
from UAV.utils.general import boot_time_str, With, toml_load
from UAV.mavlink.camera_client import CAMERA_IMAGE_CAPTURED


from gstreamer import GstPipeline, Gst, GstContext, GstPipes
from gstreamer.utils import to_gst_string

import time
from pathlib import Path
import asyncio

import gstreamer.utils as gst_utils


DISPLAY_H264_PIPELINE = to_gst_string([
    'udpsrc port={} ! application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)H264, payload=(int)96',
    'queue ! rtph264depay ! avdec_h264',
    'fpsdisplaysink ',
])
# gst-launch-1.0 udpsrc port=5000 ! application/x-rtp,media=(string)video,clock-rate=(int)90000,encoding-name=(string)RAW,sampling=(string)RGB ! rtpvrawdepay ! videoconvert ! autovideosink
DISPLAY_RAW_PIPELINE = to_gst_string([
    # 'udpsrc port={} ! application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)RAW, sampling=(string)RGB,depth=(string)8, width=(string)640, height=(string)480, payload=(int)96',
    # 'udpsrc port={} ! application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)RAW, sampling=(string)RGB,depth=(string)8, width=(string)640, height=(string)480',
    'udpsrc port={} caps = "application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)RAW, sampling=(string)RGB, depth=(string)8, width=(string)640, height=(string)480"',
    'queue ! rtpvrawdepay ! videoconvert',
    # 'rtpvrawdepay ! videoconvert ! queue',
    'fpsdisplaysink sync=false ',
])

def display(num_cams=2, udp_encoder='h264'):
    """ Display video from drone"""
    if '264' in udp_encoder:
        display_pipelines = [GstPipeline(DISPLAY_H264_PIPELINE.format(5100+i)) for i in range(num_cams)]
    else:
        display_pipelines = [GstPipeline(DISPLAY_RAW_PIPELINE.format(5100 + i)) for i in range(num_cams)]

    with GstContext(loglevel=LogLevels.CRITICAL):  # GST main loop in thread
        with GstPipes(display_pipelines, loglevel=LogLevels.INFO):  # this will show the video on fpsdisplaysink
            while any(p.is_active for p in display_pipelines):
                time.sleep(.5)






if __name__ == '__main__':
    UDP_ENCODER = 'rawvideo'  # 'h264'
    # UDP_ENCODER = 'h264'
    num_cams = 1
    display(num_cams, UDP_ENCODER)

