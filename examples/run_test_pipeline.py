
from UAV.logging import LogLevels

from UAV.mavlink import CameraClient, CameraServer,  MAVCom, GimbalClient, GimbalServer, mavutil, mavlink
from UAV.utils.general import boot_time_str, With, read_camera_dict_from_toml, find_config_dir
from UAV.mavlink.camera_client import CAMERA_IMAGE_CAPTURED

from UAV.camera.gst_cam import GSTCamera
from gstreamer import GstPipeline, Gst, GstContext, GstPipes, GstStreamUDP, GstJpegEnc
from gstreamer.utils import to_gst_string
import gstreamer.utils as gst_utils

import time


def on_video_callback(data):
    print("on_video_callback", data)

def on_capture(buffer,):
    print('on_capture')




camera_dict = read_camera_dict_from_toml(find_config_dir() / "test_camera_info.toml")
command_display = gst_utils.format_pipeline(**camera_dict['gstreamer_udp_displaysink'])
command_src = gst_utils.format_pipeline(**camera_dict['gstreamer_src_intervideosink'])
command_udp = gst_utils.format_pipeline(**camera_dict['gstreamer_h264_udpsink'])
command_jpg = gst_utils.format_pipeline(**camera_dict['gstreamer_jpg_filesink'])
gst_utils.set_gst_debug_level(Gst.DebugLevel.FIXME)
if __name__ == "__main__":
    with GstContext(loglevel=LogLevels.CRITICAL):  # GST main loop in thread
        with GstPipeline(command_display, loglevel=10) as disp_pipeline:
            with GstPipeline(command_src, loglevel=10) as src_pipeline:

                with GstJpegEnc(command_jpg, max_count=5, on_jpeg_capture=on_capture, loglevel=10) as jpg_pipeline:
                    while not jpg_pipeline.is_done:
                        time.sleep(.1)

                with GstStreamUDP(command_udp, on_callback=on_video_callback, loglevel=10) as udp_pipeline:
                    time.sleep(2)
