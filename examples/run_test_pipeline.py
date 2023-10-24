from UAV.logging import LogLevels
from UAV.utils.general import boot_time_str, With, toml_load, config_dir
from gstreamer import GstPipeline, Gst, GstContext, GstPipes, GstStreamUDP, GstJpegEnc
import gstreamer.utils as gst_utils
import time


def on_video_callback(data):
    print("on_video_callback", data)


def on_capture(buffer, ):
    print(f'on_capture: {len(buffer) = }  bytes')


camera_dict = toml_load(config_dir() / "test_camera_0.toml")
command_h264_display = gst_utils.format_pipeline(**camera_dict['gstreamer_h264_udp_displaysink'])
command_raw_display = gst_utils.format_pipeline(**camera_dict['gstreamer_raw_udp_displaysink'])
command_src = gst_utils.format_pipeline(**camera_dict['gstreamer_video_src'])
command_udp = gst_utils.format_pipeline(**camera_dict['gstreamer_h264_udpsink'])
command_jpg = gst_utils.format_pipeline(**camera_dict['gstreamer_jpg_filesink'])
gst_utils.set_gst_debug_level(Gst.DebugLevel.FIXME)

if __name__ == "__main__":
    with GstContext(loglevel=LogLevels.CRITICAL):  # GST main loop in thread
        with GstPipeline(command_h264_display, loglevel=LogLevels.INFO) as disp_pipeline:
            with GstPipeline(command_src, loglevel=10) as src_pipeline:
                with GstJpegEnc(command_jpg, max_count=5, on_jpeg_capture=on_capture, loglevel=LogLevels.INFO) as jpg_pipeline:
                    while not jpg_pipeline.is_done:
                        time.sleep(.1)

                with GstStreamUDP(command_udp, on_callback=on_video_callback, loglevel=LogLevels.INFO) as udp_pipeline:
                    time.sleep(5)

